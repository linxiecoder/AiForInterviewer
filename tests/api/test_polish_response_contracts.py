from __future__ import annotations

from app.application.polish.feedback_projection import (
    FEEDBACK_PAYLOAD_RESPONSE_TOP_LEVEL_KEYS,
    response_safe_feedback_payload,
)
from app.application.polish.task_contracts.feedback_contract import POLISH_FEEDBACK_TASK_CONTRACT
from app.schemas.polish import PolishFeedbackPayload


STEP8_RESPONSE_METADATA_FIELDS = (
    "policy_signed_next_action",
    "follow_up_intent_classification",
    "same_node_follow_up_contract",
    "same_node_next_question_contract",
    "next_question_response_contract",
)


def test_step8_response_metadata_is_optional_response_schema_only() -> None:
    for field_name in STEP8_RESPONSE_METADATA_FIELDS:
        assert field_name in FEEDBACK_PAYLOAD_RESPONSE_TOP_LEVEL_KEYS
        assert field_name in PolishFeedbackPayload.model_fields
        assert not PolishFeedbackPayload.model_fields[field_name].is_required()
        assert field_name not in POLISH_FEEDBACK_TASK_CONTRACT.required_final_fields


def test_step8_response_projection_keeps_metadata_and_drops_provider_payload() -> None:
    projected = response_safe_feedback_payload(
        {
            "feedback_text": "same-node feedback",
            "policy_signed_next_action": {
                "action_type": "continue_same_question",
                "policy_signature": "policy_sig_step8",
                "raw_prompt": "must_drop",
            },
            "follow_up_intent_classification": {"intent": "same_node_follow_up"},
            "same_node_follow_up_contract": {"contract_id": "same_node_follow_up.v1"},
            "same_node_next_question_contract": {"contract_id": "same_node_next_question.v1"},
            "next_question_response_contract": {"contract_id": "next_question_response.v1"},
            "provider_payload": {"completion": "must_drop"},
        }
    )

    assert projected["policy_signed_next_action"] == {
        "action_type": "continue_same_question",
        "policy_signature": "policy_sig_step8",
    }
    assert projected["follow_up_intent_classification"]["intent"] == "same_node_follow_up"
    assert projected["same_node_follow_up_contract"]["contract_id"] == "same_node_follow_up.v1"
    assert projected["same_node_next_question_contract"]["contract_id"] == "same_node_next_question.v1"
    assert projected["next_question_response_contract"]["contract_id"] == "next_question_response.v1"
    assert "provider_payload" not in projected
