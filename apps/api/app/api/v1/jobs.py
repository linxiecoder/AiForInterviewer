"""Job HTTP adapters."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from typing import Any

from app.api.deps import require_authenticated_actor
from app.api.envelope import success_envelope
from app.api.errors import raise_api_error
from app.application.bindings.use_cases import BindingUseCases
from app.application.jobs.commands import CreateJobCommand, UpdateJobCommand
from app.application.jobs.queries import GetJobQuery, ListJobsQuery
from app.application.jobs.use_cases import JobUseCases
from app.domain.auth.entities import CurrentActor
from app.application.jobs.queries import GetJobQuery as AppGetJobQuery
from app.infrastructure.db.repositories.bindings import SqlAlchemyBindingRepository
from app.infrastructure.db.repositories.jobs import SqlAlchemyJobRepository
from app.schemas.bindings import JobResumeBindingResponse
from app.schemas.refs import VersionRef
from app.schemas.jobs import CreateJobRequest, JobBindingSummary, JobDetail, JobMatchSummary, JobSummary, UpdateJobRequest

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("")
async def list_jobs(actor: CurrentActor = Depends(require_authenticated_actor)) -> Any:
    jobs_use_case = JobUseCases(repository=SqlAlchemyJobRepository())
    query = ListJobsQuery(owner_id=actor.owner_id)
    jobs_result = jobs_use_case.list_by_owner(query)
    if not jobs_result.is_success:
        error = jobs_result.error
        assert error is not None
        raise_api_error(
            status_code=500,
            code="internal_error",
            message=error.message,
        )

    binding_summary = _binding_summary_builder(actor.owner_id)
    summaries = [
        _to_job_summary(job, jobs_result.value or [], binding_summary)
        for job in jobs_result.value or []
    ]
    return success_envelope(resource_type="job_list", data=summaries)


@router.post("")
async def create_job(
    payload: CreateJobRequest,
    actor: CurrentActor = Depends(require_authenticated_actor),
) -> Any:
    jobs_use_case = JobUseCases(repository=SqlAlchemyJobRepository())
    command = CreateJobCommand(
        owner_id=actor.owner_id,
        title=payload.title,
        company=payload.company,
        department=payload.department,
        responsibilities=payload.responsibilities,
        requirements=payload.requirements,
        other_notes=payload.other_notes,
        application_status=payload.application_status,
    )
    result = jobs_use_case.create(command)
    if not result.is_success:
        error = result.error
        raise_api_error(
            status_code=_error_status(error.code),
            code=error.code,
            message=error.message,
        )

    return success_envelope(resource_type="job_detail", data=_to_job_detail(*result.value, actor.owner_id))


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
) -> Any:
    jobs_use_case = JobUseCases(repository=SqlAlchemyJobRepository())
    result = jobs_use_case.get(GetJobQuery(owner_id=actor.owner_id, job_id=job_id))
    if not result.is_success:
        error = result.error
        raise_api_error(
            status_code=_error_status(error.code),
            code=error.code,
            message=error.message,
        )
    return success_envelope(resource_type="job_detail", data=_to_job_detail(*result.value, actor.owner_id))


@router.patch("/{job_id}")
async def patch_job(
    job_id: str,
    payload: UpdateJobRequest,
    actor: CurrentActor = Depends(require_authenticated_actor),
) -> Any:
    jobs_use_case = JobUseCases(repository=SqlAlchemyJobRepository())
    command = UpdateJobCommand(
        owner_id=actor.owner_id,
        title=payload.title,
        company=payload.company,
        department=payload.department,
        responsibilities=payload.responsibilities,
        requirements=payload.requirements,
        other_notes=payload.other_notes,
        application_status=payload.application_status,
        status=payload.status,
        base_version_ref=payload.base_version_ref,
        record_version=payload.record_version,
    )
    query = AppGetJobQuery(owner_id=actor.owner_id, job_id=job_id)
    result = jobs_use_case.update(query, command)
    if not result.is_success:
        error = result.error
        raise_api_error(
            status_code=_error_status(error.code),
            code=error.code,
            message=error.message,
        )

    return success_envelope(resource_type="job_detail", data=_to_job_detail(*result.value, actor.owner_id))


def _to_job_summary(job, jobs: list[object], binding_summary_builder) -> dict:
    binding_summary = binding_summary_builder(job)
    return JobSummary(
        job_id=job.job_id,
        title=job.title,
        company=job.company,
        application_status=job.application_status,
        current_version_ref=_job_version_ref(job),
        archived_at=job.archived_at,
        binding_summary=binding_summary,
        latest_match_summary=JobMatchSummary(status="match_not_generated"),
        status=job.status,
        record_version=job.record_version,
        created_at=job.created_at,
        updated_at=job.updated_at,
    ).model_dump(mode="json")


def _to_job_detail(job, version, owner_id: str) -> dict:
    binding_summary = _binding_summary_builder(owner_id)(job)
    return JobDetail(
        job_id=job.job_id,
        title=job.title,
        company=job.company,
        department=job.department,
        responsibilities=list(version.responsibilities),
        requirements=list(version.requirements),
        other_notes=version.other_notes,
        application_status=job.application_status,
        current_version_ref=_job_version_ref_from(job, version),
        binding_summary=binding_summary,
        latest_match_summary=JobMatchSummary(status="match_not_generated"),
        status=job.status,
        record_version=job.record_version,
        archived_at=job.archived_at,
        created_at=job.created_at,
        updated_at=job.updated_at,
    ).model_dump(mode="json")


def _binding_summary_builder(owner_id: str):
    binding_usecase = BindingUseCases(
        binding_repository=SqlAlchemyBindingRepository(),
        job_repository=SqlAlchemyJobRepository(),
    )

    def _build(job):
        bindings = binding_usecase._binding_repository.list_by_job(owner_id=owner_id, job_id=job.job_id)
        active = [binding for binding in bindings if binding.status == "active"]
        if not active:
            return JobBindingSummary(
                status="not_bound",
                resume_job_binding_id=None,
                resume_id=None,
                resume_title=None,
                resume_version_ref=None,
                bound_at=None,
            )

        latest = sorted(active, key=lambda item: item.updated_at, reverse=True)[0]
        return JobBindingSummary(
            status="bound",
            resume_job_binding_id=latest.binding_id,
            resume_id=latest.resume_id,
            resume_title=None,
            resume_version_ref=VersionRef(
                resource_type="resume",
                resource_id=latest.resume_id,
                version_id=latest.resume_version_id,
            ),
            bound_at=latest.created_at,
        )

    return _build


def _job_version_ref(job) -> VersionRef:
    return VersionRef(
        resource_type="job",
        resource_id=job.job_id,
        version_id=job.current_version_id,
    )


def _job_version_ref_from(job, version) -> VersionRef:
    return VersionRef(
        resource_type="job",
        resource_id=job.job_id,
        version_id=version.job_version_id,
    )


def _error_status(code: str) -> int:
    if code in {"stale_version_conflict", "idempotency_conflict"}:
        return 409
    if code == "validation_failed":
        return 422
    if code == "not_found_or_inaccessible":
        return 404
    return 400
