"""Mistral embeddings API function."""

from __future__ import annotations

from typing import Any
import os

import numpy as np

from .base import EmbeddingFunction


class MistralEmbeddingFunction(EmbeddingFunction):
    """Embedding function for the Mistral embeddings API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "mistral-embed",
        api_key_env_var: str | None = None,
    ) -> None:
        try:
            from mistralai import Mistral
        except ImportError as exc:
            raise ValueError(
                "mistralai is not installed. Install with `pip install mistralai`."
            ) from exc

        self.model = model
        self.api_key_env_var = api_key_env_var
        if api_key is None:
            if api_key_env_var:
                api_key = os.environ.get(api_key_env_var)
            else:
                api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError(
                "Mistral API key not provided. Set MISTRAL_API_KEY or pass api_key explicitly."
            )

        self._client = Mistral(api_key=api_key)

    def __call__(self, input: list[str]) -> list[list[float]]:
        if not all(isinstance(item, str) for item in input):
            raise ValueError("Mistral only supports text documents")
        response = self._client.embeddings.create(model=self.model, inputs=input)
        return [
            np.array(item.embedding, dtype=np.float32).tolist() for item in response.data
        ]

    @staticmethod
    def name() -> str:
        return "mistral"

    def default_space(self) -> str:
        return "cosine"

    def supported_spaces(self) -> list[str]:
        return ["cosine", "l2", "ip"]

    @staticmethod
    def build_from_config(config: dict[str, Any]) -> "EmbeddingFunction":
        model = config.get("model")
        api_key_env_var = config.get("api_key_env_var")
        if not model:
            raise ValueError("model must be provided")
        return MistralEmbeddingFunction(model=model, api_key_env_var=api_key_env_var)

    def get_config(self) -> dict[str, Any]:
        config = {"model": self.model}
        if self.api_key_env_var:
            config["api_key_env_var"] = self.api_key_env_var
        return config

    @staticmethod
    def validate_config(config: dict[str, Any]) -> None:
        if not isinstance(config, dict):
            raise ValueError("Embedding config must be a map")
