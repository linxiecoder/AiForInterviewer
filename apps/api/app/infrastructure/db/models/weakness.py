"""Weakness model skeletons."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class Weakness(OwnedRecordMixin, Base):
    __tablename__ = "weaknesses"

    normalized_title: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str | None] = mapped_column(String(160), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity_hint: Mapped[str | None] = mapped_column(String(40), nullable=True)
    confidence_level: Mapped[str | None] = mapped_column(String(40), nullable=True)
    source_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    session_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    feedback_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    question_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    answer_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    loss_point_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    repeated_loss_point_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    evidence_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    trace_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    created_from_candidate_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    user_confirmation_ref_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    occurrence_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WeaknessCandidate(OwnedRecordMixin, Base):
    __tablename__ = "weakness_candidates"

    normalized_title: Mapped[str] = mapped_column(String(200), nullable=False)
    ai_task_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    target_weakness_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
