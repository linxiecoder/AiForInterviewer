"""Report use case placeholders."""

from app.application.common.result import ApplicationResult


class ReportUseCases:
    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="report_skeleton")

