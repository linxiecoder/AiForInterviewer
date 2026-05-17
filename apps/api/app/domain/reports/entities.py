"""Report domain entities."""

from dataclasses import dataclass

from app.domain.shared.refs import OwnerRef


@dataclass(frozen=True)
class InterviewReport:
    report_id: str
    owner_ref: OwnerRef
    status: str

