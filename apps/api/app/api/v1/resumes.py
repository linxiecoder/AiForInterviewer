"""Resume API boundary for list/detail operations."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, sessionmaker
from typing import Any

from app.api.deps import get_db_session_factory, require_authenticated_actor
from app.api.envelope import success_envelope
from app.api.errors import raise_api_error
from app.application.resumes.commands import CreateResumeCommand, UpdateResumeCommand
from app.application.resumes.use_cases import ResumeUseCases
from app.domain.auth.entities import CurrentActor
from app.infrastructure.db.repositories.resumes import SqlAlchemyResumeRepository
from app.schemas.resumes import CreateResumeRequest, ResumeDetail, ResumeSummary, UpdateResumeRequest

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.get("")
async def list_resumes(
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    use_cases = ResumeUseCases(repository=SqlAlchemyResumeRepository(session_factory))
    result = use_cases.list_for_owner(owner_id=actor.owner_id)
    if not result.is_success:
        error = result.error
        raise_api_error(
            status_code=_error_status(error.code),
            code=error.code,
            message=error.message,
        )

    data = [_to_resume_summary(resume) for resume in result.value or []]
    return success_envelope(resource_type="resume_list", data=data)


@router.post("", status_code=201)
async def create_resume(
    payload: CreateResumeRequest,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    use_cases = ResumeUseCases(repository=SqlAlchemyResumeRepository(session_factory))
    result = use_cases.create(
        CreateResumeCommand(
            owner_id=actor.owner_id,
            title=payload.title,
            markdown_text=payload.markdown_text,
        )
    )
    if not result.is_success:
        error = result.error
        raise_api_error(
            status_code=_error_status(error.code),
            code=error.code,
            message=error.message,
        )

    resume, _version = result.value
    return success_envelope(resource_type="resume_detail", data=_to_resume_summary(resume))


@router.get("/{resume_id}")
async def get_resume(
    resume_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    use_cases = ResumeUseCases(repository=SqlAlchemyResumeRepository(session_factory))
    result = use_cases.get_detail(owner_id=actor.owner_id, resume_id=resume_id)
    if not result.is_success:
        error = result.error
        raise_api_error(
            status_code=_error_status(error.code),
            code=error.code,
            message=error.message,
        )

    return success_envelope(resource_type="resume_detail", data=_to_resume_detail(*result.value))


@router.patch("/{resume_id}")
async def patch_resume(
    resume_id: str,
    payload: UpdateResumeRequest,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    use_cases = ResumeUseCases(repository=SqlAlchemyResumeRepository(session_factory))
    result = use_cases.update(
        UpdateResumeCommand(
            owner_id=actor.owner_id,
            resume_id=resume_id,
            title=payload.title,
            markdown_text=payload.markdown_text,
            base_version_ref=payload.base_version_ref,
        )
    )
    if not result.is_success:
        error = result.error
        raise_api_error(
            status_code=_error_status(error.code),
            code=error.code,
            message=error.message,
        )

    return success_envelope(resource_type="resume_detail", data=_to_resume_detail(*result.value))


def _to_resume_summary(resume) -> dict:
    current_version_ref = resume.current_version_ref
    current_version_ref_payload = None
    if current_version_ref is not None:
        current_version_ref_payload = {
            "resource_type": current_version_ref.resource_type,
            "resource_id": current_version_ref.resource_id,
            "version_id": current_version_ref.version_id,
        }

    return ResumeSummary(
        resume_id=resume.resume_id,
        title=resume.title,
        status=resume.status,
        current_version_ref=current_version_ref_payload,
        current_version_id=resume.current_version_ref.version_id,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
        file_name=resume.file_name,
    ).model_dump(mode="json")


def _to_resume_detail(resume, version) -> dict:
    summary = _to_resume_summary(resume)
    return ResumeDetail(
        **summary,
        markdown_text=version.markdown_text,
        derived_outline=None,
    ).model_dump(mode="json")


def _error_status(code: str) -> int:
    if code in {"stale_version_conflict", "idempotency_conflict"}:
        return 409
    if code == "validation_failed":
        return 422
    if code == "not_found_or_inaccessible":
        return 404
    return 400
