from __future__ import annotations

from typing import Any

import pytest

from app.application.ai_runtime.contracts import RuntimePolicyError, RuntimeValidationError
from app.application.polish.execution_flow import (
    ExecutionSnapshot,
    ProgressCanonicalWriteHandler,
    ProgressProjectionRefreshHandler,
    QuestionExecutionHandler,
    QuestionExecutionInput,
    create_execution_snapshot,
    feedback_execution_flow_metadata,
    feedback_payload_with_execution_flow,
)
from app.application.polish.ports import AuthorityDecisionResult, PolishQuestion, PolishSession
from app.domain.shared.clock import utc_now


OWNER_ID = "usr_execution_flow"
ACTOR_ID = OWNER_ID
SESSION_ID = "ses_execution_flow"
NODE_REF = "node_execution_flow"


def test_question_execution_handler_persists_trace_only_authority_metadata() -> None:
    repository = _QuestionRepository()
    decision = AuthorityDecisionResult(
        allowed=True,
        decision_ref="qauth_execution_flow",
        execution_target=NODE_REF,
        control_reason_codes=("backend_plan_current_priority",),
        details={"decision_ref_contract": "trace_only"},
    )

    snapshot = create_execution_snapshot(
        flow="question_generation",
        authority_decision=decision,
        runtime_flags={"task_type": "polish_question_generation"},
        asset_refs=("asset_execution_flow",),
    )

    result = QuestionExecutionHandler(repository).persist_result(
        QuestionExecutionInput(
            owner_id=OWNER_ID,
            actor_id=ACTOR_ID,
            session_id=SESSION_ID,
            ai_task_id="task_execution_flow",
            agent_run_id="agent_execution_flow",
            candidate=_accepted_candidate(),
            snapshot=snapshot,
            trace_refs=("trace_execution_flow",),
            contract_ids=("P-POLISH-QUESTION",),
        ),
        now=utc_now(),
    )

    metadata = result.question.question_metadata
    execution_flow = metadata["execution_flow"]
    assert execution_flow["flow"] == "question_generation"
    assert execution_flow["decision_ref"] == "qauth_execution_flow"
    assert execution_flow["decision_ref_contract"] == "trace_only"
    assert execution_flow["durable_idempotency_contract"] is False
    assert execution_flow["execution_target"] == NODE_REF
    assert execution_flow["runtime_flags"] == ["task_type=polish_question_generation"]
    assert execution_flow["asset_snapshot"] == ["asset_execution_flow"]
    assert metadata["progress_node_ref"] == NODE_REF
    assert len(repository.questions) == 1


def test_question_snapshot_creation_rejects_missing_or_denied_authority() -> None:
    repository = _QuestionRepository()
    denied = AuthorityDecisionResult(
        allowed=False,
        decision_ref="qauth_denied",
        rejection_reason="execution_target_missing",
    )
    with pytest.raises(RuntimePolicyError, match="authority rejected"):
        create_execution_snapshot(flow="question_generation", authority_decision=denied)

    missing_target = AuthorityDecisionResult(allowed=True, decision_ref="qauth_missing")
    with pytest.raises(RuntimeValidationError, match="target is required"):
        create_execution_snapshot(flow="question_generation", authority_decision=missing_target)

    invalid_snapshot_input = _question_execution_input(
        snapshot=ExecutionSnapshot(
            flow="feedback_evaluation",
            decision_ref="qauth_invalid_flow",
            execution_target=NODE_REF,
        )
    )
    with pytest.raises(RuntimeValidationError, match="snapshot flow is invalid"):
        QuestionExecutionHandler(repository).persist_result(
            invalid_snapshot_input
        )

    assert repository.questions == []


def test_feedback_execution_flow_metadata_is_trace_only_and_payload_scoped() -> None:
    execution_flow = feedback_execution_flow_metadata(
        owner_id=OWNER_ID,
        session_id=SESSION_ID,
        answer_id="answer_execution_flow",
        task_id="task_feedback_execution_flow",
    )

    payload = feedback_payload_with_execution_flow(
        {"status": "generated", "feedback_metadata": {"provider_status": "called"}},
        execution_flow=execution_flow,
    )

    assert execution_flow["flow"] == "feedback_evaluation"
    assert execution_flow["decision_ref"].startswith("feedback_eval_")
    assert execution_flow["decision_ref_contract"] == "trace_only"
    assert execution_flow["durable_idempotency_contract"] is False
    assert execution_flow["execution_target"] == "answer_execution_flow"
    assert payload["feedback_metadata"]["provider_status"] == "called"
    assert payload["feedback_metadata"]["execution_flow"] == execution_flow


def test_progress_projection_refresh_and_canonical_write_are_separate_handlers() -> None:
    service = _ProgressTreeService()
    detail = _ProgressDetail()

    projection = ProgressProjectionRefreshHandler(service).refresh(detail, regenerate=False)

    assert projection["status"] == "ready"
    assert service.refresh_calls == 1
    assert service.generate_calls == 0

    repository = _ProgressRepository()
    session = _session()
    written = ProgressCanonicalWriteHandler(repository).write(session)

    assert written is session
    assert repository.updated_sessions == [session]
    assert service.refresh_calls == 1


def _question_execution_input(*, snapshot: ExecutionSnapshot | None = None) -> QuestionExecutionInput:
    return QuestionExecutionInput(
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        ai_task_id="task_execution_flow",
        agent_run_id="agent_execution_flow",
        candidate=_accepted_candidate(),
        snapshot=snapshot
        or ExecutionSnapshot(
            flow="question_generation",
            decision_ref="qauth_execution_flow",
            execution_target=NODE_REF,
        ),
        trace_refs=("trace_execution_flow",),
        contract_ids=("P-POLISH-QUESTION",),
    )


def _accepted_candidate() -> dict[str, Any]:
    return {
        "candidate_ref": "candidate_execution_flow",
        "question_text": "Explain how you make an async write path observable and idempotent.",
        "question_sources": (
            {
                "index": 1,
                "source_type": "resume_project",
                "title": "Async payment pipeline",
                "excerpt": "Designed retries, idempotency keys and metrics.",
                "ref_id": "evidence_execution_flow",
                "availability": "available",
            },
        ),
        "progress_node_ref": NODE_REF,
        "evidence_refs": ("evidence_execution_flow",),
        "context_digest": "ctx_execution_flow",
        "question_metadata": {
            "generation_mode": "new_question",
            "request_source": "explicit_selected_category",
            "selected_progress_node_ref": NODE_REF,
        },
        "quality_gate": {"status": "accepted", "passed": True, "blocking_reasons": ()},
    }


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


class _ProgressTreeService:
    def __init__(self) -> None:
        self.generate_calls = 0
        self.refresh_calls = 0

    def generate_initial(self, context: dict[str, Any]) -> dict[str, Any]:
        self.generate_calls += 1
        return {"status": "ready", "progress_percent": 0, "progress_tree_plan": {}, "progress_tree_state": {}}

    def refresh_state(
        self,
        *,
        context: dict[str, Any],
        existing_plan: dict[str, Any],
        existing_state: dict[str, Any],
    ) -> dict[str, Any]:
        self.refresh_calls += 1
        return {
            "status": "ready",
            "progress_percent": 50,
            "progress_tree_plan": existing_plan,
            "progress_tree_state": existing_state,
        }


class _ProgressDetail:
    progress_context = {"content_digest": "ctx_progress_projection"}
    progress_tree_plan = {"status": "ready", "nodes": []}
    progress_tree_state = {"status": "ready", "node_states": []}


class _ProgressRepository:
    def __init__(self) -> None:
        self.updated_sessions: list[PolishSession] = []

    def update_progress_tree(self, session: PolishSession) -> None:
        self.updated_sessions.append(session)


def _session() -> PolishSession:
    now = utc_now()
    return PolishSession(
        session_id=SESSION_ID,
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        binding_id="binding_execution_flow",
        resume_id="resume_execution_flow",
        resume_version_id="resume_version_execution_flow",
        job_id="job_execution_flow",
        job_version_id="job_version_execution_flow",
        status="running",
        topic_id="topic_execution_flow",
        subtopic_id=None,
        custom_topic_text_summary=None,
        created_at=now,
        updated_at=now,
        progress_tree_status="ready",
        progress_percent=50,
        progress_tree_plan={"status": "ready"},
        progress_tree_state={"status": "ready"},
    )
