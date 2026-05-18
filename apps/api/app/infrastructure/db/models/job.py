"""Job models for F5-M2 backend."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class Job(OwnedRecordMixin, Base):
    __tablename__ = "jobs"

    title: Mapped[str] = mapped_column(String(160), nullable=False)
    company: Mapped[str | None] = mapped_column(String(160), nullable=True)
    department: Mapped[str | None] = mapped_column(String(160), nullable=True)
    application_status: Mapped[str] = mapped_column(String(64), nullable=False, default="draft")
    current_version_id: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class JobVersion(OwnedRecordMixin, Base):
    __tablename__ = "job_versions"

    job_id: Mapped[str] = mapped_column(String(80), index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    responsibilities: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    requirements: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    other_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
