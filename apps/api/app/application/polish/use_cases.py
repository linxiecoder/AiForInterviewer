"""Polish use case placeholders."""

from app.application.common.result import ApplicationResult


class PolishUseCases:
    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="polish_skeleton")

