"""Resume use case implementations."""

from app.application.common.result import ApplicationResult
from app.application.resumes.commands import CreateResumeCommand
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
