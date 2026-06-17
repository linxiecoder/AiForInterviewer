"""AI task queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetAiTaskQuery:
    owner_id: str
    ai_task_id: str
