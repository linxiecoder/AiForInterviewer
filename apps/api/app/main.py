from fastapi import APIRouter, FastAPI

app = FastAPI(title="ai-for-interviewer")
api_v1 = APIRouter(prefix="/api/v1")


@api_v1.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_v1)
