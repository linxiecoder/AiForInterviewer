"""Polish repository facade for M2.5 use case slices."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.db.repositories.polish import SqlAlchemyPolishRepository
from app.infrastructure.db.repositories.polish_candidates import (
    PolishCandidateActionError,
    SqlAlchemyPolishCandidateRepository,
)


class PolishRepository:
    def __init__(
        self,
        session_factory: sessionmaker[Session] | None = None,
        *,
        core_repository: SqlAlchemyPolishRepository | None = None,
        candidate_repository: SqlAlchemyPolishCandidateRepository | None = None,
    ) -> None:
        self._core_repository = core_repository or SqlAlchemyPolishRepository(session_factory)
        self._candidate_repository = candidate_repository or SqlAlchemyPolishCandidateRepository(session_factory)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._core_repository, name)

    def list_candidates(
        self,
        *,
        owner_id: str,
        status: str | None = None,
        candidate_type: str | None = None,
        session_id: str | None = None,
        source_type: str | None = None,
        confidence_level: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[dict[str, Any], ...]:
        return self._candidate_repository.list_candidates(
            owner_id=owner_id,
            status=status,
            candidate_type=candidate_type,
            session_id=session_id,
            source_type=source_type,
            confidence_level=confidence_level,
            limit=limit,
            offset=offset,
        )

    def get_candidate(self, *, owner_id: str, candidate_id: str) -> dict[str, Any] | None:
        return self._candidate_repository.get_candidate(owner_id=owner_id, candidate_id=candidate_id)

    def confirm_candidate(self, *, owner_id: str, actor_id: str, candidate_id: str) -> dict[str, Any]:
        return self._candidate_repository.confirm_candidate(
            owner_id=owner_id,
            actor_id=actor_id,
            candidate_id=candidate_id,
        )

    def dismiss_candidate(self, *, owner_id: str, actor_id: str, candidate_id: str) -> dict[str, Any]:
        return self._candidate_repository.dismiss_candidate(
            owner_id=owner_id,
            actor_id=actor_id,
            candidate_id=candidate_id,
        )

    def merge_candidate(
        self,
        *,
        owner_id: str,
        actor_id: str,
        candidate_id: str,
        target_candidate_id: str,
    ) -> dict[str, Any]:
        return self._candidate_repository.merge_candidate(
            owner_id=owner_id,
            actor_id=actor_id,
            candidate_id=candidate_id,
            target_candidate_id=target_candidate_id,
        )

    def archive_candidate(self, *, owner_id: str, actor_id: str, candidate_id: str) -> dict[str, Any]:
        return self._candidate_repository.archive_candidate(
            owner_id=owner_id,
            actor_id=actor_id,
            candidate_id=candidate_id,
        )


__all__ = ["PolishCandidateActionError", "PolishRepository"]

