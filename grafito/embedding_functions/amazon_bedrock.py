"""Amazon Bedrock embeddings API function."""

from __future__ import annotations

from typing import Any
import orjson

import numpy as np

from .base import EmbeddingFunction


class AmazonBedrockEmbeddingFunction(EmbeddingFunction):
    """Embedding function for Amazon Bedrock embeddings."""

    def __init__(
        self,
        session: Any | None = None,
        model_name: str = "amazon.titan-embed-text-v1",
        region_name: str | None = None,
        profile_name: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        aws_session_token: str | None = None,
        **client_kwargs: Any,
    ) -> None:
        try:
            import boto3
        except ImportError as exc:
            raise ValueError(
                "boto3 is not installed. Install with `pip install boto3`."
            ) from exc

        self.model_name = model_name
        for key, value in client_kwargs.items():
            if not isinstance(value, (str, int, float, bool, list, dict, tuple)):
                raise ValueError(f"Keyword argument {key} is not a primitive type")
        self.client_kwargs = client_kwargs

        session_args: dict[str, Any] = {}
        if region_name:
            session_args["region_name"] = region_name
        if profile_name:
            session_args["profile_name"] = profile_name
        if aws_access_key_id:
            session_args["aws_access_key_id"] = aws_access_key_id
        if aws_secret_access_key:
            session_args["aws_secret_access_key"] = aws_secret_access_key
        if aws_session_token:
            session_args["aws_session_token"] = aws_session_token

        self._session_args: dict[str, Any] = {}
        if session is None:
            session = boto3.Session(**session_args)
        if hasattr(session, "region_name") and session.region_name:
            self._session_args["region_name"] = session.region_name
        if hasattr(session, "profile_name") and session.profile_name:
            self._session_args["profile_name"] = session.profile_name

        self._client = session.client("bedrock-runtime", **client_kwargs)

    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = []
        for text in input:
            body = orjson.dumps({"inputText": text}).decode('utf-8')
            response = self._client.invoke_model(
                body=body,
                modelId=self.model_name,
                accept="application/json",
                contentType="application/json",
            )
            response_body = orjson.loads(response["body"].read())
            embedding = response_body.get("embedding")
            embeddings.append(np.array(embedding, dtype=np.float32).tolist())
        return embeddings

    @staticmethod
    def name() -> str:
        return "amazon_bedrock"

    def default_space(self) -> str:
        return "cosine"

    def supported_spaces(self) -> list[str]:
        return ["cosine", "l2", "ip"]

    @staticmethod
    def build_from_config(config: dict[str, Any]) -> "EmbeddingFunction":
        model_name = config.get("model_name")
        session_args = config.get("session_args") or {}
        client_kwargs = config.get("client_kwargs") or {}
        if not model_name:
            raise ValueError("model_name must be provided")
        return AmazonBedrockEmbeddingFunction(
            model_name=model_name,
            **session_args,
            **client_kwargs,
        )

    def get_config(self) -> dict[str, Any]:
        config = {"model_name": self.model_name}
        if self._session_args:
            config["session_args"] = dict(self._session_args)
        if self.client_kwargs:
            config["client_kwargs"] = dict(self.client_kwargs)
        return config

    @staticmethod
    def validate_config(config: dict[str, Any]) -> None:
        if not isinstance(config, dict):
            raise ValueError("Embedding config must be a map")
