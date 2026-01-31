"""TensorFlow Hub embeddings function."""

from __future__ import annotations

from typing import Any

import numpy as np

from .base import EmbeddingFunction


class TensorFlowHubEmbeddingFunction(EmbeddingFunction):
    """Embedding function for TensorFlow Hub models (e.g., USE)."""

    def __init__(self, model_url: str) -> None:
        try:
            import tensorflow_hub as hub
        except ImportError as exc:
            raise ValueError(
                "tensorflow_hub is not installed. Install with `pip install tensorflow_hub`."
            ) from exc

        if not model_url:
            raise ValueError("model_url must be provided")
        self.model_url = model_url
        self._model = hub.load(model_url)

    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = self._model(input)
        return [np.array(item, dtype=np.float32).tolist() for item in embeddings]

    @staticmethod
    def name() -> str:
        return "tensorflow_hub"

    def default_space(self) -> str:
        return "cosine"

    def supported_spaces(self) -> list[str]:
        return ["cosine", "l2", "ip"]

    @staticmethod
    def build_from_config(config: dict[str, Any]) -> "EmbeddingFunction":
        model_url = config.get("model_url")
        if not model_url:
            raise ValueError("model_url must be provided")
        return TensorFlowHubEmbeddingFunction(model_url=model_url)

    def get_config(self) -> dict[str, Any]:
        return {"model_url": self.model_url}

    @staticmethod
    def validate_config(config: dict[str, Any]) -> None:
        if not isinstance(config, dict):
            raise ValueError("Embedding config must be a map")
