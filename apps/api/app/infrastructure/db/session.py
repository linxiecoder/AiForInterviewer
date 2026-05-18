"""Database session factory and schema bootstrap helpers."""

from dataclasses import dataclass
from dataclasses import field
from os import getenv

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.db.base import Base


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
