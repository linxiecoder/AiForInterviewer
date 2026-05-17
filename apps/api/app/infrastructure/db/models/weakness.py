"""Weakness model skeletons."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class Weakness(OwnedRecordMixin, Base):
    __tablename__ = "weaknesses"

    normalized_title: Mapped[str] = mapped_column(String(200), nullable=False)
    created_from_candidate_id: Mapped[str | None] = mapped_column(String(80), nullable=True)


class WeaknessCandidate(OwnedRecordMixin, Base):
    __tablename__ = "weakness_candidates"

    normalized_title: Mapped[str] = mapped_column(String(200), nullable=False)
    ai_task_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    target_weakness_id: Mapped[str | None] = mapped_column(String(80), nullable=True)

