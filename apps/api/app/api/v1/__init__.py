"""API v1 router composition."""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.interview_records import router as interview_records_router
from app.api.v1.interviews import router as interviews_router

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
    """Build the API v1 router from stable and active route boundaries."""
    router = APIRouter(prefix=prefix)
    router.include_router(health_router)
    router.include_router(interview_records_router)
    router.include_router(interviews_router)
    return router
