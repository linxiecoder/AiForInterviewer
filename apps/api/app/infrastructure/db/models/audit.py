"""Trace and audit model skeletons."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class ApiRequestTrace(OwnedRecordMixin, Base):
    __tablename__ = "api_request_traces"

    request_id: Mapped[str] = mapped_column(String(80), index=True)
    trace_id: Mapped[str] = mapped_column(String(80), index=True)
    audit_event_id: Mapped[str | None] = mapped_column(String(80), nullable=True)


class AuditEvent(OwnedRecordMixin, Base):
    __tablename__ = "audit_events"

    api_request_trace_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    target_ref_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

