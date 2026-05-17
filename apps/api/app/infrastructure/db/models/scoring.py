"""Scoring model skeletons."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class ScoreRuleSet(OwnedRecordMixin, Base):
    __tablename__ = "score_rule_sets"

    score_type: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)


class ScoreRuleVersion(OwnedRecordMixin, Base):
    __tablename__ = "score_rule_versions"

    score_rule_set_id: Mapped[str] = mapped_column(String(80), index=True)
    version: Mapped[str] = mapped_column(String(64), nullable=False)


class ScoreDimension(OwnedRecordMixin, Base):
    __tablename__ = "score_dimensions"

    score_rule_version_id: Mapped[str] = mapped_column(String(80), index=True)
    dimension_key: Mapped[str] = mapped_column(String(80), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False)


class ScoreResult(OwnedRecordMixin, Base):
    __tablename__ = "score_results"

    score_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_ref_id: Mapped[str] = mapped_column(String(80), index=True)
    score_rule_version_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ai_task_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    score_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rubric_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ScoreEvidenceLink(OwnedRecordMixin, Base):
    __tablename__ = "score_evidence_links"

    score_result_id: Mapped[str] = mapped_column(String(80), index=True)
    score_dimension_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    evidence_ref_id: Mapped[str] = mapped_column(String(80), index=True)
    evidence_role: Mapped[str | None] = mapped_column(String(80), nullable=True)


class LowConfidenceFlag(OwnedRecordMixin, Base):
    __tablename__ = "low_confidence_flags"

    target_ref_id: Mapped[str] = mapped_column(String(80), index=True)
    validation_result_ref_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    trace_ref_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    reason: Mapped[str] = mapped_column(String(120), nullable=False)
    impact_scope: Mapped[str | None] = mapped_column(Text, nullable=True)

