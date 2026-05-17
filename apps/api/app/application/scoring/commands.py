"""Scoring commands."""

from dataclasses import dataclass

from app.domain.shared.enums import ScoreType
from app.domain.shared.refs import ResourceRef


@dataclass(frozen=True)
class CreateScoringTaskCommand:
    score_type: ScoreType
    target_ref: ResourceRef

