"""Asset model skeletons."""

from typing import Any

from sqlalchemy import JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class Asset(OwnedRecordMixin, Base):
    __tablename__ = "assets"

    normalized_title: Mapped[str] = mapped_column(String(200), nullable=False)
    asset_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str | None] = mapped_column(String(160), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_version_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    evidence_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    trace_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    resume_version_ref_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    job_version_ref_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    question_pattern: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_from_candidate_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    user_confirmation_ref_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    fact_source: Mapped[str | None] = mapped_column(String(80), nullable=True)


class AssetVersion(OwnedRecordMixin, Base):
    __tablename__ = "asset_versions"

    asset_id: Mapped[str] = mapped_column(String(80), index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    edit_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_actor_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_from_candidate_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
