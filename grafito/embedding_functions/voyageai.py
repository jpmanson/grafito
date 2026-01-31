"""Voyage AI embeddings API function."""

from __future__ import annotations

from typing import Any
import os

import numpy as np

from .base import EmbeddingFunction


class VoyageAIEmbeddingFunction(EmbeddingFunction):
    """Embedding function for the Voyage AI API."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "voyage-large-2",
        api_key_env_var: str | None = None,
        input_type: str | None = None,
        truncation: bool = True,
    ) -> None:
        try:
            import voyageai
        except ImportError as exc:
            raise ValueError(
                "voyageai is not installed. Install with `pip install voyageai`."
            ) from exc

        self.model_name = model_name
        self.api_key_env_var = api_key_env_var
        self.input_type = input_type
        self.truncation = truncation

        if api_key is None:
            if api_key_env_var:
                api_key = os.environ.get(api_key_env_var)
            else:
                api_key = os.environ.get("VOYAGE_API_KEY")
        if not api_key:
            raise ValueError(
                "Voyage API key not provided. Set VOYAGE_API_KEY or pass api_key explicitly."
            )

        self._client = voyageai.Client(api_key=api_key)

    def __call__(self, input: list[str]) -> list[list[float]]:
        response = self._client.embed(
            texts=input,
            model=self.model_name,
            input_type=self.input_type,
            truncation=self.truncation,
        )
        return [
            np.array(embedding, dtype=np.float32).tolist()
            for embedding in response.embeddings
        ]

    @staticmethod
    def name() -> str:
        return "voyageai"

    def default_space(self) -> str:
        return "cosine"

    def supported_spaces(self) -> list[str]:
        return ["cosine", "l2", "ip"]

    @staticmethod
    def build_from_config(config: dict[str, Any]) -> "EmbeddingFunction":
        model_name = config.get("model_name")
        api_key_env_var = config.get("api_key_env_var")
        if not model_name:
            raise ValueError("model_name must be provided")
        return VoyageAIEmbeddingFunction(
            api_key_env_var=api_key_env_var,
            model_name=model_name,
            input_type=config.get("input_type"),
            truncation=config.get("truncation", True),
        )

    def get_config(self) -> dict[str, Any]:
        config: dict[str, Any] = {"model_name": self.model_name}
        if self.api_key_env_var:
            config["api_key_env_var"] = self.api_key_env_var
        if self.input_type is not None:
            config["input_type"] = self.input_type
        config["truncation"] = self.truncation
        return config

    @staticmethod
    def validate_config(config: dict[str, Any]) -> None:
        if not isinstance(config, dict):
            raise ValueError("Embedding config must be a map")
