from __future__ import annotations

import json

from app.application.polish.commands import CompletePolishQuestionCommand
from app.application.polish.entities import PolishAnswer, PolishFeedback, PolishQuestion
from app.domain.shared.clock import utc_now
from tests.api.test_polish_question_graph_integration import (
    ACTOR_ID,
    NODE_REF,
    OWNER_ID,
    SESSION_ID,
    _progress_state,
    _use_cases,
)


def test_complete_question_records_progress_tree_side_effects() -> None:
    progress_tree_state = _progress_state()
    progress_tree_state["node_states"] = [
        {"progress_node_ref": NODE_REF, "status": "pending", "completed_questions_count": 0}
    ]
    use_cases, repository = _use_cases(
        ai_orchestration_facade=None,
        progress_tree_state=progress_tree_state,
    )
    now = utc_now()
    question = PolishQuestion(
        question_id="que_complete_question_flow",
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        ai_task_id="task_complete_question_flow",
        question_text="Explain one backend workflow decision.",
        status="generated",
        created_at=now,
        updated_at=now,
        progress_node_ref=NODE_REF,
        evidence_refs=("resume_project_001",),
        question_metadata={
            "question_pattern": "project_deep_dive",
            "focus_key": "focus_payment_reliability",
            "focus_dimension": "system_design",
            "template_signature": "tpl_payment_reliability_v1",
            "blueprint_signature": "bp_payment_reliability_v1",
        },
    )
    repository.add_question(question)

    result = use_cases.complete_question(
        CompletePolishQuestionCommand(
            owner_id=OWNER_ID,
            actor_id=ACTOR_ID,
            session_id=SESSION_ID,
            question_id=question.question_id,
        )
    )

    assert result.is_success
    assert result.value is not None
    updated_state = result.value.progress_tree_state
    assert updated_state["summary"] == "manual_question_completed"
    completed_entries = updated_state["completed_focus_refs"]
    assert len(completed_entries) == 1
    completed_entry = completed_entries[0]
    assert completed_entry["question_id"] == question.question_id
    assert completed_entry["progress_node_ref"] == NODE_REF
    assert completed_entry["focus_key"] == "focus_payment_reliability"
    assert completed_entry["focus_dimension"] == "system_design"
    assert completed_entry["template_signature"] == "tpl_payment_reliability_v1"
    assert completed_entry["blueprint_signature"] == "bp_payment_reliability_v1"
    assert completed_entry["source"] == "manual_question_complete"
    assert completed_entry["completed_at"]
    assert completed_entry["feedback_consistency"] == {
        "source_basis": "step2_effective_generated_feedback + manual_question_complete",
        "question_id": question.question_id,
        "answer_count": 0,
        "has_effective_generated_feedback": False,
        "effective_feedback_count": 0,
        "ineffective_feedback_status_counts": {},
        "mastery_projection_status": "manual_only",
        "source_traceability": [],
    }

    matching_node_state = next(
        node_state for node_state in updated_state["node_states"] if node_state["progress_node_ref"] == NODE_REF
    )
    assert matching_node_state["status"] == "completed"
    assert matching_node_state["completed_questions_count"] == 1
    assert updated_state["current_priority"]["progress_node_ref"] == NODE_REF
    assert repository.session.progress_tree_state == updated_state


def test_complete_question_records_feedback_consistency_without_counting_invalid_feedback_as_mastery() -> None:
    progress_tree_state = _progress_state()
    progress_tree_state["node_states"] = [
        {"progress_node_ref": NODE_REF, "status": "pending", "completed_questions_count": 0}
    ]
    use_cases, repository = _use_cases(
        ai_orchestration_facade=None,
        progress_tree_state=progress_tree_state,
    )
    now = utc_now()
    question = PolishQuestion(
        question_id="que_complete_question_feedback_consistency",
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        ai_task_id="task_complete_question_feedback_consistency",
        question_text="Explain one backend workflow decision.",
        status="generated",
        created_at=now,
        updated_at=now,
        progress_node_ref=NODE_REF,
        evidence_refs=("resume_project_001",),
        question_metadata={
            "focus_key": "focus_payment_reliability",
            "focus_dimension": "system_design",
        },
    )
    repository.add_question(question)
    answer = PolishAnswer(
        answer_id="answer_complete_question_feedback_consistency",
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        question_id=question.question_id,
        answer_round=1,
        answer_text="我会补充幂等、失败恢复和观测指标。",
        status="submitted",
        created_at=now,
        updated_at=now,
    )
    generated_feedback = _feedback(
        feedback_id="feedback_complete_question_generated",
        answer_id=answer.answer_id,
        status="generated",
        feedback_summary=json.dumps(
            {
                "status": "generated",
                "feedback_text": "有效反馈。",
                "score_result": {"score_value": 82, "dimension_scores": []},
            }
        ),
        created_at=now,
    )
    validation_failed_feedback = _feedback(
        feedback_id="feedback_complete_question_validation_failed",
        answer_id=answer.answer_id,
        status="validation_failed",
        feedback_summary=json.dumps({"status": "validation_failed", "feedback_text": ""}),
        created_at=now,
    )
    pending_feedback = _feedback(
        feedback_id="feedback_complete_question_pending",
        answer_id=answer.answer_id,
        status="pending",
        feedback_summary=json.dumps({"status": "pending", "feedback_text": ""}),
        created_at=now,
    )
    repository.list_answers_for_session = lambda owner_id, session_id: (answer,)
    repository.list_feedbacks_for_session = lambda owner_id, session_id: (
        generated_feedback,
        validation_failed_feedback,
        pending_feedback,
    )

    result = use_cases.complete_question(
        CompletePolishQuestionCommand(
            owner_id=OWNER_ID,
            actor_id=ACTOR_ID,
            session_id=SESSION_ID,
            question_id=question.question_id,
        )
    )

    assert result.is_success
    assert result.value is not None
    completed_entry = result.value.progress_tree_state["completed_focus_refs"][0]
    consistency = completed_entry["feedback_consistency"]
    assert consistency["has_effective_generated_feedback"] is True
    assert consistency["effective_feedback_count"] == 1
    assert consistency["ineffective_feedback_status_counts"] == {
        "pending": 1,
        "validation_failed": 1,
    }
    assert consistency["mastery_projection_status"] == "effective_feedback_available"
    assert consistency["source_traceability"] == [
        {
            "answer_id": answer.answer_id,
            "answer_round": 1,
            "feedback_id": generated_feedback.feedback_id,
            "status": "generated",
            "source_basis": "step2_effective_generated_feedback",
        }
    ]
    question_two = PolishQuestion(
        question_id="que_complete_question_feedback_consistency_two",
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        ai_task_id="task_complete_question_feedback_consistency_two",
        question_text="Explain a second backend workflow decision.",
        status="generated",
        created_at=now,
        updated_at=now,
        progress_node_ref=NODE_REF,
        evidence_refs=("resume_project_001",),
        question_metadata={
            "focus_key": "focus_payment_observability",
            "focus_dimension": "system_design",
        },
    )
    repository.add_question(question_two)

    second_result = use_cases.complete_question(
        CompletePolishQuestionCommand(
            owner_id=OWNER_ID,
            actor_id=ACTOR_ID,
            session_id=SESSION_ID,
            question_id=question_two.question_id,
        )
    )

    assert second_result.is_success
    assert second_result.value is not None
    repeated_completed_entries = second_result.value.progress_tree_state["completed_focus_refs"]
    first_entry_after_second_completion = next(
        entry for entry in repeated_completed_entries if entry["question_id"] == question.question_id
    )
    assert first_entry_after_second_completion["feedback_consistency"] == consistency


def _feedback(
    *,
    feedback_id: str,
    answer_id: str,
    status: str,
    feedback_summary: str,
    created_at: object,
) -> PolishFeedback:
    return PolishFeedback(
        feedback_id=feedback_id,
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        answer_id=answer_id,
        ai_task_id=f"task_{feedback_id}",
        score_result_id=None,
        feedback_summary=feedback_summary,
        status=status,
        created_at=created_at,
        updated_at=created_at,
    )
