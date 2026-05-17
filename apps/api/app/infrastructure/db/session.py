"""Database session factory placeholder."""

from dataclasses import dataclass
from os import getenv

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@dataclass(frozen=True)
class DbSettings:
    database_url: str = getenv("API_DATABASE_URL", "sqlite+pysqlite:///:memory:")


def build_session_factory(settings: DbSettings | None = None) -> sessionmaker[Session]:
    resolved = settings or DbSettings()
    engine = create_engine(resolved.database_url, future=True)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

