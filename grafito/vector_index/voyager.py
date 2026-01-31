"""Voyager-based vector index backend (optional).

Voyager is Spotify's successor to Annoy, providing fast approximate 
nearest neighbor search with support for arbitrary integer keys.
"""

from __future__ import annotations

from typing import Any

import numpy as np

try:
    from voyager import Index, Space
except Exception as exc:  # pragma: no cover - optional dependency
    raise ImportError("voyager is not installed") from exc

from .base import VectorIndex


class VoyagerIndexBackend(VectorIndex):
    """Approximate k-NN backend using Voyager (Spotify).
    
    Voyager supports arbitrary integer IDs natively and provides
    fast HNSW-based approximate nearest neighbor search.
    """

    # Map metric names to Voyager Space
    METRIC_MAP = {
        "cosine": Space.Cosine,
        "cos": Space.Cosine,
        "euclidean": Space.Euclidean,
        "l2": Space.Euclidean,
        "ip": Space.InnerProduct,
        "inner_product": Space.InnerProduct,
    }

    def __init__(self, dim: int, method: str = "hnsw", options: dict[str, Any] | None = None) -> None:
        super().__init__(dim=dim, method=method, options=options)
        metric_name = (self.options.get("metric") or "cosine").lower()
        if metric_name not in self.METRIC_MAP:
            valid = ", ".join(sorted(set(self.METRIC_MAP.keys())))
            raise ValueError(f"metric must be one of: {valid}")
        self._space = self.METRIC_MAP[metric_name]
        self._index = self._build_index()
        self._size = 0

    def _build_index(self) -> Index:
        """Build a new Voyager index with configured parameters."""
        M = int(self.options.get("M", 12))
        ef_construction = int(self.options.get("ef_construction", 200))
        
        if M <= 0:
            raise ValueError("M must be a positive integer")
        if ef_construction <= 0:
            raise ValueError("ef_construction must be a positive integer")
        
        return Index(
            space=self._space,
            num_dimensions=self.dim,
            M=M,
            ef_construction=ef_construction,
        )

    def add(self, ids: list[int], vectors: list[list[float]]) -> None:
        if len(ids) != len(vectors):
            raise ValueError("ids and vectors length mismatch")
        if not ids:
            return
        vecs = self._as_matrix(vectors)
        id_arr = np.array(ids, dtype=np.int64)
        self._index.add_items(vectors=vecs, ids=id_arr)
        self._size += len(ids)

    def remove(self, ids: list[int]) -> None:
        """Mark items as deleted.
        
        Note: Voyager supports marking items as deleted but they
        remain in the index until it's rebuilt.
        """
        for idx in ids:
            try:
                self._index.mark_deleted(int(idx))
                self._size = max(0, self._size - 1)
            except Exception:
                pass  # ID not found, ignore

    def search(self, vector: list[float], k: int) -> list[tuple[int, float]]:
        if k <= 0 or self._size == 0:
            return []
        vec = np.array(vector, dtype="float32")
        
        # Apply ef_search if configured
        query_ef = self.options.get("ef_search")
        if query_ef is not None:
            neighbors, distances = self._index.query(vec, k=k, query_ef=int(query_ef))
        else:
            neighbors, distances = self._index.query(vec, k=k)
        
        results = []
        for idx, dist in zip(neighbors, distances):
            if idx == -1:
                continue
            # Convert distance to similarity score (negative distance)
            results.append((int(idx), -float(dist)))
        return results

    def save(self, path: str) -> None:
        """Save index to disk."""
        if self._size == 0:
            return
        self._index.save(path)

    def load(self, path: str) -> None:
        """Load index from disk."""
        self._index = Index.load(path)
        self._size = len(self._index)

    def supports_remove(self) -> bool:
        """Voyager supports soft deletion."""
        return True

    def get_vector(self, idx: int) -> list[float] | None:
        """Retrieve a stored vector by ID."""
        try:
            vec = self._index.get_vector(int(idx))
            if vec is not None:
                return list(vec)
        except Exception:
            pass
        return None

    def _as_matrix(self, vectors: list[list[float]]) -> np.ndarray:
        """Convert vectors to numpy matrix with validation."""
        mat = np.array(vectors, dtype="float32")
        if mat.ndim != 2 or mat.shape[1] != self.dim:
            raise ValueError(f"Vector dimension mismatch: expected {self.dim}")
        return mat
