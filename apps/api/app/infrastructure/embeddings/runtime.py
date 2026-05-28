"""Runtime wiring for embedding providers."""

from __future__ import annotations

import os
from collections.abc import Sequence

from app.application.embeddings.ports import (
    EmbeddingBatchResult,
    EmbeddingProvider,
    EmbeddingProviderError,
)
from app.infrastructure.embeddings.openai_compatible import (
    EMBEDDING_PROVIDER_ENV,
    OpenAICompatibleEmbeddingProvider,
    OpenAICompatibleEmbeddingSettings,
)


class UnavailableEmbeddingProvider:
    def __init__(self, reason: str) -> None:
        self.reason = reason

    def embed_texts(self, texts: Sequence[str]) -> EmbeddingBatchResult:
        raise EmbeddingProviderError(self.reason)


def build_embedding_provider_from_env() -> EmbeddingProvider:
    provider = (os.getenv(EMBEDDING_PROVIDER_ENV) or "openai_compatible").strip().lower()
    if provider in {"openai", "openai_compatible", "openai-compatible"}:
        try:
            return OpenAICompatibleEmbeddingProvider(OpenAICompatibleEmbeddingSettings.from_env())
        except EmbeddingProviderError as exc:
            return UnavailableEmbeddingProvider(str(exc))
    if provider in {"none", "disabled", "off"}:
        return UnavailableEmbeddingProvider("Embedding provider is disabled.")
    return UnavailableEmbeddingProvider(f"Unsupported {EMBEDDING_PROVIDER_ENV}: {provider or '<blank>'}.")
