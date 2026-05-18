"""Job application use cases for backend persistence and API-facing validation."""

from __future__ import annotations

from dataclasses import replace
from dataclasses import dataclass
from datetime import datetime

from app.application.common.result import ApplicationResult
from app.domain.jobs.commands import CreateJobCommand, UpdateJobCommand
from app.domain.jobs.entities import Job, JobVersion
from app.domain.jobs.ports import JobRepository
from app.application.jobs.queries import GetJobQuery, ListJobsQuery
from app.domain.shared.clock import utc_now
from app.domain.shared.errors import DomainError
from app.domain.shared.ids import generate_resource_id, ResourceIdPrefix


JOB_STATUSES = {"active", "archived", "deleted", "draft"}
JOB_APPLICATION_STATUSES = {"draft", "applied", "interviewing", "closed"}
JOB_VERSION_STATUSES = {"current", "superseded", "archived"}


@dataclass(frozen=True)
class JobUseCases:
    repository: JobRepository

    def create(self, command: CreateJobCommand) -> ApplicationResult[tuple[Job, JobVersion]]:
        now = utc_now()
        if not command.title.strip():
            return ApplicationResult(
                error=DomainError(code="validation_failed", message="Title cannot be empty")
            )
        if not command.responsibilities:
            return ApplicationResult(
                error=DomainError(code="validation_failed", message="Responsibilities cannot be empty")
            )
        if not command.requirements:
            return ApplicationResult(
                error=DomainError(code="validation_failed", message="Requirements cannot be empty")
            )

        application_status = command.application_status or "draft"
        if application_status not in JOB_APPLICATION_STATUSES:
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="Unsupported application status",
                )
            )

        job_id = generate_resource_id(ResourceIdPrefix.JOB)
        job_version_id = generate_resource_id(ResourceIdPrefix.JOB)
        job = Job(
            job_id=job_id,
            owner_id=command.owner_id,
            title=command.title,
            company=command.company,
            department=command.department,
            application_status=application_status,
            status="active",
            current_version_id=job_version_id,
            record_version=1,
            created_at=now,
            updated_at=now,
            archived_at=None,
        )
        version = JobVersion(
            job_version_id=job_version_id,
            owner_id=command.owner_id,
            job_id=job_id,
            version_number=1,
            responsibilities=list(command.responsibilities),
            requirements=list(command.requirements),
            other_notes=command.other_notes,
            status="current",
            created_at=now,
        )

        self.repository.create_job(job)
        self.repository.create_job_version(version)
        return ApplicationResult(value=(job, version))

    def list_by_owner(self, query: ListJobsQuery) -> ApplicationResult[list[Job]]:
        return ApplicationResult(value=self.repository.list_by_owner(query.owner_id))

    def get(self, query: GetJobQuery) -> ApplicationResult[tuple[Job, JobVersion] | None]:
        job = self.repository.get(query.job_id)
        if job is None or job.owner_id != query.owner_id:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Job not found")
            )

        version = self.repository.get_job_version(job.current_version_id)
        if version is None:
            return ApplicationResult(
                error=DomainError(code="internal_error", message="Job current version missing")
            )
        return ApplicationResult(value=(job, version))

    def update(self, query: GetJobQuery, command: UpdateJobCommand) -> ApplicationResult[tuple[Job, JobVersion]]:
        job = self.repository.get(query.job_id)
        if job is None:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Job not found")
            )

        if job.owner_id != command.owner_id:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Job not found")
            )

        if command.base_version_ref is None and command.record_version is None:
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="base_version_ref or record_version is required",
                )
            )

        if command.responsibilities is not None and not command.responsibilities:
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="Responsibilities cannot be empty",
                )
            )

        if command.requirements is not None and not command.requirements:
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="Requirements cannot be empty",
                )
            )

        if command.base_version_ref is not None:
            if command.base_version_ref.resource_type != "job":
                return ApplicationResult(
                    error=DomainError(
                        code="validation_failed",
                        message="base_version_ref.resource_type must be job",
                    )
                )
            if command.base_version_ref.resource_id != job.job_id:
                return ApplicationResult(
                    error=DomainError(
                        code="validation_failed",
                        message="base_version_ref.resource_id does not match target job",
                    )
                )
            if command.base_version_ref.version_id != job.current_version_id:
                return ApplicationResult(
                    error=DomainError(
                        code="stale_version_conflict",
                        message="Base version is stale",
                    )
                )

        if command.record_version is not None and command.record_version != job.record_version:
            return ApplicationResult(
                error=DomainError(
                    code="stale_version_conflict",
                    message="Record version is stale",
                )
            )

        now = utc_now()
        has_version_change = any(
            item is not None
            for item in (command.responsibilities, command.requirements, command.other_notes, command.status)
        )

        next_version = 0
        next_current_version_id = job.current_version_id
        next_job_version = self.repository.get_job_version(job.current_version_id)
        if next_job_version is None:
            return ApplicationResult(
                error=DomainError(code="internal_error", message="Job current version missing")
            )

        title = job.title if command.title is None else command.title
        company = job.company if command.company is None else command.company
        department = job.department if command.department is None else command.department

        if command.application_status is not None and command.application_status not in JOB_APPLICATION_STATUSES:
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="Unsupported application status",
                )
            )

        if command.status is not None:
            if command.status not in JOB_STATUSES:
                return ApplicationResult(
                    error=DomainError(code="validation_failed", message="Unsupported job status")
                )

        if has_version_change:
            next_version = next_job_version.version_number + 1
            next_current_version_id = generate_resource_id(ResourceIdPrefix.JOB)
            updated_version = JobVersion(
                job_version_id=next_current_version_id,
                owner_id=job.owner_id,
                job_id=job.job_id,
                version_number=next_version,
                responsibilities=list(
                    command.responsibilities
                    if command.responsibilities is not None
                    else next_job_version.responsibilities
                ),
                requirements=list(
                    command.requirements
                    if command.requirements is not None
                    else next_job_version.requirements
                ),
                other_notes=command.other_notes
                if command.other_notes is not None
                else next_job_version.other_notes,
                status="current",
                created_at=now,
            )

            superseded_version = replace(next_job_version, status="superseded")
            self.repository.update_job_version(superseded_version)
            self.repository.create_job_version(updated_version)

        next_status = command.status or job.status
        next_archived_at = job.archived_at
        if command.status == "archived":
            next_archived_at = now
        elif command.status in {"active", "draft"}:
            next_archived_at = None

        if command.department is not None:
            department = command.department
        else:
            department = job.department

        updated_job = replace(
            job,
            title=title,
            company=company,
            department=department,
            application_status=command.application_status or job.application_status,
            status=next_status,
            record_version=job.record_version + 1,
            current_version_id=next_current_version_id,
            updated_at=now,
            archived_at=next_archived_at,
        )

        self.repository.update_job(updated_job)

        if has_version_change:
            return ApplicationResult(
                value=(updated_job, updated_version)
            )

        return ApplicationResult(
            value=(updated_job, next_job_version)
        )
