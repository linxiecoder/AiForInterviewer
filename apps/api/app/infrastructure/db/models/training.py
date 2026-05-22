"""Training persistence models."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class TrainingRecommendation(OwnedRecordMixin, Base):
    __tablename__ = "training_recommendations"

    normalized_topic: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str | None] = mapped_column(String(160), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_level: Mapped[str | None] = mapped_column(String(40), nullable=True)
    source_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    evidence_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    trace_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    candidate_ref_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    target_weakness_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    question_pattern: Mapped[str | None] = mapped_column(String(120), nullable=True)
    expected_answer_dimensions_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_from_candidate_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    user_confirmation_ref_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    ai_task_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    confirmation_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TrainingTask(OwnedRecordMixin, Base):
    __tablename__ = "training_tasks"

    training_recommendation_id: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str | None] = mapped_column(String(160), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_weakness_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    question_pattern: Mapped[str | None] = mapped_column(String(120), nullable=True)
    expected_answer_dimensions_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    source_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    evidence_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    trace_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    explicit_action_ref_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    progress_update_hint_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
