"""Ollama local embeddings API function."""

from __future__ import annotations

from typing import Any
import os

import numpy as np

from .base import EmbeddingFunction


class OllamaEmbeddingFunction(EmbeddingFunction):
    """Embedding function for the Ollama local embeddings API."""

    def __init__(
        self,
        model: str = "nomic-embed-text",
        base_url: str | None = None,
    ) -> None:
        try:
            import httpx
        except ImportError as exc:
            raise ValueError(
                "httpx is not installed. Install with `pip install httpx`."
            ) from exc

        self.model = model
        self.base_url = base_url or os.environ.get("OLLAMA_HOST") or "http://localhost:11434"
        self._api_url = self.base_url.rstrip("/") + "/api/embeddings"
        self._session = httpx.Client()

    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = []
        for text in input:
            response = self._session.post(
                self._api_url,
                json={"model": self.model, "prompt": text},
            )
            payload = response.json()
            if isinstance(payload, dict) and "error" in payload:
                raise ValueError(f"Ollama API error: {payload['error']}")
            embeddings.append(np.array(payload["embedding"], dtype=np.float32).tolist())
        return embeddings

    @staticmethod
    def name() -> str:
        return "ollama"

    def default_space(self) -> str:
        return "cosine"

    def supported_spaces(self) -> list[str]:
        return ["cosine", "l2", "ip"]

    @staticmethod
    def build_from_config(config: dict[str, Any]) -> "EmbeddingFunction":
        model = config.get("model")
        base_url = config.get("base_url")
        if not model:
            raise ValueError("model must be provided")
        return OllamaEmbeddingFunction(model=model, base_url=base_url)

    def get_config(self) -> dict[str, Any]:
        config = {"model": self.model}
        if self.base_url:
            config["base_url"] = self.base_url
        return config

    @staticmethod
    def validate_config(config: dict[str, Any]) -> None:
        if not isinstance(config, dict):
            raise ValueError("Embedding config must be a map")
