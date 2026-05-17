"""Question model skeleton."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class Question(OwnedRecordMixin, Base):
    __tablename__ = "questions"

    session_id: Mapped[str] = mapped_column(String(80), index=True)
    ai_task_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    question_text: Mapped[str | None] = mapped_column(Text, nullable=True)

