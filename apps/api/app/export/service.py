"""R0 Markdown 导出服务，基于 session / score / review 生成可追溯内容。"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from app.interview_flow import InterviewFlowNotFound
from app.interview_flow.contract import (
    FIELD_ANSWER,
    FIELD_CONTENT,
    FIELD_QUESTION,
    FIELD_SESSION_ID,
    FIELD_TURN_ID,
    FIELD_TURNS,
    INTERVIEW_FLOW_RECORD_SOURCE,
)
from app.interview_record_contract import (
    DEFAULT_RECORD_VERSION,
    FIELD_ID,
    FIELD_PAYLOAD,
    PAYLOAD_INTERVIEW,
    PAYLOAD_REVIEW,
)
from app.persistence import InterviewRecordStore, TraceabilityStore
from app.review import ReviewService
from app.scoring import ScoringService
from app.traceability import TRACE_TYPE_REVIEW_EXPORT, TraceabilityRecord, TraceabilityStatus

PAYLOAD_SCORE = "score"
EXPORT_PAYLOAD_KEY = "export"
EXPORT_FORMAT_KEY = "format"
EXPORT_CONTENT_KEY = "content"
EXPORT_CONTENT_VERSION_KEY = "content_version"
EXPORT_METADATA_KEY = "metadata"
EXPORT_GENERATED_AT_KEY = "generated_at"
EXPORT_FORMAT_MARKDOWN = "markdown"
EXPORT_CONTENT_VERSION = "r0-export-v1"


class ExportService:
    """基于 session 构建可确定性 Markdown export payload 并持久化。"""

    def __init__(
        self,
        *,
        store: InterviewRecordStore,
        scoring_service: ScoringService | None = None,
        review_service: ReviewService | None = None,
        trace_store: TraceabilityStore | None = None,
    ) -> None:
        self.store = store
        self.trace_store = trace_store
        self.scoring_service = scoring_service or ScoringService(
            store=store,
            trace_store=trace_store,
        )
        self.review_service = review_service or ReviewService(
            store=store,
            scoring_service=self.scoring_service,
            trace_store=trace_store,
        )

    def generate_export(
        self,
        *,
        owner_id: str,
        session_id: str,
        persist: bool = True,
    ) -> dict[str, Any]:
        """生成 Markdown export 内容，默认持久化回 session payload。"""
        record, interview, turns = _get_session_context(
            store=self.store,
            owner_id=owner_id,
            session_id=session_id,
        )

        score_payload = (
            _payload_nested_dict(record[FIELD_PAYLOAD], PAYLOAD_SCORE)
            or self.scoring_service.generate_score(
                owner_id=owner_id,
                session_id=session_id,
                persist=False,
            )["score"]
        )
        review_payload = (
            _payload_nested_dict(record[FIELD_PAYLOAD], PAYLOAD_REVIEW)
            or self.review_service.generate_review(
                owner_id=owner_id,
                session_id=session_id,
                persist=False,
            )["review"]
        )
        if not isinstance(score_payload, Mapping):
            score_payload = {}
        if not isinstance(review_payload, Mapping):
            review_payload = {}

        export_content = _build_markdown_content(
            interview=interview,
            turns=turns,
            score_payload=score_payload,
            review_payload=review_payload,
            owner_id=owner_id,
            session_id=session_id,
        )
        export_payload = {
            EXPORT_FORMAT_KEY: EXPORT_FORMAT_MARKDOWN,
            EXPORT_CONTENT_KEY: export_content,
            EXPORT_CONTENT_VERSION_KEY: EXPORT_CONTENT_VERSION,
            EXPORT_METADATA_KEY: {
                "session_id": str(interview.get(FIELD_SESSION_ID, session_id)),
                "owner_id": owner_id,
                EXPORT_GENERATED_AT_KEY: _utc_now(),
                "record_id": str(record[FIELD_ID]),
                "turn_count": len(turns),
                "score": score_payload,
                "review_version": str(review_payload.get("content_version", "")),
            },
        }

        payload = deepcopy(record[FIELD_PAYLOAD])
        payload[EXPORT_PAYLOAD_KEY] = export_payload
        payload[PAYLOAD_SCORE] = score_payload
        payload[PAYLOAD_REVIEW] = review_payload

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
                status=TraceabilityStatus.COMPLETED,
                request_id=f"export:{record[FIELD_ID]}",
                operation_id="export.markdown",
                session_ref=str(interview.get(FIELD_SESSION_ID, session_id)),
                answer_ref=_latest_answer_ref(turns),
                score_ref=f"score:{session_id}:{score_payload.get('content_version', '')}",
                review_ref=f"review:{session_id}:{review_payload.get('content_version', '')}",
                export_ref=f"export:{session_id}:{EXPORT_CONTENT_VERSION}",
                source_snapshot_ref=f"{record[FIELD_ID]}:export",
                content_version=EXPORT_CONTENT_VERSION,
                metadata={
                    "operation": "export.markdown",
                    "record_id": record[FIELD_ID],
                    "format": EXPORT_FORMAT_MARKDOWN,
                },
            )
        )
        return {
            "record_id": record[FIELD_ID],
            "owner_id": owner_id,
            "session_id": str(interview.get(FIELD_SESSION_ID, session_id)),
            EXPORT_PAYLOAD_KEY: export_payload,
        }

    def _record_trace(self, record: TraceabilityRecord) -> None:
        if self.trace_store is not None:
            self.trace_store.create_trace(record)


def _build_markdown_content(
    *,
    interview: Mapping[str, Any],
    turns: list[Mapping[str, Any]],
    score_payload: Mapping[str, Any],
    review_payload: Mapping[str, Any],
    owner_id: str,
    session_id: str,
) -> str:
    """生成可断言的 Markdown 内容。"""
    score_value = score_payload.get("value")
    review_summary = str(review_payload.get("summary", "")) if isinstance(review_payload, Mapping) else ""
    weaknesses = review_payload.get("weakness", [])
    improvements = review_payload.get("improvements", [])
    if not isinstance(weaknesses, list):
        weaknesses = []
    if not isinstance(improvements, list):
        improvements = []

    lines = [
        f"# Interview Review Export",
        f"- 会话：{session_id}",
        f"- Owner：{owner_id}",
        f"- 模式：{interview.get('mode', 'r0_mock')}",
        "",
        "## Score",
        f"- score: {score_value}",
        "",
        "## Review Summary",
        f"- {review_summary}",
        "",
        "## Weakness",
    ]

    if weaknesses:
        for item in weaknesses:
            lines.append(f"- {item}")
    else:
        lines.append("- 无明显薄弱项。")

    lines.extend(["", "## Improvement"])
    if improvements:
        lines.extend(f"- {item}" for item in improvements[:3])
    else:
        lines.append("- 无明显改进建议。")
    lines.extend(["", "## Interview Q&A"])

    for index, turn in enumerate(turns, start=1):
        question = str(turn.get(FIELD_QUESTION, ""))
        answer = _answer_content(turn)
        lines.extend(
            [
                f"### Q{index}",
                f"- 问题：{question}",
                f"- 回答：{answer}",
            ]
        )

    return "\n".join(lines)


def _answer_content(turn: Mapping[str, Any]) -> str:
    """从 turn 中提取可渲染的 answer。"""
    answer = turn.get("answer")
    if not isinstance(answer, Mapping):
        return ""
    answer_content = answer.get("content")
    return answer_content if isinstance(answer_content, str) else ""


def _latest_answer_ref(turns: list[dict[str, Any]]) -> str | None:
    for turn in reversed(turns):
        answer = turn.get(FIELD_ANSWER)
        if isinstance(answer, Mapping) and answer.get(FIELD_CONTENT):
            return f"answer:{turn.get(FIELD_TURN_ID, '')}"
    return None


def _payload_nested_dict(payload: Mapping[str, Any], key: str) -> Mapping[str, Any] | None:
    """读取 payload key 指向的 dict。"""
    value = payload.get(key)
    return value if isinstance(value, Mapping) else None


def _get_session_context(
    *,
    store: InterviewRecordStore,
    owner_id: str,
    session_id: str,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    """按 owner + session 取 latest session，未找到则抛 NotFound。"""
    record = _latest_session_record(store=store, owner_id=owner_id, session_id=session_id)
    if record is None:
        raise InterviewFlowNotFound("INTERVIEW_SESSION_NOT_FOUND")

    payload = record[FIELD_PAYLOAD]
    interview = payload.get(PAYLOAD_INTERVIEW, {})
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
        snapshot_index = interview.get("snapshot_index", 0)
        if not isinstance(snapshot_index, int):
            snapshot_index = 0
        if latest is None or snapshot_index > latest[0]:
            latest = (snapshot_index, record)
    return latest[1] if latest is not None else None


def _utc_now() -> str:
    """返回 export trace 可追溯时间戳。"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
