"""FAISS-based vector index backend (optional)."""

from __future__ import annotations

from typing import Any

import numpy as np

try:
    import faiss
except Exception as exc:  # pragma: no cover - optional dependency
    raise ImportError(
        "faiss is not installed. Install with `pip install grafito[faiss]` "
        "or `uv pip install grafito[faiss]`."
    ) from exc

from .base import VectorIndex


class FaissIndex(VectorIndex):
    """FAISS ANN backend using ID-mapped indexes."""

    def __init__(self, dim: int, method: str = "flat", options: dict[str, Any] | None = None) -> None:
        super().__init__(dim=dim, method=method, options=options)
        self.metric = (self.options.get("metric") or "l2").lower()
        if self.metric not in ("l2", "ip"):
            raise ValueError("metric must be 'l2' or 'ip'")
        self._index = self._build_index()
        self._pending_ids: list[int] = []
        self._pending_vectors: list[list[float]] = []

    def add(self, ids: list[int], vectors: list[list[float]]) -> None:
        if len(ids) != len(vectors):
            raise ValueError("ids and vectors length mismatch")
        vecs = self._as_matrix(vectors)
        id_arr = np.array(ids, dtype=np.int64)
        if hasattr(self._index, "is_trained") and not self._index.is_trained:
            self._pending_ids.extend(ids)
            self._pending_vectors.extend(vectors)
            nlist = int(self.options.get("nlist", 100))
            if len(self._pending_vectors) < nlist:
                return
            pending_vecs = self._as_matrix(self._pending_vectors)
            pending_ids = np.array(self._pending_ids, dtype=np.int64)
            self._index.train(pending_vecs)
            self._index.add_with_ids(pending_vecs, pending_ids)
            self._pending_ids = []
            self._pending_vectors = []
            return
        self._index.add_with_ids(vecs, id_arr)

    def remove(self, ids: list[int]) -> None:
        if not ids:
            return
        id_arr = np.array(ids, dtype=np.int64)
        self._index.remove_ids(id_arr)

    def search(self, vector: list[float], k: int) -> list[tuple[int, float]]:
        if k <= 0:
            return []
        if hasattr(self._index, "is_trained") and not self._index.is_trained:
            return []
        vecs = self._as_matrix([vector])
        scores, ids = self._index.search(vecs, k)
        results = []
        for idx, score in zip(ids[0], scores[0]):
            if idx == -1:
                continue
            results.append((int(idx), float(score)))
        return results

    def save(self, path: str) -> None:
        faiss.write_index(self._index, path)

    def load(self, path: str) -> None:
        self._index = faiss.read_index(path)

    def supports_exact(self) -> bool:
        return self.method == "flat"

    def supports_remove(self) -> bool:
        return True

    def _build_index(self):
        if self.method == "flat":
            base = self._build_flat_index()
        elif self.method == "ivf_flat":
            base = self._build_ivf_index()
        elif self.method == "hnsw":
            base = self._build_hnsw_index()
        else:
            raise ValueError(f"Unsupported FAISS method: {self.method}")

        return faiss.IndexIDMap2(base)

    def _build_flat_index(self):
        if self.metric == "ip":
            return faiss.IndexFlatIP(self.dim)
        return faiss.IndexFlatL2(self.dim)

    def _build_ivf_index(self):
        nlist = int(self.options.get("nlist", 100))
        if nlist <= 0:
            raise ValueError("nlist must be a positive integer")
        quantizer = self._build_flat_index()
        if self.metric == "ip":
            base = faiss.IndexIVFFlat(quantizer, self.dim, nlist, faiss.METRIC_INNER_PRODUCT)
        else:
            base = faiss.IndexIVFFlat(quantizer, self.dim, nlist, faiss.METRIC_L2)
        nprobe = int(self.options.get("nprobe", 10))
        base.nprobe = max(1, nprobe)
        return base

    def _build_hnsw_index(self):
        m = int(self.options.get("hnsw_m", 32))
        if m <= 0:
            raise ValueError("hnsw_m must be a positive integer")
        if self.metric == "ip":
            base = faiss.IndexHNSWFlat(self.dim, m, faiss.METRIC_INNER_PRODUCT)
        else:
            base = faiss.IndexHNSWFlat(self.dim, m, faiss.METRIC_L2)
        ef_search = self.options.get("ef_search")
        ef_construction = self.options.get("ef_construction")
        if ef_search is not None:
            base.hnsw.efSearch = int(ef_search)
        if ef_construction is not None:
            base.hnsw.efConstruction = int(ef_construction)
        return base

    def _as_matrix(self, vectors: list[list[float]]) -> np.ndarray:
        mat = np.array(vectors, dtype="float32")
        if mat.ndim != 2 or mat.shape[1] != self.dim:
            raise ValueError(f"Vector dimension mismatch: expected {self.dim}")
        return mat
