"""AI task use case placeholders."""

from app.application.common.result import ApplicationResult


class AiTaskUseCases:
    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="ai_task_skeleton")

