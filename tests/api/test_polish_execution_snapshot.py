from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from app.application.ai_runtime.contracts import RuntimePolicyError, RuntimeValidationError
from app.application.polish.execution_flow import (
    ExecutionSnapshot,
    QuestionExecutionHandler,
    QuestionExecutionInput,
    create_execution_snapshot,
)
from app.application.polish.ports import AuthorityDecisionResult, PolishQuestion


OWNER_ID = "usr_snapshot"
ACTOR_ID = OWNER_ID
SESSION_ID = "ses_snapshot"
NODE_REF = "node_snapshot"


def test_allowed_authority_creates_immutable_target_equal_snapshot() -> None:
    decision = AuthorityDecisionResult(
        allowed=True,
        decision_ref="qauth_snapshot",
        execution_target=NODE_REF,
    )
    runtime_flags = {"task_type": "polish_question_generation", "llm_max_retries": 2}
    asset_refs = ["asset-a", "asset-b"]

    snapshot = create_execution_snapshot(
        flow="question_generation",
        authority_decision=decision,
        runtime_flags=runtime_flags,
        asset_refs=asset_refs,
    )
    runtime_flags["task_type"] = "changed_after_snapshot"
    asset_refs.append("asset-c")

    assert snapshot.flow == "question_generation"
    assert snapshot.decision_ref == "qauth_snapshot"
    assert snapshot.execution_target == NODE_REF
    assert "task_type=polish_question_generation" in snapshot.runtime_flags
    assert "llm_max_retries=2" in snapshot.runtime_flags
    assert snapshot.asset_snapshot == ("asset-a", "asset-b")
    assert snapshot.decision_ref_contract == "trace_only"
    assert snapshot.durable_idempotency_contract is False
    with pytest.raises(FrozenInstanceError):
        snapshot.execution_target = "changed"  # type: ignore[misc]


def test_rejected_authority_cannot_create_snapshot() -> None:
    decision = AuthorityDecisionResult(
        allowed=False,
        decision_ref="qauth_rejected",
        rejection_reason="execution_target_missing",
    )

    with pytest.raises(RuntimePolicyError, match="authority rejected"):
        create_execution_snapshot(flow="question_generation", authority_decision=decision)


def test_snapshot_metadata_excludes_local_runtime_decision_sources() -> None:
    snapshot = create_execution_snapshot(
        flow="question_generation",
        authority_decision=AuthorityDecisionResult(
            allowed=True,
            decision_ref="qauth_snapshot_metadata",
            execution_target=NODE_REF,
        ),
        runtime_flags={"task_type": "polish_question_generation"},
        asset_refs=("asset-a",),
    )

    metadata = snapshot.to_metadata()

    assert metadata["execution_target"] == NODE_REF
    assert "selected_progress_node_ref" not in metadata
    assert "completed_focus_refs" not in metadata
    assert "llm_recommendation" not in metadata
    assert "graph_available" not in metadata
    assert "provider_success" not in metadata


def test_executor_refuses_missing_or_invalid_snapshot() -> None:
    repository = _QuestionRepository()

    with pytest.raises(RuntimeValidationError, match="snapshot is required"):
        QuestionExecutionHandler(repository).persist_result(
            _question_execution_input(snapshot=None)
        )

    with pytest.raises(RuntimeValidationError, match="snapshot flow is invalid"):
        QuestionExecutionHandler(repository).persist_result(
            _question_execution_input(
                snapshot=ExecutionSnapshot(
                    flow="feedback_evaluation",
                    decision_ref="qauth_wrong_flow",
                    execution_target=NODE_REF,
                )
            )
        )

    assert repository.questions == []


def _question_execution_input(*, snapshot: ExecutionSnapshot | None) -> QuestionExecutionInput:
    return QuestionExecutionInput(
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        ai_task_id="task_snapshot",
        agent_run_id="agent_snapshot",
        candidate={
            "candidate_ref": "candidate_snapshot",
            "question_text": "Explain immutable execution snapshots.",
            "progress_node_ref": NODE_REF,
            "evidence_refs": (),
            "question_metadata": {},
            "quality_gate": {"status": "accepted", "passed": True, "blocking_reasons": ()},
        },
        snapshot=snapshot,  # type: ignore[arg-type]
        trace_refs=("trace_snapshot",),
        contract_ids=("P-POLISH-QUESTION",),
    )


class _QuestionRepository:
    def __init__(self) -> None:
        self.questions: list[PolishQuestion] = []

    def list_questions_for_session(self, owner_id: str, session_id: str) -> tuple[PolishQuestion, ...]:
        return tuple(
            question
            for question in self.questions
            if question.owner_id == owner_id and question.session_id == session_id
        )

    def add_question(self, question: PolishQuestion) -> None:
        self.questions.append(question)

    def add_question_once(
        self,
        *,
        owner_id: str,
        session_id: str,
        graph_persistence_idempotency_key: str,
        question: PolishQuestion,
    ) -> tuple[PolishQuestion, bool]:
        self.questions.append(question)
        return question, True
