"""Polish feedback task contract pilot."""

from __future__ import annotations

from typing import Any

from app.application.llm.task_contracts import (
    AiTaskContract,
    AiTaskContractFailure,
    AiTaskContractValidationContext,
    business_rule_failure,
)
from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_CANDIDATE_PAYLOAD_FIELDS,
    POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
    POLISH_FEEDBACK_FINAL_PAYLOAD_FIELDS,
    POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
    POLISH_FEEDBACK_TASK_TYPE,
)
from app.application.polish.feedback_validation import (
    validate_feedback_candidate_payload,
    validate_final_feedback_payload,
)


POLISH_FEEDBACK_AI_TASK_CONTRACT_ID = "ai_task_contract.polish_feedback.v1"
POLISH_FEEDBACK_CANDIDATE_REQUIRED_FIELDS = (
    "feedback_text",
    "answer_summary",
    "score_result",
    "loss_points",
    "reference_answer",
)


def _candidate_business_failures(
    payload: dict[str, Any],
    context: AiTaskContractValidationContext,
) -> tuple[AiTaskContractFailure, ...]:
    expected_progress_state_ref = context.metadata.get("expected_progress_state_ref")
    _, errors = validate_feedback_candidate_payload(
        payload,
        expected_progress_state_ref=str(expected_progress_state_ref) if expected_progress_state_ref else None,
    )
    return tuple(business_rule_failure(reason, field="candidate_payload") for reason in errors)


def _final_business_failures(
    payload: dict[str, Any],
    _context: AiTaskContractValidationContext,
) -> tuple[AiTaskContractFailure, ...]:
    _, errors = validate_final_feedback_payload(payload)
    return tuple(business_rule_failure(reason, field="final_payload") for reason in errors)


POLISH_FEEDBACK_TASK_CONTRACT = AiTaskContract(
    contract_id=POLISH_FEEDBACK_AI_TASK_CONTRACT_ID,
    task_type=POLISH_FEEDBACK_TASK_TYPE,
    schema_id=POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    schema_version=POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
    contract_ids=POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
    required_candidate_fields=POLISH_FEEDBACK_CANDIDATE_REQUIRED_FIELDS,
    required_final_fields=POLISH_FEEDBACK_FINAL_PAYLOAD_FIELDS,
    candidate_validator=_candidate_business_failures,
    final_validator=_final_business_failures,
)


__all__ = [
    "POLISH_FEEDBACK_AI_TASK_CONTRACT_ID",
    "POLISH_FEEDBACK_CANDIDATE_PAYLOAD_FIELDS",
    "POLISH_FEEDBACK_CANDIDATE_REQUIRED_FIELDS",
    "POLISH_FEEDBACK_TASK_CONTRACT",
]
