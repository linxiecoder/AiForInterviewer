from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.application.polish.feedback_schema import POLISH_FEEDBACK_FINAL_SCHEMA_ID
from app.application.polish.payload_helpers import (
    _clean,
    _dict_items,
    _mapping,
    _number,
    _stable_string_values,
    _string_tuple,
)
from app.domain.polish.policies.scoring_policy import ADAPTIVE_RUBRIC_DIMENSIONS


def normalize_legacy_final_feedback_payload(payload: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(payload)
    if _clean(result.get("schema_id"), max_chars=120) != POLISH_FEEDBACK_FINAL_SCHEMA_ID:
        return result
    _normalize_legacy_score_result(result)
    result["asset_consistency_check"] = _legacy_asset_consistency_check(result.get("asset_consistency_check"))
    result["answer_coverage"] = _legacy_answer_coverage(result.get("answer_coverage"))
    result["answer_change_analysis"] = _legacy_answer_change_analysis(result.get("answer_change_analysis"))
    result["feedback_cards"] = _legacy_feedback_cards(result.get("feedback_cards"))
    if not isinstance(result.get("next_recommended_actions"), list):
        result["next_recommended_actions"] = []
    return result


def _normalize_legacy_score_result(payload: dict[str, Any]) -> None:
    score_result = _mapping(payload.get("score_result"))
    if score_result is None:
        return
    score_value = _number(score_result.get("score_value"))
    if score_value is None:
        return
    progress_ref = _legacy_progress_ref(score_result)
    score_result["progress_state_ref"] = progress_ref
    insights = _legacy_adaptive_insights(score_result)
    score_result["adaptive_insights"] = insights if any(insights.values()) else _legacy_adaptive_insights_from_payload(payload)
    if not _has_complete_legacy_score_dimensions(score_result):
        score_result["adaptive_rubric"] = _legacy_adaptive_rubric(progress_ref)
        score_result["dimension_scores"] = _legacy_dimension_scores(score_result, progress_ref)
    if not _string_tuple(score_result.get("signals")):
        score_result["signals"] = ["progress_update"]
    if not _dict_items(score_result.get("progress_updates")):
        score_result["progress_updates"] = [
            {
                "progress_node_ref": progress_ref,
                "signal": "progress_update",
                "dimension": ADAPTIVE_RUBRIC_DIMENSIONS[0],
                "rationale": "Legacy final payload compatibility projection.",
            }
        ]
    payload["score_result"] = score_result


def _legacy_progress_ref(score_result: dict[str, Any]) -> str:
    adaptive_rubric = _mapping(score_result.get("adaptive_rubric")) or {}
    progress_updates = _dict_items(score_result.get("progress_updates"))
    return (
        _clean(score_result.get("progress_state_ref"), max_chars=120)
        or _clean(adaptive_rubric.get("progress_state_ref"), max_chars=120)
        or next(
            (
                _clean(item.get("progress_node_ref") or item.get("node_ref"), max_chars=120)
                for item in progress_updates
                if _clean(item.get("progress_node_ref") or item.get("node_ref"), max_chars=120)
            ),
            "",
        )
        or "legacy_feedback_progress_state"
    )


def _legacy_adaptive_insights(score_result: dict[str, Any]) -> dict[str, list[str]]:
    source = _mapping(score_result.get("adaptive_insights")) or {}
    return {
        "weak_skills": list(_stable_string_values(source.get("weak_skills"), max_items=20, max_chars=160)),
        "strong_skills": list(_stable_string_values(source.get("strong_skills"), max_items=20, max_chars=160)),
        "unstable_skills": list(_stable_string_values(source.get("unstable_skills"), max_items=20, max_chars=160)),
        "overweighted_skills": list(_stable_string_values(source.get("overweighted_skills"), max_items=20, max_chars=160)),
        "underweighted_skills": list(_stable_string_values(source.get("underweighted_skills"), max_items=20, max_chars=160)),
    }


def _legacy_adaptive_insights_from_payload(payload: dict[str, Any]) -> dict[str, list[str]]:
    coverage = _legacy_answer_coverage(payload.get("answer_coverage"))
    weak_skills = [
        text
        for text in (
            *(_clean(item.get("reason"), max_chars=160) for item in _dict_items(payload.get("loss_points"))),
            *_stable_string_values(coverage.get("weak_points"), max_items=20, max_chars=160),
            *_stable_string_values(coverage.get("missing_points"), max_items=20, max_chars=160),
        )
        if text
    ]
    return {
        "weak_skills": list(dict.fromkeys(weak_skills[:20])) or ["legacy_feedback_follow_up_required"],
        "strong_skills": [],
        "unstable_skills": [],
        "overweighted_skills": [],
        "underweighted_skills": [],
    }


def _has_complete_legacy_score_dimensions(score_result: dict[str, Any]) -> bool:
    rubric = _mapping(score_result.get("adaptive_rubric")) or {}
    rubric_dimensions = {_dimension_name(item.get("dimension")) for item in _dict_items(rubric.get("dimensions"))}
    score_dimensions = {
        _dimension_name(item.get("dimension") or item.get("dimension_key"))
        for item in _dict_items(score_result.get("dimension_scores"))
    }
    required = set(ADAPTIVE_RUBRIC_DIMENSIONS)
    return required <= rubric_dimensions and required <= score_dimensions


def _legacy_adaptive_rubric(progress_ref: str) -> dict[str, Any]:
    weight = round(1 / len(ADAPTIVE_RUBRIC_DIMENSIONS), 6)
    return {
        "rubric_version": "polish_answer.progress_adaptive_rubric.v1",
        "progress_state_ref": progress_ref,
        "dimensions": [
            {
                "dimension": dimension,
                "adaptive_weight": weight,
                "progress_basis": [progress_ref],
                "anchor_refs": [],
            }
            for dimension in ADAPTIVE_RUBRIC_DIMENSIONS
        ],
    }


def _legacy_dimension_scores(score_result: dict[str, Any], progress_ref: str) -> list[dict[str, Any]]:
    score_value = _number(score_result.get("score_value")) or 0.0
    dimension_score = score_value * 100 if 0 <= score_value <= 1 else score_value
    weight = round(1 / len(ADAPTIVE_RUBRIC_DIMENSIONS), 6)
    rationale = _clean(score_result.get("reasoning"), max_chars=2000) or "Legacy final payload compatibility projection."
    return [
        {
            "dimension": dimension,
            "score": dimension_score,
            "adaptive_weight": weight,
            "progress_focus": [progress_ref],
            "rationale": rationale,
        }
        for dimension in ADAPTIVE_RUBRIC_DIMENSIONS
    ]


def _legacy_asset_consistency_check(value: object) -> dict[str, Any]:
    source = _mapping(value) or {}
    status = _clean(source.get("status"), max_chars=80)
    if status == "passed":
        status = "consistent"
    if status not in {"consistent", "conflict", "insufficient_asset_context", "not_applicable"}:
        status = "not_applicable"
    return {
        **source,
        "status": status,
        "checked_asset_refs": list(_stable_string_values(source.get("checked_asset_refs"), max_items=20, max_chars=160)),
        "conflicts": list(_dict_items(source.get("conflicts"))),
        "unsupported_claims": list(_dict_items(source.get("unsupported_claims"))),
        "user_clarification_required": bool(source.get("user_clarification_required", False)),
    }


def _legacy_answer_coverage(value: object) -> dict[str, Any]:
    source = _mapping(value) or {}
    result = dict(source)
    for field_name in ("expected_points", "covered_points", "missing_points", "weak_points", "contradicted_points"):
        result[field_name] = _legacy_string_values(result.get(field_name), max_items=40, max_chars=240)
    return result


def _legacy_answer_change_analysis(value: object) -> dict[str, Any]:
    source = _mapping(value) or {}
    trend = _clean(source.get("trend") or source.get("status"), max_chars=80)
    if trend not in {"improved", "regressed", "mixed", "unchanged", "first_attempt"}:
        trend = "first_attempt"
    result = dict(source)
    result["has_prior_attempts"] = bool(source.get("has_prior_attempts", False))
    for field_name in (
        "previous_answer_refs",
        "retained_points",
        "newly_added_points",
        "regressed_points",
        "repeated_loss_points",
        "fixed_loss_points",
    ):
        result[field_name] = _legacy_string_values(result.get(field_name), max_items=40, max_chars=240)
    result["trend"] = trend
    result["score_delta"] = _number(source.get("score_delta"))
    return result


def _legacy_feedback_cards(value: object) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for item in _dict_items(value):
        card = dict(item)
        if not _clean(card.get("card_type") or card.get("type"), max_chars=80):
            card["card_type"] = "overall"
        cards.append(card)
    return cards or [
        {
            "card_id": "legacy_feedback_overall",
            "card_type": "overall",
            "title": "反馈摘要",
            "summary": "Legacy final payload compatibility projection.",
        }
    ]


def _legacy_string_values(value: object, *, max_items: int, max_chars: int) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    result: list[str] = []
    for item in value:
        text = _clean(item, max_chars=max_chars)
        if text and text not in result:
            result.append(text)
        if len(result) >= max_items:
            break
    return result


def _dimension_name(value: object) -> str:
    return _clean(value, max_chars=80).lower().replace("-", "_").replace(" ", "_")
