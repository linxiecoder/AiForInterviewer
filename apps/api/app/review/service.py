"""R1 可信复盘服务，基于多维 score + trace evidence 生成 review。"""

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
    FIELD_SNAPSHOT_INDEX,
    FIELD_TRACE_SUMMARY,
    FIELD_TURN_ID,
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
from app.persistence import InterviewRecordStore, TraceabilityStore
from app.scoring import ScoringService
from app.traceability import (
    TRACE_TYPE_REVIEW_EXPORT,
    TraceabilityRecord,
    TraceabilityStatus,
    build_trace_summary,
)

REVIEW_PAYLOAD_KEY = "review"
REVIEW_SUMMARY_KEY = "summary"
REVIEW_SCORE_TOTAL_KEY = "score_total"
REVIEW_DIMENSIONS_KEY = "dimensions"
REVIEW_STRENGTHS_KEY = "strengths"
REVIEW_RISKS_KEY = "risks"
REVIEW_SUGGESTIONS_KEY = "suggestions"
REVIEW_WEAKNESS_KEY = "weakness"
REVIEW_WEAK_AREAS_KEY = "weak_areas"
REVIEW_IMPROVEMENTS_KEY = "improvements"
REVIEW_CITATION_REFS_KEY = "citation_refs"
REVIEW_EVIDENCE_REFS_KEY = "evidence_refs"
REVIEW_EVIDENCE_GAP_REFS_KEY = "evidence_gap_refs"
REVIEW_LOW_CONFIDENCE_KEY = "low_confidence"
REVIEW_LOW_CONFIDENCE_REASON_KEY = "low_confidence_reason"
REVIEW_STATUS_KEY = "status"
REVIEW_DEGRADED_KEY = "degraded"
REVIEW_RETRYABLE_KEY = "retryable"
REVIEW_REVIEW_SUMMARY_KEY = "review_summary"
REVIEW_CONTENT_VERSION_KEY = "content_version"
REVIEW_GENERATED_AT_KEY = "generated_at"
REVIEW_METADATA_KEY = "metadata"

REVIEW_CONTENT_VERSION = "r1-review-v1"
REVIEW_STATUS_GENERATED = "generated"
REVIEW_STATUS_DEGRADED = "degraded"


class ReviewService:
    """基于 score 与 turns 生成 minimal review summary 与改进建议。"""

    def __init__(
        self,
        *,
        store: InterviewRecordStore,
        provider: LLMProvider | None = None,
        scoring_service: ScoringService | None = None,
        trace_store: TraceabilityStore | None = None,
    ) -> None:
        self.store = store
        self.provider = provider
        self.trace_store = trace_store
        self.scoring_service = scoring_service or ScoringService(
            store=store,
            provider=provider,
            trace_store=trace_store,
        )

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
        _bump_snapshot_index(payload)

        if persist:
            record = self.store.create_record(
                owner_id=owner_id,
                source=INTERVIEW_FLOW_RECORD_SOURCE,
                version=DEFAULT_RECORD_VERSION,
                payload=payload,
            )

        self._record_trace(
            TraceabilityRecord(
                owner_id=owner_id,
                trace_type=TRACE_TYPE_REVIEW_EXPORT,
                status=(
                    TraceabilityStatus.DEGRADED
                    if review_payload[REVIEW_STATUS_KEY] == REVIEW_STATUS_DEGRADED
                    else TraceabilityStatus.COMPLETED
                ),
                request_id=f"review-{_short_id()}",
                operation_id="review.generate",
                session_ref=str(interview.get(FIELD_SESSION_ID, session_id)),
                answer_ref=_latest_answer_ref(turns),
                score_ref=f"score:{session_id}:{score_payload.get('content_version', '')}",
                review_ref=f"review:{session_id}:{REVIEW_CONTENT_VERSION}",
                citation_refs=tuple(review_payload[REVIEW_CITATION_REFS_KEY]),
                evidence_refs=tuple(review_payload[REVIEW_EVIDENCE_REFS_KEY]),
                evidence_gap_ref=_first_or_none(review_payload[REVIEW_EVIDENCE_GAP_REFS_KEY]),
                source_snapshot_ref=f"{record[FIELD_ID]}:review",
                content_version=REVIEW_CONTENT_VERSION,
                retryable=bool(review_payload[REVIEW_RETRYABLE_KEY]),
                metadata={
                    "operation": "review.generate",
                    "record_id": record[FIELD_ID],
                    "review_version": REVIEW_CONTENT_VERSION,
                    "status": review_payload[REVIEW_STATUS_KEY],
                },
            )
        )
        return {
            "record_id": record[FIELD_ID],
            "owner_id": owner_id,
            "session_id": str(interview.get(FIELD_SESSION_ID, session_id)),
            "score": score_payload,
            REVIEW_PAYLOAD_KEY: review_payload,
            FIELD_TRACE_SUMMARY: _trace_summary(
                trace_store=self.trace_store,
                owner_id=owner_id,
                session_id=session_id,
            ),
        }

    def _record_trace(self, record: TraceabilityRecord) -> None:
        if self.trace_store is not None:
            self.trace_store.create_trace(record)


def build_review_payload(
    *,
    score_payload: Mapping[str, Any],
    interview: Mapping[str, Any],
    turns: list[Mapping[str, Any]],
    provider_comment: str | None = None,
) -> dict[str, Any]:
    """基于分数与回答情况构建最小 review payload。"""
    score_value = _score_total(score_payload)
    answered_count = len([turn for turn in turns if _has_answer(turn)])
    total_count = max(len(turns), 1)
    dimensions = _list_of_mappings(score_payload.get("dimensions"))
    citation_refs = _string_list(score_payload.get("citation_refs"))
    evidence_refs = _string_list(score_payload.get("evidence_refs"))
    evidence_gap_refs = _string_list(score_payload.get("evidence_gap_refs"))
    low_confidence = bool(score_payload.get("low_confidence")) or bool(evidence_gap_refs)
    low_confidence_reason = str(score_payload.get("low_confidence_reason", "")).strip()
    status = REVIEW_STATUS_DEGRADED if low_confidence else REVIEW_STATUS_GENERATED

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

    suggestions = _string_list(score_payload.get("suggestions")) or [
        "每题补齐动作、过程、结果三个维度。",
        "对关键问题给出可量化结果。",
        "将 weak point 落到可执行的下一步计划。",
    ]
    weak_areas = _string_list(score_payload.get("weak_areas")) or weaknesses[:3]
    if evidence_gap_refs and "补充证据链以降低复盘不确定性。" not in suggestions:
        suggestions.append("补充证据链以降低复盘不确定性。")
    review_summary = _review_summary(
        summary=summary,
        low_confidence=low_confidence,
        low_confidence_reason=low_confidence_reason,
    )

    return {
        REVIEW_SUMMARY_KEY: summary,
        REVIEW_REVIEW_SUMMARY_KEY: review_summary,
        REVIEW_SCORE_TOTAL_KEY: score_value,
        REVIEW_DIMENSIONS_KEY: dimensions,
        REVIEW_STRENGTHS_KEY: strengths,
        REVIEW_RISKS_KEY: risks[:3],
        REVIEW_SUGGESTIONS_KEY: suggestions,
        REVIEW_WEAKNESS_KEY: weaknesses[:3],
        REVIEW_WEAK_AREAS_KEY: weak_areas[:3],
        REVIEW_IMPROVEMENTS_KEY: improvements[:3],
        REVIEW_CITATION_REFS_KEY: citation_refs,
        REVIEW_EVIDENCE_REFS_KEY: evidence_refs,
        REVIEW_EVIDENCE_GAP_REFS_KEY: evidence_gap_refs,
        REVIEW_LOW_CONFIDENCE_KEY: low_confidence,
        REVIEW_LOW_CONFIDENCE_REASON_KEY: low_confidence_reason,
        REVIEW_STATUS_KEY: status,
        REVIEW_DEGRADED_KEY: status == REVIEW_STATUS_DEGRADED,
        REVIEW_RETRYABLE_KEY: False,
        REVIEW_CONTENT_VERSION_KEY: REVIEW_CONTENT_VERSION,
        REVIEW_GENERATED_AT_KEY: _utc_now(),
        REVIEW_METADATA_KEY: {
            "session_id": str(interview.get(FIELD_SESSION_ID, "")),
            "owner_id": str(interview.get("metadata", {}).get("owner_id", "")),
            "score": score_value,
            "answered_count": answered_count,
            "total_count": total_count,
            "provider_comment_present": bool(provider_comment),
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


def _latest_answer_ref(turns: list[Mapping[str, Any]]) -> str | None:
    for turn in reversed(turns):
        answer = turn.get(FIELD_ANSWER) if isinstance(turn, Mapping) else {}
        if isinstance(answer, Mapping) and answer.get(FIELD_CONTENT):
            return f"answer:{turn.get(FIELD_TURN_ID, '')}"
    return None


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


def _bump_snapshot_index(payload: dict[str, Any]) -> None:
    interview = payload.get(PAYLOAD_INTERVIEW)
    if not isinstance(interview, dict):
        return
    current = interview.get(FIELD_SNAPSHOT_INDEX)
    interview[FIELD_SNAPSHOT_INDEX] = current + 1 if isinstance(current, int) else 1


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


def _score_total(score_payload: Mapping[str, Any]) -> int:
    value = score_payload.get("score_total", score_payload.get("value", 0))
    return _clamp_int(value, 0, 100)


def _review_summary(
    *,
    summary: str,
    low_confidence: bool,
    low_confidence_reason: str,
) -> str:
    if not low_confidence:
        return summary
    reason = low_confidence_reason or "证据链不足"
    return f"{summary} 由于{reason}，本次复盘标记为低置信度。"


def _trace_summary(
    *,
    trace_store: TraceabilityStore | None,
    owner_id: str,
    session_id: str,
) -> dict[str, Any]:
    if trace_store is None:
        return build_trace_summary(())
    return build_trace_summary(trace_store.list_traces(owner_id=owner_id, session_ref=session_id))


def _list_of_mappings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = str(item).strip() if item is not None else ""
        if text and text not in result:
            result.append(text)
    return result


def _first_or_none(values: Any) -> str | None:
    items = _string_list(values)
    return items[0] if items else None


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
