"""ST13_20 R1 数据追踪领域模型。"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

TRACE_TYPE_INTERVIEW = "interview"
TRACE_TYPE_RAG_EVIDENCE = "rag_evidence"
TRACE_TYPE_REVIEW_EXPORT = "review_export"

TRACE_SUMMARY_STATUS_EMPTY = "empty"
TRACE_SUMMARY_STATUS_AVAILABLE = "available"
TRACE_SUMMARY_REQUEST_ID_MAX_LENGTH = 64


class TraceabilityStatus(StrEnum):
    """R1 数据追踪最小状态集合。"""

    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    DEGRADED = "degraded"
    RETRYABLE = "retryable"


@dataclass(frozen=True)
class TraceabilityRecord:
    """可持久化的最小 traceability 输入。"""

    owner_id: str
    trace_type: str
    status: TraceabilityStatus
    request_id: str
    operation_id: str
    job_ref: str | None = None
    resume_ref: str | None = None
    session_ref: str | None = None
    turn_ref: str | None = None
    answer_ref: str | None = None
    score_ref: str | None = None
    review_ref: str | None = None
    export_ref: str | None = None
    retrieval_query_ref: str | None = None
    retrieval_result_ref: str | None = None
    citation_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    evidence_gap_ref: str | None = None
    source_snapshot_ref: str | None = None
    schema_version: int = 1
    content_version: str | None = None
    retryable: bool = False
    failure_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def build_trace_summary(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """把持久化 trace records 转成前端可展示的安全摘要。"""
    ordered_records = list(records)
    summary = _empty_trace_summary()
    if not ordered_records:
        return summary

    summary["status"] = TRACE_SUMMARY_STATUS_AVAILABLE
    summary["counts"]["total"] = len(ordered_records)

    for record in ordered_records:
        trace_type = _optional_string(record.get("trace_type"))
        if trace_type in summary["counts"]:
            summary["counts"][trace_type] += 1

        _append_unique(summary["session_refs"], record.get("session_ref"))
        _append_unique(summary["turn_refs"], record.get("turn_ref"))
        _append_unique(summary["answer_refs"], record.get("answer_ref"))
        _append_unique(summary["score_refs"], record.get("score_ref"))
        _append_unique(summary["review_refs"], record.get("review_ref"))
        _append_unique(summary["export_refs"], record.get("export_ref"))

        rag_summary = summary["rag"]
        _append_unique(rag_summary["retrieval_query_refs"], record.get("retrieval_query_ref"))
        _append_unique(rag_summary["retrieval_result_refs"], record.get("retrieval_result_ref"))
        _extend_unique(rag_summary["citation_refs"], record.get("citation_refs"))
        _extend_unique(rag_summary["evidence_refs"], record.get("evidence_refs"))
        _append_unique(rag_summary["evidence_gap_refs"], record.get("evidence_gap_ref"))
        if trace_type == TRACE_TYPE_RAG_EVIDENCE:
            _append_unique(rag_summary["statuses"], record.get("status"))

        request_ref = _request_ref(record)
        if request_ref is not None:
            summary["request_refs"].append(request_ref)

    return summary


def _empty_trace_summary() -> dict[str, Any]:
    return {
        "status": TRACE_SUMMARY_STATUS_EMPTY,
        "counts": {
            "total": 0,
            TRACE_TYPE_INTERVIEW: 0,
            TRACE_TYPE_RAG_EVIDENCE: 0,
            TRACE_TYPE_REVIEW_EXPORT: 0,
        },
        "session_refs": [],
        "turn_refs": [],
        "answer_refs": [],
        "score_refs": [],
        "review_refs": [],
        "export_refs": [],
        "rag": {
            "retrieval_query_refs": [],
            "retrieval_result_refs": [],
            "citation_refs": [],
            "evidence_refs": [],
            "evidence_gap_refs": [],
            "statuses": [],
        },
        "request_refs": [],
    }


def _request_ref(record: Mapping[str, Any]) -> dict[str, str] | None:
    request_id = _limited_string(record.get("request_id"))
    operation_id = _limited_string(record.get("operation_id"))
    if request_id is None and operation_id is None:
        return None
    ref: dict[str, str] = {}
    for key in ("trace_type", "status"):
        value = _optional_string(record.get(key))
        if value is not None:
            ref[key] = value
    if request_id is not None:
        ref["request_id"] = request_id
    if operation_id is not None:
        ref["operation_id"] = operation_id
    return ref


def _append_unique(items: list[str], value: Any) -> None:
    text = _optional_string(value)
    if text is not None and text not in items:
        items.append(text)


def _extend_unique(items: list[str], values: Any) -> None:
    if not isinstance(values, Iterable) or isinstance(values, (str, bytes)):
        return
    for value in values:
        _append_unique(items, value)


def _limited_string(value: Any) -> str | None:
    text = _optional_string(value)
    if text is None:
        return None
    return text[:TRACE_SUMMARY_REQUEST_ID_MAX_LENGTH]


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
