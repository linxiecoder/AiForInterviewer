"""AI task queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetAiTaskQuery:
    ai_task_id: str

