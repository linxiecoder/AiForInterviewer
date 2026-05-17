"""AI task commands."""

from dataclasses import dataclass, field

from app.domain.shared.refs import ResourceRef


@dataclass(frozen=True)
class CreateAiTaskCommand:
    task_type: str
    contract_ids: tuple[str, ...]
    input_refs: tuple[ResourceRef, ...] = field(default_factory=tuple)

