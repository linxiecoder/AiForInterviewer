"""FastAPI application factory for the API service boundary."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

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
from app.persistence import InterviewRecordStore


def create_app(
    settings: ApiSettings | None = None,
    *,
    initialize_schema: bool = False,
) -> FastAPI:
    """Build the API app without writing database schema during module import."""
    resolved_settings = settings or get_settings()
    store = InterviewRecordStore(resolved_settings.database_path)

    @asynccontextmanager
    async def lifespan(_application: FastAPI) -> AsyncIterator[None]:
        # Runtime schema initialization belongs to app startup; tests can opt
        # into initialize_schema=True for a local temporary database.
        if not initialize_schema:
            store.initialize()
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
    if initialize_schema:
        store.initialize()
    application.include_router(build_api_v1_router(resolved_settings.api_prefix))
    return application


settings = get_settings()
app = create_app(settings)
