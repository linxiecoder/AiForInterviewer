from __future__ import annotations

from app.application.polish.commands import CompletePolishQuestionCommand
from app.application.polish.entities import PolishQuestion
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

    matching_node_state = next(
        node_state for node_state in updated_state["node_states"] if node_state["progress_node_ref"] == NODE_REF
    )
    assert matching_node_state["status"] == "completed"
    assert matching_node_state["completed_questions_count"] == 1
    assert updated_state["current_priority"]["progress_node_ref"] == NODE_REF
    assert repository.session.progress_tree_state == updated_state
