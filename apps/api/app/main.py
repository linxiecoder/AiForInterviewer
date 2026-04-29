from fastapi import FastAPI
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import build_api_v1_router
from app.boundary import get_settings, http_exception_handler

settings = get_settings()

app = FastAPI(title=settings.title, version=settings.version)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

app.include_router(build_api_v1_router(settings.api_prefix))
