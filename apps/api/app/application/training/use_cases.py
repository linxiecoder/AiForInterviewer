"""Training use case placeholders."""

from app.application.common.result import ApplicationResult


class TrainingUseCases:
    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="training_skeleton")

