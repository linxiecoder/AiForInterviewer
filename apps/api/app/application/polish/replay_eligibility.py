from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.application.polish.answer_equivalence import (
    answer_covers_reference_section,
    answer_strongly_matches_reference,
)
from app.application.polish.payload_helpers import (
    _clean,
    _dict_items,
    _mapping,
    _number,
    _stable_string_values,
)
from app.application.polish.question_source_normalization import _previous_feedback_payload

@dataclass(frozen=True, slots=True)
class ReferenceReplayEligibility:
    loss_point_ids: frozenset[str]
    score_floor: float
    match_terms: tuple[str, ...]
    reason: str

@dataclass(frozen=True, slots=True)
class ReplayEligibilityResult:
    eligibility: ReferenceReplayEligibility | None
    reason: str

@dataclass(frozen=True, slots=True)
class ReplayEligibilityAdapters:
    clean: Callable[..., str]
    context_value: Callable[[dict[str, Any], str], object]
    dict_items: Callable[[object], tuple[dict[str, Any], ...]]
    previous_feedback_payload: Callable[[dict[str, Any]], dict[str, Any] | None]
    stable_previous_reference_answer_text: Callable[[dict[str, Any]], str]
    previous_answer_loss_point_ids: Callable[[dict[str, Any]], set[str]]
    replayed_reference_loss_ids: Callable[[str, dict[str, Any], set[str]], set[str]]
    reference_replay_match_terms: Callable[[set[str], list[dict[str, Any]]], tuple[str, ...]]
    loss_points_for_ids: Callable[[dict[str, Any], set[str]], list[dict[str, Any]]]
    candidate_answer_coverage_is_resolved: Callable[[dict[str, Any], tuple[str, ...]], bool]
    has_unresolved_non_replay_feedback_points: Callable[[dict[str, Any], set[str], tuple[str, ...]], bool]
    historical_replay_score_floor: Callable[[dict[str, Any], set[str]], float | None]
    answer_covers_full_reference_answer: Callable[[str, str], bool]

def replay_eligibility(
    payload: dict[str, Any],
    context: dict[str, Any],
    *,
    adapters: ReplayEligibilityAdapters,
) -> ReplayEligibilityResult:
    answer_text = adapters.clean(
        adapters.context_value(context, "_step4_raw_answer_text") or adapters.context_value(context, "answer_text"),
        max_chars=12000,
    )
    if not answer_text:
        return ReplayEligibilityResult(eligibility=None, reason="missing_answer_text")
    skipped_reason = "no_historical_generated_feedback_payload"
    for answer in adapters.dict_items(adapters.context_value(context, "same_question_answers")):
        historical_payload = adapters.previous_feedback_payload(answer)
        if historical_payload is None:
            continue

        reference_answer_text = adapters.stable_previous_reference_answer_text(answer)
        skipped_reason = "reference_answer_not_equivalent"
        if not reference_answer_text or not adapters.answer_covers_full_reference_answer(
            answer_text,
            reference_answer_text,
        ):
            continue

        previous_loss_ids = adapters.previous_answer_loss_point_ids(answer)
        skipped_reason = "missing_historical_loss_points"
        if not previous_loss_ids:
            continue

        replayed_loss_ids = adapters.replayed_reference_loss_ids(answer_text, answer, previous_loss_ids)
        skipped_reason = "reference_loss_points_not_fully_replayed"
        if not replayed_loss_ids or not previous_loss_ids <= replayed_loss_ids:
            continue

        match_terms = adapters.reference_replay_match_terms(
            replayed_loss_ids,
            adapters.loss_points_for_ids(answer, replayed_loss_ids),
        )
        if not adapters.candidate_answer_coverage_is_resolved(payload, match_terms):
            skipped_reason = "unresolved_answer_coverage"
            continue
        if adapters.has_unresolved_non_replay_feedback_points(payload, replayed_loss_ids, match_terms):
            skipped_reason = "unresolved_non_replay_feedback_points"
            continue

        score_floor = adapters.historical_replay_score_floor(historical_payload, replayed_loss_ids)
        skipped_reason = "missing_historical_score_floor"
        if score_floor is None:
            continue
        reason = "reference_answer_equivalent_and_coverage_resolved"
        return ReplayEligibilityResult(
            eligibility=ReferenceReplayEligibility(
                loss_point_ids=frozenset(replayed_loss_ids),
                score_floor=score_floor,
                match_terms=match_terms,
                reason=reason,
            ),
            reason=reason,
        )
    return ReplayEligibilityResult(eligibility=None, reason=skipped_reason)

def _replayed_reference_loss_ids(
    answer_text: str,
    answer: dict[str, Any],
    previous_loss_ids: set[str],
) -> set[str]:
    replayed_loss_ids: set[str] = set()
    for section in _dict_items(answer.get("reference_answer_sections")):
        section_content = _clean(section.get("content"), max_chars=4000)
        if not section_content or not _answer_covers_reference_section(answer_text, section_content):
            continue
        for loss_id in _stable_string_values(
            section.get("addresses_loss_point_ids"),
            max_items=40,
            max_chars=120,
        ):
            if loss_id in previous_loss_ids:
                replayed_loss_ids.add(loss_id)
    return replayed_loss_ids

def _previous_answer_loss_point_ids(answer: dict[str, Any]) -> set[str]:
    loss_ids: set[str] = set()
    for loss_id in _stable_string_values(
        answer.get("loss_point_ids"),
        max_items=40,
        max_chars=120,
    ):
        loss_ids.add(loss_id)
    for loss_point in _dict_items(answer.get("loss_points")):
        loss_id = _clean(loss_point.get("loss_point_id"), max_chars=120)
        if loss_id:
            loss_ids.add(loss_id)
    return loss_ids

def _answer_covers_reference_section(answer_text: str, section_content: str) -> bool:
    return answer_covers_reference_section(answer_text, section_content)

def _answer_covers_full_reference_answer(answer_text: str, reference_answer_text: str) -> bool:
    return answer_strongly_matches_reference(answer_text, reference_answer_text)

def _reference_replay_match_terms(
    replay_loss_ids: set[str],
    removed_loss_points: list[dict[str, Any]],
) -> tuple[str, ...]:
    terms: list[str] = []
    for loss_id in sorted(replay_loss_ids):
        if loss_id:
            terms.append(loss_id)
    for loss_point in removed_loss_points:
        for field_name in ("reason", "description", "summary"):
            term = _clean(loss_point.get(field_name), max_chars=240)
            if term and term not in terms:
                terms.append(term)
    return tuple(terms)

def _loss_points_for_ids(answer: dict[str, Any], replay_loss_ids: set[str]) -> list[dict[str, Any]]:
    loss_points: list[dict[str, Any]] = []
    for loss_point in _dict_items(answer.get("loss_points")):
        loss_id = _clean(loss_point.get("loss_point_id"), max_chars=120)
        if loss_id in replay_loss_ids:
            loss_points.append(dict(loss_point))
    historical_payload = _previous_feedback_payload(answer)
    if historical_payload is None:
        return loss_points
    for loss_point in _dict_items(historical_payload.get("loss_points")):
        loss_id = _clean(loss_point.get("loss_point_id"), max_chars=120)
        if loss_id in replay_loss_ids and loss_point not in loss_points:
            loss_points.append(dict(loss_point))
    return loss_points

def _historical_replay_score_floor(
    historical_payload: dict[str, Any],
    replay_loss_ids: set[str],
) -> float | None:
    score_result = _mapping(historical_payload.get("score_result"))
    if score_result is None:
        return None
    historical_score = _number(score_result.get("score_value"))
    if historical_score is None:
        return None
    recovered_points = 0.0
    for loss_point in _dict_items(historical_payload.get("loss_points")):
        loss_id = _clean(loss_point.get("loss_point_id"), max_chars=120)
        if loss_id not in replay_loss_ids:
            continue
        deduction = _number(loss_point.get("deduction") or loss_point.get("deducted_points"))
        if deduction is not None and deduction > 0:
            recovered_points += deduction
    if recovered_points <= 0:
        return None
    return round(max(historical_score, min(100.0, historical_score + recovered_points)), 2)
