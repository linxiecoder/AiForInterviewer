"""Scoring domain ports."""

from typing import Protocol

from app.domain.scoring.entities import ScoreResult


class ScoreResultReader(Protocol):
    def get(self, score_result_id: str) -> ScoreResult | None: ...

