"""Application boundary settings and shared error-envelope helpers."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.interview_record_contract import (
    API_DATABASE_PATH_ENV,
    DEFAULT_DATABASE_DIR,
    DEFAULT_DATABASE_FILE,
)

API_TITLE_ENV = "API_TITLE"
API_VERSION_ENV = "API_VERSION"
ENVIRONMENT_ENV = "ENVIRONMENT"
API_PREFIX_ENV = "API_PREFIX"
API_HOST_ENV = "API_HOST"
API_PORT_ENV = "API_PORT"
DEFAULT_API_TITLE = "ai-for-interviewer"
DEFAULT_API_VERSION = "0.1.0"
DEFAULT_ENVIRONMENT = "development"
DEFAULT_API_PREFIX = "/api/v1"
DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 8001
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
    """Runtime settings consumed by the FastAPI application boundary."""

    title: str
    version: str
    environment: str
    api_prefix: str
    host: str
    port: int
    database_path: str


def get_settings() -> ApiSettings:
    """Read API settings from environment variables with local defaults."""
    return ApiSettings(
        title=_env(API_TITLE_ENV, DEFAULT_API_TITLE),
        version=_env(API_VERSION_ENV, DEFAULT_API_VERSION),
        environment=_env(ENVIRONMENT_ENV, DEFAULT_ENVIRONMENT),
        api_prefix=_normalize_prefix(_env(API_PREFIX_ENV, DEFAULT_API_PREFIX)),
        host=_env(API_HOST_ENV, DEFAULT_API_HOST),
        port=_env_int(API_PORT_ENV, DEFAULT_API_PORT),
        database_path=_env(
            API_DATABASE_PATH_ENV,
            os.path.join(tempfile.gettempdir(), DEFAULT_DATABASE_DIR, DEFAULT_DATABASE_FILE),
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


def _env(name: str, default: str) -> str:
    value = os.getenv(name, default).strip()
    return value or default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _normalize_prefix(prefix: str) -> str:
    normalized = prefix.strip() or DEFAULT_API_PREFIX
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    return normalized.rstrip("/") or "/"
