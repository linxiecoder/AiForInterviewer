"""后端启动配置、schema bootstrap 与脱敏日志测试。"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[2] / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.boundary import (  # noqa: E402
    AUTO_MIGRATE_ON_STARTUP_ENV,
    ENVIRONMENT_ENV,
    ApiSettings,
    get_settings,
)
from app.interview_record_contract import (  # noqa: E402
    API_DATABASE_PATH_ENV,
    DATABASE_URL_ENV,
)
from app.main import create_app  # noqa: E402
from app.persistence import describe_database_location  # noqa: E402


def test_settings_reads_local_dotenv_without_mutating_environment(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """本地启动可读取 .env，但不会把真实连接串写回进程环境。"""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql://dotenv_user:dotenv_password@localhost:55432/interviewer",
                "API_PORT=8123",
                "AUTO_MIGRATE_ON_STARTUP=false",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv(DATABASE_URL_ENV, raising=False)
    monkeypatch.delenv(API_DATABASE_PATH_ENV, raising=False)
    monkeypatch.delenv(AUTO_MIGRATE_ON_STARTUP_ENV, raising=False)
    monkeypatch.delenv(ENVIRONMENT_ENV, raising=False)

    settings = get_settings(env_file=env_file)

    assert settings.database_path.startswith("postgresql://dotenv_user:")
    assert settings.port == 8123
    assert settings.auto_migrate_on_startup is False
    assert os.getenv(DATABASE_URL_ENV) is None


def test_settings_ignores_dotenv_when_environment_is_test(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """测试环境不读取仓库 .env，避免本机真实数据库影响隔离测试。"""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=postgresql://dotenv_user:dotenv_password@localhost:55432/interviewer",
        encoding="utf-8",
    )
    sqlite_path = tmp_path / "api.sqlite3"
    monkeypatch.setenv(ENVIRONMENT_ENV, "test")
    monkeypatch.setenv(API_DATABASE_PATH_ENV, str(sqlite_path))
    monkeypatch.delenv(DATABASE_URL_ENV, raising=False)

    settings = get_settings(env_file=env_file)

    assert settings.database_path == str(sqlite_path)


def test_process_sqlite_path_overrides_dotenv_database_url(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """测试夹具显式设置 SQLite 路径时，不应被本地 .env 的 PG 地址覆盖。"""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=postgresql://dotenv_user:dotenv_password@localhost:55432/interviewer",
        encoding="utf-8",
    )
    sqlite_path = tmp_path / "fixture.sqlite3"
    monkeypatch.delenv(DATABASE_URL_ENV, raising=False)
    monkeypatch.delenv(ENVIRONMENT_ENV, raising=False)
    monkeypatch.setenv(API_DATABASE_PATH_ENV, str(sqlite_path))

    settings = get_settings(env_file=env_file)

    assert settings.database_path == str(sqlite_path)


def test_database_description_redacts_postgresql_password() -> None:
    """启动日志中的 PostgreSQL 描述不得暴露用户、密码或原始 DSN。"""
    description = describe_database_location(
        "postgresql://startup_user:startup_password@localhost:55432/interviewer",
    )

    assert description == "database=postgresql host=localhost port=55432 db=interviewer"
    assert "startup_password" not in description
    assert "startup_user" not in description


def test_startup_logs_docs_database_and_bootstraps_sqlite(
    tmp_path: Path,
    caplog,
) -> None:
    """FastAPI lifespan 会执行 SQLite schema bootstrap 并输出文档地址。"""
    database_path = tmp_path / "startup.sqlite3"
    settings = ApiSettings(
        title="startup-test",
        version="0.1.0",
        environment="test",
        api_prefix="/api/v1",
        host="127.0.0.1",
        port=8124,
        database_path=str(database_path),
        auto_migrate_on_startup=True,
    )
    app = create_app(settings)

    async def run_lifespan() -> None:
        with caplog.at_level(logging.INFO, logger="uvicorn.error"):
            async with app.router.lifespan_context(app):
                pass

    asyncio.run(run_lifespan())

    log_text = caplog.text
    assert database_path.exists()
    assert "API server ready" in log_text
    assert "API base URL: http://127.0.0.1:8124/api/v1" in log_text
    assert "Swagger UI: http://127.0.0.1:8124/docs" in log_text
    assert "OpenAPI JSON: http://127.0.0.1:8124/openapi.json" in log_text
    assert "Database: database=sqlite path=startup.sqlite3" in log_text
    assert "auto_migrate_on_startup=true" in log_text


def test_startup_can_disable_schema_bootstrap(
    tmp_path: Path,
    caplog,
) -> None:
    """AUTO_MIGRATE_ON_STARTUP=false 时启动日志稳定且不写入 schema。"""
    database_path = tmp_path / "startup-disabled.sqlite3"
    settings = ApiSettings(
        title="startup-test",
        version="0.1.0",
        environment="test",
        api_prefix="/api/v1",
        host="0.0.0.0",
        port=8125,
        database_path=str(database_path),
        auto_migrate_on_startup=False,
    )
    app = create_app(settings)

    async def run_lifespan() -> None:
        with caplog.at_level(logging.INFO, logger="uvicorn.error"):
            async with app.router.lifespan_context(app):
                pass

    asyncio.run(run_lifespan())

    assert not database_path.exists()
    assert "Database schema bootstrap disabled: auto_migrate_on_startup=false" in caplog.text
    assert "Swagger UI: http://127.0.0.1:8125/docs" in caplog.text
