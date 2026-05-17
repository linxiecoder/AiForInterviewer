"""Review model skeleton."""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class InterviewReview(OwnedRecordMixin, Base):
    __tablename__ = "interview_reviews"

    session_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    report_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    real_interview_input_ref_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ai_task_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    review_type: Mapped[str] = mapped_column(String(80), nullable=False)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

