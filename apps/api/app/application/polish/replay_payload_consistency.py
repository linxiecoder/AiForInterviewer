from __future__ import annotations

from typing import Any

from app.application.polish.answer_equivalence import text_matches_reference_terms
from app.application.polish.payload_helpers import (
    _clean,
    _dict_items,
    _mapping,
    _number,
    _stable_string_values,
    _string_tuple,
)
from app.application.polish.score_flooring import _dimension_score_mean

_STEP4_BLOCKED_NEXT_ACTIONS_AFTER_REPLAY = frozenset(
    {
        "continue-next-question", "continue_next_question",
        "continue-fixing-loss-points", "continue-same-question",
        "continue_fixing_loss_points", "continue_same_question",
        "improve-current-answer", "improve_current_answer",
        "retry", "retry-current-answer", "retry-same-question",
        "retry-same-question-preserve-regressed-points",
        "retry_current_answer", "retry_same_question",
        "retry_same_question_preserve_regressed_points",
        "revise-current-answer", "revise_current_answer",
    }
)
_ANSWER_CHANGE_UNRESOLVED_FIELDS = (
    "repeated_loss_points", "repeated_loss_point_ids",
    "remaining_loss_points", "remaining_loss_point_ids",
    "regressed_points", "next_retry_focus",
)


def _remove_replayed_loss_points(payload: dict[str, Any], replay_loss_ids: set[str]) -> list[dict[str, Any]]:
    remaining_loss_points: list[dict[str, Any]] = []
    removed_loss_points: list[dict[str, Any]] = []
    for loss_point in _dict_items(payload.get("loss_points")):
        loss_id = _clean(loss_point.get("loss_point_id"), max_chars=120)
        if loss_id and loss_id in replay_loss_ids:
            removed_loss_points.append(dict(loss_point))
            continue
        remaining_loss_points.append(dict(loss_point))
    payload["loss_points"] = remaining_loss_points
    _remove_replayed_key_loss_points(payload, replay_loss_ids)
    _sync_reference_answer_addresses(payload)
    return removed_loss_points


def _sync_reference_replay_payload_consistency(
    payload: dict[str, Any],
    replay_loss_ids: set[str],
    match_terms: tuple[str, ...],
) -> None:
    _remove_replayed_loss_points(payload, replay_loss_ids)
    _remove_replayed_key_loss_points_by_terms(payload, match_terms)
    _sync_answer_coverage_after_reference_replay(payload, match_terms)
    _sync_answer_change_after_reference_replay(payload, replay_loss_ids, match_terms)
    _sync_next_actions_after_reference_replay(payload)
    _sync_feedback_cards_after_step4(payload)


def _has_reference_replay_payload_contradiction(
    payload: dict[str, Any],
    replay_loss_ids: set[str],
    match_terms: tuple[str, ...],
) -> bool:
    current_loss_ids = {
        loss_id
        for loss_point in _dict_items(payload.get("loss_points"))
        if (loss_id := _clean(loss_point.get("loss_point_id"), max_chars=120))
    }
    if current_loss_ids:
        return True
    key_loss_points = payload.get("key_loss_points")
    if isinstance(key_loss_points, (list, tuple)) and key_loss_points:
        return True
    if _has_unresolved_step4_feedback_points(payload):
        return True
    answer_coverage = _mapping(payload.get("answer_coverage")) or {}
    for field_name in ("missing_points", "weak_points", "contradicted_points"):
        for item in _string_tuple(answer_coverage.get(field_name)):
            if _text_matches_reference_replay_terms(item, match_terms):
                return True
    answer_change = _mapping(payload.get("answer_change_analysis")) or {}
    for field_name in _ANSWER_CHANGE_UNRESOLVED_FIELDS:
        for item in _string_tuple(answer_change.get(field_name)):
            if _text_matches_reference_replay_terms(item, match_terms):
                return True
    if any(_is_blocked_reference_replay_next_action(action) for action in _string_tuple(payload.get("next_recommended_actions"))):
        return True
    if not _score_result_matches_dimensions(payload):
        return True
    return bool(current_loss_ids & replay_loss_ids)


def _sync_feedback_cards_after_step4(payload: dict[str, Any]) -> None:
    cards = payload.get("feedback_cards")
    if not isinstance(cards, list):
        return
    synced_cards: list[dict[str, Any]] = []
    for card in cards:
        if not isinstance(card, dict):
            continue
        card_type = _clean(card.get("card_type") or card.get("type"), max_chars=80)
        if card_type == "loss_points" and not _dict_items(payload.get("loss_points")):
            continue
        synced_card = dict(card)
        card_payload = synced_card.get("payload")
        if card_type == "overall" and isinstance(card_payload, dict):
            synced_card["payload"] = dict(card_payload) | {"score_result": payload.get("score_result")}
        elif card_type == "loss_points":
            synced_card["payload"] = payload.get("loss_points")
        elif card_type == "reference_answer":
            synced_card["payload"] = payload.get("reference_answer")
        elif card_type == "answer_coverage":
            synced_card["payload"] = payload.get("answer_coverage")
        elif card_type == "answer_change":
            synced_card["payload"] = payload.get("answer_change_analysis")
        elif card_type == "next_actions":
            synced_card["payload"] = {"next_recommended_actions": payload.get("next_recommended_actions") or []}
        synced_cards.append(synced_card)
    payload["feedback_cards"] = synced_cards


def _remove_replayed_key_loss_points(payload: dict[str, Any], replay_loss_ids: set[str]) -> None:
    key_loss_points = payload.get("key_loss_points")
    if not isinstance(key_loss_points, (list, tuple)):
        return
    remaining_items: list[Any] = []
    for item in key_loss_points:
        if isinstance(item, dict):
            loss_id = _clean(item.get("loss_point_id") or item.get("loss_id") or item.get("id"), max_chars=120)
            if loss_id and loss_id in replay_loss_ids:
                continue
            remaining_items.append(dict(item))
            continue
        if _clean(item, max_chars=120) not in replay_loss_ids:
            remaining_items.append(item)
    payload["key_loss_points"] = remaining_items


def _sync_reference_answer_addresses(payload: dict[str, Any]) -> None:
    remaining_loss_ids = {
        loss_id
        for loss_point in _dict_items(payload.get("loss_points"))
        if (loss_id := _clean(loss_point.get("loss_point_id"), max_chars=120))
    }
    reference_answer = _mapping(payload.get("reference_answer"))
    if reference_answer is None:
        return
    normalized_sections: list[dict[str, Any]] = []
    for section in _dict_items(reference_answer.get("sections")):
        normalized_section = dict(section)
        normalized_section["addresses_loss_point_ids"] = [
            loss_id
            for loss_id in _stable_string_values(section.get("addresses_loss_point_ids"), max_items=40, max_chars=120)
            if loss_id in remaining_loss_ids
        ]
        normalized_sections.append(normalized_section)
    payload["reference_answer"] = dict(reference_answer) | {"sections": normalized_sections}


def _sync_answer_coverage_after_reference_replay(payload: dict[str, Any], match_terms: tuple[str, ...]) -> None:
    answer_coverage = _mapping(payload.get("answer_coverage"))
    if answer_coverage is None:
        return
    updated_coverage = dict(answer_coverage)
    for field_name in ("missing_points", "weak_points", "contradicted_points"):
        updated_coverage[field_name] = [
            item
            for item in _string_tuple(updated_coverage.get(field_name))
            if not _text_matches_reference_replay_terms(item, match_terms)
        ]
    covered_points = list(_string_tuple(updated_coverage.get("covered_points")))
    if "reference_answer_covered" not in covered_points:
        covered_points.append("reference_answer_covered")
    updated_coverage["covered_points"] = covered_points
    payload["answer_coverage"] = updated_coverage


def _sync_answer_change_after_reference_replay(
    payload: dict[str, Any],
    replay_loss_ids: set[str],
    match_terms: tuple[str, ...],
) -> None:
    answer_change = _mapping(payload.get("answer_change_analysis"))
    if answer_change is None:
        return
    updated_change = dict(answer_change)
    for field_name in _ANSWER_CHANGE_UNRESOLVED_FIELDS:
        updated_change[field_name] = [
            item
            for item in _string_tuple(updated_change.get(field_name))
            if not _text_matches_reference_replay_terms(item, match_terms)
        ]
    for field_name in ("fixed_loss_points", "fixed_loss_point_ids"):
        fixed_items = list(_string_tuple(updated_change.get(field_name)))
        for loss_id in sorted(replay_loss_ids):
            if loss_id not in fixed_items:
                fixed_items.append(loss_id)
        updated_change[field_name] = fixed_items
    if not updated_change.get("regressed_points") and not updated_change.get("repeated_loss_points"):
        updated_change["trend"] = "improved"
    payload["answer_change_analysis"] = updated_change


def _sync_next_actions_after_reference_replay(payload: dict[str, Any]) -> None:
    answer_change = _mapping(payload.get("answer_change_analysis")) or {}
    if not _string_tuple(answer_change.get("regressed_points")) and not _string_tuple(
        answer_change.get("repeated_loss_points")
    ):
        payload["next_recommended_actions"] = [
            action
            for action in _string_tuple(payload.get("next_recommended_actions"))
            if action != "retry_same_question_preserve_regressed_points"
        ]
    next_actions = [
        action
        for action in _string_tuple(payload.get("next_recommended_actions"))
        if not _is_blocked_reference_replay_next_action(action)
    ]
    payload["next_recommended_actions"] = next_actions
    if _has_unresolved_step4_feedback_points(payload):
        if not next_actions:
            payload["next_recommended_actions"] = ["review_reference_answer"]
        return
    payload["next_recommended_actions"] = next_actions or ["review_reference_answer"]


def _is_blocked_reference_replay_next_action(action: str) -> bool:
    normalized_action = action.strip().lower().replace("_", "-")
    return action in _STEP4_BLOCKED_NEXT_ACTIONS_AFTER_REPLAY or normalized_action in _STEP4_BLOCKED_NEXT_ACTIONS_AFTER_REPLAY


def _has_unresolved_step4_feedback_points(payload: dict[str, Any]) -> bool:
    if _dict_items(payload.get("loss_points")):
        return True
    answer_coverage = _mapping(payload.get("answer_coverage")) or {}
    for field_name in ("missing_points", "weak_points", "contradicted_points"):
        if _string_tuple(answer_coverage.get(field_name)):
            return True
    answer_change = _mapping(payload.get("answer_change_analysis")) or {}
    return any(_string_tuple(answer_change.get(field_name)) for field_name in _ANSWER_CHANGE_UNRESOLVED_FIELDS)


def _score_result_matches_dimensions(payload: dict[str, Any]) -> bool:
    score_result = _mapping(payload.get("score_result"))
    if score_result is None:
        return False
    score_value = _number(score_result.get("score_value"))
    if score_value is None:
        return False
    dimension_mean = _dimension_score_mean(score_result)
    if dimension_mean is None:
        return True
    return abs(score_value - dimension_mean) <= 0.5


def _remove_replayed_key_loss_points_by_terms(payload: dict[str, Any], match_terms: tuple[str, ...]) -> None:
    key_loss_points = payload.get("key_loss_points")
    if not isinstance(key_loss_points, (list, tuple)):
        return
    payload["key_loss_points"] = [
        dict(item) if isinstance(item, dict) else item
        for item in key_loss_points
        if not _text_matches_reference_replay_terms(item, match_terms)
    ]


def _text_matches_reference_replay_terms(value: object, match_terms: tuple[str, ...]) -> bool:
    return text_matches_reference_terms(value, match_terms)
