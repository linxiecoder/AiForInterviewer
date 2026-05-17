"""AI task API DTO skeletons."""

from pydantic import BaseModel, Field

from app.domain.shared.enums import AiTaskStatus
from app.schemas.refs import ResourceRef, TraceRefSchema


class AiTaskStatusResponse(BaseModel):
    ai_task_id: str
    task_type: str
    status: AiTaskStatus
    contract_ids: list[str] = Field(default_factory=list)
    retryable: bool = False
    result_ref: TraceRefSchema | None = None
    user_visible_status: str


class AiTaskResultResponse(BaseModel):
    ai_task_id: str
    status: AiTaskStatus
    result_ref: TraceRefSchema | None = None
    candidate_refs: list[ResourceRef] = Field(default_factory=list)
    suggestion_refs: list[ResourceRef] = Field(default_factory=list)
    validation_result_ref: ResourceRef | None = None
    provider_payload: None = None

