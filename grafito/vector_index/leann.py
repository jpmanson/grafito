"""LEANN-based vector index backend (optional)."""

from __future__ import annotations

from typing import Any
import os

import numpy as np
import pickle
import tempfile
from pathlib import Path

try:
    from leann import LeannBuilder, LeannSearcher
except Exception:  # pragma: no cover - optional dependency
    try:
        from leann.api import LeannBuilder, LeannSearcher
    except Exception as exc:  # pragma: no cover - optional dependency
        raise ImportError("leann is not installed") from exc

from .base import VectorIndex


class LeannIndexBackend(VectorIndex):
    """Approximate k-NN backend using LEANN."""

    def __init__(self, dim: int, method: str = "leann", options: dict[str, Any] | None = None) -> None:
        super().__init__(dim=dim, method=method, options=options)
        # Force store_embeddings=True for LEANN to support fallback manual search
        if "store_embeddings" not in self.options:
            self.options["store_embeddings"] = True
        self.metric = (self.options.get("metric") or "l2").lower()
        if self.metric not in ("l2", "cosine", "ip"):
            raise ValueError("metric must be 'l2', 'cosine', or 'ip'")
        self.backend_name = self.options.get("backend_name", "hnsw")
        self.embedding_model = self.options.get("embedding_model", "custom")
        # Use "file" mode with embeddings stored, not "precomputed" which leads to pruned indexes
        self.embedding_mode = self.options.get("embedding_mode", "file")
        self.embedding_options = self.options.get("embedding_options", {
            "store": True,
            "prune": False,
            "compact": False,
        })
        self.backend_kwargs = self.options.get("backend_kwargs", {
            "prune": False,
            "compact": False,
        })
        self.auto_build = bool(self.options.get("auto_build", True))
        self._vectors: dict[int, list[float]] = {}
        self._dirty = False
        self._searcher: LeannSearcher | None = None
        self._temp_index_path: str | None = None
        if "n_trees" in self.options:
            self._parse_n_trees()
        if "search_k" in self.options:
            self._parse_search_k()

        # Auto-create index_path if not provided (for in-memory databases)
        if not self.options.get("index_path"):
            temp_dir = Path(tempfile.gettempdir()) / ".grafito" / "indexes"
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".leann", dir=temp_dir
            )
            self._temp_index_path = temp_file.name
            temp_file.close()
            self.options["index_path"] = self._temp_index_path

    def __del__(self) -> None:
        """Clean up temporary index file if created."""
        if self._temp_index_path and Path(self._temp_index_path).exists():
            try:
                os.unlink(self._temp_index_path)
            except OSError:
                pass

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
        if self._dirty and not self.auto_build:
            raise ValueError("LEANN index is dirty; call rebuild or enable auto_build")
        self._ensure_built()
        if not self._vectors and not self._index_exists():
            return []
        searcher = self._ensure_searcher()
        query_embedding = np.array(vector, dtype="float32")
        search_kwargs = self._build_search_kwargs()
        try:
            try:
                results = searcher.backend_impl.search(query_embedding, k, **search_kwargs)
            except TypeError:
                results = searcher.backend_impl.search(query_embedding, k)
        except (RuntimeError, ValueError) as e:
            # If LEANN fails due to pruned index issues, fall back to manual search
            # using stored vectors (slower but works)
            if "pruned" in str(e).lower() or "zmq_port" in str(e).lower():
                return self._manual_search(vector, k)
            raise
        labels = results.get("labels", [[]])
        distances = results.get("distances", [[]])
        output = []
        for idx, dist in zip(labels[0], distances[0]):
            try:
                output.append((int(idx), -float(dist)))
            except ValueError:
                continue
        return output

    def rebuild(self) -> None:
        """Force rebuild of the index, ignoring auto_build setting."""
        if not self._vectors:
            self._dirty = False
            return
        # Temporarily enable auto_build to force rebuild
        orig_auto_build = self.auto_build
        self.auto_build = True
        try:
            self._ensure_built()
        finally:
            self.auto_build = orig_auto_build

    def save(self, path: str) -> None:
        self._ensure_built()
        # LEANN persists during build; ensure index exists on disk.
        # Check for both .leann and .index extensions (intermediate file)
        leann_path = Path(path)
        index_path = leann_path.with_suffix('.index')
        if not leann_path.exists() and not index_path.exists():
            raise ValueError("LEANN index not found on disk")

    def load(self, path: str) -> None:
        if not Path(path).exists():
            raise ValueError("LEANN index not found on disk")
        self._searcher = None
        self._dirty = False

    def supports_remove(self) -> bool:
        return False

    def get_vector(self, idx: int) -> list[float] | None:
        return self._vectors.get(int(idx))

    def _ensure_built(self) -> None:
        if not self._dirty:
            return
        if not self.auto_build:
            return
        if not self._vectors:
            self._dirty = False
            return
        index_path = self.options.get("index_path")
        if not index_path:
            raise ValueError("LEANN index_path must be provided")
        index_path = str(Path(index_path))
        Path(index_path).parent.mkdir(parents=True, exist_ok=True)

        ids = list(self._vectors.keys())
        embeddings = np.array(list(self._vectors.values()), dtype="float32")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as handle:
            pickle.dump((ids, embeddings), handle)
            embeddings_file = handle.name

        # Configure builder with options to store embeddings (avoid pruned indexes)
        builder_kwargs = {
            "compact": False,  # Avoid compact index
            **self.backend_kwargs,
        }
        builder = LeannBuilder(
            backend_name=self.backend_name,
            embedding_model=self.embedding_model,
            dimensions=self.dim,
            embedding_mode=self.embedding_mode,
            embedding_options=self.embedding_options,
            **builder_kwargs,
        )
        builder.build_index_from_embeddings(index_path, embeddings_file)
        try:
            os.unlink(embeddings_file)
        except OSError:
            pass
        self._searcher = None
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

    def _ensure_searcher(self) -> LeannSearcher:
        if self._searcher is not None:
            return self._searcher
        index_path = self.options.get("index_path")
        if not index_path:
            raise ValueError("LEANN index_path must be provided")
        # Create searcher without forcing recompute_embeddings to allow LEANN
        # to use its default behavior based on the index type
        self._searcher = LeannSearcher(
            index_path,
            enable_warmup=False,
            **self.backend_kwargs,
        )
        return self._searcher

    def _index_exists(self) -> bool:
        index_path = self.options.get("index_path")
        if not index_path:
            return False
        return Path(index_path).exists()

    def _manual_search(self, vector: list[float], k: int) -> list[tuple[int, float]]:
        """Fallback manual search using stored vectors when LEANN index is pruned."""
        if not self._vectors:
            return []

        query_vec = np.array(vector, dtype="float32")
        similarities = []

        for idx, stored_vec in self._vectors.items():
            stored_array = np.array(stored_vec, dtype="float32")

            # Compute similarity based on metric
            if self.metric == "cosine":
                # Cosine similarity
                norm_query = np.linalg.norm(query_vec)
                norm_stored = np.linalg.norm(stored_array)
                if norm_query > 0 and norm_stored > 0:
                    sim = np.dot(query_vec, stored_array) / (norm_query * norm_stored)
                else:
                    sim = 0.0
            elif self.metric == "ip":
                # Inner product
                sim = np.dot(query_vec, stored_array)
            else:  # l2
                # Negative L2 distance (so higher is better like other metrics)
                sim = -np.linalg.norm(query_vec - stored_array)

            similarities.append((idx, float(sim)))

        # Sort by similarity (descending) and take top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]

    def _build_search_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        search_k = self._parse_search_k()
        if search_k is not None:
            kwargs["search_k"] = search_k
        # Don't force recompute_embeddings setting - let LEANN use its default behavior
        # based on the index type (pruned vs non-pruned)
        for key in ("complexity", "beam_width", "prune_ratio", "pruning_strategy", "batch_size"):
            if key in self.options:
                kwargs[key] = self.options[key]
        return kwargs
