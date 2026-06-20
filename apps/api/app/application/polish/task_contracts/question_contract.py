"""Polish question generation task contract pilot."""

from __future__ import annotations

from typing import Any

from app.application.llm.task_contracts import (
    AiTaskContract,
    AiTaskContractFailure,
    AiTaskContractValidationContext,
    business_rule_failure,
)
from app.application.polish.question_generation_policy import (
    DEFAULT_QUESTION_GENERATION_RUNTIME_POLICY,
    QUESTION_KIND_TAXONOMY,
)


POLISH_QUESTION_AI_TASK_CONTRACT_ID = "ai_task_contract.polish_question.v1"
POLISH_QUESTION_CANDIDATE_REQUIRED_FIELDS = (
    "question_text",
    "question_kind",
    "focus_dimension",
    "difficulty",
    "skill_dimension",
    "expected_signal",
    "follow_ups",
    "scoring_rubric",
    "evidence_refs",
    "confidence",
    "clarification_needed",
)
_DIFFICULTY_VALUES = frozenset({"easy", "medium", "hard", "clarification"})
_CONFIDENCE_VALUES = frozenset({"high", "medium", "low"})
_QUESTION_KIND_VALUES = frozenset(QUESTION_KIND_TAXONOMY)


def _question_business_failures(
    payload: dict[str, Any],
    _context: AiTaskContractValidationContext,
) -> tuple[AiTaskContractFailure, ...]:
    failures: list[AiTaskContractFailure] = []
    question_text = _clean(payload.get("question_text"))
    if not question_text:
        failures.append(business_rule_failure("llm_question_text_required", field="question_text"))
    elif _contains_unsafe_marker(question_text):
        failures.append(business_rule_failure("llm_question_text_unsafe_leakage", field="question_text"))

    question_kind = _clean(payload.get("question_kind"))
    if question_kind not in _QUESTION_KIND_VALUES:
        failures.append(
            business_rule_failure(
                "llm_question_kind_invalid",
                field="question_kind",
                details={"allowed": sorted(_QUESTION_KIND_VALUES), "actual": question_kind},
            )
        )

    difficulty = _clean(payload.get("difficulty"))
    if difficulty not in _DIFFICULTY_VALUES:
        failures.append(
            business_rule_failure(
                "llm_difficulty_invalid",
                field="difficulty",
                details={"allowed": sorted(_DIFFICULTY_VALUES), "actual": difficulty},
            )
        )

    if not _clean(payload.get("skill_dimension")):
        failures.append(business_rule_failure("llm_skill_dimension_required", field="skill_dimension"))
    if not _clean(payload.get("expected_signal")):
        failures.append(business_rule_failure("llm_expected_signal_required", field="expected_signal"))
    if not _string_list(payload.get("follow_ups")):
        failures.append(business_rule_failure("llm_follow_ups_required", field="follow_ups"))
    if not _valid_scoring_rubric(payload.get("scoring_rubric")):
        failures.append(business_rule_failure("llm_scoring_rubric_required", field="scoring_rubric"))
    if not _string_list(payload.get("evidence_refs")):
        failures.append(business_rule_failure("llm_evidence_refs_required", field="evidence_refs"))

    confidence = _clean(payload.get("confidence"))
    if confidence not in _CONFIDENCE_VALUES:
        failures.append(
            business_rule_failure(
                "llm_confidence_invalid",
                field="confidence",
                details={"allowed": sorted(_CONFIDENCE_VALUES), "actual": confidence},
            )
        )
    if not isinstance(payload.get("clarification_needed"), bool):
        failures.append(
            business_rule_failure(
                "llm_clarification_needed_required",
                field="clarification_needed",
            )
        )
    return tuple(failures)


POLISH_QUESTION_TASK_CONTRACT = AiTaskContract(
    contract_id=POLISH_QUESTION_AI_TASK_CONTRACT_ID,
    task_type=DEFAULT_QUESTION_GENERATION_RUNTIME_POLICY.task_type,
    schema_id=DEFAULT_QUESTION_GENERATION_RUNTIME_POLICY.prompt_schema_id,
    schema_version=DEFAULT_QUESTION_GENERATION_RUNTIME_POLICY.prompt_schema_version,
    contract_ids=DEFAULT_QUESTION_GENERATION_RUNTIME_POLICY.contract_ids,
    required_candidate_fields=POLISH_QUESTION_CANDIDATE_REQUIRED_FIELDS,
    required_final_fields=POLISH_QUESTION_CANDIDATE_REQUIRED_FIELDS,
    candidate_validator=_question_business_failures,
    final_validator=_question_business_failures,
)


def _clean(value: object, *, max_chars: int = 240) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text


def _string_list(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    result: list[str] = []
    for item in value:
        text = _clean(item)
        if text:
            result.append(text)
    return tuple(result)


def _valid_scoring_rubric(value: object) -> bool:
    if not isinstance(value, list) or not value:
        return False
    for item in value:
        if not isinstance(item, dict):
            return False
        signals = _string_list(item.get("signals"))
        if not _clean(item.get("dimension")) or not signals:
            return False
    return True


def _contains_unsafe_marker(value: str) -> bool:
    lowered = value.lower()
    return any(
        marker in lowered
        for marker in (
            "raw prompt",
            "raw completion",
            "system prompt",
            "provider payload",
            "api key",
            "secret",
            "token=",
        )
    )


__all__ = [
    "POLISH_QUESTION_AI_TASK_CONTRACT_ID",
    "POLISH_QUESTION_CANDIDATE_REQUIRED_FIELDS",
    "POLISH_QUESTION_TASK_CONTRACT",
]
