"""AI task use cases."""

from app.application.common.result import ApplicationResult
from app.application.ai_tasks.ports import AiTaskRepository
from app.application.ai_tasks.queries import GetAiTaskQuery
from app.domain.shared.errors import DomainError


class AiTaskUseCases:
    def __init__(self, repository: AiTaskRepository | None = None) -> None:
        self._repository = repository

    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="ai_task_skeleton")

    def get_status(self, query: GetAiTaskQuery) -> ApplicationResult[dict[str, object]]:
        if self._repository is None:
            return ApplicationResult(error=_not_found())
        status = self._repository.get_status(owner_id=query.owner_id, ai_task_id=query.ai_task_id)
        if status is None:
            return ApplicationResult(error=_not_found())
        return ApplicationResult(value=status)

    def get_result(self, query: GetAiTaskQuery) -> ApplicationResult[dict[str, object]]:
        if self._repository is None:
            return ApplicationResult(error=_not_found())
        result = self._repository.get_result(owner_id=query.owner_id, ai_task_id=query.ai_task_id)
        if result is None:
            return ApplicationResult(error=_not_found())
        return ApplicationResult(value=result)


def _not_found() -> DomainError:
    return DomainError(code="not_found_or_inaccessible", message="AI task not found")
