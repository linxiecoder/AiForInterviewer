"""Persisted polish candidate records."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.shared.clock import utc_now
from app.infrastructure.db.base import Base


class PolishCandidateRecord(Base):
    __tablename__ = "polish_candidates"
    __table_args__ = (
        UniqueConstraint("owner_id", "merge_key", name="uq_polish_candidates_owner_merge_key"),
    )

    candidate_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    candidate_type: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(64), default="candidate", nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), index=True)
    source_refs_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    evidence_refs_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    trace_refs_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    session_id: Mapped[str] = mapped_column(String(80), index=True)
    question_id: Mapped[str] = mapped_column(String(80), index=True)
    answer_id: Mapped[str] = mapped_column(String(80), index=True)
    feedback_id: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_level: Mapped[str] = mapped_column(String(40), index=True)
    merge_key: Mapped[str] = mapped_column(String(520), nullable=False)
    merge_target_candidate_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    target_formal_ref_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    candidate_payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    user_confirmation_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
