"""Inert AI Runtime persistence models for PR2."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.mixins import OwnedRecordMixin


class AgentRun(OwnedRecordMixin, Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        UniqueConstraint("owner_id", "thread_id", name="uq_agent_runs_owner_thread"),
        UniqueConstraint("owner_id", "graph_name", "idempotency_key_hash", name="uq_agent_runs_owner_graph_idem"),
        Index("ix_agent_runs_owner_task", "owner_id", "ai_task_id"),
        Index("ix_agent_runs_owner_status", "owner_id", "status"),
        Index("ix_agent_runs_owner_graph", "owner_id", "graph_name"),
        Index("ix_agent_runs_owner_thread", "owner_id", "thread_id"),
    )

    ai_task_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    graph_name: Mapped[str] = mapped_column(String(120), nullable=False)
    graph_version: Mapped[str] = mapped_column(String(80), nullable=False)
    entrypoint_name: Mapped[str] = mapped_column(String(120), nullable=False)
    thread_id: Mapped[str] = mapped_column(String(80), nullable=False)
    idempotency_key_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    input_refs_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    output_refs_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    pending_writes_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    error_summary_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    interrupted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AgentNodeRun(OwnedRecordMixin, Base):
    __tablename__ = "agent_node_runs"
    __table_args__ = (
        UniqueConstraint("owner_id", "agent_run_id", "node_name", "attempt_number", name="uq_agent_node_runs_attempt"),
        Index("ix_agent_node_runs_owner_run", "owner_id", "agent_run_id"),
        Index("ix_agent_node_runs_owner_node", "owner_id", "node_name"),
        Index("ix_agent_node_runs_owner_status", "owner_id", "status"),
    )

    agent_run_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    graph_name: Mapped[str] = mapped_column(String(120), nullable=False)
    node_name: Mapped[str] = mapped_column(String(120), nullable=False)
    node_version: Mapped[str] = mapped_column(String(80), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    llm_call_ids_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    side_effect_keys_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    input_digest: Mapped[str | None] = mapped_column(String(128), nullable=True)
    output_digest: Mapped[str | None] = mapped_column(String(128), nullable=True)
    validation_summary_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AgentInterrupt(OwnedRecordMixin, Base):
    __tablename__ = "agent_interrupts"
    __table_args__ = (
        UniqueConstraint("owner_id", "id", "idempotency_key_hash", name="uq_agent_interrupts_owner_idem"),
        Index("ix_agent_interrupts_owner_run", "owner_id", "agent_run_id"),
        Index("ix_agent_interrupts_owner_node", "owner_id", "node_name"),
        Index("ix_agent_interrupts_owner_expires", "owner_id", "expires_at"),
    )

    agent_run_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    agent_node_run_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    node_name: Mapped[str] = mapped_column(String(120), nullable=False)
    interrupt_type: Mapped[str] = mapped_column(String(80), nullable=False)
    resume_schema_id: Mapped[str] = mapped_column(String(120), nullable=False)
    prompt_summary_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    resume_payload_summary_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    idempotency_key_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)


class AgentCheckpointRef(OwnedRecordMixin, Base):
    __tablename__ = "agent_checkpoint_refs"
    __table_args__ = (
        UniqueConstraint(
            "owner_id",
            "checkpoint_namespace",
            "thread_id",
            "checkpoint_id",
            name="uq_agent_checkpoint_refs_owner_checkpoint",
        ),
        Index("ix_agent_checkpoint_refs_owner_run", "owner_id", "agent_run_id"),
        Index("ix_agent_checkpoint_refs_owner_thread", "owner_id", "thread_id"),
        Index("ix_agent_checkpoint_refs_owner_retention", "owner_id", "retention_expires_at"),
    )

    agent_run_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    agent_node_run_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    graph_name: Mapped[str] = mapped_column(String(120), nullable=False)
    node_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    checkpoint_namespace: Mapped[str] = mapped_column(String(120), nullable=False)
    thread_id: Mapped[str] = mapped_column(String(80), nullable=False)
    checkpoint_id: Mapped[str] = mapped_column(String(120), nullable=False)
    checkpoint_metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    retention_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LlmCall(OwnedRecordMixin, Base):
    __tablename__ = "llm_calls"
    __table_args__ = (
        Index("ix_llm_calls_owner_task", "owner_id", "ai_task_id"),
        Index("ix_llm_calls_owner_run", "owner_id", "agent_run_id"),
        Index("ix_llm_calls_owner_status", "owner_id", "status"),
        Index("ix_llm_calls_owner_model", "owner_id", "configured_model"),
    )

    ai_task_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    agent_run_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    agent_node_run_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    graph_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    node_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    contract_ids_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    configured_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    provider_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    schema_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    request_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    response_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    evidence_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    usage_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    fallback_reason: Mapped[str | None] = mapped_column(String(240), nullable=True)
    validation_errors_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    low_confidence_flags_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    error_summary_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LlmCallPayload(OwnedRecordMixin, Base):
    __tablename__ = "llm_call_payloads"
    __table_args__ = (
        UniqueConstraint("owner_id", "llm_call_id", "payload_kind", name="uq_llm_call_payloads_owner_call_kind"),
        Index("ix_llm_call_payloads_owner_call", "owner_id", "llm_call_id"),
        Index("ix_llm_call_payloads_owner_kind", "owner_id", "payload_kind"),
        Index("ix_llm_call_payloads_owner_retention", "owner_id", "retention_expires_at"),
        Index("ix_llm_call_payloads_owner_raw", "owner_id", "raw_enabled"),
    )

    llm_call_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    payload_kind: Mapped[str] = mapped_column(String(80), nullable=False)
    capture_policy_version: Mapped[str] = mapped_column(String(80), nullable=False)
    sanitized: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    raw_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payload_summary_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    payload_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw_payload_ciphertext_ref: Mapped[str | None] = mapped_column(String(240), nullable=True)
    encryption_key_ref: Mapped[str | None] = mapped_column(String(240), nullable=True)
    retention_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    access_audit_ref_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
