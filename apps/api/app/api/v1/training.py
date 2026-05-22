"""Training recommendation HTTP adapters."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db_session_factory, require_authenticated_actor
from app.api.envelope import success_envelope
from app.api.errors import raise_api_error
from app.application.training.use_cases import TrainingUseCases
from app.domain.auth.entities import CurrentActor
from app.domain.shared.errors import DomainError
from app.infrastructure.db.repositories.training import SqlAlchemyTrainingRepository


router = APIRouter(prefix="/training-suggestions", tags=["training"])


@router.get("")
async def list_training_suggestions(
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    result = _use_cases(session_factory).list_training_suggestions(owner_id=actor.owner_id)
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(
        resource_type="training_suggestion_list",
        data=list(result.value or ()),
    )


@router.post("/{recommendation_id}/dismiss")
async def dismiss_training_suggestion(
    recommendation_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    result = _use_cases(session_factory).dismiss_training_suggestion(
        owner_id=actor.owner_id,
        actor_id=actor.actor_id,
        recommendation_id=recommendation_id,
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(resource_type="training_suggestion", data=result.value)


@router.post("/{recommendation_id}/tasks")
async def start_training_task(
    recommendation_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    result = _use_cases(session_factory).start_training_task(
        owner_id=actor.owner_id,
        actor_id=actor.actor_id,
        recommendation_id=recommendation_id,
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(resource_type="training_task", data=result.value)


@router.post("/{recommendation_id}/tasks/{task_id}/complete")
async def complete_training_task(
    recommendation_id: str,
    task_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    result = _use_cases(session_factory).complete_training_task(
        owner_id=actor.owner_id,
        recommendation_id=recommendation_id,
        task_id=task_id,
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(resource_type="training_task", data=result.value)


def _use_cases(session_factory: sessionmaker[Session]) -> TrainingUseCases:
    return TrainingUseCases(repository=SqlAlchemyTrainingRepository(session_factory))


def _raise_result_error(error: DomainError | None) -> None:
    if error is None:
        raise_api_error(status_code=500, code="internal_error", message="Unknown training error.")
    status_code = 404 if error.code == "not_found_or_inaccessible" else 409
    raise_api_error(status_code=status_code, code=error.code, message=error.message)
