"""Historical feedback summary for Step6 derived-only progress views."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from app.application.polish.score_evolution import (
    STEP6_DERIVED_SOURCE_BASIS,
    FeedbackSourceTrace,
    JsonMapping,
    JsonPayload,
    effective_feedback_records,
)


@dataclass(frozen=True, slots=True)
class LongitudinalFeedbackSummary:
    improvements: tuple[str, ...]
    remaining_gaps: tuple[str, ...]
    regressions: tuple[str, ...]
    source_trace_refs: tuple[FeedbackSourceTrace, ...]
    source_basis: str = STEP6_DERIVED_SOURCE_BASIS

    def to_payload(self) -> JsonPayload:
        return {
            "source_basis": self.source_basis,
            "improvements": list(self.improvements),
            "remaining_gaps": list(self.remaining_gaps),
            "regressions": list(self.regressions),
            "source_traceability": [trace.to_payload() for trace in self.source_trace_refs],
        }


def build_longitudinal_feedback_summary(history: Sequence[JsonMapping]) -> LongitudinalFeedbackSummary:
    improvements: list[str] = []
    remaining_gaps: list[str] = []
    regressions: list[str] = []
    records = effective_feedback_records(history)
    for record in records:
        change = _mapping(record.payload.get("answer_change_analysis")) or {}
        improvements.extend(_improvement_signals(change))
        remaining_gaps.extend(_remaining_gap_signals(change))
        regressions.extend(_regression_signals(change))
    return LongitudinalFeedbackSummary(
        improvements=tuple(dict.fromkeys(improvements)),
        remaining_gaps=tuple(dict.fromkeys(remaining_gaps)),
        regressions=tuple(dict.fromkeys(regressions)),
        source_trace_refs=tuple(record.source_trace for record in records),
    )


def _improvement_signals(change: JsonMapping) -> tuple[str, ...]:
    summary = _mapping(change.get("derived_improvement_summary")) or {}
    signals: list[str] = []
    score_delta = _number(summary.get("score_delta"))
    if score_delta is not None and score_delta > 0:
        signals.append(f"score_delta:+{score_delta:.1f}")
    signals.extend(_dimension_delta_signals(summary.get("positive_dimension_deltas"), positive=True))
    signals.extend(f"fixed_loss_point:{loss_id}" for loss_id in _string_values(summary.get("fixed_loss_point_ids")))
    return tuple(signals)


def _remaining_gap_signals(change: JsonMapping) -> tuple[str, ...]:
    summary = _mapping(change.get("derived_remaining_gap_summary")) or {}
    signals = [f"remaining_loss_point:{loss_id}" for loss_id in _string_values(summary.get("remaining_loss_point_ids"))]
    signals.extend(_dimension_delta_signals(summary.get("non_positive_dimension_deltas"), positive=False))
    return tuple(signals)


def _regression_signals(change: JsonMapping) -> tuple[str, ...]:
    summary = _mapping(change.get("derived_regression_summary")) or {}
    signals: list[str] = []
    score_delta = _number(summary.get("score_delta"))
    if score_delta is not None and score_delta < 0:
        signals.append(f"score_delta:{score_delta:.1f}")
    signals.extend(_dimension_delta_signals(summary.get("negative_dimension_deltas"), positive=False))
    signals.extend(f"regressed_point:{point}" for point in _string_values(summary.get("regressed_points")))
    return tuple(signals)


def _dimension_delta_signals(value: object, *, positive: bool) -> tuple[str, ...]:
    deltas = _mapping(value) or {}
    signals: list[str] = []
    for dimension, raw_delta in sorted(deltas.items()):
        delta = _number(raw_delta)
        if delta is None:
            continue
        if positive and delta > 0:
            signals.append(f"dimension:{dimension}:+{delta:.1f}")
        if not positive and delta <= 0:
            signals.append(f"dimension:{dimension}:{delta:.1f}")
    return tuple(signals)


def _mapping(value: object) -> JsonMapping | None:
    return value if isinstance(value, Mapping) else None


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _string_values(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(str(item) for item in value if str(item).strip())
