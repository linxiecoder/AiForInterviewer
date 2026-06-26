from __future__ import annotations

from types import SimpleNamespace

import app.api.v1.polish as polish_api
from app.application.polish.entities import PolishTaskStatus
from app.domain.shared.clock import utc_now
from app.domain.shared.refs import ResourceRef, TraceRef
from app.schemas.polish import PolishTaskStatusResponse


def test_step8_feedback_response_envelope_preserves_refs_and_contract_metadata() -> None:
    now = utc_now()
    task = PolishTaskStatus(
        ai_task_id="task_step8_response_envelope",
        task_type="polish_feedback_generation",
        status="succeeded",
        contract_ids=("P-POLISH-005",),
        retryable=False,
        result_ref=TraceRef(trace_ref_id="trc_step8_response_envelope", trace_type="feedback", created_at=now),
        user_visible_status="反馈已生成",
        score_type="polish_answer",
        candidate_refs=(
            ResourceRef(resource_type="question", resource_id="ques_step8"),
            ResourceRef(resource_type="progress_node", resource_id="pnode_step8"),
        ),
        suggestion_refs=(ResourceRef(resource_type="feedback_next_action", resource_id="same_node_follow_up"),),
        validation_errors=("same_node_contract_metadata_missing",),
    )
    answer = SimpleNamespace(
        answer_id="ans_step8_response_envelope",
        answer_round=2,
        feedback_id="trc_step8_response_envelope",
        feedback_created_at=now,
        score_result_id="score_step8_response_envelope",
        feedback_payload={
            "schema_id": "polish_feedback_generated_v1",
            "schema_version": "1.0",
            "status": "generated",
            "contract_ids": ["P-POLISH-005"],
            "feedback_id": "trc_step8_response_envelope",
            "feedback_text": "same-node metadata remains visible",
            "score_result": {"score_value": 82},
            "policy_signed_next_action": {
                "action_type": "continue_same_question",
                "policy_signature": "policy_sig_step8",
            },
            "follow_up_intent_classification": {"intent": "same_node_follow_up"},
            "same_node_follow_up_contract": {"contract_id": "same_node_follow_up.v1"},
            "same_node_next_question_contract": {"contract_id": "same_node_next_question.v1"},
            "next_question_response_contract": {"contract_id": "next_question_response.v1"},
        },
    )

    response = PolishTaskStatusResponse.model_validate(
        polish_api._feedback_response(
            task,
            answer,
            session_id="psess_step8",
            question_id="ques_step8",
        )
    ).model_dump(mode="json")

    assert response["candidate_refs"] == [
        {"resource_type": "question", "resource_id": "ques_step8"},
        {"resource_type": "progress_node", "resource_id": "pnode_step8"},
    ]
    assert response["suggestion_refs"] == [
        {"resource_type": "feedback_next_action", "resource_id": "same_node_follow_up"}
    ]
    assert response["validation_errors"] == ["same_node_contract_metadata_missing"]
    assert response["feedback_payload"]["policy_signed_next_action"]["policy_signature"] == "policy_sig_step8"
    assert response["feedback_payload"]["same_node_follow_up_contract"]["contract_id"] == "same_node_follow_up.v1"
