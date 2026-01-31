"""USearch-based vector index backend (optional)."""

from __future__ import annotations

from typing import Any

import numpy as np

try:
    from usearch.index import Index, MetricKind
except Exception as exc:  # pragma: no cover - optional dependency
    raise ImportError(
        "usearch is not installed. Install with `pip install grafito[usearch]` "
        "or `uv pip install grafito[usearch]`."
    ) from exc

from .base import VectorIndex


class USearchIndexBackend(VectorIndex):
    """Approximate k-NN backend using USearch.
    
    USearch is a fast, lightweight vector search library that supports
    arbitrary integer keys (no ID mapping needed) and multiple distance metrics.
    """

    # Map metric names to USearch MetricKind
    METRIC_MAP = {
        "l2": MetricKind.L2sq,
        "ip": MetricKind.IP,
        "cos": MetricKind.Cos,
        "cosine": MetricKind.Cos,
        "hamming": MetricKind.Hamming,
        "tanimoto": MetricKind.Tanimoto,
    }

    def __init__(self, dim: int, method: str = "hnsw", options: dict[str, Any] | None = None) -> None:
        super().__init__(dim=dim, method=method, options=options)
        metric_name = (self.options.get("metric") or "cos").lower()
        if metric_name not in self.METRIC_MAP:
            valid = ", ".join(sorted(self.METRIC_MAP.keys()))
            raise ValueError(f"metric must be one of: {valid}")
        self._metric = self.METRIC_MAP[metric_name]
        self._index = self._build_index()
        self._size = 0

    def _build_index(self) -> Index:
        """Build a new USearch index with configured parameters."""
        connectivity = int(self.options.get("connectivity", 16))
        expansion_add = int(self.options.get("expansion_add", 128))
        expansion_search = int(self.options.get("expansion_search", 64))
        
        if connectivity <= 0:
            raise ValueError("connectivity must be a positive integer")
        if expansion_add <= 0:
            raise ValueError("expansion_add must be a positive integer")
        if expansion_search <= 0:
            raise ValueError("expansion_search must be a positive integer")
        
        return Index(
            ndim=self.dim,
            metric=self._metric,
            connectivity=connectivity,
            expansion_add=expansion_add,
            expansion_search=expansion_search,
        )

    def add(self, ids: list[int], vectors: list[list[float]]) -> None:
        if len(ids) != len(vectors):
            raise ValueError("ids and vectors length mismatch")
        if not ids:
            return
        vecs = self._as_matrix(vectors)
        keys = np.array(ids, dtype=np.int64)
        self._index.add(keys, vecs)
        self._size += len(ids)

    def remove(self, ids: list[int]) -> None:
        """Remove vectors by their IDs.
        
        Note: USearch supports removal but marks items as deleted.
        They remain in the index until compaction.
        """
        for idx in ids:
            try:
                self._index.remove(int(idx))
                self._size = max(0, self._size - 1)
            except Exception:
                pass  # ID not found, ignore

    def search(self, vector: list[float], k: int) -> list[tuple[int, float]]:
        if k <= 0 or self._size == 0:
            return []
        vec = np.array(vector, dtype="float32")
        matches = self._index.search(vec, k)
        results = []
        # USearch returns Matches object with keys and distances arrays
        # For single query, these are 1D arrays
        keys = matches.keys
        distances = matches.distances
        for key, distance in zip(keys, distances):
            if key == -1 or key == np.iinfo(np.uint64).max:
                continue
            # Convert distance to similarity score (negative distance)
            results.append((int(key), -float(distance)))
        return results

    def save(self, path: str) -> None:
        """Save index to disk."""
        if self._size == 0:
            return
        self._index.save(path)

    def load(self, path: str) -> None:
        """Load index from disk."""
        self._index = Index.restore(path)
        self._size = len(self._index)

    def supports_remove(self) -> bool:
        """USearch supports removal (soft delete)."""
        return True

    def get_vector(self, idx: int) -> list[float] | None:
        """Retrieve a stored vector by ID.
        
        Note: USearch supports vector retrieval if the index was built
        with the `multi` option enabled. Otherwise returns None.
        """
        try:
            vec = self._index.get(int(idx))
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
