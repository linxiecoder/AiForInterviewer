"""Report API DTOs."""

from datetime import datetime

from pydantic import Field
from pydantic import BaseModel

from app.schemas.refs import SourceAvailabilitySchema


class ReportSectionResponse(BaseModel):
    section_key: str
    section_summary: str | None = None
    score_ref: str | None = None


class ReportDetailResponse(BaseModel):
    report_id: str
    report_type: str
    session_ref: str | None = None
    report_status: str
    sections: list[ReportSectionResponse] = Field(default_factory=list)
    score_ref: str | None = None
    copy_content_available: bool
    source_availability: SourceAvailabilitySchema
    generated_at: datetime | None = None
