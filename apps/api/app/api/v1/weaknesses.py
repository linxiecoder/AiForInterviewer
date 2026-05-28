"""Weakness HTTP adapters."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db_session_factory, require_authenticated_actor
from app.api.envelope import success_envelope
from app.api.errors import raise_api_error
from app.application.weaknesses.use_cases import WeaknessUseCases
from app.domain.auth.entities import CurrentActor
from app.domain.shared.errors import DomainError
from app.infrastructure.db.repositories.weaknesses import SqlAlchemyWeaknessRepository
from app.schemas.weaknesses import UpdateWeaknessStatusRequest

router = APIRouter(prefix="/weaknesses", tags=["weaknesses"])


@router.get("")
async def list_weaknesses(
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    q: str | None = Query(default=None),
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    result = _use_cases(session_factory).list_weaknesses(
        owner_id=actor.owner_id,
        status=status,
        severity=severity,
        q=q,
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(resource_type="weakness_list", data=list(result.value or ()))


@router.get("/{weakness_id}")
async def get_weakness(
    weakness_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    result = _use_cases(session_factory).get_weakness(
        owner_id=actor.owner_id,
        weakness_id=weakness_id,
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(resource_type="weakness_detail", data=result.value)


@router.post("/{weakness_id}/status")
async def update_weakness_status(
    weakness_id: str,
    payload: UpdateWeaknessStatusRequest,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    result = _use_cases(session_factory).update_status(
        owner_id=actor.owner_id,
        actor_id=actor.actor_id,
        weakness_id=weakness_id,
        status=payload.status,
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(resource_type="weakness_detail", data=result.value)


def _use_cases(session_factory: sessionmaker[Session]) -> WeaknessUseCases:
    return WeaknessUseCases(repository=SqlAlchemyWeaknessRepository(session_factory))


def _raise_result_error(error: DomainError | None) -> None:
    if error is None:
        raise_api_error(status_code=500, code="internal_error", message="Unknown weakness error.")
    status_code = _error_status(error.code)
    raise_api_error(status_code=status_code, code=error.code, message=error.message)


def _error_status(code: str) -> int:
    if code == "not_found_or_inaccessible":
        return 404
    if code == "validation_failed":
        return 422
    if code.endswith("_conflict"):
        return 409
    return 400
