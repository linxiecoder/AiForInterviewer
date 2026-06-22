from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from pydantic import ValidationError

from app.application.polish.feedback_evaluation import normalize_semantic_score_result
from app.application.polish.feedback_models import FeedbackCandidatePayload, FeedbackFinalPayload
from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_CANDIDATE_PAYLOAD_FIELDS,
    POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
    POLISH_FEEDBACK_FINAL_PAYLOAD_FIELDS,
    POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
)
from app.application.polish.feedback_rules import (
    ANSWER_CHANGE_TRENDS,
    ASSET_CONFLICT_TYPES,
    ASSET_CONSISTENCY_STATUSES,
    FEEDBACK_CARD_TYPES,
)

_ALLOWED_STATUSES = ("generated", "partial", "low_confidence", "validation_failed")
_UNSAFE_MARKERS = (
    "raw_prompt",
    "system_prompt",
    "developer_prompt",
    "completion",
    "raw_completion",
    "full_completion",
    "completion_text",
    "reasoning_content",
    "provider_payload",
    "raw_provider",
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
_UNSAFE_KEY_MARKERS = frozenset(_UNSAFE_MARKERS) | frozenset(
    {
        "prompt",
        "user_prompt",
        "internal_prompt",
        "hidden_rubric",
        "hidden_scoring",
        "hidden_scoring_rules",
    }
)
_UNSAFE_VALUE_MARKERS = (
    "raw_prompt",
    "system_prompt",
    "developer_prompt",
    "user_prompt",
    "internal_prompt",
    "raw_completion",
    "full_completion",
    "completion_text",
    "reasoning_content",
    "provider_payload",
    "raw_provider",
    "raw_provider_payload",
    "provider_response",
    "raw_provider_response",
    "full_resume",
    "full_jd",
    "hidden_rubric",
    "hidden_scoring",
)
_UNSAFE_VALUE_PATTERNS = (
    re.compile(r"\bapi[_-]?key\s*[:=]\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"\bcookie\s*[:=]\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"\btoken\s*[:=]\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"\bsecret\s*[:=]\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"\bbearer\s+[a-z0-9._~+/=-]+", re.IGNORECASE),
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
_CANDIDATE_REQUIRED_FIELDS = (
    "feedback_text",
    "answer_summary",
    "score_result",
    "loss_points",
    "reference_answer",
)
_CANDIDATE_FORBIDDEN_FIELDS = frozenset(
    {
        "feedback_id",
        "deduction",
        "deducted_points",
        "raw_prompt",
        "raw_completion",
        "full_completion",
        "completion_text",
        "reasoning_content",
        "provider_payload",
        "raw_provider",
        "raw_provider_payload",
        "full_resume",
        "full_jd",
        "full_answer",
        "token",
        "secret",
        "cookie",
    }
)
_SAME_QUESTION_EFFECT_ENUMS = ("unchanged", "improved", "regressed", "not_applicable")
_OPTIONAL_ENHANCED_FIELD_TYPES: dict[str, type | tuple[type, ...]] = {
    "score_result": dict,
    "scoring_dimensions": list,
    "knowledge_points": list,
    "technical_principles": list,
    "project_asset_consistency_check": dict,
    "asset_consistency_check": dict,
    "answer_coverage": dict,
    "answer_change_analysis": dict,
    "feedback_cards": list,
    "session_similarity_check": dict,
}
_FINAL_REQUIRED_FIELDS = (
    "schema_id",
    "schema_version",
    "status",
    "contract_ids",
    "feedback_id",
    "feedback_text",
    "answer_summary",
    "score_result",
    "loss_points",
    "reference_answer",
    "asset_consistency_check",
    "answer_coverage",
    "answer_change_analysis",
    "feedback_cards",
    "next_recommended_actions",
    "low_confidence_flags",
    "trace_refs",
    "feedback_metadata",
)
_FINAL_FORBIDDEN_FIELDS = frozenset()
_PHASE5_SCORE_RESULT_EXTENSION_FIELDS = (
    "stability_layer",
    "calibration_layer",
    "learning_control",
)
FEEDBACK_TEXT_MAX_CHARS = 12000
FEEDBACK_ANSWER_SUMMARY_MAX_CHARS = 4000
FEEDBACK_EVIDENCE_REF_MAX_ITEMS = 40
FEEDBACK_EVIDENCE_REF_MAX_CHARS = 200
FEEDBACK_VALIDATION_WARNING_MAX_ITEMS = 40
FEEDBACK_VALIDATION_WARNING_MAX_CHARS = 160
FEEDBACK_REFERENCE_SECTION_CONTENT_MAX_CHARS = 12000
FEEDBACK_REFERENCE_LOSS_REF_MAX_ITEMS = 40
FEEDBACK_REFERENCE_LOSS_REF_MAX_CHARS = 120


def validate_feedback_candidate_payload(
    payload: object,
    *,
    expected_progress_state_ref: str | None = None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    if not isinstance(payload, dict):
        return None, ("feedback_payload_schema_invalid",)

    errors: list[str] = []
    warnings: list[str] = _candidate_pre_validation_warnings(payload)
    source_payload = deepcopy(payload)

    forbidden_fields = _CANDIDATE_FORBIDDEN_FIELDS & set(source_payload)
    if forbidden_fields:
        errors.append("feedback_candidate_forbidden_fields")
    if _contains_unsafe_marker(payload):
        errors.append("feedback_payload_unsafe_leakage")
    if errors:
        return None, tuple(dict.fromkeys(errors))

    _append_candidate_reference_answer_recovery_warnings(source_payload, warnings)

    try:
        candidate_model = FeedbackCandidatePayload.model_validate(source_payload)
    except ValidationError as exc:
        return None, _candidate_model_errors(exc)

    normalized = candidate_model.model_dump(mode="json", exclude_none=True)
    warnings.extend(candidate_model.validation_warnings)

    normalized["feedback_text"] = _clean(normalized.get("feedback_text"), max_chars=FEEDBACK_TEXT_MAX_CHARS)
    if not normalized["feedback_text"]:
        errors.append("feedback_text_required")
    normalized["answer_summary"] = _clean(
        normalized.get("answer_summary"),
        max_chars=FEEDBACK_ANSWER_SUMMARY_MAX_CHARS,
    )
    if not normalized["answer_summary"]:
        errors.append("answer_summary_required")
    normalized["score_reasoning"] = _normalize_score_reasoning_for_candidate(
        normalized.get("score_reasoning"),
        warnings=warnings,
    )
    normalized_score_result, score_errors, score_warnings = normalize_semantic_score_result(
        normalized.get("score_result"),
        expected_progress_state_ref=expected_progress_state_ref,
    )
    errors.extend(score_errors)
    warnings.extend(score_warnings)
    if normalized_score_result is not None:
        normalized["score_result"] = normalized_score_result
    normalized["low_confidence_flags"] = _string_list(normalized.get("low_confidence_flags"), max_items=20, max_item_chars=160)
    normalized["evidence_refs"] = _string_list(
        normalized.get("evidence_refs"),
        max_items=FEEDBACK_EVIDENCE_REF_MAX_ITEMS,
        max_item_chars=FEEDBACK_EVIDENCE_REF_MAX_CHARS,
    )

    normalized["loss_points"] = _normalize_loss_point_evidence_refs(normalized.get("loss_points"), errors=errors)
    _normalize_loss_point_ids(normalized.get("loss_points"))
    loss_point_ids, _, _, loss_errors = _loss_points(
        normalized.get("loss_points"),
        generated_status=False,
    )
    errors.extend(loss_errors)

    normalized["reference_answer"] = deepcopy(normalized.get("reference_answer"))
    reference_answer = normalized["reference_answer"]
    normalized["reference_answer"] = _normalize_reference_answer_sections(
        reference_answer,
        known_loss_point_ids=loss_point_ids,
        errors=errors,
        warnings=warnings,
        recoverable=True,
    )

    if normalized.get("same_question_effect") is not None:
        normalized_effect, effect_warnings = _normalize_candidate_same_question_effect(
            normalized.get("same_question_effect")
        )
        normalized["same_question_effect"] = normalized_effect
        warnings.extend(effect_warnings)
        warnings.extend(_same_question_effect(normalized.get("same_question_effect")))
    if normalized.get("project_asset_update_candidates") is not None:
        normalized_candidates, candidate_warnings = _normalize_candidate_project_asset_update_candidates(
            normalized.get("project_asset_update_candidates")
        )
        normalized["project_asset_update_candidates"] = normalized_candidates
        warnings.extend(candidate_warnings)
    warnings.extend(_optional_enhancement_warnings(normalized))
    if warnings:
        _append_validation_warnings(normalized, warnings)

    if errors:
        return None, tuple(dict.fromkeys(errors))
    return normalized, ()


def validate_final_feedback_payload(
    payload: object,
    *,
    require_feedback_id: bool = True,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    if not isinstance(payload, dict):
        return None, ("feedback_payload_schema_invalid",)

    errors: list[str] = []
    normalized = deepcopy(payload)

    if _contains_unsafe_marker(payload):
        errors.append("feedback_payload_unsafe_leakage")
    if errors:
        return None, tuple(dict.fromkeys(errors))

    model_input = deepcopy(payload)
    if not require_feedback_id and isinstance(model_input, dict):
        model_input.setdefault("feedback_id", "")
    try:
        final_model = FeedbackFinalPayload.model_validate(model_input)
    except ValidationError as exc:
        return None, _final_model_errors(exc)
    normalized = final_model.model_dump(mode="json")

    unexpected_fields = set(normalized) - set(POLISH_FEEDBACK_FINAL_PAYLOAD_FIELDS)
    if unexpected_fields:
        errors.append("feedback_final_unknown_fields")
    forbidden_fields = _FINAL_FORBIDDEN_FIELDS & set(normalized)
    if forbidden_fields:
        errors.append("feedback_final_forbidden_fields")

    for field in _FINAL_REQUIRED_FIELDS:
        if field == "feedback_id" and not require_feedback_id:
            continue
        if field not in normalized:
            errors.append("feedback_final_required_fields_missing")

    normalized["schema_id"] = _clean(normalized.get("schema_id"), max_chars=120)
    if normalized["schema_id"] != POLISH_FEEDBACK_FINAL_SCHEMA_ID:
        errors.append("feedback_schema_id_invalid")
    normalized["schema_version"] = _clean(normalized.get("schema_version"), max_chars=40)
    if normalized["schema_version"] != POLISH_FEEDBACK_FINAL_SCHEMA_VERSION:
        errors.append("feedback_schema_version_invalid")

    normalized["status"] = _clean(normalized.get("status"), max_chars=40)
    if normalized["status"] not in _ALLOWED_STATUSES:
        errors.append("feedback_status_invalid")
    normalized["contract_ids"] = _string_list(normalized.get("contract_ids"), max_items=20, max_item_chars=80)
    if set(POLISH_FEEDBACK_FINAL_CONTRACT_IDS) - set(normalized["contract_ids"]):
        errors.append("feedback_contract_ids_missing_required")
    normalized["feedback_id"] = _clean(normalized.get("feedback_id"), max_chars=120)
    if not normalized["feedback_id"] and require_feedback_id:
        errors.append("feedback_id_required")
    normalized["feedback_text"] = _clean(normalized.get("feedback_text"), max_chars=FEEDBACK_TEXT_MAX_CHARS)
    if not normalized["feedback_text"]:
        errors.append("feedback_text_required")
    normalized["answer_summary"] = _clean(
        normalized.get("answer_summary"),
        max_chars=FEEDBACK_ANSWER_SUMMARY_MAX_CHARS,
    )
    if not normalized["answer_summary"]:
        errors.append("answer_summary_required")
    normalized["low_confidence_flags"] = _string_list(
        normalized.get("low_confidence_flags"),
        max_items=FEEDBACK_VALIDATION_WARNING_MAX_ITEMS,
        max_item_chars=FEEDBACK_VALIDATION_WARNING_MAX_CHARS,
    )

    normalized_score_result, score_errors, score_warnings = normalize_semantic_score_result(normalized.get("score_result"))
    errors.extend(score_errors)
    if score_warnings:
        metadata = normalized.get("feedback_metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        existing = _string_list(
            metadata.get("validation_warnings"),
            max_items=FEEDBACK_VALIDATION_WARNING_MAX_ITEMS,
            max_item_chars=FEEDBACK_VALIDATION_WARNING_MAX_CHARS,
        )
        metadata["validation_warnings"] = list(dict.fromkeys([*existing, *score_warnings]))
        normalized["feedback_metadata"] = metadata
    if normalized_score_result is not None:
        normalized["score_result"] = _restore_phase5_score_result_extensions(
            normalized_score_result,
            normalized.get("score_result"),
        )
    else:
        normalized["score_result"] = normalized.get("score_result")

    normalized["loss_points"] = _normalize_loss_point_evidence_refs(normalized.get("loss_points"), errors=errors)
    loss_point_ids, _, _, loss_errors = _loss_points(
        normalized.get("loss_points"),
        generated_status=False,
    )
    errors.extend(loss_errors)
    if not isinstance(normalized["loss_points"], list):
        errors.append("loss_points_invalid")

    reference_answer = normalized.get("reference_answer")
    normalized["reference_answer"] = deepcopy(reference_answer)
    final_reference_warnings: list[str] = []
    normalized["reference_answer"] = _normalize_reference_answer_sections(
        reference_answer,
        known_loss_point_ids=loss_point_ids,
        errors=errors,
        warnings=final_reference_warnings,
        recoverable=False,
    )
    if final_reference_warnings:
        metadata = normalized.get("feedback_metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        existing = _string_list(
            metadata.get("validation_warnings"),
            max_items=FEEDBACK_VALIDATION_WARNING_MAX_ITEMS,
            max_item_chars=FEEDBACK_VALIDATION_WARNING_MAX_CHARS,
        )
        metadata["validation_warnings"] = list(dict.fromkeys([*existing, *final_reference_warnings]))
        normalized["feedback_metadata"] = metadata

    normalized["asset_consistency_check"] = normalized.get("asset_consistency_check", {})
    normalized["answer_coverage"] = normalized.get("answer_coverage", {})
    normalized["answer_change_analysis"] = normalized.get("answer_change_analysis", {})
    normalized["feedback_cards"] = normalized.get("feedback_cards", [])
    normalized["next_recommended_actions"] = normalized.get("next_recommended_actions")
    normalized["trace_refs"] = _string_list(normalized.get("trace_refs"), max_items=20, max_item_chars=160)
    if not normalized["trace_refs"]:
        errors.append("trace_refs_required")
    normalized["feedback_metadata"] = normalized.get("feedback_metadata")
    if not isinstance(normalized["feedback_metadata"], dict):
        errors.append("feedback_metadata_invalid")

    errors.extend(_asset_consistency_check(normalized.get("asset_consistency_check"), require=True))
    errors.extend(_answer_coverage(normalized.get("answer_coverage"), require=True))
    errors.extend(_answer_change_analysis(normalized.get("answer_change_analysis"), require=True))
    errors.extend(
        _feedback_cards(
            normalized.get("feedback_cards"),
            asset_consistency_check=normalized.get("asset_consistency_check"),
            answer_change_analysis=normalized.get("answer_change_analysis"),
            require=True,
        )
    )
    if errors:
        return None, tuple(dict.fromkeys(errors))
    return normalized, ()


def _candidate_pre_validation_warnings(payload: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    score_reasoning = payload.get("score_reasoning")
    if not isinstance(score_reasoning, list) or not score_reasoning:
        warnings.append("score_reasoning_missing")
    same_question_effect = payload.get("same_question_effect")
    if same_question_effect not in (None, "", {}):
        if isinstance(same_question_effect, str):
            if same_question_effect not in _SAME_QUESTION_EFFECT_ENUMS and same_question_effect != "first_attempt":
                warnings.append("same_question_effect_invalid")
        elif not isinstance(same_question_effect, dict):
            warnings.append("same_question_effect_invalid")
    candidates = payload.get("project_asset_update_candidates")
    if candidates not in (None, []):
        if not isinstance(candidates, list):
            warnings.append("project_asset_update_candidates_invalid")
        else:
            for candidate in candidates:
                if not isinstance(candidate, dict):
                    warnings.append("project_asset_update_candidate_invalid")
                elif candidate.get("user_confirmation_required") is not True:
                    warnings.append("project_asset_candidate_user_confirmation_required")
    reference_answer = payload.get("reference_answer")
    if isinstance(reference_answer, dict) and isinstance(reference_answer.get("addresses_loss_point_ids"), list):
        sections = reference_answer.get("sections")
        if isinstance(sections, list) and len(sections) == 1:
            warnings.append("reference_answer_top_level_addresses_loss_point_ids_normalized")
        else:
            warnings.append("reference_answer_top_level_addresses_loss_point_ids_unassigned")
    return warnings


def _append_candidate_reference_answer_recovery_warnings(payload: dict[str, Any], warnings: list[str]) -> None:
    reference_answer = payload.get("reference_answer")
    if not isinstance(reference_answer, dict):
        return
    sections = reference_answer.get("sections")
    if not isinstance(sections, list):
        return
    seen_section_ids: set[str] = set()
    for section in sections:
        if not isinstance(section, dict):
            continue
        section_id = _clean(section.get("section_id") or section.get("id"), max_chars=120)
        if not section_id:
            warnings.append("reference_answer_section_id_generated")
        elif section_id in seen_section_ids:
            warnings.append("reference_answer_section_id_rewritten")
        seen_section_ids.add(section_id)
        if not _clean(section.get("title"), max_chars=240):
            warnings.append("reference_answer_section_title_generated")
        addresses = section.get("addresses_loss_point_ids")
        if addresses is not None and not isinstance(addresses, list):
            warnings.append("reference_answer_addresses_loss_point_ids_invalid")


def _candidate_model_errors(exc: ValidationError) -> tuple[str, ...]:
    errors: list[str] = []
    for issue in exc.errors():
        loc = ".".join(str(part) for part in issue.get("loc", ()))
        if loc == "feedback_text":
            errors.append("feedback_text_required")
        elif loc == "answer_summary":
            errors.append("answer_summary_required")
        elif loc.startswith("loss_points") and loc.endswith("loss_point_id"):
            errors.append("loss_point_identity_unrecoverable")
        elif loc.startswith("loss_points"):
            errors.append("loss_point_invalid")
        elif loc == "score_result":
            errors.append("score_result_required")
        elif loc == "reference_answer":
            errors.append("reference_answer_required")
        elif loc == "reference_answer.sections":
            errors.append("reference_answer_sections_required")
        elif loc.startswith("reference_answer.sections") and loc.endswith("section_id"):
            errors.append("reference_answer_section_identity_unrecoverable")
        elif loc.startswith("reference_answer.sections"):
            errors.append("reference_answer_sections_invalid")
        else:
            errors.append("feedback_payload_schema_invalid")
    return tuple(dict.fromkeys(errors or ["feedback_payload_schema_invalid"]))


def _restore_phase5_score_result_extensions(
    normalized_score_result: dict[str, Any],
    source_score_result: object,
) -> dict[str, Any]:
    restored = dict(normalized_score_result)
    if not isinstance(source_score_result, dict):
        return restored
    for field_name in _PHASE5_SCORE_RESULT_EXTENSION_FIELDS:
        value = source_score_result.get(field_name)
        if isinstance(value, dict):
            restored[field_name] = deepcopy(value)
    return restored


def _final_model_errors(exc: ValidationError) -> tuple[str, ...]:
    errors: list[str] = []
    for issue in exc.errors():
        error_type = str(issue.get("type") or "")
        loc = ".".join(str(part) for part in issue.get("loc", ()))
        if error_type == "extra_forbidden":
            errors.append("feedback_final_unknown_fields")
        elif error_type == "missing":
            errors.append("feedback_final_required_fields_missing")
        elif loc == "status":
            errors.append("feedback_status_invalid")
        elif loc == "reference_answer":
            errors.append("reference_answer_required")
        elif loc == "reference_answer.sections":
            errors.append("reference_answer_sections_required")
        elif loc.startswith("reference_answer.sections") and loc.endswith("section_id"):
            errors.append("reference_answer_section_identity_unrecoverable")
        elif loc.startswith("reference_answer.sections"):
            errors.append("reference_answer_sections_invalid")
        else:
            errors.append("feedback_payload_schema_invalid")
    return tuple(dict.fromkeys(errors or ["feedback_payload_schema_invalid"]))


def _normalize_score_reasoning_for_candidate(value: object, *, warnings: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        warnings.append("score_reasoning_missing")
        return []

    normalized_reasoning: list[dict[str, Any]] = []
    for reason in value:
        if not isinstance(reason, dict):
            warnings.append("score_reasoning_item_invalid")
            continue
        dimension = _clean(reason.get("dimension"), max_chars=80)
        rationale = _clean(reason.get("rationale"), max_chars=2000)
        if not dimension or not rationale:
            warnings.append("score_reasoning_item_fields_missing")
            continue
        item = dict(reason)
        item["dimension"] = dimension
        item["rationale"] = rationale
        normalized_reasoning.append(item)

    if not normalized_reasoning:
        warnings.append("score_reasoning_missing")
    return normalized_reasoning


def _normalize_loss_point_evidence_refs(
    value: object,
    *,
    errors: list[str],
) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        errors.append("loss_points_invalid")
        return []

    normalized_items: list[Any] = []
    for item in value:
        if not isinstance(item, dict):
            normalized_items.append(item)
            continue
        normalized_item = dict(item)
        if "evidence_refs" in normalized_item:
            refs = normalized_item.get("evidence_refs")
            if refs is None:
                normalized_item["evidence_refs"] = []
            elif isinstance(refs, list):
                normalized_item["evidence_refs"] = _string_list(
                    refs,
                    max_items=FEEDBACK_EVIDENCE_REF_MAX_ITEMS,
                    max_item_chars=FEEDBACK_EVIDENCE_REF_MAX_CHARS,
                )
            else:
                errors.append("loss_point_evidence_refs_invalid")
                normalized_item["evidence_refs"] = []
        normalized_items.append(normalized_item)
    return normalized_items


def _normalize_loss_point_ids(value: object) -> None:
    if not isinstance(value, list):
        return
    for item in value:
        if not isinstance(item, dict):
            continue
        if _clean(item.get("loss_point_id"), max_chars=120):
            continue
        alias = _clean(item.get("id") or item.get("loss_id"), max_chars=120)
        if alias:
            item["loss_point_id"] = alias


def _normalize_reference_answer_sections(
    value: object,
    *,
    known_loss_point_ids: set[str],
    errors: list[str],
    warnings: list[str],
    recoverable: bool,
) -> object:
    if not isinstance(value, dict):
        errors.append("reference_answer_required")
        return value

    sections = value.get("sections")
    if not isinstance(sections, list) or not sections:
        errors.append("reference_answer_sections_required")
        return value
    if not all(isinstance(section, dict) for section in sections):
        errors.append("reference_answer_sections_invalid")
        return value

    normalized_sections: list[dict[str, Any]] = []
    seen_section_ids: set[str] = set()
    for index, raw_section in enumerate(sections, start=1):
        section = dict(raw_section)
        content = _clean(section.get("content"), max_chars=FEEDBACK_REFERENCE_SECTION_CONTENT_MAX_CHARS)
        if not content:
            warnings.append("reference_answer_section_content_missing")
            continue
        section["content"] = content

        section_id = _clean(section.get("section_id") or section.get("id"), max_chars=120)
        if not section_id:
            if recoverable:
                section_id = _generated_reference_section_id(index, seen_section_ids)
                warnings.append("reference_answer_section_id_generated")
            else:
                errors.append("reference_answer_section_identity_unrecoverable")
                section_id = _generated_reference_section_id(index, seen_section_ids)
        elif section_id in seen_section_ids:
            if recoverable:
                section_id = _generated_reference_section_id(index, seen_section_ids)
                warnings.append("reference_answer_section_id_rewritten")
            else:
                errors.append("reference_answer_section_id_duplicate")
        seen_section_ids.add(section_id)
        section["section_id"] = section_id
        section.pop("id", None)

        title = _clean(section.get("title"), max_chars=240)
        if not title:
            title = f"参考回答 {index}"
            warnings.append("reference_answer_section_title_generated")
        section["title"] = title

        raw_refs = section.get("addresses_loss_point_ids")
        if raw_refs is None:
            section["addresses_loss_point_ids"] = []
        elif not isinstance(raw_refs, list):
            section["addresses_loss_point_ids"] = []
            warnings.append("reference_answer_addresses_loss_point_ids_invalid")
        else:
            normalized_refs: list[str] = []
            for ref in _string_list(
                raw_refs,
                max_items=FEEDBACK_REFERENCE_LOSS_REF_MAX_ITEMS,
                max_item_chars=FEEDBACK_REFERENCE_LOSS_REF_MAX_CHARS,
            ):
                if ref not in known_loss_point_ids:
                    if recoverable:
                        warnings.append("reference_answer_unknown_loss_point_ref_removed")
                    else:
                        errors.append("reference_answer_unknown_loss_point_ref")
                    continue
                if ref not in normalized_refs:
                    normalized_refs.append(ref)
            section["addresses_loss_point_ids"] = normalized_refs

        normalized_sections.append(section)

    if not normalized_sections:
        errors.append("reference_answer_sections_invalid")

    normalized_reference_answer = dict(value)
    normalized_reference_answer["sections"] = normalized_sections
    return normalized_reference_answer


def _generated_reference_section_id(index: int, seen_section_ids: set[str]) -> str:
    candidate = f"section_{index}"
    suffix = index
    while candidate in seen_section_ids:
        suffix += 1
        candidate = f"section_{suffix}"
    return candidate


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
            errors.append("loss_point_identity_unrecoverable")
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
            errors.append("reference_answer_section_identity_unrecoverable")
        elif section_id in seen_section_ids:
            errors.append("reference_answer_section_id_duplicate")
        seen_section_ids.add(section_id)

        refs = _string_list(
            section.get("addresses_loss_point_ids"),
            max_items=FEEDBACK_REFERENCE_LOSS_REF_MAX_ITEMS,
            max_item_chars=FEEDBACK_REFERENCE_LOSS_REF_MAX_CHARS,
        )
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


def _asset_consistency_check(value: object, *, require: bool) -> list[str]:
    if value in (None, {}):
        return ["asset_consistency_check_required"] if require else []
    if not isinstance(value, dict):
        return ["asset_consistency_check_invalid"]

    errors: list[str] = []
    status = _clean(value.get("status"), max_chars=80)
    if status not in ASSET_CONSISTENCY_STATUSES:
        errors.append("asset_consistency_status_invalid")
    if not isinstance(value.get("checked_asset_refs"), list):
        errors.append("asset_consistency_checked_refs_invalid")
    conflicts = value.get("conflicts")
    if not isinstance(conflicts, list):
        errors.append("asset_consistency_conflicts_invalid")
        conflicts = []
    unsupported_claims = value.get("unsupported_claims")
    if not isinstance(unsupported_claims, list):
        errors.append("asset_consistency_unsupported_claims_invalid")
        unsupported_claims = []
    if not isinstance(value.get("user_clarification_required"), bool):
        errors.append("asset_consistency_user_clarification_required_invalid")
    if status == "conflict" and not conflicts and not unsupported_claims:
        errors.append("asset_consistency_conflict_details_required")
    for conflict in conflicts:
        if not isinstance(conflict, dict):
            errors.append("asset_consistency_conflict_invalid")
            continue
        conflict_type = _clean(conflict.get("conflict_type"), max_chars=80)
        if conflict_type not in ASSET_CONFLICT_TYPES:
            errors.append("asset_consistency_conflict_type_invalid")
        missing = [field for field in _CONFLICT_REQUIRED_FIELDS if not _clean(conflict.get(field), max_chars=500)]
        if "clarification_question" in missing:
            errors.append("asset_consistency_conflict_clarification_required")
        if missing:
            errors.append("asset_consistency_conflict_fields_required")
    for claim in unsupported_claims:
        if not isinstance(claim, dict):
            errors.append("asset_consistency_unsupported_claim_invalid")
            continue
        if not _clean(claim.get("current_answer_claim"), max_chars=500):
            errors.append("asset_consistency_unsupported_claim_required")
    return errors


def _answer_coverage(value: object, *, require: bool) -> list[str]:
    if value in (None, {}):
        return ["answer_coverage_required"] if require else []
    if not isinstance(value, dict):
        return ["answer_coverage_invalid"]
    errors: list[str] = []
    for field_name in (
        "expected_points",
        "covered_points",
        "missing_points",
        "weak_points",
        "contradicted_points",
    ):
        if not isinstance(value.get(field_name), list):
            errors.append("answer_coverage_fields_invalid")
    return errors


def _answer_change_analysis(value: object, *, require: bool) -> list[str]:
    if value in (None, {}):
        return ["answer_change_analysis_required"] if require else []
    if not isinstance(value, dict):
        return ["answer_change_analysis_invalid"]
    errors: list[str] = []
    if not isinstance(value.get("has_prior_attempts"), bool):
        errors.append("answer_change_has_prior_attempts_invalid")
    for field_name in (
        "previous_answer_refs",
        "retained_points",
        "newly_added_points",
        "regressed_points",
        "repeated_loss_points",
        "fixed_loss_points",
    ):
        if not isinstance(value.get(field_name), list):
            errors.append("answer_change_fields_invalid")
    score_delta = value.get("score_delta")
    if score_delta is not None and not _is_number(score_delta):
        errors.append("answer_change_score_delta_invalid")
    if _clean(value.get("trend"), max_chars=80) not in ANSWER_CHANGE_TRENDS:
        errors.append("answer_change_trend_invalid")
    return errors


def _feedback_cards(
    value: object,
    *,
    asset_consistency_check: object,
    answer_change_analysis: object,
    require: bool,
) -> list[str]:
    if value in (None, []):
        return ["feedback_cards_required"] if require else []
    if not isinstance(value, list):
        return ["feedback_cards_invalid"]
    errors: list[str] = []
    card_types: list[str] = []
    for card in value:
        if not isinstance(card, dict):
            errors.append("feedback_card_invalid")
            continue
        card_type = _clean(card.get("card_type") or card.get("type"), max_chars=80)
        if card_type not in FEEDBACK_CARD_TYPES:
            errors.append("feedback_card_type_invalid")
            continue
        card_types.append(card_type)
    order = [FEEDBACK_CARD_TYPES.index(card_type) for card_type in card_types if card_type in FEEDBACK_CARD_TYPES]
    if order != sorted(order):
        errors.append("feedback_cards_order_invalid")
    asset_status = asset_consistency_check.get("status") if isinstance(asset_consistency_check, dict) else None
    if asset_status == "conflict" and card_types[:1] != ["asset_consistency"]:
        errors.append("feedback_cards_asset_consistency_first_required")
    regressed_points = []
    if isinstance(answer_change_analysis, dict):
        regressed_points = answer_change_analysis.get("regressed_points")
    if regressed_points and "answer_change" not in card_types:
        errors.append("feedback_cards_answer_change_required")
    return errors


def _same_question_effect(value: object) -> list[str]:
    if value in (None, {}):
        return []
    if not isinstance(value, dict):
        return ["same_question_effect_invalid"]

    errors: list[str] = []
    for field_name in _SAME_QUESTION_LIST_FIELDS:
        if not isinstance(value.get(field_name), list):
            errors.append("same_question_effect_invalid_fields")
    score_delta = value.get("score_delta")
    if score_delta is not None and not _is_number(score_delta):
        errors.append("same_question_score_delta_invalid")
    return errors


def _normalize_candidate_same_question_effect(value: object) -> tuple[dict[str, Any], list[str]]:
    if isinstance(value, dict):
        normalized = dict(value)
        for field_name in _SAME_QUESTION_LIST_FIELDS:
            if not isinstance(normalized.get(field_name), list):
                normalized[field_name] = []
        if "trend" in normalized:
            trend = _clean(normalized.get("trend"), max_chars=80)
            if trend:
                normalized["trend"] = trend
        return normalized, []
    trend = _clean(value, max_chars=80)
    if trend in _SAME_QUESTION_EFFECT_ENUMS:
        normalized_trend = "unchanged" if trend == "not_applicable" else trend
        return (
            {
                "trend": normalized_trend,
                "improved_points": [],
                "repeated_loss_point_ids": [],
                "regressed_points": [],
                "next_retry_focus": [],
                "score_delta": None,
            },
            [],
        )
    return {}, ["same_question_effect_invalid"]


def _normalize_candidate_project_asset_update_candidates(value: object) -> tuple[list[dict[str, Any]], list[str]]:
    if value in (None, []):
        return [], []
    if not isinstance(value, list):
        return [], ["project_asset_update_candidates_invalid"]

    normalized: list[dict[str, Any]] = []
    warnings: list[str] = []
    for candidate in value:
        if not isinstance(candidate, dict):
            warnings.append("project_asset_update_candidate_invalid")
            continue
        if candidate.get("candidate_type") != "project_asset_update_candidate":
            warnings.append("project_asset_candidate_type_invalid")
            continue
        item = dict(candidate)
        if item.get("user_confirmation_required") is not True:
            warnings.append("project_asset_candidate_user_confirmation_required")
            item["user_confirmation_required"] = True
        for field_name in _FORMAL_ASSET_WRITE_FLAGS:
            if item.pop(field_name, None) is True:
                warnings.append("project_asset_candidate_formal_write_forbidden")
        for field_name in _FULL_ASSET_BODY_FIELDS:
            if field_name in item:
                item.pop(field_name, None)
                warnings.append("project_asset_candidate_full_asset_body_forbidden")
        target_asset_ref = item.get("target_asset_ref")
        if target_asset_ref is not None and not _is_reference_object(target_asset_ref):
            item.pop("target_asset_ref", None)
            warnings.append("project_asset_candidate_target_ref_invalid")
        normalized.append(item)
    return normalized, warnings


def _optional_enhancement_warnings(payload: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for field_name, expected_type in _OPTIONAL_ENHANCED_FIELD_TYPES.items():
        if field_name not in payload:
            continue
        value = payload.get(field_name)
        if value in (None, {}, []):
            continue
        if not isinstance(value, expected_type):
            warnings.append(f"{field_name}_invalid")
            payload.pop(field_name, None)
    return warnings


def _append_validation_warnings(payload: dict[str, Any], warnings: list[str]) -> None:
    deduped = list(dict.fromkeys(warning for warning in warnings if warning))
    if not deduped:
        return
    metadata = payload.get("feedback_metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    existing = _string_list(
        metadata.get("validation_warnings"),
        max_items=FEEDBACK_VALIDATION_WARNING_MAX_ITEMS,
        max_item_chars=FEEDBACK_VALIDATION_WARNING_MAX_CHARS,
    )
    metadata["validation_warnings"] = list(dict.fromkeys([*existing, *deduped]))
    payload["feedback_metadata"] = metadata


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
            key_text = _normalize_unsafe_marker_text(key)
            if key_text in _UNSAFE_KEY_MARKERS:
                return True
            if _contains_unsafe_marker(nested):
                return True
        return False
    if isinstance(value, (list, tuple)):
        return any(_contains_unsafe_marker(item) for item in value)
    if isinstance(value, str):
        normalized = _normalize_unsafe_marker_text(value)
        if any(marker in normalized for marker in _UNSAFE_VALUE_MARKERS):
            return True
        return any(pattern.search(value) for pattern in _UNSAFE_VALUE_PATTERNS)
    return False


def _normalize_unsafe_marker_text(value: object) -> str:
    return re.sub(r"[\s-]+", "_", str(value).strip().lower())


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
