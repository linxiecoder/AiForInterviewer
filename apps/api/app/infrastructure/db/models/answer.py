"""Answer persistence model."""

from sqlalchemy import Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class Answer(OwnedRecordMixin, Base):
    __tablename__ = "answers"
    __table_args__ = (
        UniqueConstraint("owner_id", "question_id", "answer_round", name="uq_answers_owner_question_round"),
        UniqueConstraint(
            "owner_id",
            "actor_id",
            "session_id",
            "question_id",
            "idempotency_key",
            name="uq_answers_owner_actor_session_question_idem",
        ),
    )

    session_id: Mapped[str] = mapped_column(String(80), index=True)
    question_id: Mapped[str] = mapped_column(String(80), index=True)
    answer_round: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    request_body_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
