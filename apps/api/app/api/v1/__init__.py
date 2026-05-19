"""API v1 router composition."""

from fastapi import APIRouter

from app.api.v1.ai_tasks import router as ai_tasks_router
from app.api.v1.auth import router as auth_router
from app.api.v1.assets import router as assets_router
from app.api.v1.bindings import router as bindings_router
from app.api.v1.contract_baseline import router as contract_baseline_router
from app.api.v1.health import router as health_router
from app.api.v1.job_match_analyses import router as job_match_analyses_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.polish import router as polish_router
from app.api.v1.pressure import router as pressure_router
from app.api.v1.reports import router as reports_router
from app.api.v1.resumes import router as resumes_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.scoring import router as scoring_router
from app.api.v1.training import router as training_router
from app.api.v1.weaknesses import router as weaknesses_router


def build_api_v1_router(prefix: str) -> APIRouter:
    """Build the API v1 router from stable and active route boundaries."""
    router = APIRouter(prefix=prefix)
    router.include_router(health_router)
    router.include_router(auth_router)
    router.include_router(contract_baseline_router)
    router.include_router(resumes_router)
    router.include_router(jobs_router)
    router.include_router(bindings_router)
    router.include_router(job_match_analyses_router)
    router.include_router(ai_tasks_router)
    router.include_router(scoring_router)
    router.include_router(polish_router)
    router.include_router(pressure_router)
    router.include_router(reports_router)
    router.include_router(reviews_router)
    router.include_router(assets_router)
    router.include_router(weaknesses_router)
    router.include_router(training_router)
    return router
