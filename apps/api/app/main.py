"""FastAPI 应用工厂。"""

from contextlib import asynccontextmanager
from dataclasses import dataclass
import os
from typing import Iterable

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.errors import ApiHttpError, api_http_error_handler
from app.api.v1 import build_api_v1_router
from app.infrastructure.db.session import DbSettings, configure_session_factory
from app.infrastructure.llm.job_match import LlmJobMatchAnalyzer
from app.infrastructure.llm.runtime import build_llm_transport_from_env
from app.infrastructure.observability.http_logging import HttpAccessLogMiddleware
from app.infrastructure.observability.logging import BackendLogSettings, LogUtil
from app.infrastructure.security.auth import AuthRuntime, build_auth_runtime_from_env

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
API_DEBUG_ENV = "API_DEBUG"
API_CORS_ALLOW_ORIGINS_ENV = "API_CORS_ALLOW_ORIGINS"
API_CORS_LOCAL_LIKE_ENV_VALUES = {"local", "test", "development", "dev"}
DEFAULT_CORS_ALLOW_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:5174",
    "http://localhost:5174",
)
DEFAULT_CORS_METHODS = ("GET", "POST", "PATCH", "DELETE", "OPTIONS")
DEFAULT_CORS_HEADERS = ("Content-Type", "Accept", "Authorization")


@dataclass(frozen=True)
class ApiSettings:
    """FastAPI 入口运行配置。"""

    title: str = DEFAULT_API_TITLE
    version: str = DEFAULT_API_VERSION
    api_prefix: str = DEFAULT_API_PREFIX
    host: str = DEFAULT_API_HOST
    port: int = DEFAULT_API_PORT
    debug: bool = False
    cors_allow_origins: tuple[str, ...] = ()


def get_settings() -> ApiSettings:
    """读取当前保留 API 入口需要的最小运行配置。"""
    return ApiSettings(
        title=_env(API_TITLE_ENV, DEFAULT_API_TITLE),
        version=_env(API_VERSION_ENV, DEFAULT_API_VERSION),
        api_prefix=_normalize_prefix(_env(API_PREFIX_ENV, DEFAULT_API_PREFIX)),
        host=_env(API_HOST_ENV, DEFAULT_API_HOST),
        port=_env_int(API_PORT_ENV, DEFAULT_API_PORT),
        debug=_env_bool(API_DEBUG_ENV, False),
        cors_allow_origins=_read_cors_allow_origins(),
    )


def create_app(
    settings: ApiSettings | None = None,
    *,
    initialize_schema: bool = True,
    auth_runtime: AuthRuntime | None = None,
    db_settings: DbSettings | None = None,
) -> FastAPI:
    """构建当前保留的 API app，并初始化当前 SQLAlchemy schema。"""
    resolved_settings = settings or get_settings()
    LogUtil.configure(
        BackendLogSettings(level="DEBUG" if resolved_settings.debug else "INFO")
    )
    db_session_factory = configure_session_factory(
        db_settings,
        initialize=initialize_schema,
    )

    @asynccontextmanager
    async def lifespan(_application: FastAPI):
        _log_runtime_ready(resolved_settings)
        yield

    application = FastAPI(
        title=resolved_settings.title,
        version=resolved_settings.version,
        debug=resolved_settings.debug,
        lifespan=lifespan,
    )
    application.state.settings = resolved_settings
    application.state.db_session_factory = db_session_factory
    application.state.llm_transport = build_llm_transport_from_env()
    application.state.job_match_analyzer = LlmJobMatchAnalyzer(application.state.llm_transport)
    application.state.auth_runtime = auth_runtime or build_auth_runtime_from_env(
        cookie_path=resolved_settings.api_prefix
    )
    _add_cors_middleware(application, resolved_settings.cors_allow_origins)
    application.add_middleware(HttpAccessLogMiddleware)
    application.add_exception_handler(ApiHttpError, api_http_error_handler)
    application.include_router(build_api_v1_router(resolved_settings.api_prefix))
    return application


def _log_runtime_ready(settings: ApiSettings) -> None:
    for line in _startup_log_lines(settings):
        LogUtil.api_runtime_ready(message=line)


def _startup_log_lines(settings: ApiSettings) -> tuple[str, ...]:
    server_url = _server_url(settings)
    return (
        "API server ready",
        f"API debug: {'enabled' if settings.debug else 'disabled'}",
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


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _env_optional(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    return value.strip() or None


def _read_cors_allow_origins() -> tuple[str, ...]:
    configured = _env_optional(API_CORS_ALLOW_ORIGINS_ENV)
    if configured is None:
        env_mode = _read_env_mode()
        if env_mode in API_CORS_LOCAL_LIKE_ENV_VALUES:
            return DEFAULT_CORS_ALLOW_ORIGINS
        return tuple()
    origins = _parse_cors_origins(configured)
    return tuple(_filter_cors_wildcards(origins))


def _read_env_mode() -> str:
    return (
        _env("API_AUTH_ENV", _env("API_ENV", "local")).strip().lower()
        or "local"
    )


def _parse_cors_origins(raw: str) -> tuple[str, ...]:
    values = (value.strip() for value in raw.split(","))
    return tuple(value for value in values if value)


def _filter_cors_wildcards(origins: tuple[str, ...]) -> tuple[str, ...]:
    if "*" in origins:
        LogUtil.api_cors_wildcard_dropped()
    return tuple(dict.fromkeys(origin for origin in origins if origin != "*"))


def _add_cors_middleware(application: FastAPI, cors_allow_origins: Iterable[str]) -> None:
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(cors_allow_origins),
        allow_credentials=True,
        allow_methods=DEFAULT_CORS_METHODS,
        allow_headers=DEFAULT_CORS_HEADERS,
    )


def _normalize_prefix(prefix: str) -> str:
    normalized = prefix.strip() or DEFAULT_API_PREFIX
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    return normalized.rstrip("/") or "/"


settings = get_settings()
app = create_app(settings)
