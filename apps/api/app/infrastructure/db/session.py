"""Database session factory and schema bootstrap helpers."""

from dataclasses import dataclass
from dataclasses import field
from os import getenv

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.db.base import Base


_KNOWN_SCHEMA_COLUMN_BACKFILLS: tuple[tuple[str, str, str], ...] = (
    ("interview_sessions", "resume_id", "VARCHAR(80)"),
    ("interview_sessions", "job_id", "VARCHAR(80)"),
    ("polish_session_details", "custom_topic_text_summary", "VARCHAR(240)"),
    ("polish_session_details", "progress_tree_status", "VARCHAR(40)"),
    ("polish_session_details", "progress_percent", "INTEGER"),
    ("polish_session_details", "progress_tree_plan_json", "JSON"),
    ("polish_session_details", "progress_tree_state_json", "JSON"),
    ("questions", "question_sources_json", "JSON"),
    ("questions", "question_metadata_json", "JSON"),
    ("questions", "progress_node_ref", "VARCHAR(120)"),
    ("questions", "context_digest", "VARCHAR(120)"),
    ("questions", "evidence_ref_ids", "JSON"),
    ("weaknesses", "title", "VARCHAR(160)"),
    ("weaknesses", "summary", "TEXT"),
    ("weaknesses", "severity_hint", "VARCHAR(40)"),
    ("weaknesses", "confidence_level", "VARCHAR(40)"),
    ("weaknesses", "source_refs_json", "JSON"),
    ("weaknesses", "session_refs_json", "JSON"),
    ("weaknesses", "feedback_refs_json", "JSON"),
    ("weaknesses", "question_refs_json", "JSON"),
    ("weaknesses", "answer_refs_json", "JSON"),
    ("weaknesses", "loss_point_refs_json", "JSON"),
    ("weaknesses", "repeated_loss_point_refs_json", "JSON"),
    ("weaknesses", "evidence_refs_json", "JSON"),
    ("weaknesses", "trace_refs_json", "JSON"),
    ("weaknesses", "user_confirmation_ref_json", "JSON"),
    ("weaknesses", "occurrence_count", "INTEGER"),
    ("weaknesses", "first_seen_at", "DATETIME"),
    ("weaknesses", "last_seen_at", "DATETIME"),
    ("weaknesses", "archived_at", "DATETIME"),
    ("assets", "asset_type", "VARCHAR(64)"),
    ("assets", "title", "VARCHAR(160)"),
    ("assets", "summary", "TEXT"),
    ("assets", "content", "TEXT"),
    ("assets", "source_refs_json", "JSON"),
    ("assets", "evidence_refs_json", "JSON"),
    ("assets", "trace_refs_json", "JSON"),
    ("assets", "resume_version_ref_json", "JSON"),
    ("assets", "job_version_ref_json", "JSON"),
    ("assets", "question_pattern", "VARCHAR(120)"),
    ("assets", "created_from_candidate_id", "VARCHAR(80)"),
    ("assets", "user_confirmation_ref_json", "JSON"),
    ("assets", "fact_source", "VARCHAR(80)"),
    ("asset_versions", "content", "TEXT"),
    ("asset_versions", "edit_summary", "TEXT"),
    ("asset_versions", "created_by_actor_id", "VARCHAR(80)"),
)


@dataclass(frozen=True)
class DbSettings:
    database_url: str = field(default_factory=lambda: _default_database_url())


_session_factory: sessionmaker[Session] | None = None


def build_session_factory(settings: DbSettings | None = None) -> sessionmaker[Session]:
    resolved = settings or DbSettings()
    engine = _build_engine(resolved.database_url)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def configure_session_factory(
    settings: DbSettings | None = None,
    *,
    initialize: bool = True,
) -> sessionmaker[Session]:
    global _session_factory
    _session_factory = build_session_factory(settings)
    if initialize:
        initialize_schema(session_factory=_session_factory)
    return _session_factory


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = configure_session_factory()
    return _session_factory


def initialize_schema(
    settings: DbSettings | None = None,
    *,
    session_factory: sessionmaker[Session] | None = None,
) -> None:
    _load_models()
    factory = session_factory or build_session_factory(settings)
    bind = factory.kw["bind"]
    Base.metadata.create_all(bind=bind)
    _backfill_known_schema_columns(bind)


def _build_engine(database_url: str) -> Engine:
    if database_url == "sqlite+pysqlite:///:memory:":
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            future=True,
        )
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            future=True,
        )
    return create_engine(database_url, future=True)


def _default_database_url() -> str:
    return (
        getenv("API_DATABASE_URL")
        or getenv("DATABASE_URL")
        or "sqlite+pysqlite:///:memory:"
    )


def _load_models() -> None:
    import app.infrastructure.db.models  # noqa: F401


def _backfill_known_schema_columns(bind: Engine) -> None:
    inspector = inspect(bind)
    table_names = set(inspector.get_table_names())
    if not table_names:
        return

    with bind.begin() as connection:
        for table_name, column_name, column_sql in _KNOWN_SCHEMA_COLUMN_BACKFILLS:
            if table_name not in table_names:
                continue
            columns = {column["name"] for column in inspector.get_columns(table_name)}
            if column_name in columns:
                continue
            connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"))
