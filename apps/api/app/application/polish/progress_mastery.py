"""Historical progress mastery projection for Step6."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from app.application.polish.score_evolution import (
    STEP6_DERIVED_SOURCE_BASIS,
    DimensionScorePoint,
    FeedbackSourceTrace,
    JsonMapping,
    JsonPayload,
    build_score_evolution,
)


@dataclass(frozen=True, slots=True)
class ProgressMasteryState:
    mastery_level: str
    latest_score: float | None
    score_delta: float | None
    dimension_stability: Mapping[str, str]
    positive_signal_count: int
    non_positive_signal_count: int
    included_feedback_count: int
    excluded_feedback_count: int
    source_trace_refs: tuple[FeedbackSourceTrace, ...]
    source_basis: str = STEP6_DERIVED_SOURCE_BASIS

    def to_payload(self) -> JsonPayload:
        return {
            "source_basis": self.source_basis,
            "mastery_level": self.mastery_level,
            "latest_score": self.latest_score,
            "score_delta": self.score_delta,
            "dimension_stability": dict(self.dimension_stability),
            "positive_signal_count": self.positive_signal_count,
            "non_positive_signal_count": self.non_positive_signal_count,
            "included_feedback_count": self.included_feedback_count,
            "excluded_feedback_count": self.excluded_feedback_count,
            "source_traceability": [trace.to_payload() for trace in self.source_trace_refs],
        }


def build_progress_mastery_state(history: Sequence[JsonMapping]) -> ProgressMasteryState:
    evolution = build_score_evolution(history)
    score_points = evolution.score_over_time
    latest_score = score_points[-1].score if score_points else None
    score_delta = (
        round(score_points[-1].score - score_points[0].score, 2) if len(score_points) >= 2 else None
    )
    return ProgressMasteryState(
        mastery_level=_mastery_level(latest_score),
        latest_score=latest_score,
        score_delta=score_delta,
        dimension_stability=_dimension_stability(evolution.dimension_score_evolution),
        positive_signal_count=sum(1 for point in score_points if point.score >= 70),
        non_positive_signal_count=sum(1 for point in score_points if point.score < 70),
        included_feedback_count=evolution.included_feedback_count,
        excluded_feedback_count=evolution.excluded_feedback_count,
        source_trace_refs=evolution.source_trace_refs,
    )


def _mastery_level(score: float | None) -> str:
    if score is None:
        return "no_effective_feedback"
    if score >= 85:
        return "mastered"
    if score >= 70:
        return "stable"
    if score >= 60:
        return "developing"
    return "needs_focus"


def _dimension_stability(points_by_dimension: Mapping[str, Sequence[DimensionScorePoint]]) -> dict[str, str]:
    stability: dict[str, str] = {}
    for dimension, points in points_by_dimension.items():
        if not points:
            continue
        latest_score = float(points[-1].score)
        level = _mastery_level(latest_score)
        if len(points) < 2:
            stability[dimension] = f"{level}:insufficient_history"
            continue
        delta = round(float(points[-1].score) - float(points[0].score), 2)
        trend = "stable"
        if delta > 0:
            trend = "improving"
        if delta < 0:
            trend = "regressing"
        stability[dimension] = f"{level}:{trend}"
    return stability
