"""Review queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetReviewQuery:
    review_id: str

