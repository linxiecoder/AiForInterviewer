"""Review domain ports."""

from typing import Protocol

from app.domain.reviews.entities import InterviewReview


class ReviewReader(Protocol):
    def get(self, review_id: str) -> InterviewReview | None: ...

