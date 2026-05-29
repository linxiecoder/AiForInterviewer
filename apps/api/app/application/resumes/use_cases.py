"""Resume use case implementations."""

from app.application.common.result import ApplicationResult
from dataclasses import replace

from app.application.resumes.commands import CreateResumeCommand, UpdateResumeCommand
from app.application.resumes.ports import ResumeRepository
from app.domain.resumes.entities import Resume, ResumeVersion
from app.domain.shared.clock import utc_now
from app.domain.shared.errors import DomainError
from app.domain.shared.ids import ResourceIdPrefix, generate_resource_id
from app.domain.shared.refs import OwnerRef, VersionRef


class ResumeUseCases:
    def __init__(self, repository: ResumeRepository):
        self._repository = repository

    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="resume_skeleton")

    def create(self, command: CreateResumeCommand) -> ApplicationResult[tuple[Resume, ResumeVersion]]:
        title = command.title.strip()
        markdown_text = command.markdown_text.strip()
        if not title:
            return ApplicationResult(
                error=DomainError(code="validation_failed", message="Title cannot be empty")
            )
        if not markdown_text:
            return ApplicationResult(
                error=DomainError(code="validation_failed", message="Resume content cannot be empty")
            )

        now = utc_now()
        resume_id = generate_resource_id(ResourceIdPrefix.RESUME)
        resume_version_id = generate_resource_id(ResourceIdPrefix.RESUME)
        resume = Resume(
            resume_id=resume_id,
            owner_ref=OwnerRef(owner_id=command.owner_id),
            current_version_ref=VersionRef(
                resource_type="resume",
                resource_id=resume_id,
                version_id=resume_version_id,
            ),
            status="active",
            title=title,
            file_name=None,
            created_at=now,
            updated_at=now,
        )
        version = ResumeVersion(
            resume_version_id=resume_version_id,
            owner_id=command.owner_id,
            resume_id=resume_id,
            version_number=1,
            markdown_text=markdown_text,
            status="current",
            created_at=now,
        )

        self._repository.create_with_version(resume, version)
        return ApplicationResult(value=(resume, version))

    def list_for_owner(self, owner_id: str) -> ApplicationResult[list[Resume]]:
        return ApplicationResult(value=self._repository.list_by_owner(owner_id))

    def get_detail(self, owner_id: str, resume_id: str) -> ApplicationResult[tuple[Resume, ResumeVersion]]:
        resume = self._repository.get(resume_id)
        if resume is None or resume.owner_ref.owner_id != owner_id or resume.status == "deleted":
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Resume not found")
            )

        version = self._repository.get_version(resume.current_version_ref.version_id)
        if version is None:
            return ApplicationResult(
                error=DomainError(code="internal_error", message="Resume current version missing")
            )

        return ApplicationResult(value=(resume, version))

    def delete(self, owner_id: str, resume_id: str) -> ApplicationResult[tuple[Resume, ResumeVersion]]:
        resume = self._repository.get(resume_id)
        if resume is None or resume.owner_ref.owner_id != owner_id or resume.status == "deleted":
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Resume not found")
            )

        version = self._repository.get_version(resume.current_version_ref.version_id)
        if version is None:
            return ApplicationResult(
                error=DomainError(code="internal_error", message="Resume current version missing")
            )

        updated_resume = replace(resume, status="deleted", updated_at=utc_now())
        self._repository.add(updated_resume)
        return ApplicationResult(value=(updated_resume, version))

    def update(self, command: UpdateResumeCommand) -> ApplicationResult[tuple[Resume, ResumeVersion]]:
        resume = self._repository.get(command.resume_id)
        if resume is None or resume.owner_ref.owner_id != command.owner_id or resume.status == "deleted":
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Resume not found")
            )

        title = command.title.strip()
        markdown_text = command.markdown_text.strip()
        if not title:
            return ApplicationResult(
                error=DomainError(code="validation_failed", message="Title cannot be empty")
            )
        if not markdown_text:
            return ApplicationResult(
                error=DomainError(code="validation_failed", message="Resume content cannot be empty")
            )

        if command.base_version_ref.resource_type != "resume":
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="base_version_ref.resource_type must be resume",
                )
            )
        if command.base_version_ref.resource_id != resume.resume_id:
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="base_version_ref.resource_id does not match target resume",
                )
            )
        if command.base_version_ref.version_id != resume.current_version_ref.version_id:
            return ApplicationResult(
                error=DomainError(code="stale_version_conflict", message="Base version is stale")
            )

        current_version = self._repository.get_version(resume.current_version_ref.version_id)
        if current_version is None:
            return ApplicationResult(
                error=DomainError(code="internal_error", message="Resume current version missing")
            )

        now = utc_now()
        next_version_id = generate_resource_id(ResourceIdPrefix.RESUME)
        next_version = ResumeVersion(
            resume_version_id=next_version_id,
            owner_id=command.owner_id,
            resume_id=resume.resume_id,
            version_number=current_version.version_number + 1,
            markdown_text=markdown_text,
            status="current",
            created_at=now,
        )
        updated_resume = replace(
            resume,
            title=title,
            current_version_ref=VersionRef(
                resource_type="resume",
                resource_id=resume.resume_id,
                version_id=next_version_id,
            ),
            updated_at=now,
        )

        self._repository.add_version(replace(current_version, status="superseded"))
        self._repository.add_version(next_version)
        self._repository.add(updated_resume)

        return ApplicationResult(value=(updated_resume, next_version))
