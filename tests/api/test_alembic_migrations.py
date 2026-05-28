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
            "rag_documents",
            "rag_chunks",
        }.issubset(tables)
        with engine.connect() as connection:
            version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert version == "0003_asset_rag_pgvector"
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


def test_asset_rag_revision_preserves_legacy_unversioned_rag_tables(monkeypatch) -> None:
    temp_artifacts = ManagedTempArtifacts(test_id="api-alembic-rag-legacy")
    workspace = temp_artifacts.make_temp_dir("sqlite-db")
    try:
        db_url = f"sqlite+pysqlite:///{(workspace / 'legacy-rag.sqlite').as_posix()}"
        monkeypatch.setenv("API_DATABASE_URL", db_url)

        config = Config("alembic.ini")
        command.upgrade(config, "0002_known_column_backfills")

        engine = create_engine(db_url, future=True)
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    CREATE TABLE rag_documents (
                        id TEXT PRIMARY KEY,
                        owner_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        visibility TEXT NOT NULL,
                        source_type TEXT NOT NULL,
                        source_label TEXT NOT NULL,
                        content_summary TEXT NOT NULL,
                        source_version TEXT NOT NULL,
                        index_status TEXT NOT NULL,
                        failure_reason TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    CREATE TABLE rag_chunks (
                        id TEXT PRIMARY KEY,
                        owner_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        resource_id TEXT NOT NULL,
                        chunk_ref TEXT NOT NULL,
                        chunk_index INTEGER NOT NULL,
                        visibility TEXT NOT NULL,
                        source_type TEXT NOT NULL,
                        source_label TEXT NOT NULL,
                        content_summary TEXT NOT NULL,
                        source_version TEXT NOT NULL,
                        start_offset INTEGER NOT NULL,
                        end_offset INTEGER NOT NULL,
                        index_status TEXT NOT NULL,
                        failure_reason TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO rag_documents (
                        id, owner_id, document_id, visibility, source_type, source_label,
                        content_summary, source_version, index_status, created_at, updated_at
                    )
                    VALUES (
                        'legacy_doc_1', 'owner_1', 'legacy_doc_1', 'owner_only',
                        'private_document', 'Legacy Doc', 'legacy summary',
                        'v1', 'indexed', '2026-05-01T00:00:00Z', '2026-05-01T00:00:00Z'
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO rag_chunks (
                        id, owner_id, document_id, resource_id, chunk_ref, chunk_index,
                        visibility, source_type, source_label, content_summary, source_version,
                        start_offset, end_offset, index_status, created_at, updated_at
                    )
                    VALUES (
                        'legacy_chunk_1', 'owner_1', 'legacy_doc_1', 'legacy_doc_1',
                        'legacy_doc_1:chunk-0', 0, 'owner_only', 'private_document',
                        'Legacy Doc', 'legacy chunk', 'v1', 0, 12, 'indexed',
                        '2026-05-01T00:00:00Z', '2026-05-01T00:00:00Z'
                    )
                    """
                )
            )

        command.upgrade(config, "head")

        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert {
            "rag_documents",
            "rag_chunks",
            "rag_documents_legacy_pre_0003",
            "rag_chunks_legacy_pre_0003",
        }.issubset(tables)
        assert {"source_id", "title", "metadata_json"}.issubset(_column_names(engine, "rag_documents"))
        assert {"source_id", "asset_id", "content", "embedding"}.issubset(_column_names(engine, "rag_chunks"))

        with engine.connect() as connection:
            version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            legacy_documents = connection.execute(
                text("SELECT COUNT(*) FROM rag_documents_legacy_pre_0003")
            ).scalar_one()
            legacy_chunks = connection.execute(text("SELECT COUNT(*) FROM rag_chunks_legacy_pre_0003")).scalar_one()
        assert version == "0003_asset_rag_pgvector"
        assert legacy_documents == 1
        assert legacy_chunks == 1
    finally:
        temp_artifacts.cleanup()


def _column_names(engine, table_name: str) -> list[str]:
    return [column["name"] for column in inspect(engine).get_columns(table_name)]
