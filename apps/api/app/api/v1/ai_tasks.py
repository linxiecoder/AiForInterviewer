"""AI task status and result route boundary."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, sessionmaker
from starlette.concurrency import run_in_threadpool

from app.api.deps import get_db_session_factory, require_authenticated_actor
from app.api.envelope import success_envelope
from app.api.errors import raise_api_error
from app.application.ai_tasks.queries import GetAiTaskQuery
from app.application.ai_tasks.use_cases import AiTaskUseCases
from app.domain.auth.entities import CurrentActor
from app.domain.shared.errors import DomainError
from app.infrastructure.db.repositories.ai_tasks import SqlAlchemyAiTaskRepository

router = APIRouter(prefix="/ai-tasks", tags=["ai-tasks"])


@router.get("/{ai_task_id}")
async def get_ai_task_status(
    ai_task_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    use_cases = _use_cases(session_factory)
    result = await run_in_threadpool(
        use_cases.get_status,
        GetAiTaskQuery(owner_id=actor.owner_id, ai_task_id=ai_task_id),
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(resource_type="ai_task", data=result.value)


@router.get("/{ai_task_id}/result")
async def get_ai_task_result(
    ai_task_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    use_cases = _use_cases(session_factory)
    result = await run_in_threadpool(
        use_cases.get_result,
        GetAiTaskQuery(owner_id=actor.owner_id, ai_task_id=ai_task_id),
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(resource_type="ai_task_result", data=result.value)


def _use_cases(session_factory: sessionmaker[Session]) -> AiTaskUseCases:
    return AiTaskUseCases(SqlAlchemyAiTaskRepository(session_factory))


def _raise_result_error(error: DomainError | None) -> None:
    if error is None:
        raise_api_error(status_code=500, code="internal_error", message="Unknown AI task error.")
    status_code = 404 if error.code == "not_found_or_inaccessible" else 422
    raise_api_error(status_code=status_code, code=error.code, message=error.message)
