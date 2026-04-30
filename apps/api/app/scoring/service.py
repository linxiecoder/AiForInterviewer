"""R0 评分服务，实现最小 0-100 score 并持久化到 session payload。"""

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
from app.persistence import InterviewRecordStore

SCORE_PAYLOAD_KEY = "score"
SCORE_VALUE_KEY = "value"
SCORE_STRATEGY_KEY = "scoring_strategy"
SCORE_CONTENT_VERSION_KEY = "content_version"
SCORE_GENERATED_AT_KEY = "generated_at"
SCORE_EXPLANATION_KEY = "explanation"
SCORE_METADATA_KEY = "metadata"

SCORE_MIN = 0
SCORE_MAX = 100
SCORE_CONTENT_VERSION = "r0-score-v1"
SCORE_DETERMINISTIC_STRATEGY = "deterministic"
SCORE_PROVIDER_STRATEGY = "provider_assisted"


class ScoringService:
    """按 interview session 计算最小 0-100 score，并可持久化。"""

    def __init__(
        self,
        *,
        store: InterviewRecordStore,
        provider: LLMProvider | None = None,
    ) -> None:
        self.store = store
        self.provider = provider

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
            score_payload = _provider_score(
                provider=self.provider,
                interview=interview,
                turns=turns,
                session_id=session_id,
                owner_id=owner_id,
            )
        else:
            score_payload = _deterministic_score_payload(turns=turns)

        score_payload = {
            SCORE_VALUE_KEY: _clamp_score(int(score_payload[SCORE_VALUE_KEY])),
            SCORE_STRATEGY_KEY: score_payload[SCORE_STRATEGY_KEY],
            SCORE_CONTENT_VERSION_KEY: SCORE_CONTENT_VERSION,
            SCORE_EXPLANATION_KEY: _score_explanation(
                int(score_payload[SCORE_VALUE_KEY]),
            ),
            SCORE_GENERATED_AT_KEY: _utc_now(),
            SCORE_METADATA_KEY: {
                **score_payload.get(SCORE_METADATA_KEY, {}),
                "session_id": str(interview.get(FIELD_SESSION_ID, session_id)),
                "owner_id": owner_id,
                "status": str(interview.get(RESPONSE_STATUS, SESSION_STATUS_IN_PROGRESS)),
            },
        }

        payload = deepcopy(record[FIELD_PAYLOAD])
        payload[SCORE_PAYLOAD_KEY] = score_payload

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
        }


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
