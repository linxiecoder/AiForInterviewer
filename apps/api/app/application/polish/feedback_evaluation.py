"""Progress-aware adaptive evaluation contract for Polish feedback."""

from __future__ import annotations

from typing import Any, TypeGuard

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
ADAPTIVE_INSIGHT_DICT_ALIASES = {
    "weaknesses": "weak_skills",
    "weakness": "weak_skills",
    "weak_points": "weak_skills",
    "gaps": "weak_skills",
    "strengths": "strong_skills",
    "strength": "strong_skills",
    "strong_points": "strong_skills",
    "risks": "unstable_skills",
    "risk": "unstable_skills",
    "drifts": "unstable_skills",
    "drift": "unstable_skills",
    "unstable": "unstable_skills",
    "overweighted": "overweighted_skills",
    "overweight": "overweighted_skills",
    "underweighted": "underweighted_skills",
    "underweight": "underweighted_skills",
}


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
    expected_ref = _clean(expected_progress_state_ref, max_chars=120)
    progress_state_ref = _clean(score_result.get("progress_state_ref"), max_chars=120) or expected_ref
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
    normalization_warnings: list[str] = []
    adaptive_insights, adaptive_insight_errors, adaptive_insight_warnings = _normalize_adaptive_insights(
        score_result.get("adaptive_insights")
    )
    errors.extend(adaptive_insight_errors)
    normalization_warnings.extend(adaptive_insight_warnings)

    raw_dimensions = score_result.get("dimension_scores")
    if not isinstance(raw_dimensions, list):
        return None, ("score_result_dimension_scores_required",), ()

    rubric_weight_by_key = _adaptive_rubric_weight_by_key(raw_adaptive_rubric)
    score_scale_factor = _score_scale_factor(raw_dimensions)
    if score_scale_factor != 1.0:
        normalization_warnings.append("score_result_scores_normalized_from_unit_scale")
    dimensions: list[SemanticScoreDimension] = []
    dimension_weight_by_key: dict[str, float] = {}
    progress_focus_by_key: dict[str, tuple[str, ...]] = {}
    for raw_item in raw_dimensions:
        if not isinstance(raw_item, dict):
            errors.append("score_result_dimension_scores_invalid")
            continue
        dimension = _clean(raw_item.get("dimension") or raw_item.get("dimension_key"), max_chars=80)
        score = raw_item.get("score", raw_item.get("dimension_score"))
        if not _is_number(score):
            errors.append("score_value_invalid")
            continue
        dimension_key = _dimension_key(dimension)
        adaptive_weight = raw_item.get("adaptive_weight")
        if not _is_number(adaptive_weight) and dimension_key in rubric_weight_by_key:
            adaptive_weight = rubric_weight_by_key[dimension_key]
            normalization_warnings.append("score_result_adaptive_weight_recovered_from_adaptive_rubric")
        progress_focus = tuple(
            _progress_focus_list(
                raw_item.get("progress_focus"),
                default_progress_state_ref=progress_state_ref,
            )
        )
        if not progress_focus and progress_state_ref:
            progress_focus = (progress_state_ref,)
            normalization_warnings.append("score_result_progress_focus_defaulted_to_progress_state")
        if dimension_key and _is_number(adaptive_weight):
            dimension_weight_by_key[dimension_key] = float(adaptive_weight)
        if dimension_key and progress_focus:
            progress_focus_by_key[dimension_key] = progress_focus
        dimensions.append(
            SemanticScoreDimension(
                dimension=dimension,
                score=float(score) * score_scale_factor,
                adaptive_weight=float(adaptive_weight) if _is_number(adaptive_weight) else 0.0,
                progress_focus=progress_focus,
                rationale=_clean(raw_item.get("rationale") or raw_item.get("reasoning"), max_chars=2000),
            )
        )

    adaptive_rubric_dimensions, adaptive_rubric_warnings = _adaptive_rubric_dimensions(
        raw_adaptive_rubric,
        dimension_weight_by_key=dimension_weight_by_key,
        progress_focus_by_key=progress_focus_by_key,
        default_progress_state_ref=progress_state_ref,
    )
    normalization_warnings.extend(adaptive_rubric_warnings)
    decision = ScoringPolicy.evaluate(
        ScoringInput(
            progress_state_ref=progress_state_ref,
            adaptive_rubric_dimensions=tuple(adaptive_rubric_dimensions),
            dimension_scores=tuple(dimensions),
            signals=tuple(_signal_list(score_result.get("signals"), max_items=20, max_item_chars=80)),
            progress_updates=tuple(
                _progress_update_list(
                    score_result.get("progress_updates"),
                    default_progress_state_ref=progress_state_ref,
                    max_items=20,
                )
            ),
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
    return normalized, (), tuple(dict.fromkeys((*normalization_warnings, *decision.warnings)))


def _adaptive_rubric_dimensions(
    value: object,
    *,
    dimension_weight_by_key: dict[str, float],
    progress_focus_by_key: dict[str, tuple[str, ...]],
    default_progress_state_ref: str,
) -> tuple[list[AdaptiveRubricDimension], tuple[str, ...]]:
    if not isinstance(value, dict):
        return [], ()
    raw_dimensions = value.get("dimensions")
    if not isinstance(raw_dimensions, list):
        return [], ()
    dimensions: list[AdaptiveRubricDimension] = []
    warnings: list[str] = []
    for raw_item in raw_dimensions:
        if not isinstance(raw_item, dict):
            continue
        dimension = _clean(raw_item.get("dimension") or raw_item.get("dimension_key"), max_chars=80)
        dimension_key = _dimension_key(dimension)
        weight = raw_item.get("adaptive_weight")
        if not _is_number(weight) and dimension_key in dimension_weight_by_key:
            weight = dimension_weight_by_key[dimension_key]
            warnings.append("adaptive_rubric_weight_recovered_from_dimension_scores")
        progress_basis = tuple(_string_list(raw_item.get("progress_basis"), max_items=10, max_item_chars=160))
        if not progress_basis and dimension_key in progress_focus_by_key:
            progress_basis = progress_focus_by_key[dimension_key]
            warnings.append("adaptive_rubric_progress_basis_recovered_from_dimension_scores")
        if not progress_basis and default_progress_state_ref:
            progress_basis = (default_progress_state_ref,)
            warnings.append("adaptive_rubric_progress_basis_defaulted_to_progress_state")
        dimensions.append(
            AdaptiveRubricDimension(
                dimension=dimension,
                adaptive_weight=float(weight) if _is_number(weight) else 0.0,
                progress_basis=progress_basis,
                anchor_refs=tuple(_string_list(raw_item.get("anchor_refs"), max_items=10, max_item_chars=120)),
            )
        )
    return dimensions, tuple(dict.fromkeys(warnings))


def _normalize_adaptive_insights(value: object) -> tuple[dict[str, list[str]], tuple[str, ...], tuple[str, ...]]:
    if isinstance(value, list):
        normalized = {key: [] for key in (*ADAPTIVE_INSIGHT_REQUIRED_KEYS, *ADAPTIVE_INSIGHT_OPTIONAL_KEYS)}
        for item in value:
            if not isinstance(item, dict):
                continue
            text = _clean(
                item.get("content") or item.get("text") or item.get("reason") or item.get("description"),
                max_chars=160,
            )
            if not text:
                continue
            item_type = _clean(item.get("type") or item.get("category") or item.get("insight_type"), max_chars=80).lower()
            if item_type in {"strength", "strong", "strong_skill"}:
                target_key = "strong_skills"
            elif item_type in {"gap", "drift", "unstable", "risk"}:
                target_key = "unstable_skills"
            elif item_type in {"overweight", "overweighted"}:
                target_key = "overweighted_skills"
            elif item_type in {"underweight", "underweighted"}:
                target_key = "underweighted_skills"
            else:
                target_key = "weak_skills"
            if text not in normalized[target_key]:
                normalized[target_key].append(text)
        if not any(normalized.values()):
            return {}, ("adaptive_insights_required",), ()
        return normalized, (), ("adaptive_insights_list_normalized",)
    if not isinstance(value, dict):
        return {}, ("adaptive_insights_required",), ()
    errors: list[str] = []
    warnings: list[str] = []
    normalized: dict[str, list[str]] = {}
    for key in (*ADAPTIVE_INSIGHT_REQUIRED_KEYS, *ADAPTIVE_INSIGHT_OPTIONAL_KEYS):
        normalized[key] = _string_list(value.get(key), max_items=20, max_item_chars=160)
    alias_data_found = False
    for alias, target_key in ADAPTIVE_INSIGHT_DICT_ALIASES.items():
        alias_items = _string_list(value.get(alias), max_items=20, max_item_chars=160)
        if not alias_items:
            continue
        alias_data_found = True
        warnings.append("adaptive_insights_dict_aliases_normalized")
        for item in alias_items:
            if item not in normalized[target_key]:
                normalized[target_key].append(item)
    if any(key not in value for key in ADAPTIVE_INSIGHT_REQUIRED_KEYS) and not alias_data_found:
        errors.append("adaptive_insights_skill_diagnosis_required")
    if not any(normalized.values()):
        errors.append("adaptive_insights_required")
    return normalized, tuple(dict.fromkeys(errors)), tuple(dict.fromkeys(warnings))


def _adaptive_rubric_weight_by_key(value: object) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    raw_dimensions = value.get("dimensions")
    if not isinstance(raw_dimensions, list):
        return {}
    result: dict[str, float] = {}
    for item in raw_dimensions:
        if not isinstance(item, dict):
            continue
        dimension_key = _dimension_key(item.get("dimension") or item.get("dimension_key"))
        weight = item.get("adaptive_weight")
        if dimension_key and _is_number(weight):
            result.setdefault(dimension_key, float(weight))
    return result


def _score_scale_factor(raw_dimensions: object) -> float:
    if not isinstance(raw_dimensions, list):
        return 1.0
    scores: list[float] = []
    for item in raw_dimensions:
        if not isinstance(item, dict):
            continue
        score = item.get("score", item.get("dimension_score"))
        if _is_number(score):
            scores.append(float(score))
    if scores and all(0 <= score <= 1 for score in scores):
        return 100.0
    return 1.0


def _progress_update_list(
    value: object,
    *,
    default_progress_state_ref: str,
    max_items: int,
) -> list[dict[str, object]]:
    if isinstance(value, dict):
        raw_items = tuple(value.items())
    elif isinstance(value, list):
        raw_items = tuple((None, item) for item in value)
    else:
        return []

    result: list[dict[str, object]] = []
    for keyed_ref, item in raw_items:
        if isinstance(item, dict):
            normalized = dict(item)
            progress_node_ref = _clean(keyed_ref, max_chars=120)
            if not normalized.get("progress_node_ref") and not normalized.get("node_ref"):
                normalized["progress_node_ref"] = progress_node_ref or default_progress_state_ref
            if not normalized.get("signal"):
                signal = _clean(normalized.get("status") or normalized.get("type"), max_chars=80)
                normalized["signal"] = signal if signal in ADAPTIVE_SIGNAL_TYPES else "progress_update"
            if not normalized.get("rationale") and normalized.get("detail"):
                normalized["rationale"] = _clean(normalized.get("detail"), max_chars=1000)
            if not normalized.get("rationale") and normalized.get("reason"):
                normalized["rationale"] = _clean(normalized.get("reason"), max_chars=1000)
            result.append(normalized)
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


def _progress_focus_list(value: object, *, default_progress_state_ref: str) -> list[str]:
    if isinstance(value, bool):
        return [default_progress_state_ref] if default_progress_state_ref else []
    return _string_list(value, max_items=10, max_item_chars=160)


def _signal_list(value: object, *, max_items: int, max_item_chars: int) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, dict):
            text = _clean(item.get("signal_type") or item.get("type"), max_chars=max_item_chars)
        else:
            text = _clean(item, max_chars=max_item_chars)
        if text and text not in result:
            result.append(text)
        if len(result) >= max_items:
            break
    return result


def _dimension_key(value: object) -> str:
    return _clean(value, max_chars=80).lower().replace("-", "_").replace(" ", "_")


def _is_number(value: object) -> TypeGuard[int | float]:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _clean(value: object, *, max_chars: int = 240) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text
