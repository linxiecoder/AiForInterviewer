"""API v1 router composition."""

from fastapi import APIRouter

from app.api.v1.health import router as health_router


def build_api_v1_router(prefix: str) -> APIRouter:
    """Build the API v1 router from stable and active route boundaries."""
    router = APIRouter(prefix=prefix)
    router.include_router(health_router)
    return router
