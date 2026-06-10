"""Scoring HTTP adapters."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db_session_factory, require_authenticated_actor
from app.api.envelope import success_envelope
from app.api.errors import raise_api_error
from app.application.scoring.commands import CreateScoreResultCommand
from app.application.scoring.queries import GetScoreResultQuery, ListScoreResultsQuery
from app.application.scoring.use_cases import ScoringUseCases
from app.domain.auth.entities import CurrentActor
from app.domain.shared.errors import DomainError
from app.infrastructure.db.repositories.scoring import SqlAlchemyScoringRepository
from app.schemas.scoring import CreateScoreResultRequest

router = APIRouter(prefix="/scoring-results", tags=["scoring"])


@router.post("")
async def create_score_result(
    payload: CreateScoreResultRequest,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    result = _use_cases(session_factory).create(
        CreateScoreResultCommand(
            owner_id=actor.owner_id,
            actor_id=actor.actor_id,
            score_type=payload.score_type,
            target_type=payload.target_type,
            target_id=payload.target_id,
            target_parent_type=payload.target_parent_type,
            target_parent_id=payload.target_parent_id,
            source_module=payload.source_module,
            source_event=payload.source_event,
            rubric_version=payload.rubric_version,
            overall_score=payload.overall_score,
            dimensions=tuple(item.model_dump(mode="python") for item in payload.dimensions),
            evidence_links=tuple(payload.evidence_links),
            next_action_type=payload.next_action_type,
        )
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(resource_type="score_result", data=result.value)


@router.get("")
async def list_score_results(
    target_type: str | None = Query(default=None),
    target_id: str | None = Query(default=None),
    target_parent_type: str | None = Query(default=None),
    target_parent_id: str | None = Query(default=None),
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    result = _use_cases(session_factory).list(
        ListScoreResultsQuery(
            owner_id=actor.owner_id,
            target_type=target_type,
            target_id=target_id,
            target_parent_type=target_parent_type,
            target_parent_id=target_parent_id,
        )
    )
    if not result.is_success:
        _raise_result_error(result.error)
    envelope = success_envelope(resource_type="score_result_list", data=list(result.value or ()))
    if target_parent_type is not None or target_parent_id is not None:
        envelope.meta = {
            "target_parent_type": target_parent_type,
            "target_parent_id": target_parent_id,
        }
    return envelope


@router.get("/{score_result_id}")
async def get_score_result(
    score_result_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    result = _use_cases(session_factory).get(
        GetScoreResultQuery(owner_id=actor.owner_id, score_result_id=score_result_id)
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(resource_type="score_result", data=result.value)


def _use_cases(session_factory: sessionmaker[Session]) -> ScoringUseCases:
    return ScoringUseCases(repository=SqlAlchemyScoringRepository(session_factory))


def _raise_result_error(error: DomainError | None) -> None:
    if error is None:
        raise_api_error(status_code=500, code="internal_error", message="Unknown scoring error.")
    raise_api_error(
        status_code=_error_status(error.code),
        code=error.code,
        message=error.message,
        details=error.details,
        retryable=error.retryable,
        user_action=error.user_action,
    )


def _error_status(code: str) -> int:
    if code == "not_found_or_inaccessible":
        return 404
    if code == "validation_failed":
        return 422
    if code.endswith("_conflict"):
        return 409
    return 400
