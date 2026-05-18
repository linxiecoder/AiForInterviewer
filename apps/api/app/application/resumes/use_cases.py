"""Resume use case implementations."""

from app.application.common.result import ApplicationResult
from app.application.resumes.ports import ResumeRepository
from app.domain.resumes.entities import Resume


class ResumeUseCases:
    def __init__(self, repository: ResumeRepository):
        self._repository = repository

    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="resume_skeleton")

    def list_for_owner(self, owner_id: str) -> ApplicationResult[list[Resume]]:
        return ApplicationResult(value=self._repository.list_by_owner(owner_id))
