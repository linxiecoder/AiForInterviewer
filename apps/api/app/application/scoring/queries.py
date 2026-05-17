"""Scoring queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetScoreResultQuery:
    score_result_id: str

