"""Base interface for text index backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TextIndex(ABC):
    """Abstract text index interface.
    
    Text indexes support full-text search over documents/content. Each backend
    implementation may use different algorithms (BM25, TF-IDF, etc.) or storage
    mechanisms (SQLite FTS5, in-memory, etc.).
    """

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        self.options = options or {}

    @abstractmethod
    def add(self, ids: list[int], contents: list[str]) -> None:
        """Add documents to the index.
        
        Args:
            ids: List of document IDs.
            contents: List of text contents to index.
        """
        raise NotImplementedError

    @abstractmethod
    def remove(self, ids: list[int]) -> None:
        """Remove documents from the index.
        
        Args:
            ids: List of document IDs to remove.
        """
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str, k: int) -> list[tuple[int, float]]:
        """Search for documents matching the query.
        
        Args:
            query: Search query string.
            k: Number of results to return.
            
        Returns:
            List of (id, score) tuples, ordered by relevance (higher=better).
        """
        raise NotImplementedError

    @abstractmethod
    def save(self, path: str) -> None:
        """Save the index to disk.
        
        Args:
            path: File path to save to.
        """
        raise NotImplementedError

    @abstractmethod
    def load(self, path: str) -> None:
        """Load the index from disk.
        
        Args:
            path: File path to load from.
        """
        raise NotImplementedError

    def rebuild(self) -> None:
        """Rebuild the index. Optional for backends that need it."""
        pass

    def supports_remove(self) -> bool:
        """Whether the backend supports incremental removal."""
        return False
