"""Cohere embeddings API function."""

from __future__ import annotations

from typing import Any
import os

import numpy as np

from .base import EmbeddingFunction


class CohereEmbeddingFunction(EmbeddingFunction):
    """Embedding function for the Cohere embeddings API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "embed-english-v3.0",
        api_key_env_var: str | None = None,
        base_url: str = "https://api.cohere.ai/v1/embed",
        input_type: str | None = "search_document",
    ) -> None:
        try:
            import httpx
        except ImportError as exc:
            raise ValueError(
                "httpx is not installed. Install with `pip install httpx`."
            ) from exc

        self.model = model
        self.api_key_env_var = api_key_env_var
        self.input_type = input_type
        if api_key is None:
            if api_key_env_var:
                api_key = os.environ.get(api_key_env_var)
            else:
                api_key = os.environ.get("COHERE_API_KEY")
        if not api_key:
            raise ValueError(
                "Cohere API key not provided. Set COHERE_API_KEY or pass api_key explicitly."
            )

        self._api_url = base_url
        self._session = httpx.Client()
        self._session.headers.update({"Authorization": f"Bearer {api_key}"})

    def __call__(self, input: list[str]) -> list[list[float]]:
        payload = {"model": self.model, "texts": input}
        if self.input_type:
            payload["input_type"] = self.input_type
        response = self._session.post(self._api_url, json=payload)
        data = response.json()
        if isinstance(data, dict) and "error" in data:
            raise ValueError(f"Cohere API error: {data['error']}")
        embeddings = data.get("embeddings", [])
        return [np.array(embedding, dtype=np.float32).tolist() for embedding in embeddings]

    @staticmethod
    def name() -> str:
        return "cohere"

    def default_space(self) -> str:
        return "cosine"

    def supported_spaces(self) -> list[str]:
        return ["cosine", "l2", "ip"]

    @staticmethod
    def build_from_config(config: dict[str, Any]) -> "EmbeddingFunction":
        model = config.get("model")
        api_key_env_var = config.get("api_key_env_var")
        input_type = config.get("input_type")
        if not model:
            raise ValueError("model must be provided")
        return CohereEmbeddingFunction(
            model=model,
            api_key_env_var=api_key_env_var,
            input_type=input_type,
        )

    def get_config(self) -> dict[str, Any]:
        config: dict[str, Any] = {"model": self.model}
        if self.api_key_env_var:
            config["api_key_env_var"] = self.api_key_env_var
        if self.input_type is not None:
            config["input_type"] = self.input_type
        return config

    @staticmethod
    def validate_config(config: dict[str, Any]) -> None:
        if not isinstance(config, dict):
            raise ValueError("Embedding config must be a map")
