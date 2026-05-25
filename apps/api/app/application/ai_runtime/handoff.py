"""AI Runtime persistence handoff contract and Core-safe write helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
import json
from typing import Any, Callable, Protocol

from app.application.ai_runtime.contracts import RuntimePolicyError, RuntimeValidationError, contains_sensitive_payload
from app.application.polish.entities import PolishQuestion, PolishQuestionSource, PolishTaskStatus
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import AiTaskStatus
from app.domain.shared.ids import ResourceIdPrefix, generate_resource_id
from app.domain.shared.refs import ResourceRef, TraceRef


@dataclass(frozen=True)
class HandoffRequest:
    owner_id: str
    run_id: str
    target_type: str
    candidate_refs: tuple[str, ...] = field(default_factory=tuple)
    trace_refs: tuple[str, ...] = field(default_factory=tuple)
    validation_result_ref: str | None = None
    side_effect_key: str | None = None


@dataclass(frozen=True)
class HandoffPlan:
    owner_id: str
    run_id: str
    target_type: str
    candidate_refs: tuple[str, ...]
    trace_refs: tuple[str, ...]
    validation_result_ref: str
    side_effect_key: str
    formal_refs: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class QuestionResultWritePlan:
    owner_id: str
    actor_id: str
    session_id: str
    ai_task_id: str
    agent_run_id: str
    candidate_ref: str
    question_text: str
    question_sources: tuple[dict[str, Any], ...]
    progress_node_ref: str
    evidence_refs: tuple[str, ...]
    context_digest: str
    question_metadata: dict[str, Any]
    quality_gate: dict[str, Any]
    trace_refs: tuple[str, ...]
    validation_result_ref: str
    side_effect_key: str
    candidate_digest: str
    contract_ids: tuple[str, ...]


@dataclass(frozen=True)
class QuestionResultWriteResult:
    question: PolishQuestion
    question_ref: ResourceRef
    task_status: PolishTaskStatus
    created: bool


class QuestionRepositoryForHandoff(Protocol):
    def list_questions_for_session(self, owner_id: str, session_id: str) -> tuple[PolishQuestion, ...]: ...

    def add_question(self, question: PolishQuestion) -> None: ...

    def add_question_once(
        self,
        *,
        owner_id: str,
        session_id: str,
        graph_persistence_idempotency_key: str,
        question: PolishQuestion,
    ) -> tuple[PolishQuestion, bool]: ...


class AgentPersistenceHandoff:
    def prepare_handoff(self, request: HandoffRequest) -> HandoffPlan:
        if not request.trace_refs:
            raise RuntimeValidationError("handoff requires trace refs")
        if not request.validation_result_ref:
            raise RuntimeValidationError("handoff requires validation result ref")
        if not request.side_effect_key:
            raise RuntimeValidationError("handoff requires side effect key")
        return HandoffPlan(
            owner_id=request.owner_id,
            run_id=request.run_id,
            target_type=request.target_type,
            candidate_refs=request.candidate_refs,
            trace_refs=request.trace_refs,
            validation_result_ref=request.validation_result_ref,
            side_effect_key=request.side_effect_key,
            formal_refs=(),
        )

    def write_question_result(
        self,
        plan: HandoffPlan | QuestionResultWritePlan,
        *,
        question_repository: QuestionRepositoryForHandoff | None = None,
        question_id_factory: Callable[[], str] | None = None,
        now: datetime | None = None,
    ) -> QuestionResultWriteResult | None:
        if isinstance(plan, HandoffPlan):
            self._fail_closed(plan)
        if not isinstance(plan, QuestionResultWritePlan):
            raise RuntimePolicyError("unsupported question result handoff plan")
        if question_repository is None:
            raise RuntimePolicyError("question result handoff requires Core repository")
        _assert_safe_question_write_plan(plan)

        timestamp = now or utc_now()
        question_id = (
            question_id_factory()
            if question_id_factory is not None
            else generate_resource_id(ResourceIdPrefix.QUESTION)
        )
        question = PolishQuestion(
            question_id=question_id,
            owner_id=plan.owner_id,
            actor_id=plan.actor_id,
            session_id=plan.session_id,
            ai_task_id=plan.ai_task_id,
            question_text=plan.question_text,
            question_sources=_question_sources_to_entities(plan.question_sources),
            progress_node_ref=plan.progress_node_ref,
            evidence_refs=plan.evidence_refs,
            context_digest=plan.context_digest,
            question_metadata=_question_metadata_for_write(plan),
            status="generated",
            created_at=timestamp,
            updated_at=timestamp,
        )

        add_question_once = getattr(question_repository, "add_question_once", None)
        if callable(add_question_once):
            persisted_question, created = add_question_once(
                owner_id=plan.owner_id,
                session_id=plan.session_id,
                graph_persistence_idempotency_key=plan.side_effect_key,
                question=question,
            )
            return _question_write_result(
                question=persisted_question,
                plan=plan,
                created=created,
                timestamp=timestamp,
            )

        # Backward compatibility for legacy/fake repositories that predate
        # repository-level idempotent writes. Production Polish persistence
        # should implement add_question_once to avoid naked read-then-write races.
        existing = _find_existing_question(question_repository, plan)
        if existing is not None:
            return _question_write_result(question=existing, plan=plan, created=False, timestamp=timestamp)

        question_repository.add_question(question)
        return _question_write_result(question=question, plan=plan, created=True, timestamp=timestamp)

    def write_feedback_result(self, plan: HandoffPlan) -> None:
        self._fail_closed(plan)

    def write_report_result(self, plan: HandoffPlan) -> None:
        self._fail_closed(plan)

    def write_review_result(self, plan: HandoffPlan) -> None:
        self._fail_closed(plan)

    def write_candidate_result(self, plan: HandoffPlan) -> None:
        self._fail_closed(plan)

    def finalize_after_confirmation(self, plan: HandoffPlan) -> None:
        self._fail_closed(plan)

    def _fail_closed(self, plan: HandoffPlan) -> None:
        raise RuntimePolicyError(f"{plan.target_type} formal write is PR5+ or later PR only")


def build_question_result_write_plan(
    *,
    owner_id: str,
    actor_id: str,
    session_id: str,
    ai_task_id: str,
    agent_run_id: str,
    candidate: dict[str, Any],
    progress_node_ref: str | None,
    trace_refs: tuple[str, ...],
    contract_ids: tuple[str, ...],
) -> QuestionResultWritePlan:
    if contains_sensitive_payload(candidate):
        raise RuntimePolicyError("question candidate contains raw or sensitive payload")
    quality_gate = candidate.get("quality_gate") if isinstance(candidate.get("quality_gate"), dict) else {}
    if not _quality_gate_accepted(quality_gate):
        raise RuntimeValidationError("question candidate quality gate is not accepted")

    question_text = str(candidate.get("question_text") or "").strip()
    resolved_progress_node_ref = str(candidate.get("progress_node_ref") or progress_node_ref or "").strip()
    context_digest = str(candidate.get("context_digest") or "").strip()
    evidence_refs = _clean_text_tuple(candidate.get("evidence_refs", ()))
    candidate_ref = str(candidate.get("candidate_ref") or "").strip()
    if not question_text:
        raise RuntimeValidationError("question candidate text is required")
    if not resolved_progress_node_ref:
        raise RuntimeValidationError("question candidate progress node ref is required")
    if not context_digest:
        raise RuntimeValidationError("question candidate context digest is required")
    if not evidence_refs:
        raise RuntimeValidationError("question candidate evidence refs are required")
    if not candidate_ref:
        raise RuntimeValidationError("question candidate ref is required")

    question_sources = _question_sources_from_candidate(candidate)
    if contains_sensitive_payload(question_sources):
        raise RuntimePolicyError("question candidate sources contain raw or sensitive payload")
    question_metadata = (
        candidate.get("question_metadata") if isinstance(candidate.get("question_metadata"), dict) else {}
    )
    if contains_sensitive_payload(question_metadata):
        raise RuntimePolicyError("question candidate metadata contains raw or sensitive payload")

    candidate_digest = _stable_json_digest(
        {
            "candidate_ref": candidate_ref,
            "question_text": question_text,
            "evidence_refs": evidence_refs,
            "progress_node_ref": resolved_progress_node_ref,
            "context_digest": context_digest,
            "quality_gate": quality_gate,
        }
    )
    combined_trace_refs = _unique_texts((*trace_refs, *_clean_text_tuple(candidate.get("trace_refs", ()))))
    validation_result_ref = _validation_ref(combined_trace_refs, candidate_ref)
    side_effect_key = "polish_question:" + _stable_json_digest(
        {
            "owner_id": owner_id,
            "session_id": session_id,
            "progress_node_ref": resolved_progress_node_ref,
            "candidate_digest": candidate_digest,
            "context_digest": context_digest,
        }
    )
    return QuestionResultWritePlan(
        owner_id=owner_id,
        actor_id=actor_id,
        session_id=session_id,
        ai_task_id=ai_task_id,
        agent_run_id=agent_run_id,
        candidate_ref=candidate_ref,
        question_text=question_text,
        question_sources=question_sources,
        progress_node_ref=resolved_progress_node_ref,
        evidence_refs=evidence_refs,
        context_digest=context_digest,
        question_metadata=dict(question_metadata),
        quality_gate=dict(quality_gate),
        trace_refs=combined_trace_refs,
        validation_result_ref=validation_result_ref,
        side_effect_key=side_effect_key,
        candidate_digest=candidate_digest,
        contract_ids=contract_ids,
    )


def _assert_safe_question_write_plan(plan: QuestionResultWritePlan) -> None:
    if contains_sensitive_payload(
        {
            "question_text": plan.question_text,
            "question_sources": plan.question_sources,
            "question_metadata": plan.question_metadata,
            "quality_gate": plan.quality_gate,
            "trace_refs": plan.trace_refs,
        }
    ):
        raise RuntimePolicyError("question result handoff contains raw or sensitive payload")
    if not _quality_gate_accepted(plan.quality_gate):
        raise RuntimeValidationError("question candidate quality gate is not accepted")
    if not plan.trace_refs or not plan.validation_result_ref or not plan.side_effect_key:
        raise RuntimeValidationError("question result handoff requires trace, validation, and side effect refs")


def _find_existing_question(
    question_repository: QuestionRepositoryForHandoff, plan: QuestionResultWritePlan
) -> PolishQuestion | None:
    for question in question_repository.list_questions_for_session(plan.owner_id, plan.session_id):
        metadata = question.question_metadata if isinstance(question.question_metadata, dict) else {}
        if metadata.get("graph_persistence_idempotency_key") == plan.side_effect_key:
            return question
    return None


def _question_write_result(
    *, question: PolishQuestion, plan: QuestionResultWritePlan, created: bool, timestamp: datetime
) -> QuestionResultWriteResult:
    question_ref = ResourceRef(resource_type="question", resource_id=question.question_id)
    candidate_refs = (
        question_ref,
        ResourceRef(resource_type="agent_run", resource_id=plan.agent_run_id),
        ResourceRef(resource_type="question_candidate", resource_id=plan.candidate_ref),
        ResourceRef(resource_type="progress_node", resource_id=question.progress_node_ref or plan.progress_node_ref),
        *tuple(ResourceRef(resource_type="evidence", resource_id=ref) for ref in question.evidence_refs),
        *tuple(ResourceRef(resource_type="trace", resource_id=ref) for ref in plan.trace_refs),
    )
    task_status = PolishTaskStatus(
        ai_task_id=plan.ai_task_id,
        task_type="polish_question_generation",
        status=AiTaskStatus.SUCCEEDED,
        contract_ids=plan.contract_ids,
        retryable=False,
        result_ref=TraceRef(trace_ref_id=question.question_id, trace_type="question", created_at=timestamp),
        user_visible_status="题目已生成",
        candidate_refs=candidate_refs,
    )
    return QuestionResultWriteResult(
        question=question, question_ref=question_ref, task_status=task_status, created=created
    )


def _question_metadata_for_write(plan: QuestionResultWritePlan) -> dict[str, Any]:
    metadata = dict(plan.question_metadata)
    metadata.update(
        {
            "llm_generation_mode": metadata.get("llm_generation_mode", "graph_candidate_handoff"),
            "graph_candidate_ref": plan.candidate_ref,
            "graph_agent_run_id": plan.agent_run_id,
            "graph_trace_refs": list(plan.trace_refs),
            "graph_validation_result_ref": plan.validation_result_ref,
            "graph_persistence_idempotency_key": plan.side_effect_key,
            "candidate_digest": plan.candidate_digest,
            "quality_gate": plan.quality_gate,
            "context_digest": plan.context_digest,
            "progress_node_ref": plan.progress_node_ref,
            "sanitized": True,
        }
    )
    return metadata


def _question_sources_to_entities(raw_sources: tuple[dict[str, Any], ...]) -> tuple[PolishQuestionSource, ...]:
    sources: list[PolishQuestionSource] = []
    for index, source in enumerate(raw_sources, start=1):
        if not isinstance(source, dict):
            continue
        sources.append(
            PolishQuestionSource(
                index=int(source.get("index") or index),
                source_type=str(source.get("source_type") or "evidence"),
                title=str(source.get("title") or source.get("ref_id") or f"evidence-{index}"),
                excerpt=str(source.get("excerpt") or ""),
                ref_id=str(source.get("ref_id")) if source.get("ref_id") is not None else None,
                availability=str(source.get("availability") or "available"),
            )
        )
    return tuple(sources)


def _question_sources_from_candidate(candidate: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    raw_sources = candidate.get("question_sources")
    if isinstance(raw_sources, (list, tuple)):
        return tuple(dict(source) for source in raw_sources if isinstance(source, dict))
    refs = _clean_text_tuple(candidate.get("evidence_refs", ()))
    return tuple(
        {
            "index": index,
            "source_type": "evidence",
            "title": ref,
            "excerpt": str(candidate.get("source_excerpt") or ""),
            "ref_id": ref,
            "availability": "available",
        }
        for index, ref in enumerate(refs, start=1)
    )


def _quality_gate_accepted(quality_gate: dict[str, Any]) -> bool:
    status = str(quality_gate.get("status") or "").strip().lower()
    if status in {"accepted", "passed"}:
        return True
    if status in {"blocked", "failed", "rejected"}:
        return False
    return quality_gate.get("passed") is True


def _validation_ref(trace_refs: tuple[str, ...], candidate_ref: str) -> str:
    for trace_ref in trace_refs:
        if "validation" in trace_ref:
            return trace_ref
    return candidate_ref


def _clean_text_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple, set)):
        return ()
    return _unique_texts(tuple(str(item).strip() for item in value if str(item).strip()))


def _unique_texts(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)


def _stable_json_digest(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()
