from __future__ import annotations

from sqlalchemy import inspect, text

from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema
from tools.testing.temp_artifacts import ManagedTempArtifacts


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
