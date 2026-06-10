"""Fetch persisted Polish candidates without exposing persistence details."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.application.common.result import ApplicationResult
from app.domain.shared.errors import DomainError


class _CandidateReader(Protocol):
    def get_candidate(self, *, owner_id: str, candidate_id: str) -> dict[str, Any] | None: ...


@dataclass(frozen=True)
class FetchPolishCandidateQuery:
    owner_id: str
    candidate_id: str


class PolishFetchCandidateUseCase:
    def __init__(self, repository: _CandidateReader) -> None:
        self._repository = repository

    def execute(self, query: FetchPolishCandidateQuery) -> ApplicationResult[dict[str, Any]]:
        candidate = self._repository.get_candidate(owner_id=query.owner_id, candidate_id=query.candidate_id)
        if candidate is None:
            return ApplicationResult(
                error=DomainError(
                    code="not_found_or_inaccessible",
                    message="Polish candidate not found",
                )
            )
        return ApplicationResult(value=candidate)

