"""SQLAlchemy repository for polish core workflows."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.polish.entities import (
    PolishAnswer,
    PolishFeedback,
    PolishQuestion,
    PolishSession,
    PolishTaskStatus,
)
from app.application.polish.ports import PolishRepository
from app.domain.shared.refs import ResourceRef
from app.infrastructure.db.models.ai_task import AiTask
from app.infrastructure.db.models.answer import Answer as AnswerModel
from app.infrastructure.db.models.feedback import Feedback as FeedbackModel
from app.infrastructure.db.models.interview import (
    InterviewSession as InterviewSessionModel,
    PolishSessionDetail as PolishSessionDetailModel,
)
from app.infrastructure.db.models.question import Question as QuestionModel
from app.infrastructure.db.session import get_session_factory


class SqlAlchemyPolishRepository(PolishRepository):
    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()

    def add_session(self, session: PolishSession) -> None:
        with self._session_factory() as db:
            db.add(_session_to_model(session))
            db.add(_detail_to_model(session))
            db.commit()

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
                    PolishSessionDetailModel.owner_id == owner_id,
                )
                .order_by(InterviewSessionModel.updated_at.desc(), InterviewSessionModel.created_at.desc())
            ).all()
            return tuple(_session_to_entity(session, detail) for session, detail in rows)

    def get_session(self, owner_id: str, session_id: str) -> PolishSession | None:
        with self._session_factory() as db:
            session_model = db.get(InterviewSessionModel, session_id)
            if session_model is None or session_model.owner_id != owner_id or session_model.mode != "polish":
                return None
            detail_model = db.scalar(
                select(PolishSessionDetailModel).where(
                    PolishSessionDetailModel.owner_id == owner_id,
                    PolishSessionDetailModel.session_id == session_id,
                )
            )
            if detail_model is None:
                return None
            return _session_to_entity(session_model, detail_model)

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

    def get_ref(self, session_id: str) -> ResourceRef | None:
        with self._session_factory() as db:
            found = db.get(InterviewSessionModel, session_id)
            if found is None or found.mode != "polish":
                return None
            return ResourceRef(resource_type="polish_session", resource_id=session_id)


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
    )


def _session_to_entity(
    session_model: InterviewSessionModel,
    detail_model: PolishSessionDetailModel,
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
    )


def _question_to_model(question: PolishQuestion) -> QuestionModel:
    return QuestionModel(
        id=question.question_id,
        owner_id=question.owner_id,
        actor_id=question.actor_id,
        record_version=1,
        status=question.status,
        trace_ref_ids=None,
        evidence_ref_ids=None,
        created_at=question.created_at,
        updated_at=question.updated_at,
        session_id=question.session_id,
        ai_task_id=question.ai_task_id,
        question_text=question.question_text,
    )


def _question_to_entity(model: QuestionModel) -> PolishQuestion:
    return PolishQuestion(
        question_id=model.id,
        owner_id=model.owner_id,
        actor_id=model.actor_id or model.owner_id,
        session_id=model.session_id,
        ai_task_id=model.ai_task_id or "",
        question_text=model.question_text or "",
        status=model.status,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


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
