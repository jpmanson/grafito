"""SentenceTransformer embedding function (optional dependency)."""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import EmbeddingFunction


class SentenceTransformerEmbeddingFunction(EmbeddingFunction):
    """SentenceTransformer embedding function."""

    models: dict[str, Any] = {}

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = "cpu",
        normalize_embeddings: bool = False,
        **kwargs: Any,
    ) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ValueError(
                "sentence_transformers is not installed. Install with `pip install sentence_transformers`"
            )

        self.model_name = model_name
        self.device = device
        self.normalize_embeddings = normalize_embeddings
        for key, value in kwargs.items():
            if not isinstance(value, (str, int, float, bool, list, dict, tuple)):
                raise ValueError(f"Keyword argument {key} is not a primitive type")
        self.kwargs = kwargs

        if model_name not in self.models:
            self.models[model_name] = SentenceTransformer(
                model_name_or_path=model_name, device=device, **kwargs
            )
        self._model = self.models[model_name]
        self._dimension: int | None = None

    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(
            list(input),
            convert_to_numpy=True,
            normalize_embeddings=self.normalize_embeddings,
        )
        if self._dimension is None and len(embeddings) > 0:
            self._dimension = int(embeddings.shape[1])
        return [np.array(embedding, dtype=np.float32).tolist() for embedding in embeddings]

    @staticmethod
    def name() -> str:
        return "sentence_transformer"

    def default_space(self) -> str:
        return "cosine"

    def supported_spaces(self) -> list[str]:
        return ["cosine", "l2", "ip"]

    @staticmethod
    def build_from_config(config: dict[str, Any]) -> "EmbeddingFunction":
        model_name = config.get("model_name")
        device = config.get("device")
        normalize_embeddings = config.get("normalize_embeddings")
        kwargs = config.get("kwargs", {})
        if model_name is None or device is None or normalize_embeddings is None:
            raise ValueError("Invalid embedding function config")
        return SentenceTransformerEmbeddingFunction(
            model_name=model_name,
            device=device,
            normalize_embeddings=normalize_embeddings,
            **kwargs,
        )

    def get_config(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "device": self.device,
            "normalize_embeddings": self.normalize_embeddings,
            "kwargs": self.kwargs,
        }

    @staticmethod
    def validate_config(config: dict[str, Any]) -> None:
        if not isinstance(config, dict):
            raise ValueError("Embedding config must be a map")

    @property
    def dimension(self) -> int | None:
        if self._dimension is not None:
            return self._dimension
        try:
            self._dimension = int(self._model.get_sentence_embedding_dimension())
        except Exception:
            return None
        return self._dimension
