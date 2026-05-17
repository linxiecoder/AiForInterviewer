"""Idempotency boundary primitives."""

from dataclasses import dataclass


@dataclass(frozen=True)
class IdempotencyKey:
    value: str

