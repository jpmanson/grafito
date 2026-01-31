"""HNSWlib-based vector index backend (optional)."""

from __future__ import annotations

from typing import Any

import numpy as np

try:
    import hnswlib
except Exception as exc:  # pragma: no cover - optional dependency
    raise ImportError(
        "hnswlib is not installed. Install with `pip install grafito[hnswlib]` "
        "or `uv pip install grafito[hnswlib]`."
    ) from exc

from .base import VectorIndex


class HNSWlibIndexBackend(VectorIndex):
    """Approximate k-NN backend using hnswlib."""

    def __init__(self, dim: int, method: str = "hnsw", options: dict[str, Any] | None = None) -> None:
        super().__init__(dim=dim, method=method, options=options)
        self.metric = (self.options.get("metric") or "l2").lower()
        if self.metric not in ("l2", "ip", "cosine"):
            raise ValueError("metric must be 'l2', 'ip', or 'cosine'")
        self._index = hnswlib.Index(space=self.metric, dim=self.dim)
        self._size = 0
        self._built = False
        self._removed: set[int] = set()

    def add(self, ids: list[int], vectors: list[list[float]]) -> None:
        if len(ids) != len(vectors):
            raise ValueError("ids and vectors length mismatch")
        if not ids:
            return
        vecs = self._as_matrix(vectors)
        labels = np.array(ids, dtype=np.int64)
        if not self._built:
            max_elements = int(self.options.get("max_elements", max(len(ids), 1024)))
            if max_elements <= 0:
                raise ValueError("max_elements must be a positive integer")
            self._index.init_index(
                max_elements=max_elements,
                ef_construction=int(self.options.get("ef_construction", 200)),
                M=int(self.options.get("M", 16)),
            )
            self._built = True
            self._size = 0
        if self._size + len(ids) > self._index.get_max_elements():
            new_size = max(self._size + len(ids), self._index.get_max_elements() * 2)
            self._index.resize_index(new_size)
        self._index.add_items(vecs, labels)
        self._size += len(ids)
        self._removed.difference_update(int(idx) for idx in ids)
        self._apply_search_params()

    def remove(self, ids: list[int]) -> None:
        for idx in ids:
            idx = int(idx)
            self._removed.add(idx)

    def search(self, vector: list[float], k: int) -> list[tuple[int, float]]:
        if k <= 0 or not self._built:
            return []
        vec = self._as_matrix([vector])
        self._apply_search_params()
        labels, distances = self._index.knn_query(vec, k=k)
        results = []
        for idx, dist in zip(labels[0], distances[0]):
            if idx == -1:
                continue
            idx = int(idx)
            if idx in self._removed:
                continue
            results.append((idx, float(dist)))
        return results

    def save(self, path: str) -> None:
        if not self._built:
            return
        self._index.save_index(path)

    def load(self, path: str) -> None:
        self._index = hnswlib.Index(space=self.metric, dim=self.dim)
        self._index.load_index(path)
        self._built = True
        self._size = self._index.get_current_count()
        self._removed = set()
        self._apply_search_params()

    def supports_remove(self) -> bool:
        return False

    def _apply_search_params(self) -> None:
        ef_search = self.options.get("ef_search")
        if ef_search is not None:
            self._index.set_ef(int(ef_search))
        num_threads = self.options.get("num_threads")
        if num_threads is not None:
            self._index.set_num_threads(int(num_threads))

    def _as_matrix(self, vectors: list[list[float]]) -> np.ndarray:
        mat = np.array(vectors, dtype="float32")
        if mat.ndim != 2 or mat.shape[1] != self.dim:
            raise ValueError(f"Vector dimension mismatch: expected {self.dim}")
        return mat
