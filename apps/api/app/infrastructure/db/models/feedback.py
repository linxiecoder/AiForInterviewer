"""Feedback model skeleton."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class Feedback(OwnedRecordMixin, Base):
    __tablename__ = "feedback"

    session_id: Mapped[str] = mapped_column(String(80), index=True)
    answer_id: Mapped[str] = mapped_column(String(80), index=True)
    ai_task_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    score_result_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    feedback_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

