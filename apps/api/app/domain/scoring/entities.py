"""Scoring domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.shared.enums import ScoreType, ValidationStatus
from app.domain.shared.refs import ResourceRef


@dataclass(frozen=True)
class ScoreDimension:
    name: str
    score: int
    confidence: float
    evidence_links: tuple[dict[str, Any], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ScoreResult:
    score_result_id: str
    owner_id: str
    score_type: ScoreType
    target_ref: ResourceRef
    target_parent_ref: ResourceRef | None
    score_value: int
    overall_score: int
    rubric_version: str
    validation_status: ValidationStatus
    dimensions: tuple[ScoreDimension, ...]
    primary_bottleneck: str
    next_action_type: str
