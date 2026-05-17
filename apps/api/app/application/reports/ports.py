"""Report ports."""

from typing import Protocol

from app.domain.shared.refs import ResourceRef


class ReportRepository(Protocol):
    def get_ref(self, report_id: str) -> ResourceRef | None: ...

