"""Job match use case placeholders."""

from app.application.common.result import ApplicationResult


class JobMatchUseCases:
    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="job_match_skeleton")

