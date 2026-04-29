from __future__ import annotations

import os
from dataclasses import dataclass

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


@dataclass(frozen=True)
class ApiSettings:
    title: str
    version: str
    environment: str
    api_prefix: str
    host: str
    port: int


def get_settings() -> ApiSettings:
    return ApiSettings(
        title=_env("API_TITLE", "ai-for-interviewer"),
        version=_env("API_VERSION", "0.1.0"),
        environment=_env("ENVIRONMENT", "development"),
        api_prefix=_normalize_prefix(_env("API_PREFIX", "/api/v1")),
        host=_env("API_HOST", "127.0.0.1"),
        port=_env_int("API_PORT", 8001),
    )


def build_error_payload(*, code: str, message: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message}}


async def http_exception_handler(
    _request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_payload(
            code=f"HTTP_{exc.status_code}",
            message=message,
        ),
        headers=exc.headers,
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
    normalized = prefix.strip() or "/api/v1"
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    return normalized.rstrip("/") or "/"
