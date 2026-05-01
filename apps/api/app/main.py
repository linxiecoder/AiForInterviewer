"""FastAPI 应用工厂。"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import build_api_v1_router
from app.boundary import (
    ApiSettings,
    get_settings,
    http_exception_handler,
    validation_exception_handler,
)
from app.persistence import (
    InterviewRecordStore,
    RAGPersistenceStore,
    TraceabilityStore,
    describe_database_location,
)

STARTUP_LOGGER = logging.getLogger("uvicorn.error")


def create_app(
    settings: ApiSettings | None = None,
    *,
    initialize_schema: bool = False,
) -> FastAPI:
    """构建 API app，避免在模块导入阶段写数据库 schema。"""
    resolved_settings = settings or get_settings()
    store = InterviewRecordStore(resolved_settings.database_path)
    traceability_store = TraceabilityStore(resolved_settings.database_path)
    rag_persistence_store = RAGPersistenceStore(resolved_settings.database_path)

    @asynccontextmanager
    async def lifespan(_application: FastAPI) -> AsyncIterator[None]:
        if not initialize_schema:
            if resolved_settings.auto_migrate_on_startup:
                _initialize_runtime_schema(
                    store=store,
                    traceability_store=traceability_store,
                    rag_persistence_store=rag_persistence_store,
                )
            else:
                STARTUP_LOGGER.info(
                    "Database schema bootstrap disabled: auto_migrate_on_startup=false"
                )
        _log_runtime_ready(resolved_settings)
        yield

    application = FastAPI(
        title=resolved_settings.title,
        version=resolved_settings.version,
        lifespan=lifespan,
    )
    application.add_exception_handler(StarletteHTTPException, http_exception_handler)
    application.add_exception_handler(RequestValidationError, validation_exception_handler)
    application.state.settings = resolved_settings
    application.state.interview_record_store = store
    application.state.traceability_store = traceability_store
    application.state.rag_persistence_store = rag_persistence_store
    if initialize_schema:
        store.initialize()
        traceability_store.initialize()
        rag_persistence_store.initialize()
    application.include_router(build_api_v1_router(resolved_settings.api_prefix))
    return application


def _initialize_runtime_schema(
    *,
    store: InterviewRecordStore,
    traceability_store: TraceabilityStore,
    rag_persistence_store: RAGPersistenceStore,
) -> None:
    try:
        store.initialize()
        traceability_store.initialize()
        rag_persistence_store.initialize()
    except Exception:
        STARTUP_LOGGER.exception("Database schema bootstrap failed")
        raise


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
        (
            "Database: "
            f"{describe_database_location(settings.database_path)}, "
            f"auto_migrate_on_startup={str(settings.auto_migrate_on_startup).lower()}"
        ),
    )


def _server_url(settings: ApiSettings) -> str:
    host = "127.0.0.1" if settings.host in {"0.0.0.0", "::"} else settings.host
    return f"http://{host}:{settings.port}"


settings = get_settings()
app = create_app(settings)
