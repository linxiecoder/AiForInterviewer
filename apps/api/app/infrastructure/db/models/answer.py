"""Answer model skeleton."""

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class Answer(OwnedRecordMixin, Base):
    __tablename__ = "answers"

    session_id: Mapped[str] = mapped_column(String(80), index=True)
    question_id: Mapped[str] = mapped_column(String(80), index=True)
    answer_round: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)

