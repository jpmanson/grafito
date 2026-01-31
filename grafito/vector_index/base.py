"""Base interface for vector index backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class VectorIndex(ABC):
    """Abstract vector index interface."""

    def __init__(self, dim: int, method: str, options: dict[str, Any] | None = None) -> None:
        if dim <= 0:
            raise ValueError("dim must be a positive integer")
        self.dim = dim
        self.method = method
        self.options = options or {}

    @abstractmethod
    def add(self, ids: list[int], vectors: list[list[float]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def remove(self, ids: list[int]) -> None:
        raise NotImplementedError

    @abstractmethod
    def search(self, vector: list[float], k: int) -> list[tuple[int, float]]:
        raise NotImplementedError

    @abstractmethod
    def save(self, path: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def load(self, path: str) -> None:
        raise NotImplementedError

    def get_vector(self, idx: int) -> list[float] | None:
        return None

    def supports_exact(self) -> bool:
        return False

    def supports_remove(self) -> bool:
        return False
