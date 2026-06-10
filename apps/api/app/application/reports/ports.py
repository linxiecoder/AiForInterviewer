"""Report ports."""

from typing import Protocol

from app.application.reports.entities import ReportDetail
from app.domain.shared.refs import ResourceRef


class ReportRepository(Protocol):
    def get_ref(self, report_id: str) -> ResourceRef | None: ...
    def get_report(self, *, owner_id: str, report_id: str) -> ReportDetail | None: ...
