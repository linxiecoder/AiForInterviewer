"""Feedback contract validator and normalization helpers for polish payloads."""

from __future__ import annotations

import copy
from dataclasses import asdict, is_dataclass
from difflib import SequenceMatcher
from typing import Any

from app.application.polish.feedback_contracts import (
    AnswerDelta,
    FEEDBACK_SCHEMA_ID,
    FEEDBACK_SCHEMA_VERSION,
    PositiveEvidencePoint,
    ScoringDimension,
    StructuredFeedbackPayload,
)

_FORBIDDEN_TOP_LEVEL_KEYS = {
    "raw_prompt",
    "prompt",
    "completion",
    "provider_payload",
    "provider_response",
    "llm_payload",
    "raw_response",
    "raw_llm_response",
    "system_prompt",
}
_FORBIDDEN_NESTED_KEYS = {"hidden_rubric", "rubric_secret", "secret_rubric"}
_FORBIDDEN_PROB_KEYS = {"pass_probability", "pass_prob", "exact_pass_probability"}


def validate_feedback_consistency(payload: dict[str, Any]) -> dict[str, Any]:
    raw_payload = _as_payload_dict(payload)
    normalized_payload = normalize_feedback_payload(payload)
    blocking_issues: list[str] = []
    warnings: list[str] = []
    repair_suggestions: list[str] = []

    _validate_point_references(
        normalized_payload,
        blocking_issues=blocking_issues,
        warnings=warnings,
        repair_suggestions=repair_suggestions,
    )
    _validate_score_consistency(
        normalized_payload,
        blocking_issues=blocking_issues,
        warnings=warnings,
        repair_suggestions=repair_suggestions,
    )
    _validate_critical_loss_reference_coverage(
        normalized_payload,
        text_key="p7_reference_answer",
        blocking_issues=blocking_issues,
        warnings=warnings,
        repair_suggestions=repair_suggestions,
        reference_field="required_reference_terms",
    )
    _validate_critical_loss_reference_coverage(
        normalized_payload,
        text_key="oral_script",
        blocking_issues=blocking_issues,
        warnings=warnings,
        repair_suggestions=repair_suggestions,
        reference_field="required_oral_terms",
    )
    _validate_positive_evidence_retained(
        normalized_payload,
        blocking_issues=blocking_issues,
        warnings=warnings,
        repair_suggestions=repair_suggestions,
    )
    _validate_retry_focus(
        normalized_payload,
        blocking_issues=blocking_issues,
        warnings=warnings,
        repair_suggestions=repair_suggestions,
    )
    _validate_repeated_loss_and_mastery(
        normalized_payload,
        blocking_issues=blocking_issues,
        warnings=warnings,
        repair_suggestions=repair_suggestions,
    )
    _validate_improved_points(
        normalized_payload,
        blocking_issues=blocking_issues,
        warnings=warnings,
        repair_suggestions=repair_suggestions,
    )
    _validate_oral_not_reference_copy(
        normalized_payload,
        blocking_issues=blocking_issues,
        warnings=warnings,
        repair_suggestions=repair_suggestions,
    )
    _validate_isolated_reference_answer(
        normalized_payload,
        blocking_issues=blocking_issues,
        warnings=warnings,
        repair_suggestions=repair_suggestions,
    )
    _validate_no_leaks(
        raw_payload,
        blocking_issues=blocking_issues,
        warnings=warnings,
        repair_suggestions=repair_suggestions,
    )
    _validate_no_leaks(
        normalized_payload,
        blocking_issues=blocking_issues,
        warnings=warnings,
        repair_suggestions=repair_suggestions,
    )

    if blocking_issues:
        normalized_payload = build_safe_structured_feedback_fallback(
            normalized_payload,
            reason="; ".join(blocking_issues[:2]) or "feedback validation failed",
        )

    return {
        "allow_emit": not blocking_issues,
        "blocking_issues": blocking_issues,
        "warnings": warnings,
        "repair_suggestions": repair_suggestions,
        "normalized_feedback_payload": normalized_payload,
    }


def build_safe_structured_feedback_fallback(
    input_payload: object,
    reason: str,
) -> dict[str, Any]:
    mapped = normalize_feedback_payload(input_payload)
    answer_id = str(mapped.get("answer_id", ""))
    feedback_id = str(mapped.get("feedback_id", ""))
    if not feedback_id:
        feedback_id = f"{answer_id}_fallback" if answer_id else "fallback_feedback"
    score_result = {
        "score_result_id": mapped.get("feedback_id") or feedback_id,
        "score_type": "polish_answer",
        "score_value": 0,
        "score_version": FEEDBACK_SCHEMA_VERSION,
        "rubric_version": "fallback",
        "confidence_level": "low",
    }

    fallback = StructuredFeedbackPayload(
        schema_id=FEEDBACK_SCHEMA_ID,
        schema_version=FEEDBACK_SCHEMA_VERSION,
        status="blocked",
        feedback_id=feedback_id,
        feedback_text=f"反馈一致性校验失败，已返回安全降级反馈：{reason}",
        feedback_summary=f"safe fallback for {feedback_id}",
        answer_diagnosis={"reason": reason, "mode": "safe_fallback"},
        scoring_dimensions=(),
        score_result=score_result,
        positive_evidence_points=(
            PositiveEvidencePoint(
                point_id="safe_point_000",
                title="fallback_point",
                evidence_excerpt="请补充更完整的回答细节并重试。",
                location="both",
                dimension_id="overall",
            ),
        ),
        loss_points=(),
        missing_answer_dimensions=(),
        interview_intent=str(mapped.get("interview_intent", "")),
        p7_reference_answer="请从题目与简历背景出发，补充问题上下文、技术边界与结果验证。",
        reference_answer_requirements=(),
        oral_script=(
            "我会先给出结论和关键约束，再说明具体技术动作与可验证结果，"
            "然后补充补救方案与复盘。"
        ),
        oral_script_requirements=(),
        knowledge_points=(),
        technical_principles=(),
        technical_gaps=(),
        communication_gaps=(),
        next_recommended_actions=("answer_again",),
        weakness_candidates=(),
        asset_candidates=(),
        validation_result_ref={"resource_type": "validation_result", "resource_id": feedback_id},
        trace_refs=(
            {"trace_ref_id": answer_id, "trace_type": "answer", "created_at": None}
            if answer_id
            else {}
        ,),
        low_confidence_flags=(
            {
                "flag_id": "feedback_contract_inconsistent",
                "reason": reason,
                "impact_scope": "score_result, loss_points, reference_answer, oral_script",
                "recommended_action": "regenerate_feedback_with_consistent_feedback_contract",
            },
        ),
        feedback_metadata={
            "fallback_reason": reason,
            "fallback_mode": "validate_feedback_consistency",
        },
        score_delta=0,
        dimension_delta={},
        improved_points=(),
        remaining_gaps=(),
        repeated_loss_points=(),
        regressed_points=(),
        mastery_status="requires_rework",
        should_continue_same_question=False,
        should_generate_next_question=False,
        updated_reference_answer=None,
        updated_oral_script=None,
        next_retry_focus=(),
    )
    if isinstance(mapped.get("answer_delta"), dict):
        answer_delta = AnswerDelta(**mapped["answer_delta"]) if _dict_matches_dataclass(AnswerDelta, mapped["answer_delta"]) else None
        if answer_delta is not None:
            # keep the same fallback delta shape as contract expectation
            fallback = _replace_answer_delta(fallback, answer_delta)
    return fallback.to_payload()


def normalize_feedback_payload(payload: object) -> dict[str, Any]:
    raw = _as_payload_dict(payload)
    if not isinstance(raw, dict):
        return _safe_minimum_payload()

    p7_reference_answer = str(
        raw.get("p7_reference_answer")
        or _dict_get_scalar(raw.get("reference_answer"), "summary")
        or ""
    )
    if not p7_reference_answer:
        reference_outline = _dict_get_scalar(raw.get("reference_answer"), "outline")
        if isinstance(reference_outline, list):
            p7_reference_answer = "；".join(str(x) for x in reference_outline)

    answer_diagnosis = raw.get("answer_diagnosis", {})
    if not isinstance(answer_diagnosis, dict):
        answer_diagnosis = {}

    scoring_dimensions = _normalize_scoring_dimensions(raw.get("scoring_dimensions", raw.get("dimension_scores", ())))
    score_result = raw.get("score_result")
    if not isinstance(score_result, dict):
        score_result = compute_score_result_from_dimensions(scoring_dimensions)
    else:
        if "score_value" not in score_result:
            score_result = {
                **score_result,
                **compute_score_result_from_dimensions(scoring_dimensions),
            }

    normalized: dict[str, Any] = {
        "schema_id": str(raw.get("schema_id", FEEDBACK_SCHEMA_ID)),
        "schema_version": str(raw.get("schema_version", FEEDBACK_SCHEMA_VERSION)),
        "status": str(raw.get("status", "generated")),
        "feedback_id": str(raw.get("feedback_id", raw.get("result_ref", ""))),
        "feedback_text": str(raw.get("feedback_text", raw.get("feedback_summary", ""))),
        "feedback_summary": str(raw.get("feedback_summary", raw.get("feedback_text", ""))),
        "answer_diagnosis": answer_diagnosis,
        "scoring_dimensions": [asdict(dim) for dim in scoring_dimensions],
        "score_result": score_result,
        "positive_evidence_points": _normalize_positive_evidence_points(
            raw.get("positive_evidence_points", ())
        ),
        "loss_points": _normalize_loss_points(raw.get("loss_points", ())),
        "missing_answer_dimensions": raw.get("missing_answer_dimensions", ()),
        "interview_intent": str(raw.get("interview_intent", raw.get("question_pattern", ""))),
        "p7_reference_answer": p7_reference_answer,
        "reference_answer_requirements": _normalize_reference_requirements(
            raw.get("reference_answer_requirements", ())
        ),
        "oral_script": str(raw.get("oral_script", "")),
        "oral_script_requirements": _normalize_oral_requirements(
            raw.get("oral_script_requirements", ())
        ),
        "knowledge_points": raw.get("knowledge_points", []),
        "technical_principles": raw.get("technical_principles", []),
        "technical_gaps": _to_list(raw.get("technical_gaps")),
        "communication_gaps": _to_list(raw.get("communication_gaps")),
        "next_recommended_actions": _to_list(raw.get("next_recommended_actions")),
        "weakness_candidates": _to_list(raw.get("weakness_candidates")),
        "asset_candidates": _to_list(raw.get("asset_candidates")),
        "validation_result_ref": raw.get("validation_result_ref"),
        "trace_refs": _to_list(raw.get("trace_refs")),
        "low_confidence_flags": _to_list(raw.get("low_confidence_flags")),
        "feedback_metadata": {
            **({"normalized_from": "legacy_payload"} if _is_legacy_payload_shape(raw) else {}),
            **raw.get("feedback_metadata", {}),
        },
        "score_delta": int(raw.get("score_delta", 0)),
        "dimension_delta": raw.get("dimension_delta", {}),
        "improved_points": _to_list(raw.get("improved_points")),
        "remaining_gaps": _to_list(raw.get("remaining_gaps")),
        "repeated_loss_points": _to_list(raw.get("repeated_loss_points")),
        "regressed_points": _to_list(raw.get("regressed_points")),
        "mastery_status": raw.get("mastery_status"),
        "should_continue_same_question": bool(raw.get("should_continue_same_question", False)),
        "should_generate_next_question": bool(raw.get("should_generate_next_question", False)),
        "next_retry_focus": _normalize_retry_focus(raw.get("next_retry_focus", raw.get("retry_focus", ()))),
        "updated_reference_answer": raw.get("updated_reference_answer"),
        "updated_oral_script": raw.get("updated_oral_script"),
        "answer_id": raw.get("answer_id", ""),
        "question_id": raw.get("question_id", ""),
        "question_text": str(raw.get("question_text", "")),
        "answer_text": str(raw.get("answer_text", "")),
        "answer_delta": raw.get("answer_delta", {}),
        "previous_loss_points": _to_list(raw.get("previous_loss_points")),
    }
    return normalized


def compute_score_result_from_dimensions(dimensions: object) -> dict[str, int]:
    normalized = _normalize_scoring_dimensions(dimensions)
    if not normalized:
        return {"score_value": 0, "weight_total": 0.0, "score_version": FEEDBACK_SCHEMA_VERSION}

    weighted_score = 0.0
    weighted_max = 0.0
    for dimension in normalized:
        max_score = max(float(dimension.max_score), 0.0)
        weight = max(float(dimension.weight), 0.0)
        if max_score <= 0 or weight <= 0:
            continue
        score = max(0.0, min(float(dimension.score_value), float(dimension.max_score)))
        weighted_score += (score / max_score) * weight
        weighted_max += weight
    if weighted_max <= 0:
        return {"score_value": 0, "weight_total": 0.0, "score_version": FEEDBACK_SCHEMA_VERSION}

    score_value = int(round((weighted_score / weighted_max) * 100))
    return {
        "score_value": score_value,
        "weight_total": weighted_max,
        "score_version": FEEDBACK_SCHEMA_VERSION,
    }


def _is_legacy_payload_shape(payload: dict[str, Any]) -> bool:
    return (
        "contract_id" in payload
        and payload.get("schema_id") is None
        and "p7_reference_answer" not in payload
    ) or "reference_answer" in payload


def _validate_point_references(
    payload: dict[str, Any],
    *,
    blocking_issues: list[str],
    warnings: list[str],
    repair_suggestions: list[str],
) -> None:
    positive_points = payload.get("positive_evidence_points", ())
    loss_points = payload.get("loss_points", ())
    if not isinstance(positive_points, list):
        blocking_issues.append("positive_evidence_points_must_be_array")
        repair_suggestions.append("normalize_positive_evidence_points_to_array")
        return
    if not isinstance(loss_points, list):
        blocking_issues.append("loss_points_must_be_array")
        repair_suggestions.append("normalize_loss_points_to_array")
        return

    valid_dimension_ids = {
        str(dimension.get("dimension_id"))
        for dimension in payload.get("scoring_dimensions", ())
        if isinstance(dimension, dict) and dimension.get("dimension_id")
    }
    for point in loss_points:
        if not isinstance(point, dict):
            blocking_issues.append("loss_point_must_be_object")
            continue
        if not point.get("loss_point_id") or not point.get("reason"):
            blocking_issues.append("loss_point_missing_required_fields")
        if point.get("dimension_id") and str(point["dimension_id"]) not in valid_dimension_ids:
            warnings.append(f"loss_point_dimension_not_defined:{point.get('loss_point_id')}")
    for point in positive_points:
        if not isinstance(point, dict):
            blocking_issues.append("positive_evidence_point_must_be_object")
            continue
        if not point.get("point_id") or not point.get("evidence_excerpt"):
            blocking_issues.append("positive_evidence_point_missing_required_fields")
        if point.get("dimension_id") and str(point["dimension_id"]) not in valid_dimension_ids:
            warnings.append(f"positive_point_dimension_not_defined:{point.get('point_id')}")


def _validate_score_consistency(
    payload: dict[str, Any],
    *,
    blocking_issues: list[str],
    warnings: list[str],
    repair_suggestions: list[str],
) -> None:
    score_result = payload.get("score_result")
    if not isinstance(score_result, dict):
        blocking_issues.append("score_result_must_be_object")
        repair_suggestions.append("normalize_score_result")
        return
    actual = _to_int(score_result.get("score_value"))
    computed = compute_score_result_from_dimensions(payload.get("scoring_dimensions", ()))
    expected = int(computed.get("score_value", 0))
    if actual != expected:
        blocking_issues.append(
            f"score_result_inconsistent:{actual}!={expected}"
        )
        repair_suggestions.append("recompute_score_result_from_scoring_dimensions")
    dimensions = payload.get("scoring_dimensions", ())
    if not isinstance(dimensions, list) or not dimensions:
        warnings.append("scoring_dimensions_missing")


def _validate_critical_loss_reference_coverage(
    payload: dict[str, Any],
    *,
    text_key: str,
    blocking_issues: list[str],
    warnings: list[str],
    repair_suggestions: list[str],
    reference_field: str,
) -> None:
    target_text = str(payload.get(text_key, "")).lower()
    critical_points = [point for point in payload.get("loss_points", []) if isinstance(point, dict) and point.get("critical")]
    for point in critical_points:
        required_terms = _to_list(point.get(reference_field))
        if not required_terms:
            continue
        if not _contains_any(normalized=required_terms, content=target_text):
            blocking_issues.append(
                f"critical_loss_point_not_covered_by_{text_key}:{point.get('loss_point_id')}"
            )
            repair_suggestions.append(
                f"align_{text_key}_with_loss_point:{point.get('loss_point_id')}"
            )


def _validate_positive_evidence_retained(
    payload: dict[str, Any],
    *,
    blocking_issues: list[str],
    warnings: list[str],
    repair_suggestions: list[str],
) -> None:
    reference_text = str(payload.get("p7_reference_answer", "")).lower()
    oral_text = str(payload.get("oral_script", "")).lower()
    positive_points = payload.get("positive_evidence_points", [])

    for point in positive_points:
        if not isinstance(point, dict):
            continue
        excerpt = str(point.get("evidence_excerpt", "")).lower()
        if not excerpt:
            blocking_issues.append("positive_evidence_point_requires_excerpt")
            repair_suggestions.append("add_evidence_excerpt_for_positive_point")
            continue
        location = str(point.get("location", "both")).lower()
        appears_reference = excerpt in reference_text
        appears_oral = excerpt in oral_text
        if location == "reference_answer" and not appears_reference:
            blocking_issues.append(f"positive_point_not_retained_in_reference:{point.get('point_id')}")
            repair_suggestions.append("keep_positive_point_in_reference_answer")
        elif location == "oral_script" and not appears_oral:
            blocking_issues.append(f"positive_point_not_retained_in_oral:{point.get('point_id')}")
            repair_suggestions.append("keep_positive_point_in_oral_script")
        elif location == "both" and not (appears_reference or appears_oral):
            blocking_issues.append(f"positive_point_not_retained:{point.get('point_id')}")
            repair_suggestions.append("retain_positive_evidence_in_reference_or_oral")


def _validate_retry_focus(
    payload: dict[str, Any],
    *,
    blocking_issues: list[str],
    warnings: list[str],
    repair_suggestions: list[str],
) -> None:
    remaining_gaps = set(_to_list(payload.get("remaining_gaps")))
    next_retry_focus = payload.get("next_retry_focus", [])
    if not next_retry_focus:
        return
    if not remaining_gaps:
        blocking_issues.append("next_retry_focus_without_remaining_gaps")
        repair_suggestions.append("set_remaining_gaps_before_retry_focus")
        return
    for focus in next_retry_focus:
        if isinstance(focus, str):
            focus_area = focus
        elif isinstance(focus, dict):
            focus_area = str(focus.get("focus_area", "")).strip()
        else:
            continue
        if focus_area and focus_area not in remaining_gaps:
            warnings.append(f"next_retry_focus_not_from_remaining_gaps:{focus_area}")


def _validate_repeated_loss_and_mastery(
    payload: dict[str, Any],
    *,
    blocking_issues: list[str],
    warnings: list[str],
    repair_suggestions: list[str],
) -> None:
    repeated = _to_list(payload.get("repeated_loss_points", []))
    if not repeated:
        return
    status = str(payload.get("mastery_status", "")).lower()
    if status in {"mastered", "mastery_achieved", "passed", "qualified"}:
        blocking_issues.append(
            "mastery_status_conflicts_with_repeated_loss_points"
        )
        repair_suggestions.append("downgrade_mastery_status_if_repeated_gaps_exist")


def _validate_improved_points(
    payload: dict[str, Any],
    *,
    blocking_issues: list[str],
    warnings: list[str],
    repair_suggestions: list[str],
) -> None:
    improved_points = set(_to_list(payload.get("improved_points", [])))
    if not improved_points:
        return
    previous_losses = {point.get("loss_point_id") for point in _to_list(payload.get("previous_loss_points", []))}
    if not previous_losses:
        blocking_issues.append("improved_points_without_previous_loss_points")
        repair_suggestions.append("provide_previous_loss_points_for_delta_repair_tracking")
        return
    invalid = sorted(item for item in improved_points if item not in previous_losses)
    if invalid:
        blocking_issues.append("improved_points_not_from_previous_loss_points:" + ",".join(invalid))
        repair_suggestions.append("derive_improved_points_only_from_previous_losses")


def _validate_oral_not_reference_copy(
    payload: dict[str, Any],
    *,
    blocking_issues: list[str],
    warnings: list[str],
    repair_suggestions: list[str],
) -> None:
    reference_text = str(payload.get("p7_reference_answer", ""))
    oral = str(payload.get("oral_script", ""))
    if not reference_text or not oral:
        return
    ratio = SequenceMatcher(None, reference_text, oral).ratio()
    if ratio >= 0.92:
        blocking_issues.append("oral_script_is_reference_copy")
        repair_suggestions.append("rewrite_oral_script_as口语化版本")

def _validate_isolated_reference_answer(
    payload: dict[str, Any],
    *,
    blocking_issues: list[str],
    warnings: list[str],
    repair_suggestions: list[str],
) -> None:
    if not payload.get("p7_reference_answer"):
        return
    has_support = bool(payload.get("scoring_dimensions")) or bool(payload.get("loss_points")) or bool(
        payload.get("positive_evidence_points")
    )
    if not has_support:
        blocking_issues.append("isolated_reference_answer")
        repair_suggestions.append("attach scoring_dimensions_or_loss_points_or_positive_points")


def _validate_no_leaks(
    payload: dict[str, Any],
    *,
    blocking_issues: list[str],
    warnings: list[str],
    repair_suggestions: list[str],
) -> None:
    forbidden_found = _collect_forbidden_fields(payload)
    for key in sorted(forbidden_found):
        if "rubric" in key.lower() and "hidden_rubric" in key.lower():
            blocking_issues.append("hidden_rubric_present")
            repair_suggestions.append("remove_hidden_rubric_before_emit")
        elif "prob" in key.lower() and ("pass" in key.lower() or "prob" in key.lower()):
            blocking_issues.append("exact_pass_probability_present")
            repair_suggestions.append("remove_exact_probability_fields")
        else:
            blocking_issues.append(f"{key}_present")
            repair_suggestions.append(f"remove_{key}_before_emit")


def _collect_forbidden_fields(payload: Any, path: str = "") -> set[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            if not isinstance(key, str):
                continue
            lowered = key.lower()
            normalized = lowered.replace("-", "_")
            if normalized in _FORBIDDEN_TOP_LEVEL_KEYS or normalized in _FORBIDDEN_NESTED_KEYS:
                found.add(normalized)
            if normalized in _FORBIDDEN_PROB_KEYS:
                found.add(normalized)
            next_path = f"{path}.{key}" if path else key
            if isinstance(value, (dict, list, tuple)):
                found.update(_collect_forbidden_fields(value, path=next_path))
            elif (
                isinstance(value, str)
                and normalized != "prompt_version"
                and any(token in lowered for token in ("prompt", "completion"))
                and (
                    "prompt_version" in lowered
                    or "answer_prompt" in lowered
                    or "system_prompt" in lowered
                )
            ):
                found.add(normalized)
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            found.update(_collect_forbidden_fields(item, path=path))
    return found


def _as_payload_dict(payload: object) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, StructuredFeedbackPayload):
        return payload.to_payload()
    if is_dataclass(payload):
        return asdict(payload)
    if hasattr(payload, "__dict__") and isinstance(payload.__dict__, dict):
        return dict(payload.__dict__)
    return {}


def _safe_minimum_payload() -> dict[str, Any]:
    return {
        "schema_id": FEEDBACK_SCHEMA_ID,
        "schema_version": FEEDBACK_SCHEMA_VERSION,
        "status": "generated",
        "feedback_id": "fallback_feedback",
        "feedback_text": "反馈数据异常，已进入降级返回。",
        "feedback_summary": "fallback",
        "answer_diagnosis": {},
        "scoring_dimensions": [],
        "score_result": compute_score_result_from_dimensions([]),
        "positive_evidence_points": [],
        "loss_points": [],
        "missing_answer_dimensions": [],
        "interview_intent": "",
        "p7_reference_answer": "",
        "reference_answer_requirements": [],
        "oral_script": "",
        "oral_script_requirements": [],
        "knowledge_points": [],
        "technical_principles": [],
        "technical_gaps": [],
        "communication_gaps": [],
        "next_recommended_actions": [],
        "weakness_candidates": [],
        "asset_candidates": [],
        "validation_result_ref": None,
        "trace_refs": [],
        "low_confidence_flags": [],
        "feedback_metadata": {"normalized_from": "minimum_fallback"},
        "score_delta": 0,
        "dimension_delta": {},
        "improved_points": [],
        "remaining_gaps": [],
        "repeated_loss_points": [],
        "regressed_points": [],
        "mastery_status": None,
        "should_continue_same_question": False,
        "should_generate_next_question": False,
        "next_retry_focus": [],
        "updated_reference_answer": None,
        "updated_oral_script": None,
        "answer_id": "",
        "question_id": "",
        "question_text": "",
        "answer_text": "",
        "answer_delta": {},
        "previous_loss_points": [],
    }


def _normalize_scoring_dimensions(raw_dimensions: Any) -> tuple[ScoringDimension, ...]:
    dimensions: list[ScoringDimension] = []
    for raw_dimension in _to_list(raw_dimensions):
        if isinstance(raw_dimension, ScoringDimension):
            dimensions.append(raw_dimension)
            continue
        if not isinstance(raw_dimension, dict):
            continue
        try:
            dimensions.append(
                ScoringDimension(
                    dimension_id=str(raw_dimension.get("dimension_id") or raw_dimension.get("key", "")),
                    score_value=_to_int(raw_dimension.get("score_value", raw_dimension.get("score", 0))),
                    max_score=_to_int(raw_dimension.get("max_score", 100)),
                    weight=float(raw_dimension.get("weight", 1.0)),
                    is_critical=bool(raw_dimension.get("is_critical", raw_dimension.get("critical", False))),
                    rationale=_as_string_or_none(raw_dimension.get("rationale")),
                )
            )
        except (TypeError, ValueError):
            continue
    return tuple(dimensions)


def _normalize_positive_evidence_points(raw_points: Any) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for point in _to_list(raw_points):
        if isinstance(point, dict):
            points.append(point)
            continue
        if isinstance(point, str):
            points.append({"point_id": point, "title": point, "evidence_excerpt": point})
    return points


def _normalize_loss_points(raw_points: Any) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for point in _to_list(raw_points):
        if isinstance(point, dict):
            normalized = dict(point)
            normalized["critical"] = bool(
                normalized.get("critical", normalized.get("is_critical", False))
            )
            points.append(normalized)
    return points


def _normalize_reference_requirements(raw_requirements: Any) -> list[dict[str, Any]]:
    requirements: list[dict[str, Any]] = []
    for requirement in _to_list(raw_requirements):
        if isinstance(requirement, dict):
            requirements.append(requirement)
    return requirements


def _normalize_oral_requirements(raw_requirements: Any) -> list[dict[str, Any]]:
    requirements: list[dict[str, Any]] = []
    for requirement in _to_list(raw_requirements):
        if isinstance(requirement, dict):
            requirements.append(requirement)
    return requirements


def _normalize_retry_focus(raw_retry_focus: Any) -> list[dict[str, Any]]:
    focuses: list[dict[str, Any]] = []
    for raw_focus in _to_list(raw_retry_focus):
        if isinstance(raw_focus, dict):
            focus = dict(raw_focus)
            focus["focus_area"] = str(focus.get("focus_area", focus.get("focus", ""))).strip()
            if focus.get("focus_area"):
                focuses.append(focus)
        elif isinstance(raw_focus, str) and raw_focus.strip():
            focuses.append({"focus_area": raw_focus.strip(), "priority": 1})
    return focuses


def _to_list(value: Any) -> list[Any]:
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _dict_get_scalar(source: Any, key: str) -> Any:
    if isinstance(source, dict):
        return source.get(key)
    return None


def _contains_any(*, normalized: list[str], content: str) -> bool:
    if not content:
        return False
    return any(token in content for token in (token.lower().strip() for token in normalized if token.strip()))


def _as_string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _dict_matches_dataclass(cls: type[Any], payload: dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    return payload.get("score_delta") is not None or "dimension_delta" in payload


def _replace_answer_delta(payload: StructuredFeedbackPayload, answer_delta: AnswerDelta) -> StructuredFeedbackPayload:
    as_dict = payload.to_payload()
    merged = copy.deepcopy(as_dict)
    merged.update(
        {
            "score_delta": answer_delta.score_delta,
            "dimension_delta": answer_delta.dimension_delta,
            "improved_points": list(answer_delta.improved_points),
            "remaining_gaps": list(answer_delta.remaining_gaps),
            "repeated_loss_points": list(answer_delta.repeated_loss_points),
            "regressed_points": list(answer_delta.regressed_points),
            "mastery_status": answer_delta.mastery_status,
            "should_continue_same_question": answer_delta.should_continue_same_question,
            "should_generate_next_question": answer_delta.should_generate_next_question,
            "updated_reference_answer": answer_delta.updated_reference_answer,
            "updated_oral_script": answer_delta.updated_oral_script,
            "next_retry_focus": [asdict(focus) for focus in answer_delta.next_retry_focus],
        }
    )
    return StructuredFeedbackPayload(**merged)
