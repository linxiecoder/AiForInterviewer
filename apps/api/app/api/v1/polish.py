"""
面试打磨（Polish）HTTP 路由适配器。

职责：
  - 将 HTTP 请求翻译成 Application 层的 Command / Query
  - 将 Application 层的 Entity / Result 翻译成 JSON 响应
  - 日志埋点、幂等键处理、安全过滤（敏感字段脱敏）
  - 不包含业务逻辑，所有决策委派给 PolishUseCases

端点概览：
  主题 /sessions /questions /answers /feedback /progress-tree
"""

from __future__ import annotations

import re
from time import perf_counter
from typing import Any

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session, sessionmaker
from starlette.concurrency import run_in_threadpool

from app.api.deps import (
    get_ai_orchestration_facade,
    get_db_session_factory,
    get_llm_transport,
    get_question_generation_runtime_policy,
    get_question_generation_runtime_policy_resolver,
    require_authenticated_actor,
)
from app.api.envelope import success_envelope
from app.api.errors import raise_api_error
from app.application.polish.commands import (
    CompletePolishQuestionCommand,
    CreatePolishAnswerCommand,
    CreatePolishFeedbackTaskCommand,
    CreatePolishQuestionTaskCommand,
    CreatePolishSessionCommand,
    EndPolishSessionCommand,
    GeneratePolishSessionReportCommand,
    GenerateInitialPolishProgressTreeCommand,
    RefreshPolishProgressTreeStateCommand,
    SoftDeletePolishSessionCommand,
)
from app.application.ai_runtime.facade import AiOrchestrationFacade
from app.application.polish.entities import (
    PolishAnswer,
    PolishSession,
    PolishSessionDetail,
    PolishTaskStatus,
    PolishTopic,
)
from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
    POLISH_FEEDBACK_FINAL_PAYLOAD_FIELDS,
    POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
)
from app.application.polish.feedback_generation_service import FeedbackGenerationService
from app.application.polish.queries import GetPolishSessionQuery, ListPolishSessionsQuery, ListPolishTopicsQuery
from app.application.polish.progress_tree import PolishProgressTreeLlmService
from app.application.polish.question_generation_policy import (
    QuestionGenerationRuntimePolicy,
    QuestionGenerationRuntimePolicyResolver,
)
from app.application.polish.question_generation_service import QuestionGenerationService
from app.application.polish.question_metadata import empty_question_metadata, normalize_question_metadata
from app.application.polish.session_continuity import (
    SessionContinuitySnapshot,
    compute_session_continuity,
)
from app.application.polish.theme_strategy import PolishThemeStrategy, resolve_polish_theme_strategy
from app.application.polish.use_cases import (
    POLISH_TOPICS,
    QUESTION_EXECUTION_SOURCE_FEEDBACK_NEXT_QUESTION_INTENT,
    QUESTION_GENERATION_MODE_NEW,
    PolishUseCases,
)
from app.domain.auth.entities import CurrentActor
from app.domain.shared.enums import ApiStatus
from app.domain.shared.errors import DomainError
from app.domain.shared.refs import TraceRef, VersionRef as DomainVersionRef
from app.infrastructure.db.repositories.assets import SqlAlchemyAssetRepository
from app.infrastructure.db.repositories.bindings import SqlAlchemyBindingRepository
from app.infrastructure.db.repositories.job_match import SqlAlchemyJobMatchAnalysisRepository
from app.infrastructure.db.repositories.jobs import SqlAlchemyJobRepository
from app.infrastructure.db.repositories.polish import SqlAlchemyPolishRepository
from app.infrastructure.db.repositories.resumes import SqlAlchemyResumeRepository
from app.application.llm.ports import LlmTransport
from app.infrastructure.observability.logging import LogUtil
from app.schemas.polish import (
    CreateAnswerRequest,
    CreateFeedbackNextQuestionIntentRequest,
    CreateFeedbackTaskRequest,
    CreateQuestionTaskRequest,
    CreatePolishSessionRequest,
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

# ── 常量区 ──────────────────────────────────────────────────────────
# 以下常量控制：Legacy 兼容标题、默认反馈文案、推荐操作列表、响应脱敏规则

LEGACY_TOPIC_TITLE_BY_ID = {
    "topic_project_depth": "经历真实性与贡献澄清",
    "topic_system_design": "能力深度与技术深挖",
    "topic_behavioral": "情景模拟与角色扮演",
}
PENDING_FEEDBACK_TEXT = "本轮反馈尚未生成"

# 仅作答（无反馈）时允许的推荐操作
ANSWER_NEXT_RECOMMENDED_ACTIONS = (
    "answer_again",
    "continue_same_question",
)

# 反馈 payload 中禁止暴露给前端的字段（LLM 原始输入/输出）
FORBIDDEN_FEEDBACK_PAYLOAD_RESPONSE_KEYS = frozenset(
    {
        "prompt",
        "raw_prompt",  # sensitive response denylist marker
        "system_prompt",  # sensitive response denylist marker
        "completion",
        "raw_completion",
        "provider_payload",  # sensitive response denylist marker
        "raw_provider_payload",  # sensitive response denylist marker
        "provider_response",
        "raw_provider_response",
    }
)

FEEDBACK_PAYLOAD_RESPONSE_TOP_LEVEL_KEYS = frozenset(POLISH_FEEDBACK_FINAL_PAYLOAD_FIELDS) | frozenset(
    {
        "error",
        "retryable",
        "user_visible_status",
        "validation_errors",
    }
)


# ── 主题端点 ────────────────────────────────────────────────────────

@router.get("/polish-topics")
async def list_polish_topics(
    resume_job_binding_id: str | None = None,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
    llm_transport: LlmTransport = Depends(get_llm_transport),
) -> Any:
    use_cases = _use_cases(session_factory, llm_transport)
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


# ── 会话端点 ────────────────────────────────────────────────────────

@router.get("/polish-sessions")
async def list_polish_sessions(
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
    llm_transport: LlmTransport = Depends(get_llm_transport),
) -> Any:
    use_cases = _use_cases(session_factory, llm_transport)
    result = use_cases.list_sessions(ListPolishSessionsQuery(owner_id=actor.owner_id))
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(
        resource_type="polish_session_list",
        data=[_session_summary_response(session).model_dump(mode="json") for session in result.value],
    )


@router.post("/polish-sessions", status_code=201)
async def create_polish_session(
    # 创建新打磨会话：绑定简历-岗位关系，指定主题/子主题/自定义主题文本，进度树初始为待生成
    payload: CreatePolishSessionRequest,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
    llm_transport: LlmTransport = Depends(get_llm_transport),
) -> Any:
    use_cases = _use_cases(session_factory, llm_transport)
    started_at = perf_counter()
    LogUtil.polish_session_create_started(
        resume_job_binding_id=payload.resume_job_binding_id,
        topic_id=payload.topic_id,
        subtopic_id=payload.subtopic_id,
        has_custom_topic_text=bool(payload.custom_topic_text),
        polish_theme=payload.polish_theme,
    )
    create_result = await run_in_threadpool(
        use_cases.create_session,
        CreatePolishSessionCommand(
            owner_id=actor.owner_id,
            actor_id=actor.actor_id,
            resume_job_binding_id=payload.resume_job_binding_id,
            topic_id=payload.topic_id,
            subtopic_id=payload.subtopic_id,
            custom_topic_text=payload.custom_topic_text,
            polish_theme=payload.polish_theme,
        ),
    )
    if not create_result.is_success:
        LogUtil.polish_session_create_failed(
            duration_ms=_elapsed_ms(started_at),
            error_code=create_result.error.code,
            error_message=create_result.error.message,
        )
        _raise_result_error(create_result.error)

    get_result = use_cases.get_session(
        GetPolishSessionQuery(owner_id=actor.owner_id, session_id=create_result.value.session_id)
    )
    if not get_result.is_success:
        LogUtil.polish_session_create_failed(
            duration_ms=_elapsed_ms(started_at),
            session_id=create_result.value.session_id,
            error_code=get_result.error.code,
            error_message=get_result.error.message,
        )
        _raise_result_error(get_result.error)
    LogUtil.polish_session_create_completed(
        duration_ms=_elapsed_ms(started_at),
        session_id=create_result.value.session_id,
        progress_tree_status=create_result.value.progress_tree_status,
        progress_percent=create_result.value.progress_percent,
    )
    return success_envelope(
        resource_type="polish_session",
        data=_session_response(get_result.value),
    )


@router.get("/polish-sessions/{session_id}")
async def get_polish_session(
    session_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
    llm_transport: LlmTransport = Depends(get_llm_transport),
) -> Any:
    """获取单个打磨会话详情：包含所有轮次（turns）、题目、答案、反馈"""
    use_cases = _use_cases(session_factory, llm_transport)
    result = use_cases.get_session(GetPolishSessionQuery(owner_id=actor.owner_id, session_id=session_id))
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(
        resource_type="polish_session",
        data=_session_response(result.value),
    )


# ── 出题/作答/反馈端点 ─────────────────────────────────────────────

@router.post("/polish-sessions/{session_id}/questions", status_code=202)
async def create_polish_question_task(
    session_id: str,
    payload: CreateQuestionTaskRequest | None = None,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
    llm_transport: LlmTransport = Depends(get_llm_transport),
    ai_orchestration_facade: AiOrchestrationFacade | None = Depends(get_ai_orchestration_facade),
    question_generation_policy: QuestionGenerationRuntimePolicy = Depends(get_question_generation_runtime_policy),
    question_generation_policy_resolver: QuestionGenerationRuntimePolicyResolver = Depends(
        get_question_generation_runtime_policy_resolver
    ),
) -> Any:
    intent = payload or CreateQuestionTaskRequest()
    use_cases = _use_cases(
        session_factory,
        llm_transport,
        ai_orchestration_facade=ai_orchestration_facade,
        question_generation_policy=question_generation_policy,
        question_generation_policy_resolver=question_generation_policy_resolver,
    )
    result = await run_in_threadpool(
        use_cases.create_question_task,
        CreatePolishQuestionTaskCommand(
            owner_id=actor.owner_id,
            actor_id=actor.actor_id,
            generation_mode=QUESTION_GENERATION_MODE_NEW,
            session_id=session_id,
            selected_progress_node_ref=intent.selected_progress_node_ref,
            exclude_question_refs=tuple(intent.exclude_question_refs),
            completed_focus_refs=tuple(intent.completed_focus_refs),
        ),
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(
        status=ApiStatus.ACCEPTED,
        resource_type="ai_task",
        data=_task_response(
            result.value,
            contract_shape=_question_task_contract_shape(result.value),
        ),
    )


# 将题目标记为已完成，返回更新后的会话详情
@router.post("/polish-sessions/{session_id}/questions/{question_id}/complete")
async def complete_polish_question(
    session_id: str,
    question_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
    llm_transport: LlmTransport = Depends(get_llm_transport),
) -> Any:
    use_cases = _use_cases(session_factory, llm_transport)
    result = await run_in_threadpool(
        use_cases.complete_question,
        CompletePolishQuestionCommand(
            owner_id=actor.owner_id,
            actor_id=actor.actor_id,
            session_id=session_id,
            question_id=question_id,
        ),
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(
        resource_type="polish_session",
        data=_session_response(result.value),
    )


# 结束打磨会话，标记为已完成
@router.post("/polish-sessions/{session_id}/end")
async def end_polish_session(
    session_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
    llm_transport: LlmTransport = Depends(get_llm_transport),
) -> Any:
    use_cases = _use_cases(session_factory, llm_transport)
    result = await run_in_threadpool(
        use_cases.end_session,
        EndPolishSessionCommand(
            owner_id=actor.owner_id,
            actor_id=actor.actor_id,
            session_id=session_id,
        ),
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(
        resource_type="polish_session",
        data=_session_response(result.value),
    )


@router.post("/polish-sessions/{session_id}/report")
async def generate_polish_session_report(
    session_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
    llm_transport: LlmTransport = Depends(get_llm_transport),
) -> Any:
    use_cases = _use_cases(session_factory, llm_transport)
    result = await run_in_threadpool(
        use_cases.generate_session_report,
        GeneratePolishSessionReportCommand(
            owner_id=actor.owner_id,
            actor_id=actor.actor_id,
            session_id=session_id,
        ),
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(
        resource_type="polish_session_report",
        data=_session_response(result.value),
    )


@router.post("/polish-sessions/{session_id}/delete")
async def soft_delete_polish_session(
    session_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
    llm_transport: LlmTransport = Depends(get_llm_transport),
) -> Any:
    use_cases = _use_cases(session_factory, llm_transport)
    result = await run_in_threadpool(
        use_cases.soft_delete_session,
        SoftDeletePolishSessionCommand(
            owner_id=actor.owner_id,
            actor_id=actor.actor_id,
            session_id=session_id,
        ),
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(
        resource_type="polish_session",
        data=_session_response(result.value),
    )


# 提交用户作答（同步），支持 Idempotency-Key 幂等重试
@router.post("/polish-sessions/{session_id}/answers", status_code=201)
async def create_polish_answer(
    session_id: str,
    payload: CreateAnswerRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
    llm_transport: LlmTransport = Depends(get_llm_transport),
) -> Any:
    use_cases = _use_cases(session_factory, llm_transport)
    base_ref = (
        DomainVersionRef(
            resource_type=payload.base_question_version_ref.resource_type,
            resource_id=payload.base_question_version_ref.resource_id,
            version_id=payload.base_question_version_ref.version_id,
        )
        if payload.base_question_version_ref is not None
        else None
    )
    clean_idempotency_key = _clean_optional_header(idempotency_key)
    command = CreatePolishAnswerCommand(
        owner_id=actor.owner_id,
        actor_id=actor.actor_id,
        session_id=session_id,
        question_id=payload.question_id,
        answer_text=payload.answer_text,
        base_question_version_ref=base_ref,
        idempotency_key=clean_idempotency_key,
    )
    result = await run_in_threadpool(use_cases.create_answer, command)
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(
        resource_type="polish_answer",
        data=_answer_response(result.value, idempotency_key=clean_idempotency_key),
    )


# 异步创建反馈任务（LLM 分析回答），返回 ai_task + 会话中的最新反馈 payload
@router.post("/polish-sessions/{session_id}/feedback", status_code=202)
async def create_polish_feedback_task(
    session_id: str,
    payload: CreateFeedbackTaskRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
    llm_transport: LlmTransport = Depends(get_llm_transport),
) -> Any:
    use_cases = _use_cases(session_factory, llm_transport)
    clean_idempotency_key = _clean_optional_header(idempotency_key)
    command = CreatePolishFeedbackTaskCommand(
        owner_id=actor.owner_id,
        actor_id=actor.actor_id,
        session_id=session_id,
        answer_id=payload.answer_id,
        internal_scoring_context=payload.scoring_context,
    )
    object.__setattr__(command, "idempotency_key", clean_idempotency_key)
    result = await run_in_threadpool(
        use_cases.create_feedback_task,
        command,
    )
    if not result.is_success:
        _raise_result_error(result.error)
    detail_result = use_cases.get_session(GetPolishSessionQuery(owner_id=actor.owner_id, session_id=session_id))
    if not detail_result.is_success:
        _raise_result_error(detail_result.error)
    answer_detail = _find_session_answer_detail(detail_result.value, payload.answer_id)
    if answer_detail is None:
        _raise_result_error(
            DomainError(code="not_found_or_inaccessible", message="Feedback answer not found after generation")
        )
    turn_question_id, answer = answer_detail
    return success_envelope(
        status=ApiStatus.ACCEPTED,
        resource_type="ai_task",
        data=_feedback_response(
            result.value,
            answer,
            session_id=session_id,
            question_id=turn_question_id,
        ),
    )


@router.post("/polish-sessions/{session_id}/feedback/{feedback_id}/next-question", status_code=202)
async def create_polish_feedback_next_question_task(
    session_id: str,
    feedback_id: str,
    payload: CreateFeedbackNextQuestionIntentRequest | None = None,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
    llm_transport: LlmTransport = Depends(get_llm_transport),
    ai_orchestration_facade: AiOrchestrationFacade | None = Depends(get_ai_orchestration_facade),
    question_generation_policy: QuestionGenerationRuntimePolicy = Depends(get_question_generation_runtime_policy),
    question_generation_policy_resolver: QuestionGenerationRuntimePolicyResolver = Depends(
        get_question_generation_runtime_policy_resolver
    ),
) -> Any:
    intent = payload or CreateFeedbackNextQuestionIntentRequest()
    use_cases = _use_cases(
        session_factory,
        llm_transport,
        ai_orchestration_facade=ai_orchestration_facade,
        question_generation_policy=question_generation_policy,
        question_generation_policy_resolver=question_generation_policy_resolver,
    )
    result = await run_in_threadpool(
        use_cases.create_question_task,
        CreatePolishQuestionTaskCommand(
            owner_id=actor.owner_id,
            actor_id=actor.actor_id,
            session_id=session_id,
            selected_progress_node_ref=intent.selected_progress_node_ref,
            exclude_question_refs=tuple(intent.exclude_question_refs),
            completed_focus_refs=tuple(intent.completed_focus_refs),
            execution_source=QUESTION_EXECUTION_SOURCE_FEEDBACK_NEXT_QUESTION_INTENT,
            authorized_feedback_id=feedback_id,
        ),
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(
        status=ApiStatus.ACCEPTED,
        resource_type="ai_task",
        data=_task_response(
            result.value,
            contract_shape=_question_task_contract_shape(result.value),
        ),
    )


# ── 进度树刷新端点 ──────────────────────────────────────────────────
# 刷新进度树状态：API 层只做适配，状态刷新与持久化统一委托 Application 层。
@router.post("/polish-sessions/{session_id}/progress-tree/state")
async def refresh_polish_progress_tree_state(
    session_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
    llm_transport: LlmTransport = Depends(get_llm_transport),
) -> Any:
    use_cases = _use_cases(session_factory, llm_transport)
    result = await run_in_threadpool(
        use_cases.refresh_progress_tree_state,
        RefreshPolishProgressTreeStateCommand(
            owner_id=actor.owner_id,
            actor_id=actor.actor_id,
            session_id=session_id,
        ),
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(
        resource_type="polish_session",
        data=_session_response(result.value),
    )


@router.post("/polish-sessions/{session_id}/progress-tree/generate")
async def generate_initial_polish_progress_tree(
    session_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
    llm_transport: LlmTransport = Depends(get_llm_transport),
) -> Any:
    use_cases = _use_cases(session_factory, llm_transport)
    result = await run_in_threadpool(
        use_cases.generate_initial_progress_tree,
        GenerateInitialPolishProgressTreeCommand(
            owner_id=actor.owner_id,
            actor_id=actor.actor_id,
            session_id=session_id,
        ),
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(
        resource_type="polish_session",
        data=_session_response(result.value),
    )


# ── 辅助函数：获取 UseCases ─────────────────────────────────────────

def _use_cases(
    session_factory: sessionmaker[Session],
    llm_transport: LlmTransport,
    *,
    ai_orchestration_facade: AiOrchestrationFacade | None = None,
    question_generation_policy: QuestionGenerationRuntimePolicy | None = None,
    question_generation_policy_resolver: QuestionGenerationRuntimePolicyResolver | None = None,
) -> PolishUseCases:
    return PolishUseCases(
        polish_repository=SqlAlchemyPolishRepository(session_factory),
        binding_repository=SqlAlchemyBindingRepository(session_factory),
        resume_repository=SqlAlchemyResumeRepository(session_factory),
        job_repository=SqlAlchemyJobRepository(session_factory),
        job_match_repository=SqlAlchemyJobMatchAnalysisRepository(session_factory),
        asset_repository=SqlAlchemyAssetRepository(session_factory),
        progress_tree_service=PolishProgressTreeLlmService(llm_transport),
        question_generation_service=QuestionGenerationService(
            llm_transport=llm_transport,
            runtime_policy=question_generation_policy,
        ),
        feedback_generation_service=FeedbackGenerationService(llm_transport=llm_transport),
        question_generation_policy=question_generation_policy,
        question_generation_policy_resolver=question_generation_policy_resolver,
        ai_orchestration_facade=ai_orchestration_facade,
    )


# 计算从 started_at 至今的毫秒数（用于日志埋点）
def _elapsed_ms(started_at: float) -> float:
    return round((perf_counter() - started_at) * 1000, 3)


# ── 响应构建函数：主题 ──────────────────────────────────────────────

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


# ── 响应构建函数：会话详情（含所有轮次、兼容 Legacy 字段） ──────────

def _session_response(session: PolishSessionDetail) -> dict[str, object]:
    core = session.session
    turns = _session_turn_payloads(session)
    active_turn = turns[-1] if turns else None
    active_question_ref = (
        {"resource_type": "question", "resource_id": active_turn["question_id"]}
        if active_turn
        else None
    )
    active_node_ref = _active_progress_node_ref(active_turn, session.progress_tree_state)
    current_node_ref = (
        {"resource_type": "progress_node", "resource_id": active_node_ref}
        if active_node_ref is not None
        else None
    )
    theme_strategy = _theme_strategy_for_session(core)
    payload = {
        "session_id": core.session_id,
        "session_status": core.status,
        "resume_job_binding_id": core.binding_id,
        "resume_id": core.resume_id,
        "resume_version_id": core.resume_version_id,
        "job_id": core.job_id,
        "job_version_id": core.job_version_id,
        "job_title": session.job_title or "未命名岗位",
        "job_company": session.job_company or "未命名公司",
        "resume_title": session.resume_title or "未命名简历",
        "binding_label": session.binding_label or "",
        "polish_theme": theme_strategy.theme,
        "polish_theme_label": theme_strategy.label,
        "explicit_weight": theme_strategy.explicit_weight,
        "implicit_weight": theme_strategy.implicit_weight,
        "turns": turns,
        "progress_tree_status": session.progress_tree_status,
        "progress_percent": session.progress_percent,
        "progress_tree_plan": session.progress_tree_plan,
        "progress_tree_state": session.progress_tree_state,
        "topic_ref": _topic_ref(core.topic_id),
        "subtopic_ref": _subtopic_ref(core.topic_id, core.subtopic_id),
        "custom_topic_text_summary": core.custom_topic_text_summary,
        "report_id": core.report_summary.report_id if core.report_summary is not None else None,
        "report_status": core.report_summary.report_status if core.report_summary is not None else None,
        "report_generated_at": (
            core.report_summary.report_generated_at if core.report_summary is not None else None
        ),
        "current_question_ref": active_question_ref,
        "active_question_ref": active_question_ref,
        "progress_position_ref": current_node_ref,
        "current_node_ref": current_node_ref,
        "current_node_progress_node_ref": active_node_ref,
        "active_question_refs": [
            {"resource_type": "question", "resource_id": turn["question_id"]}
            for turn in turns
        ],
        "active_question_progress_node_ref": active_node_ref,
        "active_question_evidence_refs": (
            list(active_turn["evidence_refs"]) if active_turn else []
        ),
        "active_question_context_digest": (
            active_turn["context_digest"] if active_turn else None
        ),
        "low_confidence_flags": [],
        "created_at": core.created_at,
        "updated_at": core.updated_at,
        "mode": "polish",
        # keep legacy fields and compatibility shape for existing callers
    }
    continuity = compute_session_continuity(
        SessionContinuitySnapshot(
            session_status=str(core.status or ""),
            progress_tree_status=str(session.progress_tree_status or ""),
            progress_tree_plan=session.progress_tree_plan if isinstance(session.progress_tree_plan, dict) else {},
            progress_tree_state=session.progress_tree_state if isinstance(session.progress_tree_state, dict) else {},
            turn_count=len(turns),
            active_question_id=str(active_turn.get("question_id")) if active_turn else None,
            active_progress_node_ref=active_node_ref,
            evidence_refs=tuple(str(ref) for ref in active_turn.get("evidence_refs", ())) if active_turn else (),
            context_digest=str(active_turn.get("context_digest")) if active_turn and active_turn.get("context_digest") else None,
            question_metadata_items=tuple(turn.get("question_metadata") for turn in turns),
        )
    )
    payload.update(continuity.to_response_payload())
    return payload


# ── 响应构建函数：会话摘要 ───────────────────────────────────────────

def _session_summary_response(session: PolishSessionDetail) -> PolishSessionSummaryResponse:
    core = session.session
    theme_strategy = _theme_strategy_for_session(core)
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
        job_title=session.job_title or "未命名岗位",
        job_company=session.job_company or "未命名公司",
        resume_title=session.resume_title or "未命名简历",
        binding_label=session.binding_label or "",
        polish_theme=theme_strategy.theme,
        polish_theme_label=theme_strategy.label,
        explicit_weight=theme_strategy.explicit_weight,
        implicit_weight=theme_strategy.implicit_weight,
        topic_id=core.topic_id,
        subtopic_id=core.subtopic_id,
        custom_topic_text_summary=core.custom_topic_text_summary,
        report_id=core.report_summary.report_id if core.report_summary is not None else None,
        report_status=core.report_summary.report_status if core.report_summary is not None else None,
        report_generated_at=core.report_summary.report_generated_at if core.report_summary is not None else None,
        created_at=core.created_at,
        updated_at=core.updated_at,
    )


# 根据 session.polish_theme 解析主题策略，兜底返回无主题策略
def _theme_strategy_for_session(session: PolishSession) -> PolishThemeStrategy:
    try:
        return resolve_polish_theme_strategy(session.polish_theme)
    except ValueError:
        return resolve_polish_theme_strategy(None)


# 构建会话中所有轮次（turns）的 JSON payload
def _session_turn_payloads(session: PolishSessionDetail) -> list[dict[str, object]]:
    return [
        {
            "question_id": turn.question_id,
            "question_text": turn.question_text,
            "question_sources": [
                {
                    "index": source.index,
                    "source_type": source.source_type,
                    "title": source.title,
                    "excerpt": source.excerpt,
                    "ref_id": source.ref_id,
                    "availability": source.availability,
                }
                for source in turn.question_sources
            ],
            "question_created_at": turn.question_created_at,
            "progress_node_ref": turn.progress_node_ref,
            "evidence_refs": list(turn.evidence_refs),
            "context_digest": turn.context_digest,
            "question_metadata": _question_metadata_payload(turn.question_metadata),
            "answers": [
                _session_answer_payload(
                    answer,
                    session_id=session.session.session_id,
                    question_id=turn.question_id,
                )
                for answer in turn.answers
            ],
        }
        for turn in getattr(session, "turns", ())
    ]


# ── 响应构建函数：答案 metadata、活跃节点引用 ───────────────────────

def _question_metadata_payload(raw_metadata: object) -> dict[str, Any]:
    try:
        return normalize_question_metadata(raw_metadata)
    except Exception:
        return empty_question_metadata().to_dict()


# 从活跃轮次或进度树状态中提取当前进度节点引用
def _active_progress_node_ref(
    active_turn: dict[str, object] | None,
    progress_tree_state: dict[str, Any],
) -> str | None:
    if active_turn is not None:
        turn_node_ref = active_turn.get("progress_node_ref")
        if isinstance(turn_node_ref, str) and turn_node_ref:
            return turn_node_ref
    current_priority = progress_tree_state.get("current_priority")
    if isinstance(current_priority, dict):
        priority_ref = current_priority.get("progress_node_ref")
        if isinstance(priority_ref, str) and priority_ref:
            return priority_ref
    return None


# ── 响应构建函数：答案、反馈、任务 ──────────────────────────────────

def _session_answer_payload(answer: object, *, session_id: str, question_id: str) -> dict[str, object]:
    feedback_payload = _answer_feedback_payload(answer, session_id=session_id, question_id=question_id)
    return {
        "answer_id": getattr(answer, "answer_id"),
        "answer_round": getattr(answer, "answer_round"),
        "answer_text": getattr(answer, "answer_text"),
        "answer_created_at": getattr(answer, "answer_created_at"),
        "feedback_text": feedback_payload["feedback_text"],
        "feedback_id": getattr(answer, "feedback_id", None),
        "score_result_id": getattr(answer, "score_result_id", None),
        "feedback_created_at": getattr(answer, "feedback_created_at", None),
        "feedback_payload": feedback_payload,
        "next_recommended_actions": list(feedback_payload.get("next_recommended_actions", [])),
        "low_confidence_flags": list(feedback_payload.get("low_confidence_flags", [])),
        "trace_refs": list(feedback_payload.get("trace_refs", [])),
    }


def _answer_response(answer: PolishAnswer, *, idempotency_key: str | None = None) -> dict[str, object]:
    feedback_payload = _answer_feedback_payload(answer)
    payload: dict[str, object] = {
        "answer_id": answer.answer_id,
        "session_id": answer.session_id,
        "question_id": answer.question_id,
        "answer_round": answer.answer_round,
        "answer_text": answer.answer_text,
        "status": answer.status,
        "created_at": answer.created_at,
        "updated_at": answer.updated_at,
        "feedback_text": feedback_payload["feedback_text"],
        "feedback_id": None,
        "score_result_id": None,
        "feedback_created_at": None,
        "feedback_payload": feedback_payload,
        "next_recommended_actions": list(feedback_payload.get("next_recommended_actions", [])),
        "low_confidence_flags": list(feedback_payload.get("low_confidence_flags", [])),
        "trace_refs": list(feedback_payload.get("trace_refs", [])),
    }
    if idempotency_key is not None:
        payload["idempotency_key"] = idempotency_key
    return payload


def _feedback_response(
    task: PolishTaskStatus,
    answer: object,
    *,
    session_id: str,
    question_id: str,
) -> dict[str, object]:
    feedback_payload = _answer_feedback_payload(answer, session_id=session_id, question_id=question_id)
    payload = _task_response(task, contract_shape=feedback_payload)
    payload.update(
        {
            "feedback_id": getattr(answer, "feedback_id", None),
            "feedback_status": feedback_payload["status"],
            "session_id": session_id,
            "question_id": question_id,
            "answer_id": getattr(answer, "answer_id"),
            "answer_round": getattr(answer, "answer_round"),
            "feedback_text": feedback_payload["feedback_text"],
            "feedback_created_at": getattr(answer, "feedback_created_at", None),
            "score_result_id": getattr(answer, "score_result_id", None),
            "score_result": feedback_payload.get("score_result"),
            "feedback_payload": feedback_payload,
            "next_recommended_actions": list(feedback_payload.get("next_recommended_actions", [])),
            "low_confidence_flags": list(feedback_payload.get("low_confidence_flags", [])),
            "trace_refs": list(feedback_payload.get("trace_refs", [])),
        }
    )
    return payload


# ── 辅助函数：幂等键清理 ────────────────────────────────────────────

def _clean_optional_header(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


# ── 核心：反馈 payload 构造（pending / stored payload） ───────────────
def _answer_feedback_payload(
    answer: object,
    *,
    session_id: str | None = None,
    question_id: str | None = None,
) -> dict[str, object]:
    answer_id = str(getattr(answer, "answer_id"))
    answer_session_id = session_id or str(getattr(answer, "session_id", ""))
    answer_question_id = question_id or str(getattr(answer, "question_id", ""))
    feedback_id = getattr(answer, "feedback_id", None)
    stored_payload = getattr(answer, "feedback_payload", None)
    if isinstance(stored_payload, dict) and feedback_id:
        payload = _response_safe_feedback_payload(stored_payload)
        if "feedback_text" not in payload:
            fallback_text = getattr(answer, "feedback_text", None)
            if isinstance(fallback_text, str) and fallback_text.strip():
                payload["feedback_text"] = fallback_text
        return payload
    return _pending_feedback_payload(
        answer_id=answer_id,
        session_id=answer_session_id,
        question_id=answer_question_id,
        feedback_id=str(feedback_id) if feedback_id else None,
        trace_refs=_answer_trace_refs(answer),
    )


def _pending_feedback_payload(
    *,
    answer_id: str,
    session_id: str,
    question_id: str,
    feedback_id: str | None,
    trace_refs: list[dict[str, object]],
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_id": POLISH_FEEDBACK_FINAL_SCHEMA_ID,
        "schema_version": POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
        "contract_ids": list(POLISH_FEEDBACK_FINAL_CONTRACT_IDS),
        "status": "pending",
        "feedback_text": PENDING_FEEDBACK_TEXT,
        "answer_summary": None,
        "score_result": None,
        "loss_points": [],
        "reference_answer": None,
        "next_recommended_actions": list(ANSWER_NEXT_RECOMMENDED_ACTIONS),
        "trace_refs": trace_refs,
        "low_confidence_flags": [],
        "feedback_metadata": {
            "llm_called": False,
            "pending_reason": "feedback_not_generated",
            "answer_id": answer_id,
            "session_id": session_id,
            "question_id": question_id,
        },
    }
    if feedback_id:
        payload["feedback_id"] = feedback_id
    return payload


# ── 安全脱敏 ────────────────────────────────────────────────────────

REDACTED_SENSITIVE_FEEDBACK_DETAIL = "redacted_sensitive_detail"
ADDITIONAL_FORBIDDEN_FEEDBACK_PAYLOAD_RESPONSE_KEYS = frozenset(
    {
        "hidden_rubric",
        "full_evidence_text",
        "full_resume",
        "full_jd",
        "token",
        "api_key",
        "cookie",
        "secret",
        "hidden_scoring",
        "hidden_scoring_rules",
    }
)
FORBIDDEN_FEEDBACK_PAYLOAD_RESPONSE_VALUE_MARKERS = (
    "raw_prompt",  # sensitive response denylist marker
    "system_prompt",  # sensitive response denylist marker
    "developer_prompt",
    "user_prompt",
    "raw_completion",
    "completion",
    "provider_payload",  # sensitive response denylist marker
    "raw_provider_payload",  # sensitive response denylist marker
    "provider_response",
    "raw_provider_response",
    "hidden_rubric",
    "full_evidence_text",
    "full_resume",
    "full_resume_markdown",
    "full_jd",
    "full_jd_text",
    "hidden_scoring",
    "hidden_scoring_rules",
)
FORBIDDEN_FEEDBACK_PAYLOAD_RESPONSE_ASSIGNMENT_PATTERNS = (
    re.compile(r"api[_-]?key\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"cookie\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"token\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"secret\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"\bbearer\s+[a-z0-9._~+/=-]+", re.IGNORECASE),
)


# ── 安全脱敏 ────────────────────────────────────────────────────────

# 检查 dict key 是否属于禁止暴露的字段
def _is_forbidden_feedback_payload_response_key(key: str) -> bool:
    normalized = key.strip().lower()
    return (
        normalized in FORBIDDEN_FEEDBACK_PAYLOAD_RESPONSE_KEYS
        or normalized in ADDITIONAL_FORBIDDEN_FEEDBACK_PAYLOAD_RESPONSE_KEYS
        or "prompt" in normalized
    )


# 将字符串中的分隔符标准化为下划线（便于后续匹配标记）
def _normalized_feedback_sensitive_marker_text(value: str) -> str:
    return re.sub(r"[\s-]+", "_", value.lower())


# 递归脱敏：检查文本中是否包含敏感标记
def _redact_forbidden_feedback_payload_response_text(value: str) -> str:
    normalized = _normalized_feedback_sensitive_marker_text(value)
    if any(marker in normalized for marker in FORBIDDEN_FEEDBACK_PAYLOAD_RESPONSE_VALUE_MARKERS):
        return REDACTED_SENSITIVE_FEEDBACK_DETAIL
    if any(pattern.search(value) for pattern in FORBIDDEN_FEEDBACK_PAYLOAD_RESPONSE_ASSIGNMENT_PATTERNS):
        return REDACTED_SENSITIVE_FEEDBACK_DETAIL
    return value

# 安全获取反馈 payload：先删除禁止字段，再脱敏文本值
def _response_safe_feedback_payload(payload: dict[str, Any]) -> dict[str, object]:
    sanitized = _drop_forbidden_feedback_payload_response_keys(payload)
    if isinstance(sanitized, dict):
        return sanitized
    return {}


# 递归删除 payload 中所有禁止暴露的键，并脱敏字符串值中的敏感内容
def _drop_forbidden_feedback_payload_response_keys(value: Any, *, _depth: int = 0) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _drop_forbidden_feedback_payload_response_keys(item, _depth=_depth + 1)
            for key, item in value.items()
            if not _is_forbidden_feedback_payload_response_key(str(key))
            and (_depth != 0 or str(key) in FEEDBACK_PAYLOAD_RESPONSE_TOP_LEVEL_KEYS)
        }
    if isinstance(value, list):
        return [_drop_forbidden_feedback_payload_response_keys(item, _depth=_depth) for item in value]
    if isinstance(value, tuple):
        return [_drop_forbidden_feedback_payload_response_keys(item, _depth=_depth) for item in value]
    if isinstance(value, str):
        return _redact_forbidden_feedback_payload_response_text(value)
    return value


# 构造答案的 trace 引用
def _answer_trace_refs(answer: object) -> list[dict[str, object]]:
    answer_created_at = getattr(answer, "answer_created_at", None) or getattr(answer, "created_at", None)
    return [
        {
            "trace_ref_id": str(getattr(answer, "answer_id")),
            "trace_type": "answer",
            "created_at": answer_created_at,
            "redaction_boundary": "none",
        }
    ]


# 在 session detail 中按 answer_id 查找对应的 (question_id, answer)
def _find_session_answer_detail(session: PolishSessionDetail, answer_id: str) -> tuple[str, object] | None:
    for turn in session.turns:
        for answer in turn.answers:
            if answer.answer_id == answer_id:
                return turn.question_id, answer
    return None


# 将 ResourceRef 转为前端可用的扁平 dict（用于兼容旧版响应）
def _resource_ref_dump(ref: ResourceRef | None) -> dict[str, str] | None:
    if ref is None:
        return None
    return {"resource_type": ref.resource_type, "resource_id": ref.resource_id}


# ── 响应构建函数：任务状态 ──────────────────────────────────────────

def _task_response(task: PolishTaskStatus, *, contract_shape: dict[str, Any] | None = None) -> dict[str, object]:
    active_question_refs = [
        {"resource_type": ref.resource_type, "resource_id": ref.resource_id}
        for ref in task.candidate_refs
        if ref.resource_type == "question"
    ]
    active_question_progress_node_ref = next(
        (ref.resource_id for ref in task.candidate_refs if ref.resource_type == "progress_node"),
        None,
    )
    active_question_evidence_refs = [
        ref.resource_id
        for ref in task.candidate_refs
        if ref.resource_type == "evidence"
    ]
    payload = {
        "ai_task_id": task.ai_task_id,
        "task_type": task.task_type,
        "status": task.status,
        "contract_ids": list(task.contract_ids),
        "retryable": task.retryable,
        "result_ref": _trace_ref(task.result_ref),
        "user_visible_status": task.user_visible_status,
        "score_type": task.score_type,
        "active_question_refs": active_question_refs,
        "active_question_progress_node_ref": active_question_progress_node_ref,
        "active_question_evidence_refs": [
            {"resource_type": "evidence", "resource_id": ref}
            for ref in active_question_evidence_refs
        ],
        "active_question_context_digest": None,
        "candidate_refs": [
            {"resource_type": ref.resource_type, "resource_id": ref.resource_id}
            for ref in task.candidate_refs
        ],
        "suggestion_refs": [
            {"resource_type": ref.resource_type, "resource_id": ref.resource_id}
            for ref in task.suggestion_refs
        ],
        "validation_errors": list(getattr(task, "validation_errors", ())),
    }
    return payload


# ── 响应构建函数：题目契约形状 ──────────────────────────────────────

def _question_task_contract_shape(task: PolishTaskStatus) -> dict[str, Any]:
    question_ref: dict[str, str] | None = None
    progress_node_ref: str | None = None
    evidence_refs: list[dict[str, str]] = []
    source_refs: list[dict[str, str]] = []
    for ref in task.candidate_refs:
        source_refs.append({"resource_type": ref.resource_type, "resource_id": ref.resource_id})
        if ref.resource_type == "question":
            question_ref = {"resource_type": ref.resource_type, "resource_id": ref.resource_id}
        elif ref.resource_type == "progress_node":
            progress_node_ref = ref.resource_id
        elif ref.resource_type == "evidence":
            evidence_refs.append({"resource_type": ref.resource_type, "resource_id": ref.resource_id})
    return {
        "contract_id": "P-POLISH-002",
        "status": str(task.status),
        "source_refs": source_refs,
        "source_availability": "available" if source_refs else "partial",
        "question_ref": question_ref,
        "progress_node_ref": progress_node_ref,
        "evidence_refs": evidence_refs,
        "context_digest": None,
        "low_confidence_flags": [],
        "validation_result_ref": None,
        "trace_refs": [_trace_ref(task.result_ref)] if task.result_ref is not None else [],
        "session_summary_update_ref": None,
        "next_recommended_actions": ["continue_same_question"],
        "user_confirmation_required": False,
    }


# ── 响应构建函数：主题/子主题/标题/TraceRef ────────────────────────

def _topic_ref(topic_id: str | None) -> PolishTopicRefResponse | None:

    if topic_id is None:
        return None
    topic = next((item for item in POLISH_TOPICS if item.topic_id == topic_id), None)
    title = topic.title if topic else LEGACY_TOPIC_TITLE_BY_ID.get(topic_id)
    return PolishTopicRefResponse(topic_id=topic_id, title=title)


def _subtopic_ref(topic_id: str | None, subtopic_id: str | None) -> PolishSubtopicRefResponse | None:
    """根据 topic_id 和 subtopic_id 查找子主题引用，兜底返回 None"""
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


# 构造会话标题：优先取自定义主题文本，其次子主题标题，再取主题标题
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


# 将 TraceRef 转换为 TraceRefSchema（用于响应序列化）
def _trace_ref(ref: TraceRef | None) -> TraceRefSchema | None:
    if ref is None:
        return None
    return TraceRefSchema(
        trace_ref_id=ref.trace_ref_id,
        trace_type=ref.trace_type,
        created_at=ref.created_at,
        redaction_boundary=ref.redaction_boundary,
    )


# ── 错误处理 ────────────────────────────────────────────────────────

# 将 Domain Result 错误抛出为 API 异常
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


# 将 Domain error code 映射到 HTTP status code
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
