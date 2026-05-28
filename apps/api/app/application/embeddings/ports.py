"""Embedding provider port."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


class EmbeddingProviderError(RuntimeError):
    """Raised when embedding generation cannot complete."""


@dataclass(frozen=True)
class EmbeddingBatchResult:
    model: str
    dimension: int
    vectors: tuple[tuple[float, ...], ...]


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: Sequence[str]) -> EmbeddingBatchResult: ...
