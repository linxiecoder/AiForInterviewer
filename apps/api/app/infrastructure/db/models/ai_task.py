"""AI task model skeletons."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class AiTask(OwnedRecordMixin, Base):
    __tablename__ = "ai_tasks"

    task_type: Mapped[str] = mapped_column(String(80), nullable=False)
    contract_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    idempotency_record_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    target_ref_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    timeout_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AiTaskResult(OwnedRecordMixin, Base):
    __tablename__ = "ai_task_results"

    ai_task_id: Mapped[str] = mapped_column(String(80), index=True)
    result_sequence: Mapped[str] = mapped_column(String(40), default="0")
    validation_result_ref_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    trace_ref_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    result_ref_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    candidate_refs_json: Mapped[list[dict[str, str]] | None] = mapped_column(JSON, nullable=True)
    suggestion_refs_json: Mapped[list[dict[str, str]] | None] = mapped_column(JSON, nullable=True)
    validation_errors_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    source_availability: Mapped[str | None] = mapped_column(String(40), nullable=True)
    low_confidence_flags_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    safe_summary_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

