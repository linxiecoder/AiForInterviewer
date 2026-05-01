"""应用边界配置与共享 error envelope 辅助函数。"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.interview_record_contract import (
    API_DATABASE_PATH_ENV,
    DATABASE_URL_ENV,
    DEFAULT_DATABASE_DIR,
    DEFAULT_DATABASE_FILE,
)

API_TITLE_ENV = "API_TITLE"
API_VERSION_ENV = "API_VERSION"
ENVIRONMENT_ENV = "ENVIRONMENT"
API_PREFIX_ENV = "API_PREFIX"
API_HOST_ENV = "API_HOST"
API_PORT_ENV = "API_PORT"
AUTO_MIGRATE_ON_STARTUP_ENV = "AUTO_MIGRATE_ON_STARTUP"
DEFAULT_API_TITLE = "ai-for-interviewer"
DEFAULT_API_VERSION = "0.1.0"
DEFAULT_ENVIRONMENT = "development"
DEFAULT_API_PREFIX = "/api/v1"
DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 8001
DEFAULT_AUTO_MIGRATE_ON_STARTUP = True
DEFAULT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"
ERROR_KEY = "error"
ERROR_CODE_KEY = "code"
ERROR_MESSAGE_KEY = "message"
ERROR_REQUEST_ID_KEY = "request_id"
ERROR_DETAILS_KEY = "details"
HTTP_ERROR_CODE_PREFIX = "HTTP"
REQUEST_VALIDATION_ERROR_MESSAGE = "request validation failed"
REQUEST_VALIDATION_ERROR_STATUS_CODE = 422


@dataclass(frozen=True)
class ApiSettings:
    """FastAPI 应用边界运行配置。"""

    title: str
    version: str
    environment: str
    api_prefix: str
    host: str
    port: int
    database_path: str
    auto_migrate_on_startup: bool


def get_settings(env_file: Path | None = None) -> ApiSettings:
    """读取环境变量和本地 .env，返回 API 运行配置。"""
    dotenv_values = _load_local_env_file(env_file)
    return ApiSettings(
        title=_env(API_TITLE_ENV, DEFAULT_API_TITLE, dotenv_values),
        version=_env(API_VERSION_ENV, DEFAULT_API_VERSION, dotenv_values),
        environment=_env(ENVIRONMENT_ENV, DEFAULT_ENVIRONMENT, dotenv_values),
        api_prefix=_normalize_prefix(_env(API_PREFIX_ENV, DEFAULT_API_PREFIX, dotenv_values)),
        host=_env(API_HOST_ENV, DEFAULT_API_HOST, dotenv_values),
        port=_env_int(API_PORT_ENV, DEFAULT_API_PORT, dotenv_values),
        database_path=_database_location(dotenv_values),
        auto_migrate_on_startup=_env_bool(
            AUTO_MIGRATE_ON_STARTUP_ENV,
            DEFAULT_AUTO_MIGRATE_ON_STARTUP,
            dotenv_values,
        ),
    )


def build_error_payload(
    *,
    code: str,
    message: str,
    request_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """构造共享 error envelope，并保留可选 provider 元数据。"""
    error: dict[str, Any] = {ERROR_CODE_KEY: code, ERROR_MESSAGE_KEY: message}
    if request_id is not None:
        error[ERROR_REQUEST_ID_KEY] = request_id
    if details is not None:
        error[ERROR_DETAILS_KEY] = details
    return {ERROR_KEY: error}


async def http_exception_handler(
    _request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Adapt FastAPI HTTP exceptions to the project error envelope."""
    message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_payload(
            code=f"{HTTP_ERROR_CODE_PREFIX}_{exc.status_code}",
            message=message,
        ),
        headers=exc.headers,
    )


async def validation_exception_handler(
    _request: Request,
    _exc: RequestValidationError,
) -> JSONResponse:
    """Adapt request validation failures to the project error envelope."""
    return JSONResponse(
        status_code=REQUEST_VALIDATION_ERROR_STATUS_CODE,
        content=build_error_payload(
            code=f"{HTTP_ERROR_CODE_PREFIX}_{REQUEST_VALIDATION_ERROR_STATUS_CODE}",
            message=REQUEST_VALIDATION_ERROR_MESSAGE,
        ),
    )


def _env(name: str, default: str, dotenv_values: dict[str, str] | None = None) -> str:
    value = _env_optional(name, dotenv_values)
    return value if value is not None else default


def _env_int(name: str, default: int, dotenv_values: dict[str, str] | None = None) -> int:
    value = _env_optional(name, dotenv_values)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_bool(name: str, default: bool, dotenv_values: dict[str, str] | None = None) -> bool:
    value = _env_optional(name, dotenv_values)
    if value is None:
        return default
    normalized = value.lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _database_location(dotenv_values: dict[str, str] | None = None) -> str:
    database_url = _clean_env_value(os.getenv(DATABASE_URL_ENV))
    if database_url is not None:
        return database_url
    process_sqlite_path = _clean_env_value(os.getenv(API_DATABASE_PATH_ENV))
    if process_sqlite_path is not None:
        return process_sqlite_path
    if DATABASE_URL_ENV not in os.environ and dotenv_values is not None:
        dotenv_database_url = _clean_env_value(dotenv_values.get(DATABASE_URL_ENV))
        if dotenv_database_url is not None:
            return dotenv_database_url
    return _env(
        API_DATABASE_PATH_ENV,
        os.path.join(tempfile.gettempdir(), DEFAULT_DATABASE_DIR, DEFAULT_DATABASE_FILE),
        dotenv_values,
    )


def _normalize_prefix(prefix: str) -> str:
    normalized = prefix.strip() or DEFAULT_API_PREFIX
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    return normalized.rstrip("/") or "/"


def _env_optional(name: str, dotenv_values: dict[str, str] | None = None) -> str | None:
    if name in os.environ:
        return _clean_env_value(os.getenv(name))
    if dotenv_values is None:
        return None
    return _clean_env_value(dotenv_values.get(name))


def _clean_env_value(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if cleaned.startswith("<") and cleaned.endswith(">"):
        return None
    return cleaned


def _load_local_env_file(env_file: Path | None = None) -> dict[str, str]:
    if os.getenv(ENVIRONMENT_ENV, "").strip().lower() == "test":
        return {}
    path = env_file or DEFAULT_ENV_FILE
    if not path.is_file():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        name, raw_value = line.split("=", 1)
        key = name.strip()
        if not key:
            continue
        values[key] = _strip_env_quotes(raw_value.strip())
    return values


def _strip_env_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value
