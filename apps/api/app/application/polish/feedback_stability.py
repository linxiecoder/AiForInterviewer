from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.application.polish.answer_equivalence import semantic_text
from app.application.polish.feedback_rules import apply_feedback_core_rules
from app.application.polish.payload_helpers import _clean, _dict_items, _list_items, _mapping, _string_tuple
from app.application.polish.payload_normalization import payload_normalization
from app.application.polish.question_source_normalization import (
    _previous_feedback_payload,
    _stable_previous_reference_answer_text,
)
from app.application.polish.replay_eligibility import (
    ReplayEligibilityAdapters,
    _answer_covers_full_reference_answer,
    _historical_replay_score_floor,
    _loss_points_for_ids,
    _previous_answer_loss_point_ids,
    _reference_replay_match_terms,
    _replayed_reference_loss_ids,
    replay_eligibility,
)
from app.application.polish.replay_payload_consistency import (
    _has_reference_replay_payload_contradiction,
    _remove_replayed_loss_points,
    _sync_feedback_cards_after_step4,
    _sync_reference_replay_payload_consistency,
    _text_matches_reference_replay_terms,
)
from app.application.polish.score_flooring import (
    _raise_score_result_floor,
    _set_score_result_value,
    _stable_score_from_loss_points,
)

_STEP4_STABILITY_CONTROLS_VERSION = "polish_step4_stability_controls.v2"


def stable_feedback_generation_context(context: dict[str, Any]) -> dict[str, Any]:
    return payload_normalization(context)


def apply_step4_stability_controls(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(payload)
    score_result = _mapping(result.get("score_result"))
    if score_result is None:
        return result

    metadata = dict(_mapping(result.get("feedback_metadata")) or {})
    metadata["step4_stability_controls_version"] = _STEP4_STABILITY_CONTROLS_VERSION

    eligibility_result = replay_eligibility(
        result,
        context,
        adapters=ReplayEligibilityAdapters(
            clean=_clean,
            context_value=_context_value,
            dict_items=_dict_items,
            previous_feedback_payload=_previous_feedback_payload,
            stable_previous_reference_answer_text=_stable_previous_reference_answer_text,
            previous_answer_loss_point_ids=_previous_answer_loss_point_ids,
            replayed_reference_loss_ids=_replayed_reference_loss_ids,
            reference_replay_match_terms=_reference_replay_match_terms,
            loss_points_for_ids=_loss_points_for_ids,
            candidate_answer_coverage_is_resolved=_candidate_answer_coverage_is_resolved,
            has_unresolved_non_replay_feedback_points=_has_unresolved_non_replay_feedback_points,
            historical_replay_score_floor=_historical_replay_score_floor,
            answer_covers_full_reference_answer=_answer_covers_full_reference_answer,
        ),
    )
    eligibility = eligibility_result.eligibility
    if eligibility is not None:
        replayed_result = deepcopy(result)
        replay_loss_ids = set(eligibility.loss_point_ids)
        removed_loss_points = _remove_replayed_loss_points(replayed_result, replay_loss_ids)
        replayed_result = apply_feedback_core_rules(replayed_result, context)
        _sync_reference_replay_payload_consistency(replayed_result, replay_loss_ids, eligibility.match_terms)
        if _has_reference_replay_payload_contradiction(replayed_result, replay_loss_ids, eligibility.match_terms):
            metadata["reference_answer_replay_skipped_reason"] = "post_replay_payload_inconsistent"
            if removed_loss_points:
                metadata["reference_answer_replay_removed_loss_point_count"] = len(removed_loss_points)
        else:
            final_score = _raise_score_result_floor(replayed_result, eligibility.score_floor)
            if final_score is not None and not _has_reference_replay_payload_contradiction(
                replayed_result,
                replay_loss_ids,
                eligibility.match_terms,
            ):
                metadata["reference_answer_replay_detected"] = True
                metadata["reference_answer_replay_loss_point_ids"] = sorted(eligibility.loss_point_ids)
                metadata["reference_answer_replay_score_floor"] = final_score
                if final_score != eligibility.score_floor:
                    metadata["reference_answer_replay_score_floor_candidate"] = eligibility.score_floor
                    metadata["reference_answer_replay_final_score"] = final_score
                metadata["reference_answer_replay_score_basis"] = "historical_score_plus_replayed_deductions"
                replayed_result["feedback_metadata"] = metadata
                _sync_feedback_cards_after_step4(replayed_result)
                return replayed_result
            metadata["reference_answer_replay_skipped_reason"] = (
                "score_floor_inconsistent" if final_score is None else "post_replay_payload_inconsistent"
            )
            if removed_loss_points:
                metadata["reference_answer_replay_removed_loss_point_count"] = len(removed_loss_points)
    else:
        metadata["reference_answer_replay_skipped_reason"] = eligibility_result.reason

    if _has_same_question_stability_basis(context):
        stable_score = _stable_score_from_loss_points(result.get("loss_points"))
        if stable_score is not None:
            _set_score_result_value(result, stable_score)
            metadata["same_answer_stability_applied"] = True
            metadata["same_answer_stability_basis"] = "loss_point_deduction_baseline"
            result["feedback_metadata"] = metadata
            _sync_feedback_cards_after_step4(result)
            return result

    result["feedback_metadata"] = metadata
    return result


def _has_same_question_stability_basis(context: dict[str, Any]) -> bool:
    answer_text = _clean(
        _context_value(context, "_step4_raw_answer_text") or _context_value(context, "answer_text"),
        max_chars=12000,
    )
    answer_key = semantic_text(answer_text)
    if not answer_key:
        return False
    for answer in _dict_items(_context_value(context, "same_question_answers")):
        if not _clean(answer.get("answer_id"), max_chars=120):
            continue
        previous_answer_text = _clean(answer.get("answer_text"), max_chars=12000)
        if not previous_answer_text or semantic_text(previous_answer_text) != answer_key:
            continue
        if _clean(answer.get("reference_answer_text"), max_chars=12000):
            return True
        if _dict_items(answer.get("reference_answer_sections")):
            return True
    return False


def _has_unresolved_non_replay_feedback_points(
    payload: dict[str, Any],
    replay_loss_ids: set[str],
    match_terms: tuple[str, ...],
) -> bool:
    for loss_point in _dict_items(payload.get("loss_points")):
        loss_id = _clean(loss_point.get("loss_point_id"), max_chars=120)
        if not loss_id or loss_id not in replay_loss_ids:
            return True
    for item in _list_items(payload.get("key_loss_points")):
        if not _text_matches_reference_replay_terms(item, match_terms):
            return True
    if not _candidate_answer_coverage_is_resolved(payload, match_terms):
        return True
    answer_change = _mapping(payload.get("answer_change_analysis")) or {}
    for field_name in (
        "repeated_loss_points",
        "repeated_loss_point_ids",
        "remaining_loss_points",
        "remaining_loss_point_ids",
        "regressed_points",
        "next_retry_focus",
    ):
        for item in _string_tuple(answer_change.get(field_name)):
            if not _text_matches_reference_replay_terms(item, match_terms):
                return True
    return False


def _candidate_answer_coverage_is_resolved(payload: dict[str, Any], match_terms: tuple[str, ...]) -> bool:
    answer_coverage = _mapping(payload.get("answer_coverage")) or {}
    for field_name in ("missing_points", "weak_points", "contradicted_points"):
        if _string_tuple(answer_coverage.get(field_name)):
            return False
    return True


def _context_value(context: dict[str, Any], field_name: str) -> Any:
    return context.get(field_name)
