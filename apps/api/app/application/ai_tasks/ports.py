"""AI task ports."""

from typing import Protocol

from app.domain.shared.refs import ResourceRef


class AiTaskRepository(Protocol):
    def get_ref(self, ai_task_id: str) -> ResourceRef | None: ...

