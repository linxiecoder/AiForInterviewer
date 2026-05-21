"""Question model skeleton."""

from typing import Any

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class Question(OwnedRecordMixin, Base):
    __tablename__ = "questions"

    session_id: Mapped[str] = mapped_column(String(80), index=True)
    ai_task_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    question_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    question_sources_json: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    question_metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    progress_node_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    context_digest: Mapped[str | None] = mapped_column(String(120), nullable=True)
