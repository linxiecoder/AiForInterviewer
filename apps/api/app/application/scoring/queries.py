"""Scoring queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetScoreResultQuery:
    owner_id: str
    score_result_id: str


@dataclass(frozen=True)
class ListScoreResultsQuery:
    owner_id: str
    target_type: str | None = None
    target_id: str | None = None
    target_parent_type: str | None = None
    target_parent_id: str | None = None
