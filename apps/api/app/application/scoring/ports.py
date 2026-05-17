"""Scoring ports."""

from typing import Protocol

from app.domain.shared.refs import ResourceRef


class ScoringRepository(Protocol):
    def get_ref(self, score_result_id: str) -> ResourceRef | None: ...

