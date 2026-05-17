"""Report domain events."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportCreated:
    report_id: str

