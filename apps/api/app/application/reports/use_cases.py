"""Report use cases."""

from app.application.common.result import ApplicationResult
from app.application.reports.entities import ReportDetail
from app.application.reports.ports import ReportRepository
from app.application.reports.queries import GetReportQuery
from app.domain.shared.errors import DomainError


class ReportUseCases:
    def __init__(self, repository: ReportRepository | None = None) -> None:
        self._repository = repository

    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="report_skeleton")

    def get_report(self, query: GetReportQuery) -> ApplicationResult[ReportDetail]:
        if not _is_valid_report_id(query.report_id):
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="Report id must use report_* format.",
                )
            )
        if self._repository is None:
            return ApplicationResult(
                error=DomainError(
                    code="internal_error",
                    message="Report repository is not available.",
                )
            )

        report = self._repository.get_report(owner_id=query.owner_id, report_id=query.report_id)
        if report is None:
            return ApplicationResult(
                error=DomainError(
                    code="not_found_or_inaccessible",
                    message="Report not found or inaccessible.",
                )
            )
        if report.report_type != "polish_summary":
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="Only polish_summary reports can be retrieved in this slice.",
                )
            )
        return ApplicationResult(value=report)


def _is_valid_report_id(report_id: str) -> bool:
    return report_id.startswith("report_") and len(report_id) <= 80
