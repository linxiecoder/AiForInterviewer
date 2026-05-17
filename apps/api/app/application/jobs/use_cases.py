"""Job use case placeholders."""

from app.application.common.result import ApplicationResult


class JobUseCases:
    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="job_skeleton")

