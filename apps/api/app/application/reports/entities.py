"""Report read models for application use cases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ReportSectionDetail:
    section_key: str
    section_summary: str | None
    score_ref: str | None


@dataclass(frozen=True)
class ReportDetail:
    report_id: str
    owner_id: str
    session_id: str | None
    report_type: str
    report_status: str
    score_ref: str | None
    generated_at: datetime | None
    sections: tuple[ReportSectionDetail, ...] = ()

    @property
    def copy_content_available(self) -> bool:
        # M4 retrieval V1 is read-only; copy-content/copy-events endpoints remain unimplemented.
        return False
