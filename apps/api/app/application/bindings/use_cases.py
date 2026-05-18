"""Binding application use cases."""

from __future__ import annotations

from dataclasses import replace

from app.application.bindings.commands import CreateBindingCommand, DeleteBindingCommand, RegisterResumeVersionCommand
from app.application.bindings.queries import GetBindingQuery
from app.application.common.result import ApplicationResult
from app.domain.bindings.entities import ResumeJobBinding
from app.domain.bindings.ports import BindingRepository
from app.domain.jobs.entities import Job
from app.domain.jobs.ports import JobRepository
from app.domain.shared.clock import utc_now
from app.domain.shared.errors import DomainError
from app.domain.shared.ids import generate_resource_id, ResourceIdPrefix

BINDING_STATUSES = {"active", "unbound", "stale", "archived", "unbinding"}


class BindingUseCases:
    def __init__(self, binding_repository: BindingRepository, job_repository: JobRepository):
        self._binding_repository = binding_repository
        self._job_repository = job_repository

    def register_resume(self, command: RegisterResumeVersionCommand) -> None:
        self._binding_repository.register_resume(
            owner_id=command.owner_id,
            resume_id=command.resume_id,
            resume_version_id=command.resume_version_id,
        )

    def create(self, command: CreateBindingCommand) -> ApplicationResult[ResumeJobBinding]:
        now = utc_now()
        job = self._job_repository.get(command.job_id)
        if job is None or job.owner_id != command.owner_id:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Job not found")
            )

        resume_version_id = command.resume_version_id
        if resume_version_id is None:
            resume_version_id = self._binding_repository.get_resume_current_version(
                owner_id=command.owner_id,
                resume_id=command.resume_id,
            )
            if resume_version_id is None:
                return ApplicationResult(
                    error=DomainError(
                        code="validation_failed",
                        message="resume version is required when resume has no current version",
                    )
                )

        if resume_version_id != self._binding_repository.get_resume_current_version(
            owner_id=command.owner_id,
            resume_id=command.resume_id,
        ):
            return ApplicationResult(
                error=DomainError(code="validation_failed", message="resume not owned or invalid")
            )

        current_version_id = command.job_version_id or job.current_version_id
        if not current_version_id:
            return ApplicationResult(
                error=DomainError(code="validation_failed", message="Job has no current version")
            )

        existing_active = self._binding_repository.find_active_binding(
            owner_id=command.owner_id,
            resume_id=command.resume_id,
            job_id=command.job_id,
        )
        if existing_active is not None:
            if (
                existing_active.resume_version_id == resume_version_id
                and existing_active.job_version_id == current_version_id
            ):
                return ApplicationResult(value=existing_active)
            return ApplicationResult(
                error=DomainError(
                    code="idempotency_conflict",
                    message="Active binding conflict for same resume and job",
                )
            )

        binding_id = generate_resource_id(ResourceIdPrefix.BINDING)
        binding = ResumeJobBinding(
            binding_id=binding_id,
            owner_id=command.owner_id,
            resume_id=command.resume_id,
            job_id=command.job_id,
            resume_version_id=resume_version_id,
            job_version_id=current_version_id,
            status="active",
            unbound_at=None,
            unbound_by=None,
            record_version=1,
            created_at=now,
            updated_at=now,
        )
        self._binding_repository.add(binding)
        return ApplicationResult(value=binding)

    def get(self, query: GetBindingQuery) -> ApplicationResult[ResumeJobBinding | None]:
        binding = self._binding_repository.get(query.binding_id)
        if binding is None or binding.owner_id != query.owner_id:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Binding not found")
            )
        return ApplicationResult(value=binding)

    def delete(self, query: GetBindingQuery, command: DeleteBindingCommand) -> ApplicationResult[ResumeJobBinding]:
        binding = self._binding_repository.get(query.binding_id)
        if binding is None or binding.owner_id != command.owner_id:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Binding not found")
            )

        if command.base_version_ref is not None:
            try:
                expected_version = int(command.base_version_ref.version_id)
            except ValueError:
                return ApplicationResult(
                    error=DomainError(code="validation_failed", message="Invalid base version")
                )
            if expected_version != binding.record_version:
                return ApplicationResult(
                    error=DomainError(
                        code="stale_version_conflict",
                        message="Binding record version stale",
                    )
                )

        if command.record_version is not None and command.record_version != binding.record_version:
            return ApplicationResult(
                error=DomainError(
                    code="stale_version_conflict",
                    message="Binding record version stale",
                )
            )

        if binding.status == "unbound":
            return ApplicationResult(value=binding)

        if binding.status not in BINDING_STATUSES:
            return ApplicationResult(
                error=DomainError(code="validation_failed", message="Binding status invalid")
            )

        now = utc_now()
        updated = replace(
            binding,
            status="unbound",
            unbound_at=now,
            unbound_by=command.owner_id,
            record_version=binding.record_version + 1,
            updated_at=now,
        )
        self._binding_repository.update(updated)
        return ApplicationResult(value=updated)


def _extract_job_title(job: Job | None) -> str | None:
    if job is None:
        return None
    return job.title
