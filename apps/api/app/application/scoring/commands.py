"""Scoring commands."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.scoring.entities import ScoreDimension
from app.domain.shared.enums import ScoreType
from app.domain.shared.refs import ResourceRef


@dataclass(frozen=True)
class CreateScoringTaskCommand:
    score_type: ScoreType
    target_ref: ResourceRef


@dataclass(frozen=True)
class CreateScoreResultCommand:
    owner_id: str
    actor_id: str
    score_type: ScoreType | str
    target_type: str
    target_id: str
    rubric_version: str
    dimensions: tuple[ScoreDimension | dict[str, Any], ...]
    target_parent_type: str | None = None
    target_parent_id: str | None = None
    source_module: str | None = None
    source_event: str | None = None
    overall_score: int | None = None
    evidence_links: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    next_action_type: str | None = None
