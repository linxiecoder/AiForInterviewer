"""Derived-only score evolution views for Step6 progress mastery."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final


JsonMapping = Mapping[str, object]
JsonPayload = dict[str, object]


STEP6_DERIVED_SOURCE_BASIS: Final = "step2_effective_generated_feedback + step5_effective_feedback_history"
STEP6_SOURCE_FIELDS: Final = (
    "feedback_id",
    "answer_id",
    "answer_round",
    "generated_feedback_payload.status",
    "generated_feedback_payload.score_result",
)
STEP6_STEP5_HISTORY_SOURCE_FIELDS: Final = (
    "answer_id",
    "answer_round",
    "step5_effective_feedback_history.score_result",
    "step5_effective_feedback_history.loss_point_ids",
)


@dataclass(frozen=True, slots=True)
class FeedbackSourceTrace:
    feedback_id: str | None
    answer_id: str
    answer_round: int | None
    status: str
    payload_status: str
    source_kind: str
    source_basis: str = STEP6_DERIVED_SOURCE_BASIS
    source_fields: tuple[str, ...] = STEP6_SOURCE_FIELDS

    def to_payload(self) -> JsonPayload:
        return {
            "feedback_id": self.feedback_id,
            "answer_id": self.answer_id,
            "answer_round": self.answer_round,
            "status": self.status,
            "payload_status": self.payload_status,
            "source_kind": self.source_kind,
            "source_basis": self.source_basis,
            "source_fields": list(self.source_fields),
        }


@dataclass(frozen=True, slots=True)
class EffectiveFeedbackRecord:
    payload: JsonMapping
    source_trace: FeedbackSourceTrace
    sort_index: int


@dataclass(frozen=True, slots=True)
class ScoreSnapshot:
    feedback_id: str | None
    answer_id: str
    answer_round: int | None
    score: float
    source_basis: str = STEP6_DERIVED_SOURCE_BASIS

    def to_payload(self) -> JsonPayload:
        return {
            "feedback_id": self.feedback_id,
            "answer_id": self.answer_id,
            "answer_round": self.answer_round,
            "score": self.score,
            "source_basis": self.source_basis,
        }


@dataclass(frozen=True, slots=True)
class DimensionScorePoint:
    feedback_id: str | None
    answer_id: str
    answer_round: int | None
    dimension: str
    score: float
    source_basis: str = STEP6_DERIVED_SOURCE_BASIS

    def to_payload(self) -> JsonPayload:
        return {
            "feedback_id": self.feedback_id,
            "answer_id": self.answer_id,
            "answer_round": self.answer_round,
            "dimension": self.dimension,
            "score": self.score,
            "source_basis": self.source_basis,
        }


@dataclass(frozen=True, slots=True)
class ScoreEvolution:
    score_over_time: tuple[ScoreSnapshot, ...]
    dimension_score_evolution: Mapping[str, tuple[DimensionScorePoint, ...]]
    source_trace_refs: tuple[FeedbackSourceTrace, ...]
    included_feedback_count: int
    excluded_feedback_count: int
    source_basis: str = STEP6_DERIVED_SOURCE_BASIS

    def to_payload(self) -> JsonPayload:
        return {
            "source_basis": self.source_basis,
            "included_feedback_count": self.included_feedback_count,
            "excluded_feedback_count": self.excluded_feedback_count,
            "score_over_time": [point.to_payload() for point in self.score_over_time],
            "dimension_score_evolution": {
                dimension: [point.to_payload() for point in points]
                for dimension, points in self.dimension_score_evolution.items()
            },
            "source_traceability": [trace.to_payload() for trace in self.source_trace_refs],
        }


def build_score_evolution(history: Sequence[JsonMapping]) -> ScoreEvolution:
    records = effective_feedback_records(history)
    score_points: list[ScoreSnapshot] = []
    dimension_points: dict[str, list[DimensionScorePoint]] = {}

    for record in records:
        score_result = _mapping(record.payload.get("score_result"))
        if score_result is None:
            continue
        score_value = _number(score_result.get("score_value"))
        if score_value is None:
            continue
        trace = record.source_trace
        score_points.append(
            ScoreSnapshot(
                feedback_id=trace.feedback_id,
                answer_id=trace.answer_id,
                answer_round=trace.answer_round,
                score=round(score_value, 2),
            )
        )
        for dimension, dimension_score in _dimension_scores(score_result).items():
            dimension_points.setdefault(dimension, []).append(
                DimensionScorePoint(
                    feedback_id=trace.feedback_id,
                    answer_id=trace.answer_id,
                    answer_round=trace.answer_round,
                    dimension=dimension,
                    score=dimension_score,
                )
            )

    return ScoreEvolution(
        score_over_time=tuple(score_points),
        dimension_score_evolution={dimension: tuple(points) for dimension, points in dimension_points.items()},
        source_trace_refs=tuple(point.source_trace for point in records if _has_score(point.payload)),
        included_feedback_count=len(score_points),
        excluded_feedback_count=max(len(history) - len(score_points), 0),
    )


def effective_feedback_records(history: Sequence[JsonMapping]) -> tuple[EffectiveFeedbackRecord, ...]:
    records: list[EffectiveFeedbackRecord] = []
    for index, item in enumerate(history):
        extracted = _payload_from_history_item(item)
        if extracted is None:
            continue
        payload, source_kind, source_fields = extracted
        status = _source_status(item, payload, source_kind)
        payload_status = _payload_status(payload, source_kind)
        if status != "generated" or payload_status != "generated":
            continue
        answer_id = _clean(item.get("answer_id") or payload.get("answer_id"))
        feedback_id = _optional_clean(item.get("feedback_id") or payload.get("feedback_id"))
        answer_round = _int_value(item.get("answer_round"))
        records.append(
            EffectiveFeedbackRecord(
                payload=payload,
                source_trace=FeedbackSourceTrace(
                    feedback_id=feedback_id,
                    answer_id=answer_id,
                    answer_round=answer_round,
                    status=status,
                    payload_status=payload_status,
                    source_kind=source_kind,
                    source_fields=source_fields,
                ),
                sort_index=index,
            )
        )
    return tuple(sorted(records, key=_record_sort_key))


def _payload_from_history_item(item: JsonMapping) -> tuple[JsonMapping, str, tuple[str, ...]] | None:
    nested = _mapping(item.get("generated_feedback_payload"))
    if nested is not None:
        return nested, "generated_feedback_payload", STEP6_SOURCE_FIELDS
    if _mapping(item.get("score_result")) is not None:
        return item, "step5_effective_feedback_history", STEP6_STEP5_HISTORY_SOURCE_FIELDS
    return None


def _source_status(item: JsonMapping, payload: JsonMapping, source_kind: str) -> str:
    status = _clean(item.get("status") or item.get("feedback_status") or payload.get("status"))
    if status:
        return status
    if source_kind == "step5_effective_feedback_history":
        return "generated"
    return ""


def _payload_status(payload: JsonMapping, source_kind: str) -> str:
    status = _clean(payload.get("status"))
    if status:
        return status
    if source_kind == "step5_effective_feedback_history":
        return "generated"
    return ""


def _record_sort_key(record: EffectiveFeedbackRecord) -> tuple[int, str, str]:
    answer_round = record.source_trace.answer_round
    round_key = answer_round if answer_round is not None else record.sort_index
    return (round_key, record.source_trace.answer_id, record.source_trace.feedback_id or "")


def _has_score(payload: JsonMapping) -> bool:
    score_result = _mapping(payload.get("score_result"))
    return score_result is not None and _number(score_result.get("score_value")) is not None


def _dimension_scores(score_result: JsonMapping) -> dict[str, float]:
    scores: dict[str, float] = {}
    dimension_scores = score_result.get("dimension_scores")
    if not isinstance(dimension_scores, Sequence) or isinstance(dimension_scores, (str, bytes)):
        return scores
    for item in dimension_scores:
        score_item = _mapping(item)
        if score_item is None:
            continue
        dimension = _clean(score_item.get("dimension"))
        score = _number(score_item.get("score"))
        if dimension and score is not None:
            scores[dimension] = round(score, 2)
    return scores


def _mapping(value: object) -> JsonMapping | None:
    return value if isinstance(value, Mapping) else None


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _int_value(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _clean(value: object) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())[:240]


def _optional_clean(value: object) -> str | None:
    cleaned = _clean(value)
    return cleaned or None
