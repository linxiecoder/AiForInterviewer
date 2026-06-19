"""Execution flow handlers for Polish application orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from typing import Any

from app.application.ai_runtime.contracts import RuntimePolicyError, RuntimeValidationError
from app.application.ai_runtime.handoff import (
    AgentPersistenceHandoff,
    QuestionRepositoryForHandoff,
    QuestionResultWriteResult,
    build_question_result_write_plan,
)
from app.application.polish.feedback_generation_service import (
    FeedbackGenerationContext,
    FeedbackGenerationResult,
    FeedbackGenerationService,
)
from app.application.polish.ports import AuthorityDecisionResult, PolishRepository, PolishSession


@dataclass(frozen=True)
class ExecutionSnapshot:
    flow: str
    decision_ref: str
    execution_target: str
    runtime_flags: tuple[str, ...] = ()
    asset_snapshot: tuple[str, ...] = ()
    decision_ref_contract: str = "trace_only"
    durable_idempotency_contract: bool = False

    def to_metadata(self) -> dict[str, Any]:
        return {
            "flow": self.flow,
            "decision_ref": self.decision_ref,
            "decision_ref_contract": self.decision_ref_contract,
            "durable_idempotency_contract": self.durable_idempotency_contract,
            "execution_target": self.execution_target,
            "runtime_flags": list(self.runtime_flags),
            "asset_snapshot": list(self.asset_snapshot),
        }


@dataclass(frozen=True)
class QuestionExecutionInput:
    owner_id: str
    actor_id: str
    session_id: str
    ai_task_id: str
    agent_run_id: str
    candidate: dict[str, Any]
    snapshot: ExecutionSnapshot
    trace_refs: tuple[str, ...]
    contract_ids: tuple[str, ...]


class QuestionExecutionHandler:
    def __init__(
        self,
        question_repository: QuestionRepositoryForHandoff,
        *,
        handoff: AgentPersistenceHandoff | None = None,
    ) -> None:
        self._question_repository = question_repository
        self._handoff = handoff or AgentPersistenceHandoff()

    def persist_result(
        self,
        execution_input: QuestionExecutionInput,
        *,
        now: datetime | None = None,
    ) -> QuestionResultWriteResult:
        snapshot = execution_input.snapshot
        if not isinstance(snapshot, ExecutionSnapshot):
            raise RuntimeValidationError("question execution snapshot is required")
        if snapshot.flow != "question_generation":
            raise RuntimeValidationError("question execution snapshot flow is invalid")
        if not snapshot.execution_target:
            raise RuntimeValidationError("question execution snapshot target is required")

        candidate = question_candidate_with_execution_flow(
            execution_input.candidate,
            snapshot=snapshot,
        )
        plan = build_question_result_write_plan(
            owner_id=execution_input.owner_id,
            actor_id=execution_input.actor_id,
            session_id=execution_input.session_id,
            ai_task_id=execution_input.ai_task_id,
            agent_run_id=execution_input.agent_run_id,
            candidate=candidate,
            progress_node_ref=snapshot.execution_target,
            trace_refs=execution_input.trace_refs,
            contract_ids=execution_input.contract_ids,
        )
        write_result = self._handoff.write_question_result(
            plan,
            question_repository=self._question_repository,
            now=now,
        )
        if write_result is None:
            raise RuntimePolicyError("question execution handoff did not persist a result")
        return write_result


class FeedbackExecutionHandler:
    def __init__(self, generation_service: FeedbackGenerationService) -> None:
        self._generation_service = generation_service

    def generate(self, context: FeedbackGenerationContext) -> FeedbackGenerationResult:
        return self._generation_service.generate_feedback_v1(context)


class ProgressCanonicalWriteHandler:
    def __init__(self, repository: PolishRepository) -> None:
        self._repository = repository

    def write(self, session: PolishSession) -> PolishSession:
        self._repository.update_progress_tree(session)
        return session


class ProgressProjectionRefreshHandler:
    def __init__(self, progress_tree_service: Any) -> None:
        self._progress_tree_service = progress_tree_service

    def refresh(self, detail: Any, *, regenerate: bool) -> dict[str, Any]:
        if regenerate:
            return self._progress_tree_service.generate_initial(detail.progress_context)
        return self._progress_tree_service.refresh_state(
            context=detail.progress_context,
            existing_plan=detail.progress_tree_plan,
            existing_state=detail.progress_tree_state,
        )


def question_candidate_with_execution_flow(
    candidate: dict[str, Any],
    *,
    snapshot: ExecutionSnapshot,
) -> dict[str, Any]:
    enriched = dict(candidate)
    metadata = enriched.get("question_metadata") if isinstance(enriched.get("question_metadata"), dict) else {}
    metadata = dict(metadata)
    metadata["execution_flow"] = snapshot.to_metadata()
    enriched["question_metadata"] = metadata
    return enriched


def create_execution_snapshot(
    *,
    flow: str,
    authority_decision: AuthorityDecisionResult,
    runtime_flags: Any = (),
    asset_refs: Any = (),
) -> ExecutionSnapshot:
    if not authority_decision.allowed:
        raise RuntimePolicyError("execution snapshot authority rejected")
    if not authority_decision.execution_target:
        raise RuntimeValidationError("execution snapshot target is required")
    return ExecutionSnapshot(
        flow=flow,
        decision_ref=authority_decision.decision_ref,
        execution_target=authority_decision.execution_target,
        runtime_flags=_freeze_snapshot_values(runtime_flags),
        asset_snapshot=_freeze_snapshot_values(asset_refs),
    )


def feedback_execution_flow_metadata(
    *,
    owner_id: str,
    session_id: str,
    answer_id: str,
    task_id: str,
) -> dict[str, Any]:
    decision_ref = "feedback_eval_" + _short_digest(owner_id, session_id, answer_id, task_id)
    return _execution_flow_metadata(
        flow="feedback_evaluation",
        decision_ref=decision_ref,
        execution_target=answer_id,
    )


def feedback_payload_with_execution_flow(
    payload: dict[str, Any],
    *,
    execution_flow: dict[str, Any],
) -> dict[str, Any]:
    enriched = dict(payload)
    metadata = enriched.get("feedback_metadata") if isinstance(enriched.get("feedback_metadata"), dict) else {}
    enriched["feedback_metadata"] = dict(metadata) | {"execution_flow": dict(execution_flow)}
    return enriched


def _execution_flow_metadata(
    *,
    flow: str,
    decision_ref: str,
    execution_target: str | None,
) -> dict[str, Any]:
    return {
        "flow": flow,
        "decision_ref": decision_ref,
        "decision_ref_contract": "trace_only",
        "durable_idempotency_contract": False,
        "execution_target": execution_target,
    }


def _short_digest(*parts: str) -> str:
    joined = "|".join(parts)
    return sha256(joined.encode("utf-8")).hexdigest()[:16]


def _freeze_snapshot_values(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, dict):
        items = (
            f"{key}={value[key]}"
            for key in sorted(value)
            if value[key] is not None and str(value[key])
        )
        return tuple(str(item) for item in items)
    if isinstance(value, (str, bytes)):
        text = value.decode("utf-8", errors="ignore") if isinstance(value, bytes) else value
        return (text,) if text else ()
    try:
        return tuple(str(item) for item in value if item is not None and str(item))
    except TypeError:
        text = str(value)
        return (text,) if text else ()
