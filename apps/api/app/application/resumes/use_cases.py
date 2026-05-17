"""Resume use case placeholders."""

from app.application.common.result import ApplicationResult


class ResumeUseCases:
    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="resume_skeleton")

