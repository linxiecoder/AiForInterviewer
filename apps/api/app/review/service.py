"""R0 复盘摘要服务，基于 score + turns 生成 minimal review。"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from app.interview_flow import InterviewFlowNotFound
from app.interview_flow.contract import (
    DEFAULT_INTERVIEW_MODE,
    FIELD_ANSWER,
    FIELD_CONTENT,
    FIELD_MODE,
    FIELD_QUESTION,
    FIELD_SESSION_ID,
    FIELD_TURNS,
    INTERVIEW_FLOW_RECORD_SOURCE,
    SESSION_STATUS_IN_PROGRESS,
)
from app.interview_record_contract import (
    DEFAULT_RECORD_VERSION,
    FIELD_ID,
    FIELD_PAYLOAD,
    PAYLOAD_INTERVIEW,
    RESPONSE_STATUS,
)
from app.llm.constants import DEFAULT_PROMPT_VERSION, PURPOSE_REVIEW
from app.llm.models import LLMGenerateRequest
from app.llm.providers import LLMProvider
from app.persistence import InterviewRecordStore
from app.scoring import ScoringService

REVIEW_PAYLOAD_KEY = "review"
REVIEW_SUMMARY_KEY = "summary"
REVIEW_STRENGTHS_KEY = "strengths"
REVIEW_RISKS_KEY = "risks"
REVIEW_SUGGESTIONS_KEY = "suggestions"
REVIEW_WEAKNESS_KEY = "weakness"
REVIEW_IMPROVEMENTS_KEY = "improvements"
REVIEW_CONTENT_VERSION_KEY = "content_version"
REVIEW_GENERATED_AT_KEY = "generated_at"
REVIEW_METADATA_KEY = "metadata"

REVIEW_CONTENT_VERSION = "r0-review-v1"


class ReviewService:
    """基于 score 与 turns 生成 minimal review summary 与改进建议。"""

    def __init__(
        self,
        *,
        store: InterviewRecordStore,
        provider: LLMProvider | None = None,
        scoring_service: ScoringService | None = None,
    ) -> None:
        self.store = store
        self.provider = provider
        self.scoring_service = scoring_service or ScoringService(store=store, provider=provider)

    def generate_review(
        self,
        *,
        owner_id: str,
        session_id: str,
        use_provider: bool = False,
        persist: bool = True,
    ) -> dict[str, Any]:
        """生成 review payload，默认 deterministic。"""
        record, interview, turns = _get_session_context(
            store=self.store,
            owner_id=owner_id,
            session_id=session_id,
        )

        score_payload = (
            _review_score_from_payload(payload=record[FIELD_PAYLOAD])
            if _review_score_from_payload(payload=record[FIELD_PAYLOAD]) is not None
            else self.scoring_service.generate_score(
                owner_id=owner_id,
                session_id=session_id,
                use_provider=use_provider,
                persist=False,
            )["score"]
        )
        if not isinstance(score_payload, Mapping):
            score_payload = {}

        provider_comment: str | None = None
        if use_provider and self.provider is not None:
            provider_request = LLMGenerateRequest(
                purpose=PURPOSE_REVIEW,
                job=dict(_payload_field(interview, "job")),
                resume=dict(_payload_field(interview, "resume")),
                history=_history_payload(turns=turns),
                last_answer=None,
                metadata={
                    "mode": str(_payload_field(interview, FIELD_MODE) or DEFAULT_INTERVIEW_MODE),
                    "session_id": session_id,
                },
                request_id=f"review-{_short_id()}",
                session_id=session_id,
                turn_index=max(len(turns) - 1, 0),
                prompt_version=DEFAULT_PROMPT_VERSION,
            )
            provider_comment = self.provider.generate(provider_request).content

        review_payload = build_review_payload(
            score_payload=score_payload,
            interview=interview,
            turns=turns,
            provider_comment=provider_comment,
        )

        payload = deepcopy(record[FIELD_PAYLOAD])
        payload[REVIEW_PAYLOAD_KEY] = review_payload
        payload["score"] = score_payload

        if persist:
            record = self.store.create_record(
                owner_id=owner_id,
                source=INTERVIEW_FLOW_RECORD_SOURCE,
                version=DEFAULT_RECORD_VERSION,
                payload=payload,
            )

        return {
            "record_id": record[FIELD_ID],
            "owner_id": owner_id,
            "session_id": str(interview.get(FIELD_SESSION_ID, session_id)),
            "score": score_payload,
            REVIEW_PAYLOAD_KEY: review_payload,
        }


def build_review_payload(
    *,
    score_payload: Mapping[str, Any],
    interview: Mapping[str, Any],
    turns: list[Mapping[str, Any]],
    provider_comment: str | None = None,
) -> dict[str, Any]:
    """基于分数与回答情况构建最小 review payload。"""
    score_value = _clamp_int(score_payload.get("value", 0), 0, 100)
    answered_count = len([turn for turn in turns if _has_answer(turn)])
    total_count = max(len(turns), 1)

    if score_value >= 80:
        summary = "表现良好，已覆盖主要题目并给出较完整答案。"
        strengths = ["回答节奏稳定，问题切入清晰。"]
    elif score_value >= 60:
        summary = "表现中等，具备基本思路，但仍可补齐细节。"
        strengths = ["问题已逐步响应，表达有一定完整度。"]
    else:
        summary = "表现偏弱，需在结构化表达与案例细节上补强。"
        strengths = ["已建立完整作答流程，可继续完善。"]

    risks = []
    if answered_count < total_count:
        risks.append("存在未回答或内容不足问题。")
    if score_value < 70:
        risks.append("部分回答缺乏决策依据或结果指标。")
    if not risks:
        risks.append("当前暂无明显阻塞项。")

    weaknesses: list[str] = []
    improvements: list[str] = []
    for index, turn in enumerate(turns, start=1):
        answer_text = _answer_content(turn)
        if not answer_text.strip():
            weaknesses.append(f"问题 {index} 尚未形成可复用回答。")
            improvements.append(f"问题 {index} 需要补充作答框架与关键点。")
        elif len(answer_text.strip()) < 24:
            weaknesses.append(f"问题 {index} 回答较短。")
            improvements.append(f"问题 {index} 需要补充场景、结果和权衡。")

    if not weaknesses:
        weaknesses.append("未发现明显薄弱项。")
    if not improvements:
        improvements.append("继续保持当前深度，并保持结构化表达。")

    suggestions = [
        "每题补齐动作、过程、结果三个维度。",
        "对关键问题给出可量化结果。",
        "将 weak point 落到可执行的下一步计划。",
    ]

    return {
        REVIEW_SUMMARY_KEY: summary,
        REVIEW_STRENGTHS_KEY: strengths,
        REVIEW_RISKS_KEY: risks[:3],
        REVIEW_SUGGESTIONS_KEY: suggestions,
        REVIEW_WEAKNESS_KEY: weaknesses[:3],
        REVIEW_IMPROVEMENTS_KEY: improvements[:3],
        REVIEW_CONTENT_VERSION_KEY: REVIEW_CONTENT_VERSION,
        REVIEW_GENERATED_AT_KEY: _utc_now(),
        REVIEW_METADATA_KEY: {
            "session_id": str(interview.get(FIELD_SESSION_ID, "")),
            "owner_id": str(interview.get("metadata", {}).get("owner_id", "")),
            "score": score_value,
            "answered_count": answered_count,
            "total_count": total_count,
            "provider_comment": provider_comment,
            "status": str(interview.get(RESPONSE_STATUS, SESSION_STATUS_IN_PROGRESS)),
        },
    }


def _history_payload(turns: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """将 turn 历史转换成 provider 可读摘要。"""
    history: list[dict[str, Any]] = []
    for turn in turns:
        answer = turn.get(FIELD_ANSWER) if isinstance(turn, Mapping) else {}
        answer_text = answer.get(FIELD_CONTENT) if isinstance(answer, Mapping) else None
        history.append(
            {
                "question": str(turn.get(FIELD_QUESTION, "")) if isinstance(turn, Mapping) else "",
                "answer": answer_text if isinstance(answer_text, str) else "",
            }
        )
    return history


def _has_answer(turn: Mapping[str, Any]) -> bool:
    """判断 turn 是否有有效答案。"""
    answer = turn.get(FIELD_ANSWER)
    if not isinstance(answer, Mapping):
        return False
    content = answer.get(FIELD_CONTENT)
    return isinstance(content, str) and bool(content.strip())


def _answer_content(turn: Mapping[str, Any]) -> str:
    """取出 turn 的 answer 文本。"""
    answer = turn.get(FIELD_ANSWER)
    if not isinstance(answer, Mapping):
        return ""
    content = answer.get(FIELD_CONTENT)
    return content if isinstance(content, str) else ""


def _payload_field(interview: Mapping[str, Any], field: str) -> Mapping[str, Any] | Any:
    return interview.get(field, {})


def _get_session_context(
    *,
    store: InterviewRecordStore,
    owner_id: str,
    session_id: str,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    """按 owner + session_id 获取最新 session 记录。"""
    record = _latest_session_record(store=store, owner_id=owner_id, session_id=session_id)
    if record is None:
        raise InterviewFlowNotFound("INTERVIEW_SESSION_NOT_FOUND")

    payload = record[FIELD_PAYLOAD]
    interview = payload.get(PAYLOAD_INTERVIEW)
    interview = interview if isinstance(interview, Mapping) else {}
    turns = interview.get(FIELD_TURNS, [])
    turns = [dict(turn) for turn in turns] if isinstance(turns, list) else []
    return record, dict(interview), turns


def _latest_session_record(
    *,
    store: InterviewRecordStore,
    owner_id: str,
    session_id: str,
) -> dict[str, Any] | None:
    """按 owner + session 找到 snapshot 最新记录。"""
    latest: tuple[int, dict[str, Any]] | None = None
    for summary in store.list_records(owner_id=owner_id):
        record = store.get_record(summary[FIELD_ID])
        if record is None:
            continue
        payload = record.get(FIELD_PAYLOAD)
        interview = payload.get(PAYLOAD_INTERVIEW) if isinstance(payload, Mapping) else None
        if not isinstance(interview, Mapping):
            continue
        if str(interview.get(FIELD_SESSION_ID)) != session_id:
            continue
        snapshot_index = interview.get("snapshot_index")
        index = snapshot_index if isinstance(snapshot_index, int) else 0
        if latest is None or index > latest[0]:
            latest = (index, record)
    return latest[1] if latest is not None else None


def _review_score_from_payload(*, payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """从 session payload 读取已有 score，缺失则返回 None。"""
    score = payload.get("score")
    return score if isinstance(score, Mapping) else None


def _clamp_int(value: Any, min_value: int, max_value: int) -> int:
    """将数值限制在闭区间。"""
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        return min_value
    return max(min_value, min(max_value, normalized))


def _short_id() -> str:
    """给 provider request 生成可读短 id。"""
    from uuid import uuid4

    return uuid4().hex[:12]


def _utc_now() -> str:
    """返回统一时间戳，便于 trace 与测试。"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
