"""Reference table model skeletons."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class EvidenceRef(OwnedRecordMixin, Base):
    __tablename__ = "evidence_refs"

    source_ref_id: Mapped[str] = mapped_column(String(80), index=True)
    version_ref_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    snapshot_ref_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    evidence_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class TraceRef(OwnedRecordMixin, Base):
    __tablename__ = "trace_refs"

    api_request_trace_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ai_task_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    audit_event_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    trace_kind: Mapped[str] = mapped_column(String(80), nullable=False)
    trace_key: Mapped[str] = mapped_column(String(160), nullable=False)


class UserConfirmation(OwnedRecordMixin, Base):
    __tablename__ = "user_confirmations"

    target_ref_id: Mapped[str] = mapped_column(String(80), index=True)
    audit_event_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    before_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

