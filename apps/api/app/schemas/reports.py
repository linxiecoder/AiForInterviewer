"""Report API DTO placeholder."""

from pydantic import BaseModel


class ReportResponse(BaseModel):
    report_id: str
    status: str

