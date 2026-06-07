from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.domain.polish.policies.answer_change_policy import (
    AnswerChangeInput,
    AnswerChangePolicy,
    PreviousAnswerSnapshot,
)
from app.domain.polish.policies.answer_coverage_policy import AnswerCoverageInput, AnswerCoveragePolicy
from app.domain.polish.policies.asset_consistency_policy import (
    AssetConsistencyInput,
    AssetConsistencyPolicy,
    CanonicalAssetItem,
)
from app.domain.polish.policies.scoring_policy import ScoringInput, ScoringLossPoint, ScoringPolicy
from app.domain.polish.policies.feedback_next_action_policy import (
    FeedbackNextActionInput,
    FeedbackNextActionPolicy,
)


FEEDBACK_CORE_RULES_VERSION = "polish_feedback_core_rules.phase4.v1"

ASSET_CONSISTENCY_STATUSES = (
    "consistent",
    "conflict",
    "insufficient_asset_context",
    "not_applicable",
)
ASSET_CONFLICT_TYPES = (
    "fact_conflict",
    "responsibility_conflict",
    "metric_conflict",
    "scope_conflict",
    "timeline_conflict",
    "technology_stack_conflict",
    "unsupported_claim",
)
ANSWER_CHANGE_TRENDS = ("improved", "regressed", "mixed", "unchanged", "first_attempt")
FEEDBACK_CARD_TYPES = (
    "asset_consistency",
    "overall",
    "answer_coverage",
    "answer_change",
    "loss_points",
    "reference_answer",
    "next_actions",
    "asset_update_candidates",
)

_PHASE4_FIELDS = (
    "asset_consistency_check",
    "answer_coverage",
    "answer_change_analysis",
    "feedback_cards",
)
_REUSABLE_CANONICAL_ASSET_STATUSES = {"asset_confirmed"}


def apply_feedback_core_rules(payload: dict[str, Any], context: object) -> dict[str, Any]:
    """Apply deterministic Phase 4 feedback rules over an LLM candidate payload."""

    result = deepcopy(payload)
    canonical_assets = _canonical_project_assets(context)
    asset_items = _asset_items(canonical_assets)
    answer_text = _ctx_text(context, "answer_text", max_chars=12000)
    original_missing = _missing_phase4_fields(payload)

    _normalize_asset_update_candidates(result)
    _normalize_loss_points(result)
    _apply_scoring_policy(result)
    _normalize_reference_answer(result)
    _normalize_same_question_effect(result)

    asset_check = _build_asset_consistency_check(
        answer_text=answer_text,
        asset_items=asset_items,
        canonical_assets_available=bool(canonical_assets.get("available")) and bool(asset_items),
    )
    result["asset_consistency_check"] = asset_check

    answer_coverage = _build_answer_coverage(result, context, answer_text=answer_text, asset_check=asset_check)
    result["answer_coverage"] = answer_coverage
    answer_change = _build_answer_change_analysis(result, context, answer_coverage=answer_coverage)
    result["answer_change_analysis"] = answer_change
    result["next_recommended_actions"] = _next_recommended_actions(
        result.get("next_recommended_actions"),
        asset_check=asset_check,
        answer_coverage=answer_coverage,
        answer_change=answer_change,
        candidates=result.get("project_asset_update_candidates"),
        low_confidence_flags=result.get("low_confidence_flags"),
        generation_status=_clean(result.get("status"), max_chars=80) or "generated",
    )
    result["feedback_cards"] = _build_feedback_cards(
        result,
        asset_check=asset_check,
        answer_coverage=answer_coverage,
        answer_change=answer_change,
    )
    result["low_confidence_flags"] = _phase4_low_confidence_flags(result.get("low_confidence_flags"), asset_check)
    result["feedback_metadata"] = _phase4_feedback_metadata(
        result.get("feedback_metadata"),
        missing_phase4_fields=original_missing,
        canonical_assets_available=bool(asset_items),
    )
    return result


def _missing_phase4_fields(payload: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for field_name in _PHASE4_FIELDS:
        value = payload.get(field_name)
        if value in (None, {}, []):
            missing.append(field_name)
    return missing


def _phase4_feedback_metadata(
    value: object,
    *,
    missing_phase4_fields: list[str],
    canonical_assets_available: bool,
) -> dict[str, Any]:
    metadata = dict(value) if isinstance(value, dict) else {}
    warnings = _string_list(metadata.get("phase4_validation_warnings"), max_items=20, max_item_chars=160)
    for field_name in missing_phase4_fields:
        if field_name == "asset_consistency_check" and canonical_assets_available:
            warning = "asset_consistency_check_missing_from_llm_policy_generated"
        else:
            warning = f"{field_name}_missing_from_llm_policy_generated"
        if warning not in warnings:
            warnings.append(warning)
    metadata["feedback_core_rules_version"] = FEEDBACK_CORE_RULES_VERSION
    metadata["phase4_fields_generated"] = True
    if warnings:
        metadata["phase4_validation_warnings"] = warnings
    return metadata


def _phase4_low_confidence_flags(value: object, asset_check: dict[str, Any]) -> list[str]:
    return _string_list(value, max_items=20, max_item_chars=160)


def _build_asset_consistency_check(
    *,
    answer_text: str,
    asset_items: list[dict[str, Any]],
    canonical_assets_available: bool,
) -> dict[str, Any]:
    decision = AssetConsistencyPolicy.evaluate(
        AssetConsistencyInput(
            answer_text=answer_text,
            asset_items=tuple(_canonical_asset_item(item) for item in asset_items),
            canonical_assets_available=canonical_assets_available,
        )
    )
    return decision.to_legacy_dict()


def _canonical_asset_item(item: dict[str, Any]) -> CanonicalAssetItem:
    return CanonicalAssetItem(
        asset_id=_clean(item.get("asset_id"), max_chars=120),
        title=_clean(item.get("title"), max_chars=240),
        summary=_clean(item.get("summary"), max_chars=800),
        content_excerpt=_clean(item.get("content_excerpt"), max_chars=800),
    )


def _build_answer_coverage(
    payload: dict[str, Any],
    context: object,
    *,
    answer_text: str,
    asset_check: dict[str, Any],
) -> dict[str, Any]:
    decision = AnswerCoveragePolicy.evaluate(
        AnswerCoverageInput(
            answer_text=answer_text,
            expected_points=tuple(_expected_points(context)),
            loss_point_reasons=tuple(
                reason
                for loss_point in _dict_list(payload.get("loss_points"))
                if (reason := _clean(loss_point.get("reason"), max_chars=240))
            ),
            contradicted_asset_claims=tuple(
                claim
                for conflict in _dict_list(asset_check.get("conflicts"))
                if (claim := _clean(conflict.get("asset_claim"), max_chars=240))
            ),
        )
    )
    return decision.to_legacy_dict()


def _build_answer_change_analysis(
    payload: dict[str, Any],
    context: object,
    *,
    answer_coverage: dict[str, Any],
) -> dict[str, Any]:
    previous_answers = _dict_list(_ctx(context, "same_question_answers"))
    effect = payload.get("same_question_effect") if isinstance(payload.get("same_question_effect"), dict) else {}
    score_delta = effect.get("score_delta")
    decision = AnswerChangePolicy.evaluate(
        AnswerChangeInput(
            current_covered_points=tuple(
                _string_list(answer_coverage.get("covered_points"), max_items=40, max_item_chars=240)
            ),
            current_loss_point_ids=tuple(_loss_point_ids(payload.get("loss_points"))),
            current_score_value=_score_value(payload.get("score_result")),
            previous_answers=tuple(_previous_answer_snapshot(answer) for answer in previous_answers),
            llm_regressed_points=tuple(
                _string_list(effect.get("regressed_points"), max_items=20, max_item_chars=240)
            ),
            llm_repeated_loss_point_ids=tuple(
                _string_list(effect.get("repeated_loss_point_ids"), max_items=20, max_item_chars=120)
            ),
            llm_score_delta=(
                float(score_delta)
                if isinstance(score_delta, (int, float)) and not isinstance(score_delta, bool)
                else None
            ),
        )
    )
    return decision.to_legacy_dict()


def _previous_answer_snapshot(answer: dict[str, Any]) -> PreviousAnswerSnapshot:
    coverage = answer.get("answer_coverage") if isinstance(answer.get("answer_coverage"), dict) else {}
    covered_points = [
        *_string_list(coverage.get("covered_points"), max_items=20, max_item_chars=240),
        *_string_list(answer.get("covered_points"), max_items=20, max_item_chars=240),
    ]
    loss_point_ids = [*_string_list(answer.get("loss_point_ids"), max_items=40, max_item_chars=120)]
    for loss_point in _dict_list(answer.get("loss_points")):
        loss_id = _clean(loss_point.get("loss_point_id"), max_chars=120)
        if loss_id:
            loss_point_ids.append(loss_id)
    score_value = _score_value(answer.get("score_result"))
    if score_value is None:
        score_value = _score_value(answer)
    return PreviousAnswerSnapshot(
        answer_id=_clean(answer.get("answer_id"), max_chars=120),
        covered_points=tuple(_unique(covered_points)),
        loss_point_ids=tuple(_unique(loss_point_ids)),
        score_value=score_value,
    )


def _next_recommended_actions(
    value: object,
    *,
    asset_check: dict[str, Any],
    answer_coverage: dict[str, Any],
    answer_change: dict[str, Any],
    candidates: object,
    low_confidence_flags: object = (),
    generation_status: str | None = "generated",
    validation_failed: bool = False,
) -> list[str]:
    decision = FeedbackNextActionPolicy.decide(
        FeedbackNextActionInput(
            existing_actions=tuple(_string_list(value, max_items=20, max_item_chars=160)),
            generation_status=generation_status,
            validation_failed=validation_failed,
            asset_status=_clean(asset_check.get("status"), max_chars=80),
            asset_conflict_count=len(_dict_list(asset_check.get("conflicts"))),
            unsupported_claim_count=len(_dict_list(asset_check.get("unsupported_claims"))),
            asset_user_clarification_required=bool(asset_check.get("user_clarification_required")),
            missing_points=tuple(_string_list(answer_coverage.get("missing_points"), max_items=40, max_item_chars=240)),
            weak_points=tuple(_string_list(answer_coverage.get("weak_points"), max_items=40, max_item_chars=240)),
            contradicted_points=tuple(
                _string_list(answer_coverage.get("contradicted_points"), max_items=40, max_item_chars=240)
            ),
            regressed_points=tuple(
                _string_list(answer_change.get("regressed_points"), max_items=40, max_item_chars=240)
            ),
            has_asset_update_candidates=bool(_dict_list(candidates)),
            all_asset_update_candidates_require_confirmation=all(
                bool(candidate.get("user_confirmation_required"))
                for candidate in _dict_list(candidates)
            ),
            low_confidence_flags=tuple(_string_list(low_confidence_flags, max_items=20, max_item_chars=160)),
        )
    )
    return decision.to_legacy_actions()


def _build_feedback_cards(
    payload: dict[str, Any],
    *,
    asset_check: dict[str, Any],
    answer_coverage: dict[str, Any],
    answer_change: dict[str, Any],
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = [
        {
            "card_type": "asset_consistency",
            "status": asset_check.get("status"),
            "payload": asset_check,
        },
        {
            "card_type": "overall",
            "status": payload.get("status"),
            "payload": {
                "feedback_text": payload.get("feedback_text"),
                "answer_summary": payload.get("answer_summary"),
                "score_result": payload.get("score_result"),
            },
        },
        {
            "card_type": "answer_coverage",
            "status": "available",
            "payload": answer_coverage,
        },
    ]
    if answer_change.get("has_prior_attempts") or answer_change.get("regressed_points"):
        cards.append(
            {
                "card_type": "answer_change",
                "status": answer_change.get("trend"),
                "payload": answer_change,
            }
        )
    if _dict_list(payload.get("loss_points")):
        cards.append({"card_type": "loss_points", "status": "available", "payload": payload.get("loss_points")})
    if isinstance(payload.get("reference_answer"), dict):
        cards.append(
            {"card_type": "reference_answer", "status": "available", "payload": payload.get("reference_answer")}
        )
    cards.append(
        {
            "card_type": "next_actions",
            "status": "available",
            "payload": {"next_recommended_actions": payload.get("next_recommended_actions") or []},
        }
    )
    candidates = _dict_list(payload.get("project_asset_update_candidates"))
    if candidates:
        cards.append({"card_type": "asset_update_candidates", "status": "candidate", "payload": candidates})
    return cards


def _normalize_asset_update_candidates(payload: dict[str, Any]) -> None:
    candidates = payload.get("project_asset_update_candidates")
    if not isinstance(candidates, list):
        return
    normalized: list[Any] = []
    for item in candidates:
        if not isinstance(item, dict):
            normalized.append(item)
            continue
        candidate = dict(item)
        if candidate.get("candidate_type") == "project_asset_update_candidate":
            candidate["user_confirmation_required"] = True
        normalized.append(candidate)
    payload["project_asset_update_candidates"] = normalized


def _normalize_loss_points(payload: dict[str, Any]) -> None:
    loss_points = payload.get("loss_points")
    if not isinstance(loss_points, list):
        return
    normalized: list[Any] = []
    for item in loss_points:
        if not isinstance(item, dict):
            normalized.append(item)
            continue
        loss_point = dict(item)
        if not _clean(loss_point.get("loss_point_id"), max_chars=120):
            alias = _clean(loss_point.get("id") or loss_point.get("loss_id"), max_chars=120)
            if alias:
                loss_point["loss_point_id"] = alias
        if not _clean(loss_point.get("reason"), max_chars=1000):
            description = _clean(loss_point.get("description"), max_chars=1000)
            if description:
                loss_point["reason"] = description
        normalized.append(loss_point)
    payload["loss_points"] = normalized


def _apply_scoring_policy(payload: dict[str, Any]) -> None:
    raw_loss_points = payload.get("loss_points")
    normalized_loss_points = raw_loss_points if isinstance(raw_loss_points, list) else []

    decision = ScoringPolicy.evaluate(
        ScoringInput(
            loss_points=tuple(
                ScoringLossPoint(
                    loss_point_id=_clean(loss_point.get("loss_point_id"), max_chars=120),
                    severity=_clean(loss_point.get("severity"), max_chars=40),
                    reason=_clean(loss_point.get("reason"), max_chars=1000),
                )
                for loss_point in _dict_list(payload.get("loss_points"))
            )
        )
    )
    payload["score_result"] = {
        "score_type": "polish_answer",
        "score_value": decision.score_value,
        "scoring_basis": "score_result computed from loss_point severities on server; LLM score fields are not trusted",
    }

    scored_loss_points: list[dict[str, Any]] = []
    scored_iter = iter(decision.scored_loss_points)
    for loss_point in normalized_loss_points:
        if not isinstance(loss_point, dict):
            scored_loss_points.append(loss_point)
            continue
        scored_loss_point = next(scored_iter, None)
        normalized = dict(loss_point)
        if scored_loss_point is not None:
            normalized["deduction"] = scored_loss_point.deduction
            normalized["severity"] = scored_loss_point.severity
            normalized.pop("deducted_points", None)
        else:
            normalized["deduction"] = 0.0
        scored_loss_points.append(normalized)
    payload["loss_points"] = scored_loss_points

    warnings = _string_list(payload.get("low_confidence_flags"), max_items=20, max_item_chars=160)
    for warning in decision.warnings:
        warning_text = _clean(warning, max_chars=160)
        if warning_text and warning_text not in warnings:
            warnings.append(warning_text)
    payload["low_confidence_flags"] = warnings


def _normalize_reference_answer(payload: dict[str, Any]) -> None:
    reference_answer = payload.get("reference_answer")
    if not isinstance(reference_answer, dict):
        return
    sections = reference_answer.get("sections")
    if not isinstance(sections, list):
        return
    normalized_sections: list[Any] = []
    for item in sections:
        if not isinstance(item, dict):
            normalized_sections.append(item)
            continue
        section = dict(item)
        if not _clean(section.get("section_id"), max_chars=120):
            alias = _clean(section.get("id"), max_chars=120)
            if alias:
                section["section_id"] = alias
        normalized_sections.append(section)
    normalized_reference_answer = dict(reference_answer)
    normalized_reference_answer["sections"] = normalized_sections
    payload["reference_answer"] = normalized_reference_answer


def _normalize_same_question_effect(payload: dict[str, Any]) -> None:
    effect = payload.get("same_question_effect")
    if isinstance(effect, dict):
        normalized_effect = dict(effect)
        for field_name in ("improved_points", "repeated_loss_point_ids", "regressed_points", "next_retry_focus"):
            if not isinstance(normalized_effect.get(field_name), list):
                normalized_effect[field_name] = []
        payload["same_question_effect"] = normalized_effect
        return
    trend = _clean(effect, max_chars=80)
    if trend in ANSWER_CHANGE_TRENDS:
        payload["same_question_effect"] = {
            "trend": trend,
            "improved_points": [],
            "repeated_loss_point_ids": [],
            "regressed_points": [],
            "next_retry_focus": [],
            "score_delta": None,
        }


def _expected_points(context: object) -> list[str]:
    question_metadata = _ctx_dict(context, "question_metadata")
    progress_node = _ctx_dict(context, "progress_node_snapshot")
    canonical_assets = _canonical_project_assets(context)
    job_snapshot = _ctx_dict(context, "job_snapshot")
    points: list[str] = []
    points.extend(_string_list(question_metadata.get("expected_answer_dimensions"), max_items=12, max_item_chars=240))
    points.append(_clean(progress_node.get("expected_capability"), max_chars=240))
    points.extend(_string_list(progress_node.get("missing_points"), max_items=8, max_item_chars=160))
    for item in _asset_items(canonical_assets):
        points.append(_clean(item.get("summary") or item.get("content_excerpt") or item.get("title"), max_chars=240))
    points.extend(_string_list(job_snapshot.get("requirements"), max_items=8, max_item_chars=180))
    return _unique([point for point in points if point])[:12]


def _loss_point_ids(value: object) -> list[str]:
    return _unique(
        [
            loss_id
            for loss_point in _dict_list(value)
            if (loss_id := _clean(loss_point.get("loss_point_id"), max_chars=120))
        ]
    )


def _score_value(value: object) -> float | None:
    if not isinstance(value, dict):
        return None
    score_value = value.get("score_value")
    if isinstance(score_value, (int, float)) and not isinstance(score_value, bool):
        return float(score_value)
    return None


def _canonical_project_assets(context: object) -> dict[str, Any]:
    value = _ctx(context, "canonical_project_assets")
    return value if isinstance(value, dict) else {}


def _asset_items(canonical_assets: dict[str, Any]) -> list[dict[str, Any]]:
    items = canonical_assets.get("items")
    if not isinstance(items, list):
        return []
    return [
        item
        for item in items
        if isinstance(item, dict) and _clean(item.get("status")) in _REUSABLE_CANONICAL_ASSET_STATUSES
    ]


def _has_unresolved_answer_points(answer_coverage: dict[str, Any]) -> bool:
    return any(
        bool(answer_coverage.get(field_name))
        for field_name in ("missing_points", "weak_points", "contradicted_points")
    )


def _ctx(context: object, field_name: str) -> object:
    if isinstance(context, dict):
        return context.get(field_name)
    return getattr(context, field_name, None)


def _ctx_text(context: object, field_name: str, *, max_chars: int = 1000) -> str:
    return _clean(_ctx(context, field_name), max_chars=max_chars)


def _ctx_dict(context: object, field_name: str) -> dict[str, Any]:
    value = _ctx(context, field_name)
    return value if isinstance(value, dict) else {}


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


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


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def _clean(value: object, *, max_chars: int = 240) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text
