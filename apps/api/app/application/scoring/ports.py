"""Scoring ports."""

from typing import Any, Protocol

from app.domain.shared.refs import ResourceRef


class ScoringRepository(Protocol):
    def get_ref(self, score_result_id: str) -> ResourceRef | None: ...

    def add_score_result(self, score_result: dict[str, Any]) -> dict[str, Any]: ...

    def get_score_result(self, *, owner_id: str, score_result_id: str) -> dict[str, Any] | None: ...

    def list_score_results(
        self,
        *,
        owner_id: str,
        target_type: str | None = None,
        target_id: str | None = None,
        target_parent_type: str | None = None,
        target_parent_id: str | None = None,
    ) -> tuple[dict[str, Any], ...]: ...
