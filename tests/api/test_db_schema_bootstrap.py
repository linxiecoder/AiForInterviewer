from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.dialects import postgresql, sqlite

from app.infrastructure.db.session import (
    DbSettings,
    _column_sql_for_dialect,
    build_session_factory,
    initialize_schema,
)
from tools.testing.temp_artifacts import ManagedTempArtifacts


def test_backfill_datetime_column_sql_compiles_per_dialect() -> None:
    assert _column_sql_for_dialect("DATETIME", sqlite.dialect()) == "DATETIME"
    assert _column_sql_for_dialect("DATETIME", postgresql.dialect()) == "TIMESTAMP WITH TIME ZONE"
    assert _column_sql_for_dialect("VARCHAR(80)", postgresql.dialect()) == "VARCHAR(80)"


def test_initialize_schema_backfills_polish_session_summary_columns() -> None:
    temp_artifacts = ManagedTempArtifacts(test_id="api-db-schema-bootstrap")
    workspace = temp_artifacts.make_temp_dir("sqlite-db")
    try:
        db_url = f"sqlite+pysqlite:///{(workspace / 'bootstrap.sqlite').as_posix()}"
        settings = DbSettings(database_url=db_url)
        engine = build_session_factory(settings).kw["bind"]

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    CREATE TABLE interview_sessions (
                        binding_id VARCHAR(80),
                        resume_version_id VARCHAR(80),
                        job_version_id VARCHAR(80),
                        mode VARCHAR(32) NOT NULL,
                        id VARCHAR(80) NOT NULL PRIMARY KEY,
                        owner_id VARCHAR(80) NOT NULL,
                        actor_id VARCHAR(80),
                        record_version INTEGER NOT NULL,
                        status VARCHAR(64) NOT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        trace_ref_ids JSON,
                        evidence_ref_ids JSON
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    CREATE TABLE polish_session_details (
                        session_id VARCHAR(80) NOT NULL UNIQUE,
                        topic_ref_id VARCHAR(80),
                        subtopic_ref_id VARCHAR(80),
                        id VARCHAR(80) NOT NULL PRIMARY KEY,
                        owner_id VARCHAR(80) NOT NULL,
                        actor_id VARCHAR(80),
                        record_version INTEGER NOT NULL,
                        status VARCHAR(64) NOT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        trace_ref_ids JSON,
                        evidence_ref_ids JSON
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    CREATE TABLE questions (
                        session_id VARCHAR(80),
                        ai_task_id VARCHAR(80),
                        question_text TEXT,
                        id VARCHAR(80) NOT NULL PRIMARY KEY,
                        owner_id VARCHAR(80) NOT NULL,
                        actor_id VARCHAR(80),
                        record_version INTEGER NOT NULL,
                        status VARCHAR(64) NOT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        trace_ref_ids JSON,
                        evidence_ref_ids JSON
                    )
                    """
                )
            )

        initialize_schema(settings)

        inspector = inspect(build_session_factory(settings).kw["bind"])
        interview_columns = {column["name"] for column in inspector.get_columns("interview_sessions")}
        polish_detail_columns = {column["name"] for column in inspector.get_columns("polish_session_details")}
        question_columns = {column["name"] for column in inspector.get_columns("questions")}
        candidate_columns = {column["name"] for column in inspector.get_columns("polish_candidates")}
        weakness_columns = {column["name"] for column in inspector.get_columns("weaknesses")}
        asset_columns = {column["name"] for column in inspector.get_columns("assets")}
        asset_version_columns = {column["name"] for column in inspector.get_columns("asset_versions")}
        training_recommendation_columns = {column["name"] for column in inspector.get_columns("training_recommendations")}
        training_task_columns = {column["name"] for column in inspector.get_columns("training_tasks")}

        assert {"resume_id", "job_id"}.issubset(interview_columns)
        assert "custom_topic_text_summary" in polish_detail_columns
        assert "question_sources_json" in question_columns
        assert "question_metadata_json" in question_columns
        assert {
            "candidate_id",
            "owner_id",
            "candidate_type",
            "status",
            "source_type",
            "source_refs_json",
            "evidence_refs_json",
            "trace_refs_json",
            "session_id",
            "question_id",
            "answer_id",
            "feedback_id",
            "title",
            "summary",
            "evidence_excerpt",
            "reason",
            "confidence_level",
            "merge_key",
            "merge_target_candidate_id",
            "target_formal_ref_json",
            "candidate_payload_json",
            "user_confirmation_required",
            "created_at",
            "updated_at",
            "dismissed_at",
            "confirmed_at",
            "archived_at",
        }.issubset(candidate_columns)
        assert {
            "title",
            "summary",
            "confidence_level",
            "source_refs_json",
            "evidence_refs_json",
            "trace_refs_json",
            "created_from_candidate_id",
            "user_confirmation_ref_json",
        }.issubset(weakness_columns)
        assert {
            "asset_type",
            "title",
            "summary",
            "content",
            "source_refs_json",
            "evidence_refs_json",
            "trace_refs_json",
            "created_from_candidate_id",
            "user_confirmation_ref_json",
            "fact_source",
        }.issubset(asset_columns)
        assert {
            "asset_id",
            "version_number",
            "content",
            "edit_summary",
            "created_by_actor_id",
            "created_from_candidate_id",
        }.issubset(asset_version_columns)
        assert {
            "title",
            "summary",
            "reason",
            "confidence_level",
            "source_refs_json",
            "evidence_refs_json",
            "trace_refs_json",
            "candidate_ref_json",
            "target_weakness_refs_json",
            "question_pattern",
            "expected_answer_dimensions_json",
            "created_from_candidate_id",
            "user_confirmation_ref_json",
            "dismissed_at",
        }.issubset(training_recommendation_columns)
        assert {
            "training_recommendation_id",
            "target_weakness_refs_json",
            "question_pattern",
            "expected_answer_dimensions_json",
            "source_refs_json",
            "evidence_refs_json",
            "trace_refs_json",
            "explicit_action_ref_json",
            "progress_update_hint_json",
            "started_at",
            "completed_at",
        }.issubset(training_task_columns)
    finally:
        temp_artifacts.cleanup()


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


def _column_names(inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}
