from __future__ import annotations

from pathlib import Path
import sys

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

ROOT_DIR = Path(__file__).resolve().parents[2]
API_DIR = ROOT_DIR / "apps" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))


def _dotenv_database_url() -> str | None:
    dotenv_path = ROOT_DIR / ".env"
    if not dotenv_path.exists():
        return None
    values: dict[str, str] = {}
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        values[key] = value.strip().strip("\"'")
    return values.get("API_DATABASE_URL") or values.get("DATABASE_URL")

from app.infrastructure.db.base import Base
from app.infrastructure.db.session import DbSettings
import app.infrastructure.db.models  # noqa: F401

BASELINE_REVISION = "0001_initial_schema"
HEAD_REVISION = "head"
ALEMBIC_VERSION_TABLE = "alembic_version"


def main() -> int:
    database_url = _database_url()
    if database_url == "sqlite+pysqlite:///:memory:":
        print("[db] skip alembic upgrade: in-memory SQLite is test-only")
        return 0

    config = _alembic_config(database_url)
    engine = create_engine(database_url, future=True)
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    if ALEMBIC_VERSION_TABLE in table_names:
        command.upgrade(config, HEAD_REVISION)
        return 0

    application_tables = set(Base.metadata.tables)
    existing_application_tables = table_names & application_tables
    if not existing_application_tables:
        command.upgrade(config, HEAD_REVISION)
        return 0

    missing_tables = sorted(application_tables - table_names)
    if missing_tables:
        joined = ", ".join(missing_tables[:12])
        suffix = " ..." if len(missing_tables) > 12 else ""
        raise RuntimeError(
            "Refusing to stamp a partial legacy schema. "
            f"Missing application tables: {joined}{suffix}"
        )

    print(
        "[db] legacy unversioned application schema detected; "
        f"stamping {BASELINE_REVISION} before upgrade"
    )
    command.stamp(config, BASELINE_REVISION)
    command.upgrade(config, HEAD_REVISION)
    return 0


def _alembic_config(database_url: str) -> Config:
    config = Config(str(ROOT_DIR / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def _database_url() -> str:
    settings_url = DbSettings().database_url
    if settings_url != "sqlite+pysqlite:///:memory:":
        return settings_url
    return _dotenv_database_url() or settings_url


if __name__ == "__main__":
    raise SystemExit(main())
