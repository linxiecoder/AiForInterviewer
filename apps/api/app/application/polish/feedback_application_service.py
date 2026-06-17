"""Focused application service for Polish feedback operations."""

from __future__ import annotations

import json
import threading
import time
from hashlib import sha256
from typing import Any, Protocol

from app.application.common.logging import LogUtil
from app.application.common.result import ApplicationResult
from app.application.polish.agents.feedback import build_feedback_planned_handoff
from app.application.polish.commands import CreatePolishFeedbackTaskCommand
from app.application.polish.context_hygiene import normalize_context_hygiene_metadata
from app.application.polish.entities import (
    PolishFeedback,
    PolishQuestionSource,
    PolishSession,
    PolishSessionAnswerDetail,
    PolishSessionDetail,
    PolishSessionTurn,
    PolishTaskStatus,
)
from app.application.polish.feedback_generation_service import (
    FeedbackGenerationContext,
    FeedbackGenerationService,
)
from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
    POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
    POLISH_FEEDBACK_TASK_TYPE,
)
from app.application.polish.next_question_authorization import (
    feedback_next_question_authorization_metadata,
)
from app.application.polish.ports import PolishRepository
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import AiTaskStatus
from app.domain.shared.errors import DomainError
from app.domain.shared.ids import ResourceIdPrefix, generate_resource_id
from app.domain.shared.refs import ResourceRef, TraceRef
from app.usecases.polish import PersistPolishResultCommand, PolishPersistResultUseCase


class _FeedbackOperations(Protocol):
    _polish_repository: PolishRepository
    _feedback_generation_service: FeedbackGenerationService

    def _build_session_detail(
        self,
        *,
        owner_id: str,
        session: PolishSession,
        include_turns: bool = True,
    ) -> PolishSessionDetail: ...


_FEEDBACK_GENERATION_LOCKS_GUARD = threading.Lock()
_FEEDBACK_GENERATION_LOCKS: dict[tuple[str, str, str], threading.Lock] = {}
_FEEDBACK_IDEMPOTENCY_KEY_MAX_LENGTH = 128
_FEEDBACK_SYNC_WAIT_SECONDS = 0.25


class PolishFeedbackApplicationService:
    def __init__(self, operations: _FeedbackOperations) -> None:
        self._operations = operations

    def bind(self, operations: _FeedbackOperations) -> None:
        self._operations = operations

    def create_feedback_task(
        self,
        command: CreatePolishFeedbackTaskCommand,
    ) -> ApplicationResult[PolishTaskStatus]:
        idempotency_key = _normalize_feedback_idempotency_key(getattr(command, "idempotency_key", None))
        idempotency_key_error = _validate_feedback_idempotency_key(idempotency_key)
        if idempotency_key_error is not None:
            return ApplicationResult(error=idempotency_key_error)
        request_body_hash = _feedback_request_body_hash(command)

        session = self._operations._polish_repository.get_session(command.owner_id, command.session_id)
        if session is None:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Polish session not found")
            )
        answer = self._operations._polish_repository.get_answer(command.owner_id, command.answer_id)
        if answer is None or answer.session_id != command.session_id:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Answer not found")
            )
        question = self._operations._polish_repository.get_question(command.owner_id, answer.question_id)
        if question is None or question.session_id != command.session_id:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Question not found")
            )

        feedback_lock = _feedback_generation_lock(
            owner_id=command.owner_id,
            session_id=command.session_id,
            answer_id=answer.answer_id,
        )
        with feedback_lock:
            if idempotency_key is not None:
                replay_result = _feedback_idempotency_lookup(
                    self._operations._polish_repository,
                    owner_id=command.owner_id,
                    idempotency_key=idempotency_key,
                    request_body_hash=request_body_hash,
                )
                replay_status = replay_result.get("status") if isinstance(replay_result, dict) else None
                if replay_status == "conflict":
                    return ApplicationResult(
                        error=DomainError(
                            code="idempotency_conflict",
                            message="Feedback task idempotency key conflicts with request body",
                            details={
                                "field": "idempotency_key",
                                "reason": "idempotency_conflict",
                            },
                        )
                    )
                if replay_status == "orphan":
                    return ApplicationResult(
                        error=DomainError(
                            code="generation_failed",
                            message="Feedback task result is incomplete and requires retry",
                            details={
                                "reason": "orphan_feedback_task_result",
                                "ai_task_id": str(replay_result.get("ai_task_id") or ""),
                            },
                            retryable=True,
                        )
                    )
                replay_feedback = replay_result.get("feedback") if isinstance(replay_result, dict) else None
                if isinstance(replay_feedback, PolishFeedback):
                    return ApplicationResult(value=_existing_feedback_task(replay_feedback))

            existing_feedback = self._operations._polish_repository.get_latest_feedback_for_answer(
                owner_id=command.owner_id,
                answer_id=answer.answer_id,
                status="generated",
            )
            if (
                existing_feedback is not None
                and existing_feedback.session_id == command.session_id
                and _has_generated_feedback_payload(existing_feedback)
            ):
                return ApplicationResult(value=_existing_generated_feedback_task(existing_feedback))

            detail = self._operations._build_session_detail(owner_id=command.owner_id, session=session)
            turn = next((item for item in detail.turns if item.question_id == question.question_id), None)
            if turn is None:
                return ApplicationResult(
                    error=DomainError(code="not_found_or_inaccessible", message="Answer turn not found")
                )
            answer_detail = next((item for item in turn.answers if item.answer_id == answer.answer_id), None)
            if answer_detail is None:
                return ApplicationResult(
                    error=DomainError(code="not_found_or_inaccessible", message="Answer turn not found")
                )

            generation_started_at = time.perf_counter()
            LogUtil.feedback_generation_started(
                session_id=session.session_id,
                question_id=question.question_id,
                answer_id=answer.answer_id,
            )
            now = utc_now()
            task_id = generate_resource_id(ResourceIdPrefix.TASK)
            feedback_id = generate_resource_id(ResourceIdPrefix.TRACE)
            generation_context = _build_feedback_generation_context(
                detail=detail,
                turn=turn,
                answer=answer_detail,
                owner_id=command.owner_id,
                actor_id=command.actor_id,
            )
            running_task = PolishTaskStatus(
                ai_task_id=task_id,
                task_type=POLISH_FEEDBACK_TASK_TYPE,
                status=AiTaskStatus.RUNNING,
                contract_ids=POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
                retryable=False,
                result_ref=TraceRef(trace_ref_id=task_id, trace_type="ai_task", created_at=now),
                user_visible_status="反馈生成中",
            )
            running_persist_result = _persist_feedback_running_task(
                self._operations._polish_repository,
                task=running_task,
                owner_id=command.owner_id,
                actor_id=command.actor_id,
                target_ref_id=command.answer_id,
                idempotency_record_id=_feedback_idempotency_record_id(
                    idempotency_key,
                    request_body_hash,
                ),
            )
            if not running_persist_result.is_success:
                return running_persist_result

            completion: dict[str, ApplicationResult[PolishTaskStatus] | None] = {"result": None}

            def run_generation() -> None:
                completion["result"] = _complete_feedback_generation(
                    self._operations,
                    generation_context=generation_context,
                    owner_id=command.owner_id,
                    actor_id=command.actor_id,
                    session_id=session.session_id,
                    question_id=question.question_id,
                    answer_id=answer.answer_id,
                    task_id=task_id,
                    feedback_id=feedback_id,
                    target_ref_id=command.answer_id,
                    idempotency_record_id=_feedback_idempotency_record_id(
                        idempotency_key,
                        request_body_hash,
                    ),
                    generation_started_at=generation_started_at,
                )

            generation_thread = threading.Thread(
                target=run_generation,
                name=f"feedback-generation-{task_id}",
                daemon=True,
            )
            generation_thread.start()
            generation_thread.join(_FEEDBACK_SYNC_WAIT_SECONDS)
            if completion["result"] is not None:
                return completion["result"]
            return ApplicationResult(value=running_task)


def _complete_feedback_generation(
    operations: _FeedbackOperations,
    *,
    generation_context: FeedbackGenerationContext,
    owner_id: str,
    actor_id: str,
    session_id: str,
    question_id: str,
    answer_id: str,
    task_id: str,
    feedback_id: str,
    target_ref_id: str,
    idempotency_record_id: str | None,
    generation_started_at: float,
) -> ApplicationResult[PolishTaskStatus]:
    now = utc_now()
    generation_result = operations._feedback_generation_service.generate_feedback_v1(generation_context)
    if not generation_result.succeeded or generation_result.payload is None:
        failed_payload = _failed_feedback_payload_for_storage(
            session_id=session_id,
            question_id=question_id,
            answer_id=answer_id,
            feedback_id=feedback_id,
            validation_errors=generation_result.validation_errors,
            metadata=generation_result.metadata,
        )
        task = PolishTaskStatus(
            ai_task_id=task_id,
            task_type=POLISH_FEEDBACK_TASK_TYPE,
            status=AiTaskStatus.GENERATION_FAILED,
            contract_ids=POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
            retryable=True,
            result_ref=TraceRef(trace_ref_id=task_id, trace_type="validation_result", created_at=now),
            user_visible_status="反馈生成失败，可重试",
            validation_errors=generation_result.validation_errors,
        )
        feedback = PolishFeedback(
            feedback_id=feedback_id,
            owner_id=owner_id,
            actor_id=actor_id,
            session_id=session_id,
            answer_id=answer_id,
            ai_task_id=task_id,
            score_result_id=None,
            feedback_summary=json.dumps(failed_payload, ensure_ascii=False, sort_keys=True),
            status=str(AiTaskStatus.GENERATION_FAILED),
            created_at=now,
            updated_at=now,
        )
        generation_log_fields = _feedback_generation_log_fields(generation_result.metadata)
        LogUtil.feedback_generation_failed(
            session_id=session_id,
            question_id=question_id,
            answer_id=answer_id,
            error_code=(
                generation_result.validation_errors[0]
                if generation_result.validation_errors
                else None
            ),
            duration_ms=_feedback_generation_duration_ms(generation_started_at),
            **generation_log_fields,
        )
        return _persist_feedback_task_result(
            operations._polish_repository,
            feedback=feedback,
            task=task,
            owner_id=owner_id,
            actor_id=actor_id,
            target_ref_id=target_ref_id,
            idempotency_record_id=idempotency_record_id,
        )

    payload = _generated_feedback_payload_for_storage(
        generation_result.payload,
        session_id=session_id,
        question_id=question_id,
        answer_id=answer_id,
        feedback_id=feedback_id,
    )
    planned_feedback_handoff = build_feedback_planned_handoff(
        payload=payload,
        generation_result=generation_result,
        context=generation_context,
        task_id=task_id,
        feedback_id=feedback_id,
    )
    payload = planned_feedback_handoff.payload
    feedback = PolishFeedback(
        feedback_id=feedback_id,
        owner_id=owner_id,
        actor_id=actor_id,
        session_id=session_id,
        answer_id=answer_id,
        ai_task_id=task_id,
        score_result_id=None,
        feedback_summary=json.dumps(payload, ensure_ascii=False, sort_keys=True),
        status="generated",
        created_at=now,
        updated_at=now,
    )
    task = PolishTaskStatus(
        ai_task_id=task_id,
        task_type=POLISH_FEEDBACK_TASK_TYPE,
        status=AiTaskStatus.SUCCEEDED,
        contract_ids=POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
        retryable=False,
        result_ref=TraceRef(trace_ref_id=feedback_id, trace_type="feedback", created_at=now),
        user_visible_status="反馈已生成",
        candidate_refs=planned_feedback_handoff.task_candidate_refs,
    )
    persist_result = _persist_feedback_task_result(
        operations._polish_repository,
        feedback=feedback,
        task=task,
        owner_id=owner_id,
        actor_id=actor_id,
        target_ref_id=target_ref_id,
        idempotency_record_id=idempotency_record_id,
    )
    generation_log_fields = _feedback_generation_log_fields(generation_result.metadata)
    LogUtil.feedback_generation_succeeded(
        session_id=session_id,
        question_id=question_id,
        answer_id=answer_id,
        error_code=None,
        duration_ms=_feedback_generation_duration_ms(generation_started_at),
        **generation_log_fields,
    )
    return persist_result


def _feedback_generation_lock(
    *,
    owner_id: str,
    session_id: str,
    answer_id: str,
) -> threading.Lock:
    lock_key = (owner_id, session_id, answer_id)
    with _FEEDBACK_GENERATION_LOCKS_GUARD:
        existing = _FEEDBACK_GENERATION_LOCKS.get(lock_key)
        if existing is None:
            existing = threading.Lock()
            _FEEDBACK_GENERATION_LOCKS[lock_key] = existing
        return existing


def _normalize_feedback_idempotency_key(raw_key: object) -> str | None:
    if raw_key is None:
        return None
    key = str(raw_key).strip()
    return key or None


def _validate_feedback_idempotency_key(idempotency_key: str | None) -> DomainError | None:
    if idempotency_key is None:
        return None
    if len(idempotency_key) > _FEEDBACK_IDEMPOTENCY_KEY_MAX_LENGTH:
        return DomainError(
            code="validation_failed",
            message="Idempotency key is too long",
            details={
                "field": "idempotency_key",
                "max_length": _FEEDBACK_IDEMPOTENCY_KEY_MAX_LENGTH,
                "actual_length": len(idempotency_key),
            },
        )
    return None


def _feedback_request_body_hash(command: CreatePolishFeedbackTaskCommand) -> str:
    payload = {
        "session_id": command.session_id,
        "answer_id": command.answer_id,
        "scoring_context": getattr(command, "internal_scoring_context", None),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _feedback_idempotency_record_id(
    idempotency_key: str | None,
    request_body_hash: str,
) -> str | None:
    if idempotency_key is None:
        return None
    key_hash = sha256(idempotency_key.encode("utf-8")).hexdigest()[:24]
    return f"polish_feedback:{key_hash}:{request_body_hash[:24]}"


def _feedback_idempotency_lookup(
    repository: PolishRepository,
    *,
    owner_id: str,
    idempotency_key: str,
    request_body_hash: str,
) -> dict[str, object]:
    lookup = getattr(repository, "get_feedback_task_idempotency_record", None)
    if not callable(lookup):
        return {"status": "missing"}
    result = lookup(
        owner_id=owner_id,
        idempotency_key=idempotency_key,
        request_body_hash=request_body_hash,
    )
    return result if isinstance(result, dict) else {"status": "missing"}


def _persist_feedback_task_result(
    repository: PolishRepository,
    *,
    feedback: PolishFeedback,
    task: PolishTaskStatus,
    owner_id: str,
    actor_id: str,
    target_ref_id: str,
    idempotency_record_id: str | None,
) -> ApplicationResult[PolishTaskStatus]:
    atomic_writer = getattr(repository, "add_feedback_task_result", None)
    if callable(atomic_writer):
        atomic_writer(
            feedback,
            task,
            owner_id=owner_id,
            actor_id=actor_id,
            target_ref_id=target_ref_id,
            idempotency_record_id=idempotency_record_id,
        )
        return ApplicationResult(value=task)
    return PolishPersistResultUseCase(repository).execute(
        PersistPolishResultCommand(
            feedback=feedback,
            task=task,
            owner_id=owner_id,
            actor_id=actor_id,
            target_ref_id=target_ref_id,
        )
    )


def _persist_feedback_running_task(
    repository: PolishRepository,
    *,
    task: PolishTaskStatus,
    owner_id: str,
    actor_id: str,
    target_ref_id: str,
    idempotency_record_id: str | None,
) -> ApplicationResult[PolishTaskStatus]:
    running_writer = getattr(repository, "add_feedback_running_task", None)
    if callable(running_writer):
        running_writer(
            task,
            owner_id=owner_id,
            actor_id=actor_id,
            target_ref_id=target_ref_id,
            idempotency_record_id=idempotency_record_id,
        )
        return ApplicationResult(value=task)
    add_task = getattr(repository, "add_task", None)
    if callable(add_task):
        add_task(task, owner_id=owner_id, actor_id=actor_id, target_ref_id=target_ref_id)
        return ApplicationResult(value=task)
    return ApplicationResult(
        error=DomainError(code="generation_failed", message="Feedback task repository is unavailable", retryable=True)
    )


def _build_feedback_generation_context(
    *,
    detail: PolishSessionDetail,
    turn: PolishSessionTurn,
    answer: PolishSessionAnswerDetail,
    owner_id: str,
    actor_id: str,
) -> FeedbackGenerationContext:
    progress_context = detail.progress_context if isinstance(detail.progress_context, dict) else {}
    return FeedbackGenerationContext(
        owner_id=owner_id,
        actor_id=actor_id,
        session_id=detail.session.session_id,
        question_id=turn.question_id,
        answer_id=answer.answer_id,
        question_text=turn.question_text,
        answer_text=answer.answer_text,
        answer_round=answer.answer_round,
        polish_theme=detail.session.polish_theme or detail.session.topic_id or "",
        progress_node_ref=turn.progress_node_ref or "",
        question_sources=_feedback_question_sources(turn.question_sources),
        evidence_refs=tuple(ref for ref in turn.evidence_refs if isinstance(ref, str) and ref.strip()),
        same_question_answers=_feedback_same_question_answers(turn=turn, current_answer_id=answer.answer_id),
        same_project_turns=(),
        session_recent_turns=_feedback_recent_turns(detail.turns),
        project_asset_summaries=_canonical_project_asset_items({"canonical_project_assets": progress_context.get("canonical_project_assets")}),
        canonical_project_assets=(
            progress_context.get("canonical_project_assets")
            if isinstance(progress_context.get("canonical_project_assets"), dict)
            else {}
        ),
        retrieved_rag_chunks=(
            progress_context.get("retrieved_rag_chunks")
            if isinstance(progress_context.get("retrieved_rag_chunks"), dict)
            else {}
        ),
        question_metadata=turn.question_metadata if isinstance(turn.question_metadata, dict) else {},
        job_snapshot=_feedback_job_snapshot(progress_context.get("job_snapshot")),
        resume_snapshot=_feedback_resume_snapshot(progress_context.get("resume_snapshot")),
        progress_node_snapshot=_feedback_progress_node_snapshot(
            detail.progress_tree_plan,
            progress_node_ref=turn.progress_node_ref,
            question_text=turn.question_text,
        ),
        progress_state=detail.progress_tree_state if isinstance(detail.progress_tree_state, dict) else {},
    )


def _feedback_generation_log_fields(metadata: dict[str, Any]) -> dict[str, Any]:
    source = metadata if isinstance(metadata, dict) else {}
    return {
        "llm_called": _metadata_bool(source.get("llm_called")),
        "provider_status": _metadata_string(source.get("provider_status")),
        "validation_stage": _metadata_string(source.get("validation_stage")),
        "candidate_valid": _metadata_bool(source.get("candidate_valid")),
        "prompt_char_count": _metadata_int(source.get("prompt_char_count")),
        "evidence_item_count": _metadata_int(source.get("evidence_item_count")),
    }


def _feedback_generation_duration_ms(started_at: float) -> float:
    return round((time.perf_counter() - started_at) * 1000, 3)


def _metadata_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _metadata_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _metadata_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _generated_feedback_payload_for_storage(
    payload: dict[str, Any],
    *,
    session_id: str,
    question_id: str,
    answer_id: str,
    feedback_id: str,
) -> dict[str, Any]:
    stored = dict(payload)
    stored["feedback_id"] = feedback_id
    metadata = stored.get("feedback_metadata")
    stored["feedback_metadata"] = (metadata if isinstance(metadata, dict) else {}) | {
        "generated": True,
        "llm_called": True,
        "task_type": POLISH_FEEDBACK_TASK_TYPE,
        "answer_id": answer_id,
        "question_id": question_id,
        "session_id": session_id,
    }
    stored["feedback_metadata"].update(feedback_next_question_authorization_metadata(stored))
    return stored


def _failed_feedback_payload_for_storage(
    *,
    session_id: str,
    question_id: str,
    answer_id: str,
    feedback_id: str,
    validation_errors: tuple[str, ...],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    error_code = validation_errors[0] if validation_errors else "llm_transport_generation_failed"
    source_metadata = metadata if isinstance(metadata, dict) else {}
    error_type = source_metadata.get("provider_error_type")
    feedback_metadata: dict[str, Any] = {
        "llm_called": _metadata_bool(source_metadata.get("llm_called")) or False,
        "task_type": POLISH_FEEDBACK_TASK_TYPE,
        "answer_id": answer_id,
        "question_id": question_id,
        "session_id": session_id,
    }
    for field_name in (
        "provider_status",
        "candidate_valid",
        "validation_stage",
        "llm_output_validation_status",
        "prompt_version",
        "schema_id",
        "schema_version",
        "provider_error_type",
    ):
        if field_name in source_metadata:
            feedback_metadata[field_name] = source_metadata[field_name]
    if any(
        field_name in source_metadata
        for field_name in (
            "context_hygiene_status",
            "safe_context_metadata",
            "validation_signals",
        )
    ):
        normalized_hygiene = normalize_context_hygiene_metadata(source_metadata)
        for hygiene_field_name in (
            "context_hygiene_status",
            "safe_context_metadata",
            "validation_signals",
        ):
            feedback_metadata[hygiene_field_name] = normalized_hygiene[hygiene_field_name]
    return {
        "schema_id": POLISH_FEEDBACK_FINAL_SCHEMA_ID,
        "schema_version": POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
        "contract_ids": list(POLISH_FEEDBACK_FINAL_CONTRACT_IDS),
        "status": str(AiTaskStatus.GENERATION_FAILED),
        "feedback_id": feedback_id,
        "feedback_text": "反馈生成失败，可重试",
        "answer_summary": "",
        "user_visible_status": "反馈生成失败，可重试",
        "retryable": True,
        "error": {
            "code": error_code,
            "message": "反馈生成超时或失败，可重试",
            "metadata": {"error_type": error_type} if error_type else {},
        },
        "validation_errors": list(validation_errors),
        "score_result": None,
        "loss_points": [],
        "reference_answer": None,
        "next_recommended_actions": ["retry_same_question", "continue_same_question"],
        "trace_refs": [],
        "low_confidence_flags": [],
        "feedback_metadata": feedback_metadata,
    }


def _existing_generated_feedback_task(feedback: PolishFeedback) -> PolishTaskStatus:
    payload = _feedback_payload_from_summary(feedback.feedback_summary)
    return PolishTaskStatus(
        ai_task_id=feedback.ai_task_id,
        task_type=POLISH_FEEDBACK_TASK_TYPE,
        status=AiTaskStatus.SUCCEEDED,
        contract_ids=POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
        retryable=False,
        result_ref=TraceRef(
            trace_ref_id=feedback.feedback_id,
            trace_type="feedback",
            created_at=feedback.created_at,
        ),
        user_visible_status="反馈已存在",
        candidate_refs=_feedback_candidate_refs_from_payload(payload),
    )


def _existing_feedback_task(feedback: PolishFeedback) -> PolishTaskStatus:
    payload = _feedback_payload_from_summary(feedback.feedback_summary)
    if str(feedback.status) == str(AiTaskStatus.GENERATION_FAILED) or (
        isinstance(payload, dict) and payload.get("status") == str(AiTaskStatus.GENERATION_FAILED)
    ):
        validation_errors = ()
        if isinstance(payload, dict) and isinstance(payload.get("validation_errors"), list):
            validation_errors = tuple(str(item) for item in payload["validation_errors"] if str(item))
        user_visible_status = "反馈生成失败，可重试"
        if isinstance(payload, dict):
            raw_status = payload.get("user_visible_status")
            if isinstance(raw_status, str) and raw_status.strip():
                user_visible_status = raw_status.strip()
        return PolishTaskStatus(
            ai_task_id=feedback.ai_task_id,
            task_type=POLISH_FEEDBACK_TASK_TYPE,
            status=AiTaskStatus.GENERATION_FAILED,
            contract_ids=POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
            retryable=True,
            result_ref=TraceRef(
                trace_ref_id=feedback.ai_task_id,
                trace_type="validation_result",
                created_at=feedback.created_at,
            ),
            user_visible_status=user_visible_status,
            validation_errors=validation_errors,
        )
    return _existing_generated_feedback_task(feedback)


def _has_generated_feedback_payload(feedback: PolishFeedback) -> bool:
    payload = _feedback_payload_from_summary(feedback.feedback_summary)
    return isinstance(payload, dict) and payload.get("status") == "generated"


def _feedback_candidate_refs_from_payload(payload: object) -> tuple[ResourceRef, ...]:
    if not isinstance(payload, dict):
        return ()
    result: list[ResourceRef] = []
    metadata = payload.get("feedback_metadata")
    if isinstance(metadata, dict):
        feedback_candidate_ref = str(metadata.get("candidate_ref") or "").strip()
        if feedback_candidate_ref:
            result.append(ResourceRef(resource_type="feedback_candidate", resource_id=feedback_candidate_ref))
        asset_refs = metadata.get("asset_update_candidate_refs")
        if isinstance(asset_refs, (list, tuple)):
            for ref in asset_refs:
                resource_id = str(ref or "").strip()
                if resource_id:
                    result.append(ResourceRef(resource_type="asset_update_candidate", resource_id=resource_id))

    refs = payload.get("candidate_refs")
    if not isinstance(refs, (list, tuple)):
        return tuple(dict.fromkeys(result))
    for item in refs:
        if not isinstance(item, dict):
            continue
        resource_type = str(item.get("resource_type") or "").strip()
        resource_id = str(item.get("resource_id") or "").strip()
        if resource_type in {"feedback_candidate", "asset_update_candidate"} and resource_id:
            result.append(ResourceRef(resource_type=resource_type, resource_id=resource_id))
    return tuple(dict.fromkeys(result))


def _canonical_project_asset_items(canonical_evidence_pack: dict[str, Any] | None) -> tuple[dict[str, Any], ...]:
    if not isinstance(canonical_evidence_pack, dict):
        return ()
    canonical_project_assets = canonical_evidence_pack.get("canonical_project_assets")
    if not isinstance(canonical_project_assets, dict):
        return ()
    items = canonical_project_assets.get("items")
    if not isinstance(items, list):
        return ()
    result: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        if str(item.get("status") or "") != "asset_confirmed":
            continue
        asset_id = item.get("asset_id")
        if isinstance(asset_id, str):
            item_asset_id = asset_id
        else:
            item_asset_id = item.get("asset_ref")
            if not isinstance(item_asset_id, str):
                item_asset_id = f"canonical_asset_{index}"
        result.append(
            {
                "asset_id": item_asset_id,
                "status": str(item.get("status") or ""),
                "asset_type": str(item.get("asset_type") or ""),
                "title": str(item.get("title") or ""),
                "summary": str(item.get("summary") or item.get("content_excerpt") or ""),
                "content_excerpt": str(item.get("content_excerpt") or ""),
                "source_refs": list(_safe_string_items(item.get("source_refs"))),
                "evidence_refs": list(_safe_string_items(item.get("evidence_refs"))),
                "current_version_id": str(item.get("current_version_id") or ""),
                "priority": item.get("priority") if isinstance(item.get("priority"), int) else None,
                "relevance_reason": str(item.get("relevance_reason") or ""),
            }
        )
    return tuple(result)


def _safe_string_items(items: object) -> tuple[str, ...]:
    if not isinstance(items, (list, tuple)):
        return ()
    return tuple(
        str(item)
        for item in items
        if isinstance(item, str) and item.strip()
    )


def _feedback_question_sources(sources: tuple[PolishQuestionSource, ...]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "index": source.index,
            "source_type": source.source_type,
            "title": source.title,
            "excerpt": source.excerpt,
            "ref_id": source.ref_id,
            "availability": source.availability,
        }
        for source in sources
    )


def _feedback_same_question_answers(
    *,
    turn: PolishSessionTurn,
    current_answer_id: str,
) -> tuple[dict[str, Any], ...]:
    answers: list[dict[str, Any]] = []
    for answer in turn.answers[-5:]:
        if answer.answer_id == current_answer_id:
            continue
        feedback_payload = answer.feedback_payload if isinstance(answer.feedback_payload, dict) else {}
        loss_point_ids: list[str] = []
        compact_loss_points: list[dict[str, Any]] = []
        loss_points = feedback_payload.get("loss_points") if isinstance(feedback_payload, dict) else None
        if isinstance(loss_points, list):
            for loss_point in loss_points:
                if not isinstance(loss_point, dict):
                    continue
                loss_point_id = str(loss_point.get("loss_point_id") or "")
                if loss_point_id:
                    loss_point_ids.append(loss_point_id)
                    compact_loss_points.append(
                        {
                            "loss_point_id": loss_point_id,
                            "reason": _feedback_context_excerpt(loss_point.get("reason"), max_chars=240),
                        }
                    )
        answer_coverage = feedback_payload.get("answer_coverage") if isinstance(feedback_payload, dict) else None
        if not isinstance(answer_coverage, dict):
            answer_coverage = {}
        score_result = feedback_payload.get("score_result") if isinstance(feedback_payload, dict) else None
        if not isinstance(score_result, dict):
            score_result = {}
        answers.append(
            {
                "answer_id": answer.answer_id,
                "answer_round": answer.answer_round,
                "answer_summary": _feedback_context_excerpt(answer.answer_text, max_chars=700),
                "feedback_summary": _feedback_context_excerpt(answer.feedback_text, max_chars=700),
                "loss_point_ids": loss_point_ids,
                "loss_points": compact_loss_points,
                "covered_points": _clean_feedback_list(answer_coverage.get("covered_points")),
                "missing_points": _clean_feedback_list(answer_coverage.get("missing_points")),
                "answer_coverage": {
                    "covered_points": _clean_feedback_list(answer_coverage.get("covered_points")),
                    "missing_points": _clean_feedback_list(answer_coverage.get("missing_points")),
                },
                "score_result": {"score_value": score_result.get("score_value")}
                if score_result.get("score_value") is not None
                else {},
            }
        )
    return tuple(answers)


def _feedback_recent_turns(turns: tuple[PolishSessionTurn, ...]) -> tuple[dict[str, Any], ...]:
    recent_turns: list[dict[str, Any]] = []
    for turn in turns[-3:]:
        latest_answer = turn.answers[-1] if turn.answers else None
        recent_turns.append(
            {
                "question_id": turn.question_id,
                "question_summary": _feedback_context_excerpt(turn.question_text, max_chars=500),
                "progress_node_ref": turn.progress_node_ref,
                "answer_id": latest_answer.answer_id if latest_answer is not None else None,
                "answer_round": latest_answer.answer_round if latest_answer is not None else None,
                "answer_summary": _feedback_context_excerpt(latest_answer.answer_text, max_chars=700)
                if latest_answer is not None
                else None,
                "feedback_summary": _feedback_context_excerpt(latest_answer.feedback_text, max_chars=700)
                if latest_answer is not None
                else None,
            }
        )
    return tuple(recent_turns)


def _feedback_job_snapshot(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        "job_id": value.get("job_id"),
        "job_version_id": value.get("job_version_id"),
        "title": value.get("title"),
        "company": value.get("company"),
        "responsibilities": _clean_feedback_list(value.get("responsibilities"))[:5],
        "requirements": _clean_feedback_list(value.get("requirements"))[:5],
        "content_digest": value.get("content_digest"),
    }


def _feedback_resume_snapshot(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        "resume_id": value.get("resume_id"),
        "resume_version_id": value.get("resume_version_id"),
        "title": value.get("title"),
        "summary": value.get("summary"),
        "projects": _clean_feedback_list(value.get("project_experiences"))[:5],
        "content_digest": value.get("content_digest"),
    }


def _feedback_context_excerpt(value: Any, *, max_chars: int) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text


def _feedback_progress_node_snapshot(
    progress_tree_plan: dict[str, Any],
    *,
    progress_node_ref: str | None,
    question_text: str,
) -> dict[str, Any]:
    if progress_node_ref:
        for node in _iter_progress_nodes(progress_tree_plan.get("nodes")):
            node_ref = _feedback_progress_node_ref(node)
            if node_ref == progress_node_ref:
                snapshot = dict(node)
                snapshot.setdefault("node_ref", progress_node_ref)
                snapshot.setdefault("question_title", question_text)
                return snapshot
    return {
        "node_ref": progress_node_ref or "",
        "question_title": question_text,
        "title": question_text,
    }


def _iter_progress_nodes(value: Any):
    if isinstance(value, dict):
        yield value
        for child_key in ("children", "items", "nodes", "deferred_candidates"):
            yield from _iter_progress_nodes(value.get(child_key))
    elif isinstance(value, list) or isinstance(value, tuple):
        for item in value:
            yield from _iter_progress_nodes(item)


def _feedback_progress_node_ref(node: dict[str, Any]) -> str | None:
    for key in ("progress_node_ref", "node_ref", "ref", "id"):
        value = node.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _clean_feedback_list(value: Any) -> list[Any]:
    if not isinstance(value, list) and not isinstance(value, tuple):
        return []
    return [item for item in value if item not in (None, "")]


def _feedback_payload_from_summary(value: str | None) -> dict[str, Any] | None:
    if value is None:
        return None
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None
