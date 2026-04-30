"""R0 模拟面试主链路、评分、复盘与 Markdown 导出 API。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.interview_flow import InterviewFlowNotFound, InterviewFlowService
from app.interview_flow.contract import (
    ANSWER_ROUTE,
    DEFAULT_INTERVIEW_MODE,
    FIELD_SESSION_ID,
    INTERVIEWS_ROUTE_PREFIX,
    SESSION_ROUTE,
)
from app.export import ExportService
from app.llm import LLMProviderError, build_llm_provider
from app.review import ReviewService
from app.scoring import ScoringService

REVIEW_ROUTE = "/{session_id}/review"
EXPORT_ROUTE = "/{session_id}/export"

router = APIRouter(prefix=INTERVIEWS_ROUTE_PREFIX, tags=["interviews"])


class StartInterviewRequest(BaseModel):
    """启动 R0 面试所需的最小输入。"""

    owner_id: str = Field(..., min_length=1)
    job: dict[str, Any] = Field(default_factory=dict)
    resume: dict[str, Any] = Field(default_factory=dict)
    mode: str = Field(default=DEFAULT_INTERVIEW_MODE, min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SubmitAnswerRequest(BaseModel):
    """提交单轮回答所需的最小输入。"""

    owner_id: str = Field(..., min_length=1)
    turn_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewRequest(BaseModel):
    """复盘生成请求。"""

    owner_id: str = Field(..., min_length=1)
    use_provider: bool = Field(default=False)
    persist: bool = Field(default=True)


class ExportRequest(BaseModel):
    """Markdown 导出请求。"""

    owner_id: str = Field(..., min_length=1)
    persist: bool = Field(default=True)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=None)
async def start_interview(request: Request, body: StartInterviewRequest) -> Any:
    """创建 session，并通过 ST13_11 provider 生成首题。"""
    try:
        return _service(request, require_provider=True).start_interview(
            owner_id=body.owner_id,
            job=body.job,
            resume=body.resume,
            mode=body.mode,
            metadata=body.metadata,
        )
    except LLMProviderError as exc:
        return _provider_error_response(exc)


@router.post(ANSWER_ROUTE, response_model=None)
async def submit_answer(
    request: Request,
    session_id: str,
    body: SubmitAnswerRequest,
) -> Any:
    """保存回答，并生成下一轮最小 follow-up。"""
    try:
        return _service(request, require_provider=True).submit_answer(
            owner_id=body.owner_id,
            session_id=session_id,
            turn_id=body.turn_id,
            content=body.content,
            metadata=body.metadata,
        )
    except InterviewFlowNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except LLMProviderError as exc:
        return _provider_error_response(exc)


@router.post(REVIEW_ROUTE)
async def generate_review(
    request: Request,
    session_id: str,
    body: ReviewRequest,
) -> dict[str, Any]:
    """为已存在 session 生成 review summary、weakness 与 improvement。"""
    try:
        return _review_service(
            request,
            use_provider=body.use_provider,
        ).generate_review(
            owner_id=body.owner_id,
            session_id=session_id,
            use_provider=body.use_provider,
            persist=body.persist,
        )
    except InterviewFlowNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except LLMProviderError as exc:
        return _provider_error_response(exc)


@router.post(EXPORT_ROUTE)
@router.get(EXPORT_ROUTE)
async def generate_markdown_export(
    request: Request,
    session_id: str,
    owner_id: str | None = None,
    body: ExportRequest | None = None,
) -> dict[str, Any]:
    """基于 session + score + review 生成 Markdown export payload。"""
    if body is not None and owner_id is None:
        owner_id = body.owner_id
    if owner_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="owner_id is required",
        )

    try:
        return _export_service(request).generate_export(
            owner_id=owner_id,
            session_id=session_id,
            persist=True if body is None else body.persist,
        )
    except InterviewFlowNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


@router.get(SESSION_ROUTE)
async def restore_session(
    request: Request,
    session_id: str,
    owner_id: str = Query(..., min_length=1),
) -> dict[str, Any]:
    """按 owner_id + session_id 恢复最新 session snapshot。"""
    try:
        return _service(request, require_provider=False).restore_session(
            owner_id=owner_id,
            session_id=session_id,
        )
    except InterviewFlowNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


@router.get("")
async def list_history(
    request: Request,
    owner_id: str = Query(..., min_length=1),
) -> dict[str, list[dict[str, Any]]]:
    """返回 owner 范围内的 R0 面试历史摘要。"""
    return _service(request, require_provider=False).list_history(owner_id=owner_id)


def _service(request: Request, *, require_provider: bool) -> InterviewFlowService:
    provider = getattr(request.app.state, "llm_provider", None)
    if require_provider and provider is None:
        provider = build_llm_provider()
        request.app.state.llm_provider = provider
    return InterviewFlowService(
        store=request.app.state.interview_record_store,
        provider=provider,
        trace_store=getattr(request.app.state, "traceability_store", None),
    )


def _scoring_service(request: Request, *, require_provider: bool) -> ScoringService:
    provider = getattr(request.app.state, "llm_provider", None)
    if require_provider and provider is None:
        provider = build_llm_provider()
        request.app.state.llm_provider = provider
    return ScoringService(
        store=request.app.state.interview_record_store,
        provider=provider,
        trace_store=getattr(request.app.state, "traceability_store", None),
    )


def _review_service(request: Request, *, use_provider: bool) -> ReviewService:
    provider = getattr(request.app.state, "llm_provider", None)
    if use_provider and provider is None:
        provider = build_llm_provider()
        request.app.state.llm_provider = provider
    return ReviewService(
        store=request.app.state.interview_record_store,
        provider=provider,
        trace_store=getattr(request.app.state, "traceability_store", None),
    )


def _export_service(request: Request) -> ExportService:
    return ExportService(
        store=request.app.state.interview_record_store,
        trace_store=getattr(request.app.state, "traceability_store", None),
    )


def _provider_error_response(exc: LLMProviderError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content=exc.to_payload())
