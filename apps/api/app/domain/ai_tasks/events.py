"""AI task domain events."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AiTaskQueued:
    ai_task_id: str

