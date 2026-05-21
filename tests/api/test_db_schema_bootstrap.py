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

        assert {"resume_id", "job_id"}.issubset(interview_columns)
        assert "custom_topic_text_summary" in polish_detail_columns
        assert "question_sources_json" in question_columns
        assert "question_metadata_json" in question_columns
    finally:
        temp_artifacts.cleanup()
