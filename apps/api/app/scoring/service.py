"""R1 评分服务，实现 0-100 多维 score 并持久化到 session payload。"""

from __future__ import annotations

import re
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
    FIELD_TURN_ID,
    FIELD_TURNS,
    INTERVIEW_FLOW_RECORD_SOURCE,
    SESSION_STATUS_IN_PROGRESS,
)
from app.interview_record_contract import (
    DEFAULT_RECORD_VERSION,
    FIELD_ID,
    FIELD_PAYLOAD,
    PAYLOAD_INTERVIEW as PAYLOAD_INTERVIEW_KEY,
    RESPONSE_STATUS,
)
from app.llm.constants import DEFAULT_PROMPT_VERSION, PURPOSE_SCORE
from app.llm.models import LLMGenerateRequest
from app.llm.providers import LLMProvider
from app.persistence import InterviewRecordStore, TraceabilityStore
from app.traceability import (
    TRACE_TYPE_REVIEW_EXPORT,
    TraceabilityRecord,
    TraceabilityStatus,
    build_trace_summary,
)

SCORE_PAYLOAD_KEY = "score"
SCORE_VALUE_KEY = "value"
SCORE_TOTAL_KEY = "score_total"
SCORE_DIMENSIONS_KEY = "dimensions"
SCORE_STATUS_KEY = "status"
SCORE_STRATEGY_KEY = "scoring_strategy"
SCORE_CONTENT_VERSION_KEY = "content_version"
SCORE_GENERATED_AT_KEY = "generated_at"
SCORE_EXPLANATION_KEY = "explanation"
SCORE_METADATA_KEY = "metadata"
SCORE_CITATION_REFS_KEY = "citation_refs"
SCORE_EVIDENCE_REFS_KEY = "evidence_refs"
SCORE_EVIDENCE_GAP_REFS_KEY = "evidence_gap_refs"
SCORE_LOW_CONFIDENCE_KEY = "low_confidence"
SCORE_LOW_CONFIDENCE_REASON_KEY = "low_confidence_reason"
SCORE_SUGGESTIONS_KEY = "suggestions"
SCORE_WEAK_AREAS_KEY = "weak_areas"
SCORE_REVIEW_SUMMARY_KEY = "review_summary"

SCORE_MIN = 0
SCORE_MAX = 100
SCORE_CONTENT_VERSION = "r1-score-v1"
SCORE_DETERMINISTIC_STRATEGY = "deterministic"
SCORE_PROVIDER_STRATEGY = "provider_assisted"
SCORE_STATUS_GENERATED = "generated"
SCORE_STATUS_DEGRADED = "degraded"

SCORE_DIMENSION_DEFINITIONS = (
    ("professional_fit", "专业匹配度"),
    ("clarity", "表达清晰度"),
    ("technical_depth", "技术深度"),
    ("role_relevance", "岗位相关性"),
    ("risk_uncertainty", "风险与不确定性"),
)


class ScoringService:
    """按 interview session 计算最小 0-100 score，并可持久化。"""

    def __init__(
        self,
        *,
        store: InterviewRecordStore,
        provider: LLMProvider | None = None,
        trace_store: TraceabilityStore | None = None,
    ) -> None:
        self.store = store
        self.provider = provider
        self.trace_store = trace_store

    def generate_score(
        self,
        *,
        owner_id: str,
        session_id: str,
        use_provider: bool = False,
        persist: bool = True,
    ) -> dict[str, Any]:
        """生成 score，必要时可走 provider 辅助，默认 deterministic。"""
        record, interview, turns = _get_session_context(
            store=self.store,
            owner_id=owner_id,
            session_id=session_id,
        )

        if use_provider and self.provider is not None:
            base_score_payload = _provider_score(
                provider=self.provider,
                interview=interview,
                turns=turns,
                session_id=session_id,
                owner_id=owner_id,
            )
        else:
            base_score_payload = _deterministic_score_payload(turns=turns)

        score_payload = _build_score_payload(
            base_score_payload=base_score_payload,
            interview=interview,
            turns=turns,
            owner_id=owner_id,
            session_id=session_id,
            trace_summary=_trace_summary(
                trace_store=self.trace_store,
                owner_id=owner_id,
                session_id=session_id,
            ),
        )

        payload = deepcopy(record[FIELD_PAYLOAD])
        payload[SCORE_PAYLOAD_KEY] = score_payload
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
                    if score_payload[SCORE_STATUS_KEY] == SCORE_STATUS_DEGRADED
                    else TraceabilityStatus.COMPLETED
                ),
                request_id=f"score-{_short_id()}",
                operation_id="score.generate",
                session_ref=str(interview.get(FIELD_SESSION_ID, session_id)),
                answer_ref=_latest_answer_ref(turns),
                score_ref=f"score:{session_id}:{SCORE_CONTENT_VERSION}",
                citation_refs=tuple(score_payload[SCORE_CITATION_REFS_KEY]),
                evidence_refs=tuple(score_payload[SCORE_EVIDENCE_REFS_KEY]),
                evidence_gap_ref=_first_or_none(score_payload[SCORE_EVIDENCE_GAP_REFS_KEY]),
                source_snapshot_ref=f"{record[FIELD_ID]}:score",
                content_version=SCORE_CONTENT_VERSION,
                retryable=bool(score_payload[SCORE_LOW_CONFIDENCE_KEY]),
                metadata={
                    "operation": "score.generate",
                    "record_id": record[FIELD_ID],
                    "score_total": score_payload[SCORE_TOTAL_KEY],
                    "strategy": score_payload[SCORE_STRATEGY_KEY],
                    "status": score_payload[SCORE_STATUS_KEY],
                },
            )
        )
        return {
            "record_id": record[FIELD_ID],
            "owner_id": owner_id,
            "session_id": str(interview.get(FIELD_SESSION_ID, session_id)),
            "score": score_payload,
        }

    def _record_trace(self, record: TraceabilityRecord) -> None:
        if self.trace_store is not None:
            self.trace_store.create_trace(record)


def _deterministic_score_payload(*, turns: list[dict[str, Any]]) -> dict[str, Any]:
    """用回答覆盖率和长度给出稳定 score，范围 0-100。"""
    answered_count, total_chars = _answer_metrics(turns=turns)
    total_count = len(turns)
    if total_count <= 0:
        value = SCORE_MIN
    else:
        answered_rate = answered_count / total_count
        average_length = total_chars / answered_count if answered_count else 0
        value = round(answered_rate * 70 + min(average_length / 10.0, 3.0) / 3.0 * 30)

    return {
        SCORE_VALUE_KEY: _clamp_score(value),
        SCORE_STRATEGY_KEY: SCORE_DETERMINISTIC_STRATEGY,
        SCORE_METADATA_KEY: {
            "turn_count": total_count,
            "answered_count": answered_count,
        },
    }


def _build_score_payload(
    *,
    base_score_payload: Mapping[str, Any],
    interview: Mapping[str, Any],
    turns: list[dict[str, Any]],
    owner_id: str,
    session_id: str,
    trace_summary: Mapping[str, Any],
) -> dict[str, Any]:
    score_total = _clamp_score(int(base_score_payload[SCORE_VALUE_KEY]))
    evidence = _evidence_context(trace_summary=trace_summary)
    low_confidence_reasons = _low_confidence_reasons(
        turns=turns,
        evidence_gap_refs=evidence["evidence_gap_refs"],
        rag_statuses=evidence["rag_statuses"],
    )
    low_confidence = bool(low_confidence_reasons)
    status = SCORE_STATUS_DEGRADED if low_confidence else SCORE_STATUS_GENERATED
    dimensions = _score_dimensions(
        score_total=score_total,
        turns=turns,
        citation_refs=evidence["citation_refs"],
        evidence_refs=evidence["evidence_refs"],
        evidence_gap_refs=evidence["evidence_gap_refs"],
        low_confidence=low_confidence,
        low_confidence_reason="；".join(low_confidence_reasons),
    )
    suggestions = _score_suggestions(
        score_total=score_total,
        evidence_gap_refs=evidence["evidence_gap_refs"],
    )
    weak_areas = _score_weak_areas(dimensions=dimensions)

    return {
        SCORE_VALUE_KEY: score_total,
        SCORE_TOTAL_KEY: score_total,
        SCORE_DIMENSIONS_KEY: dimensions,
        SCORE_STATUS_KEY: status,
        SCORE_STRATEGY_KEY: base_score_payload[SCORE_STRATEGY_KEY],
        SCORE_CONTENT_VERSION_KEY: SCORE_CONTENT_VERSION,
        SCORE_EXPLANATION_KEY: _score_explanation(score_total),
        SCORE_GENERATED_AT_KEY: _utc_now(),
        SCORE_CITATION_REFS_KEY: evidence["citation_refs"],
        SCORE_EVIDENCE_REFS_KEY: evidence["evidence_refs"],
        SCORE_EVIDENCE_GAP_REFS_KEY: evidence["evidence_gap_refs"],
        SCORE_LOW_CONFIDENCE_KEY: low_confidence,
        SCORE_LOW_CONFIDENCE_REASON_KEY: "；".join(low_confidence_reasons),
        SCORE_SUGGESTIONS_KEY: suggestions,
        SCORE_WEAK_AREAS_KEY: weak_areas,
        SCORE_REVIEW_SUMMARY_KEY: _score_review_summary(
            score_total=score_total,
            low_confidence=low_confidence,
        ),
        SCORE_METADATA_KEY: {
            **dict(base_score_payload.get(SCORE_METADATA_KEY, {})),
            "session_id": str(interview.get(FIELD_SESSION_ID, session_id)),
            "owner_id": owner_id,
            "status": str(interview.get(RESPONSE_STATUS, SESSION_STATUS_IN_PROGRESS)),
            "trace_status": str(trace_summary.get("status", "empty")),
        },
    }


def _evidence_context(*, trace_summary: Mapping[str, Any]) -> dict[str, list[str]]:
    rag = trace_summary.get("rag")
    rag = rag if isinstance(rag, Mapping) else {}
    return {
        "citation_refs": _string_list(rag.get("citation_refs")),
        "evidence_refs": _string_list(rag.get("evidence_refs")),
        "evidence_gap_refs": _string_list(rag.get("evidence_gap_refs")),
        "rag_statuses": _string_list(rag.get("statuses")),
    }


def _low_confidence_reasons(
    *,
    turns: list[dict[str, Any]],
    evidence_gap_refs: list[str],
    rag_statuses: list[str],
) -> list[str]:
    reasons: list[str] = []
    answered_count, _total_chars = _answer_metrics(turns=turns)
    if not turns or answered_count == 0:
        reasons.append("缺少可评分回答")
    if evidence_gap_refs:
        reasons.append("存在 RAG evidence gap")
    if any(status in {"degraded", "failed", "retryable"} for status in rag_statuses):
        reasons.append("RAG trace 状态降级")
    return reasons


def _score_dimensions(
    *,
    score_total: int,
    turns: list[dict[str, Any]],
    citation_refs: list[str],
    evidence_refs: list[str],
    evidence_gap_refs: list[str],
    low_confidence: bool,
    low_confidence_reason: str,
) -> list[dict[str, Any]]:
    answered_count, total_chars = _answer_metrics(turns=turns)
    average_length = total_chars / answered_count if answered_count else 0
    adjustments = (2, 0, -4 if average_length < 48 else 3, 1, -6 if low_confidence else 2)
    reasons = (
        "结合岗位与简历信息，回答覆盖了主要匹配点。",
        "回答结构基本清晰，可继续补充上下文和结果。",
        "技术细节随回答长度和具体案例深度提升。",
        "回答围绕当前岗位问题展开，具备岗位相关性。",
        "证据链和不确定性会影响该维度的置信度。",
    )
    dimensions: list[dict[str, Any]] = []
    for (dimension_id, label), adjustment, reason in zip(
        SCORE_DIMENSION_DEFINITIONS,
        adjustments,
        reasons,
        strict=True,
    ):
        dimension_score = _clamp_score(score_total + adjustment)
        dimensions.append(
            {
                "id": dimension_id,
                "label": label,
                "score": dimension_score,
                "reason": _dimension_reason(
                    base_reason=reason,
                    citation_refs=citation_refs,
                    evidence_gap_refs=evidence_gap_refs,
                ),
                "evidence_refs": evidence_refs,
                "citation_refs": citation_refs,
                "evidence_gap_refs": evidence_gap_refs,
                "low_confidence": low_confidence,
                "low_confidence_reason": low_confidence_reason,
            }
        )
    return dimensions


def _dimension_reason(
    *,
    base_reason: str,
    citation_refs: list[str],
    evidence_gap_refs: list[str],
) -> str:
    suffixes: list[str] = []
    if citation_refs:
        suffixes.append("已关联可追踪 citation。")
    if evidence_gap_refs:
        suffixes.append("存在 evidence gap，需降低证据置信度。")
    return " ".join([base_reason, *suffixes])


def _score_suggestions(*, score_total: int, evidence_gap_refs: list[str]) -> list[str]:
    suggestions = [
        "每题补齐动作、过程、结果三个维度。",
        "对关键问题给出可量化结果。",
    ]
    if score_total < 70:
        suggestions.append("优先补强技术细节和岗位关联案例。")
    if evidence_gap_refs:
        suggestions.append("补充可引用证据，降低 evidence gap 对复盘可信度的影响。")
    return suggestions


def _score_weak_areas(*, dimensions: list[dict[str, Any]]) -> list[str]:
    weak = [
        str(dimension["label"])
        for dimension in dimensions
        if isinstance(dimension.get("score"), int) and dimension["score"] < 70
    ]
    return weak[:3] or ["暂无明显薄弱项"]


def _score_review_summary(*, score_total: int, low_confidence: bool) -> str:
    summary = _score_explanation(score_total)
    if low_confidence:
        return f"{summary} 当前证据链存在缺口，复盘结论需标记低置信度。"
    return summary


def _provider_score(
    *,
    provider: LLMProvider,
    interview: Mapping[str, Any],
    turns: list[dict[str, Any]],
    session_id: str,
    owner_id: str,
) -> dict[str, Any]:
    """调用 ST13_11 provider 边界生成 score；解析失败回退 deterministic。"""
    request = LLMGenerateRequest(
        purpose=PURPOSE_SCORE,
        job=dict(interview.get("job", {})),
        resume=dict(interview.get("resume", {})),
        history=_history_payload(turns=turns),
        last_answer=None,
        metadata={
            "mode": str(interview.get(FIELD_MODE) or DEFAULT_INTERVIEW_MODE),
            "session_id": session_id,
            "owner_id": owner_id,
        },
        request_id=f"score-{_short_id()}",
        session_id=session_id,
        turn_index=len(turns),
        prompt_version=DEFAULT_PROMPT_VERSION,
    )
    result = provider.generate(request)
    extracted = _extract_score(result.content)
    score_value = extracted if extracted is not None else _deterministic_score_payload(turns=turns)[
        SCORE_VALUE_KEY
    ]

    return {
        SCORE_VALUE_KEY: score_value,
        SCORE_STRATEGY_KEY: SCORE_PROVIDER_STRATEGY,
        SCORE_METADATA_KEY: {
            "provider": result.provider,
            "model": result.model,
            "provider_request_id": result.request_id,
        },
    }


def _extract_score(content: str) -> int | None:
    """从 provider 输出中提取 0~100 的第一个整数。"""
    match = re.search(r"\b(?:100|[1-9]?\d)\b", content)
    if match is None:
        return None
    value = int(match.group(0))
    if value < SCORE_MIN or value > SCORE_MAX:
        return None
    return value


def _answer_metrics(turns: list[dict[str, Any]]) -> tuple[int, int]:
    """统计已回答条目数和回答总字符。"""
    answered = 0
    total_chars = 0
    for turn in turns:
        answer = turn.get(FIELD_ANSWER)
        if not isinstance(answer, Mapping):
            continue
        content = answer.get(FIELD_CONTENT)
        if not isinstance(content, str):
            continue
        text = content.strip()
        if not text:
            continue
        answered += 1
        total_chars += len(text)
    return answered, total_chars


def _clamp_score(value: int) -> int:
    """确保 score 落在 0~100 闭区间。"""
    return max(SCORE_MIN, min(SCORE_MAX, int(value)))


def _history_payload(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """将 turn 历史转成 provider 可读的精简上下文。"""
    history: list[dict[str, Any]] = []
    for turn in turns:
        answer = turn.get(FIELD_ANSWER)
        if not isinstance(answer, Mapping):
            answer = {}
        history.append(
            {
                "question": str(turn.get(FIELD_QUESTION, "")),
                "answer": answer.get(FIELD_CONTENT),
            }
        )
    return history


def _latest_answer_ref(turns: list[dict[str, Any]]) -> str | None:
    for turn in reversed(turns):
        answer = turn.get(FIELD_ANSWER)
        if isinstance(answer, Mapping) and answer.get(FIELD_CONTENT):
            return f"answer:{turn.get(FIELD_TURN_ID, '')}"
    return None


def _bump_snapshot_index(payload: dict[str, Any]) -> None:
    interview = payload.get(PAYLOAD_INTERVIEW_KEY)
    if not isinstance(interview, dict):
        return
    current = interview.get(FIELD_SNAPSHOT_INDEX)
    interview[FIELD_SNAPSHOT_INDEX] = current + 1 if isinstance(current, int) else 1


def _trace_summary(
    *,
    trace_store: TraceabilityStore | None,
    owner_id: str,
    session_id: str,
) -> dict[str, Any]:
    if trace_store is None:
        return build_trace_summary(())
    return build_trace_summary(trace_store.list_traces(owner_id=owner_id, session_ref=session_id))


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


def _get_session_context(
    *,
    store: InterviewRecordStore,
    owner_id: str,
    session_id: str,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    """按 owner + session_id 获取最新 session 记录和 payload。"""
    record = _latest_session_record(store=store, owner_id=owner_id, session_id=session_id)
    if record is None:
        raise InterviewFlowNotFound("INTERVIEW_SESSION_NOT_FOUND")

    payload = record[FIELD_PAYLOAD]
    interview = payload.get(PAYLOAD_INTERVIEW_KEY)
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
    """按 owner + session 取最新 snapshot。"""
    latest: tuple[int, dict[str, Any]] | None = None
    for summary in store.list_records(owner_id=owner_id):
        record = store.get_record(summary[FIELD_ID])
        if record is None:
            continue
        payload = record.get(FIELD_PAYLOAD)
        interview = payload.get(PAYLOAD_INTERVIEW_KEY) if isinstance(payload, Mapping) else None
        if not isinstance(interview, Mapping):
            continue
        if str(interview.get(FIELD_SESSION_ID)) != session_id:
            continue
        snapshot_index = interview.get(FIELD_SNAPSHOT_INDEX)
        index = snapshot_index if isinstance(snapshot_index, int) else 0
        if latest is None or index > latest[0]:
            latest = (index, record)
    return latest[1] if latest is not None else None


def _short_id() -> str:
    """给 provider request 生成可读短 id。"""
    from uuid import uuid4

    return uuid4().hex[:12]


def _utc_now() -> str:
    """返回统一时间戳，便于 trace 与测试。"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _score_explanation(value: int) -> str:
    """给 score 附加最小解释。"""
    if value >= 80:
        return "完成度高，答案完整性与深度表现稳定。"
    if value >= 60:
        return "完成度一般，核心点有覆盖但仍需补充细节。"
    return "完成度偏低，存在明显可提升空间。"
