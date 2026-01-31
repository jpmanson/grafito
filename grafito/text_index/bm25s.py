"""BM25S text index backend (optional dependency)."""

from __future__ import annotations

import os
from typing import Any

try:
    import bm25s
except ImportError as exc:  # pragma: no cover - optional dependency
    raise ImportError(
        "bm25s is not installed. Install with `pip install grafito[bm25s]` "
        "or `uv pip install grafito[bm25s]`."
    ) from exc

from .base import TextIndex


class BM25SIndex(TextIndex):
    """Text index backend using the bm25s library.
    
    This backend provides fast BM25 ranking using numpy/scipy. It maintains
    an in-memory index that can be saved/loaded from disk.
    """

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        """Initialize BM25S index.
        
        Args:
            options: Optional configuration. Supported options:
                - stopwords: Stopword list or language code (default: "en")
                - stemmer: Stemmer function or None
        """
        super().__init__(options)
        self._retriever = bm25s.BM25()
        self._id_to_internal: dict[int, int] = {}
        self._internal_to_id: dict[int, int] = {}
        self._contents: list[str] = []
        self._dirty = True
        self._stopwords = self.options.get("stopwords", "en")

    def add(self, ids: list[int], contents: list[str]) -> None:
        """Add documents to the index.
        
        Args:
            ids: List of document IDs.
            contents: List of text contents to index.
        """
        if len(ids) != len(contents):
            raise ValueError("ids and contents length mismatch")
        
        for idx, content in zip(ids, contents):
            if idx in self._id_to_internal:
                # Update existing document
                internal_idx = self._id_to_internal[idx]
                self._contents[internal_idx] = content
            else:
                # Add new document
                internal_idx = len(self._contents)
                self._id_to_internal[idx] = internal_idx
                self._internal_to_id[internal_idx] = idx
                self._contents.append(content)
        
        self._dirty = True

    def remove(self, ids: list[int]) -> None:
        """Remove documents from the index.
        
        Note: BM25S doesn't support incremental removal. Removed documents
        are marked as empty and excluded from results.
        
        Args:
            ids: List of document IDs to remove.
        """
        for idx in ids:
            if idx in self._id_to_internal:
                internal_idx = self._id_to_internal[idx]
                self._contents[internal_idx] = ""  # Mark as empty
        self._dirty = True

    def search(self, query: str, k: int) -> list[tuple[int, float]]:
        """Search for documents matching the query.
        
        Args:
            query: Search query string.
            k: Number of results to return.
            
        Returns:
            List of (id, score) tuples, ordered by relevance.
        """
        if not query or not query.strip():
            return []
        
        self._ensure_built()
        
        if not self._contents:
            return []
        
        query_tokens = bm25s.tokenize(query, stopwords=self._stopwords)
        results, scores = self._retriever.retrieve(query_tokens, k=min(k, len(self._contents)))
        
        output = []
        for i in range(results.shape[1]):
            internal_idx = int(results[0, i])
            score = float(scores[0, i])
            
            # Skip empty (removed) documents
            if not self._contents[internal_idx]:
                continue
            
            external_id = self._internal_to_id.get(internal_idx)
            if external_id is not None:
                output.append((external_id, score))
        
        return output

    def save(self, path: str) -> None:
        """Save the index to disk.
        
        Args:
            path: Directory path to save to.
        """
        self._ensure_built()
        os.makedirs(path, exist_ok=True)
        self._retriever.save(path, corpus=self._contents)
        
        # Save ID mappings
        import json
        mappings_path = os.path.join(path, "id_mappings.json")
        with open(mappings_path, "w") as f:
            json.dump({
                "id_to_internal": {str(k): v for k, v in self._id_to_internal.items()},
                "internal_to_id": {str(k): v for k, v in self._internal_to_id.items()},
            }, f)

    def load(self, path: str) -> None:
        """Load the index from disk.
        
        Args:
            path: Directory path to load from.
        """
        self._retriever = bm25s.BM25.load(path, load_corpus=True)
        self._contents = list(self._retriever.corpus) if hasattr(self._retriever, 'corpus') else []
        
        # Load ID mappings
        import json
        mappings_path = os.path.join(path, "id_mappings.json")
        if os.path.exists(mappings_path):
            with open(mappings_path) as f:
                data = json.load(f)
                self._id_to_internal = {int(k): v for k, v in data.get("id_to_internal", {}).items()}
                self._internal_to_id = {int(k): v for k, v in data.get("internal_to_id", {}).items()}
        
        self._dirty = False

    def rebuild(self) -> None:
        """Force rebuild of the index."""
        self._dirty = True
        self._ensure_built()

    def supports_remove(self) -> bool:
        return False  # Soft removal only

    def _ensure_built(self) -> None:
        """Rebuild the index if necessary."""
        if not self._dirty:
            return
        
        if not self._contents:
            self._dirty = False
            return
        
        corpus_tokens = bm25s.tokenize(self._contents, stopwords=self._stopwords)
        self._retriever = bm25s.BM25()
        self._retriever.index(corpus_tokens)
        self._dirty = False
