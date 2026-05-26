"""Single-call decision contract for next polish question generation."""

from __future__ import annotations

import json
from typing import Any


NEXT_QUESTION_AGENT_SCHEMA_ID = "polish_next_question_agent_decision_v1"
NEXT_QUESTION_AGENT_SCHEMA_VERSION = "v1"
NEXT_QUESTION_AGENT_PROMPT_VERSION = "polish_next_question_agent_prompt.v1"

TURN_INTENTS = (
    "project_implementation_deep_dive",
    "architecture_tradeoff_deep_dive",
    "failure_recovery_deep_dive",
    "extension_design_followup",
    "mechanism_understanding_check",
    "gap_compensation_design",
    "clarification",
)
EVIDENCE_SUPPORT_LEVELS = (
    "direct_implemented",
    "adjacent_implemented",
    "conceptual_only",
    "unsupported",
)
MAIN_QUESTION_STYLES = (
    "ask_how_implemented",
    "ask_why_tradeoff",
    "ask_failure_recovery",
    "ask_mechanism_understanding",
    "ask_hypothetical_design",
    "ask_clarification",
)
ALLOWED_EXTENSION_DEPTHS = (
    "none",
    "follow_up_only",
    "main_question_allowed",
    "required",
)
NEXT_QUESTION_KINDS = (
    "implementation_deep_dive",
    "architecture_tradeoff_deep_dive",
    "failure_recovery_deep_dive",
    "extension_design_followup",
    "mechanism_understanding_check",
    "gap_compensation_design",
    "clarification",
)
QUESTION_DIFFICULTIES = ("easy", "medium", "hard", "clarification")
CHECK_STATUSES = ("pass", "warn", "fail")

FORBIDDEN_OUTPUT_MARKERS = (
    "raw_prompt",
    "system_prompt",
    "developer_prompt",
    "provider_payload",
    "raw_completion",
    "api_key",
    "token=",
    "secret=",
    "-----begin",
)
FACTUAL_CLAIM_PATTERNS = (
    "你设计了",
    "你实现了",
    "你主导了",
    "你负责了",
    "你落地了",
    "你当时设计",
    "你当时实现",
    "在你负责的项目中",
    "在你做的项目中设计了",
)


def validate_next_question_agent_output(
    payload: dict[str, Any],
    *,
    allowed_evidence_refs: tuple[str, ...],
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Validate and normalize the structured NextQuestionAgent output."""

    if not isinstance(payload, dict):
        return None, ("next_question_schema_invalid",)

    errors: list[str] = []
    if _contains_forbidden_output(payload):
        errors.append("next_question_output_unsafe_leakage")

    schema_id = _clean(payload.get("schema_id"), max_chars=120)
    if schema_id != NEXT_QUESTION_AGENT_SCHEMA_ID:
        errors.append("next_question_schema_id_invalid")
    prompt_version = _clean(payload.get("prompt_version"), max_chars=120)
    if not prompt_version:
        errors.append("next_question_prompt_version_required")

    clarification_needed = payload.get("clarification_needed")
    if not isinstance(clarification_needed, bool):
        errors.append("next_question_clarification_needed_required")
        clarification_needed = False

    confidence = _clean(payload.get("confidence"), max_chars=40)
    if confidence not in {"high", "medium", "low"}:
        errors.append("next_question_confidence_invalid")

    missing_context = _string_list(payload.get("missing_context"), max_items=12, max_item_chars=120)
    decision, decision_errors = _decision(payload.get("decision"), allowed_evidence_refs=allowed_evidence_refs)
    errors.extend(decision_errors)
    question, question_errors = _question(payload.get("question"))
    errors.extend(question_errors)
    persistence_hints = _persistence_hints(payload.get("persistence_hints"))
    post_check_hints = _post_check_hints(payload.get("post_check_hints"))

    evidence_refs = _string_list(payload.get("evidence_refs"), max_items=12, max_item_chars=160)
    allowed = set(allowed_evidence_refs)
    if any(ref not in allowed for ref in evidence_refs):
        errors.append("next_question_evidence_refs_out_of_scope")

    if decision is not None and question is not None:
        errors.extend(_post_check(decision=decision, question=question, post_check_hints=post_check_hints))

    if errors:
        return None, tuple(dict.fromkeys(errors))

    return (
        {
            "schema_id": schema_id,
            "schema_version": NEXT_QUESTION_AGENT_SCHEMA_VERSION,
            "prompt_version": prompt_version,
            "clarification_needed": bool(clarification_needed),
            "confidence": confidence,
            "missing_context": missing_context,
            "decision": decision or {},
            "question": question or {},
            "persistence_hints": persistence_hints,
            "evidence_refs": evidence_refs,
            "post_check_hints": post_check_hints,
        },
        (),
    )


def _decision(raw: object, *, allowed_evidence_refs: tuple[str, ...]) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(raw, dict):
        return None, ["next_question_decision_required"]
    turn_intent = _enum(raw.get("turn_intent"), TURN_INTENTS, "next_question_turn_intent_invalid", errors)
    evidence_support_level = _enum(
        raw.get("evidence_support_level"),
        EVIDENCE_SUPPORT_LEVELS,
        "next_question_evidence_support_level_invalid",
        errors,
    )
    main_question_style = _enum(
        raw.get("main_question_style"),
        MAIN_QUESTION_STYLES,
        "next_question_main_question_style_invalid",
        errors,
    )
    allowed_extension_depth = _enum(
        raw.get("allowed_extension_depth"),
        ALLOWED_EXTENSION_DEPTHS,
        "next_question_allowed_extension_depth_invalid",
        errors,
    )
    primary_refs = _string_list(raw.get("primary_evidence_refs"), max_items=8, max_item_chars=160)
    secondary_refs = _string_list(raw.get("secondary_evidence_refs"), max_items=8, max_item_chars=160)
    allowed = set(allowed_evidence_refs)
    if any(ref not in allowed for ref in (*primary_refs, *secondary_refs)):
        errors.append("next_question_decision_evidence_refs_out_of_scope")
    return (
        {
            "turn_intent": turn_intent,
            "intent_reason": _clean(raw.get("intent_reason"), max_chars=500),
            "evidence_support_level": evidence_support_level,
            "evidence_support_reason": _clean(raw.get("evidence_support_reason"), max_chars=500),
            "main_question_style": main_question_style,
            "allowed_extension_depth": allowed_extension_depth,
            "primary_evidence_refs": primary_refs,
            "secondary_evidence_refs": secondary_refs,
            "unsupported_capability_claims": _string_list(
                raw.get("unsupported_capability_claims"), max_items=12, max_item_chars=120
            ),
            "risk_flags": _string_list(raw.get("risk_flags"), max_items=12, max_item_chars=120),
            "avoid_patterns_applied": _string_list(
                raw.get("avoid_patterns_applied"), max_items=12, max_item_chars=120
            ),
        },
        errors,
    )


def _question(raw: object) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(raw, dict):
        return None, ["next_question_question_required"]
    question_text = _clean(raw.get("question_text"), max_chars=600)
    if not question_text:
        errors.append("next_question_question_text_required")
    question_kind = _enum(raw.get("question_kind"), NEXT_QUESTION_KINDS, "next_question_kind_invalid", errors)
    difficulty = _enum(raw.get("difficulty"), QUESTION_DIFFICULTIES, "next_question_difficulty_invalid", errors)
    skill_dimension = _clean(raw.get("skill_dimension"), max_chars=200)
    if not skill_dimension:
        errors.append("next_question_skill_dimension_required")
    expected_signal = _clean(raw.get("expected_signal"), max_chars=400)
    if not expected_signal:
        errors.append("next_question_expected_signal_required")
    follow_ups = _string_list(raw.get("follow_ups"), max_items=4, max_item_chars=240)
    if not follow_ups:
        errors.append("next_question_follow_ups_required")
    scoring_rubric = _scoring_rubric(raw.get("scoring_rubric"))
    if not scoring_rubric:
        errors.append("next_question_scoring_rubric_required")
    return (
        {
            "question_text": question_text,
            "question_kind": question_kind,
            "difficulty": difficulty,
            "skill_dimension": skill_dimension,
            "expected_signal": expected_signal,
            "follow_ups": follow_ups,
            "scoring_rubric": scoring_rubric,
        },
        errors,
    )


def _persistence_hints(raw: object) -> dict[str, Any]:
    data = raw if isinstance(raw, dict) else {}
    return {
        "should_persist_decision": bool(data.get("should_persist_decision", True)),
        "should_update_progress": bool(data.get("should_update_progress", True)),
        "next_focus_candidates": _string_list(data.get("next_focus_candidates"), max_items=8, max_item_chars=160),
        "trace_tags": _string_list(data.get("trace_tags"), max_items=12, max_item_chars=80),
    }


def _post_check_hints(raw: object) -> dict[str, Any]:
    data = raw if isinstance(raw, dict) else {}
    question_style_check = _clean(data.get("question_style_check"), max_chars=40) or "pass"
    evidence_grounding_check = _clean(data.get("evidence_grounding_check"), max_chars=40) or "pass"
    if question_style_check not in CHECK_STATUSES:
        question_style_check = "fail"
    if evidence_grounding_check not in CHECK_STATUSES:
        evidence_grounding_check = "fail"
    return {
        "claims_to_verify": _string_list(data.get("claims_to_verify"), max_items=12, max_item_chars=120),
        "unsupported_terms_in_question": _string_list(
            data.get("unsupported_terms_in_question"), max_items=12, max_item_chars=120
        ),
        "question_style_check": question_style_check,
        "evidence_grounding_check": evidence_grounding_check,
    }


def _post_check(*, decision: dict[str, Any], question: dict[str, Any], post_check_hints: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if post_check_hints.get("question_style_check") == "fail":
        errors.append("next_question_post_check_question_style_failed")
    if post_check_hints.get("evidence_grounding_check") == "fail":
        errors.append("next_question_post_check_evidence_grounding_failed")

    question_text = str(question.get("question_text") or "")
    unsupported_claims = tuple(str(item) for item in decision.get("unsupported_capability_claims") or () if item)
    if (
        decision.get("evidence_support_level") == "adjacent_implemented"
        and decision.get("allowed_extension_depth") == "follow_up_only"
    ):
        if any(claim and claim in question_text for claim in unsupported_claims):
            errors.append("next_question_post_check_unsupported_claim_in_main_question")
        if post_check_hints.get("unsupported_terms_in_question"):
            errors.append("next_question_post_check_unsupported_claim_in_main_question")

    if decision.get("evidence_support_level") == "adjacent_implemented":
        lowered = question_text.lower()
        if any(pattern in question_text for pattern in FACTUAL_CLAIM_PATTERNS) and any(
            claim and claim in question_text for claim in unsupported_claims
        ):
            errors.append("next_question_post_check_unsupported_claim_as_fact")
        if any(marker in lowered for marker in FORBIDDEN_OUTPUT_MARKERS):
            errors.append("next_question_output_unsafe_leakage")
    return errors


def _scoring_rubric(raw: object) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    result: list[dict[str, Any]] = []
    for item in raw[:4]:
        if not isinstance(item, dict):
            continue
        dimension = _clean(item.get("dimension"), max_chars=120)
        signals = _string_list(item.get("signals"), max_items=4, max_item_chars=160)
        if dimension and signals:
            result.append({"dimension": dimension, "signals": signals})
    return result


def _enum(value: object, allowed: tuple[str, ...], error: str, errors: list[str]) -> str:
    text = _clean(value, max_chars=120)
    if text not in allowed:
        errors.append(error)
        return ""
    return text


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


def _contains_forbidden_output(payload: dict[str, Any]) -> bool:
    try:
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True).lower()
    except TypeError:
        serialized = str(payload).lower()
    return any(marker in serialized for marker in FORBIDDEN_OUTPUT_MARKERS)
