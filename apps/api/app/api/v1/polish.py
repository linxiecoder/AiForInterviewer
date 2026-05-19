"""Polish core HTTP adapters."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db_session_factory, require_authenticated_actor
from app.api.envelope import success_envelope
from app.api.errors import raise_api_error
from app.application.polish.commands import (
    CreatePolishAnswerCommand,
    CreatePolishFeedbackTaskCommand,
    CreatePolishQuestionTaskCommand,
    CreatePolishSessionCommand,
)
from app.application.polish.entities import (
    PolishAnswer,
    PolishSession,
    PolishSessionDetail,
    PolishTaskStatus,
    PolishTopic,
)
from app.application.polish.queries import GetPolishSessionQuery, ListPolishSessionsQuery, ListPolishTopicsQuery
from app.application.polish.use_cases import POLISH_TOPICS, PolishUseCases
from app.domain.auth.entities import CurrentActor
from app.domain.shared.enums import ApiStatus
from app.domain.shared.refs import TraceRef, VersionRef as DomainVersionRef
from app.infrastructure.db.repositories.bindings import SqlAlchemyBindingRepository
from app.infrastructure.db.repositories.jobs import SqlAlchemyJobRepository
from app.infrastructure.db.repositories.polish import SqlAlchemyPolishRepository
from app.infrastructure.db.repositories.resumes import SqlAlchemyResumeRepository
from app.schemas.polish import (
    CreateAnswerRequest,
    CreateFeedbackTaskRequest,
    CreatePolishSessionRequest,
    CreateQuestionTaskRequest,
    PolishAnswerResponse,
    PolishSessionResponse,
    PolishSessionSummaryResponse,
    PolishSubtopicRefResponse,
    PolishSubtopicResponse,
    PolishTaskStatusResponse,
    PolishTopicRefResponse,
    PolishTopicResponse,
)
from app.schemas.refs import ResourceRef, TraceRefSchema


router = APIRouter(tags=["polish"])


@router.get("/polish-topics")
async def list_polish_topics(
    resume_job_binding_id: str | None = None,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    use_cases = _use_cases(session_factory)
    result = use_cases.list_topics(
        ListPolishTopicsQuery(
            owner_id=actor.owner_id,
            resume_job_binding_id=resume_job_binding_id,
        )
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(
        resource_type="polish_topic_list",
        data=[_topic_response(topic).model_dump(mode="json") for topic in result.value],
    )


@router.get("/polish-sessions")
async def list_polish_sessions(
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    use_cases = _use_cases(session_factory)
    result = use_cases.list_sessions(ListPolishSessionsQuery(owner_id=actor.owner_id))
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(
        resource_type="polish_session_list",
        data=[_session_summary_response(session).model_dump(mode="json") for session in result.value],
    )


@router.post("/polish-sessions", status_code=201)
async def create_polish_session(
    payload: CreatePolishSessionRequest,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    use_cases = _use_cases(session_factory)
    create_result = use_cases.create_session(
        CreatePolishSessionCommand(
            owner_id=actor.owner_id,
            actor_id=actor.actor_id,
            resume_job_binding_id=payload.resume_job_binding_id,
            topic_id=payload.topic_id,
            subtopic_id=payload.subtopic_id,
            custom_topic_text=payload.custom_topic_text,
        )
    )
    if not create_result.is_success:
        _raise_result_error(create_result.error)

    get_result = use_cases.get_session(
        GetPolishSessionQuery(owner_id=actor.owner_id, session_id=create_result.value.session_id)
    )
    if not get_result.is_success:
        _raise_result_error(get_result.error)
    return success_envelope(
        resource_type="polish_session",
        data=_session_response(get_result.value).model_dump(mode="json"),
    )


@router.get("/polish-sessions/{session_id}")
async def get_polish_session(
    session_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    use_cases = _use_cases(session_factory)
    result = use_cases.get_session(GetPolishSessionQuery(owner_id=actor.owner_id, session_id=session_id))
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(
        resource_type="polish_session",
        data=_session_response(result.value).model_dump(mode="json"),
    )


@router.post("/polish-sessions/{session_id}/questions", status_code=202)
async def create_polish_question_task(
    session_id: str,
    payload: CreateQuestionTaskRequest,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    use_cases = _use_cases(session_factory)
    result = use_cases.create_question_task(
        CreatePolishQuestionTaskCommand(
            owner_id=actor.owner_id,
            actor_id=actor.actor_id,
            session_id=session_id,
            progress_node_ref=payload.progress_node_ref,
        )
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(
        status=ApiStatus.ACCEPTED,
        resource_type="ai_task",
        data=_task_response(result.value).model_dump(mode="json"),
    )


@router.post("/polish-sessions/{session_id}/answers", status_code=201)
async def create_polish_answer(
    session_id: str,
    payload: CreateAnswerRequest,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    use_cases = _use_cases(session_factory)
    base_ref = (
        DomainVersionRef(
            resource_type=payload.base_question_version_ref.resource_type,
            resource_id=payload.base_question_version_ref.resource_id,
            version_id=payload.base_question_version_ref.version_id,
        )
        if payload.base_question_version_ref is not None
        else None
    )
    result = use_cases.create_answer(
        CreatePolishAnswerCommand(
            owner_id=actor.owner_id,
            actor_id=actor.actor_id,
            session_id=session_id,
            question_id=payload.question_id,
            answer_text=payload.answer_text,
            base_question_version_ref=base_ref,
        )
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(
        resource_type="polish_answer",
        data=_answer_response(result.value).model_dump(mode="json"),
    )


@router.post("/polish-sessions/{session_id}/feedback", status_code=202)
async def create_polish_feedback_task(
    session_id: str,
    payload: CreateFeedbackTaskRequest,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    use_cases = _use_cases(session_factory)
    result = use_cases.create_feedback_task(
        CreatePolishFeedbackTaskCommand(
            owner_id=actor.owner_id,
            actor_id=actor.actor_id,
            session_id=session_id,
            answer_id=payload.answer_id,
        )
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(
        status=ApiStatus.ACCEPTED,
        resource_type="ai_task",
        data=_task_response(result.value).model_dump(mode="json", exclude_none=True),
    )


def _use_cases(session_factory: sessionmaker[Session]) -> PolishUseCases:
    return PolishUseCases(
        polish_repository=SqlAlchemyPolishRepository(session_factory),
        binding_repository=SqlAlchemyBindingRepository(session_factory),
        resume_repository=SqlAlchemyResumeRepository(session_factory),
        job_repository=SqlAlchemyJobRepository(session_factory),
    )


def _topic_response(topic: PolishTopic) -> PolishTopicResponse:
    return PolishTopicResponse(
        topic_id=topic.topic_id,
        title=topic.title,
        description=topic.description,
        requires_job_binding=topic.requires_job_binding,
        disabled_reason=topic.disabled_reason,
        subtopics=[
            PolishSubtopicResponse(
                subtopic_id=subtopic.subtopic_id,
                topic_id=subtopic.topic_id,
                title=subtopic.title,
                description=subtopic.description,
                disabled_reason=subtopic.disabled_reason,
            )
            for subtopic in topic.subtopics
        ],
    )


def _session_response(session: PolishSessionDetail) -> PolishSessionResponse:
    core = session.session
    turns = _session_turn_payloads(session)
    return PolishSessionResponse(
        session_id=core.session_id,
        session_status=core.status,
        resume_job_binding_id=core.binding_id,
        resume_id=core.resume_id,
        resume_version_id=core.resume_version_id,
        job_id=core.job_id,
        job_version_id=core.job_version_id,
        job_title=session.job_title or "\u672a\u547d\u540d\u5c97",
        job_company=session.job_company or "\u672a\u547d\u540d\u516c\u53f8",
        resume_title=session.resume_title or "\u672a\u547d\u540d\u7b80\u5386",
        binding_label=session.binding_label or "",
        turns=turns,
        topic_ref=_topic_ref(core.topic_id),
        subtopic_ref=_subtopic_ref(core.topic_id, core.subtopic_id),
        custom_topic_text_summary=core.custom_topic_text_summary,
        current_question_ref=None,
        progress_position_ref=None,
        low_confidence_flags=[],
        created_at=core.created_at,
        updated_at=core.updated_at,
    )


def _session_summary_response(session: PolishSessionDetail) -> PolishSessionSummaryResponse:
    core = session.session
    return PolishSessionSummaryResponse(
        id=core.session_id,
        session_id=core.session_id,
        title=_session_title(session),
        status=core.status,
        resume_job_binding_id=core.binding_id,
        resume_id=core.resume_id,
        resume_version_id=core.resume_version_id,
        job_id=core.job_id,
        job_version_id=core.job_version_id,
        job_title=session.job_title or "\u672a\u547d\u540d\u5c97",
        job_company=session.job_company or "\u672a\u547d\u540d\u516c\u53f8",
        resume_title=session.resume_title or "\u672a\u547d\u540d\u7b80\u5386",
        binding_label=session.binding_label or "",
        topic_id=core.topic_id,
        subtopic_id=core.subtopic_id,
        custom_topic_text_summary=core.custom_topic_text_summary,
        created_at=core.created_at,
        updated_at=core.updated_at,
    )


def _session_turn_payloads(session: PolishSessionDetail) -> list[dict[str, object]]:
    return [
        {
            "question_id": turn.question_id,
            "question_text": turn.question_text,
            "question_created_at": turn.question_created_at,
            "answers": [
                {
                    "answer_id": answer.answer_id,
                    "answer_round": answer.answer_round,
                    "answer_text": answer.answer_text,
                    "answer_created_at": answer.answer_created_at,
                    "feedback_text": answer.feedback_text,
                    "feedback_id": answer.feedback_id,
                    "score_result_id": answer.score_result_id,
                    "feedback_created_at": answer.feedback_created_at,
                }
                for answer in turn.answers
            ],
        }
        for turn in getattr(session, "turns", ())
    ]
def _answer_response(answer: PolishAnswer) -> PolishAnswerResponse:
    return PolishAnswerResponse(
        answer_id=answer.answer_id,
        session_id=answer.session_id,
        question_id=answer.question_id,
        answer_round=answer.answer_round,
        answer_text=answer.answer_text,
        created_at=answer.created_at,
        updated_at=answer.updated_at,
    )


def _task_response(task: PolishTaskStatus) -> PolishTaskStatusResponse:
    return PolishTaskStatusResponse(
        ai_task_id=task.ai_task_id,
        task_type=task.task_type,
        status=task.status,
        contract_ids=list(task.contract_ids),
        retryable=task.retryable,
        result_ref=_trace_ref(task.result_ref),
        user_visible_status=task.user_visible_status,
        score_type=task.score_type,
        candidate_refs=[
            ResourceRef(resource_type=ref.resource_type, resource_id=ref.resource_id)
            for ref in task.candidate_refs
        ],
        suggestion_refs=[
            ResourceRef(resource_type=ref.resource_type, resource_id=ref.resource_id)
            for ref in task.suggestion_refs
        ],
    )


def _topic_ref(topic_id: str | None) -> PolishTopicRefResponse | None:
    if topic_id is None:
        return None
    topic = next((item for item in POLISH_TOPICS if item.topic_id == topic_id), None)
    return PolishTopicRefResponse(topic_id=topic_id, title=topic.title if topic else None)


def _subtopic_ref(topic_id: str | None, subtopic_id: str | None) -> PolishSubtopicRefResponse | None:
    if topic_id is None or subtopic_id is None:
        return None
    topic = next((item for item in POLISH_TOPICS if item.topic_id == topic_id), None)
    subtopic = None
    if topic is not None:
        subtopic = next((item for item in topic.subtopics if item.subtopic_id == subtopic_id), None)
    return PolishSubtopicRefResponse(
        topic_id=topic_id,
        subtopic_id=subtopic_id,
        title=subtopic.title if subtopic else None,
    )


def _session_title(session: PolishSessionDetail) -> str:
    if session.session.custom_topic_text_summary:
        return session.session.custom_topic_text_summary
    if session.session.topic_id is not None and session.session.subtopic_id is not None:
        subtopic = _subtopic_ref(session.session.topic_id, session.session.subtopic_id)
        if subtopic is not None and subtopic.title:
            return subtopic.title
    topic = _topic_ref(session.session.topic_id)
    if topic is not None and topic.title:
        return topic.title
    return "Polish session"


def _trace_ref(ref: TraceRef | None) -> TraceRefSchema | None:
    if ref is None:
        return None
    return TraceRefSchema(
        trace_ref_id=ref.trace_ref_id,
        trace_type=ref.trace_type,
        created_at=ref.created_at,
        redaction_boundary=ref.redaction_boundary,
    )


def _raise_result_error(error) -> None:
    assert error is not None
    raise_api_error(
        status_code=_error_status(error.code),
        code=error.code,
        message=error.message,
        details=error.details,
        retryable=error.retryable,
        user_action=error.user_action,
    )


def _error_status(code: str) -> int:
    if code in {"stale_version_conflict", "idempotency_conflict"}:
        return 409
    if code == "validation_failed":
        return 422
    if code == "not_found_or_inaccessible":
        return 404
    if code == "source_unavailable":
        return 409
    return 400
