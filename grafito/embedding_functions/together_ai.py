"""Together AI embeddings API function."""

from __future__ import annotations

from typing import Any
import os

import numpy as np

from .base import EmbeddingFunction


class TogetherAIEmbeddingFunction(EmbeddingFunction):
    """Embedding function for the Together AI embeddings API."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "togethercomputer/m2-bert-80M-8k-retrieval",
        api_key_env_var: str | None = None,
        base_url: str = "https://api.together.xyz/v1/embeddings",
    ) -> None:
        try:
            import httpx
        except ImportError as exc:
            raise ValueError(
                "httpx is not installed. Install with `pip install httpx`."
            ) from exc

        self.model_name = model_name
        self.api_key_env_var = api_key_env_var
        if api_key is None:
            if api_key_env_var:
                api_key = os.environ.get(api_key_env_var)
            else:
                api_key = os.environ.get("TOGETHER_API_KEY")
        if not api_key:
            raise ValueError(
                "Together API key not provided. Set TOGETHER_API_KEY or pass api_key explicitly."
            )

        self._api_url = base_url
        self._session = httpx.Client()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "accept": "application/json",
            }
        )

    def __call__(self, input: list[str]) -> list[list[float]]:
        if not input:
            raise ValueError("Input is required")
        if not isinstance(input, list):
            raise ValueError("Input must be a list")
        if not all(isinstance(item, str) for item in input):
            raise ValueError("All items in input must be strings")

        response = self._session.post(
            self._api_url,
            json={"model": self.model_name, "input": input},
        )
        data = response.json()
        if isinstance(data, dict) and "error" in data:
            raise ValueError(f"Together AI API error: {data['error']}")

        embeddings = [item["embedding"] for item in data.get("data", [])]
        return [
            np.array(embedding, dtype=np.float32).tolist() for embedding in embeddings
        ]

    @staticmethod
    def name() -> str:
        return "together_ai"

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
        return TogetherAIEmbeddingFunction(
            model_name=model_name,
            api_key_env_var=api_key_env_var,
        )

    def get_config(self) -> dict[str, Any]:
        config = {"model_name": self.model_name}
        if self.api_key_env_var:
            config["api_key_env_var"] = self.api_key_env_var
        return config

    @staticmethod
    def validate_config(config: dict[str, Any]) -> None:
        if not isinstance(config, dict):
            raise ValueError("Embedding config must be a map")
