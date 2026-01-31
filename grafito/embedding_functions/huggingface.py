"""Hugging Face Inference API embedding function."""

from __future__ import annotations

from typing import Any
import os

import numpy as np

from .base import EmbeddingFunction


class HuggingFaceEmbeddingFunction(EmbeddingFunction):
    """Embedding function for the Hugging Face Inference API."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        api_key_env_var: str | None = None,
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
                api_key = (
                    os.environ.get("HF_TOKEN")
                    or os.environ.get("HUGGINGFACE_HUB_TOKEN")
                    or os.environ.get("HUGGINGFACEHUB_API_TOKEN")
                    or os.environ.get("HUGGINGFACE_API_KEY")
                )
        if not api_key:
            raise ValueError(
                "Hugging Face API token not provided. Set HF_TOKEN or HUGGINGFACE_HUB_TOKEN, "
                "or pass api_key explicitly."
            )

        self._api_url = (
            "https://api-inference.huggingface.co/pipeline/feature-extraction/"
            f"{model_name}"
        )
        self._session = httpx.Client()
        self._session.headers.update({"Authorization": f"Bearer {api_key}"})

    def __call__(self, input: list[str]) -> list[list[float]]:
        response = self._session.post(
            self._api_url,
            json={"inputs": input, "options": {"wait_for_model": True}},
        )
        payload = response.json()
        if isinstance(payload, dict) and "error" in payload:
            raise ValueError(f"Hugging Face API error: {payload['error']}")
        return [np.array(embedding, dtype=np.float32).tolist() for embedding in payload]

    @staticmethod
    def name() -> str:
        return "huggingface"

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
        return HuggingFaceEmbeddingFunction(
            api_key_env_var=api_key_env_var, model_name=model_name
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
