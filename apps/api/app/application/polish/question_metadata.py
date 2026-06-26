"""Internal metadata model for evidence-aware polish questions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from app.application.polish.context_hygiene import (
    CONTEXT_HYGIENE_STATUSES,
    normalize_context_hygiene_metadata,
)


QUESTION_METADATA_SCHEMA_ID = "polish_question_metadata"
QUESTION_METADATA_SCHEMA_VERSION = "1"
BUILDER_VERSION = "evidence-aware-question-builder-v1"
VALIDATOR_VERSION = "question-quality-validator-v2"
SIGNAL_VERSION = "evidence-signals-v1"
FORBIDDEN_NESTED_METADATA_KEYS = {
    "prompt",
    "raw_prompt",
    "system_prompt",
    "developer_prompt",
    "user_prompt",
    "completion",
    "provider_payload",
    "provider_response",
    "raw_completion",
    "raw_provider_payload",
    "raw_provider_response",
    "full_resume",
    "full_jd",
    "primary_evidence_text",
}


@dataclass(frozen=True)
class QuestionMetadata:
    question_pattern: str | None
    scenario_constraint_summary: str | None
    expected_answer_dimensions: tuple[str, ...]
    quality_score: int | None
    quality_warnings: tuple[str, ...]
    confidence_level: str | None
    low_confidence_flags: tuple[str, ...]
    evidence_signal_refs: tuple[str, ...]
    anti_repeat_refs: tuple[str, ...]
    source_availability: str | None = None
    primary_question_evidence: dict[str, Any] | None = None
    primary_question_evidence_ref: str | None = None
    claim_mode: str | None = None
    grounding_gate_result: str | None = None
    grounding_gate_issues: tuple[str, ...] = ()
    grounding_status: str | None = None
    grounding_validation_errors: tuple[str, ...] = ()
    grounding_blocking_errors: tuple[str, ...] = ()
    grounding_warnings: tuple[str, ...] = ()
    grounding_blocking_bypassed: bool = False
    manual_review_required: bool = False
    manual_review_reason: str | None = None
    generated_at: str | None = None
    generation_mode: str | None = None
    request_source: str | None = None
    selected_primary_category_ref: str | None = None
    selected_secondary_category_ref: str | None = None
    selected_progress_node_ref: str | None = None
    selected_category_path: tuple[str, ...] = ()
    parent_question_id: str | None = None
    parent_answer_id: str | None = None
    parent_feedback_id: str | None = None
    authorized_feedback_id: str | None = None
    authorized_answer_id: str | None = None
    authorized_parent_question_id: str | None = None
    next_question_execution_grant: dict[str, Any] | None = None
    exclude_question_refs: tuple[str, ...] = ()
    completed_focus_refs: tuple[str, ...] = ()
    focus_dimension: str | None = None
    focus_key: str | None = None
    template_signature: str | None = None
    blueprint_signature: str | None = None
    duplicate_gate_result: str | None = None
    similarity_checked: bool = False
    max_similarity_in_same_category: float | None = None
    mastery_exception_used: bool = False
    follow_up_reason: str | None = None
    follow_up_target_dimension: str | None = None
    follow_up_coverage_matrix: dict[str, Any] | None = None
    follow_up_focus_source: str | None = None
    recommended_follow_up_action: str | None = None
    follow_up_completion_status: str | None = None
    context_hygiene_status: str = "unknown"
    safe_context_metadata: dict[str, Any] | None = None
    fallback_reason: str | None = None
    validation_signals: dict[str, Any] | None = None
    builder_version: str = BUILDER_VERSION
    validator_version: str = VALIDATOR_VERSION
    signal_version: str = SIGNAL_VERSION
    schema_id: str = QUESTION_METADATA_SCHEMA_ID
    schema_version: str = QUESTION_METADATA_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "builder_version": self.builder_version,
            "validator_version": self.validator_version,
            "signal_version": self.signal_version,
            "question_pattern": self.question_pattern,
            "scenario_constraint_summary": self.scenario_constraint_summary,
            "expected_answer_dimensions": list(self.expected_answer_dimensions),
            "quality_score": self.quality_score,
            "quality_warnings": list(self.quality_warnings),
            "confidence_level": self.confidence_level,
            "low_confidence_flags": list(self.low_confidence_flags),
            "evidence_signal_refs": list(self.evidence_signal_refs),
            "anti_repeat_refs": list(self.anti_repeat_refs),
            "source_availability": self.source_availability,
            "primary_question_evidence": self.primary_question_evidence,
            "primary_question_evidence_ref": self.primary_question_evidence_ref,
            "claim_mode": self.claim_mode,
            "grounding_gate_result": self.grounding_gate_result,
            "grounding_gate_issues": list(self.grounding_gate_issues),
            "grounding_status": self.grounding_status,
            "grounding_validation_errors": list(self.grounding_validation_errors),
            "grounding_blocking_errors": list(self.grounding_blocking_errors),
            "grounding_warnings": list(self.grounding_warnings),
            "grounding_blocking_bypassed": self.grounding_blocking_bypassed,
            "manual_review_required": self.manual_review_required,
            "manual_review_reason": self.manual_review_reason,
            "generated_at": self.generated_at,
            "generation_mode": self.generation_mode,
            "request_source": self.request_source,
            "selected_primary_category_ref": self.selected_primary_category_ref,
            "selected_secondary_category_ref": self.selected_secondary_category_ref,
            "selected_progress_node_ref": self.selected_progress_node_ref,
            "selected_category_path": list(self.selected_category_path),
            "parent_question_id": self.parent_question_id,
            "parent_answer_id": self.parent_answer_id,
            "parent_feedback_id": self.parent_feedback_id,
            "authorized_feedback_id": self.authorized_feedback_id,
            "authorized_answer_id": self.authorized_answer_id,
            "authorized_parent_question_id": self.authorized_parent_question_id,
            "next_question_execution_grant": self.next_question_execution_grant,
            "exclude_question_refs": list(self.exclude_question_refs),
            "completed_focus_refs": list(self.completed_focus_refs),
            "focus_dimension": self.focus_dimension,
            "focus_key": self.focus_key,
            "template_signature": self.template_signature,
            "blueprint_signature": self.blueprint_signature,
            "duplicate_gate_result": self.duplicate_gate_result,
            "similarity_checked": self.similarity_checked,
            "max_similarity_in_same_category": self.max_similarity_in_same_category,
            "mastery_exception_used": self.mastery_exception_used,
            "follow_up_reason": self.follow_up_reason,
            "follow_up_target_dimension": self.follow_up_target_dimension,
            "follow_up_coverage_matrix": self.follow_up_coverage_matrix or {},
            "follow_up_focus_source": self.follow_up_focus_source,
            "recommended_follow_up_action": self.recommended_follow_up_action,
            "follow_up_completion_status": self.follow_up_completion_status,
            "context_hygiene_status": self.context_hygiene_status,
            "safe_context_metadata": self.safe_context_metadata or {},
            "fallback_reason": self.fallback_reason,
            "validation_signals": self.validation_signals or {},
        }


def empty_question_metadata() -> QuestionMetadata:
    return QuestionMetadata(
        question_pattern=None,
        scenario_constraint_summary=None,
        expected_answer_dimensions=(),
        quality_score=None,
        quality_warnings=(),
        confidence_level=None,
        low_confidence_flags=(),
        evidence_signal_refs=(),
        anti_repeat_refs=(),
        context_hygiene_status="unknown",
        safe_context_metadata={},
        fallback_reason="legacy_or_malformed_metadata",
        validation_signals={},
    )


def normalize_question_metadata(raw: object) -> dict[str, Any]:
    """Return a safe C-lite metadata object from persisted or legacy payloads."""

    payload = _metadata_payload(raw)
    if not payload:
        return empty_question_metadata().to_dict()

    context_hygiene = normalize_context_hygiene_metadata(payload)
    normalized = {
        "schema_id": _string_or_none(payload.get("schema_id")) or QUESTION_METADATA_SCHEMA_ID,
        "schema_version": _string_or_none(payload.get("schema_version")) or QUESTION_METADATA_SCHEMA_VERSION,
        "builder_version": _string_or_none(payload.get("builder_version")) or BUILDER_VERSION,
        "validator_version": _string_or_none(payload.get("validator_version")) or VALIDATOR_VERSION,
        "signal_version": _string_or_none(payload.get("signal_version")) or SIGNAL_VERSION,
        "question_pattern": _string_or_none(payload.get("question_pattern")),
        "scenario_constraint_summary": _string_or_none(payload.get("scenario_constraint_summary"), max_chars=500),
        "expected_answer_dimensions": _string_list(payload.get("expected_answer_dimensions")),
        "quality_score": _quality_score_or_none(payload.get("quality_score")),
        "quality_warnings": _string_list(payload.get("quality_warnings")),
        "confidence_level": _string_or_none(payload.get("confidence_level")),
        "low_confidence_flags": _string_list(payload.get("low_confidence_flags")),
        "evidence_signal_refs": _string_list(payload.get("evidence_signal_refs")),
        "anti_repeat_refs": _string_list(payload.get("anti_repeat_refs")),
        "source_availability": _string_or_none(payload.get("source_availability")),
        "primary_question_evidence": _safe_primary_question_evidence(payload.get("primary_question_evidence")),
        "primary_question_evidence_ref": _string_or_none(
            payload.get("primary_question_evidence_ref"), max_chars=120
        ),
        "claim_mode": _string_or_none(payload.get("claim_mode"), max_chars=80),
        "grounding_gate_result": _string_or_none(payload.get("grounding_gate_result"), max_chars=80),
        "grounding_gate_issues": _string_list(payload.get("grounding_gate_issues")),
        "grounding_status": _string_or_none(payload.get("grounding_status"), max_chars=80),
        "grounding_validation_errors": _string_list(payload.get("grounding_validation_errors")),
        "grounding_blocking_errors": _string_list(payload.get("grounding_blocking_errors")),
        "grounding_warnings": _string_list(payload.get("grounding_warnings")),
        "grounding_blocking_bypassed": _bool_or_false(payload.get("grounding_blocking_bypassed")),
        "manual_review_required": _bool_or_false(payload.get("manual_review_required")),
        "manual_review_reason": _string_or_none(payload.get("manual_review_reason"), max_chars=160),
        "generated_at": _string_or_none(payload.get("generated_at"), max_chars=80),
        "generation_mode": _string_or_none(payload.get("generation_mode"), max_chars=80),
        "request_source": _string_or_none(payload.get("request_source"), max_chars=120),
        "selected_primary_category_ref": _string_or_none(
            payload.get("selected_primary_category_ref"), max_chars=120
        ),
        "selected_secondary_category_ref": _string_or_none(
            payload.get("selected_secondary_category_ref"), max_chars=120
        ),
        "selected_progress_node_ref": _string_or_none(payload.get("selected_progress_node_ref"), max_chars=120),
        "selected_category_path": _string_list(payload.get("selected_category_path")),
        "parent_question_id": _string_or_none(payload.get("parent_question_id"), max_chars=120),
        "parent_answer_id": _string_or_none(payload.get("parent_answer_id"), max_chars=120),
        "parent_feedback_id": _string_or_none(payload.get("parent_feedback_id"), max_chars=120),
        "authorized_feedback_id": _string_or_none(payload.get("authorized_feedback_id"), max_chars=120),
        "authorized_answer_id": _string_or_none(payload.get("authorized_answer_id"), max_chars=120),
        "authorized_parent_question_id": _string_or_none(
            payload.get("authorized_parent_question_id"), max_chars=120
        ),
        "next_question_execution_grant": _safe_next_question_execution_grant_snapshot(
            payload.get("next_question_execution_grant")
        ),
        "exclude_question_refs": _string_list(payload.get("exclude_question_refs")),
        "completed_focus_refs": _string_list(payload.get("completed_focus_refs")),
        "focus_dimension": _string_or_none(payload.get("focus_dimension"), max_chars=160),
        "focus_key": _string_or_none(payload.get("focus_key"), max_chars=160),
        "template_signature": _string_or_none(payload.get("template_signature"), max_chars=240),
        "blueprint_signature": _string_or_none(payload.get("blueprint_signature"), max_chars=240),
        "duplicate_gate_result": _string_or_none(payload.get("duplicate_gate_result"), max_chars=120),
        "similarity_checked": _bool_or_false(payload.get("similarity_checked")),
        "max_similarity_in_same_category": _float_or_none(payload.get("max_similarity_in_same_category")),
        "mastery_exception_used": _bool_or_false(payload.get("mastery_exception_used")),
        "follow_up_reason": _string_or_none(payload.get("follow_up_reason"), max_chars=240),
        "follow_up_target_dimension": _string_or_none(payload.get("follow_up_target_dimension"), max_chars=240),
        "follow_up_coverage_matrix": _safe_json_dict(
            payload.get("follow_up_coverage_matrix"),
            max_items=64,
            max_depth=4,
        ),
        "follow_up_focus_source": _string_or_none(payload.get("follow_up_focus_source"), max_chars=120),
        "recommended_follow_up_action": _string_or_none(
            payload.get("recommended_follow_up_action"),
            max_chars=120,
        ),
        "follow_up_completion_status": _string_or_none(
            payload.get("follow_up_completion_status"),
            max_chars=120,
        ),
        "context_hygiene_status": context_hygiene["context_hygiene_status"],
        "safe_context_metadata": context_hygiene["safe_context_metadata"],
        "fallback_reason": context_hygiene["fallback_reason"],
        "validation_signals": context_hygiene["validation_signals"],
    }
    canonical_keys = {
        "source_support_level",
        "canonical_project_assets_available",
        "canonical_project_asset_refs",
    }
    if any(key in payload for key in canonical_keys):
        normalized.update(
            {
                "source_support_level": _string_or_none(payload.get("source_support_level"), max_chars=120),
                "canonical_project_assets_available": _bool_or_false(
                    payload.get("canonical_project_assets_available")
                ),
                "canonical_project_asset_refs": _string_list(
                    payload.get("canonical_project_asset_refs"), max_item_chars=160
                ),
            }
        )

    adaptive_keys = {
        "adaptive_interview_flow",
        "adaptive_difficulty_level",
        "adaptive_learning_path",
        "adaptive_session_structure",
    }
    if any(key in payload for key in adaptive_keys):
        normalized.update(
            {
                "adaptive_interview_flow": _safe_json_dict(
                    payload.get("adaptive_interview_flow"),
                    max_items=80,
                    max_depth=6,
                ),
                "adaptive_difficulty_level": _string_or_none(
                    payload.get("adaptive_difficulty_level"),
                    max_chars=80,
                ),
                "adaptive_learning_path": _safe_json_dict(
                    payload.get("adaptive_learning_path"),
                    max_items=80,
                    max_depth=6,
                ),
                "adaptive_session_structure": _safe_json_list(
                    payload.get("adaptive_session_structure"),
                    max_items=16,
                    max_depth=5,
                ),
            }
        )

    step7_contract_keys = {
        "policy_signed_next_action",
        "follow_up_intent_classification",
        "same_node_follow_up_contract",
        "same_node_next_question_contract",
        "next_question_response_contract",
    }
    if any(key in payload for key in step7_contract_keys):
        normalized.update(
            {
                "policy_signed_next_action": _safe_json_dict(
                    payload.get("policy_signed_next_action"),
                    max_items=24,
                    max_depth=4,
                ),
                "follow_up_intent_classification": _safe_json_dict(
                    payload.get("follow_up_intent_classification"),
                    max_items=24,
                    max_depth=4,
                ),
                "same_node_follow_up_contract": _safe_json_dict(
                    payload.get("same_node_follow_up_contract"),
                    max_items=32,
                    max_depth=4,
                ),
                "same_node_next_question_contract": _safe_json_dict(
                    payload.get("same_node_next_question_contract"),
                    max_items=32,
                    max_depth=4,
                ),
                "next_question_response_contract": _safe_json_dict(
                    payload.get("next_question_response_contract"),
                    max_items=32,
                    max_depth=4,
                ),
            }
        )

    prompt_keys = {
        "prompt_asset_version",
        "prompt_schema_id",
        "prompt_schema_version",
        "prompt_policy_version",
        "prompt_policy_source",
        "prompt_policy_source_type",
        "prompt_policy_source_version",
        "prompt_policy_source_chain",
        "prompt_policy_fallback",
        "prompt_policy_resolution_context",
        "prompt_policy_item_sources",
        "prompt_input_digest",
        "prompt_evidence_refs",
        "prompt_safety_summary",
    }
    if any(key in payload for key in prompt_keys):
        normalized.update(
            {
                "prompt_asset_version": _string_or_none(payload.get("prompt_asset_version"), max_chars=120),
                "prompt_schema_id": _string_or_none(payload.get("prompt_schema_id"), max_chars=120),
                "prompt_schema_version": _string_or_none(payload.get("prompt_schema_version"), max_chars=80),
                "prompt_policy_version": _string_or_none(payload.get("prompt_policy_version"), max_chars=120),
                "prompt_policy_source": _string_or_none(payload.get("prompt_policy_source"), max_chars=120),
                "prompt_policy_source_type": _string_or_none(
                    payload.get("prompt_policy_source_type"), max_chars=120
                ),
                "prompt_policy_source_version": _string_or_none(
                    payload.get("prompt_policy_source_version"), max_chars=120
                ),
                "prompt_policy_source_chain": _string_list(
                    payload.get("prompt_policy_source_chain"), max_item_chars=160
                ),
                "prompt_policy_fallback": _bool_or_false(payload.get("prompt_policy_fallback")),
                "prompt_policy_resolution_context": _safe_string_map(
                    payload.get("prompt_policy_resolution_context")
                ),
                "prompt_policy_item_sources": _safe_nested_string_map(
                    payload.get("prompt_policy_item_sources")
                ),
                "prompt_input_digest": _string_or_none(payload.get("prompt_input_digest"), max_chars=160),
                "prompt_evidence_refs": _string_list(payload.get("prompt_evidence_refs"), max_item_chars=160),
                "prompt_safety_summary": _safe_prompt_safety_summary(payload.get("prompt_safety_summary")),
            }
        )
    llm_keys = {
        "llm_task_type",
        "prompt_version",
        "question_schema_version",
        "llm_output_validation_status",
        "llm_generation_mode",
        "fallback_reason",
        "fallback_visible",
        "graph_fallback_reason",
        "graph_status",
        "provider_status",
        "phase_results",
        "tool_results",
        "validator_result",
        "repair_attempted",
        "provider_summary",
        "model_summary",
        "validation_errors",
        "redaction_boundary",
        "llm_difficulty",
        "llm_skill_dimension",
        "llm_expected_signal",
        "llm_confidence",
        "llm_missing_context",
        "llm_clarification_needed",
    }
    llm_trigger_keys = llm_keys - {"fallback_reason"}
    if any(key in payload for key in llm_trigger_keys):
        normalized.update(
            {
                "llm_task_type": _string_or_none(payload.get("llm_task_type"), max_chars=120),
                "prompt_version": _string_or_none(payload.get("prompt_version"), max_chars=120),
                "question_schema_version": _int_or_none(payload.get("question_schema_version")),
                "llm_output_validation_status": _string_or_none(
                    payload.get("llm_output_validation_status"), max_chars=80
                ),
                "llm_generation_mode": _string_or_none(payload.get("llm_generation_mode"), max_chars=80),
                "fallback_reason": _string_or_none(payload.get("fallback_reason"), max_chars=120),
                "fallback_visible": _bool_or_false(payload.get("fallback_visible")),
                "graph_fallback_reason": _string_or_none(payload.get("graph_fallback_reason"), max_chars=120),
                "graph_status": _string_or_none(payload.get("graph_status"), max_chars=120),
                "provider_status": _string_or_none(payload.get("provider_status"), max_chars=120),
                "phase_results": _safe_phase_results(payload.get("phase_results")),
                "tool_results": _safe_tool_results(payload.get("tool_results")),
                "validator_result": _safe_validator_result(payload.get("validator_result")),
                "repair_attempted": _bool_or_false(payload.get("repair_attempted")),
                "provider_summary": _safe_summary_dict(payload.get("provider_summary")),
                "model_summary": _safe_summary_dict(payload.get("model_summary")),
                "validation_errors": _validation_errors(payload.get("validation_errors")),
                "redaction_boundary": _string_or_none(payload.get("redaction_boundary"), max_chars=160),
                "llm_difficulty": _string_or_none(payload.get("llm_difficulty"), max_chars=80),
                "llm_skill_dimension": _string_or_none(payload.get("llm_skill_dimension"), max_chars=160),
                "llm_expected_signal": _string_or_none(payload.get("llm_expected_signal"), max_chars=300),
                "llm_confidence": _string_or_none(payload.get("llm_confidence"), max_chars=80),
                "llm_missing_context": _string_list(payload.get("llm_missing_context"), max_item_chars=240),
                "llm_clarification_needed": (
                    bool(payload.get("llm_clarification_needed"))
                    if isinstance(payload.get("llm_clarification_needed"), bool)
                    else None
                ),
            }
        )
    return normalized


def next_question_execution_grant_snapshot_to_metadata(snapshot: object) -> dict[str, Any]:
    normalized = _safe_next_question_execution_grant_snapshot(snapshot)
    if normalized is None:
        return {}
    return {"next_question_execution_grant": normalized}


def question_metadata_to_dict(raw: object) -> dict[str, Any]:
    if isinstance(raw, QuestionMetadata):
        return normalize_question_metadata(raw.to_dict())
    to_dict = getattr(raw, "to_dict", None)
    if callable(to_dict):
        try:
            return normalize_question_metadata(to_dict())
        except Exception:
            return empty_question_metadata().to_dict()
    return normalize_question_metadata(raw)


def _safe_next_question_execution_grant_snapshot(value: object) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        source = value
    else:
        to_dict = getattr(value, "to_dict", None)
        if callable(to_dict):
            candidate = to_dict()
            source = candidate if isinstance(candidate, dict) else {}
        else:
            source = {}
    grant_id = _string_or_none(source.get("grant_id"), max_chars=160)
    if grant_id is None:
        return None
    return {
        "schema_id": _string_or_none(source.get("schema_id"), max_chars=160)
        or "polish_next_question_execution_grant_snapshot",
        "schema_version": _string_or_none(source.get("schema_version"), max_chars=40) or "1",
        "grant_id": grant_id,
        "session_id": _string_or_none(source.get("session_id"), max_chars=160),
        "feedback_id": _string_or_none(source.get("feedback_id"), max_chars=160),
        "answer_id": _string_or_none(source.get("answer_id"), max_chars=160),
        "parent_question_id": _string_or_none(source.get("parent_question_id"), max_chars=160),
        "selected_progress_node_ref": _string_or_none(
            source.get("selected_progress_node_ref"), max_chars=160
        ),
        "allowed_progress_node_refs": _string_list(
            source.get("allowed_progress_node_refs"), max_item_chars=160
        ),
        "freshness_marker": _string_or_none(source.get("freshness_marker"), max_chars=240),
        "reason_codes": _string_list(source.get("reason_codes"), max_item_chars=120),
        "issued_at": _string_or_none(source.get("issued_at"), max_chars=80),
        "expires_at": _string_or_none(source.get("expires_at"), max_chars=80),
        "consumed_at": _string_or_none(source.get("consumed_at"), max_chars=80),
        "lifecycle_state": _string_or_none(source.get("lifecycle_state"), max_chars=80),
    }


def build_follow_up_coverage_decision(
    *,
    feedback_payload: object,
    expected_answer_dimensions: object,
    completed_focus_refs: tuple[str, ...],
    used_focus_refs: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Build follow-up coverage matrix and focus decision from structured feedback."""

    matrix = _build_follow_up_coverage_matrix(
        feedback_payload=feedback_payload,
        expected_answer_dimensions=expected_answer_dimensions,
        completed_focus_refs=completed_focus_refs,
        used_focus_refs=used_focus_refs,
    )
    focus = _select_follow_up_focus(matrix)
    return {"coverage_matrix": matrix, "focus": focus}


def merge_follow_up_completed_focus_refs(
    follow_up_context: dict[str, Any],
    current_refs: tuple[str, ...],
) -> tuple[str, ...]:
    matrix = follow_up_context.get("coverage_matrix")
    matrix_refs = matrix.get("completed_focus_refs") if isinstance(matrix, dict) else ()
    return tuple(_unique_texts([*current_refs, *_string_list(matrix_refs, max_item_chars=160)]))


def sync_follow_up_completed_focus_refs(
    follow_up_context: dict[str, Any],
    completed_focus_refs: tuple[str, ...],
) -> None:
    refs = list(_unique_texts(completed_focus_refs, max_chars=160))
    follow_up_context["completed_focus_refs"] = refs
    matrix = follow_up_context.get("coverage_matrix")
    if isinstance(matrix, dict):
        matrix["completed_focus_refs"] = refs


def _build_follow_up_coverage_matrix(
    *,
    feedback_payload: object,
    expected_answer_dimensions: object,
    completed_focus_refs: tuple[str, ...],
    used_focus_refs: tuple[str, ...],
) -> dict[str, Any]:
    payload = feedback_payload if isinstance(feedback_payload, dict) else {}
    answer_coverage = payload.get("answer_coverage") if isinstance(payload.get("answer_coverage"), dict) else {}
    answer_change = (
        payload.get("answer_change_analysis")
        if isinstance(payload.get("answer_change_analysis"), dict)
        else {}
    )
    asset_check = (
        payload.get("asset_consistency_check")
        if isinstance(payload.get("asset_consistency_check"), dict)
        else {}
    )

    coverage_available = bool(answer_coverage)
    expected_points = _follow_up_text_list(answer_coverage.get("expected_points"))
    if not expected_points:
        expected_points = _follow_up_text_list(expected_answer_dimensions)
    covered_points = _follow_up_text_list(answer_coverage.get("covered_points"))
    missing_points = _filter_covered_points(
        _follow_up_text_list(answer_coverage.get("missing_points")),
        covered_points,
    )
    weak_points = _filter_covered_points(
        _follow_up_text_list(answer_coverage.get("weak_points")),
        covered_points,
    )
    contradicted_points = _filter_covered_points(
        _follow_up_text_list(answer_coverage.get("contradicted_points")),
        covered_points,
    )
    if not missing_points:
        legacy_missing = [
            _string_or_none(
                item.get("title") or item.get("dimension_id") or item.get("expected_dimension"),
                max_chars=240,
            )
            for item in _dict_list(payload.get("missing_answer_dimensions"))
        ]
        missing_points = _filter_covered_points(
            [item for item in legacy_missing if item],
            covered_points,
        )

    regressed_points = _follow_up_text_list(answer_change.get("regressed_points"))
    fixed_loss_points = _follow_up_text_list(answer_change.get("fixed_loss_points"), max_chars=120)
    repeated_loss_points = _follow_up_text_list(answer_change.get("repeated_loss_points"), max_chars=120)
    asset_conflicts = _follow_up_asset_conflicts(asset_check)
    completed_refs = list(_unique_texts(completed_focus_refs, max_chars=160))
    for point in covered_points:
        completed_refs.extend(
            (
                _follow_up_focus_key("missing_point", point),
                _follow_up_focus_key("weak_point", point),
                _follow_up_focus_key("expected_point", point),
            )
        )
    for loss_point_id in [*fixed_loss_points, *repeated_loss_points]:
        completed_refs.append(_follow_up_focus_key("loss_point", loss_point_id))

    return {
        "expected_points": expected_points,
        "covered_points": covered_points,
        "missing_points": missing_points,
        "weak_points": weak_points,
        "contradicted_points": contradicted_points,
        "regressed_points": regressed_points,
        "fixed_loss_points": fixed_loss_points,
        "repeated_loss_points": repeated_loss_points,
        "asset_conflicts": asset_conflicts,
        "completed_focus_refs": _unique_texts(completed_refs, max_chars=160),
        "used_focus_refs": list(_unique_texts(used_focus_refs, max_chars=160)),
        "focus_key": None,
        "coverage_available": coverage_available,
    }


def _select_follow_up_focus(matrix: dict[str, Any]) -> dict[str, str]:
    completed_refs = set(_string_list(matrix.get("completed_focus_refs"), max_item_chars=160))
    completed_refs.update(_string_list(matrix.get("used_focus_refs"), max_item_chars=160))
    candidates: list[dict[str, str]] = []
    for conflict in _dict_list(matrix.get("asset_conflicts")):
        candidates.append(
            _follow_up_focus_candidate(
                source_type="asset_conflict",
                target_dimension=_asset_conflict_focus_text(conflict),
                follow_up_reason="asset_conflict",
                recommended_action="clarify_asset_conflict",
            )
        )
    candidates.extend(
        _follow_up_point_candidates(
            matrix.get("regressed_points"),
            source_type="regressed_point",
            follow_up_reason="regressed_point",
            recommended_action="retry_same_question_preserve_regressed_points",
        )
    )
    candidates.extend(
        _follow_up_point_candidates(
            matrix.get("missing_points"),
            source_type="missing_point",
            follow_up_reason="missing_point",
            recommended_action="continue_same_question",
        )
    )
    candidates.extend(
        _follow_up_point_candidates(
            matrix.get("weak_points"),
            source_type="weak_point",
            follow_up_reason="weak_point",
            recommended_action="continue_same_question",
        )
    )
    prior_focus_points = [
        *_follow_up_text_list(matrix.get("regressed_points")),
        *_follow_up_text_list(matrix.get("missing_points")),
        *_follow_up_text_list(matrix.get("weak_points")),
        *_follow_up_text_list(matrix.get("contradicted_points")),
    ]
    expected_uncovered = [
        point
        for point in _follow_up_text_list(matrix.get("expected_points"))
        if not _contains_similar_text(_follow_up_text_list(matrix.get("covered_points")), point)
        and not _contains_similar_text(prior_focus_points, point)
    ]
    candidates.extend(
        _follow_up_point_candidates(
            expected_uncovered,
            source_type="expected_point",
            follow_up_reason="expected_point",
            recommended_action="continue_same_question",
        )
    )
    if candidates:
        for candidate in candidates:
            if candidate["focus_key"] not in completed_refs:
                matrix["focus_key"] = candidate["focus_key"]
                matrix["focus_source"] = candidate["focus_source"]
                matrix["recommended_action"] = candidate["recommended_action"]
                return {**candidate, "completion_status": "focus_pending"}
        return _completed_follow_up_focus(matrix)
    if matrix.get("coverage_available") and matrix.get("expected_points"):
        return _completed_follow_up_focus(matrix)
    fallback = _follow_up_focus_candidate(
        source_type="controlled_fallback",
        target_dimension="失败路径、边界和验证指标",
        follow_up_reason="category_uncovered_direction",
        recommended_action="continue_same_question",
    )
    matrix["focus_key"] = fallback["focus_key"]
    matrix["focus_source"] = fallback["focus_source"]
    matrix["recommended_action"] = fallback["recommended_action"]
    return {**fallback, "completion_status": "focus_pending"}


def _completed_follow_up_focus(matrix: dict[str, Any]) -> dict[str, str]:
    completed = _follow_up_focus_candidate(
        source_type="completed",
        target_dimension="所有追问焦点已完成",
        follow_up_reason="all_focus_completed",
        recommended_action="focus_complete",
    )
    matrix["focus_key"] = completed["focus_key"]
    matrix["focus_source"] = completed["focus_source"]
    matrix["recommended_action"] = completed["recommended_action"]
    return {**completed, "completion_status": "all_focus_completed"}


def _follow_up_point_candidates(
    value: object,
    *,
    source_type: str,
    follow_up_reason: str,
    recommended_action: str,
) -> list[dict[str, str]]:
    return [
        _follow_up_focus_candidate(
            source_type=source_type,
            target_dimension=point,
            follow_up_reason=follow_up_reason,
            recommended_action=recommended_action,
        )
        for point in _follow_up_text_list(value)
    ]


def _follow_up_focus_candidate(
    *,
    source_type: str,
    target_dimension: str,
    follow_up_reason: str,
    recommended_action: str,
) -> dict[str, str]:
    target = _compact_follow_up_target(target_dimension) or "失败路径、边界和验证指标"
    return {
        "focus_key": _follow_up_focus_key(source_type, target),
        "focus_source": source_type,
        "target_dimension": target,
        "follow_up_reason": follow_up_reason,
        "recommended_action": recommended_action,
    }


def _follow_up_focus_key(source_type: str, value: str) -> str:
    safe_source = _string_or_none(source_type, max_chars=80) or "controlled_fallback"
    seed_value = _string_or_none(value, max_chars=240) or "follow_up"
    seed = f"{safe_source}:{seed_value}"
    return f"focus_{safe_source}_{sha256(seed.encode('utf-8')).hexdigest()[:12]}"


def _follow_up_text_list(value: object, *, max_chars: int = 240) -> list[str]:
    return _string_list(value, max_item_chars=max_chars)


def _follow_up_asset_conflicts(asset_check: object) -> list[dict[str, str]]:
    if not isinstance(asset_check, dict) or asset_check.get("status") != "conflict":
        return []
    conflicts: list[dict[str, str]] = []
    for item in _dict_list(asset_check.get("conflicts"))[:6]:
        compact = {
            "conflict_type": _string_or_none(item.get("conflict_type"), max_chars=120),
            "current_answer_claim": _string_or_none(item.get("current_answer_claim"), max_chars=160),
            "asset_claim": _string_or_none(item.get("asset_claim"), max_chars=160),
            "severity": _string_or_none(item.get("severity"), max_chars=80),
        }
        compact = {key: value for key, value in compact.items() if value}
        if compact:
            conflicts.append(compact)
    return conflicts


def _asset_conflict_focus_text(conflict: dict[str, Any]) -> str:
    parts = [
        _string_or_none(conflict.get("current_answer_claim"), max_chars=120),
        _string_or_none(conflict.get("asset_claim"), max_chars=120),
        _string_or_none(conflict.get("conflict_type"), max_chars=80),
    ]
    return " / ".join(part for part in parts if part) or "资产事实冲突"


def _filter_covered_points(points: list[str], covered_points: list[str]) -> list[str]:
    return [point for point in points if not _contains_similar_text(covered_points, point)]


def _contains_similar_text(values: list[str], point: str) -> bool:
    normalized = _string_or_none(point, max_chars=240)
    if not normalized:
        return False
    for value in values:
        current = _string_or_none(value, max_chars=240)
        if current and (current in normalized or normalized in current):
            return True
    return False


def _compact_follow_up_target(value: object) -> str | None:
    return _string_or_none(value, max_chars=80)


def _unique_texts(values: object, *, max_chars: int = 240) -> list[str]:
    return _string_list(values, max_item_chars=max_chars)


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _safe_string_map(
    raw: object,
    *,
    max_items: int = 24,
    max_key_chars: int = 80,
    max_value_chars: int = 160,
) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    safe: dict[str, str] = {}
    for key, value in raw.items():
        if len(safe) >= max_items:
            break
        safe_key = _string_or_none(key, max_chars=max_key_chars)
        safe_value = _string_or_none(value, max_chars=max_value_chars)
        if safe_key and safe_value:
            safe[safe_key] = safe_value
    return safe


def _context_hygiene_status(raw: object) -> str:
    value = _string_or_none(raw, max_chars=40)
    return value if value in CONTEXT_HYGIENE_STATUSES else "unknown"


def _safe_nested_string_map(raw: object) -> dict[str, dict[str, str]]:
    if not isinstance(raw, dict):
        return {}
    safe: dict[str, dict[str, str]] = {}
    for key, value in raw.items():
        if len(safe) >= 24:
            break
        safe_key = _string_or_none(key, max_chars=80)
        if not safe_key or not isinstance(value, dict):
            continue
        safe[safe_key] = _safe_string_map(value, max_items=8, max_key_chars=80, max_value_chars=160)
    return safe


def _safe_json_dict(raw: object, *, max_items: int = 32, max_depth: int = 4) -> dict[str, Any]:
    value = _safe_json_value(raw, max_items=max_items, max_depth=max_depth)
    return value if isinstance(value, dict) else {}


def _safe_json_list(raw: object, *, max_items: int = 32, max_depth: int = 4) -> list[Any]:
    value = _safe_json_value(raw, max_items=max_items, max_depth=max_depth)
    return value if isinstance(value, list) else []


def _safe_json_value(raw: object, *, max_items: int, max_depth: int) -> Any:
    if max_depth <= 0:
        return None
    if raw is None or isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return raw
    if isinstance(raw, str):
        return _string_or_none(raw, max_chars=600)
    if isinstance(raw, (list, tuple)):
        values: list[Any] = []
        for item in raw[:max_items]:
            safe_item = _safe_json_value(item, max_items=max_items, max_depth=max_depth - 1)
            if safe_item is not None:
                values.append(safe_item)
        return values
    if isinstance(raw, dict):
        values: dict[str, Any] = {}
        for key, value in raw.items():
            if len(values) >= max_items:
                break
            safe_key = _string_or_none(key, max_chars=120)
            if not safe_key or safe_key in FORBIDDEN_NESTED_METADATA_KEYS:
                continue
            safe_value = _safe_json_value(value, max_items=max_items, max_depth=max_depth - 1)
            if safe_value is not None:
                values[safe_key] = safe_value
        return values
    return _string_or_none(raw, max_chars=600)


def _metadata_payload(raw: object) -> dict[str, Any]:
    if isinstance(raw, QuestionMetadata):
        return raw.to_dict()
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return {}
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError:
            return {}
        return loaded if isinstance(loaded, dict) else {}
    return {}


def _safe_primary_question_evidence(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    allowed_refs = _string_list(value.get("allowed_source_refs"))
    payload = {
        "ref": _string_or_none(value.get("ref"), max_chars=120),
        "source_type": _string_or_none(value.get("source_type"), max_chars=80),
        "title": _string_or_none(value.get("title"), max_chars=180),
        "summary": _string_or_none(value.get("summary"), max_chars=500),
        "claim_mode": _string_or_none(value.get("claim_mode"), max_chars=80),
        "allowed_source_refs": allowed_refs,
        "confidence_level": _string_or_none(value.get("confidence_level"), max_chars=40),
    }
    return payload if payload["ref"] and payload["summary"] else None


def _string_or_none(value: object, *, max_chars: int = 240) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    return text[:max_chars] if text else None


def _string_list(value: object, *, max_item_chars: int = 240) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_items: list[object] = [value]
    elif isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        return []
    result: list[str] = []
    for item in raw_items:
        text = _string_or_none(item, max_chars=max_item_chars)
        if text and text not in result:
            result.append(text)
    return result


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_or_none(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bool_or_false(value: object) -> bool:
    return bool(value) if isinstance(value, bool) else False


def _safe_summary_dict(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        text = _string_or_none(value, max_chars=80)
        return {"kind": text} if text else {}
    allowed = {"kind", "status", "validation_status", "confidence_level", "model_name", "error_type"}
    result: dict[str, Any] = {}
    for key in allowed:
        if key not in value:
            continue
        raw = value.get(key)
        if isinstance(raw, bool):
            result[key] = raw
        elif isinstance(raw, int):
            result[key] = raw
        else:
            text = _string_or_none(raw, max_chars=120)
            if text:
                result[key] = text
    return result


def _safe_prompt_safety_summary(value: object) -> dict[str, bool]:
    if not isinstance(value, dict):
        return {}
    allowed = {
        "input_data_untrusted",
        "raw_prompt_persisted",
        "raw_completion_persisted",
        "provider_payload_persisted",
        "full_evidence_persisted",
    }
    return {key: bool(value[key]) for key in allowed if isinstance(value.get(key), bool)}


def _safe_phase_results(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, Any]] = []
    for item in value[:12]:
        if not isinstance(item, dict):
            continue
        phase = _string_or_none(item.get("phase"), max_chars=80)
        status = _string_or_none(item.get("status"), max_chars=80)
        if not phase or not status:
            continue
        safe_item: dict[str, Any] = {"phase": phase, "status": status}
        tool_name = _string_or_none(item.get("tool_name"), max_chars=120)
        if tool_name:
            safe_item["tool_name"] = tool_name
        output_ref = _string_or_none(item.get("output_ref"), max_chars=160)
        if output_ref:
            safe_item["output_ref"] = output_ref
        attempts = _int_or_none(item.get("attempts"))
        if attempts is not None:
            safe_item["attempts"] = attempts
        latency_ms = _float_or_none(item.get("latency_ms"))
        if latency_ms is not None:
            safe_item["latency_ms"] = latency_ms
        retry_delay_seconds = _float_or_none(item.get("retry_delay_seconds"))
        if retry_delay_seconds is not None:
            safe_item["retry_delay_seconds"] = retry_delay_seconds
        error = _string_or_none(item.get("error"), max_chars=160)
        if error:
            safe_item["error"] = error
        result.append(safe_item)
    return result


def _safe_tool_results(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, Any]] = []
    for item in value[:12]:
        if not isinstance(item, dict):
            continue
        tool_name = _string_or_none(item.get("tool_name"), max_chars=120)
        status = _string_or_none(item.get("status"), max_chars=80)
        if not tool_name or not status:
            continue
        safe_item: dict[str, Any] = {"tool_name": tool_name, "status": status}
        input_schema_id = _string_or_none(item.get("input_schema_id"), max_chars=160)
        output_schema_id = _string_or_none(item.get("output_schema_id"), max_chars=160)
        output_ref = _string_or_none(item.get("output_ref"), max_chars=160)
        if input_schema_id:
            safe_item["input_schema_id"] = input_schema_id
        if output_schema_id:
            safe_item["output_schema_id"] = output_schema_id
        if output_ref:
            safe_item["output_ref"] = output_ref
        attempts = _int_or_none(item.get("attempts"))
        if attempts is not None:
            safe_item["attempts"] = attempts
        latency_ms = _float_or_none(item.get("latency_ms"))
        if latency_ms is not None:
            safe_item["latency_ms"] = latency_ms
        error = _string_or_none(item.get("error"), max_chars=160)
        if error:
            safe_item["error"] = error
        result.append(safe_item)
    return result


def _safe_validator_result(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, Any] = {}
    if isinstance(value.get("passed"), bool):
        result["passed"] = value["passed"]
    blocking_reasons = _string_list(value.get("blocking_reasons"), max_item_chars=120)
    low_confidence_reasons = _string_list(value.get("low_confidence_reasons"), max_item_chars=120)
    checked_rules = _string_list(value.get("checked_rules"), max_item_chars=120)
    if blocking_reasons:
        result["blocking_reasons"] = blocking_reasons
    if low_confidence_reasons:
        result["low_confidence_reasons"] = low_confidence_reasons
    if checked_rules:
        result["checked_rules"] = checked_rules
    return result


def _validation_errors(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, str]] = []
    for item in value[:20]:
        if not isinstance(item, dict):
            continue
        code = _string_or_none(item.get("code"), max_chars=120)
        message = _string_or_none(item.get("message"), max_chars=200)
        if code:
            result.append({"code": code, "message": message or code})
    return result


def _quality_score_or_none(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        score = int(value)
    except (TypeError, ValueError):
        return None
    return max(0, min(100, score))


def _dedupe(items: list[str]) -> tuple[str, ...]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return tuple(result)
