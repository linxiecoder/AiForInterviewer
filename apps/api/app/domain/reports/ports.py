"""Report domain ports."""

from typing import Protocol

from app.domain.reports.entities import InterviewReport


class ReportReader(Protocol):
    def get(self, report_id: str) -> InterviewReport | None: ...

