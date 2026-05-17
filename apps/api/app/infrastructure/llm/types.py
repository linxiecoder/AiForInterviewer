"""LLM transport DTOs for infrastructure boundary."""

from dataclasses import dataclass, field
from typing import Any

from app.domain.shared.enums import ConfidenceLevel, ValidationStatus


@dataclass(frozen=True)
class LlmTransportRequest:
    contract_ids: tuple[str, ...]
    task_type: str
    input_refs: tuple[str, ...] = field(default_factory=tuple)
    evidence_bundle: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LlmTransportResult:
    result: dict[str, Any]
    validation_status: ValidationStatus
    confidence_level: ConfidenceLevel
    low_confidence_flags: tuple[str, ...]
    trace_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]

