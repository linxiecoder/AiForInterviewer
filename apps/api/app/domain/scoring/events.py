"""Scoring domain events."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreResultCreated:
    score_result_id: str

