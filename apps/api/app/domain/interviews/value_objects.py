"""Interview value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SessionMode:
    value: str

