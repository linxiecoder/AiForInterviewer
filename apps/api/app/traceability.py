"""ST13_20 R1 数据追踪领域模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

TRACE_TYPE_INTERVIEW = "interview"
TRACE_TYPE_RAG_EVIDENCE = "rag_evidence"
TRACE_TYPE_REVIEW_EXPORT = "review_export"


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
