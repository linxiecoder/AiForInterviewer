"""Reusable SQLAlchemy model mixins."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.shared.clock import utc_now


class IdMixin:
    id: Mapped[str] = mapped_column(String(80), primary_key=True)


class OwnerMixin:
    owner_id: Mapped[str] = mapped_column(String(80), index=True)


class ActorMixin:
    actor_id: Mapped[str | None] = mapped_column(String(80), nullable=True)


class VersionMixin:
    record_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class StatusMixin:
    status: Mapped[str] = mapped_column(String(64), nullable=False)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class TraceEvidenceMixin:
    trace_ref_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    evidence_ref_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)


class OwnedRecordMixin(IdMixin, OwnerMixin, ActorMixin, VersionMixin, StatusMixin, TimestampMixin, TraceEvidenceMixin):
    __abstract__ = True

