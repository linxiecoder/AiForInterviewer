"""Persisted polish candidate HTTP adapters."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db_session_factory, require_authenticated_actor
from app.api.envelope import success_envelope
from app.api.errors import raise_api_error
from app.domain.auth.entities import CurrentActor
from app.infrastructure.db.repositories.polish_candidates import SqlAlchemyPolishCandidateRepository


router = APIRouter(prefix="/polish-candidates", tags=["polish-candidates"])


@router.get("")
async def list_polish_candidates(
    status: str | None = Query(default=None),
    candidate_type: str | None = Query(default=None),
    session_id: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    confidence_level: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    repository = SqlAlchemyPolishCandidateRepository(session_factory)
    candidates = repository.list_candidates(
        owner_id=actor.owner_id,
        status=status,
        candidate_type=candidate_type,
        session_id=session_id,
        source_type=source_type,
        confidence_level=confidence_level,
        limit=limit,
        offset=offset,
    )
    return success_envelope(resource_type="polish_candidate_list", data=list(candidates))


@router.get("/{candidate_id}")
async def get_polish_candidate(
    candidate_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    repository = SqlAlchemyPolishCandidateRepository(session_factory)
    candidate = repository.get_candidate(owner_id=actor.owner_id, candidate_id=candidate_id)
    if candidate is None:
        raise_api_error(
            status_code=404,
            code="not_found_or_inaccessible",
            message="Polish candidate not found",
        )
    return success_envelope(resource_type="polish_candidate", data=candidate)
