"""Report commands."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateReportTaskCommand:
    session_id: str
    report_type: str

