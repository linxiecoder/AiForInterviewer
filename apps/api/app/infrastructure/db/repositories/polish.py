"""SQLAlchemy repository for polish core workflows."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import timezone
from hashlib import sha256
from typing import Any

from sqlalchemy import func, select, text, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.application.ai_runtime.contracts import RuntimeConflictError
from app.application.polish.ports import (
    PolishAnswer,
    PolishFeedback,
    PolishQuestion,
    PolishQuestionSource,
    PolishRepository,
    PolishSession,
    PolishSessionReportSummary,
    PolishSessionVersionConflictError,
    PolishTaskStatus,
)
from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
    POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
    POLISH_FEEDBACK_TASK_TYPE,
)
from app.application.polish.question_metadata import (
    empty_question_metadata,
    normalize_question_metadata,
    question_metadata_to_dict,
)
from app.application.polish.theme_strategy import PolishThemeStrategy, resolve_polish_theme_strategy
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import AiTaskStatus
from app.domain.shared.refs import ResourceRef, TraceRef
from app.infrastructure.db.models.ai_task import AiTask, AiTaskResult
from app.infrastructure.db.models.answer import Answer as AnswerModel
from app.infrastructure.db.models.feedback import Feedback as FeedbackModel
from app.infrastructure.db.models.interview import (
    InterviewSession as InterviewSessionModel,
    PolishSessionDetail as PolishSessionDetailModel,
)
from app.infrastructure.db.models.question import Question as QuestionModel
from app.infrastructure.db.models.report import InterviewReport as InterviewReportModel
from app.infrastructure.db.session import get_session_factory


_ANSWER_ROUND_RETRY_LIMIT = 3
_QUESTION_GENERATION_TASK_TYPES = {
    "polish_question_generation",
    "polish_question_follow_up_generation",
}
_TASK_RESULT_TERMINAL_FAILURE_STATUSES = {
    AiTaskStatus.VALIDATION_FAILED.value,
    AiTaskStatus.SOURCE_UNAVAILABLE.value,
    AiTaskStatus.GENERATION_FAILED.value,
    AiTaskStatus.TIMED_OUT.value,
    AiTaskStatus.CANCELLED.value,
}
_FEEDBACK_LIFECYCLE_TERMINAL_STATUSES = {
    AiTaskStatus.CANCELLED.value,
    AiTaskStatus.TIMED_OUT.value,
}
_FEEDBACK_LIFECYCLE_RETRYABLE_STATUSES = {AiTaskStatus.TIMED_OUT.value}


class SqlAlchemyPolishRepository(PolishRepository):
    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()

    def add_session(self, session: PolishSession) -> None:
        with self._session_factory() as db:
            db.add(_session_to_model(session))
            db.add(_detail_to_model(session))
            db.commit()

    def update_progress_tree(self, session: PolishSession) -> None:
        with self._session_factory() as db:
            session_model = db.get(InterviewSessionModel, session.session_id)
            if session_model is None or session_model.owner_id != session.owner_id:
                return
            result = db.execute(
                update(PolishSessionDetailModel)
                .where(
                    PolishSessionDetailModel.owner_id == session.owner_id,
                    PolishSessionDetailModel.session_id == session.session_id,
                    PolishSessionDetailModel.record_version == session.record_version,
                )
                .values(
                    progress_tree_status=session.progress_tree_status,
                    progress_percent=session.progress_percent,
                    progress_tree_plan_json=_payload_with_theme_metadata(session.progress_tree_plan, session.polish_theme),
                    progress_tree_state_json=_payload_with_theme_metadata(session.progress_tree_state, session.polish_theme),
                    status=session.status,
                    updated_at=session.updated_at,
                    record_version=PolishSessionDetailModel.record_version + 1,
                )
            )
            if result.rowcount == 0:
                _raise_session_version_conflict_if_present(
                    db,
                    owner_id=session.owner_id,
                    session_id=session.session_id,
                    base_record_version=session.record_version,
                )
                return
            session_model.status = session.status
            session_model.updated_at = session.updated_at
            session_model.record_version = session_model.record_version + 1
            db.commit()

    def save_session_status(self, session: PolishSession) -> None:
        with self._session_factory() as db:
            session_model = db.get(InterviewSessionModel, session.session_id)
            if session_model is None or session_model.owner_id != session.owner_id:
                return
            result = db.execute(
                update(PolishSessionDetailModel)
                .where(
                    PolishSessionDetailModel.owner_id == session.owner_id,
                    PolishSessionDetailModel.session_id == session.session_id,
                    PolishSessionDetailModel.record_version == session.record_version,
                )
                .values(
                    status=session.status,
                    updated_at=session.updated_at,
                    record_version=PolishSessionDetailModel.record_version + 1,
                )
            )
            if result.rowcount == 0:
                _raise_session_version_conflict_if_present(
                    db,
                    owner_id=session.owner_id,
                    session_id=session.session_id,
                    base_record_version=session.record_version,
                )
                return
            session_model.status = session.status
            session_model.updated_at = session.updated_at
            session_model.record_version = session_model.record_version + 1
            db.commit()

    def create_session_report(
        self,
        *,
        owner_id: str,
        actor_id: str,
        session_id: str,
        report_id: str,
    ) -> PolishSession:
        with self._session_factory() as db:
            session_model = db.get(InterviewSessionModel, session_id)
            if session_model is None or session_model.owner_id != owner_id or session_model.mode != "polish":
                raise ValueError("Polish session not found")
            detail_model = _get_session_detail_model(db, owner_id=owner_id, session_id=session_id)
            if detail_model is None:
                raise ValueError("Polish session detail not found")
            existing_report = _latest_report_model(db, owner_id=owner_id, session_id=session_id)
            now = utc_now()
            if existing_report is None:
                existing_report = InterviewReportModel(
                    id=report_id,
                    owner_id=owner_id,
                    actor_id=actor_id,
                    record_version=1,
                    status="available",
                    trace_ref_ids=None,
                    evidence_ref_ids=None,
                    created_at=now,
                    updated_at=now,
                    session_id=session_id,
                    ai_task_id=None,
                    score_result_id=None,
                    report_type="polish_summary",
                    generated_at=now,
                )
                db.add(existing_report)
            else:
                existing_report.updated_at = now
            session_model.updated_at = now
            detail_model.updated_at = now
            db.commit()
            return _session_to_entity(session_model, detail_model, existing_report)

    def list_sessions(self, owner_id: str) -> tuple[PolishSession, ...]:
        with self._session_factory() as db:
            rows = db.execute(
                select(InterviewSessionModel, PolishSessionDetailModel)
                .join(
                    PolishSessionDetailModel,
                    PolishSessionDetailModel.session_id == InterviewSessionModel.id,
                )
                .where(
                    InterviewSessionModel.owner_id == owner_id,
                    InterviewSessionModel.mode == "polish",
                    InterviewSessionModel.status != "deleted",
                    PolishSessionDetailModel.owner_id == owner_id,
                )
                .order_by(InterviewSessionModel.updated_at.desc(), InterviewSessionModel.created_at.desc())
            ).all()
            return tuple(
                _session_to_entity(
                    session,
                    detail,
                    _latest_report_model(db, owner_id=owner_id, session_id=session.id),
                )
                for session, detail in rows
            )

    def get_session(self, owner_id: str, session_id: str) -> PolishSession | None:
        with self._session_factory() as db:
            session_model = db.get(InterviewSessionModel, session_id)
            if session_model is None or session_model.owner_id != owner_id or session_model.mode != "polish":
                return None
            detail_model = _get_session_detail_model(db, owner_id=owner_id, session_id=session_id)
            if detail_model is None:
                return None
            report_model = _latest_report_model(db, owner_id=owner_id, session_id=session_id)
            return _session_to_entity(session_model, detail_model, report_model)

    def list_questions_for_session(self, owner_id: str, session_id: str) -> tuple[PolishQuestion, ...]:
        with self._session_factory() as db:
            rows = db.scalars(
                select(QuestionModel)
                .where(
                    QuestionModel.owner_id == owner_id,
                    QuestionModel.session_id == session_id,
                )
                .order_by(QuestionModel.created_at.asc(), QuestionModel.id.asc())
            ).all()
            return tuple(_question_to_entity(model) for model in rows)

    def add_question(self, question: PolishQuestion) -> None:
        with self._session_factory() as db:
            db.add(_question_to_model(question))
            db.commit()

    def add_question_once(
        self,
        *,
        owner_id: str,
        session_id: str,
        graph_persistence_idempotency_key: str,
        question: PolishQuestion,
    ) -> tuple[PolishQuestion, bool]:
        with self._session_factory() as db:
            _acquire_question_final_write_db_lock(
                db,
                owner_id=owner_id,
                session_id=session_id,
                graph_persistence_idempotency_key=graph_persistence_idempotency_key,
            )
            existing = _find_question_model_by_graph_persistence_idempotency_key(
                db,
                owner_id=owner_id,
                session_id=session_id,
                graph_persistence_idempotency_key=graph_persistence_idempotency_key,
            )
            if existing is not None:
                _assert_question_final_write_replay_matches(existing, question)
                return _question_to_entity(existing), False

            db.add(_question_to_model(question))
            db.commit()
            return question, True

    def get_question(self, owner_id: str, question_id: str) -> PolishQuestion | None:
        with self._session_factory() as db:
            found = db.get(QuestionModel, question_id)
            if found is None or found.owner_id != owner_id:
                return None
            return _question_to_entity(found)

    def add_answer(self, answer: PolishAnswer) -> None:
        with self._session_factory() as db:
            db.add(_answer_to_model(answer))
            db.commit()

    def add_answer_once(
        self,
        *,
        answer: PolishAnswer,
        idempotency_key: str | None,
        request_body_hash: str | None,
    ) -> PolishAnswer:
        last_error: IntegrityError | None = None
        for _ in range(_ANSWER_ROUND_RETRY_LIMIT):
            with self._session_factory() as db:
                if idempotency_key is not None:
                    existing = _find_answer_model_by_idempotency_key(
                        db,
                        owner_id=answer.owner_id,
                        actor_id=answer.actor_id,
                        session_id=answer.session_id,
                        question_id=answer.question_id,
                        idempotency_key=idempotency_key,
                    )
                    if existing is not None:
                        return _answer_to_entity(existing)

                answer_to_save = replace(
                    answer,
                    answer_round=_next_answer_round(
                        db,
                        owner_id=answer.owner_id,
                        question_id=answer.question_id,
                    ),
                    idempotency_key=idempotency_key,
                    request_body_hash=request_body_hash,
                )
                model = _answer_to_model(answer_to_save)
                db.add(model)
                try:
                    db.commit()
                except IntegrityError as exc:
                    db.rollback()
                    last_error = exc
                    if idempotency_key is not None:
                        existing = _find_answer_model_by_idempotency_key(
                            db,
                            owner_id=answer.owner_id,
                            actor_id=answer.actor_id,
                            session_id=answer.session_id,
                            question_id=answer.question_id,
                            idempotency_key=idempotency_key,
                        )
                        if existing is not None:
                            return _answer_to_entity(existing)
                    continue
                return _answer_to_entity(model)

        if last_error is not None:
            raise last_error
        raise RuntimeError("answer round allocation failed")

    def get_answer(self, owner_id: str, answer_id: str) -> PolishAnswer | None:
        with self._session_factory() as db:
            found = db.get(AnswerModel, answer_id)
            if found is None or found.owner_id != owner_id:
                return None
            return _answer_to_entity(found)

    def list_answers_for_session(self, owner_id: str, session_id: str) -> tuple[PolishAnswer, ...]:
        with self._session_factory() as db:
            rows = db.scalars(
                select(AnswerModel)
                .where(
                    AnswerModel.owner_id == owner_id,
                    AnswerModel.session_id == session_id,
                )
                .order_by(
                    AnswerModel.question_id.asc(),
                    AnswerModel.answer_round.asc(),
                    AnswerModel.created_at.asc(),
                    AnswerModel.id.asc(),
                )
            ).all()
            return tuple(_answer_to_entity(model) for model in rows)

    def count_answers_for_question(self, owner_id: str, question_id: str) -> int:
        with self._session_factory() as db:
            return int(
                db.scalar(
                    select(func.count())
                    .select_from(AnswerModel)
                    .where(
                        AnswerModel.owner_id == owner_id,
                        AnswerModel.question_id == question_id,
                    )
                )
                or 0
            )

    def add_feedback(self, feedback: PolishFeedback) -> None:
        with self._session_factory() as db:
            db.add(_feedback_to_model(feedback))
            db.commit()

    def get_latest_feedback_for_answer(
        self,
        *,
        owner_id: str,
        answer_id: str,
        status: str | None = None,
    ) -> PolishFeedback | None:
        with self._session_factory() as db:
            conditions = [
                FeedbackModel.owner_id == owner_id,
                FeedbackModel.answer_id == answer_id,
            ]
            if status is not None:
                conditions.append(FeedbackModel.status == status)
            model = db.scalars(
                select(FeedbackModel)
                .where(*conditions)
                .order_by(
                    FeedbackModel.created_at.desc(),
                    FeedbackModel.id.desc(),
                )
                .limit(1)
            ).first()
            return _feedback_to_entity(model) if model is not None else None

    def list_feedbacks_for_session(self, owner_id: str, session_id: str) -> tuple[PolishFeedback, ...]:
        with self._session_factory() as db:
            rows = db.scalars(
                select(FeedbackModel)
                .where(
                    FeedbackModel.owner_id == owner_id,
                    FeedbackModel.session_id == session_id,
                )
                .order_by(
                    FeedbackModel.answer_id.asc(),
                    FeedbackModel.created_at.asc(),
                    FeedbackModel.id.asc(),
                )
            ).all()
            return tuple(_feedback_to_entity(model) for model in rows)

    def add_task(self, task: PolishTaskStatus, *, owner_id: str, actor_id: str, target_ref_id: str) -> None:
        with self._session_factory() as db:
            db.add(
                _task_to_model(
                    task,
                    owner_id=owner_id,
                    actor_id=actor_id,
                    target_ref_id=target_ref_id,
                    idempotency_record_id=None,
                )
            )
            if _should_persist_task_safe_summary(task):
                db.add(_task_result_to_model(task, owner_id=owner_id, actor_id=actor_id))
            db.commit()

    def add_feedback_running_task(
        self,
        task: PolishTaskStatus,
        *,
        owner_id: str,
        actor_id: str,
        target_ref_id: str,
        idempotency_record_id: str | None = None,
    ) -> tuple[PolishTaskStatus, bool]:
        with self._session_factory() as db:
            _acquire_feedback_running_task_db_lock(db, task_id=task.ai_task_id)
            existing = db.get(AiTask, task.ai_task_id)
            if existing is not None:
                return _task_status_from_model(existing), False
            db.add(
                _task_to_model(
                    task,
                    owner_id=owner_id,
                    actor_id=actor_id,
                    target_ref_id=target_ref_id,
                    idempotency_record_id=idempotency_record_id,
                )
            )
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                existing_after_conflict = db.get(AiTask, task.ai_task_id)
                if existing_after_conflict is not None:
                    return _task_status_from_model(existing_after_conflict), False
                raise
            return task, True

    def add_feedback_task_result(
        self,
        feedback: PolishFeedback,
        task: PolishTaskStatus,
        *,
        owner_id: str,
        actor_id: str,
        target_ref_id: str,
        idempotency_record_id: str | None = None,
    ) -> None:
        with self._session_factory() as db:
            existing_task = db.get(AiTask, task.ai_task_id)
            lifecycle_terminal_status = (
                _feedback_lifecycle_terminal_status_from_task(existing_task)
                if existing_task is not None
                else None
            )
            if existing_task is not None and lifecycle_terminal_status is not None:
                _apply_lifecycle_terminal_to_task_model(
                    existing_task,
                    terminal_status=lifecycle_terminal_status,
                )
                db.merge(
                    _task_result_from_lifecycle_terminal_task(
                        existing_task,
                        terminal_status=lifecycle_terminal_status,
                    )
                )
                db.commit()
                return
            should_add_feedback = True
            if idempotency_record_id is None:
                should_add_feedback = True
            else:
                existing_feedback = db.scalar(
                    select(FeedbackModel)
                    .where(FeedbackModel.owner_id == owner_id, FeedbackModel.ai_task_id == task.ai_task_id)
                    .order_by(FeedbackModel.created_at.asc(), FeedbackModel.id.asc())
                    .limit(1)
                )
                existing_result = db.get(AiTaskResult, f"{task.ai_task_id}_result")
                if existing_feedback is not None and existing_result is not None:
                    return
                should_add_feedback = existing_feedback is None
            if existing_task is None:
                db.add(
                    _task_to_model(
                        task,
                        owner_id=owner_id,
                        actor_id=actor_id,
                        target_ref_id=target_ref_id,
                        idempotency_record_id=idempotency_record_id,
                    )
                )
            else:
                _apply_task_to_model(
                    existing_task,
                    task,
                    owner_id=owner_id,
                    actor_id=actor_id,
                    target_ref_id=target_ref_id,
                    idempotency_record_id=idempotency_record_id,
                )
            if idempotency_record_id is None:
                db.add(_task_result_to_model(task, owner_id=owner_id, actor_id=actor_id))
            else:
                db.merge(_task_result_to_model(task, owner_id=owner_id, actor_id=actor_id))
            try:
                if should_add_feedback:
                    db.add(_feedback_to_model(feedback))
                db.flush()
                db.commit()
            except SQLAlchemyError:
                db.rollback()
                raise

    def get_feedback_task_idempotency_record(
        self,
        *,
        owner_id: str,
        idempotency_key: str,
        request_body_hash: str,
    ) -> dict[str, object]:
        prefix = _feedback_idempotency_record_prefix(idempotency_key)
        expected_record_id = _feedback_idempotency_record_id(idempotency_key, request_body_hash)
        with self._session_factory() as db:
            tasks = db.scalars(
                select(AiTask)
                .where(
                    AiTask.owner_id == owner_id,
                    AiTask.task_type == POLISH_FEEDBACK_TASK_TYPE,
                    AiTask.idempotency_record_id.like(f"{prefix}%"),
                )
                .order_by(AiTask.created_at.asc(), AiTask.id.asc())
            ).all()
            if not tasks:
                return {"status": "missing"}
            task = next((item for item in tasks if item.idempotency_record_id == expected_record_id), None)
            if task is None:
                return {"status": "conflict"}
            result = db.scalar(
                select(AiTaskResult)
                .where(AiTaskResult.owner_id == owner_id, AiTaskResult.ai_task_id == task.id)
                .limit(1)
            )
            feedback = db.scalar(
                select(FeedbackModel)
                .where(FeedbackModel.owner_id == owner_id, FeedbackModel.ai_task_id == task.id)
                .order_by(FeedbackModel.created_at.desc(), FeedbackModel.id.desc())
                .limit(1)
            )
            if result is None and feedback is not None:
                result = _repair_missing_terminal_feedback_task_result(db, task, feedback)
            lifecycle_terminal_status = _feedback_lifecycle_terminal_status_from_task(task)
            if lifecycle_terminal_status is not None:
                feedback = _materialize_lifecycle_terminal_feedback(
                    db,
                    task,
                    result,
                    feedback,
                    terminal_status=lifecycle_terminal_status,
                )
                result = db.get(AiTaskResult, f"{task.id}_result")
            if result is None or feedback is None:
                if task.status in {str(AiTaskStatus.QUEUED), str(AiTaskStatus.RUNNING)}:
                    return {"status": "running", "task": _task_status_from_model(task)}
                if task.status in _FEEDBACK_LIFECYCLE_TERMINAL_STATUSES and result is not None:
                    return {"status": "terminal", "task": _task_status_from_model(task)}
                return {"status": "orphan", "ai_task_id": task.id}
            return {"status": "replay", "feedback": _feedback_to_entity(feedback)}

    def get_ref(self, session_id: str) -> ResourceRef | None:
        with self._session_factory() as db:
            found = db.get(InterviewSessionModel, session_id)
            if found is None or found.mode != "polish":
                return None
            return ResourceRef(resource_type="polish_session", resource_id=session_id)


def _payload_with_theme_metadata(payload: dict | None, theme: str | None) -> dict | None:
    if payload is None:
        return None
    result = dict(payload)
    strategy = _resolve_strategy_or_none(theme) or resolve_polish_theme_strategy(None)
    result["polish_theme"] = strategy.theme
    result["polish_theme_label"] = strategy.label
    result["explicit_weight"] = strategy.explicit_weight
    result["implicit_weight"] = strategy.implicit_weight
    return result


def _acquire_question_final_write_db_lock(
    db: Session,
    *,
    owner_id: str,
    session_id: str,
    graph_persistence_idempotency_key: str,
) -> None:
    lock_key = f"{owner_id}:{session_id}:{graph_persistence_idempotency_key}"
    dialect_name = db.get_bind().dialect.name
    if dialect_name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": _signed_lock_id(lock_key)})
        return
    if dialect_name == "sqlite":
        db.execute(text("BEGIN IMMEDIATE"))
        return
    db.execute(
        select(InterviewSessionModel.session_id)
        .where(
            InterviewSessionModel.owner_id == owner_id,
            InterviewSessionModel.session_id == session_id,
        )
        .with_for_update()
    ).first()


def _acquire_feedback_running_task_db_lock(db: Session, *, task_id: str) -> None:
    lock_key = f"polish_feedback_task:{task_id}"
    dialect_name = db.get_bind().dialect.name
    if dialect_name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": _signed_lock_id(lock_key)})
        return
    if dialect_name == "sqlite":
        db.execute(text("BEGIN IMMEDIATE"))


def _signed_lock_id(lock_key: str) -> int:
    raw = int.from_bytes(sha256(lock_key.encode("utf-8")).digest()[:8], "big", signed=False)
    return raw if raw < 2**63 else raw - 2**64


def _assert_question_final_write_replay_matches(existing: QuestionModel, incoming: PolishQuestion) -> None:
    existing_metadata = (
        existing.question_metadata_json if isinstance(existing.question_metadata_json, dict) else {}
    )
    incoming_metadata = incoming.question_metadata if isinstance(incoming.question_metadata, dict) else {}
    existing_digest = str(existing_metadata.get("final_question_digest") or "").strip()
    incoming_digest = str(incoming_metadata.get("final_question_digest") or "").strip()
    if existing_digest and incoming_digest:
        if existing_digest != incoming_digest:
            raise RuntimeConflictError("question final-write intent conflict")
        return
    if _question_model_final_write_signature(existing) != _question_entity_final_write_signature(incoming):
        raise RuntimeConflictError("question final-write intent conflict")


def _question_model_final_write_signature(question: QuestionModel) -> tuple[object, ...]:
    return (
        _clean_final_write_text(question.question_text),
        _clean_final_write_text(question.progress_node_ref),
        _clean_final_write_text(question.context_digest),
        _clean_final_write_refs(question.evidence_ref_ids),
    )


def _question_entity_final_write_signature(question: PolishQuestion) -> tuple[object, ...]:
    return (
        _clean_final_write_text(question.question_text),
        _clean_final_write_text(question.progress_node_ref),
        _clean_final_write_text(question.context_digest),
        _clean_final_write_refs(question.evidence_refs),
    )


def _clean_final_write_text(value: object) -> str:
    return str(value or "").strip()


def _clean_final_write_refs(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple, set)):
        return ()
    return tuple(dict.fromkeys(str(item).strip() for item in value if str(item).strip()))


def _find_question_model_by_graph_persistence_idempotency_key(
    db: Session,
    *,
    owner_id: str,
    session_id: str,
    graph_persistence_idempotency_key: str,
) -> QuestionModel | None:
    rows = db.scalars(
        select(QuestionModel)
        .where(
            QuestionModel.owner_id == owner_id,
            QuestionModel.session_id == session_id,
        )
        .order_by(QuestionModel.created_at.asc(), QuestionModel.id.asc())
    ).all()
    for row in rows:
        metadata = row.question_metadata_json if isinstance(row.question_metadata_json, dict) else {}
        if metadata.get("graph_persistence_idempotency_key") == graph_persistence_idempotency_key:
            return row
    return None


def _find_answer_model_by_idempotency_key(
    db: Session,
    *,
    owner_id: str,
    actor_id: str,
    session_id: str,
    question_id: str,
    idempotency_key: str,
) -> AnswerModel | None:
    return db.scalar(
        select(AnswerModel).where(
            AnswerModel.owner_id == owner_id,
            AnswerModel.actor_id == actor_id,
            AnswerModel.session_id == session_id,
            AnswerModel.question_id == question_id,
            AnswerModel.idempotency_key == idempotency_key,
        )
    )


def _next_answer_round(db: Session, *, owner_id: str, question_id: str) -> int:
    current_max = db.scalar(
        select(func.max(AnswerModel.answer_round)).where(
            AnswerModel.owner_id == owner_id,
            AnswerModel.question_id == question_id,
        )
    )
    return int(current_max or 0) + 1


def _theme_from_detail(detail_model: PolishSessionDetailModel) -> str | None:
    for payload in (detail_model.progress_tree_plan_json, detail_model.progress_tree_state_json):
        if not isinstance(payload, dict):
            continue
        raw_theme = payload.get("polish_theme")
        if isinstance(raw_theme, str):
            strategy = _resolve_strategy_or_none(raw_theme)
            if strategy is not None:
                return strategy.theme
    return None


def _resolve_strategy_or_none(theme: str | None) -> PolishThemeStrategy | None:
    if theme is None:
        return None
    try:
        return resolve_polish_theme_strategy(theme)
    except ValueError:
        return None


def _get_session_detail_model(
    db: Session,
    *,
    owner_id: str,
    session_id: str,
) -> PolishSessionDetailModel | None:
    return db.scalar(
        select(PolishSessionDetailModel).where(
            PolishSessionDetailModel.owner_id == owner_id,
            PolishSessionDetailModel.session_id == session_id,
        )
    )


def _raise_session_version_conflict_if_present(
    db: Session,
    *,
    owner_id: str,
    session_id: str,
    base_record_version: int,
) -> None:
    current_record_version = db.scalar(
        select(PolishSessionDetailModel.record_version).where(
            PolishSessionDetailModel.owner_id == owner_id,
            PolishSessionDetailModel.session_id == session_id,
        )
    )
    if current_record_version is None:
        return
    raise PolishSessionVersionConflictError(
        base_record_version=base_record_version,
        current_record_version=current_record_version,
    )


def _latest_report_model(
    db: Session,
    *,
    owner_id: str,
    session_id: str,
) -> InterviewReportModel | None:
    return db.scalars(
        select(InterviewReportModel)
        .where(
            InterviewReportModel.owner_id == owner_id,
            InterviewReportModel.session_id == session_id,
        )
        .order_by(InterviewReportModel.generated_at.desc(), InterviewReportModel.created_at.desc())
    ).first()


def _session_to_model(session: PolishSession) -> InterviewSessionModel:
    return InterviewSessionModel(
        id=session.session_id,
        owner_id=session.owner_id,
        actor_id=session.actor_id,
        record_version=1,
        status=session.status,
        trace_ref_ids=None,
        evidence_ref_ids=None,
        created_at=session.created_at,
        updated_at=session.updated_at,
        binding_id=session.binding_id,
        resume_id=session.resume_id,
        resume_version_id=session.resume_version_id,
        job_id=session.job_id,
        job_version_id=session.job_version_id,
        mode="polish",
    )


def _detail_to_model(session: PolishSession) -> PolishSessionDetailModel:
    return PolishSessionDetailModel(
        id=f"{session.session_id}_detail",
        owner_id=session.owner_id,
        actor_id=session.actor_id,
        record_version=1,
        status=session.status,
        trace_ref_ids=None,
        evidence_ref_ids=None,
        created_at=session.created_at,
        updated_at=session.updated_at,
        session_id=session.session_id,
        topic_ref_id=session.topic_id,
        subtopic_ref_id=session.subtopic_id,
        custom_topic_text_summary=session.custom_topic_text_summary,
        progress_tree_status=session.progress_tree_status,
        progress_percent=session.progress_percent,
        progress_tree_plan_json=_payload_with_theme_metadata(session.progress_tree_plan, session.polish_theme),
        progress_tree_state_json=_payload_with_theme_metadata(session.progress_tree_state, session.polish_theme),
    )


def _session_to_entity(
    session_model: InterviewSessionModel,
    detail_model: PolishSessionDetailModel,
    report_model: InterviewReportModel | None = None,
) -> PolishSession:
    return PolishSession(
        session_id=session_model.id,
        owner_id=session_model.owner_id,
        actor_id=session_model.actor_id or session_model.owner_id,
        binding_id=session_model.binding_id or "",
        resume_id=session_model.resume_id or "",
        resume_version_id=session_model.resume_version_id or "",
        job_id=session_model.job_id or "",
        job_version_id=session_model.job_version_id or "",
        status=session_model.status,
        topic_id=detail_model.topic_ref_id,
        subtopic_id=detail_model.subtopic_ref_id,
        custom_topic_text_summary=detail_model.custom_topic_text_summary,
        created_at=session_model.created_at,
        updated_at=session_model.updated_at,
        record_version=detail_model.record_version,
        polish_theme=_theme_from_detail(detail_model),
        progress_tree_status=detail_model.progress_tree_status or "insufficient_context",
        progress_percent=detail_model.progress_percent or 0,
        progress_tree_plan=detail_model.progress_tree_plan_json or {},
        progress_tree_state=detail_model.progress_tree_state_json or {},
        report_summary=_report_summary_to_entity(report_model),
    )


def _report_summary_to_entity(report_model: InterviewReportModel | None) -> PolishSessionReportSummary | None:
    if report_model is None:
        return None
    return PolishSessionReportSummary(
        report_id=report_model.id,
        report_status=report_model.status,
        report_generated_at=report_model.generated_at,
    )


def _question_to_model(question: PolishQuestion) -> QuestionModel:
    return QuestionModel(
        id=question.question_id,
        owner_id=question.owner_id,
        actor_id=question.actor_id,
        record_version=1,
        status=question.status,
        trace_ref_ids=None,
        evidence_ref_ids=list(question.evidence_refs) or None,
        created_at=question.created_at,
        updated_at=question.updated_at,
        session_id=question.session_id,
        ai_task_id=question.ai_task_id,
        question_text=question.question_text,
        question_sources_json=_question_sources_to_json(question.question_sources),
        question_metadata_json=_question_metadata_to_json(question.question_metadata),
        progress_node_ref=question.progress_node_ref,
        context_digest=question.context_digest,
    )


def _question_to_entity(model: QuestionModel) -> PolishQuestion:
    return PolishQuestion(
        question_id=model.id,
        owner_id=model.owner_id,
        actor_id=model.actor_id or model.owner_id,
        session_id=model.session_id,
        ai_task_id=model.ai_task_id or "",
        question_text=model.question_text or "",
        question_sources=_question_sources_to_entities(model.question_sources_json),
        question_metadata=_question_metadata_to_entity(getattr(model, "question_metadata_json", None)),
        progress_node_ref=model.progress_node_ref,
        evidence_refs=_question_evidence_refs_to_entities(model.evidence_ref_ids),
        context_digest=model.context_digest,
        status=model.status,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _question_evidence_refs_to_entities(raw_refs: object) -> tuple[str, ...]:
    if not isinstance(raw_refs, list):
        return ()
    return tuple(str(ref) for ref in raw_refs if str(ref))


def _question_metadata_to_json(raw_metadata: object) -> dict[str, Any]:
    try:
        return _with_graph_persistence_metadata(question_metadata_to_dict(raw_metadata), raw_metadata)
    except Exception:
        return empty_question_metadata().to_dict()


def _question_metadata_to_entity(raw_metadata: object) -> dict[str, Any]:
    try:
        return _with_graph_persistence_metadata(normalize_question_metadata(raw_metadata), raw_metadata)
    except Exception:
        return empty_question_metadata().to_dict()


def _with_graph_persistence_metadata(metadata: dict[str, Any], raw_metadata: object) -> dict[str, Any]:
    if not isinstance(raw_metadata, dict):
        return metadata
    result = dict(metadata)
    raw_key = raw_metadata.get("graph_persistence_idempotency_key")
    if isinstance(raw_key, str):
        key = raw_key.strip()
        if key:
            result["graph_persistence_idempotency_key"] = key
    raw_sanitized = raw_metadata.get("sanitized")
    if isinstance(raw_sanitized, bool):
        result["sanitized"] = raw_sanitized
    return result


def _question_sources_to_json(sources: tuple[PolishQuestionSource, ...]) -> list[dict]:
    return [
        {
            "index": source.index,
            "source_type": source.source_type,
            "title": source.title,
            "excerpt": source.excerpt,
            "ref_id": source.ref_id,
            "availability": source.availability,
        }
        for source in sources
    ]


def _question_sources_to_entities(raw_sources: object) -> tuple[PolishQuestionSource, ...]:
    if not isinstance(raw_sources, list):
        return ()
    sources: list[PolishQuestionSource] = []
    for raw_source in raw_sources:
        if not isinstance(raw_source, dict):
            continue
        source_type = str(raw_source.get("source_type") or "")
        title = str(raw_source.get("title") or "")
        excerpt = str(raw_source.get("excerpt") or "")
        if not source_type or not title or not excerpt:
            continue
        raw_index = raw_source.get("index")
        index = raw_index if isinstance(raw_index, int) and raw_index >= 1 else len(sources) + 1
        ref_id = raw_source.get("ref_id")
        sources.append(
            PolishQuestionSource(
                index=index,
                source_type=source_type,
                title=title,
                excerpt=excerpt,
                ref_id=str(ref_id) if ref_id is not None else None,
                availability=str(raw_source.get("availability") or "available"),
            )
        )
    return tuple(sources)


def _answer_to_model(answer: PolishAnswer) -> AnswerModel:
    return AnswerModel(
        id=answer.answer_id,
        owner_id=answer.owner_id,
        actor_id=answer.actor_id,
        record_version=1,
        status=answer.status,
        trace_ref_ids=None,
        evidence_ref_ids=None,
        created_at=answer.created_at,
        updated_at=answer.updated_at,
        session_id=answer.session_id,
        question_id=answer.question_id,
        answer_round=answer.answer_round,
        answer_text=answer.answer_text,
        idempotency_key=answer.idempotency_key,
        request_body_hash=answer.request_body_hash,
    )


def _answer_to_entity(model: AnswerModel) -> PolishAnswer:
    return PolishAnswer(
        answer_id=model.id,
        owner_id=model.owner_id,
        actor_id=model.actor_id or model.owner_id,
        session_id=model.session_id,
        question_id=model.question_id,
        answer_round=model.answer_round,
        answer_text=model.answer_text,
        status=model.status,
        created_at=model.created_at,
        updated_at=model.updated_at,
        idempotency_key=getattr(model, "idempotency_key", None),
        request_body_hash=getattr(model, "request_body_hash", None),
    )


def _feedback_to_model(feedback: PolishFeedback) -> FeedbackModel:
    return FeedbackModel(
        id=feedback.feedback_id,
        owner_id=feedback.owner_id,
        actor_id=feedback.actor_id,
        record_version=1,
        status=feedback.status,
        trace_ref_ids=None,
        evidence_ref_ids=None,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at,
        session_id=feedback.session_id,
        answer_id=feedback.answer_id,
        ai_task_id=feedback.ai_task_id,
        score_result_id=feedback.score_result_id,
        feedback_summary=feedback.feedback_summary,
    )


def _task_to_model(
    task: PolishTaskStatus,
    *,
    owner_id: str,
    actor_id: str,
    target_ref_id: str,
    idempotency_record_id: str | None,
) -> AiTask:
    return AiTask(
        id=task.ai_task_id,
        owner_id=owner_id,
        actor_id=actor_id,
        record_version=1,
        status=str(task.status),
        trace_ref_ids=[task.result_ref.trace_ref_id],
        evidence_ref_ids=None,
        task_type=task.task_type,
        contract_ids=list(task.contract_ids),
        idempotency_record_id=idempotency_record_id,
        target_ref_id=target_ref_id,
        created_at=task.result_ref.created_at,
        updated_at=task.result_ref.created_at,
    )


def _apply_task_to_model(
    model: AiTask,
    task: PolishTaskStatus,
    *,
    owner_id: str,
    actor_id: str,
    target_ref_id: str,
    idempotency_record_id: str | None,
) -> None:
    model.owner_id = owner_id
    model.actor_id = actor_id
    model.status = str(task.status)
    model.trace_ref_ids = [task.result_ref.trace_ref_id]
    model.evidence_ref_ids = None
    model.task_type = task.task_type
    model.contract_ids = list(task.contract_ids)
    model.idempotency_record_id = idempotency_record_id
    model.target_ref_id = target_ref_id
    model.updated_at = task.result_ref.created_at


def _task_result_to_model(
    task: PolishTaskStatus,
    *,
    owner_id: str,
    actor_id: str,
) -> AiTaskResult:
    candidate_refs_json = _resource_refs_to_safe_json(task.candidate_refs)
    suggestion_refs_json = _resource_refs_to_safe_json(task.suggestion_refs)
    validation_errors_json = list(task.validation_errors)
    low_confidence_flags_json: list[str] = []
    source_availability = _source_availability_for_task(task)
    safe_summary_json = _task_safe_summary_json(
        task,
        candidate_refs_json=candidate_refs_json,
        suggestion_refs_json=suggestion_refs_json,
        validation_errors_json=validation_errors_json,
        source_availability=source_availability,
        low_confidence_flags_json=low_confidence_flags_json,
    )
    result_ref_id = (
        task.result_ref.trace_ref_id
        if task.result_ref.trace_type != "validation_result"
        else None
    )
    validation_result_ref_id = (
        task.result_ref.trace_ref_id if task.result_ref.trace_type == "validation_result" else None
    )
    return AiTaskResult(
        id=f"{task.ai_task_id}_result",
        owner_id=owner_id,
        actor_id=actor_id,
        record_version=1,
        status=str(task.status),
        trace_ref_ids=[task.result_ref.trace_ref_id],
        evidence_ref_ids=None,
        created_at=task.result_ref.created_at,
        updated_at=task.result_ref.created_at,
        ai_task_id=task.ai_task_id,
        result_sequence="0",
        validation_result_ref_id=validation_result_ref_id,
        trace_ref_id=task.result_ref.trace_ref_id,
        result_ref_id=result_ref_id,
        candidate_refs_json=candidate_refs_json if safe_summary_json is not None else None,
        suggestion_refs_json=suggestion_refs_json if safe_summary_json is not None else None,
        validation_errors_json=validation_errors_json if safe_summary_json is not None else None,
        source_availability=source_availability if safe_summary_json is not None else None,
        low_confidence_flags_json=low_confidence_flags_json if safe_summary_json is not None else None,
        safe_summary_json=safe_summary_json,
    )


def _repair_missing_terminal_feedback_task_result(
    db: Session,
    task: AiTask,
    feedback: FeedbackModel,
) -> AiTaskResult | None:
    terminal_status = _terminal_task_status_from_feedback(feedback)
    if terminal_status is None:
        return None
    _apply_terminal_feedback_to_task_model(task, feedback, terminal_status=terminal_status)
    db.merge(_task_result_from_terminal_feedback(task, feedback, terminal_status=terminal_status))
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return db.get(AiTaskResult, f"{task.id}_result")


def _materialize_lifecycle_terminal_feedback(
    db: Session,
    task: AiTask,
    result: AiTaskResult | None,
    feedback: FeedbackModel | None,
    *,
    terminal_status: AiTaskStatus,
) -> FeedbackModel | None:
    _apply_lifecycle_terminal_to_task_model(task, terminal_status=terminal_status)
    if result is None or result.status != terminal_status.value:
        db.merge(_task_result_from_lifecycle_terminal_task(task, terminal_status=terminal_status))
    if feedback is None:
        feedback = _feedback_from_lifecycle_terminal_task(
            db,
            task,
            terminal_status=terminal_status,
        )
        if feedback is not None:
            db.add(feedback)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return db.get(FeedbackModel, feedback.id) if feedback is not None else None


def _feedback_from_lifecycle_terminal_task(
    db: Session,
    task: AiTask,
    *,
    terminal_status: AiTaskStatus,
) -> FeedbackModel | None:
    answer_id = str(task.target_ref_id or "").strip()
    if not answer_id:
        return None
    answer = db.get(AnswerModel, answer_id)
    if answer is None or answer.owner_id != task.owner_id:
        return None
    feedback_id = _lifecycle_terminal_feedback_id(task.id)
    payload = _lifecycle_terminal_feedback_payload(
        task,
        feedback_id=feedback_id,
        answer=answer,
        terminal_status=terminal_status,
    )
    return FeedbackModel(
        id=feedback_id,
        owner_id=task.owner_id,
        actor_id=task.actor_id or task.owner_id,
        record_version=1,
        status=terminal_status.value,
        trace_ref_ids=[task.id],
        evidence_ref_ids=None,
        created_at=task.updated_at,
        updated_at=task.updated_at,
        session_id=answer.session_id,
        answer_id=answer_id,
        ai_task_id=task.id,
        score_result_id=None,
        feedback_summary=json.dumps(payload, ensure_ascii=False, sort_keys=True),
    )


def _lifecycle_terminal_feedback_payload(
    task: AiTask,
    *,
    feedback_id: str,
    answer: AnswerModel,
    terminal_status: AiTaskStatus,
) -> dict[str, object]:
    user_visible_status = _task_user_visible_status(terminal_status.value)
    error_code = _lifecycle_terminal_error_code(terminal_status)
    return {
        "schema_id": POLISH_FEEDBACK_FINAL_SCHEMA_ID,
        "schema_version": POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
        "contract_ids": list(POLISH_FEEDBACK_FINAL_CONTRACT_IDS),
        "status": terminal_status.value,
        "feedback_id": feedback_id,
        "feedback_text": user_visible_status,
        "answer_summary": "",
        "user_visible_status": user_visible_status,
        "retryable": terminal_status.value in _FEEDBACK_LIFECYCLE_RETRYABLE_STATUSES,
        "error": {
            "code": error_code,
            "message": user_visible_status,
            "metadata": {
                "stage": _lifecycle_terminal_stage(terminal_status),
                "ai_task_id": task.id,
            },
        },
        "validation_errors": [error_code],
        "score_result": None,
        "loss_points": [],
        "reference_answer": None,
        "next_recommended_actions": _lifecycle_terminal_next_actions(terminal_status),
        "trace_refs": [],
        "low_confidence_flags": [],
        "session_id": answer.session_id,
        "question_id": answer.question_id,
        "feedback_metadata": {
            "llm_called": False,
            "task_type": POLISH_FEEDBACK_TASK_TYPE,
            "answer_id": answer.id,
            "question_id": answer.question_id,
            "session_id": answer.session_id,
            "provider_status": "not_called",
            "stage": _lifecycle_terminal_stage(terminal_status),
        },
    }


def _task_result_from_lifecycle_terminal_task(
    task: AiTask,
    *,
    terminal_status: AiTaskStatus,
) -> AiTaskResult:
    error_code = _lifecycle_terminal_error_code(terminal_status)
    safe_summary_json = {
        "task_type": task.task_type,
        "status": terminal_status.value,
        "ai_task_id": task.id,
        "answer_id": task.target_ref_id,
        "retryable": terminal_status.value in _FEEDBACK_LIFECYCLE_RETRYABLE_STATUSES,
        "user_visible_status": _task_user_visible_status(terminal_status.value),
        "validation_errors": [error_code],
        "error": {
            "code": error_code,
            "metadata": {"stage": _lifecycle_terminal_stage(terminal_status)},
        },
    }
    return AiTaskResult(
        id=f"{task.id}_result",
        owner_id=task.owner_id,
        actor_id=task.actor_id or task.owner_id,
        record_version=1,
        status=terminal_status.value,
        trace_ref_ids=[task.id],
        evidence_ref_ids=None,
        created_at=task.updated_at,
        updated_at=task.updated_at,
        ai_task_id=task.id,
        result_sequence="0",
        validation_result_ref_id=task.id,
        trace_ref_id=task.id,
        result_ref_id=None,
        candidate_refs_json=None,
        suggestion_refs_json=None,
        validation_errors_json=[error_code],
        source_availability=None,
        low_confidence_flags_json=None,
        safe_summary_json=safe_summary_json,
    )


def _feedback_lifecycle_terminal_status_from_task(task: AiTask) -> AiTaskStatus | None:
    if task.status in _FEEDBACK_LIFECYCLE_TERMINAL_STATUSES:
        return AiTaskStatus(task.status)
    if task.status in {AiTaskStatus.QUEUED.value, AiTaskStatus.RUNNING.value} and _task_deadline_expired(task):
        return AiTaskStatus.TIMED_OUT
    return None


def _apply_lifecycle_terminal_to_task_model(
    task: AiTask,
    *,
    terminal_status: AiTaskStatus,
) -> None:
    task.status = terminal_status.value
    task.trace_ref_ids = [task.id]
    task.updated_at = utc_now()


def _task_deadline_expired(task: AiTask) -> bool:
    if task.timeout_at is None:
        return False
    timeout_at = task.timeout_at
    if timeout_at.tzinfo is None:
        timeout_at = timeout_at.replace(tzinfo=timezone.utc)
    return timeout_at <= utc_now()


def _lifecycle_terminal_feedback_id(task_id: str) -> str:
    return f"fb_task_{sha256(task_id.encode('utf-8')).hexdigest()[:32]}"


def _lifecycle_terminal_error_code(status: AiTaskStatus) -> str:
    error_codes = {
        AiTaskStatus.CANCELLED: "feedback_generation_cancelled",
        AiTaskStatus.TIMED_OUT: "feedback_generation_deadline_exceeded",
    }
    return error_codes[status]


def _lifecycle_terminal_stage(status: AiTaskStatus) -> str:
    stages = {
        AiTaskStatus.CANCELLED: "cancelled",
        AiTaskStatus.TIMED_OUT: "deadline",
    }
    return stages[status]


def _lifecycle_terminal_next_actions(status: AiTaskStatus) -> list[str]:
    if status == AiTaskStatus.TIMED_OUT:
        return ["retry_same_question", "continue_same_question"]
    return ["continue_same_question"]


def _terminal_task_status_from_feedback(feedback: FeedbackModel) -> str | None:
    if feedback.status == "generated":
        return str(AiTaskStatus.SUCCEEDED)
    if feedback.status == str(AiTaskStatus.GENERATION_FAILED):
        return str(AiTaskStatus.GENERATION_FAILED)
    payload = _feedback_summary_payload(feedback.feedback_summary)
    if payload is not None and payload.get("status") == str(AiTaskStatus.GENERATION_FAILED):
        return str(AiTaskStatus.GENERATION_FAILED)
    return None


def _apply_terminal_feedback_to_task_model(
    task: AiTask,
    feedback: FeedbackModel,
    *,
    terminal_status: str,
) -> None:
    task.status = terminal_status
    task.updated_at = feedback.updated_at
    task.trace_ref_ids = [_terminal_feedback_trace_ref_id(task, feedback, terminal_status=terminal_status)]


def _task_result_from_terminal_feedback(
    task: AiTask,
    feedback: FeedbackModel,
    *,
    terminal_status: str,
) -> AiTaskResult:
    trace_ref_id = _terminal_feedback_trace_ref_id(
        task,
        feedback,
        terminal_status=terminal_status,
    )
    safe_summary_json = _feedback_summary_payload(feedback.feedback_summary)
    return AiTaskResult(
        id=f"{task.id}_result",
        owner_id=task.owner_id,
        actor_id=task.actor_id or feedback.actor_id or feedback.owner_id,
        record_version=1,
        status=terminal_status,
        trace_ref_ids=[trace_ref_id],
        evidence_ref_ids=None,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at,
        ai_task_id=task.id,
        result_sequence="0",
        validation_result_ref_id=task.id
        if terminal_status == str(AiTaskStatus.GENERATION_FAILED)
        else None,
        trace_ref_id=trace_ref_id,
        result_ref_id=feedback.id if terminal_status == str(AiTaskStatus.SUCCEEDED) else None,
        candidate_refs_json=None,
        suggestion_refs_json=None,
        validation_errors_json=_validation_errors_from_feedback_payload(safe_summary_json),
        source_availability=None,
        low_confidence_flags_json=None,
        safe_summary_json=safe_summary_json,
    )


def _terminal_feedback_trace_ref_id(
    task: AiTask,
    feedback: FeedbackModel,
    *,
    terminal_status: str,
) -> str:
    if terminal_status == str(AiTaskStatus.SUCCEEDED):
        return feedback.id
    return task.id


def _feedback_summary_payload(value: str | None) -> dict[str, object] | None:
    if value is None:
        return None
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _validation_errors_from_feedback_payload(payload: dict[str, object] | None) -> list[str] | None:
    if payload is None:
        return None
    raw_errors = payload.get("validation_errors")
    if isinstance(raw_errors, list):
        errors = [str(item) for item in raw_errors if isinstance(item, str) and item.strip()]
        return errors or None
    raw_error = payload.get("error")
    if not isinstance(raw_error, dict):
        return None
    error_code = raw_error.get("code")
    if isinstance(error_code, str) and error_code.strip():
        return [error_code]
    return None


def _should_persist_task_safe_summary(task: PolishTaskStatus) -> bool:
    if isinstance(getattr(task, "safe_summary", None), dict):
        return True
    return (
        task.task_type in _QUESTION_GENERATION_TASK_TYPES
        and _task_status_value(task.status) in _TASK_RESULT_TERMINAL_FAILURE_STATUSES
    )


def _task_safe_summary_json(
    task: PolishTaskStatus,
    *,
    candidate_refs_json: list[dict[str, str]],
    suggestion_refs_json: list[dict[str, str]],
    validation_errors_json: list[str],
    source_availability: str | None,
    low_confidence_flags_json: list[str],
) -> dict[str, Any] | None:
    base_summary: dict[str, Any] = {
        "task_type": task.task_type,
        "status": _task_status_value(task.status),
        "user_visible_status": task.user_visible_status,
        "retryable": task.retryable,
        "candidate_refs": candidate_refs_json,
        "suggestion_refs": suggestion_refs_json,
        "validation_errors": validation_errors_json,
        "source_availability": source_availability,
        "low_confidence_flags": low_confidence_flags_json,
    }
    safe_summary = getattr(task, "safe_summary", None)
    if isinstance(safe_summary, dict):
        return base_summary | safe_summary
    if _should_persist_task_safe_summary(task):
        return base_summary
    return None


def _task_status_value(status: object) -> str:
    return str(getattr(status, "value", status))


def _resource_refs_to_safe_json(refs: tuple[ResourceRef, ...]) -> list[dict[str, str]]:
    return [
        {"resource_type": ref.resource_type, "resource_id": ref.resource_id}
        for ref in refs
    ]


def _source_availability_for_task(task: PolishTaskStatus) -> str | None:
    if _task_status_value(task.status) == AiTaskStatus.SOURCE_UNAVAILABLE.value:
        return AiTaskStatus.SOURCE_UNAVAILABLE.value
    return None


def _feedback_idempotency_record_prefix(idempotency_key: str) -> str:
    key_hash = sha256(idempotency_key.encode("utf-8")).hexdigest()[:24]
    return f"polish_feedback:{key_hash}:"


def _feedback_idempotency_record_id(idempotency_key: str, request_body_hash: str) -> str:
    return f"{_feedback_idempotency_record_prefix(idempotency_key)}{request_body_hash[:24]}"


def _task_status_from_model(model: AiTask) -> PolishTaskStatus:
    trace_refs = model.trace_ref_ids if isinstance(model.trace_ref_ids, list) else []
    trace_ref_id = next((str(item) for item in trace_refs if str(item).strip()), model.id)
    return PolishTaskStatus(
        ai_task_id=model.id,
        task_type=model.task_type,
        status=AiTaskStatus(model.status),
        contract_ids=tuple(str(item) for item in model.contract_ids or []),
        retryable=False,
        result_ref=TraceRef(
            trace_ref_id=trace_ref_id,
            trace_type="ai_task",
            created_at=model.created_at,
        ),
        user_visible_status=_task_user_visible_status(model.status),
    )


def _task_user_visible_status(status: str) -> str:
    if status == str(AiTaskStatus.RUNNING):
        return "反馈生成中"
    if status == str(AiTaskStatus.QUEUED):
        return "任务已排队"
    return status


def _feedback_to_entity(model: FeedbackModel) -> PolishFeedback:
    return PolishFeedback(
        feedback_id=model.id,
        owner_id=model.owner_id,
        actor_id=model.actor_id or model.owner_id,
        session_id=model.session_id,
        answer_id=model.answer_id,
        ai_task_id=model.ai_task_id or "",
        score_result_id=model.score_result_id,
        feedback_summary=model.feedback_summary or "",
        status=model.status,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
