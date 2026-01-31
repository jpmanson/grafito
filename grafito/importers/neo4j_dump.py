import os
import struct
import tarfile
import tempfile
from typing import Any, Iterator

from ..exceptions import DatabaseError

try:
    import zstandard as zstd
except ImportError:  # pragma: no cover - optional dependency
    zstd = None


def extract_dump(dump_path: str, output_dir: str) -> None:
    """Extract a Neo4j .dump archive into output_dir."""
    if not os.path.exists(dump_path):
        raise DatabaseError(f"Dump file not found: {dump_path}")

    with open(dump_path, "rb") as handle:
        header = handle.read(4)
        if header == b"DZV1":
            offset = 4
        elif header == b"DGV1":
            raise DatabaseError("Unsupported DGV1 (gzip) dump format.")
        else:
            offset = 0

    if zstd is None:
        raise DatabaseError(
            "zstandard is required to extract Neo4j dumps. Install with `pip install zstandard`."
        )

    os.makedirs(output_dir, exist_ok=True)
    with open(dump_path, "rb") as handle:
        handle.seek(offset)
        reader = zstd.ZstdDecompressor().stream_reader(handle)
        try:
            reader.read(24)
            with tarfile.open(fileobj=reader, mode="r|") as tar:
                for member in tar:
                    name = member.name.lstrip("./")
                    if "neostore" not in name:
                        continue
                    target_path = os.path.join(output_dir, name)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    if member.isdir():
                        os.makedirs(target_path, exist_ok=True)
                        continue
                    extracted = tar.extractfile(member)
                    if extracted is None:
                        continue
                    with open(target_path, "wb") as out_handle:
                        out_handle.write(extracted.read())
        finally:
            reader.close()


def find_store_dir(root_dir: str) -> str:
    """Locate the Neo4j store directory inside an extracted dump."""
    for dirpath, _, filenames in os.walk(root_dir):
        if "neostore.nodestore.db" in filenames:
            return dirpath
    raise DatabaseError("Neo4j store directory not found in extracted dump.")


def _choose_page_size(store_dir: str, endian: str) -> int:
    candidates = [4096, 8192, 16384]
    rel_path = os.path.join(store_dir, "neostore.relationshipstore.db")
    token_path = os.path.join(store_dir, "neostore.relationshiptypestore.db")
    if not os.path.exists(rel_path) or not os.path.exists(token_path):
        return 4096

    def max_token_id(page_size: int) -> int:
        reader = FixedRecordReader(token_path, 5, page_size=page_size)
        max_id = -1
        for token_id, data in reader.iter_records():
            if data[0] & 0x01:
                max_id = max(max_id, token_id)
        reader.close()
        return max_id

    def score_page_size(page_size: int, max_id: int) -> float:
        if max_id < 0:
            return 0.0
        reader = FixedRecordReader(rel_path, 34, page_size=page_size)
        valid = 0
        total = 0
        for record_id, data in reader.iter_records():
            header = data[0]
            if not (header & 0x01):
                continue
            total += 1
            type_int = struct.unpack(f"{endian}I", data[9:13])[0]
            type_id = type_int & 0xFFFF
            if type_id <= max_id:
                valid += 1
            if total >= 2000:
                break
        reader.close()
        return valid / total if total else 0.0

    best_page = candidates[0]
    best_score = -1.0
    for candidate in candidates:
        if os.path.getsize(rel_path) % candidate != 0:
            continue
        max_id = max_token_id(candidate)
        score = score_page_size(candidate, max_id)
        if score > best_score or (score == best_score and candidate < best_page):
            best_score = score
            best_page = candidate
    return best_page


def _sanitize_text(value: str) -> str:
    try:
        return value.encode("utf-8", errors="replace").decode("utf-8")
    except Exception:
        return value


class FixedRecordReader:
    def __init__(self, path: str, record_size: int, page_size: int | None = None):
        self.path = path
        self.record_size = record_size
        self.page_size = page_size or 4096
        self.records_per_page = self.page_size // self.record_size
        self.file = None
        self.max_record_id = 0
        if os.path.exists(self.path) and self.records_per_page > 0:
            self.file = open(self.path, "rb")
            size = os.path.getsize(self.path)
            pages = size // self.page_size
            self.max_record_id = pages * self.records_per_page

    def read_record(self, record_id: int) -> bytes:
        if not self.file:
            return b""
        page_id = record_id // self.records_per_page
        offset_in_page = (record_id % self.records_per_page) * self.record_size
        self.file.seek(page_id * self.page_size + offset_in_page)
        return self.file.read(self.record_size)

    def iter_records(self, start_id: int = 0) -> Iterator[tuple[int, bytes]]:
        if not self.file:
            return
        record_id = start_id
        while record_id < self.max_record_id:
            data = self.read_record(record_id)
            if len(data) < self.record_size:
                break
            yield record_id, data
            record_id += 1

    def close(self) -> None:
        if self.file:
            self.file.close()


class DynamicStoreManager:
    def __init__(
        self,
        store_path: str,
        record_size: int | None = None,
        endian: str = ">",
        page_size: int | None = None,
    ):
        self.store_path = store_path
        self.endian = endian
        self.record_size = record_size or self._read_record_size()
        self.reader = None
        if self.record_size and os.path.exists(self.store_path):
            self.reader = FixedRecordReader(self.store_path, self.record_size, page_size=page_size)

    def _read_record_size(self) -> int:
        if not os.path.exists(self.store_path):
            return 38
        try:
            with open(self.store_path, "rb") as handle:
                data = handle.read(4)
            if len(data) == 4:
                return struct.unpack(f"{self.endian}I", data)[0]
        except OSError:
            pass
        return 38

    def read_bytes(self, start_block_id: int | None) -> bytes:
        if not self.reader or start_block_id is None or start_block_id == 4294967295:
            return b""
        full_data = b""
        curr_id = start_block_id
        visited = set()
        while curr_id != 4294967295 and curr_id not in visited:
            visited.add(curr_id)
            data = self.reader.read_record(curr_id)
            if len(data) < self.record_size:
                break
            header_byte = data[0]
            if not (header_byte & 0x10):
                break
            nr_of_bytes = (data[1] << 16) | (data[2] << 8) | data[3]
            next_block = struct.unpack(f"{self.endian}I", data[4:8])[0]
            next_block |= ((header_byte & 0x0F) << 32)
            full_data += data[8 : 8 + nr_of_bytes]
            curr_id = next_block
        return full_data

    def read_string(self, start_block_id: int | None) -> str | None:
        full_data = self.read_bytes(start_block_id)
        if not full_data:
            return None
        try:
            return full_data.decode("utf-8", errors="replace").strip("\x00")
        except Exception:
            return full_data.decode("latin-1", errors="replace").strip("\x00")

    def close(self) -> None:
        if self.reader:
            self.reader.close()


class ShortStringDecoder:
    PUNCTUATION = [
        " ",
        "_",
        ".",
        "-",
        ":",
        "/",
        " ",
        ".",
        "-",
        "+",
        ",",
        "'",
        "@",
        "|",
        ";",
        "*",
        "?",
        "&",
        "%",
        "#",
        "(",
        ")",
        "$",
        "<",
        ">",
        "=",
    ]

    @staticmethod
    def decode(codec_id: int, blocks: list[int], length: int) -> str:
        if codec_id == 10:
            return ShortStringDecoder._decode_generic(blocks, length, 8, lambda x: chr(x))
        if codec_id == 0:
            return ShortStringDecoder._decode_generic(blocks, length, 8, lambda x: chr(x))
        if codec_id == 6:
            return ShortStringDecoder._decode_generic(blocks, length, 6, ShortStringDecoder._dec_uri)
        if codec_id == 1:
            return ShortStringDecoder._decode_generic(blocks, length, 4, ShortStringDecoder._dec_numerical)
        if codec_id == 7:
            return ShortStringDecoder._decode_generic(blocks, length, 6, ShortStringDecoder._dec_alphanum)
        if codec_id == 9:
            return ShortStringDecoder._decode_generic(blocks, length, 7, ShortStringDecoder._dec_european)
        if codec_id == 4:
            return ShortStringDecoder._decode_generic(blocks, length, 5, ShortStringDecoder._dec_lower)
        if codec_id == 3:
            return ShortStringDecoder._decode_generic(blocks, length, 5, ShortStringDecoder._dec_upper)
        return f"(Codec {codec_id} len {length})"

    @staticmethod
    def _decode_generic(blocks: list[int], length: int, step: int, decode_func) -> str:
        res = []
        block_idx = 0
        bit_idx = 39
        current_block = blocks[0]

        for _ in range(length):
            if bit_idx + step > 64:
                bits_in_first = 64 - bit_idx
                part1 = (current_block >> bit_idx) & ((1 << bits_in_first) - 1)
                block_idx += 1
                if block_idx < len(blocks):
                    current_block = blocks[block_idx]
                    bits_in_second = step - bits_in_first
                    part2 = current_block & ((1 << bits_in_second) - 1)
                    code = part1 | (part2 << bits_in_first)
                    bit_idx = bits_in_second
                else:
                    code = part1
            else:
                code = (current_block >> bit_idx) & ((1 << step) - 1)
                bit_idx += step
            res.append(decode_func(code))
        return "".join(res)

    @staticmethod
    def _dec_punctuation(code: int) -> str:
        if 0 <= code < len(ShortStringDecoder.PUNCTUATION):
            return ShortStringDecoder.PUNCTUATION[code]
        return "?"

    @staticmethod
    def _dec_uri(c: int) -> str:
        if c == 0:
            return " "
        if c <= 0x1A:
            return chr(c + ord("a") - 1)
        if c <= 0x29:
            return chr(c - 0x20 + ord("0"))
        if c <= 0x2E:
            return ShortStringDecoder._dec_punctuation(c - 0x29)
        return ShortStringDecoder._dec_punctuation(c - 0x2F + 9)

    @staticmethod
    def _dec_numerical(c: int) -> str:
        if c < 10:
            return chr(c + ord("0"))
        return ShortStringDecoder._dec_punctuation(c - 10 + 6)

    @staticmethod
    def _dec_alphanum(c: int) -> str:
        return ShortStringDecoder._dec_european(c + 0x40)

    @staticmethod
    def _dec_lower(c: int) -> str:
        if c == 0:
            return " "
        if c <= 0x1A:
            return chr(c + ord("a") - 1)
        return ShortStringDecoder._dec_punctuation(1 if c == 0x1B else c - 0x1A)

    @staticmethod
    def _dec_upper(c: int) -> str:
        if c == 0:
            return " "
        if c <= 0x1A:
            return chr(c + ord("A") - 1)
        return ShortStringDecoder._dec_punctuation(c - 0x1A)

    @staticmethod
    def _dec_european(c: int) -> str:
        if c < 0x40:
            if c == 0x17:
                return "."
            if c == 0x37:
                return "-"
            return chr(c + 0xC0)
        if c == 0x40:
            return " "
        if c == 0x60:
            return "_"
        if 0x5B <= c < 0x60:
            return chr(ord("0") + c - 0x5B)
        if 0x7B <= c < 0x80:
            return chr(ord("5") + c - 0x7B)
        return chr(c)


class TokenManager:
    def __init__(
        self,
        keys_path: str,
        names_path: str,
        is_prop: bool = False,
        endian: str = ">",
        page_size: int | None = None,
    ):
        self.keys_path = keys_path
        self.endian = endian
        self.tokens: dict[int, str] = {}
        self.is_prop = is_prop
        if self.is_prop:
            token_record_size = 9
            name_id_offset = 5
        else:
            token_record_size = 5
            name_id_offset = 1
        in_use_mask = 0x01
        self.name_store = DynamicStoreManager(names_path, endian=endian, page_size=page_size)
        self.record_size = token_record_size
        self.name_id_offset = name_id_offset
        self.in_use_mask = in_use_mask
        self._load_tokens(page_size=page_size)

    @staticmethod
    def _is_plausible_name(name: str | None) -> bool:
        if not name:
            return False
        if len(name) > 128:
            return False
        printable = sum(1 for ch in name if ch.isprintable())
        return printable / max(len(name), 1) >= 0.85

    def _load_tokens(self, page_size: int | None = None) -> None:
        if not os.path.exists(self.keys_path):
            return
        rec_size = self.record_size
        reader = FixedRecordReader(self.keys_path, rec_size, page_size=page_size)
        for token_id, data in reader.iter_records():
            header = data[0]
            if header & self.in_use_mask:
                name_id = struct.unpack(
                    f"{self.endian}I",
                    data[self.name_id_offset : self.name_id_offset + 4],
                )[0]
                name = self.name_store.read_string(name_id)
                self.tokens[token_id] = name
        reader.close()

    def get_token_name(self, token_id: int) -> str:
        return self.tokens.get(token_id, f"ID:{token_id}")

    def close(self) -> None:
        self.name_store.close()

    def get_token_name(self, token_id: int) -> str:
        return self.tokens.get(token_id, f"ID:{token_id}")

    def close(self) -> None:
        self.name_store.close()


class PropertyManager:
    def __init__(
        self,
        store_dir: str,
        key_tokens: TokenManager,
        endian: str = ">",
        page_size: int | None = None,
    ):
        self.store_dir = store_dir
        self.endian = endian
        self.prop_path = os.path.join(store_dir, "neostore.propertystore.db")
        self.string_store = DynamicStoreManager(
            os.path.join(store_dir, "neostore.propertystore.db.strings"),
            endian=endian,
            page_size=page_size,
        )
        self.key_tokens = key_tokens
        self.record_size = 41
        self.reader = FixedRecordReader(self.prop_path, self.record_size, page_size=page_size)
        self.block_endian = self.endian

    def get_properties(self, first_prop_id: int | None) -> dict[str, Any]:
        if first_prop_id is None or first_prop_id == 4294967295 or not os.path.exists(self.prop_path):
            return {}
        props: dict[str, Any] = {}
        curr_id = first_prop_id
        visited = set()
        while curr_id is not None and curr_id != 4294967295 and curr_id not in visited:
            visited.add(curr_id)
            data = self.reader.read_record(curr_id)
            if len(data) < self.record_size:
                break
            mod = data[0]
            next_prop_raw = struct.unpack(f"{self.endian}I", data[5:9])[0]
            if next_prop_raw == 4294967295:
                next_prop = None
            else:
                next_prop = next_prop_raw | ((mod & 0x0F) << 32)
            payload = data[9:41]

            i = 0
            while i < 32:
                block_data = payload[i : i + 8]
                if len(block_data) < 8:
                    break
                block = struct.unpack(f"{self.block_endian}Q", block_data)[0]
                if block == 0:
                    break

                prop_type = (block >> 24) & 0x0F
                if prop_type < 1 or prop_type > 14:
                    break

                key_id = block & 0xFFFFFF
                key_name = self.key_tokens.get_token_name(key_id)

                extra_blocks = []
                blocks_used = self._calculate_blocks_used(prop_type, block)
                for k in range(1, blocks_used):
                    if i + 8 * k < 32:
                        eb_data = payload[i + 8 * k : i + 8 * (k + 1)]
                        eb = struct.unpack(f"{self.block_endian}Q", eb_data)[0]
                        extra_blocks.append(eb)

                all_blocks = [block] + extra_blocks
                value = self._decode_block(prop_type, all_blocks)

                if value is not None and not (
                    isinstance(value, str)
                    and (value.startswith("Type:") or value.startswith("Codec") or value == "Long")
                ):
                    props[key_name] = value

                i += 8 * blocks_used
            curr_id = next_prop
        return props

    def _calculate_blocks_used(self, prop_type: int, block: int) -> int:
        if prop_type in [1, 2, 3, 4, 5, 7, 9, 10, 12, 13, 14]:
            return 1
        if prop_type == 6:
            return 1 if (block & 0x10000000) else 2
        if prop_type == 8:
            return 2
        if prop_type == 11:
            length = (block >> 33) & 0x3F
            if length <= 3:
                return 1
            if length <= 12:
                return 2
            return 3
        return 1

    def _decode_block(self, prop_type: int, blocks: list[int]) -> Any:
        block = blocks[0]
        if prop_type == 1:
            return (block & 1) == 1
        elif prop_type == 2:
            return struct.unpack("b", struct.pack("B", (block >> 28) & 0xFF))[0]
        elif prop_type == 3:
            return struct.unpack("h", struct.pack(">H", (block >> 28) & 0xFFFF))[0]
        elif prop_type == 4:
            value = chr((block >> 28) & 0xFFFF)
            return _sanitize_text(value)
        elif prop_type == 5:
            val_raw = (block >> 28) & 0xFFFFFFFF
            return struct.unpack(f"{self.endian}i", struct.pack(f"{self.endian}I", val_raw))[0]
        elif prop_type == 6:
            if (block & 0x10000000):
                return ((block & 0xFFFFFFFFF0000000) >> 28) >> 1
            if len(blocks) > 1:
                return struct.unpack(f"{self.endian}q", struct.pack(f"{self.endian}Q", blocks[1]))[0]
            return "Long"
        elif prop_type == 7:
            val_raw = (block >> 28) & 0xFFFFFFFF
            return struct.unpack(f"{self.endian}f", struct.pack(f"{self.endian}I", val_raw))[0]
        elif prop_type == 8:
            if len(blocks) > 1:
                return struct.unpack(f"{self.endian}d", struct.pack(f"{self.endian}Q", blocks[1]))[0]
            return None
        elif prop_type == 9:
            value = self.string_store.read_string(block >> 28)
            return _sanitize_text(value) if isinstance(value, str) else value
        elif prop_type == 11:
            length = (block >> 33) & 0x3F
            codec = (block >> 28) & 0x1F
            value = ShortStringDecoder.decode(codec, blocks, length)
            return _sanitize_text(value)
        return f"Type:{prop_type}"

    def close(self) -> None:
        self.string_store.close()
        self.reader.close()


class Neo4jStoreParser:
    def __init__(self, store_dir: str, endian: str = ">"):
        self.store_dir = store_dir
        self.endian = endian
        self.page_size = _choose_page_size(store_dir, endian)
        self.prop_keys = TokenManager(
            os.path.join(store_dir, "neostore.propertystore.db.index"),
            os.path.join(store_dir, "neostore.propertystore.db.index.keys"),
            is_prop=True,
            endian=endian,
            page_size=self.page_size,
        )
        self.labels = TokenManager(
            os.path.join(store_dir, "neostore.labeltokenstore.db"),
            os.path.join(store_dir, "neostore.labeltokenstore.db.names"),
            endian=endian,
            page_size=self.page_size,
        )
        self.rel_types = TokenManager(
            os.path.join(store_dir, "neostore.relationshiptypestore.db"),
            os.path.join(store_dir, "neostore.relationshiptypestore.db.names"),
            endian=endian,
            page_size=self.page_size,
        )
        self.props = PropertyManager(store_dir, self.prop_keys, endian=endian, page_size=self.page_size)

    def parse_nodes(self) -> Iterator[dict[str, Any]]:
        path = os.path.join(self.store_dir, "neostore.nodestore.db")
        if not os.path.exists(path):
            return
        reader = FixedRecordReader(path, 15, page_size=self.page_size)
        for record_id, data in reader.iter_records():
            header = data[0]
            if not (header & 0x01):
                continue
            next_prop_raw = struct.unpack(f"{self.endian}I", data[5:9])[0]
            if next_prop_raw == 4294967295:
                next_prop = None
            else:
                next_prop = next_prop_raw | ((header & 0xF0) << 28)
            lsb_labels = struct.unpack(f"{self.endian}I", data[9:13])[0]
            hsb_labels = data[13]
            labels_bits = lsb_labels | (hsb_labels << 32)

            node_labels = []
            if labels_bits & 0x8000000000:
                node_labels = []
            else:
                cnt = (labels_bits >> 36) & 0xF
                if 0 < cnt <= 7:
                    bits_per_label = 36 // cnt
                    mask = (1 << bits_per_label) - 1
                    for i in range(cnt):
                        l_id = (labels_bits >> (i * bits_per_label)) & mask
                        name = self.labels.get_token_name(l_id)
                        if name:
                            node_labels.append(name)

            yield {
                "type": "node",
                "id": record_id,
                "labels": node_labels,
                "properties": self.props.get_properties(next_prop),
            }
        reader.close()

    def parse_relationships(self) -> Iterator[dict[str, Any]]:
        path = os.path.join(self.store_dir, "neostore.relationshipstore.db")
        if not os.path.exists(path):
            return
        reader = FixedRecordReader(path, 34, page_size=self.page_size)
        for record_id, data in reader.iter_records():
            header = data[0]
            if not (header & 0x01):
                continue
            unpacked = struct.unpack(f"{self.endian}BIIIIIIIIB", data)
            type_id = unpacked[3] & 0xFFFF
            next_prop_raw = unpacked[8]
            if next_prop_raw == 4294967295:
                next_prop = None
            else:
                next_prop = next_prop_raw | ((header & 0xF0) << 28)
            yield {
                "type": "relationship",
                "id": record_id,
                "rel_type": self.rel_types.get_token_name(type_id),
                "start_node": unpacked[1] | ((header & 0x0E) << 31),
                "end_node": unpacked[2] | ((unpacked[3] & 0x70000000) << 4),
                "properties": self.props.get_properties(next_prop),
            }
        reader.close()

    def close(self) -> None:
        self.prop_keys.close()
        self.labels.close()
        self.rel_types.close()
        self.props.close()


def import_dump(  # pragma: no cover - filesystem integration
    db,
    dump_path: str,
    temp_dir: str | None = None,
    cleanup: bool = True,
    endian: str = ">",
    progress_every: int | None = None,
    node_limit: int | None = None,
    rel_limit: int | None = None,
) -> None:
    """Import a Neo4j .dump into a Grafito database instance."""
    temp_context = None
    if temp_dir is None:
        temp_context = tempfile.TemporaryDirectory(prefix="grafito_neo4j_")
        temp_dir = temp_context.name

    try:
        extract_dump(dump_path, temp_dir)
        store_dir = find_store_dir(temp_dir)
        parser = Neo4jStoreParser(store_dir, endian=endian)
        try:
            node_id_map: dict[int, int] = {}
            db.begin_transaction()
            try:
                spinner = ['-', '\\', '|', '/']
                node_count = 0
                if progress_every:
                    print("Importing nodes: 0", end='')

                for node in parser.parse_nodes():
                    labels = list(dict.fromkeys(node["labels"])) if node.get("labels") else []
                    created = db.create_node(labels=labels, properties=node["properties"])
                    node_id_map[int(node["id"])] = created.id
                    node_count += 1
                    if node_limit is not None and node_count >= node_limit:
                        break
                    if progress_every and node_count % 100 == 0:
                        spin_char = spinner[(node_count // 100) % len(spinner)]
                        print(f"\rImporting nodes: {node_count} {spin_char}", end='', flush=True)
                
                if progress_every:
                    print(f"\rImported {node_count} nodes." + " " * 20)

                rel_count = 0
                if progress_every:
                    print("Importing relationships: 0", end='')

                for rel in parser.parse_relationships():
                    start_id = node_id_map.get(int(rel["start_node"]))
                    end_id = node_id_map.get(int(rel["end_node"]))
                    if start_id is None or end_id is None:
                        continue
                    db.create_relationship(
                        start_id,
                        end_id,
                        rel["rel_type"],
                        rel["properties"],
                    )
                    rel_count += 1
                    if rel_limit is not None and rel_count >= rel_limit:
                        break
                    if progress_every and rel_count % 100 == 0:
                        spin_char = spinner[(rel_count // 100) % len(spinner)]
                        print(f"\rImporting relationships: {rel_count} {spin_char}", end='', flush=True)

                if progress_every:
                    print(f"\rImported {rel_count} relationships." + " " * 20)
                
                db.commit()
            except Exception:
                db.rollback()
                raise
        finally:
            parser.close()
    finally:
        if cleanup and temp_context is not None:
            temp_context.cleanup()
