"""Google GenAI embeddings API function."""

from __future__ import annotations

from typing import Any
import os

import numpy as np

from .base import EmbeddingFunction


class GoogleGenAIEmbeddingFunction(EmbeddingFunction):
    """Embedding function for Google GenAI embeddings."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "text-embedding-004",
        api_key_env_var: str | None = None,
        vertexai: bool | None = None,
        project: str | None = None,
        location: str | None = None,
    ) -> None:
        try:
            import google.genai as genai
        except ImportError as exc:
            raise ValueError(
                "google-genai is not installed. Install with `pip install google-genai`."
            ) from exc

        self.model_name = model_name
        self.api_key_env_var = api_key_env_var
        self.vertexai = vertexai
        self.project = project
        self.location = location

        if api_key is None:
            if api_key_env_var:
                api_key = os.environ.get(api_key_env_var)
            else:
                api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Google GenAI API key not provided. Set GOOGLE_API_KEY or pass api_key explicitly."
            )

        self._client = genai.Client(
            api_key=api_key,
            vertexai=vertexai,
            project=project,
            location=location,
        )

    def __call__(self, input: list[str]) -> list[list[float]]:
        if not input:
            raise ValueError("Input documents cannot be empty")
        if not all(isinstance(doc, str) for doc in input):
            raise ValueError("All input documents must be strings")
        response = self._client.models.embed_content(
            model=self.model_name,
            contents=input,
        )
        embeddings = []
        for item in response.embeddings:
            embeddings.append(np.array(item.values, dtype=np.float32).tolist())
        return embeddings

    @staticmethod
    def name() -> str:
        return "google_genai"

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
        return GoogleGenAIEmbeddingFunction(
            api_key_env_var=api_key_env_var,
            model_name=model_name,
            vertexai=config.get("vertexai"),
            project=config.get("project"),
            location=config.get("location"),
        )

    def get_config(self) -> dict[str, Any]:
        config: dict[str, Any] = {"model_name": self.model_name}
        if self.api_key_env_var:
            config["api_key_env_var"] = self.api_key_env_var
        if self.vertexai is not None:
            config["vertexai"] = self.vertexai
        if self.project is not None:
            config["project"] = self.project
        if self.location is not None:
            config["location"] = self.location
        return config

    @staticmethod
    def validate_config(config: dict[str, Any]) -> None:
        if not isinstance(config, dict):
            raise ValueError("Embedding config must be a map")
