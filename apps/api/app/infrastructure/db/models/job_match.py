"""Job match analysis persistence models."""

from __future__ import annotations

from sqlalchemy import Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class JobMatchAnalysis(OwnedRecordMixin, Base):
    __tablename__ = "job_match_analyses"

    binding_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    resume_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    resume_version_id: Mapped[str] = mapped_column(String(80), nullable=False)
    job_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    job_version_id: Mapped[str] = mapped_column(String(80), nullable=False)
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    overall_level: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(32), nullable=True)
    result_payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    markdown_report_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    score_rule_version: Mapped[str] = mapped_column(String(80), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_digest: Mapped[str] = mapped_column(String(80), nullable=False)
