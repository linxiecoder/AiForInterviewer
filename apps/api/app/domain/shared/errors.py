"""Domain errors that can be mapped by adapters."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DomainError(Exception):
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    retryable: bool = False
    user_action: str | None = None

