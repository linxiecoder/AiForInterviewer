"""AI task domain entities."""

from dataclasses import dataclass

from app.domain.shared.enums import AiTaskStatus
from app.domain.shared.refs import ResourceRef


@dataclass(frozen=True)
class AiTask:
    ai_task_id: str
    task_type: str
    status: AiTaskStatus
    target_ref: ResourceRef | None = None

