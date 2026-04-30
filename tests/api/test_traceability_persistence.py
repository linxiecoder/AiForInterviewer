"""ST13_20 R1 数据追踪持久化测试。"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from tools.testing.temp_artifacts import ManagedTempArtifacts

API_ROOT = Path(__file__).resolve().parents[2] / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.persistence import TraceabilityStore  # noqa: E402
from app.traceability import (  # noqa: E402
    TRACE_TYPE_INTERVIEW,
    TRACE_TYPE_RAG_EVIDENCE,
    TRACE_TYPE_REVIEW_EXPORT,
    TraceabilityRecord,
    TraceabilityStatus,
)


@pytest.fixture()
def store() -> Iterator[TraceabilityStore]:
    artifacts = ManagedTempArtifacts(test_id="tests.api.test_traceability_persistence")
    database_dir = artifacts.make_temp_dir("database")
    trace_store = TraceabilityStore(str(database_dir / "traceability.sqlite3"))
    trace_store.initialize()
    try:
        yield trace_store
    finally:
        artifacts.cleanup()


def test_create_and_read_interview_trace_relationships(store: TraceabilityStore) -> None:
    saved = store.create_trace(
        TraceabilityRecord(
            owner_id="user-r1",
            trace_type=TRACE_TYPE_INTERVIEW,
            status=TraceabilityStatus.COMPLETED,
            request_id="req-interview-1",
            operation_id="op-interview-1",
            job_ref="job-1",
            resume_ref="resume-1",
            session_ref="session-1",
            turn_ref="turn-1",
            answer_ref="answer-1",
            source_snapshot_ref="snapshot-job-resume-1",
            schema_version=1,
            content_version="interview-v1",
        )
    )

    loaded = store.get_trace(saved["id"])

    assert loaded is not None
    assert loaded["trace_type"] == TRACE_TYPE_INTERVIEW
    assert loaded["status"] == TraceabilityStatus.COMPLETED
    assert loaded["request_id"] == "req-interview-1"
    assert loaded["operation_id"] == "op-interview-1"
    assert loaded["job_ref"] == "job-1"
    assert loaded["resume_ref"] == "resume-1"
    assert loaded["session_ref"] == "session-1"
    assert loaded["turn_ref"] == "turn-1"
    assert loaded["answer_ref"] == "answer-1"
    assert loaded["source_snapshot_ref"] == "snapshot-job-resume-1"
    assert loaded["schema_version"] == 1
    assert loaded["content_version"] == "interview-v1"


def test_save_rag_citation_and_evidence_gap_references(store: TraceabilityStore) -> None:
    saved = store.create_trace(
        TraceabilityRecord(
            owner_id="user-r1",
            trace_type=TRACE_TYPE_RAG_EVIDENCE,
            status=TraceabilityStatus.DEGRADED,
            request_id="req-rag-1",
            operation_id="op-rag-1",
            session_ref="session-1",
            turn_ref="turn-1",
            retrieval_query_ref="retrieval-query-1",
            retrieval_result_ref="retrieval-result-1",
            citation_refs=("citation-1", "citation-2"),
            evidence_gap_ref="gap-low-confidence-1",
            source_snapshot_ref="rag-source-snapshot-1",
            metadata={"gap_reason": "low_confidence"},
        )
    )

    loaded = store.get_trace(saved["id"])

    assert loaded is not None
    assert loaded["status"] == TraceabilityStatus.DEGRADED
    assert loaded["retrieval_query_ref"] == "retrieval-query-1"
    assert loaded["retrieval_result_ref"] == "retrieval-result-1"
    assert loaded["citation_refs"] == ["citation-1", "citation-2"]
    assert loaded["evidence_gap_ref"] == "gap-low-confidence-1"
    assert loaded["metadata"] == {"gap_reason": "low_confidence"}


def test_save_score_review_and_export_references(store: TraceabilityStore) -> None:
    saved = store.create_trace(
        TraceabilityRecord(
            owner_id="user-r1",
            trace_type=TRACE_TYPE_REVIEW_EXPORT,
            status=TraceabilityStatus.COMPLETED,
            request_id="req-review-1",
            operation_id="op-review-1",
            session_ref="session-1",
            answer_ref="answer-1",
            score_ref="score-1",
            review_ref="review-1",
            export_ref="export-1",
            evidence_refs=("evidence-1", "gap-low-confidence-1"),
            source_snapshot_ref="review-source-snapshot-1",
            content_version="markdown-v1",
        )
    )

    loaded = store.get_trace(saved["id"])

    assert loaded is not None
    assert loaded["score_ref"] == "score-1"
    assert loaded["review_ref"] == "review-1"
    assert loaded["export_ref"] == "export-1"
    assert loaded["evidence_refs"] == ["evidence-1", "gap-low-confidence-1"]
    assert loaded["source_snapshot_ref"] == "review-source-snapshot-1"
    assert loaded["content_version"] == "markdown-v1"


@pytest.mark.parametrize(
    ("status", "expected_retryable"),
    [
        (TraceabilityStatus.FAILED, False),
        (TraceabilityStatus.DEGRADED, False),
        (TraceabilityStatus.RETRYABLE, True),
        (TraceabilityStatus.ARCHIVED, False),
    ],
)
def test_failed_and_degraded_statuses_are_persisted(
    store: TraceabilityStore,
    status: TraceabilityStatus,
    expected_retryable: bool,
) -> None:
    saved = store.create_trace(
        TraceabilityRecord(
            owner_id="user-r1",
            trace_type=TRACE_TYPE_INTERVIEW,
            status=status,
            request_id=f"req-{status}",
            operation_id=f"op-{status}",
            session_ref=f"session-{status}",
            retryable=expected_retryable,
            failure_reason=f"{status}_reason",
        )
    )

    loaded = store.get_trace(saved["id"])

    assert loaded is not None
    assert loaded["status"] == status
    assert loaded["retryable"] is expected_retryable
    assert loaded["failure_reason"] == f"{status}_reason"
