"""AI task domain ports."""

from typing import Protocol

from app.domain.ai_tasks.entities import AiTask


class AiTaskReader(Protocol):
    def get(self, ai_task_id: str) -> AiTask | None: ...

