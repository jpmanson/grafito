"""Base interface for embedding functions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class EmbeddingFunction(ABC):
    """Abstract embedding function interface."""

    @abstractmethod
    def __call__(self, input: list[str]) -> list[list[float]]:
        """Generate embeddings for the given input texts."""
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def name() -> str:
        """Return the registry name for this embedding function."""
        raise NotImplementedError

    @abstractmethod
    def default_space(self) -> str:
        """Return default distance space (e.g., cosine, l2, ip)."""
        raise NotImplementedError

    @abstractmethod
    def supported_spaces(self) -> list[str]:
        """Return supported distance spaces."""
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def build_from_config(config: dict[str, Any]) -> "EmbeddingFunction":
        """Build an embedding function from a config dict."""
        raise NotImplementedError

    @abstractmethod
    def get_config(self) -> dict[str, Any]:
        """Return a config dict for this embedding function."""
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def validate_config(config: dict[str, Any]) -> None:
        """Validate config for this embedding function."""
        raise NotImplementedError

    @property
    def dimension(self) -> int | None:
        """Return embedding dimension if known."""
        return None
