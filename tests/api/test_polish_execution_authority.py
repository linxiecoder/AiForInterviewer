"""Phase 1 regression tests for Polish execution authority boundaries."""

from __future__ import annotations

from types import SimpleNamespace

from app.application.polish.commands import CreatePolishQuestionTaskCommand
from app.application.polish import use_cases as polish_use_cases


def test_backend_authority_emits_trace_only_execution_target() -> None:
    command = CreatePolishQuestionTaskCommand(
        owner_id="owner-1",
        actor_id="actor-1",
        session_id="session-1",
        selected_progress_node_ref="node-backend",
    )
    detail = SimpleNamespace(
        progress_tree_plan={"nodes": [{"progress_node_ref": "node-backend", "children": []}]}
    )

    decision = polish_use_cases._decide_question_execution_authority(command=command, detail=detail)

    assert decision.allowed
    assert decision.execution_target == "node-backend"
    assert decision.decision_ref.startswith("qauth_")
    assert decision.control_reason_codes == ("backend_authority_target_selected",)
    assert decision.policy_reason_codes == (polish_use_cases.QUESTION_GENERATION_MODE_NEW,)
    assert decision.details["authority_source"] == polish_use_cases.QUESTION_EXECUTION_AUTHORITY_SOURCE
    assert decision.details["decision_ref_contract"] == "trace_only"


def test_backend_authority_rejects_target_not_in_backend_plan() -> None:
    command = CreatePolishQuestionTaskCommand(
        owner_id="owner-1",
        actor_id="actor-1",
        session_id="session-1",
        selected_progress_node_ref="node-from-ui",
    )
    detail = SimpleNamespace(
        progress_tree_plan={"nodes": [{"progress_node_ref": "node-backend", "children": []}]}
    )

    decision = polish_use_cases._decide_question_execution_authority(command=command, detail=detail)
    error = polish_use_cases._question_execution_authority_error(decision)

    assert not decision.allowed
    assert decision.execution_target == "node-from-ui"
    assert decision.rejection_reason == "target_progress_node_not_found"
    assert decision.control_reason_codes == ("execution_target_not_in_backend_plan",)
    assert error.code == "validation_failed"
    assert error.details["reason"] == "target_progress_node_not_found"
    assert error.details["authority_source"] == polish_use_cases.QUESTION_EXECUTION_AUTHORITY_SOURCE


def test_legacy_category_ref_no_longer_derives_execution_target() -> None:
    command = CreatePolishQuestionTaskCommand(
        owner_id="owner-1",
        actor_id="actor-1",
        session_id="session-1",
        selected_secondary_category_ref="legacy-category-node",
    )
    detail = SimpleNamespace(progress_tree_plan={"nodes": []})

    decision = polish_use_cases._decide_question_execution_authority(command=command, detail=detail)

    assert polish_use_cases._question_generation_requested_ref(command) is None
    assert not decision.allowed
    assert decision.rejection_reason == "execution_target_missing"


def test_use_cases_declares_minimum_split_landing_map() -> None:
    landing_map = polish_use_cases.POLISH_USE_CASE_SPLIT_LANDING_MAP

    assert landing_map["session_lifecycle"].endswith("PolishSessionApplicationService")
    assert landing_map["question_execution_authority"] == (
        "app.application.polish.use_cases._decide_question_execution_authority"
    )
    assert landing_map["feedback_generation"].endswith("PolishFeedbackApplicationService")
    assert landing_map["progress_canonical_write"].endswith("PolishProgressApplicationService")
