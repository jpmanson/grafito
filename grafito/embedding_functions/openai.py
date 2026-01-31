"""OpenAI embeddings API function."""

from __future__ import annotations

from typing import Any
import os

import numpy as np

from .base import EmbeddingFunction


class OpenAIEmbeddingFunction(EmbeddingFunction):
    """Embedding function for the OpenAI embeddings API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "text-embedding-3-small",
        api_key_env_var: str | None = None,
        base_url: str = "https://api.openai.com/v1/embeddings",
    ) -> None:
        try:
            import httpx
        except ImportError as exc:
            raise ValueError(
                "httpx is not installed. Install with `pip install httpx`."
            ) from exc

        self.model = model
        self.api_key_env_var = api_key_env_var
        if api_key is None:
            if api_key_env_var:
                api_key = os.environ.get(api_key_env_var)
            else:
                api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key not provided. Set OPENAI_API_KEY or pass api_key explicitly."
            )

        self._api_url = base_url
        self._session = httpx.Client()
        self._session.headers.update({"Authorization": f"Bearer {api_key}"})

    def __call__(self, input: list[str]) -> list[list[float]]:
        response = self._session.post(
            self._api_url,
            json={"model": self.model, "input": input},
        )
        payload = response.json()
        if isinstance(payload, dict) and "error" in payload:
            raise ValueError(f"OpenAI API error: {payload['error']}")
        data = payload.get("data", [])
        return [np.array(item["embedding"], dtype=np.float32).tolist() for item in data]

    @staticmethod
    def name() -> str:
        return "openai"

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
        return OpenAIEmbeddingFunction(model=model, api_key_env_var=api_key_env_var)

    def get_config(self) -> dict[str, Any]:
        config = {"model": self.model}
        if self.api_key_env_var:
            config["api_key_env_var"] = self.api_key_env_var
        return config

    @staticmethod
    def validate_config(config: dict[str, Any]) -> None:
        if not isinstance(config, dict):
            raise ValueError("Embedding config must be a map")
