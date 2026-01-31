"""Indexer definitions for vector backends."""

from __future__ import annotations

from typing import Any

from ..embedding_functions import EmbeddingFunction


class Indexer:
    """Base indexer configuration."""

    backend: str = ""

    def __init__(
        self,
        method: str = "flat",
        options: dict[str, Any] | None = None,
        embedding_function: EmbeddingFunction | None = None,
        dim: int | None = None,
    ) -> None:
        self.method = method
        self.options = options or {}
        self.embedding_function = embedding_function
        if embedding_function is None and dim is None:
            raise ValueError("Provide embedding_function or dim")
        if embedding_function is not None and dim is None:
            dim = embedding_function.dimension
        if dim is None or dim <= 0:
            raise ValueError("dim must be a positive integer")
        self.dim = dim

    def to_options(self) -> dict[str, Any]:
        return dict(self.options)

    def embedding_metadata(self) -> dict[str, Any] | None:
        if not self.embedding_function:
            return None
        return {
            "name": self.embedding_function.name(),
            "config": self.embedding_function.get_config(),
        }
