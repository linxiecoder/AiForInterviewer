"""Application result object shared by use cases."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from app.domain.shared.errors import DomainError

T = TypeVar("T")


@dataclass(frozen=True)
class ApplicationResult(Generic[T]):
    value: T | None = None
    error: DomainError | None = None

    @property
    def is_success(self) -> bool:
        return self.error is None

