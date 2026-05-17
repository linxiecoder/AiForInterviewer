"""Scoring domain entities."""

from dataclasses import dataclass

from app.domain.shared.enums import ScoreType, ValidationStatus
from app.domain.shared.refs import ResourceRef


@dataclass(frozen=True)
class ScoreResult:
    score_result_id: str
    score_type: ScoreType
    target_ref: ResourceRef
    score_value: int
    validation_status: ValidationStatus

