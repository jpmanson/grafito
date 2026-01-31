"""Annoy-based vector index backend (optional)."""

from __future__ import annotations

import json
import os
from typing import Any

import numpy as np

try:
    from annoy import AnnoyIndex
except Exception as exc:  # pragma: no cover - optional dependency
    raise ImportError("annoy is not installed") from exc

from .base import VectorIndex


class AnnoyIndexBackend(VectorIndex):
    """Approximate k-NN backend using Annoy.
    
    Note: Annoy requires consecutive integer indices starting from 0.
    This implementation maintains internal mappings between external node IDs
    and internal Annoy indices.
    """

    def __init__(self, dim: int, method: str = "annoy", options: dict[str, Any] | None = None) -> None:
        super().__init__(dim=dim, method=method, options=options)
        self.metric = (self.options.get("metric") or "angular").lower()
        if self.metric not in ("angular", "euclidean", "manhattan", "hamming", "dot"):
            raise ValueError("metric must be 'angular', 'euclidean', 'manhattan', 'hamming', or 'dot'")
        self._vectors: dict[int, list[float]] = {}
        # Mappings between external node IDs and internal consecutive indices
        self._id_to_internal: dict[int, int] = {}
        self._internal_to_id: dict[int, int] = {}
        self._index = AnnoyIndex(self.dim, self.metric)
        self._dirty = False
        if "n_trees" in self.options:
            self._parse_n_trees()
        if "search_k" in self.options:
            self._parse_search_k()

    def add(self, ids: list[int], vectors: list[list[float]]) -> None:
        if len(ids) != len(vectors):
            raise ValueError("ids and vectors length mismatch")
        for idx, vector in zip(ids, vectors):
            self._validate_vector(vector)
            self._vectors[int(idx)] = list(vector)
        self._dirty = True

    def remove(self, ids: list[int]) -> None:
        for idx in ids:
            self._vectors.pop(int(idx), None)
        self._dirty = True

    def search(self, vector: list[float], k: int) -> list[tuple[int, float]]:
        if k <= 0:
            return []
        self._validate_vector(vector)
        self._ensure_built()
        if not self._vectors and self._index.get_n_items() == 0:
            return []
        search_k = self._parse_search_k()
        if search_k is None:
            internal_ids, distances = self._index.get_nns_by_vector(
                vector,
                k,
                include_distances=True,
            )
        else:
            internal_ids, distances = self._index.get_nns_by_vector(
                vector,
                k,
                search_k=search_k,
                include_distances=True,
            )
        # Map internal indices back to external node IDs
        results = []
        for internal_idx, dist in zip(internal_ids, distances):
            external_id = self._internal_to_id.get(internal_idx)
            if external_id is not None:
                results.append((external_id, -float(dist)))
        return results

    def save(self, path: str) -> None:
        self._ensure_built()
        self._index.save(path)
        # Save ID mappings to a separate JSON file
        mappings_path = path + ".mappings.json"
        with open(mappings_path, "w") as f:
            json.dump({
                "id_to_internal": {str(k): v for k, v in self._id_to_internal.items()},
                "internal_to_id": {str(k): v for k, v in self._internal_to_id.items()},
            }, f)

    def load(self, path: str) -> None:
        self._index = AnnoyIndex(self.dim, self.metric)
        self._index.load(path)
        # Load ID mappings from JSON file
        mappings_path = path + ".mappings.json"
        if os.path.exists(mappings_path):
            with open(mappings_path) as f:
                data = json.load(f)
                self._id_to_internal = {int(k): v for k, v in data.get("id_to_internal", {}).items()}
                self._internal_to_id = {int(k): v for k, v in data.get("internal_to_id", {}).items()}
        self._dirty = False

    def unload(self) -> None:
        if hasattr(self._index, "unload"):
            self._index.unload()

    def supports_remove(self) -> bool:
        return False

    def get_vector(self, idx: int) -> list[float] | None:
        if idx in self._vectors:
            return self._vectors[idx]
        # Try to get from built index using internal mapping
        internal_idx = self._id_to_internal.get(idx)
        if internal_idx is None:
            return None
        try:
            return list(self._index.get_item_vector(internal_idx))
        except Exception:
            return None

    def _ensure_built(self) -> None:
        if not self._dirty:
            return
        self._index = AnnoyIndex(self.dim, self.metric)
        # Build mappings and add items with consecutive indices
        self._id_to_internal = {}
        self._internal_to_id = {}
        for internal_idx, (external_id, vector) in enumerate(self._vectors.items()):
            self._id_to_internal[external_id] = internal_idx
            self._internal_to_id[internal_idx] = external_id
            self._index.add_item(internal_idx, vector)
        n_trees = self._parse_n_trees()
        self._index.build(n_trees)
        self._dirty = False

    def _validate_vector(self, vector: list[float]) -> None:
        if len(vector) != self.dim:
            raise ValueError(f"Vector dimension mismatch: expected {self.dim}")
        np.array(vector, dtype="float32")

    def _parse_n_trees(self) -> int:
        n_trees = self.options.get("n_trees", 10)
        if not isinstance(n_trees, int):
            raise ValueError("n_trees must be an integer")
        if n_trees <= 0:
            raise ValueError("n_trees must be a positive integer")
        return n_trees

    def _parse_search_k(self) -> int | None:
        search_k = self.options.get("search_k")
        if search_k is None:
            return None
        if not isinstance(search_k, int):
            raise ValueError("search_k must be an integer")
        if search_k <= 0:
            raise ValueError("search_k must be a positive integer")
        return search_k
