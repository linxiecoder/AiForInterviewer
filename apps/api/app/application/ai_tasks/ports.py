"""AI task ports."""

from typing import Protocol

from app.domain.shared.refs import ResourceRef


class AiTaskRepository(Protocol):
    def get_ref(self, ai_task_id: str) -> ResourceRef | None: ...

    def get_status(self, *, owner_id: str, ai_task_id: str) -> dict[str, object] | None: ...

    def get_result(self, *, owner_id: str, ai_task_id: str) -> dict[str, object] | None: ...
