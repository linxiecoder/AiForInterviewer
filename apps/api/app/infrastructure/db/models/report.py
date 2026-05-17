"""Report model skeletons."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class InterviewReport(OwnedRecordMixin, Base):
    __tablename__ = "interview_reports"

    session_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ai_task_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    score_result_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    report_type: Mapped[str] = mapped_column(String(80), nullable=False)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReportSection(OwnedRecordMixin, Base):
    __tablename__ = "report_sections"

    report_id: Mapped[str] = mapped_column(String(80), index=True)
    section_key: Mapped[str] = mapped_column(String(80), nullable=False)
    score_result_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    section_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

