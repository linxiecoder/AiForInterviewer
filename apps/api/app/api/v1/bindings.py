"""Resume-job binding HTTP adapters."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, sessionmaker
from typing import Any

from app.api.deps import get_db_session_factory, require_authenticated_actor
from app.api.envelope import success_envelope
from app.api.errors import raise_api_error
from app.application.bindings.commands import CreateBindingCommand, DeleteBindingCommand
from app.application.bindings.queries import GetBindingQuery
from app.application.bindings.use_cases import BindingUseCases
from app.domain.auth.entities import CurrentActor
from app.infrastructure.db.repositories.bindings import SqlAlchemyBindingRepository
from app.infrastructure.db.repositories.jobs import SqlAlchemyJobRepository
from app.schemas.bindings import CreateBindingRequest, DeleteBindingRequest, JobResumeBindingResponse
from app.schemas.refs import OwnerRef, VersionRef

router = APIRouter(prefix="/resume-job-bindings", tags=["bindings"])


@router.post("")
async def create_binding(
    payload: CreateBindingRequest,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    binding_use_case = BindingUseCases(
        binding_repository=SqlAlchemyBindingRepository(session_factory),
        job_repository=SqlAlchemyJobRepository(session_factory),
    )
    command = CreateBindingCommand(
        owner_id=actor.owner_id,
        resume_id=payload.resume_id,
        job_id=payload.job_id,
        resume_version_id=payload.resume_version_id,
        job_version_id=payload.job_version_id,
    )

    result = binding_use_case.create(command)
    if not result.is_success:
        error = result.error
        raise_api_error(
            status_code=_error_status(error.code),
            code=error.code,
            message=error.message,
        )

    return success_envelope(resource_type="job_resume_binding", data=_binding_response(result.value))


@router.delete("/{binding_id}")
async def delete_binding(
    binding_id: str,
    payload: DeleteBindingRequest,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    binding_use_case = BindingUseCases(
        binding_repository=SqlAlchemyBindingRepository(session_factory),
        job_repository=SqlAlchemyJobRepository(session_factory),
    )
    query = GetBindingQuery(owner_id=actor.owner_id, binding_id=binding_id)
    command = DeleteBindingCommand(
        owner_id=actor.owner_id,
        base_version_ref=payload.base_version_ref,
        record_version=payload.record_version,
        reason=payload.reason,
    )
    result = binding_use_case.delete(query, command)

    if not result.is_success:
        error = result.error
        raise_api_error(
            status_code=_error_status(error.code),
            code=error.code,
            message=error.message,
        )

    return success_envelope(resource_type="job_resume_binding", data=_binding_response(result.value))


def _binding_response(binding) -> dict:
    return JobResumeBindingResponse(
        binding_id=binding.binding_id,
        resume_ref=VersionRef(
            resource_type="resume",
            resource_id=binding.resume_id,
            version_id=binding.resume_version_id,
        ),
        job_ref=VersionRef(
            resource_type="job",
            resource_id=binding.job_id,
            version_id=binding.job_version_id,
        ),
        binding_status=binding.status,
        created_at=binding.created_at,
        unbound_at=binding.unbound_at,
        unbound_by=OwnerRef(owner_id=binding.unbound_by) if binding.unbound_by else None,
        record_version=binding.record_version,
        resume_job_binding_id=binding.binding_id,
        preserved_history_refs=[],
        affected_default_entry_summary=None,
    ).model_dump(mode="json")


def _error_status(code: str) -> int:
    if code in {"stale_version_conflict", "idempotency_conflict"}:
        return 409
    if code == "validation_failed":
        return 422
    if code == "not_found_or_inaccessible":
        return 404
    return 400
