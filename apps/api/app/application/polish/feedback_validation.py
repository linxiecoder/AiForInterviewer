from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_GENERATED_CONTRACT_IDS,
    POLISH_FEEDBACK_GENERATED_PAYLOAD_FIELDS,
    POLISH_FEEDBACK_GENERATED_SCHEMA_ID,
    POLISH_FEEDBACK_GENERATED_SCHEMA_VERSION,
)

_ALLOWED_STATUSES = ("generated", "partial", "low_confidence", "validation_failed")
_SESSION_SIMILARITY_STATUSES = (
    "benign_reuse",
    "semantic_repetition",
    "cross_turn_conflict",
    "not_applicable",
)
_UNSAFE_MARKERS = (
    "raw_prompt",
    "system_prompt",
    "developer_prompt",
    "completion",
    "raw_completion",
    "provider_payload",
    "raw_provider_payload",
    "provider_response",
    "raw_provider_response",
    "full_resume",
    "full_jd",
    "api_key",
    "token",
    "secret",
    "cookie",
)
_CONFLICT_REQUIRED_FIELDS = (
    "conflict_type",
    "current_answer_claim",
    "asset_claim",
    "severity",
    "clarification_question",
)
_SAME_QUESTION_LIST_FIELDS = (
    "improved_points",
    "repeated_loss_point_ids",
    "regressed_points",
    "next_retry_focus",
)
_FORMAL_ASSET_WRITE_FLAGS = ("formal_asset_written", "auto_confirmed")
_FULL_ASSET_BODY_FIELDS = ("asset_body", "asset_payload", "full_asset", "full_asset_body", "content")


def normalize_generated_feedback_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a detached, minimally normalized generated-feedback payload."""

    normalized = deepcopy(payload)
    for field_name in POLISH_FEEDBACK_GENERATED_PAYLOAD_FIELDS:
        normalized.setdefault(field_name, _default_value_for_field(field_name))
    normalized["schema_id"] = _clean(normalized.get("schema_id"), max_chars=120)
    normalized["schema_version"] = _clean(normalized.get("schema_version"), max_chars=40)
    normalized["status"] = _clean(normalized.get("status"), max_chars=40)
    normalized["contract_ids"] = _string_list(normalized.get("contract_ids"), max_items=20, max_item_chars=80)
    normalized["feedback_text"] = _clean(normalized.get("feedback_text"), max_chars=12000)
    normalized["answer_summary"] = _clean(normalized.get("answer_summary"), max_chars=4000)
    normalized["low_confidence_flags"] = _string_list(
        normalized.get("low_confidence_flags"),
        max_items=20,
        max_item_chars=160,
    )
    return normalized


def validate_generated_feedback_payload(payload: object) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    if not isinstance(payload, dict):
        return None, ("feedback_payload_schema_invalid",)

    errors: list[str] = []
    if _contains_unsafe_marker(payload):
        errors.append("feedback_payload_unsafe_leakage")

    normalized = normalize_generated_feedback_payload(payload)
    status = normalized["status"]
    generated_status = status == "generated"

    if normalized["schema_id"] != POLISH_FEEDBACK_GENERATED_SCHEMA_ID:
        errors.append("feedback_schema_id_invalid")
    if normalized["schema_version"] != POLISH_FEEDBACK_GENERATED_SCHEMA_VERSION:
        errors.append("feedback_schema_version_invalid")
    if status not in _ALLOWED_STATUSES:
        errors.append("feedback_status_invalid")
    if generated_status and not normalized["feedback_text"]:
        errors.append("feedback_text_required")

    if set(POLISH_FEEDBACK_GENERATED_CONTRACT_IDS) - set(normalized["contract_ids"]):
        errors.append("feedback_contract_ids_missing_required")

    score_value, score_errors = _score_value(normalized.get("score_result"))
    errors.extend(score_errors)

    loss_point_ids, major_loss_point_ids, deductions, loss_errors = _loss_points(
        normalized.get("loss_points"),
        generated_status=generated_status,
    )
    errors.extend(loss_errors)

    covered_loss_point_ids, reference_errors = _reference_answer(
        normalized.get("reference_answer"),
        known_loss_point_ids=loss_point_ids,
    )
    errors.extend(reference_errors)

    if generated_status:
        if loss_point_ids and not _reference_sections(normalized.get("reference_answer")):
            errors.append("reference_answer_sections_required")
        missing_major_coverage = major_loss_point_ids - covered_loss_point_ids
        if missing_major_coverage:
            errors.append("loss_point_reference_mapping_missing")

    if deductions and len(deductions) == len(loss_point_ids) and score_value is not None:
        expected_score = max(0.0, 100.0 - sum(deductions))
        if abs(expected_score - score_value) > 5:
            errors.append("score_loss_deduction_mismatch")

    errors.extend(_project_asset_consistency_check(normalized.get("project_asset_consistency_check")))
    errors.extend(_same_question_effect(normalized.get("same_question_effect")))
    errors.extend(_session_similarity_check(normalized.get("session_similarity_check")))
    errors.extend(_project_asset_update_candidates(normalized.get("project_asset_update_candidates")))

    if errors:
        return None, tuple(dict.fromkeys(errors))
    return normalized, ()


def _default_value_for_field(field_name: str) -> object:
    if field_name in {
        "contract_ids",
        "scoring_dimensions",
        "loss_points",
        "knowledge_points",
        "technical_principles",
        "project_asset_update_candidates",
        "next_recommended_actions",
        "low_confidence_flags",
        "trace_refs",
    }:
        return []
    if field_name in {
        "score_result",
        "same_question_effect",
        "project_asset_consistency_check",
        "session_similarity_check",
        "reference_answer",
        "feedback_metadata",
    }:
        return {}
    return ""


def _score_value(score_result: object) -> tuple[float | None, list[str]]:
    errors: list[str] = []
    if not isinstance(score_result, dict):
        return None, ["score_result_required"]

    score_value = score_result.get("score_value")
    if not _is_number(score_value):
        return None, ["score_value_invalid"]

    numeric_score = float(score_value)
    if numeric_score < 0 or numeric_score > 100:
        errors.append("score_value_out_of_range")
    score_type = _clean(score_result.get("score_type"), max_chars=80)
    return numeric_score, errors


def _loss_points(
    value: object,
    *,
    generated_status: bool,
) -> tuple[set[str], set[str], list[float], list[str]]:
    errors: list[str] = []
    loss_point_ids: set[str] = set()
    major_loss_point_ids: set[str] = set()
    deductions: list[float] = []
    if not isinstance(value, list):
        return loss_point_ids, major_loss_point_ids, deductions, ["loss_points_invalid"]

    for item in value:
        if not isinstance(item, dict):
            errors.append("loss_point_invalid")
            continue
        loss_point_id = _clean(item.get("loss_point_id"), max_chars=120)
        if not loss_point_id:
            errors.append("loss_point_id_required")
            continue
        if loss_point_id in loss_point_ids:
            errors.append("loss_point_id_duplicate")
        loss_point_ids.add(loss_point_id)

        severity = _clean(item.get("severity"), max_chars=40).lower()
        is_major = severity == "major"
        if is_major:
            major_loss_point_ids.add(loss_point_id)

        deduction = _deduction_value(item)
        if deduction is None:
            if generated_status and is_major:
                errors.append("loss_point_major_deduction_required")
            continue
        if deduction < 0 or deduction > 100:
            errors.append("loss_point_deduction_invalid")
            continue
        deductions.append(deduction)

    return loss_point_ids, major_loss_point_ids, deductions, errors


def _reference_answer(value: object, *, known_loss_point_ids: set[str]) -> tuple[set[str], list[str]]:
    errors: list[str] = []
    covered_loss_point_ids: set[str] = set()
    sections = _reference_sections(value)
    seen_section_ids: set[str] = set()

    for section in sections:
        section_id = _clean(section.get("section_id"), max_chars=120)
        if not section_id:
            errors.append("reference_answer_section_id_required")
        elif section_id in seen_section_ids:
            errors.append("reference_answer_section_id_duplicate")
        seen_section_ids.add(section_id)

        refs = _string_list(section.get("addresses_loss_point_ids"), max_items=40, max_item_chars=120)
        for ref in refs:
            if ref not in known_loss_point_ids:
                errors.append("reference_answer_unknown_loss_point_ref")
            else:
                covered_loss_point_ids.add(ref)

    return covered_loss_point_ids, errors


def _reference_sections(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, dict):
        return []
    sections = value.get("sections")
    if not isinstance(sections, list):
        return []
    return [section for section in sections if isinstance(section, dict)]


def _project_asset_consistency_check(value: object) -> list[str]:
    errors: list[str] = []
    if value in (None, {}):
        return errors
    if not isinstance(value, dict):
        return ["project_asset_consistency_check_invalid"]

    status = _clean(value.get("status"), max_chars=80)
    if status != "conflict":
        return errors

    conflicts = value.get("conflicts")
    if not isinstance(conflicts, list) or not conflicts:
        return ["project_asset_conflicts_required"]
    for conflict in conflicts:
        if not isinstance(conflict, dict):
            errors.append("project_asset_conflict_invalid")
            continue
        missing = [field for field in _CONFLICT_REQUIRED_FIELDS if not _clean(conflict.get(field), max_chars=500)]
        if "clarification_question" in missing:
            errors.append("project_asset_conflict_clarification_required")
        if missing:
            errors.append("project_asset_conflict_fields_required")
    return errors


def _same_question_effect(value: object) -> list[str]:
    if value in (None, {}):
        return []
    if not isinstance(value, dict):
        return ["same_question_effect_invalid"]

    errors: list[str] = []
    for field_name in _SAME_QUESTION_LIST_FIELDS:
        if not isinstance(value.get(field_name), list):
            errors.append("same_question_effect_fields_invalid")
    score_delta = value.get("score_delta")
    if score_delta is not None and not _is_number(score_delta):
        errors.append("same_question_score_delta_invalid")
    return errors


def _session_similarity_check(value: object) -> list[str]:
    if value in (None, {}):
        return []
    if not isinstance(value, dict):
        return ["session_similarity_check_invalid"]

    errors: list[str] = []
    status = _clean(value.get("status"), max_chars=80)
    if status not in _SESSION_SIMILARITY_STATUSES:
        errors.append("session_similarity_status_invalid")
        return errors

    if status == "cross_turn_conflict":
        related_turn_refs = value.get("related_turn_refs")
        if not isinstance(related_turn_refs, list) or not related_turn_refs:
            errors.append("session_similarity_cross_turn_refs_required")
        has_explanation = any(
            _clean(value.get(field), max_chars=1000)
            for field in ("reason", "description", "conflict_summary", "explanation")
        )
        if not has_explanation:
            errors.append("session_similarity_cross_turn_explanation_required")
    return errors


def _project_asset_update_candidates(value: object) -> list[str]:
    if value in (None, []):
        return []
    if not isinstance(value, list):
        return ["project_asset_update_candidates_invalid"]

    errors: list[str] = []
    for candidate in value:
        if not isinstance(candidate, dict):
            errors.append("project_asset_update_candidate_invalid")
            continue
        if candidate.get("candidate_type") != "project_asset_update_candidate":
            errors.append("project_asset_candidate_type_invalid")
        if candidate.get("user_confirmation_required") is not True:
            errors.append("project_asset_candidate_user_confirmation_required")
        for field_name in _FORMAL_ASSET_WRITE_FLAGS:
            if candidate.get(field_name) is True:
                errors.append("project_asset_candidate_formal_write_forbidden")
        target_asset_ref = candidate.get("target_asset_ref")
        if target_asset_ref is not None and not _is_reference_object(target_asset_ref):
            errors.append("project_asset_candidate_target_ref_invalid")
        if any(field in candidate for field in _FULL_ASSET_BODY_FIELDS):
            errors.append("project_asset_candidate_full_asset_body_forbidden")
    return errors


def _is_reference_object(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    allowed_keys = {"resource_type", "resource_id", "ref_type", "ref_id"}
    if any(key not in allowed_keys for key in value):
        return False
    has_resource_ref = bool(_clean(value.get("resource_type"), max_chars=80)) and bool(
        _clean(value.get("resource_id"), max_chars=160)
    )
    has_generic_ref = bool(_clean(value.get("ref_type"), max_chars=80)) and bool(
        _clean(value.get("ref_id"), max_chars=160)
    )
    return has_resource_ref or has_generic_ref


def _deduction_value(item: dict[str, Any]) -> float | None:
    for field_name in ("deduction", "deducted_points"):
        value = item.get(field_name)
        if _is_number(value):
            return float(value)
    return None


def _contains_unsafe_marker(value: object) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key).lower()
            if any(marker in key_text for marker in _UNSAFE_MARKERS):
                return True
            if _contains_unsafe_marker(nested):
                return True
        return False
    if isinstance(value, (list, tuple)):
        return any(_contains_unsafe_marker(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        return any(marker in lowered for marker in _UNSAFE_MARKERS)
    return False


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


def _clean(value: object, *, max_chars: int = 240) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
