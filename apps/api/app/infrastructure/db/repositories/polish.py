"""SQLAlchemy repository for polish core workflows."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from threading import Lock
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.application.polish.entities import (
    PolishAnswer,
    PolishFeedback,
    PolishQuestion,
    PolishQuestionSource,
    PolishSession,
    PolishSessionReportSummary,
    PolishTaskStatus,
)
from app.application.polish.feedback_schema import POLISH_FEEDBACK_TASK_TYPE
from app.application.polish.ports import PolishRepository
from app.application.polish.question_metadata import (
    empty_question_metadata,
    normalize_question_metadata,
    question_metadata_to_dict,
)
from app.application.polish.theme_strategy import PolishThemeStrategy, resolve_polish_theme_strategy
from app.domain.shared.clock import utc_now
from app.domain.shared.refs import ResourceRef
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


_QUESTION_IDEMPOTENCY_LOCK_STRIPES = tuple(Lock() for _ in range(64))
_ANSWER_ROUND_RETRY_LIMIT = 3


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
            detail = db.scalar(
                select(PolishSessionDetailModel).where(
                    PolishSessionDetailModel.owner_id == session.owner_id,
                    PolishSessionDetailModel.session_id == session.session_id,
                )
            )
            session_model = db.get(InterviewSessionModel, session.session_id)
            if detail is None or session_model is None or session_model.owner_id != session.owner_id:
                return
            detail.progress_tree_status = session.progress_tree_status
            detail.progress_percent = session.progress_percent
            detail.progress_tree_plan_json = _payload_with_theme_metadata(session.progress_tree_plan, session.polish_theme)
            detail.progress_tree_state_json = _payload_with_theme_metadata(session.progress_tree_state, session.polish_theme)
            detail.updated_at = session.updated_at
            session_model.status = session.status
            session_model.updated_at = session.updated_at
            db.commit()

    def save_session_status(self, session: PolishSession) -> None:
        with self._session_factory() as db:
            session_model = db.get(InterviewSessionModel, session.session_id)
            if session_model is None or session_model.owner_id != session.owner_id:
                return
            detail = db.scalar(
                select(PolishSessionDetailModel).where(
                    PolishSessionDetailModel.owner_id == session.owner_id,
                    PolishSessionDetailModel.session_id == session.session_id,
                )
            )
            session_model.status = session.status
            session_model.updated_at = session.updated_at
            if detail is not None:
                detail.status = session.status
                detail.updated_at = session.updated_at
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
        lock = _question_idempotency_lock(
            owner_id=owner_id,
            session_id=session_id,
            graph_persistence_idempotency_key=graph_persistence_idempotency_key,
        )
        with lock:
            with self._session_factory() as db:
                existing = _find_question_model_by_graph_persistence_idempotency_key(
                    db,
                    owner_id=owner_id,
                    session_id=session_id,
                    graph_persistence_idempotency_key=graph_persistence_idempotency_key,
                )
                if existing is not None:
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
                AiTask(
                    id=task.ai_task_id,
                    owner_id=owner_id,
                    actor_id=actor_id,
                    record_version=1,
                    status=str(task.status),
                    trace_ref_ids=[task.result_ref.trace_ref_id],
                    evidence_ref_ids=None,
                    task_type=task.task_type,
                    contract_ids=list(task.contract_ids),
                    idempotency_record_id=None,
                    target_ref_id=target_ref_id,
                )
            )
            db.commit()

    def add_feedback_running_task(
        self,
        task: PolishTaskStatus,
        *,
        owner_id: str,
        actor_id: str,
        target_ref_id: str,
        idempotency_record_id: str | None = None,
    ) -> None:
        with self._session_factory() as db:
            existing = db.get(AiTask, task.ai_task_id)
            if existing is None:
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
                    existing,
                    task,
                    owner_id=owner_id,
                    actor_id=actor_id,
                    target_ref_id=target_ref_id,
                    idempotency_record_id=idempotency_record_id,
                )
            db.commit()

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
            db.add(_feedback_to_model(feedback))
            existing_task = db.get(AiTask, task.ai_task_id)
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
            db.add(_task_result_to_model(task, owner_id=owner_id, actor_id=actor_id))
            try:
                db.commit()
            except Exception:
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
            if result is None or feedback is None:
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


def _question_idempotency_lock(
    *,
    owner_id: str,
    session_id: str,
    graph_persistence_idempotency_key: str,
) -> Lock:
    lock_key = f"{owner_id}:{session_id}:{graph_persistence_idempotency_key}"
    digest = sha256(lock_key.encode("utf-8")).digest()
    return _QUESTION_IDEMPOTENCY_LOCK_STRIPES[digest[0] % len(_QUESTION_IDEMPOTENCY_LOCK_STRIPES)]


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
    )


def _feedback_idempotency_record_prefix(idempotency_key: str) -> str:
    key_hash = sha256(idempotency_key.encode("utf-8")).hexdigest()[:24]
    return f"polish_feedback:{key_hash}:"


def _feedback_idempotency_record_id(idempotency_key: str, request_body_hash: str) -> str:
    return f"{_feedback_idempotency_record_prefix(idempotency_key)}{request_body_hash[:24]}"


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
