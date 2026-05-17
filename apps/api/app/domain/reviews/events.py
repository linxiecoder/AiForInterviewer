"""Review domain events."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewCreated:
    review_id: str

