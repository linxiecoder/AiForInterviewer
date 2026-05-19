"""Job match analysis HTTP adapters."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db_session_factory, get_job_match_analyzer, require_authenticated_actor
from app.api.envelope import success_envelope
from app.api.errors import raise_api_error
from app.application.job_match.commands import CreateJobMatchAnalysisCommand
from app.application.job_match.entities import JobMatchAnalysis
from app.application.job_match.ports import JobMatchAnalyzer
from app.application.job_match.queries import GetJobMatchAnalysisQuery, GetLatestJobMatchAnalysisQuery
from app.application.job_match.use_cases import JobMatchUseCases
from app.domain.auth.entities import CurrentActor
from app.infrastructure.db.repositories.bindings import SqlAlchemyBindingRepository
from app.infrastructure.db.repositories.job_match import SqlAlchemyJobMatchAnalysisRepository
from app.infrastructure.db.repositories.jobs import SqlAlchemyJobRepository
from app.infrastructure.db.repositories.resumes import SqlAlchemyResumeRepository
from app.schemas.job_match import CreateJobMatchAnalysisRequest, JobMatchAnalysisResponse, JobMatchResultPayload


router = APIRouter(prefix="/job-match-analyses", tags=["job-match"])


@router.post("")
async def create_job_match_analysis(
    payload: CreateJobMatchAnalysisRequest,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
    job_match_analyzer: JobMatchAnalyzer = Depends(get_job_match_analyzer),
) -> Any:
    use_cases = _use_cases(session_factory, job_match_analyzer=job_match_analyzer)
    result = use_cases.create(
        CreateJobMatchAnalysisCommand(
            owner_id=actor.owner_id,
            actor_id=actor.actor_id,
            binding_id=payload.resume_job_binding_id,
        )
    )
    if not result.is_success:
        error = result.error
        assert error is not None
        raise_api_error(
            status_code=_error_status(error.code),
            code=error.code,
            message=error.message,
            details=error.details,
            retryable=_error_retryable(error.code),
            user_action=_error_user_action(error.code),
        )
    return success_envelope(
        resource_type="job_match_analysis",
        data=_analysis_response(result.value).model_dump(mode="json"),
    )


@router.get("/latest")
async def get_latest_job_match_analysis(
    resume_job_binding_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    use_cases = _use_cases(session_factory, job_match_analyzer=None)
    result = use_cases.get_latest(
        GetLatestJobMatchAnalysisQuery(
            owner_id=actor.owner_id,
            binding_id=resume_job_binding_id,
        )
    )
    if not result.is_success:
        error = result.error
        assert error is not None
        raise_api_error(
            status_code=_error_status(error.code),
            code=error.code,
            message=error.message,
        )
    return success_envelope(
        resource_type="job_match_analysis",
        data=_analysis_response(result.value).model_dump(mode="json"),
    )


@router.get("/{analysis_id}")
async def get_job_match_analysis(
    analysis_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    use_cases = _use_cases(session_factory, job_match_analyzer=None)
    result = use_cases.get(
        GetJobMatchAnalysisQuery(owner_id=actor.owner_id, analysis_id=analysis_id)
    )
    if not result.is_success:
        error = result.error
        assert error is not None
        raise_api_error(
            status_code=_error_status(error.code),
            code=error.code,
            message=error.message,
        )
    return success_envelope(
        resource_type="job_match_analysis",
        data=_analysis_response(result.value).model_dump(mode="json"),
    )


def _use_cases(
    session_factory: sessionmaker[Session],
    *,
    job_match_analyzer: JobMatchAnalyzer | None,
) -> JobMatchUseCases:
    return JobMatchUseCases(
        job_match_repository=SqlAlchemyJobMatchAnalysisRepository(session_factory),
        binding_repository=SqlAlchemyBindingRepository(session_factory),
        resume_repository=SqlAlchemyResumeRepository(session_factory),
        job_repository=SqlAlchemyJobRepository(session_factory),
        job_match_analyzer=job_match_analyzer,
    )


def _analysis_response(analysis: JobMatchAnalysis | None) -> JobMatchAnalysisResponse:
    assert analysis is not None
    return JobMatchAnalysisResponse(
        analysis_id=analysis.analysis_id,
        resume_job_binding_id=analysis.binding_id,
        resume_id=analysis.resume_id,
        resume_version_id=analysis.resume_version_id,
        job_id=analysis.job_id,
        job_version_id=analysis.job_version_id,
        status=analysis.status,
        overall_score=analysis.overall_score,
        overall_level=analysis.overall_level,
        confidence=analysis.confidence,
        result_payload=JobMatchResultPayload.model_validate(analysis.result_payload_json),
        markdown_report_text=analysis.markdown_report_text,
        score_rule_version=analysis.score_rule_version,
        prompt_version=analysis.prompt_version,
        model_name=analysis.model_name,
        source_digest=analysis.source_digest,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
    )


def _error_status(code: str) -> int:
    if code == "provider_unavailable":
        return 502
    if code == "validation_failed":
        return 422
    if code == "not_found_or_inaccessible":
        return 404
    return 500


def _error_retryable(code: str) -> bool:
    return code == "provider_unavailable"


def _error_user_action(code: str) -> str | None:
    if code == "provider_unavailable":
        return "retry_later"
    return None
