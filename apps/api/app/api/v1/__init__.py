from fastapi import APIRouter

from app.api.v1.health import router as health_router

FUTURE_ROUTE_BOUNDARIES = (
    "auth",
    "jobs",
    "resumes",
    "knowledge",
    "interviews",
    "scores",
    "reviews",
    "exports",
)


def build_api_v1_router(prefix: str) -> APIRouter:
    router = APIRouter(prefix=prefix)
    router.include_router(health_router)
    return router
