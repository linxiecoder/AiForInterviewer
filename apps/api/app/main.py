"""FastAPI 应用工厂。"""

from contextlib import asynccontextmanager
from dataclasses import dataclass
import logging
import os

from fastapi import FastAPI

from app.api.v1 import build_api_v1_router

STARTUP_LOGGER = logging.getLogger("uvicorn.error")
DEFAULT_API_TITLE = "ai-for-interviewer"
DEFAULT_API_VERSION = "0.1.0"
DEFAULT_API_PREFIX = "/api/v1"
DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 8001
API_TITLE_ENV = "API_TITLE"
API_VERSION_ENV = "API_VERSION"
API_PREFIX_ENV = "API_PREFIX"
API_HOST_ENV = "API_HOST"
API_PORT_ENV = "API_PORT"


@dataclass(frozen=True)
class ApiSettings:
    """FastAPI 入口运行配置。"""

    title: str = DEFAULT_API_TITLE
    version: str = DEFAULT_API_VERSION
    api_prefix: str = DEFAULT_API_PREFIX
    host: str = DEFAULT_API_HOST
    port: int = DEFAULT_API_PORT


def get_settings() -> ApiSettings:
    """读取当前保留 API 入口需要的最小运行配置。"""
    return ApiSettings(
        title=_env(API_TITLE_ENV, DEFAULT_API_TITLE),
        version=_env(API_VERSION_ENV, DEFAULT_API_VERSION),
        api_prefix=_normalize_prefix(_env(API_PREFIX_ENV, DEFAULT_API_PREFIX)),
        host=_env(API_HOST_ENV, DEFAULT_API_HOST),
        port=_env_int(API_PORT_ENV, DEFAULT_API_PORT),
    )


def create_app(
    settings: ApiSettings | None = None,
    *,
    initialize_schema: bool = False,
) -> FastAPI:
    """构建当前保留的 API app；legacy schema 初始化已随旧持久化层删除。"""
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(_application: FastAPI):
        if initialize_schema:
            STARTUP_LOGGER.info("Schema initialization skipped: no active persistence schema")
        _log_runtime_ready(resolved_settings)
        yield

    application = FastAPI(
        title=resolved_settings.title,
        version=resolved_settings.version,
        lifespan=lifespan,
    )
    application.state.settings = resolved_settings
    application.include_router(build_api_v1_router(resolved_settings.api_prefix))
    return application


def _log_runtime_ready(settings: ApiSettings) -> None:
    for line in _startup_log_lines(settings):
        STARTUP_LOGGER.info(line)


def _startup_log_lines(settings: ApiSettings) -> tuple[str, ...]:
    server_url = _server_url(settings)
    return (
        "API server ready",
        f"API base URL: {server_url}{settings.api_prefix}",
        f"Swagger UI: {server_url}/docs",
        f"OpenAPI JSON: {server_url}/openapi.json",
    )


def _server_url(settings: ApiSettings) -> str:
    host = "127.0.0.1" if settings.host in {"0.0.0.0", "::"} else settings.host
    return f"http://{host}:{settings.port}"


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    stripped = value.strip()
    return stripped or default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
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


settings = get_settings()
app = create_app(settings)
