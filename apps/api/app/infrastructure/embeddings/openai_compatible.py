"""OpenAI-compatible Embeddings provider."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import os
from typing import Any

import httpx

from app.application.embeddings.ports import (
    EmbeddingBatchResult,
    EmbeddingProviderError,
)
from app.infrastructure.env_reader import EnvReader

DEFAULT_EMBEDDING_BASE_URL = "https://api.openai.com/v1"
DEFAULT_EMBEDDING_TIMEOUT_SECONDS = 45.0
EMBEDDING_PROVIDER_ENV = "EMBEDDING_PROVIDER"
EMBEDDING_OPENAI_API_KEY_ENV = "EMBEDDING_OPENAI_API_KEY"
EMBEDDING_OPENAI_BASE_URL_ENV = "EMBEDDING_OPENAI_BASE_URL"
EMBEDDING_MODEL_ENV = "EMBEDDING_MODEL"
EMBEDDING_DIMENSION_ENV = "EMBEDDING_DIMENSION"
EMBEDDING_TIMEOUT_SECONDS_ENV = "EMBEDDING_TIMEOUT_SECONDS"


@dataclass(frozen=True)
class OpenAICompatibleEmbeddingSettings:
    api_key: str
    model: str
    dimension: int
    base_url: str = DEFAULT_EMBEDDING_BASE_URL
    timeout_seconds: float = DEFAULT_EMBEDDING_TIMEOUT_SECONDS

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
    ) -> "OpenAICompatibleEmbeddingSettings":
        env = EnvReader(os.environ if environ is None else environ)
        dimension_raw = env.optional(EMBEDDING_DIMENSION_ENV)
        if dimension_raw is None:
            raise EmbeddingProviderError(f"{EMBEDDING_DIMENSION_ENV} is required for asset RAG ingestion.")
        try:
            dimension = int(dimension_raw)
        except ValueError as exc:
            raise EmbeddingProviderError(f"{EMBEDDING_DIMENSION_ENV} must be an integer.") from exc
        if dimension <= 0:
            raise EmbeddingProviderError(f"{EMBEDDING_DIMENSION_ENV} must be positive.")

        model = env.optional(EMBEDDING_MODEL_ENV)
        if model is None:
            raise EmbeddingProviderError(f"{EMBEDDING_MODEL_ENV} is required for asset RAG ingestion.")

        return cls(
            api_key=env.first_of(EMBEDDING_OPENAI_API_KEY_ENV, "LLM_OPENAI_API_KEY", "OPENAI_API_KEY") or "",
            model=model,
            dimension=dimension,
            base_url=_normalize_base_url(
                env.first_of(EMBEDDING_OPENAI_BASE_URL_ENV, "LLM_OPENAI_BASE_URL", "OPENAI_BASE_URL")
                or DEFAULT_EMBEDDING_BASE_URL
            ),
            timeout_seconds=env.float(EMBEDDING_TIMEOUT_SECONDS_ENV, DEFAULT_EMBEDDING_TIMEOUT_SECONDS),
        )


class OpenAICompatibleEmbeddingProvider:
    def __init__(
        self,
        settings: OpenAICompatibleEmbeddingSettings,
        *,
        client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings
        self._client = client

    def embed_texts(self, texts: Sequence[str]) -> EmbeddingBatchResult:
        if not self._settings.api_key.strip():
            raise EmbeddingProviderError(f"{EMBEDDING_OPENAI_API_KEY_ENV} or OPENAI_API_KEY is required.")
        if not texts:
            return EmbeddingBatchResult(model=self._settings.model, dimension=self._settings.dimension, vectors=())
        payload = {"model": self._settings.model, "input": list(texts)}
        headers = {
            "Authorization": f"Bearer {self._settings.api_key}",
            "Content-Type": "application/json",
        }
        try:
            if self._client is not None:
                response = self._client.post(
                    f"{self._settings.base_url}/embeddings",
                    headers=headers,
                    json=payload,
                    timeout=self._settings.timeout_seconds,
                )
            else:
                with httpx.Client(timeout=self._settings.timeout_seconds) as client:
                    response = client.post(
                        f"{self._settings.base_url}/embeddings",
                        headers=headers,
                        json=payload,
                        timeout=self._settings.timeout_seconds,
                    )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise EmbeddingProviderError("Embedding provider request failed.") from exc

        try:
            body = response.json()
        except ValueError as exc:
            raise EmbeddingProviderError("Embedding provider returned invalid JSON.") from exc
        if not isinstance(body, dict):
            raise EmbeddingProviderError("Embedding provider response must be a JSON object.")
        vectors = _vectors_from_response(body)
        return EmbeddingBatchResult(
            model=str(body.get("model") or self._settings.model),
            dimension=self._settings.dimension,
            vectors=vectors,
        )


def _vectors_from_response(body: dict[str, Any]) -> tuple[tuple[float, ...], ...]:
    data = body.get("data")
    if not isinstance(data, list):
        raise EmbeddingProviderError("Embedding provider response is missing data.")
    ordered = sorted(data, key=lambda item: item.get("index", 0) if isinstance(item, dict) else 0)
    vectors: list[tuple[float, ...]] = []
    for item in ordered:
        if not isinstance(item, dict) or not isinstance(item.get("embedding"), list):
            raise EmbeddingProviderError("Embedding provider response item is invalid.")
        try:
            vectors.append(tuple(float(value) for value in item["embedding"]))
        except (TypeError, ValueError) as exc:
            raise EmbeddingProviderError("Embedding provider response contains non-numeric vector values.") from exc
    return tuple(vectors)


def _normalize_base_url(value: str) -> str:
    return value.rstrip("/")
