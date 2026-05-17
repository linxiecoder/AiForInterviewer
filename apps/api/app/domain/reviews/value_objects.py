"""Review value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewType:
    value: str

