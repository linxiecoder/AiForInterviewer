"""Report queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetReportQuery:
    owner_id: str
    report_id: str
