"""ST13_20 R1 RAG 最小持久化测试。"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from tools.testing.temp_artifacts import ManagedTempArtifacts

API_ROOT = Path(__file__).resolve().parents[2] / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.persistence import RAGPersistenceStore, TraceabilityStore  # noqa: E402
from app.rag.models import (  # noqa: E402
    EvidenceTarget,
    KnowledgeDocument,
    KnowledgeIndexStatus,
    KnowledgeVisibility,
    RAGSourceType,
)
from app.rag.service import RAGService, chunk_document  # noqa: E402
from app.traceability import build_trace_summary  # noqa: E402


@pytest.fixture()
def stores() -> Iterator[tuple[RAGPersistenceStore, TraceabilityStore]]:
    artifacts = ManagedTempArtifacts(test_id="tests.api.test_rag_persistence")
    database_dir = artifacts.make_temp_dir("database")
    database_path = str(database_dir / "rag-persistence.sqlite3")
    rag_store = RAGPersistenceStore(database_path)
    trace_store = TraceabilityStore(database_path)
    rag_store.initialize()
    trace_store.initialize()
    try:
        yield rag_store, trace_store
    finally:
        artifacts.cleanup()


def test_save_and_read_knowledge_document_chunks_and_index_statuses(
    stores: tuple[RAGPersistenceStore, TraceabilityStore],
) -> None:
    """document、chunk 与 pending/indexed/failed 状态应可稳定读回。"""
    rag_store, _trace_store = stores
    indexed = KnowledgeDocument(
        document_id="doc-indexed",
        owner_id="owner-a",
        visibility=KnowledgeVisibility.PRIVATE,
        source_type=RAGSourceType.PRIVATE_DOCUMENT,
        source_label="Indexed notes",
        content="alpha beta gamma delta epsilon zeta eta theta iota",
        source_version="v1",
    )
    pending = KnowledgeDocument(
        document_id="doc-pending",
        owner_id="owner-a",
        visibility=KnowledgeVisibility.PRIVATE,
        source_type=RAGSourceType.PRIVATE_DOCUMENT,
        source_label="Pending notes",
        content="pending content",
        source_version="v1",
        index_status=KnowledgeIndexStatus.PENDING,
    )
    failed = KnowledgeDocument(
        document_id="doc-failed",
        owner_id="owner-a",
        visibility=KnowledgeVisibility.PRIVATE,
        source_type=RAGSourceType.PRIVATE_DOCUMENT,
        source_label="Failed notes",
        content="failed content",
        source_version="v1",
        index_status=KnowledgeIndexStatus.FAILED,
        failure_reason="parse_failed",
    )

    rag_store.save_document(indexed, chunks=chunk_document(indexed, max_tokens=4))
    rag_store.save_document(pending, chunks=chunk_document(pending))
    rag_store.save_document(failed, chunks=chunk_document(failed))

    loaded = rag_store.get_document(owner_id="owner-a", document_id="doc-indexed")
    indexed_chunks = rag_store.list_chunks(owner_id="owner-a", document_id="doc-indexed")
    pending_loaded = rag_store.get_document(owner_id="owner-a", document_id="doc-pending")
    failed_loaded = rag_store.get_document(owner_id="owner-a", document_id="doc-failed")
    failed_chunks = rag_store.list_chunks(owner_id="owner-a", document_id="doc-failed")

    assert loaded is not None
    assert loaded["document_id"] == "doc-indexed"
    assert loaded["index_status"] == KnowledgeIndexStatus.INDEXED
    assert [chunk["chunk_ref"] for chunk in indexed_chunks] == [
        "doc-indexed:chunk-0",
        "doc-indexed:chunk-1",
        "doc-indexed:chunk-2",
    ]
    assert [chunk["chunk_index"] for chunk in indexed_chunks] == [0, 1, 2]
    assert indexed_chunks[0]["content_summary"] == "alpha beta gamma delta"
    assert pending_loaded is not None
    assert pending_loaded["index_status"] == KnowledgeIndexStatus.PENDING
    assert failed_loaded is not None
    assert failed_loaded["index_status"] == KnowledgeIndexStatus.FAILED
    assert failed_loaded["failure_reason"] == "parse_failed"
    assert failed_chunks[0]["index_status"] == KnowledgeIndexStatus.FAILED
    assert failed_chunks[0]["failure_reason"] == "parse_failed"


def test_persisted_retrieval_writes_result_citation_and_trace_summary(
    stores: tuple[RAGPersistenceStore, TraceabilityStore],
) -> None:
    """持久化 adapter 命中后应保存 result、citation，并能被 trace_summary 读取。"""
    rag_store, trace_store = stores
    document = KnowledgeDocument(
        document_id="doc-rag-hit",
        owner_id="owner-a",
        visibility=KnowledgeVisibility.PRIVATE,
        source_type=RAGSourceType.PRIVATE_DOCUMENT,
        source_label="RAG hit notes",
        content="traceability citations evidence refs are durable",
        source_version="v1",
    )
    rag_store.save_document(document, chunks=chunk_document(document))
    service = RAGService(adapter=rag_store, trace_store=trace_store, rag_store=rag_store)

    result = service.retrieve(
        actor_id="owner-a",
        query_text="traceability citation",
        evidence_target=EvidenceTarget.REVIEW,
        trigger="review",
        session_ref="session-hit",
        turn_ref="turn-hit",
        answer_ref="answer-hit",
    )

    records = rag_store.list_retrieval_records(owner_id="owner-a", session_ref="session-hit")
    summary = build_trace_summary(
        trace_store.list_traces(owner_id="owner-a", session_ref="session-hit")
    )

    assert result.result_summary.hit_count == 1
    assert records[0]["trace_ref"] is not None
    assert records[0]["retrieval_query_ref"].startswith("rag-query:")
    assert records[0]["retrieval_result_ref"] == "rag-result:1:hit"
    assert records[0]["citation_refs"] == [result.citations[0].citation_ref]
    assert records[0]["evidence_refs"] == [result.evidence_items[0].evidence_ref]
    assert records[0]["evidence_gap_ref"] is None
    assert records[0]["operation_id"] == "rag.retrieve:review"
    assert summary["rag"]["citation_refs"] == [result.citations[0].citation_ref]
    assert summary["rag"]["evidence_refs"] == [result.evidence_items[0].evidence_ref]
    assert summary["rag"]["evidence_gap_refs"] == []


def test_persisted_retrieval_writes_evidence_gap(
    stores: tuple[RAGPersistenceStore, TraceabilityStore],
) -> None:
    """无命中时应持久化 evidence gap，而不是写入伪 citation。"""
    rag_store, trace_store = stores
    document = KnowledgeDocument(
        document_id="doc-gap",
        owner_id="owner-a",
        visibility=KnowledgeVisibility.PRIVATE,
        source_type=RAGSourceType.PRIVATE_DOCUMENT,
        source_label="Gap notes",
        content="FastAPI traceability citations",
        source_version="v1",
    )
    rag_store.save_document(document, chunks=chunk_document(document))
    service = RAGService(adapter=rag_store, trace_store=trace_store, rag_store=rag_store)

    result = service.retrieve(
        actor_id="owner-a",
        query_text="postgres migration",
        evidence_target=EvidenceTarget.REVIEW,
        trigger="review",
        session_ref="session-gap",
    )

    records = rag_store.list_retrieval_records(owner_id="owner-a", session_ref="session-gap")
    summary = build_trace_summary(
        trace_store.list_traces(owner_id="owner-a", session_ref="session-gap")
    )

    assert result.degraded is True
    assert records[0]["hit_count"] == 0
    assert records[0]["empty_reason"] == "no_result"
    assert records[0]["degraded"] is True
    assert records[0]["citation_refs"] == []
    assert records[0]["evidence_gap_ref"] == "gap:no_result"
    assert summary["rag"]["citation_refs"] == []
    assert summary["rag"]["evidence_gap_refs"] == ["gap:no_result"]


def test_owner_filter_does_not_leak_invisible_document_id(
    stores: tuple[RAGPersistenceStore, TraceabilityStore],
) -> None:
    """权限过滤后为空时，持久化记录与 trace summary 不应泄露不可见 document id。"""
    rag_store, trace_store = stores
    hidden = KnowledgeDocument(
        document_id="doc-hidden-private",
        owner_id="owner-b",
        visibility=KnowledgeVisibility.PRIVATE,
        source_type=RAGSourceType.PRIVATE_DOCUMENT,
        source_label="Hidden notes",
        content="backend persistence evidence",
        source_version="v1",
    )
    rag_store.save_document(hidden, chunks=chunk_document(hidden))
    service = RAGService(adapter=rag_store, trace_store=trace_store, rag_store=rag_store)

    result = service.retrieve(
        actor_id="owner-a",
        query_text="backend persistence evidence",
        selected_resource_ids=("doc-hidden-private",),
        trigger="review",
        session_ref="session-filtered",
    )

    records = rag_store.list_retrieval_records(owner_id="owner-a", session_ref="session-filtered")
    summary = build_trace_summary(
        trace_store.list_traces(owner_id="owner-a", session_ref="session-filtered")
    )

    assert result.result_summary.empty_reason == "permission_filtered_empty"
    assert records[0]["evidence_gap_ref"] == "gap:permission_filtered_empty"
    assert "doc-hidden-private" not in str(records[0])
    assert "doc-hidden-private" not in str(summary)
    assert rag_store.get_document(owner_id="owner-a", document_id="doc-hidden-private") is None
