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
from dataclasses import replace
from time import perf_counter
from typing import Any

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session, sessionmaker
from starlette.concurrency import run_in_threadpool

from app.api.deps import get_db_session_factory, get_llm_transport, require_authenticated_actor
from app.api.envelope import success_envelope
from app.api.errors import raise_api_error
from app.application.polish.commands import (
    CompletePolishQuestionCommand,
    CreatePolishAnswerCommand,
    CreatePolishFeedbackTaskCommand,
    CreatePolishQuestionTaskCommand,
    CreatePolishSessionCommand,
    EndPolishSessionCommand,
    RefreshPolishProgressTreeStateCommand,
)
from app.application.polish.entities import (
    PolishAnswer,
    PolishSession,
    PolishSessionDetail,
    PolishTaskStatus,
    PolishTopic,
)
from app.application.polish.queries import GetPolishSessionQuery, ListPolishSessionsQuery, ListPolishTopicsQuery
from app.application.polish.progress_tree import PolishProgressTreeLlmService
from app.application.polish.question_metadata import empty_question_metadata, normalize_question_metadata
from app.application.polish.theme_strategy import PolishThemeStrategy, resolve_polish_theme_strategy
from app.application.polish.use_cases import POLISH_TOPICS, PolishUseCases
from app.domain.auth.entities import CurrentActor
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import ApiStatus
from app.domain.shared.errors import DomainError
from app.domain.shared.refs import TraceRef, VersionRef as DomainVersionRef
from app.infrastructure.db.repositories.bindings import SqlAlchemyBindingRepository
from app.infrastructure.db.repositories.job_match import SqlAlchemyJobMatchAnalysisRepository
from app.infrastructure.db.repositories.jobs import SqlAlchemyJobRepository
from app.infrastructure.db.repositories.polish import SqlAlchemyPolishRepository
from app.infrastructure.db.repositories.polish_candidates import SqlAlchemyPolishCandidateRepository
from app.infrastructure.db.repositories.resumes import SqlAlchemyResumeRepository
from app.application.llm.ports import LlmTransport
from app.infrastructure.observability.logging import LogUtil
from app.schemas.polish import (
    CreateAnswerRequest,
    CreateFeedbackTaskRequest,
    CreatePolishSessionRequest,
    CreateQuestionTaskRequest,
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
LEGACY_PENDING_FEEDBACK_TEXT = "本轮反馈尚未生成"

# 仅作答（无反馈）时允许的推荐操作
ANSWER_NEXT_RECOMMENDED_ACTIONS = (
    "answer_again",
    "continue_same_question",
    "generate_reference_answer",
    "generate_next_question",
)

# 反馈生成后允许的推荐操作（多了 explain/expand/next_round 等）
FEEDBACK_NEXT_RECOMMENDED_ACTIONS = (
    "answer_again",
    "continue_same_question",
    "generate_reference_answer",
    "explain_knowledge_point",
    "expand_technical_principle",
    "generate_next_round_suggestion",
    "generate_next_question",
)

# 反馈 payload 中禁止暴露给前端的字段（LLM 原始输入/输出）
FORBIDDEN_FEEDBACK_PAYLOAD_RESPONSE_KEYS = frozenset(
    {
        "prompt",
        "raw_prompt",
        "system_prompt",
        "completion",
        "raw_completion",
        "provider_payload",
        "raw_provider_payload",
        "provider_response",
        "raw_provider_response",
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
    # 创建新打磨会话：绑定简历-岗位关系，指定主题/子主题/自定义主题文本，同步初始化进度树
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

# 异步创建出题任务（LLM 异步生成），返回 ai_task 状态，前端轮询
@router.post("/polish-sessions/{session_id}/questions", status_code=202)
async def create_polish_question_task(
    session_id: str,
    payload: CreateQuestionTaskRequest,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
    llm_transport: LlmTransport = Depends(get_llm_transport),
) -> Any:
    use_cases = _use_cases(session_factory, llm_transport)
    result = await run_in_threadpool(
        use_cases.create_question_task,
        CreatePolishQuestionTaskCommand(
            owner_id=actor.owner_id,
            actor_id=actor.actor_id,
            session_id=session_id,
            progress_node_ref=payload.progress_node_ref,
            generation_mode=payload.generation_mode,
            selected_primary_category_ref=payload.selected_primary_category_ref,
            selected_secondary_category_ref=payload.selected_secondary_category_ref,
            selected_progress_node_ref=payload.selected_progress_node_ref,
            selected_category_path=tuple(payload.selected_category_path),
            parent_question_id=payload.parent_question_id,
            parent_answer_id=payload.parent_answer_id,
            parent_feedback_id=payload.parent_feedback_id,
            exclude_question_refs=tuple(payload.exclude_question_refs),
            completed_focus_refs=tuple(payload.completed_focus_refs),
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
    )
    if clean_idempotency_key is not None:
        object.__setattr__(command, "idempotency_key", clean_idempotency_key)
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
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
    llm_transport: LlmTransport = Depends(get_llm_transport),
) -> Any:
    use_cases = _use_cases(session_factory, llm_transport)
    result = await run_in_threadpool(
        use_cases.create_feedback_task,
        CreatePolishFeedbackTaskCommand(
            owner_id=actor.owner_id,
            actor_id=actor.actor_id,
            session_id=session_id,
            answer_id=payload.answer_id,
        ),
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


# ── 进度树刷新端点 ──────────────────────────────────────────────────
# 刷新进度树状态：若已有 LLM 可刷新的 plan 则走 LLM，否则走规则刷新
@router.post("/polish-sessions/{session_id}/progress-tree/state")
async def refresh_polish_progress_tree_state(
    session_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
    llm_transport: LlmTransport = Depends(get_llm_transport),
) -> Any:
    use_cases = _use_cases(session_factory, llm_transport)
    detail_result = use_cases.get_session(GetPolishSessionQuery(owner_id=actor.owner_id, session_id=session_id))
    if not detail_result.is_success:
        _raise_result_error(detail_result.error)
    detail = detail_result.value

    if _has_refreshable_progress_tree_plan(detail.progress_tree_plan):
        progress_tree_service = PolishProgressTreeLlmService(llm_transport)
        progress_artifacts = await run_in_threadpool(
            progress_tree_service.refresh_state,
            context=_progress_context_with_turn_refs(detail),
            existing_plan=detail.progress_tree_plan,
            existing_state=detail.progress_tree_state,
        )
        updated_session = replace(
            detail.session,
            updated_at=utc_now(),
            progress_tree_status=progress_artifacts["status"],
            progress_percent=progress_artifacts["progress_percent"],
            progress_tree_plan=progress_artifacts["progress_tree_plan"],
            progress_tree_state=progress_artifacts["progress_tree_state"],
        )
        SqlAlchemyPolishRepository(session_factory).update_progress_tree(updated_session)
        refreshed_result = use_cases.get_session(GetPolishSessionQuery(owner_id=actor.owner_id, session_id=session_id))
        if not refreshed_result.is_success:
            _raise_result_error(refreshed_result.error)
        return success_envelope(
            resource_type="polish_session",
            data=_session_response(refreshed_result.value),
        )

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


# ── 辅助函数：获取 UseCases ─────────────────────────────────────────

def _use_cases(session_factory: sessionmaker[Session], llm_transport: LlmTransport) -> PolishUseCases:
    return PolishUseCases(
        polish_repository=SqlAlchemyPolishRepository(session_factory),
        binding_repository=SqlAlchemyBindingRepository(session_factory),
        resume_repository=SqlAlchemyResumeRepository(session_factory),
        job_repository=SqlAlchemyJobRepository(session_factory),
        job_match_repository=SqlAlchemyJobMatchAnalysisRepository(session_factory),
        candidate_repository=SqlAlchemyPolishCandidateRepository(session_factory),
        progress_tree_service=PolishProgressTreeLlmService(llm_transport),
        llm_transport=llm_transport,
    )


# ── 辅助函数：进度树 LLM 刷新 ──────────────────────────────────────

def _has_refreshable_progress_tree_plan(plan: dict[str, Any]) -> bool:
    return plan.get("status") == "ready" and bool(plan.get("nodes"))


# ── 辅助函数：进度树上下文构建 ─────────────────────────────────────

def _progress_context_with_turn_refs(detail: PolishSessionDetail) -> dict[str, Any]:
    context = {**detail.progress_context}
    context["turns"] = [
        _turn_progress_context(turn_index=index, turn=turn)
        for index, turn in enumerate(detail.turns, start=1)
    ]
    return context


# 构建单个轮次的进度上下文（包含该轮所有答案和反馈的快照）
def _turn_progress_context(*, turn_index: int, turn: Any) -> dict[str, Any]:
    latest_answer = turn.answers[-1] if turn.answers else None
    return {
        "turn_index": turn_index,
        "question_id": turn.question_id,
        "question_text": turn.question_text,
        "created_at": _to_iso_string(turn.question_created_at),
        "progress_node_ref": turn.progress_node_ref,
        "evidence_refs": list(turn.evidence_refs),
        "context_digest": turn.context_digest,
        "answer_text": latest_answer.answer_text if latest_answer is not None else None,
        "feedback_text": latest_answer.feedback_text if latest_answer is not None else None,
        "feedback_id": latest_answer.feedback_id if latest_answer is not None else None,
        "score_result_id": latest_answer.score_result_id if latest_answer is not None else None,
        "answer_round": latest_answer.answer_round if latest_answer is not None else None,
        "feedback_created_at": (
            _to_iso_string(latest_answer.feedback_created_at) if latest_answer is not None else None
        ),
        "answers": [
            {
                "answer_id": answer.answer_id,
                "answer_text": answer.answer_text,
                "answer_round": answer.answer_round,
                "created_at": _to_iso_string(answer.answer_created_at),
                "feedback_text": answer.feedback_text,
                "feedback_id": answer.feedback_id,
                "score_result_id": answer.score_result_id,
                "feedback_created_at": _to_iso_string(answer.feedback_created_at),
            }
            for answer in turn.answers
        ],
    }


# ── 辅助函数：格式化 ────────────────────────────────────────────────

def _to_iso_string(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


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
    return {
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


# ── 核心：反馈 payload 构造（兼容 Legacy + 安全脱敏） ───────────────
# 返回前端可见的反馈 JSON，包含评分、失分点、知识/技术建议、trace 等
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
        return _response_safe_feedback_payload(stored_payload)
    feedback_text = _legacy_feedback_text(getattr(answer, "feedback_text", None))
    if not feedback_id:
        return {
            "contract_id": "P-POLISH-003",
            "contract_ids": ["P-POLISH-003"],
            "status": "pending",
            "polish_session_ref": {"resource_type": "polish_session", "resource_id": answer_session_id},
            "question_ref": {"resource_type": "question", "resource_id": answer_question_id},
            "answer_ref": {"resource_type": "answer", "resource_id": answer_id},
            "feedback_text": LEGACY_PENDING_FEEDBACK_TEXT,
            "feedback_summary": LEGACY_PENDING_FEEDBACK_TEXT,
            "score_result": None,
            "score_result_ref": None,
            "loss_points": [],
            "reference_answer": None,
            "knowledge_points": [],
            "technical_principles": [],
            "next_recommended_actions": list(ANSWER_NEXT_RECOMMENDED_ACTIONS),
            "candidate_refs": [],
            "validation_result_ref": None,
            "trace_refs": _answer_trace_refs(answer),
            "low_confidence_flags": [],
            "user_confirmation_required": False,
            "legacy_compatibility": {"feedback_text": LEGACY_PENDING_FEEDBACK_TEXT},
        }

    score_result_id = getattr(answer, "score_result_id", None) or f"{feedback_id}_score"
    answer_text = str(getattr(answer, "answer_text", ""))
    low_confidence_flags = _feedback_low_confidence_flags(answer_text)
    score_value = 58 if low_confidence_flags else 72
    trace_refs = _feedback_trace_refs(answer, score_result_id=score_result_id)
    return {
        "schema_id": "polish_feedback_payload_v1",
        "schema_version": "1.0",
        "contract_id": "P-POLISH-005",
        "contract_ids": ["P-POLISH-003", "P-POLISH-004", "P-POLISH-005", "P-POLISH-009"],
        "status": "generated",
        "feedback_id": feedback_id,
        "polish_session_ref": {"resource_type": "polish_session", "resource_id": answer_session_id},
        "question_ref": {"resource_type": "question", "resource_id": answer_question_id},
        "answer_ref": {"resource_type": "answer", "resource_id": answer_id},
        "feedback_text": feedback_text,
        "feedback_summary": feedback_text,
        "score_result": {
            "score_result_id": score_result_id,
            "score_type": "polish_answer",
            "score_value": score_value,
            "score_version": "polish_answer.runtime_fake.v1",
            "rubric_version": "polish_round_score.v1",
            "contract_id": "P-POLISH-004",
            "confidence_level": "low" if low_confidence_flags else "medium",
        },
        "score_result_ref": {"resource_type": "score_result", "resource_id": score_result_id},
        "loss_points": _feedback_loss_points(feedback_id=str(feedback_id), answer_id=answer_id, answer_text=answer_text, score_value=score_value),
        "reference_answer": {
            "contract_id": "P-POLISH-006",
            "summary": "先交代业务背景和目标，再说明本人负责的关键模块、技术取舍、异常处理和最终指标。",
            "outline": ["背景与约束", "本人负责范围", "关键技术方案与取舍", "验证结果与复盘"],
        },
        "knowledge_points": [
            {
                "title": "STAR + 技术决策链路",
                "explanation": "回答项目经历时需要同时覆盖场景、任务、行动、结果和技术取舍。",
            }
        ],
        "technical_principles": [
            {
                "title": "可观测结果优先",
                "explanation": "技术方案表达应绑定指标、日志、告警、压测或线上结果，避免停留在名词罗列。",
            }
        ],
        "next_recommended_actions": _feedback_next_actions(
            "provide_more_answer_detail" if low_confidence_flags else "continue_same_question"
        ),
        "candidate_refs": [
            {"resource_type": "weakness_candidate", "resource_id": f"{feedback_id}_weakness_001"},
            {"resource_type": "asset_candidate", "resource_id": f"{feedback_id}_asset_001"},
        ],
        "validation_result_ref": {"resource_type": "validation_result", "resource_id": f"{feedback_id}_validation"},
        "trace_refs": trace_refs,
        "low_confidence_flags": low_confidence_flags,
        "user_confirmation_required": False,
        "legacy_compatibility": {"feedback_text": feedback_text},
    }


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
    }
)
FORBIDDEN_FEEDBACK_PAYLOAD_RESPONSE_VALUE_MARKERS = (
    "raw_prompt",
    "system_prompt",
    "raw_completion",
    "completion",
    "provider_payload",
    "raw_provider_payload",
    "provider_response",
    "raw_provider_response",
    "hidden_rubric",
    "full_evidence_text",
    "full_resume",
    "full_resume_markdown",
    "full_jd",
    "full_jd_text",
)
FORBIDDEN_FEEDBACK_PAYLOAD_RESPONSE_ASSIGNMENT_PATTERNS = (
    re.compile(r"api[_-]?key\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"cookie\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"token\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"secret\s*=\s*[^\s,;，；]+", re.IGNORECASE),
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
def _drop_forbidden_feedback_payload_response_keys(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _drop_forbidden_feedback_payload_response_keys(item)
            for key, item in value.items()
            if not _is_forbidden_feedback_payload_response_key(str(key))
        }
    if isinstance(value, list):
        return [_drop_forbidden_feedback_payload_response_keys(item) for item in value]
    if isinstance(value, tuple):
        return [_drop_forbidden_feedback_payload_response_keys(item) for item in value]
    if isinstance(value, str):
        return _redact_forbidden_feedback_payload_response_text(value)
    return value


# ── 反馈评分模拟 ────────────────────────────────────────────────────

# 构造失分点列表（基于 score_value 模拟扣分分配）
def _feedback_loss_points(*, feedback_id: str, answer_id: str, answer_text: str, score_value: int) -> list[dict[str, object]]:
    deducted_points = 100 - score_value
    return [
        {
            "loss_point_id": f"{feedback_id}_loss_001",
            "title": "结构化举证不足",
            "deducted_points": min(16, deducted_points),
            "reason": "回答需要补充场景、个人职责、关键约束和可验证结果之间的因果链路。",
            "answer_excerpt": answer_text[:160],
            "related_answer_ref": {"resource_type": "answer", "resource_id": answer_id},
        },
        {
            "loss_point_id": f"{feedback_id}_loss_002",
            "title": "技术取舍与边界说明不足",
            "deducted_points": max(deducted_points - 16, 0),
            "reason": "建议说明替代方案、失败路径、指标或风险处理，而不是只陈述做了什么。",
            "related_answer_ref": {"resource_type": "answer", "resource_id": answer_id},
        },
    ]


# 合并主操作和全部推荐操作，去重后返回
def _feedback_next_actions(primary_action: str) -> list[str]:
    actions: list[str] = []
    for action in (primary_action, *FEEDBACK_NEXT_RECOMMENDED_ACTIONS):
        if action not in actions:
            actions.append(action)
    return actions


# 根据回答文本长度判断低置信度标记（18字阈值）
def _feedback_low_confidence_flags(answer_text: str) -> list[dict[str, str]]:
    if len(answer_text.strip()) >= 18:
        return []
    return [
        {
            "flag_id": "answer_detail_insufficient",
            "reason": "answer_too_short_for_full_scoring",
            "impact_scope": "score_result, loss_points, reference_answer",
            "recommended_action": "provide_more_answer_detail",
        }
    ]


# 兼容 Legacy：feedback_text 为空时返回"本轮反馈尚未生成"
def _legacy_feedback_text(value: object) -> str:
    text = str(value or "").strip()
    return text or LEGACY_PENDING_FEEDBACK_TEXT


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


# 构造反馈的 trace 引用（含答案 + feedback + score_result 三级）
def _feedback_trace_refs(answer: object, *, score_result_id: str) -> list[dict[str, object]]:
    trace_refs = _answer_trace_refs(answer)
    feedback_id = getattr(answer, "feedback_id", None)
    if feedback_id:
        feedback_created_at = getattr(answer, "feedback_created_at", None)
        trace_refs.extend(
            [
                {
                    "trace_ref_id": feedback_id,
                    "trace_type": "feedback",
                    "created_at": feedback_created_at,
                    "redaction_boundary": "none",
                },
                {
                    "trace_ref_id": score_result_id,
                    "trace_type": "score_result",
                    "created_at": feedback_created_at,
                    "redaction_boundary": "none",
                },
            ]
        )
    return trace_refs


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
    }
    if contract_shape is not None:
        payload["contract_shaped_fake"] = contract_shape
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
