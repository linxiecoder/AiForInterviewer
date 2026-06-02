from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from app.application.polish.context.expected_points import ExpectedPointsBuilder


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
_CLAIM_MARKERS = (
    "我负责",
    "我主导",
    "我参与",
    "我们使用",
    "我们采用",
    "项目使用",
    "项目采用",
    "负责",
    "主导",
    "built",
    "owned",
    "led",
    "used",
    "implemented",
)
_RESPONSIBILITY_LOW_MARKERS = ("参与", "协助", "support", "contributed", "helped")
_RESPONSIBILITY_HIGH_MARKERS = ("主导", "独立负责", "owner", "owned", "led", "lead")
_TECH_GROUPS: dict[str, tuple[str, ...]] = {
    "framework": ("fastapi", "django", "flask", "spring", "express", "nestjs"),
    "database": ("postgresql", "postgres", "mysql", "mongodb", "mongo", "tidb", "sqlite"),
    "message_queue": ("kafka", "rabbitmq", "rocketmq", "pulsar", "sqs"),
    "cache": ("redis", "memcached"),
    "search": ("elasticsearch", "opensearch", "solr", "bm25"),
    "language": ("python", "java", "go", "golang", "typescript", "node"),
}
_METRIC_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\s*(?:%|ms|s|qps|tps|w|k|m|万|千|秒|毫秒|天|月|年|人)\b", re.IGNORECASE)
_YEAR_PATTERN = re.compile(r"\b20\d{2}\b|20\d{2}\s*年")


def apply_feedback_core_rules(payload: dict[str, Any], context: object) -> dict[str, Any]:
    """Apply deterministic Phase 4 feedback rules over an LLM candidate payload."""

    result = deepcopy(payload)
    canonical_assets = _canonical_project_assets(context)
    asset_items = _asset_items(canonical_assets)
    answer_text = _ctx_text(context, "answer_text", max_chars=12000)
    original_missing = _missing_phase4_fields(payload)

    _normalize_asset_update_candidates(result)

    asset_check = _build_asset_consistency_check(
        answer_text=answer_text,
        asset_items=asset_items,
        canonical_assets_available=bool(canonical_assets.get("available")) and bool(asset_items),
    )
    result["asset_consistency_check"] = asset_check
    if asset_check["status"] == "conflict" or asset_items:
        result["project_asset_consistency_check"] = _legacy_project_asset_consistency(asset_check)
    else:
        result["project_asset_consistency_check"] = {"status": "not_applicable"}

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
    if not canonical_assets_available:
        return {
            "status": "insufficient_asset_context",
            "checked_asset_refs": [],
            "conflicts": [],
            "unsupported_claims": [],
            "user_clarification_required": False,
        }

    conflicts: list[dict[str, Any]] = []
    unsupported_claims: list[dict[str, Any]] = []
    asset_text = " ".join(_asset_text(item) for item in asset_items)
    answer_tokens_by_group = _tech_tokens_by_group(answer_text)
    asset_tokens_by_group = _tech_tokens_by_group(asset_text)

    for group_name, answer_tokens in answer_tokens_by_group.items():
        asset_tokens = asset_tokens_by_group.get(group_name, set())
        unsupported_tokens = sorted(token for token in answer_tokens if token not in asset_tokens)
        if not unsupported_tokens:
            continue
        if asset_tokens:
            conflicts.append(
                _conflict(
                    "technology_stack_conflict",
                    current_answer_claim=", ".join(unsupported_tokens),
                    asset_claim=", ".join(sorted(asset_tokens)),
                    asset_item=asset_items[0],
                    severity="major",
                )
            )
        elif _looks_like_project_claim(answer_text):
            for token in unsupported_tokens[:3]:
                unsupported_claims.append(
                    {
                        "claim_type": "technology_stack",
                        "current_answer_claim": token,
                        "reason": "not_supported_by_canonical_project_assets",
                        "asset_refs_checked": _checked_asset_refs(asset_items),
                    }
                )

    conflicts.extend(_metric_conflicts(answer_text, asset_items))
    conflicts.extend(_timeline_conflicts(answer_text, asset_items))
    conflicts.extend(_responsibility_conflicts(answer_text, asset_items))
    unsupported_claims = _dedupe_claims(unsupported_claims)
    for claim in unsupported_claims:
        conflicts.append(
            _conflict(
                "unsupported_claim",
                current_answer_claim=_clean(claim.get("current_answer_claim"), max_chars=240),
                asset_claim="No supporting canonical project asset fact found.",
                asset_item=asset_items[0],
                severity="major",
            )
        )

    status = "conflict" if conflicts or unsupported_claims else "consistent"
    return {
        "status": status,
        "checked_asset_refs": _checked_asset_refs(asset_items),
        "conflicts": _dedupe_conflicts(conflicts),
        "unsupported_claims": unsupported_claims,
        "user_clarification_required": status == "conflict",
    }


def _legacy_project_asset_consistency(asset_check: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": asset_check.get("status"),
        "checked_asset_refs": list(asset_check.get("checked_asset_refs") or []),
        "conflicts": list(asset_check.get("conflicts") or []),
        "unsupported_claims": list(asset_check.get("unsupported_claims") or []),
        "user_clarification_required": bool(asset_check.get("user_clarification_required")),
    }


def _build_answer_coverage(
    payload: dict[str, Any],
    context: object,
    *,
    answer_text: str,
    asset_check: dict[str, Any],
) -> dict[str, Any]:
    expected_points = _expected_points(context)
    covered_points: list[str] = []
    missing_points: list[str] = []
    weak_points: list[str] = []
    for point in expected_points:
        if _point_covered(point, answer_text):
            covered_points.append(point)
        elif _point_weakly_covered(point, answer_text):
            weak_points.append(point)
            missing_points.append(point)
        else:
            missing_points.append(point)

    for loss_point in _dict_list(payload.get("loss_points")):
        reason = _clean(loss_point.get("reason"), max_chars=240)
        if reason and reason not in weak_points:
            weak_points.append(reason)

    contradicted_points = [
        _clean(conflict.get("asset_claim"), max_chars=240)
        for conflict in _dict_list(asset_check.get("conflicts"))
        if _clean(conflict.get("asset_claim"), max_chars=240)
    ]
    return {
        "expected_points": expected_points,
        "covered_points": _unique(covered_points),
        "missing_points": _unique(missing_points),
        "weak_points": _unique(weak_points),
        "contradicted_points": _unique(contradicted_points),
    }


def _build_answer_change_analysis(
    payload: dict[str, Any],
    context: object,
    *,
    answer_coverage: dict[str, Any],
) -> dict[str, Any]:
    previous_answers = _dict_list(_ctx(context, "same_question_answers"))
    previous_refs = [_clean(item.get("answer_id"), max_chars=120) for item in previous_answers]
    previous_refs = [ref for ref in previous_refs if ref]
    if not previous_answers:
        return {
            "has_prior_attempts": False,
            "previous_answer_refs": [],
            "retained_points": [],
            "newly_added_points": list(answer_coverage.get("covered_points") or []),
            "regressed_points": [],
            "repeated_loss_points": [],
            "fixed_loss_points": [],
            "score_delta": None,
            "trend": "first_attempt",
        }

    prior_covered = _prior_covered_points(previous_answers)
    current_covered = _string_list(answer_coverage.get("covered_points"), max_items=40, max_item_chars=240)
    retained_points = [point for point in prior_covered if _contains_similar_point(current_covered, point)]
    regressed_points = [point for point in prior_covered if not _contains_similar_point(current_covered, point)]
    newly_added_points = [point for point in current_covered if not _contains_similar_point(prior_covered, point)]

    current_loss_ids = _loss_point_ids(payload.get("loss_points"))
    previous_loss_ids = _prior_loss_point_ids(previous_answers)
    repeated_loss_points = [loss_id for loss_id in previous_loss_ids if loss_id in current_loss_ids]
    fixed_loss_points = [loss_id for loss_id in previous_loss_ids if loss_id not in current_loss_ids]

    llm_effect = payload.get("same_question_effect") if isinstance(payload.get("same_question_effect"), dict) else {}
    regressed_points = _unique(
        [
            *regressed_points,
            *_string_list(llm_effect.get("regressed_points"), max_items=20, max_item_chars=240),
        ]
    )
    repeated_loss_points = _unique(
        [
            *repeated_loss_points,
            *_string_list(llm_effect.get("repeated_loss_point_ids"), max_items=20, max_item_chars=120),
        ]
    )
    score_delta = _score_delta(payload, previous_answers)
    trend = _trend(
        regressed_points=regressed_points,
        fixed_loss_points=fixed_loss_points,
        newly_added_points=newly_added_points,
        score_delta=score_delta,
    )
    return {
        "has_prior_attempts": True,
        "previous_answer_refs": previous_refs,
        "retained_points": _unique(retained_points),
        "newly_added_points": _unique(newly_added_points),
        "regressed_points": _unique(regressed_points),
        "repeated_loss_points": _unique(repeated_loss_points),
        "fixed_loss_points": _unique(fixed_loss_points),
        "score_delta": score_delta,
        "trend": trend,
    }


def _next_recommended_actions(
    value: object,
    *,
    asset_check: dict[str, Any],
    answer_coverage: dict[str, Any],
    answer_change: dict[str, Any],
    candidates: object,
) -> list[str]:
    existing = _string_list(value, max_items=20, max_item_chars=160)
    if asset_check.get("status") == "conflict":
        return _unique(
            [
                "clarify_asset_conflict",
                "revise_current_answer",
                *[action for action in existing if action != "generate_next_question"],
            ]
        )
    non_terminal_actions = [action for action in existing if action != "generate_next_question"]
    if answer_change.get("regressed_points"):
        actions = _unique(["retry_same_question_preserve_regressed_points", *non_terminal_actions])
    elif _has_unresolved_answer_points(answer_coverage):
        actions = _unique(["continue_same_question", *non_terminal_actions])
    else:
        actions = existing
    if _dict_list(candidates) and "confirm_asset_update_candidate" not in actions:
        actions.append("confirm_asset_update_candidate")
    return actions


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


def _expected_points(context: object) -> list[str]:
    return ExpectedPointsBuilder().build(context)


def _prior_covered_points(previous_answers: list[dict[str, Any]]) -> list[str]:
    points: list[str] = []
    for answer in previous_answers:
        coverage = answer.get("answer_coverage") if isinstance(answer.get("answer_coverage"), dict) else {}
        points.extend(_string_list(coverage.get("covered_points"), max_items=20, max_item_chars=240))
        points.extend(_string_list(answer.get("covered_points"), max_items=20, max_item_chars=240))
    return _unique(points)


def _prior_loss_point_ids(previous_answers: list[dict[str, Any]]) -> list[str]:
    ids: list[str] = []
    for answer in previous_answers:
        ids.extend(_string_list(answer.get("loss_point_ids"), max_items=40, max_item_chars=120))
        for loss_point in _dict_list(answer.get("loss_points")):
            loss_id = _clean(loss_point.get("loss_point_id"), max_chars=120)
            if loss_id:
                ids.append(loss_id)
    return _unique(ids)


def _loss_point_ids(value: object) -> list[str]:
    return _unique(
        [
            loss_id
            for loss_point in _dict_list(value)
            if (loss_id := _clean(loss_point.get("loss_point_id"), max_chars=120))
        ]
    )


def _score_delta(payload: dict[str, Any], previous_answers: list[dict[str, Any]]) -> float | None:
    current_score = _score_value(payload.get("score_result"))
    previous_scores = [_score_value(answer.get("score_result")) for answer in previous_answers]
    previous_scores.extend(_score_value(answer) for answer in previous_answers)
    previous_scores = [score for score in previous_scores if score is not None]
    if current_score is None or not previous_scores:
        effect = payload.get("same_question_effect") if isinstance(payload.get("same_question_effect"), dict) else {}
        score_delta = effect.get("score_delta")
        return float(score_delta) if isinstance(score_delta, (int, float)) and not isinstance(score_delta, bool) else None
    return round(current_score - previous_scores[-1], 2)


def _score_value(value: object) -> float | None:
    if not isinstance(value, dict):
        return None
    score_value = value.get("score_value")
    if isinstance(score_value, (int, float)) and not isinstance(score_value, bool):
        return float(score_value)
    return None


def _trend(
    *,
    regressed_points: list[str],
    fixed_loss_points: list[str],
    newly_added_points: list[str],
    score_delta: float | None,
) -> str:
    improved_signal = bool(fixed_loss_points or newly_added_points) or (score_delta is not None and score_delta > 0)
    regressed_signal = bool(regressed_points) or (score_delta is not None and score_delta < 0)
    if improved_signal and regressed_signal:
        return "mixed"
    if regressed_signal:
        return "regressed"
    if improved_signal:
        return "improved"
    return "unchanged"


def _metric_conflicts(answer_text: str, asset_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    answer_metrics = set(_METRIC_PATTERN.findall(answer_text))
    if not answer_metrics:
        return []
    conflicts: list[dict[str, Any]] = []
    for item in asset_items:
        asset_metrics = set(_METRIC_PATTERN.findall(_asset_text(item)))
        if asset_metrics and answer_metrics != asset_metrics:
            conflicts.append(
                _conflict(
                    "metric_conflict",
                    current_answer_claim=", ".join(sorted(answer_metrics)),
                    asset_claim=", ".join(sorted(asset_metrics)),
                    asset_item=item,
                    severity="major",
                )
            )
    return conflicts[:3]


def _timeline_conflicts(answer_text: str, asset_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    answer_years = set(_YEAR_PATTERN.findall(answer_text))
    if not answer_years:
        return []
    conflicts: list[dict[str, Any]] = []
    for item in asset_items:
        asset_years = set(_YEAR_PATTERN.findall(_asset_text(item)))
        if asset_years and answer_years != asset_years:
            conflicts.append(
                _conflict(
                    "timeline_conflict",
                    current_answer_claim=", ".join(sorted(answer_years)),
                    asset_claim=", ".join(sorted(asset_years)),
                    asset_item=item,
                    severity="major",
                )
            )
    return conflicts[:3]


def _responsibility_conflicts(answer_text: str, asset_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    answer_high = _contains_any(answer_text, _RESPONSIBILITY_HIGH_MARKERS)
    if not answer_high:
        return []
    conflicts: list[dict[str, Any]] = []
    for item in asset_items:
        asset_text = _asset_text(item)
        if _contains_any(asset_text, _RESPONSIBILITY_LOW_MARKERS):
            conflicts.append(
                _conflict(
                    "responsibility_conflict",
                    current_answer_claim="owned_or_led",
                    asset_claim="participated_or_supported",
                    asset_item=item,
                    severity="major",
                )
            )
    return conflicts[:3]


def _conflict(
    conflict_type: str,
    *,
    current_answer_claim: str,
    asset_claim: str,
    asset_item: dict[str, Any],
    severity: str,
) -> dict[str, Any]:
    asset_id = _clean(asset_item.get("asset_id"), max_chars=120)
    return {
        "conflict_type": conflict_type,
        "current_answer_claim": _clean(current_answer_claim, max_chars=400),
        "asset_claim": _clean(asset_claim, max_chars=400),
        "severity": severity,
        "asset_ref": {"resource_type": "asset", "resource_id": asset_id} if asset_id else None,
        "clarification_question": "Clarify the project fact against canonical assets before continuing.",
    }


def _dedupe_conflicts(conflicts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    result: list[dict[str, Any]] = []
    for conflict in conflicts:
        key = (
            _clean(conflict.get("conflict_type"), max_chars=80),
            _clean(conflict.get("current_answer_claim"), max_chars=120),
            _clean(conflict.get("asset_claim"), max_chars=120),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(conflict)
    return result[:8]


def _dedupe_claims(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for claim in claims:
        key = _clean(claim.get("current_answer_claim"), max_chars=160).casefold()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(claim)
    return result[:8]


def _tech_tokens_by_group(text: str) -> dict[str, set[str]]:
    lowered = text.casefold()
    result: dict[str, set[str]] = {}
    for group_name, terms in _TECH_GROUPS.items():
        found = {term for term in terms if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", lowered)}
        if found:
            result[group_name] = found
    return result


def _looks_like_project_claim(text: str) -> bool:
    lowered = text.casefold()
    return any(marker.casefold() in lowered for marker in _CLAIM_MARKERS)


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    lowered = text.casefold()
    return any(marker.casefold() in lowered for marker in markers)


def _point_covered(point: str, answer_text: str) -> bool:
    point_text = point.casefold()
    answer = answer_text.casefold()
    if point_text and point_text in answer:
        return True
    point_terms = _keywords(point)
    answer_terms = _keywords(answer_text)
    if not point_terms:
        return False
    overlap = point_terms & answer_terms
    return len(overlap) >= min(2, len(point_terms)) or any(len(term) >= 4 for term in overlap)


def _point_weakly_covered(point: str, answer_text: str) -> bool:
    return bool(_keywords(point) & _keywords(answer_text))


def _contains_similar_point(points: list[str], point: str) -> bool:
    return any(_point_covered(point, candidate) or _point_covered(candidate, point) for candidate in points)


def _keywords(value: object) -> set[str]:
    text = _clean(value, max_chars=2000).casefold()
    raw_terms = re.findall(r"[a-z0-9_+#.-]{2,}|[\u4e00-\u9fff]{2,}", text)
    terms: set[str] = set(raw_terms)
    for term in raw_terms:
        if re.fullmatch(r"[\u4e00-\u9fff]{4,}", term):
            terms.update(term[index : index + 2] for index in range(0, min(len(term) - 1, 18)))
            terms.update(term[index : index + 4] for index in range(0, min(len(term) - 3, 16)))
    return {term for term in terms if term not in {"this", "that", "with", "and", "the", "我会", "说明"}}


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


def _asset_text(item: dict[str, Any]) -> str:
    return " ".join(
        value
        for value in (
            _clean(item.get("title"), max_chars=240),
            _clean(item.get("summary"), max_chars=800),
            _clean(item.get("content_excerpt"), max_chars=800),
        )
        if value
    )


def _checked_asset_refs(asset_items: list[dict[str, Any]]) -> list[str]:
    return _unique(
        [_clean(item.get("asset_id"), max_chars=120) for item in asset_items if _clean(item.get("asset_id"), max_chars=120)]
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
