"""Deterministic scoring policy for canonical interview-answer rubric."""

from __future__ import annotations

from math import floor
from typing import Iterable

from app.domain.scoring.entities import ScoreDimension

CANONICAL_RUBRIC_VERSION = "aiforinterviewer.scoring.v1"
CANONICAL_DIMENSIONS = (
    "substance",
    "structure",
    "relevance",
    "credibility",
    "differentiation",
)
PRIMARY_BOTTLENECK_PRIORITY = (
    "relevance",
    "substance",
    "structure",
    "credibility",
    "differentiation",
)
ALLOWED_NEXT_ACTION_PREFIXES = (
    "polish_reentry_",
    "pressure_reentry_",
    "mock_reentry_",
)
FORBIDDEN_NEXT_ACTION_TYPES = {
    "training",
    "training_plan",
    "training_drill",
    "complete_training",
}


class ScoringPolicyError(ValueError):
    pass


class ScoringPolicy:
    @classmethod
    def validate_dimensions(
        cls,
        *,
        rubric_version: str | None,
        dimensions: Iterable[ScoreDimension | dict],
    ) -> tuple[ScoreDimension, ...]:
        normalized_rubric = _clean(rubric_version)
        if not normalized_rubric:
            raise ScoringPolicyError("rubric_version is required")
        normalized_dimensions = tuple(_dimension_from(value) for value in dimensions)
        if normalized_rubric == CANONICAL_RUBRIC_VERSION:
            return _validate_canonical_dimensions(normalized_dimensions)
        if not normalized_dimensions:
            raise ScoringPolicyError("scoring dimensions are required")
        return normalized_dimensions

    @classmethod
    def compute_overall_score(cls, dimensions: Iterable[ScoreDimension]) -> int:
        values = tuple(dimensions)
        if not values:
            raise ScoringPolicyError("scoring dimensions are required")
        for dimension in values:
            _validate_score(dimension.score, field_name=f"{dimension.name}.score")
        average = sum(dimension.score for dimension in values) / len(values)
        return _clamp_int(floor(average + 0.5), minimum=0, maximum=100)

    @classmethod
    def select_primary_bottleneck(cls, dimensions: Iterable[ScoreDimension]) -> str:
        values_by_name = {dimension.name: dimension for dimension in dimensions}
        if not values_by_name:
            raise ScoringPolicyError("scoring dimensions are required")
        min_score = min(dimension.score for dimension in values_by_name.values())
        candidates = {
            dimension.name
            for dimension in values_by_name.values()
            if dimension.score == min_score
        }
        for dimension_name in PRIMARY_BOTTLENECK_PRIORITY:
            if dimension_name in candidates:
                return dimension_name
        return sorted(candidates)[0]

    @classmethod
    def derive_next_action_type(
        cls,
        *,
        target_type: str,
        target_parent_type: str | None = None,
        source_module: str | None = None,
        primary_bottleneck: str,
        requested_next_action_type: str | None = None,
    ) -> str:
        requested = _clean(requested_next_action_type)
        if requested:
            _validate_next_action_type(requested)
            return requested

        scope_text = " ".join(
            value
            for value in (
                _clean(target_type),
                _clean(target_parent_type),
                _clean(source_module),
            )
            if value
        )
        if "pressure" in scope_text:
            prefix = "pressure_reentry_"
        elif "mock" in scope_text or "review" in scope_text:
            prefix = "mock_reentry_"
        else:
            prefix = "polish_reentry_"
        action = f"{prefix}{_clean(primary_bottleneck)}"
        _validate_next_action_type(action)
        return action


def _validate_canonical_dimensions(dimensions: tuple[ScoreDimension, ...]) -> tuple[ScoreDimension, ...]:
    by_name: dict[str, ScoreDimension] = {}
    for dimension in dimensions:
        if dimension.name in by_name:
            raise ScoringPolicyError("canonical scoring dimensions must not be duplicated")
        by_name[dimension.name] = dimension

    if set(by_name) != set(CANONICAL_DIMENSIONS):
        raise ScoringPolicyError(
            "canonical scoring dimensions must be exactly: "
            + ", ".join(CANONICAL_DIMENSIONS)
        )
    return tuple(by_name[name] for name in CANONICAL_DIMENSIONS)


def _dimension_from(value: ScoreDimension | dict) -> ScoreDimension:
    if isinstance(value, ScoreDimension):
        dimension = value
    elif isinstance(value, dict):
        evidence_links = value.get("evidence_links") or ()
        dimension = ScoreDimension(
            name=_clean(value.get("name") or value.get("dimension_key")),
            score=_coerce_int(value.get("score", value.get("dimension_score"))),
            confidence=_coerce_float(value.get("confidence")),
            evidence_links=tuple(
                item for item in evidence_links if isinstance(item, dict)
            ),
        )
    else:
        raise ScoringPolicyError("scoring dimensions must be objects")

    if not dimension.name:
        raise ScoringPolicyError("scoring dimension name is required")
    _validate_score(dimension.score, field_name=f"{dimension.name}.score")
    _validate_confidence(dimension.confidence, field_name=f"{dimension.name}.confidence")
    return dimension


def _validate_next_action_type(value: str) -> None:
    if value in FORBIDDEN_NEXT_ACTION_TYPES or "training" in value:
        raise ScoringPolicyError("next_action_type must not route to Training")
    if not value.startswith(ALLOWED_NEXT_ACTION_PREFIXES):
        raise ScoringPolicyError(
            "next_action_type must start with polish_reentry_, pressure_reentry_, or mock_reentry_"
        )


def _validate_score(value: int, *, field_name: str) -> None:
    if value < 0 or value > 100:
        raise ScoringPolicyError(f"{field_name} must be between 0 and 100")


def _validate_confidence(value: float, *, field_name: str) -> None:
    if value < 0 or value > 1:
        raise ScoringPolicyError(f"{field_name} must be between 0 and 1")


def _coerce_int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ScoringPolicyError("dimension score must be an integer") from exc


def _coerce_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ScoringPolicyError("dimension confidence must be a number") from exc


def _clamp_int(value: int, *, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def _clean(value: object) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())
