"""Review commands."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateReviewTaskCommand:
    source_ref_id: str
    review_type: str

