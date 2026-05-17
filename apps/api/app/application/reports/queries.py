"""Report queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetReportQuery:
    report_id: str

