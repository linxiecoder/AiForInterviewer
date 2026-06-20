from __future__ import annotations

from sqlalchemy import inspect

from app.infrastructure.db.session import (
    DbSettings,
    build_session_factory,
    initialize_schema,
)


def test_initialize_schema_creates_ai_runtime_tables_and_columns() -> None:
    settings = DbSettings(database_url="sqlite+pysqlite:///:memory:")
    session_factory = build_session_factory(settings)

    initialize_schema(session_factory=session_factory)

    inspector = inspect(session_factory.kw["bind"])
    table_names = set(inspector.get_table_names())
    runtime_tables = {
        "agent_runs",
        "agent_node_runs",
        "agent_interrupts",
        "agent_checkpoint_refs",
        "llm_calls",
        "llm_call_payloads",
    }
    assert runtime_tables.issubset(table_names)

    assert {
        "id",
        "owner_id",
        "actor_id",
        "record_version",
        "status",
        "created_at",
        "updated_at",
        "trace_ref_ids",
        "evidence_ref_ids",
        "ai_task_id",
        "graph_name",
        "graph_version",
        "entrypoint_name",
        "thread_id",
        "idempotency_key_hash",
        "input_refs_json",
        "output_refs_json",
        "pending_writes_json",
        "error_summary_json",
        "started_at",
        "completed_at",
        "interrupted_at",
    }.issubset(_column_names(inspector, "agent_runs"))
    assert {
        "agent_run_id",
        "graph_name",
        "node_name",
        "node_version",
        "attempt_number",
        "llm_call_ids_json",
        "side_effect_keys_json",
        "input_digest",
        "output_digest",
        "validation_summary_json",
        "started_at",
        "completed_at",
    }.issubset(_column_names(inspector, "agent_node_runs"))
    assert {
        "agent_run_id",
        "agent_node_run_id",
        "node_name",
        "interrupt_type",
        "resume_schema_id",
        "prompt_summary_json",
        "resume_payload_summary_json",
        "expires_at",
        "resumed_at",
        "idempotency_key_hash",
    }.issubset(_column_names(inspector, "agent_interrupts"))
    assert {
        "agent_run_id",
        "agent_node_run_id",
        "graph_name",
        "node_name",
        "checkpoint_namespace",
        "thread_id",
        "checkpoint_id",
        "checkpoint_metadata_json",
        "retention_expires_at",
    }.issubset(_column_names(inspector, "agent_checkpoint_refs"))
    assert {
        "ai_task_id",
        "agent_run_id",
        "agent_node_run_id",
        "graph_name",
        "node_name",
        "contract_ids_json",
        "configured_model",
        "provider_model",
        "prompt_version",
        "schema_id",
        "request_hash",
        "response_hash",
        "evidence_hash",
        "usage_json",
        "fallback_reason",
        "validation_errors_json",
        "low_confidence_flags_json",
        "error_summary_json",
        "started_at",
        "completed_at",
    }.issubset(_column_names(inspector, "llm_calls"))
    assert {
        "llm_call_id",
        "payload_kind",
        "capture_policy_version",
        "sanitized",
        "raw_enabled",
        "payload_summary_json",
        "payload_hash",
        "raw_payload_ciphertext_ref",
        "encryption_key_ref",
        "retention_expires_at",
        "access_audit_ref_id",
    }.issubset(_column_names(inspector, "llm_call_payloads"))
    assert {
        "candidate_refs_json",
        "suggestion_refs_json",
        "validation_errors_json",
        "source_availability",
        "low_confidence_flags_json",
        "safe_summary_json",
    }.issubset(_column_names(inspector, "ai_task_results"))


def _column_names(inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}
