"""Progress-aware adaptive evaluation contract for Polish feedback."""

from __future__ import annotations

from typing import Any

from app.domain.polish.policies.scoring_policy import (
    ADAPTIVE_ANCHOR_SET_ID,
    ADAPTIVE_COMPARATOR_VERSION,
    ADAPTIVE_RUBRIC_DIMENSIONS,
    ADAPTIVE_RUBRIC_VERSION,
    ADAPTIVE_SCORE_AGGREGATION_METHOD,
    ADAPTIVE_SCORE_BASIS,
    ADAPTIVE_SIGNAL_TYPES,
    AdaptiveRubricDimension,
    SEMANTIC_ANCHOR_SET_ID,
    SEMANTIC_COMPARATOR_VERSION,
    SEMANTIC_RUBRIC_DIMENSIONS,
    SEMANTIC_RUBRIC_VERSION,
    SEMANTIC_SCORE_AGGREGATION_METHOD,
    SEMANTIC_SCORE_BASIS,
    SEMANTIC_SIGNAL_TYPES,
    ScoringInput,
    ScoringPolicy,
    SemanticScoreDimension,
)


SEMANTIC_EVALUATION_PIPELINE = (
    "input",
    "progress_state",
    "adaptive_rubric",
    "anchor_examples",
    "llm_comparator",
    "signals",
    "progress_update",
    "kernel_aggregation",
)
SEMANTIC_EVALUATION_AGENTS = {
    "discovery": "extract weak and strong skill signals from ProgressState",
    "adaptive_rubric": "derive rubric weights only from ProgressState",
    "llm_judge": "compare answer against adaptive rubric and anchors",
    "validation": "reject static, rule-based, keyword, fallback, or non-progress adaptation",
}
SEMANTIC_ANCHOR_EXAMPLES = {
    "good_answer": [
        "tradeoffs",
        "failure handling",
        "structured reasoning",
    ],
    "bad_answer": [
        "naive solution",
        "no reasoning",
    ],
    "borderline": [
        "partial reasoning",
    ],
}
FORBIDDEN_EVALUATION_INFLUENCES = (
    "rule_based_scoring",
    "keyword_scoring",
    "quick_full_path_influence",
    "fallback_scoring",
)
ADAPTIVE_INSIGHT_REQUIRED_KEYS = ("weak_skills", "strong_skills", "unstable_skills")
ADAPTIVE_INSIGHT_OPTIONAL_KEYS = ("overweighted_skills", "underweighted_skills")


def semantic_evaluation_contract() -> dict[str, Any]:
    return {
        "evaluation_pipeline": list(SEMANTIC_EVALUATION_PIPELINE),
        "evaluation_agents": dict(SEMANTIC_EVALUATION_AGENTS),
        "progress_state_requirement": {
            "required": True,
            "source": "input_data.progress_state",
            "adaptation_policy": "progress_state_only",
        },
        "adaptive_rubric": {
            "rubric_version": ADAPTIVE_RUBRIC_VERSION,
            "semantic_only": True,
            "weight_policy": "llm_judge_must_return_progress_derived_adaptive_weight",
            "dimensions": [{"dimension": dimension, "adaptive_weight_required": True} for dimension in ADAPTIVE_RUBRIC_DIMENSIONS],
        },
        "anchor_examples": {key: list(value) for key, value in SEMANTIC_ANCHOR_EXAMPLES.items()},
        "llm_comparator": {
            "comparator_version": ADAPTIVE_COMPARATOR_VERSION,
            "anchor_set_id": ADAPTIVE_ANCHOR_SET_ID,
            "required_output": "score_result.reasoning + score_result.adaptive_rubric + score_result.dimension_scores + score_result.adaptive_insights + score_result.progress_updates",
            "aggregation_owner": "kernel_aggregation",
            "forbidden_influences": list(FORBIDDEN_EVALUATION_INFLUENCES),
        },
        "semantic_signals": list(ADAPTIVE_SIGNAL_TYPES),
    }


def normalize_semantic_score_result(
    score_result: object,
    *,
    expected_progress_state_ref: str | None = None,
) -> tuple[dict[str, Any] | None, tuple[str, ...], tuple[str, ...]]:
    if not isinstance(score_result, dict):
        return None, ("score_result_required",), ()

    errors: list[str] = []
    progress_state_ref = _clean(score_result.get("progress_state_ref"), max_chars=120)
    expected_ref = _clean(expected_progress_state_ref, max_chars=120)
    if expected_ref and progress_state_ref and progress_state_ref != expected_ref:
        errors.append("progress_state_ref_mismatch")
    raw_adaptive_rubric = score_result.get("adaptive_rubric")
    adaptive_rubric_progress_state_ref = (
        _clean(raw_adaptive_rubric.get("progress_state_ref"), max_chars=120) if isinstance(raw_adaptive_rubric, dict) else ""
    )
    if adaptive_rubric_progress_state_ref and progress_state_ref and adaptive_rubric_progress_state_ref != progress_state_ref:
        errors.append("adaptive_rubric_progress_state_ref_mismatch")
    forbidden_influences = _string_list(score_result.get("forbidden_influences"), max_items=20, max_item_chars=120)
    if any(item in FORBIDDEN_EVALUATION_INFLUENCES for item in forbidden_influences):
        errors.append("score_result_forbidden_influence_detected")
    reasoning = _clean(score_result.get("reasoning"), max_chars=4000)
    if not reasoning:
        errors.append("score_result_reasoning_required")
    adaptive_insights, adaptive_insight_errors = _normalize_adaptive_insights(score_result.get("adaptive_insights"))
    errors.extend(adaptive_insight_errors)

    adaptive_rubric_dimensions = _adaptive_rubric_dimensions(raw_adaptive_rubric)
    raw_dimensions = score_result.get("dimension_scores")
    if not isinstance(raw_dimensions, list):
        return None, ("score_result_dimension_scores_required",), ()

    dimensions: list[SemanticScoreDimension] = []
    for raw_item in raw_dimensions:
        if not isinstance(raw_item, dict):
            errors.append("score_result_dimension_scores_invalid")
            continue
        dimension = _clean(raw_item.get("dimension") or raw_item.get("dimension_key"), max_chars=80)
        score = raw_item.get("score", raw_item.get("dimension_score"))
        if not _is_number(score):
            errors.append("score_value_invalid")
            continue
        adaptive_weight = raw_item.get("adaptive_weight")
        dimensions.append(
            SemanticScoreDimension(
                dimension=dimension,
                score=float(score),
                adaptive_weight=float(adaptive_weight) if _is_number(adaptive_weight) else 0.0,
                progress_focus=tuple(_string_list(raw_item.get("progress_focus"), max_items=10, max_item_chars=160)),
                rationale=_clean(raw_item.get("rationale") or raw_item.get("reasoning"), max_chars=2000),
            )
        )

    decision = ScoringPolicy.evaluate(
        ScoringInput(
            progress_state_ref=progress_state_ref,
            adaptive_rubric_dimensions=tuple(adaptive_rubric_dimensions),
            dimension_scores=tuple(dimensions),
            signals=tuple(_string_list(score_result.get("signals"), max_items=20, max_item_chars=80)),
            progress_updates=tuple(_dict_list(score_result.get("progress_updates"), max_items=20)),
        )
    )
    validation_errors = tuple(dict.fromkeys((*errors, *decision.validation_errors)))
    if validation_errors:
        return None, validation_errors, decision.warnings

    normalized = {
        "score_type": "polish_answer",
        "score_value": decision.score_value,
        "score_scale": "0-100",
        "rubric_version": ADAPTIVE_RUBRIC_VERSION,
        "anchor_set_id": ADAPTIVE_ANCHOR_SET_ID,
        "comparator_version": ADAPTIVE_COMPARATOR_VERSION,
        "aggregation_method": ADAPTIVE_SCORE_AGGREGATION_METHOD,
        "scoring_basis": ADAPTIVE_SCORE_BASIS,
        "progress_state_ref": decision.progress_state_ref,
        "reasoning": reasoning,
        "adaptive_rubric": {
            "rubric_version": ADAPTIVE_RUBRIC_VERSION,
            "progress_state_ref": decision.progress_state_ref,
            "dimensions": [
                {
                    "dimension": item.dimension,
                    "adaptive_weight": item.adaptive_weight,
                    "progress_basis": list(item.progress_basis),
                    "anchor_refs": list(item.anchor_refs),
                }
                for item in decision.adaptive_rubric_dimensions
            ],
        },
        "dimension_scores": [
            {
                "dimension": item.dimension,
                "score": item.score,
                "adaptive_weight": item.adaptive_weight,
                "progress_focus": list(item.progress_focus),
                "rationale": item.rationale,
            }
            for item in decision.dimension_scores
        ],
        "adaptive_insights": adaptive_insights,
        "signals": list(decision.signals),
        "progress_updates": [dict(item) for item in decision.progress_updates],
    }
    return normalized, (), decision.warnings


def _adaptive_rubric_dimensions(value: object) -> list[AdaptiveRubricDimension]:
    if not isinstance(value, dict):
        return []
    raw_dimensions = value.get("dimensions")
    if not isinstance(raw_dimensions, list):
        return []
    dimensions: list[AdaptiveRubricDimension] = []
    for raw_item in raw_dimensions:
        if not isinstance(raw_item, dict):
            continue
        weight = raw_item.get("adaptive_weight")
        dimensions.append(
            AdaptiveRubricDimension(
                dimension=_clean(raw_item.get("dimension") or raw_item.get("dimension_key"), max_chars=80),
                adaptive_weight=float(weight) if _is_number(weight) else 0.0,
                progress_basis=tuple(_string_list(raw_item.get("progress_basis"), max_items=10, max_item_chars=160)),
                anchor_refs=tuple(_string_list(raw_item.get("anchor_refs"), max_items=10, max_item_chars=120)),
            )
        )
    return dimensions


def _normalize_adaptive_insights(value: object) -> tuple[dict[str, list[str]], tuple[str, ...]]:
    if not isinstance(value, dict):
        return {}, ("adaptive_insights_required",)
    errors: list[str] = []
    if any(key not in value for key in ADAPTIVE_INSIGHT_REQUIRED_KEYS):
        errors.append("adaptive_insights_skill_diagnosis_required")
    normalized: dict[str, list[str]] = {}
    for key in (*ADAPTIVE_INSIGHT_REQUIRED_KEYS, *ADAPTIVE_INSIGHT_OPTIONAL_KEYS):
        normalized[key] = _string_list(value.get(key), max_items=20, max_item_chars=160)
    return normalized, tuple(errors)


def _dict_list(value: object, *, max_items: int) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, object]] = []
    for item in value:
        if isinstance(item, dict):
            result.append(dict(item))
        if len(result) >= max_items:
            break
    return result


def _string_list(value: object, *, max_items: int, max_item_chars: int) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    result: list[str] = []
    for item in value:
        text = _clean(item, max_chars=max_item_chars)
        if text and text not in result:
            result.append(text)
        if len(result) >= max_items:
            break
    return result


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _clean(value: object, *, max_chars: int = 240) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text
