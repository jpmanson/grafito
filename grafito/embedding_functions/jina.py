"""Jina AI embeddings API function."""

from __future__ import annotations

from typing import Any
import os

import numpy as np

from .base import EmbeddingFunction


class JinaEmbeddingFunction(EmbeddingFunction):
    """Embedding function for the Jina AI embeddings API."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "jina-embeddings-v2-base-en",
        api_key_env_var: str | None = None,
        task: str | None = None,
        late_chunking: bool | None = None,
        truncate: bool | None = None,
        dimensions: int | None = None,
        embedding_type: str | None = None,
        normalized: bool | None = None,
        query_config: dict[str, Any] | None = None,
        base_url: str = "https://api.jina.ai/v1/embeddings",
    ) -> None:
        try:
            import httpx
        except ImportError as exc:
            raise ValueError(
                "httpx is not installed. Install with `pip install httpx`."
            ) from exc

        self.model_name = model_name
        self.api_key_env_var = api_key_env_var
        self.task = task
        self.late_chunking = late_chunking
        self.truncate = truncate
        self.dimensions = dimensions
        self.embedding_type = embedding_type
        self.normalized = normalized
        self.query_config = query_config

        if api_key is None:
            if api_key_env_var:
                api_key = os.environ.get(api_key_env_var)
            else:
                api_key = os.environ.get("JINA_API_KEY")
        if not api_key:
            raise ValueError(
                "Jina API key not provided. Set JINA_API_KEY or pass api_key explicitly."
            )

        self._api_url = base_url
        self._session = httpx.Client()
        self._session.headers.update({"Authorization": f"Bearer {api_key}"})

    def __call__(self, input: list[str]) -> list[list[float]]:
        payload = self._build_payload(input, is_query=False)
        response = self._session.post(self._api_url, json=payload)
        data = response.json()
        return self._convert_response(data)

    def embed_query(self, input: list[str]) -> list[list[float]]:
        payload = self._build_payload(input, is_query=True)
        response = self._session.post(self._api_url, json=payload)
        data = response.json()
        return self._convert_response(data)

    def _build_payload(self, input: list[str], is_query: bool) -> dict[str, Any]:
        payload: dict[str, Any] = {"input": input, "model": self.model_name}
        if self.task is not None:
            payload["task"] = self.task
        if self.late_chunking is not None:
            payload["late_chunking"] = self.late_chunking
        if self.truncate is not None:
            payload["truncate"] = self.truncate
        if self.dimensions is not None:
            payload["dimensions"] = self.dimensions
        if self.embedding_type is not None:
            payload["embedding_type"] = self.embedding_type
        if self.normalized is not None:
            payload["normalized"] = self.normalized
        if is_query and self.query_config:
            payload.update(self.query_config)
        return payload

    def _convert_response(self, data: Any) -> list[list[float]]:
        if isinstance(data, dict) and "error" in data:
            raise ValueError(f"Jina API error: {data['error']}")
        if "data" not in data:
            raise ValueError("Jina API response missing data")
        sorted_items = sorted(data["data"], key=lambda item: item.get("index", 0))
        return [
            np.array(item["embedding"], dtype=np.float32).tolist()
            for item in sorted_items
        ]

    @staticmethod
    def name() -> str:
        return "jina"

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
        return JinaEmbeddingFunction(
            api_key_env_var=api_key_env_var,
            model_name=model_name,
            task=config.get("task"),
            late_chunking=config.get("late_chunking"),
            truncate=config.get("truncate"),
            dimensions=config.get("dimensions"),
            embedding_type=config.get("embedding_type"),
            normalized=config.get("normalized"),
            query_config=config.get("query_config"),
        )

    def get_config(self) -> dict[str, Any]:
        config: dict[str, Any] = {"model_name": self.model_name}
        if self.api_key_env_var:
            config["api_key_env_var"] = self.api_key_env_var
        if self.task is not None:
            config["task"] = self.task
        if self.late_chunking is not None:
            config["late_chunking"] = self.late_chunking
        if self.truncate is not None:
            config["truncate"] = self.truncate
        if self.dimensions is not None:
            config["dimensions"] = self.dimensions
        if self.embedding_type is not None:
            config["embedding_type"] = self.embedding_type
        if self.normalized is not None:
            config["normalized"] = self.normalized
        if self.query_config is not None:
            config["query_config"] = self.query_config
        return config

    @staticmethod
    def validate_config(config: dict[str, Any]) -> None:
        if not isinstance(config, dict):
            raise ValueError("Embedding config must be a map")
