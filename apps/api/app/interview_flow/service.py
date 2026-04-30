"""R0 模拟面试主链路 orchestration，不承载评分、复盘或导出。"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any
from uuid import uuid4

from app.interview_flow.contract import (
    DEFAULT_INTERVIEW_MODE,
    ERROR_INTERVIEW_SESSION_NOT_FOUND,
    ERROR_INTERVIEW_TURN_NOT_FOUND,
    FIELD_ANSWER,
    FIELD_CONTENT,
    FIELD_CURRENT_TURN,
    FIELD_FINISH_REASON,
    FIELD_JOB,
    FIELD_METADATA,
    FIELD_MODE,
    FIELD_MODEL,
    FIELD_NEXT_TURN,
    FIELD_PROMPT_VERSION,
    FIELD_PROVIDER,
    FIELD_PROVIDER_REQUEST_ID,
    FIELD_PROVIDER_TRACE,
    FIELD_QUESTION,
    FIELD_RECORD_ID,
    FIELD_REQUEST_ID,
    FIELD_RESUME,
    FIELD_SESSION_ID,
    FIELD_SNAPSHOT_INDEX,
    FIELD_TURN_ID,
    FIELD_TURN_INDEX,
    FIELD_TURNS,
    FIELD_USAGE,
    INTERVIEW_FLOW_RECORD_SOURCE,
    SESSION_STATUS_IN_PROGRESS,
)
from app.interview_record_contract import (
    DEFAULT_RECORD_VERSION,
    FIELD_CREATED_AT,
    FIELD_ID,
    FIELD_OWNER_ID,
    FIELD_PAYLOAD,
    FIELD_UPDATED_AT,
    PAYLOAD_INTERVIEW,
    RESPONSE_ITEMS,
    RESPONSE_STATUS,
)
from app.llm.constants import PURPOSE_FOLLOW_UP, PURPOSE_QUESTION
from app.llm.models import LLMGenerateRequest, LLMGenerateResult
from app.llm.providers import LLMProvider
from app.persistence import InterviewRecordStore, TraceabilityStore
from app.traceability import TRACE_TYPE_INTERVIEW, TraceabilityRecord, TraceabilityStatus


class InterviewFlowNotFound(Exception):
    """主链路按 owner_id 隔离后找不到 session 或 turn。"""

    def __init__(self, message: str) -> None:
        """记录可直接进入 HTTP error envelope 的稳定 message。"""
        super().__init__(message)
        self.message = message


class InterviewFlowService:
    """协调 ST13_11 provider 与 ST13_20 persistence 的最小 R0 主链路。"""

    def __init__(
        self,
        *,
        store: InterviewRecordStore,
        provider: LLMProvider | None = None,
        trace_store: TraceabilityStore | None = None,
    ) -> None:
        """注入依赖，避免 service 自行创建第二套 persistence 或 provider。"""
        self.store = store
        self.provider = provider
        self.trace_store = trace_store

    def start_interview(
        self,
        *,
        owner_id: str,
        job: Mapping[str, Any],
        resume: Mapping[str, Any],
        mode: str = DEFAULT_INTERVIEW_MODE,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """创建 session，生成首题，并写入 ST13_20 最小记录表。"""
        session_id = _new_id(FIELD_SESSION_ID)
        turn_id = _new_id(FIELD_TURN_ID)
        request_id = _new_id(FIELD_REQUEST_ID)
        metadata_dict = dict(metadata or {})
        result = self._provider().generate(
            LLMGenerateRequest(
                purpose=PURPOSE_QUESTION,
                job=dict(job),
                resume=dict(resume),
                history=[],
                last_answer=None,
                metadata=_provider_metadata(mode=mode, metadata=metadata_dict),
                request_id=request_id,
                session_id=session_id,
                turn_index=0,
            )
        )
        turn = _turn_from_result(result=result, turn_id=turn_id, turn_index=0)
        payload = _payload(
            job=job,
            resume=resume,
            interview={
                FIELD_SESSION_ID: session_id,
                FIELD_MODE: mode,
                RESPONSE_STATUS: SESSION_STATUS_IN_PROGRESS,
                FIELD_METADATA: metadata_dict,
                FIELD_SNAPSHOT_INDEX: 0,
                FIELD_TURNS: [turn],
                FIELD_PROVIDER_TRACE: [_provider_trace(result)],
            },
        )
        record = self.store.create_record(
            owner_id=owner_id,
            source=INTERVIEW_FLOW_RECORD_SOURCE,
            version=DEFAULT_RECORD_VERSION,
            payload=payload,
        )
        self._record_trace(
            TraceabilityRecord(
                owner_id=owner_id,
                trace_type=TRACE_TYPE_INTERVIEW,
                status=TraceabilityStatus.COMPLETED,
                request_id=request_id,
                operation_id="interview.start",
                job_ref=f"job:{record[FIELD_ID]}",
                resume_ref=f"resume:{record[FIELD_ID]}",
                session_ref=session_id,
                turn_ref=turn_id,
                source_snapshot_ref=f"{record[FIELD_ID]}:snapshot:0",
                content_version="r1-interview-trace-v1",
                metadata={
                    "operation": "interview.start",
                    "record_id": record[FIELD_ID],
                    "mode": mode,
                    "provider_request_id": result.provider_request_id,
                },
            )
        )
        return _session_response(record, current_turn=turn)

    def submit_answer(
        self,
        *,
        owner_id: str,
        session_id: str,
        turn_id: str,
        content: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """保存回答，生成下一轮 follow-up，并追加新的 session snapshot。"""
        record = self._latest_session_record(owner_id=owner_id, session_id=session_id)
        if record is None:
            raise InterviewFlowNotFound(ERROR_INTERVIEW_SESSION_NOT_FOUND)

        payload = deepcopy(record[FIELD_PAYLOAD])
        interview = payload[PAYLOAD_INTERVIEW]
        turns = interview[FIELD_TURNS]
        answered_turn = _find_turn(turns=turns, turn_id=turn_id)
        if answered_turn is None:
            raise InterviewFlowNotFound(ERROR_INTERVIEW_TURN_NOT_FOUND)

        answered_turn[FIELD_ANSWER] = {
            FIELD_CONTENT: content,
            FIELD_METADATA: dict(metadata or {}),
        }
        turn_index = len(turns)
        request_id = _new_id(FIELD_REQUEST_ID)
        result = self._provider().generate(
            LLMGenerateRequest(
                purpose=PURPOSE_FOLLOW_UP,
                job=payload.get(FIELD_JOB, {}),
                resume=payload.get(FIELD_RESUME, {}),
                history=_history_for_provider(turns),
                last_answer=content,
                metadata=_provider_metadata(
                    mode=str(interview.get(FIELD_MODE) or DEFAULT_INTERVIEW_MODE),
                    metadata=dict(metadata or {}),
                ),
                request_id=request_id,
                session_id=session_id,
                turn_index=turn_index,
            )
        )
        next_turn = _turn_from_result(
            result=result,
            turn_id=_new_id(FIELD_TURN_ID),
            turn_index=turn_index,
        )
        turns.append(next_turn)
        interview[FIELD_SNAPSHOT_INDEX] = _snapshot_index(interview) + 1
        interview[FIELD_PROVIDER_TRACE].append(_provider_trace(result))

        next_record = self.store.create_record(
            owner_id=owner_id,
            source=INTERVIEW_FLOW_RECORD_SOURCE,
            version=DEFAULT_RECORD_VERSION,
            payload=payload,
        )
        self._record_trace(
            TraceabilityRecord(
                owner_id=owner_id,
                trace_type=TRACE_TYPE_INTERVIEW,
                status=TraceabilityStatus.COMPLETED,
                request_id=request_id,
                operation_id="interview.answer",
                session_ref=session_id,
                turn_ref=turn_id,
                answer_ref=f"answer:{turn_id}",
                source_snapshot_ref=(
                    f"{next_record[FIELD_ID]}:snapshot:{interview[FIELD_SNAPSHOT_INDEX]}"
                ),
                content_version="r1-interview-trace-v1",
                metadata={
                    "operation": "interview.answer",
                    "record_id": next_record[FIELD_ID],
                    "next_turn_ref": next_turn[FIELD_TURN_ID],
                    "provider_request_id": result.provider_request_id,
                },
            )
        )
        return _session_response(next_record, current_turn=next_turn, next_turn=next_turn)

    def restore_session(self, *, owner_id: str, session_id: str) -> dict[str, Any]:
        """按 owner_id + session_id 恢复最新 session snapshot。"""
        record = self._latest_session_record(owner_id=owner_id, session_id=session_id)
        if record is None:
            raise InterviewFlowNotFound(ERROR_INTERVIEW_SESSION_NOT_FOUND)
        return _session_response(record)

    def list_history(self, *, owner_id: str) -> dict[str, list[dict[str, Any]]]:
        """返回 owner 范围内每个 session 的最新摘要。"""
        latest_by_session: dict[str, tuple[int, dict[str, Any], dict[str, Any]]] = {}
        for summary in self.store.list_records(owner_id=owner_id):
            record = self.store.get_record(summary[FIELD_ID])
            if record is None:
                continue
            interview = _interview_from_record(record)
            session_id = interview.get(FIELD_SESSION_ID)
            if not isinstance(session_id, str):
                continue
            snapshot_index = _snapshot_index(interview)
            current = latest_by_session.get(session_id)
            if current is None or snapshot_index > current[0]:
                latest_by_session[session_id] = (snapshot_index, record, interview)

        items: list[dict[str, Any]] = []
        for _snapshot_index_value, record, interview in latest_by_session.values():
            turns = _turns_from_interview(interview)
            items.append(
                {
                    FIELD_RECORD_ID: record[FIELD_ID],
                    FIELD_SESSION_ID: session_id,
                    FIELD_OWNER_ID: record[FIELD_OWNER_ID],
                    RESPONSE_STATUS: interview.get(RESPONSE_STATUS, SESSION_STATUS_IN_PROGRESS),
                    FIELD_MODE: interview.get(FIELD_MODE, DEFAULT_INTERVIEW_MODE),
                    FIELD_TURN_INDEX: max(len(turns) - 1, 0),
                    FIELD_CREATED_AT: record[FIELD_CREATED_AT],
                    FIELD_UPDATED_AT: record[FIELD_UPDATED_AT],
                }
            )
        self._record_trace(
            TraceabilityRecord(
                owner_id=owner_id,
                trace_type=TRACE_TYPE_INTERVIEW,
                status=TraceabilityStatus.COMPLETED,
                request_id=_new_id(FIELD_REQUEST_ID),
                operation_id="history.list",
                content_version="r1-history-trace-v1",
                metadata={
                    "operation": "history.list",
                    "item_count": len(items),
                },
            )
        )
        return {RESPONSE_ITEMS: items}

    def _latest_session_record(
        self,
        *,
        owner_id: str,
        session_id: str,
    ) -> dict[str, Any] | None:
        latest: tuple[int, dict[str, Any]] | None = None
        for summary in self.store.list_records(owner_id=owner_id):
            record = self.store.get_record(summary[FIELD_ID])
            if record is None:
                continue
            interview = _interview_from_record(record)
            if interview.get(FIELD_SESSION_ID) == session_id:
                snapshot_index = _snapshot_index(interview)
                if latest is None or snapshot_index > latest[0]:
                    latest = (snapshot_index, record)
        return latest[1] if latest is not None else None

    def _provider(self) -> LLMProvider:
        if self.provider is None:
            raise RuntimeError("LLM provider is required for interview generation")
        return self.provider

    def _record_trace(self, record: TraceabilityRecord) -> None:
        if self.trace_store is not None:
            self.trace_store.create_trace(record)


def _payload(
    *,
    job: Mapping[str, Any],
    resume: Mapping[str, Any],
    interview: dict[str, Any],
) -> dict[str, Any]:
    return {
        FIELD_JOB: dict(job),
        FIELD_RESUME: dict(resume),
        PAYLOAD_INTERVIEW: interview,
    }


def _session_response(
    record: dict[str, Any],
    *,
    current_turn: dict[str, Any] | None = None,
    next_turn: dict[str, Any] | None = None,
) -> dict[str, Any]:
    interview = _interview_from_record(record)
    turns = _turns_from_interview(interview)
    response: dict[str, Any] = {
        FIELD_RECORD_ID: record[FIELD_ID],
        FIELD_SESSION_ID: interview[FIELD_SESSION_ID],
        FIELD_OWNER_ID: record[FIELD_OWNER_ID],
        RESPONSE_STATUS: interview.get(RESPONSE_STATUS, SESSION_STATUS_IN_PROGRESS),
        FIELD_MODE: interview.get(FIELD_MODE, DEFAULT_INTERVIEW_MODE),
        FIELD_METADATA: interview.get(FIELD_METADATA, {}),
        FIELD_TURNS: turns,
        FIELD_CURRENT_TURN: current_turn or (turns[-1] if turns else None),
    }
    if next_turn is not None:
        response[FIELD_NEXT_TURN] = next_turn
    return response


def _interview_from_record(record: dict[str, Any]) -> dict[str, Any]:
    payload = record.get(FIELD_PAYLOAD, {})
    interview = payload.get(PAYLOAD_INTERVIEW, {}) if isinstance(payload, Mapping) else {}
    return interview if isinstance(interview, dict) else {}


def _turns_from_interview(interview: Mapping[str, Any]) -> list[dict[str, Any]]:
    turns = interview.get(FIELD_TURNS, [])
    return [dict(turn) for turn in turns] if isinstance(turns, list) else []


def _turn_from_result(
    *,
    result: LLMGenerateResult,
    turn_id: str,
    turn_index: int,
) -> dict[str, Any]:
    turn: dict[str, Any] = {
        FIELD_TURN_ID: turn_id,
        FIELD_TURN_INDEX: turn_index,
        FIELD_QUESTION: result.content,
        FIELD_ANSWER: None,
        FIELD_PROVIDER: result.provider,
        FIELD_MODEL: result.model,
        FIELD_REQUEST_ID: result.request_id,
        FIELD_FINISH_REASON: result.finish_reason,
        FIELD_METADATA: dict(result.metadata),
    }
    if result.provider_request_id is not None:
        turn[FIELD_PROVIDER_REQUEST_ID] = result.provider_request_id
    if result.usage is not None:
        turn[FIELD_USAGE] = dict(result.usage)
    return turn


def _provider_trace(result: LLMGenerateResult) -> dict[str, Any]:
    trace = {
        FIELD_PROVIDER: result.provider,
        FIELD_MODEL: result.model,
        FIELD_REQUEST_ID: result.request_id,
        FIELD_FINISH_REASON: result.finish_reason,
    }
    if result.provider_request_id is not None:
        trace[FIELD_PROVIDER_REQUEST_ID] = result.provider_request_id
    return trace


def _history_for_provider(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    history: list[dict[str, Any]] = []
    for turn in turns:
        answer = turn.get(FIELD_ANSWER)
        history.append(
            {
                FIELD_QUESTION: turn.get(FIELD_QUESTION),
                FIELD_ANSWER: answer if isinstance(answer, Mapping) else None,
            }
        )
    return history


def _provider_metadata(*, mode: str, metadata: dict[str, Any]) -> dict[str, Any]:
    return {**metadata, FIELD_MODE: mode}


def _snapshot_index(interview: Mapping[str, Any]) -> int:
    value = interview.get(FIELD_SNAPSHOT_INDEX)
    return value if isinstance(value, int) else 0


def _find_turn(*, turns: list[dict[str, Any]], turn_id: str) -> dict[str, Any] | None:
    for turn in turns:
        if turn.get(FIELD_TURN_ID) == turn_id:
            return turn
    return None


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"
