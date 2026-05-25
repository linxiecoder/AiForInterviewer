from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

import app.infrastructure.db.session as db_session
from tools.testing.temp_artifacts import ManagedTempArtifacts


def test_session_runtime_backfill_symbols_are_removed() -> None:
    assert not hasattr(db_session, "_KNOWN_SCHEMA_COLUMN_BACKFILLS")
    assert not hasattr(db_session, "_backfill_known_schema_columns")
    assert "ALTER TABLE" not in Path(db_session.__file__).read_text(encoding="utf-8")


def test_alembic_upgrade_creates_version_and_representative_tables(monkeypatch) -> None:
    temp_artifacts = ManagedTempArtifacts(test_id="api-alembic-upgrade")
    workspace = temp_artifacts.make_temp_dir("sqlite-db")
    try:
        db_url = f"sqlite+pysqlite:///{(workspace / 'alembic.sqlite').as_posix()}"
        monkeypatch.setenv("API_DATABASE_URL", db_url)

        config = Config("alembic.ini")
        command.upgrade(config, "head")

        engine = create_engine(db_url, future=True)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        assert "alembic_version" in tables
        assert {
            "user_accounts",
            "jobs",
            "job_versions",
            "resumes",
            "resume_versions",
            "interview_sessions",
            "questions",
            "answers",
            "ai_tasks",
            "agent_runs",
            "llm_calls",
            "interview_reports",
            "weaknesses",
            "training_recommendations",
        }.issubset(tables)
        with engine.connect() as connection:
            version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert version == "0002_known_column_backfills"
    finally:
        temp_artifacts.cleanup()


def test_known_column_backfill_revision_is_idempotent(monkeypatch) -> None:
    temp_artifacts = ManagedTempArtifacts(test_id="api-alembic-backfill")
    workspace = temp_artifacts.make_temp_dir("sqlite-db")
    try:
        db_url = f"sqlite+pysqlite:///{(workspace / 'legacy.sqlite').as_posix()}"
        monkeypatch.setenv("API_DATABASE_URL", db_url)

        config = Config("alembic.ini")
        command.upgrade(config, "0001_initial_schema")

        engine = create_engine(db_url, future=True)
        before_columns = set(_column_names(engine, "questions"))

        command.upgrade(config, "head")
        command.downgrade(config, "0001_initial_schema")
        command.upgrade(config, "head")

        after_columns = set(_column_names(engine, "questions"))
        assert before_columns == after_columns
        assert {"question_sources_json", "question_metadata_json"}.issubset(after_columns)
    finally:
        temp_artifacts.cleanup()


def _column_names(engine, table_name: str) -> list[str]:
    return [column["name"] for column in inspect(engine).get_columns(table_name)]
