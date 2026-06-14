"""Progress-adaptive aggregation kernel for Polish answer evaluation."""

from __future__ import annotations

from dataclasses import dataclass


ADAPTIVE_SCORE_BASIS = "progress_adaptive_llm_comparator_v1"
ADAPTIVE_SCORE_AGGREGATION_METHOD = "progress_weighted_dimension_scores"
ADAPTIVE_RUBRIC_VERSION = "polish_answer.progress_adaptive_rubric.v1"
ADAPTIVE_ANCHOR_SET_ID = "polish_answer.progress_adaptive_anchors.v1"
ADAPTIVE_COMPARATOR_VERSION = "polish_answer.progress_aware_llm_comparator.v1"
ADAPTIVE_RUBRIC_DIMENSIONS = (
    "correctness",
    "depth",
    "tradeoff_reasoning",
    "structure",
    "engineering_awareness",
)
ADAPTIVE_SIGNAL_TYPES = ("weakness_detected", "strength_detected", "drift_detected", "progress_update")

# Backwards-compatible names for callers that import the semantic constants directly.
SEMANTIC_SCORE_BASIS = ADAPTIVE_SCORE_BASIS
SEMANTIC_SCORE_AGGREGATION_METHOD = ADAPTIVE_SCORE_AGGREGATION_METHOD
SEMANTIC_RUBRIC_VERSION = ADAPTIVE_RUBRIC_VERSION
SEMANTIC_ANCHOR_SET_ID = ADAPTIVE_ANCHOR_SET_ID
SEMANTIC_COMPARATOR_VERSION = ADAPTIVE_COMPARATOR_VERSION
SEMANTIC_RUBRIC_DIMENSIONS = ADAPTIVE_RUBRIC_DIMENSIONS
SEMANTIC_SIGNAL_TYPES = ADAPTIVE_SIGNAL_TYPES

_DIMENSION_ALIASES = {
    "tradeoff": "tradeoff_reasoning",
    "tradeoffs": "tradeoff_reasoning",
    "trade_off_reasoning": "tradeoff_reasoning",
    "tradeoff_reasoning": "tradeoff_reasoning",
    "tradeoff reasoning": "tradeoff_reasoning",
    "engineering awareness": "engineering_awareness",
}


@dataclass(frozen=True)
class AdaptiveRubricDimension:
    """One progress-derived rubric dimension produced by the adaptive rubric agent."""

    dimension: str
    adaptive_weight: float
    progress_basis: tuple[str, ...] = ()
    anchor_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class SemanticScoreDimension:
    """One LLM comparator score for a progress-adaptive rubric dimension."""

    dimension: str
    score: float
    adaptive_weight: float
    progress_focus: tuple[str, ...] = ()
    rationale: str = ""


@dataclass(frozen=True)
class ScoringInput:
    """Input for progress-adaptive semantic score aggregation."""

    progress_state_ref: str = ""
    adaptive_rubric_dimensions: tuple[AdaptiveRubricDimension, ...] = ()
    dimension_scores: tuple[SemanticScoreDimension, ...] = ()
    signals: tuple[str, ...] = ()
    progress_updates: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True)
class ScoringDecision:
    """Aggregation output used by feedback validation and final payload building."""

    score_type: str
    score_value: float | None
    scoring_basis: str
    aggregation_method: str
    progress_state_ref: str
    adaptive_rubric_dimensions: tuple[AdaptiveRubricDimension, ...]
    dimension_scores: tuple[SemanticScoreDimension, ...]
    signals: tuple[str, ...]
    progress_updates: tuple[dict[str, object], ...]
    warnings: tuple[str, ...] = ()
    validation_errors: tuple[str, ...] = ()


class ScoringPolicy:
    @classmethod
    def evaluate(cls, value: ScoringInput) -> ScoringDecision:
        progress_state_ref = _clean(value.progress_state_ref, max_chars=120)
        normalized_rubric: list[AdaptiveRubricDimension] = []
        normalized_dimensions: list[SemanticScoreDimension] = []
        warnings: list[str] = []
        errors: list[str] = []

        if not progress_state_ref:
            errors.append("progress_state_ref_required")
        if not value.adaptive_rubric_dimensions:
            errors.append("adaptive_rubric_required")
        if not value.progress_updates:
            errors.append("progress_updates_required")

        rubric_by_dimension: dict[str, AdaptiveRubricDimension] = {}
        for item in value.adaptive_rubric_dimensions:
            dimension = _normalize_dimension(item.dimension)
            if dimension not in ADAPTIVE_RUBRIC_DIMENSIONS:
                warnings.append(f"adaptive_rubric_dimension_ignored:{dimension or 'unknown'}")
                continue
            if not _is_valid_weight(item.adaptive_weight):
                errors.append("adaptive_rubric_weight_invalid")
                continue
            progress_basis = _normalize_tuple(item.progress_basis, max_item_chars=160)
            if not progress_basis:
                errors.append("adaptive_rubric_progress_basis_required")
                continue
            if dimension not in rubric_by_dimension:
                rubric_by_dimension[dimension] = AdaptiveRubricDimension(
                    dimension=dimension,
                    adaptive_weight=round(float(item.adaptive_weight), 6),
                    progress_basis=progress_basis,
                    anchor_refs=_normalize_tuple(item.anchor_refs, max_item_chars=120),
                )

        by_dimension: dict[str, SemanticScoreDimension] = {}
        for item in value.dimension_scores:
            dimension = _normalize_dimension(item.dimension)
            if dimension not in ADAPTIVE_RUBRIC_DIMENSIONS:
                warnings.append(f"score_result_dimension_ignored:{dimension or 'unknown'}")
                continue
            if not 0 <= item.score <= 100:
                errors.append("score_value_out_of_range")
                continue
            rubric_dimension = rubric_by_dimension.get(dimension)
            if rubric_dimension is None:
                continue
            if round(float(item.adaptive_weight), 6) != rubric_dimension.adaptive_weight:
                errors.append("score_result_adaptive_weight_mismatch")
                continue
            progress_focus = _normalize_tuple(item.progress_focus, max_item_chars=160)
            if not progress_focus:
                errors.append("score_result_progress_focus_required")
                continue
            if dimension not in by_dimension:
                by_dimension[dimension] = SemanticScoreDimension(
                    dimension=dimension,
                    score=round(float(item.score), 2),
                    adaptive_weight=rubric_dimension.adaptive_weight,
                    progress_focus=progress_focus,
                    rationale=_clean(item.rationale, max_chars=2000),
                )

        missing_rubric_dimensions = tuple(
            dimension for dimension in ADAPTIVE_RUBRIC_DIMENSIONS if dimension not in rubric_by_dimension
        )
        if missing_rubric_dimensions:
            errors.append("adaptive_rubric_dimensions_incomplete")

        missing_dimensions = tuple(dimension for dimension in ADAPTIVE_RUBRIC_DIMENSIONS if dimension not in by_dimension)
        if missing_dimensions:
            errors.append("score_result_dimension_scores_incomplete")

        for dimension in ADAPTIVE_RUBRIC_DIMENSIONS:
            if dimension in rubric_by_dimension:
                normalized_rubric.append(rubric_by_dimension[dimension])
            if dimension in by_dimension:
                normalized_dimensions.append(by_dimension[dimension])

        signals = _normalize_signals(value.signals)
        if not signals:
            errors.append("score_result_signals_required")
        progress_updates = _normalize_progress_updates(value.progress_updates)
        if value.progress_updates and not progress_updates:
            errors.append("progress_updates_invalid")

        score_value: float | None = None
        if not errors and normalized_dimensions:
            total_weight = sum(item.adaptive_weight for item in normalized_dimensions)
            score_value = round(sum(item.score * item.adaptive_weight for item in normalized_dimensions) / total_weight, 2)

        return ScoringDecision(
            score_type="polish_answer",
            score_value=score_value,
            scoring_basis=ADAPTIVE_SCORE_BASIS,
            aggregation_method=ADAPTIVE_SCORE_AGGREGATION_METHOD,
            progress_state_ref=progress_state_ref,
            adaptive_rubric_dimensions=tuple(normalized_rubric),
            dimension_scores=tuple(normalized_dimensions),
            signals=signals,
            progress_updates=progress_updates,
            warnings=tuple(dict.fromkeys(warnings)),
            validation_errors=tuple(dict.fromkeys(errors)),
        )


def _normalize_dimension(value: object) -> str:
    raw = _clean(value, max_chars=80).lower().replace("-", "_").replace(" ", "_")
    return _DIMENSION_ALIASES.get(raw, raw)


def _normalize_signals(value: tuple[str, ...]) -> tuple[str, ...]:
    signals: list[str] = []
    for item in value:
        signal = _clean(item, max_chars=80)
        if signal in ADAPTIVE_SIGNAL_TYPES and signal not in signals:
            signals.append(signal)
    return tuple(signals)


def _normalize_progress_updates(value: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    updates: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        progress_node_ref = _clean(item.get("progress_node_ref") or item.get("node_ref"), max_chars=120)
        signal = _clean(item.get("signal"), max_chars=80)
        dimension = _normalize_dimension(item.get("dimension"))
        if not progress_node_ref or not signal:
            continue
        normalized: dict[str, object] = {
            "progress_node_ref": progress_node_ref,
            "signal": signal,
        }
        if dimension:
            normalized["dimension"] = dimension
        rationale = _clean(item.get("rationale"), max_chars=1000)
        if rationale:
            normalized["rationale"] = rationale
        learning_rate = item.get("learning_rate")
        if isinstance(learning_rate, (int, float)) and not isinstance(learning_rate, bool) and learning_rate > 0:
            normalized["learning_rate"] = round(float(learning_rate), 6)
        learning_rate_basis = _clean(item.get("learning_rate_basis"), max_chars=120)
        if learning_rate_basis:
            normalized["learning_rate_basis"] = learning_rate_basis
        updates.append(normalized)
    return tuple(updates)


def _normalize_tuple(value: tuple[str, ...], *, max_item_chars: int) -> tuple[str, ...]:
    normalized: list[str] = []
    for item in value:
        text = _clean(item, max_chars=max_item_chars)
        if text and text not in normalized:
            normalized.append(text)
    return tuple(normalized)


def _is_valid_weight(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _clean(value: object, *, max_chars: int = 80) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text
