from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from app.application.polish.answer_equivalence import semantic_text
from app.application.polish.payload_helpers import (
    _clean, _dict_items, _int_value, _mapping, _number, _stable_string_values,
)
from app.application.polish.question_source_normalization import (
    _stable_asset_summary_items, _stable_canonical_project_assets, _stable_question_source_items,
    _stable_recent_turn_items, _stable_retrieved_rag_chunks, _stable_same_question_answer_items,
)

_STEP4_SAME_ANSWER_CONTEXT_MAX_ITEMS = 5
_STEP4_CONTEXT_SOURCE_MAX_ITEMS = 8
_STEP4_CONTEXT_REF_MAX_ITEMS = 20
STEP5_TREND_CONTROLS_VERSION = "polish_step5_trend_controls.v1"
_StringObjectMap = Mapping[str, object]


def payload_normalization(context: dict[str, Any]) -> dict[str, Any]:
    stable = dict(context)
    same_question_answers = stable.get("same_question_answers")
    stable["evidence_refs"] = list(
        _stable_string_values(
            stable.get("evidence_refs"),
            max_items=_STEP4_CONTEXT_REF_MAX_ITEMS,
            max_chars=200,
        )
    )
    stable["question_sources"] = list(
        _stable_question_source_items(
            stable.get("question_sources"),
            max_items=_STEP4_CONTEXT_SOURCE_MAX_ITEMS,
        )
    )
    stable["same_question_answers"] = list(
        _stable_same_question_answer_items(
            same_question_answers,
            max_items=_STEP4_SAME_ANSWER_CONTEXT_MAX_ITEMS,
        )
    )
    stable["step5_effective_feedback_history"] = list(
        _step5_effective_feedback_history(
            same_question_answers,
            max_items=_STEP4_SAME_ANSWER_CONTEXT_MAX_ITEMS,
        )
    )
    stable["session_recent_turns"] = list(_stable_recent_turn_items(stable.get("session_recent_turns"), max_items=3))
    stable["project_asset_summaries"] = list(
        _stable_asset_summary_items(
            stable.get("project_asset_summaries"),
            max_items=_STEP4_CONTEXT_SOURCE_MAX_ITEMS,
        )
    )
    stable["canonical_project_assets"] = _stable_canonical_project_assets(stable.get("canonical_project_assets"))
    if "retrieved_rag_chunks" in stable and stable.get("retrieved_rag_chunks") is not None:
        stable["retrieved_rag_chunks"] = _stable_retrieved_rag_chunks(stable.get("retrieved_rag_chunks"))
    return stable


def apply_step5_improvement_trend_controls(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(payload)
    score_result = _mapping(result.get("score_result"))
    previous = _step5_latest_effective_history_item(context)
    if score_result is None or previous is None:
        return result

    previous_score_result = _mapping(previous.get("score_result")) or {}
    neutral_reason = _step5_neutralization_reason(result, context, previous)
    neutral = bool(neutral_reason)
    score_delta = 0.0 if neutral else _step5_score_delta(
        _number(score_result.get("score_value")),
        _number(previous_score_result.get("score_value")),
    )
    dimension_delta = _step5_dimension_delta(
        score_result,
        previous_score_result,
        neutral=neutral,
    )
    previous_loss_ids = set(_step5_string_list(previous.get("loss_point_ids"), max_items=40, max_item_chars=120))
    current_loss_ids = set(_step5_loss_point_ids(result.get("loss_points")))
    fixed_loss_ids = [] if neutral else sorted(previous_loss_ids - current_loss_ids)
    remaining_loss_ids = sorted(previous_loss_ids & current_loss_ids)
    regressed_points = [] if neutral else sorted(current_loss_ids - previous_loss_ids)

    answer_change = _mapping(result.get("answer_change_analysis")) or {}
    answer_change["score_delta"] = score_delta
    answer_change["dimension_delta"] = dimension_delta
    answer_change["fixed_loss_points"] = fixed_loss_ids
    answer_change["repeated_loss_points"] = remaining_loss_ids
    answer_change["regressed_points"] = regressed_points
    answer_change["trend"] = _step5_trend(
        neutral=neutral,
        score_delta=score_delta,
        dimension_delta=dimension_delta,
        fixed_loss_ids=fixed_loss_ids,
        regressed_points=regressed_points,
    )
    answer_change["derived_improvement_summary"] = {
        "score_delta": score_delta if score_delta is not None and score_delta > 0 else 0,
        "positive_dimension_deltas": {dimension: delta for dimension, delta in dimension_delta.items() if delta > 0},
        "fixed_loss_point_ids": fixed_loss_ids,
    }
    answer_change["derived_remaining_gap_summary"] = {
        "remaining_loss_point_ids": remaining_loss_ids,
        "non_positive_dimension_deltas": {dimension: delta for dimension, delta in dimension_delta.items() if delta <= 0},
    }
    answer_change["derived_regression_summary"] = {
        "score_delta": score_delta if score_delta is not None and score_delta < 0 else 0,
        "negative_dimension_deltas": {dimension: delta for dimension, delta in dimension_delta.items() if delta < 0},
        "regressed_points": regressed_points,
    }
    result["answer_change_analysis"] = answer_change

    metadata = _mapping(result.get("feedback_metadata")) or {}
    metadata["step5_trend_controls_version"] = STEP5_TREND_CONTROLS_VERSION
    metadata["step5_effective_result_basis"] = "latest_generated_feedback"
    if neutral_reason:
        metadata["step5_trend_neutralized_reason"] = neutral_reason
    if neutral_reason == "same_answer":
        metadata["step5_same_answer_trend_neutralized"] = True
    if neutral_reason == "reference_answer_replay":
        metadata["step5_reference_replay_trend_neutralized"] = True
    result["feedback_metadata"] = metadata
    _sync_step5_answer_change_cards(result, answer_change)
    return result


def _step5_effective_feedback_history(value: object, *, max_items: int) -> tuple[dict[str, Any], ...]:
    items: list[dict[str, Any]] = []
    for item in _dict_items(value):
        payload = _mapping(item.get("generated_feedback_payload"))
        if payload is None or _clean(payload.get("status"), max_chars=40) != "generated":
            continue
        items.append(
            {
                "answer_id": _clean(item.get("answer_id"), max_chars=120),
                "answer_round": _int_value(item.get("answer_round")),
                "answer_text": _clean(item.get("answer_text"), max_chars=12000),
                "score_result": _step5_score_result(payload.get("score_result")),
                "loss_point_ids": list(_step5_loss_point_ids(payload.get("loss_points"))),
            }
        )
    return tuple(sorted(items, key=_step5_answer_sort_key)[-max_items:])


def _step5_score_result(value: object) -> dict[str, Any]:
    score_result = _mapping(value) or {}
    normalized: dict[str, Any] = {}
    score_value = _number(score_result.get("score_value"))
    if score_value is not None:
        normalized["score_value"] = round(score_value, 2)
    dimensions: list[dict[str, Any]] = []
    for item in _dict_items(score_result.get("dimension_scores")):
        dimension = _clean(item.get("dimension"), max_chars=80)
        score = _number(item.get("score"))
        if dimension and score is not None:
            dimensions.append({"dimension": dimension, "score": round(score, 2)})
    if dimensions:
        normalized["dimension_scores"] = dimensions
    return normalized


def _step5_loss_point_ids(value: object) -> tuple[str, ...]:
    ids: list[str] = []
    for item in _dict_items(value):
        loss_id = _clean(item.get("loss_point_id"), max_chars=120)
        if loss_id and loss_id not in ids:
            ids.append(loss_id)
    return tuple(ids)


def _step5_answer_sort_key(item: dict[str, Any]) -> tuple[int, str]:
    round_value = item.get("answer_round")
    return (round_value if isinstance(round_value, int) else -1, str(item.get("answer_id") or ""))


def _step5_latest_effective_history_item(context: dict[str, Any]) -> dict[str, Any] | None:
    history = context.get("step5_effective_feedback_history")
    if not isinstance(history, list):
        return None
    items = [dict(item) for item in history if isinstance(item, dict)]
    return items[-1] if items else None


def _step5_neutralization_reason(
    payload: dict[str, Any],
    context: dict[str, Any],
    previous: dict[str, Any],
) -> str:
    metadata = _mapping(payload.get("feedback_metadata")) or {}
    if metadata.get("reference_answer_replay_detected") is True:
        return "reference_answer_replay"
    current = _clean(context.get("_step4_raw_answer_text") or context.get("answer_text"), max_chars=12000)
    previous_text = _clean(previous.get("answer_text"), max_chars=12000)
    if current and previous_text and semantic_text(current) == semantic_text(previous_text):
        return "same_answer"
    return ""


def _step5_score_delta(current_score: float | None, previous_score: float | None) -> float | None:
    if current_score is None or previous_score is None:
        return None
    return round(current_score - previous_score, 2)


def _step5_dimension_delta(
    current_score_result: _StringObjectMap,
    previous_score_result: _StringObjectMap,
    *,
    neutral: bool,
) -> dict[str, float]:
    previous_scores = _step5_dimension_scores(previous_score_result)
    current_scores = _step5_dimension_scores(current_score_result)
    dimensions = sorted(set(previous_scores) & set(current_scores))
    if neutral:
        return {dimension: 0.0 for dimension in dimensions}
    return {dimension: round(current_scores[dimension] - previous_scores[dimension], 2) for dimension in dimensions}


def _step5_dimension_scores(score_result: _StringObjectMap) -> dict[str, float]:
    scores: dict[str, float] = {}
    for score in _dict_items(score_result.get("dimension_scores")):
        dimension = _clean(score.get("dimension"), max_chars=80)
        value = _number(score.get("score"))
        if dimension and value is not None:
            scores[dimension] = round(value, 2)
    return scores


def _step5_string_list(value: object, *, max_items: int, max_item_chars: int) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    result: list[str] = []
    for item in value:
        text = _clean(item, max_chars=max_item_chars)
        if text and text not in result:
            result.append(text)
        if len(result) >= max_items:
            break
    return tuple(result)


def _step5_trend(
    *,
    neutral: bool,
    score_delta: float | None,
    dimension_delta: dict[str, float],
    fixed_loss_ids: list[str],
    regressed_points: list[str],
) -> str:
    if neutral:
        return "unchanged"
    improved = bool(fixed_loss_ids) or any(delta > 0 for delta in dimension_delta.values())
    regressed = bool(regressed_points) or any(delta < 0 for delta in dimension_delta.values())
    if score_delta is not None:
        improved = improved or score_delta > 0
        regressed = regressed or score_delta < 0
    if improved and regressed:
        return "mixed"
    if regressed:
        return "regressed"
    if improved:
        return "improved"
    return "unchanged"


def _sync_step5_answer_change_cards(payload: dict[str, Any], answer_change: _StringObjectMap) -> None:
    cards = payload.get("feedback_cards")
    if not isinstance(cards, list):
        return
    for card in cards:
        if not isinstance(card, dict) or card.get("card_type") != "answer_change":
            continue
        card["status"] = answer_change.get("trend")
        card["payload"] = dict(answer_change)
        return
    cards.append({"card_type": "answer_change", "status": answer_change.get("trend"), "payload": dict(answer_change)})
