"""Stable Step6 progress view assembled from historical effective feedback."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.application.polish.longitudinal_summary import (
    LongitudinalFeedbackSummary,
    build_longitudinal_feedback_summary,
)
from app.application.polish.progress_mastery import ProgressMasteryState, build_progress_mastery_state
from app.application.polish.score_evolution import (
    STEP6_DERIVED_SOURCE_BASIS,
    FeedbackSourceTrace,
    JsonMapping,
    JsonPayload,
    ScoreEvolution,
    build_score_evolution,
)


STABLE_PROGRESS_VIEW_SCHEMA_ID = "polish_step6_stable_progress_view.v1"


@dataclass(frozen=True, slots=True)
class StableProgressView:
    progress_mastery: ProgressMasteryState
    score_evolution: ScoreEvolution
    longitudinal_summary: LongitudinalFeedbackSummary
    source_trace_refs: tuple[FeedbackSourceTrace, ...]
    schema_id: str = STABLE_PROGRESS_VIEW_SCHEMA_ID
    source_basis: str = STEP6_DERIVED_SOURCE_BASIS

    def to_payload(self) -> JsonPayload:
        return {
            "schema_id": self.schema_id,
            "source_basis": self.source_basis,
            "progress_mastery": self.progress_mastery.to_payload(),
            "score_evolution": self.score_evolution.to_payload(),
            "longitudinal_summary": self.longitudinal_summary.to_payload(),
            "source_traceability": [trace.to_payload() for trace in self.source_trace_refs],
        }


def build_stable_progress_view(history: Sequence[JsonMapping]) -> StableProgressView:
    score_evolution = build_score_evolution(history)
    progress_mastery = build_progress_mastery_state(history)
    longitudinal_summary = build_longitudinal_feedback_summary(history)
    return StableProgressView(
        progress_mastery=progress_mastery,
        score_evolution=score_evolution,
        longitudinal_summary=longitudinal_summary,
        source_trace_refs=score_evolution.source_trace_refs,
    )
