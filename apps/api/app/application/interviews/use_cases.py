"""Interview use case placeholders."""

from app.application.common.result import ApplicationResult


class InterviewUseCases:
    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="interview_skeleton")

