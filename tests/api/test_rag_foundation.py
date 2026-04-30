"""ST13_10 RAG foundation 最小行为测试。"""

from __future__ import annotations

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[2] / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.rag.models import (  # noqa: E402
    EvidenceTarget,
    KnowledgeDocument,
    KnowledgeIndexStatus,
    KnowledgeResource,
    KnowledgeVisibility,
    RAGSourceType,
)
from app.rag.service import InMemoryRAGAdapter, RAGService, chunk_document  # noqa: E402


def test_document_chunking_produces_stable_chunk_refs_and_positions() -> None:
    """同一文档输入应产生稳定 chunk ref、chunk index 和位置摘要。"""
    document = KnowledgeDocument(
        document_id="doc-rag",
        owner_id="owner-a",
        visibility=KnowledgeVisibility.PRIVATE,
        source_type=RAGSourceType.PRIVATE_DOCUMENT,
        source_label="RAG notes",
        content="alpha beta gamma delta epsilon zeta eta theta iota",
        source_version="v1",
    )

    chunks = chunk_document(document, max_tokens=4)

    assert [chunk.chunk_ref for chunk in chunks] == [
        "doc-rag:chunk-0",
        "doc-rag:chunk-1",
        "doc-rag:chunk-2",
    ]
    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]
    assert [chunk.content_summary for chunk in chunks] == [
        "alpha beta gamma delta",
        "epsilon zeta eta theta",
        "iota",
    ]
    assert chunks[0].start_offset == 0
    assert chunks[0].end_offset == len("alpha beta gamma delta")
    assert all(chunk.index_status == KnowledgeIndexStatus.INDEXED for chunk in chunks)


def test_indexed_document_keyword_retrieval_returns_chunk_citation() -> None:
    """已 indexed 的文档应可通过 keyword / substring retrieval 命中并返回 citation。"""
    service = RAGService(
        adapter=InMemoryRAGAdapter.from_documents(
            documents=[
                KnowledgeDocument(
                    document_id="doc-rag",
                    owner_id="owner-a",
                    visibility=KnowledgeVisibility.PRIVATE,
                    source_type=RAGSourceType.PRIVATE_DOCUMENT,
                    source_label="RAG notes",
                    content="FastAPI traceability retrieval citations need stable evidence refs",
                    source_version="v1",
                )
            ],
            chunk_token_limit=5,
        )
    )

    result = service.retrieve(
        actor_id="owner-a",
        query_text="traceability citation",
        evidence_target=EvidenceTarget.REVIEW,
    )

    assert result.degraded is False
    assert result.result_summary.hit_count == 1
    assert result.citations[0].source_ref == "doc-rag"
    assert result.citations[0].chunk_ref == "doc-rag:chunk-0"
    assert result.citations[0].chunk_index == 0
    assert result.evidence_items[0].citation_refs == (result.citations[0].citation_ref,)
    assert result.evidence_items[0].confidence_label == "medium"


def test_no_keyword_hit_returns_evidence_gap() -> None:
    """检索无命中时应返回明确 evidence gap，而不是伪造 citation。"""
    service = RAGService(
        adapter=InMemoryRAGAdapter.from_documents(
            documents=[
                KnowledgeDocument(
                    document_id="doc-rag",
                    owner_id="owner-a",
                    visibility=KnowledgeVisibility.PRIVATE,
                    source_type=RAGSourceType.PRIVATE_DOCUMENT,
                    source_label="RAG notes",
                    content="FastAPI traceability retrieval citations",
                    source_version="v1",
                )
            ]
        )
    )

    result = service.retrieve(actor_id="owner-a", query_text="postgres migration")

    assert result.degraded is True
    assert result.result_summary.empty_reason == "no_result"
    assert result.evidence_gap is not None
    assert result.evidence_gap.reason == "no_result"
    assert result.evidence_gap.safe_message == "当前检索没有命中可引用资料。"
    assert result.citations == []


def test_pending_and_failed_index_status_return_evidence_gap() -> None:
    """pending / failed 索引状态应返回可降级 evidence gap。"""
    service = RAGService(
        adapter=InMemoryRAGAdapter.from_documents(
            documents=[
                KnowledgeDocument(
                    document_id="doc-pending",
                    owner_id="owner-a",
                    visibility=KnowledgeVisibility.PRIVATE,
                    source_type=RAGSourceType.PRIVATE_DOCUMENT,
                    source_label="Pending notes",
                    content="not indexed yet",
                    source_version="v1",
                    index_status=KnowledgeIndexStatus.PENDING,
                ),
                KnowledgeDocument(
                    document_id="doc-failed",
                    owner_id="owner-a",
                    visibility=KnowledgeVisibility.PRIVATE,
                    source_type=RAGSourceType.PRIVATE_DOCUMENT,
                    source_label="Failed notes",
                    content="parse failed",
                    source_version="v1",
                    index_status=KnowledgeIndexStatus.FAILED,
                    failure_reason="parse_failed",
                ),
            ]
        )
    )

    pending = service.retrieve(
        actor_id="owner-a",
        query_text="not indexed",
        selected_resource_ids=["doc-pending"],
    )
    failed = service.retrieve(
        actor_id="owner-a",
        query_text="parse failed",
        selected_resource_ids=["doc-failed"],
    )

    assert pending.degraded is True
    assert pending.evidence_gap is not None
    assert pending.evidence_gap.reason == "index_pending"
    assert pending.evidence_gap.retryable is True
    assert failed.degraded is True
    assert failed.evidence_gap is not None
    assert failed.evidence_gap.reason == "index_failed"
    assert failed.evidence_gap.retryable is False


def test_unavailable_adapter_returns_retryable_degraded_gap() -> None:
    """RAG adapter 不可用时主链路应可继续，并返回 retryable degraded gap。"""
    service = RAGService(adapter=InMemoryRAGAdapter(resources=(), available=False))

    result = service.retrieve(actor_id="owner-a", query_text="anything")

    assert result.degraded is True
    assert result.evidence_gap is not None
    assert result.evidence_gap.reason == "rag_unavailable"
    assert result.evidence_gap.retryable is True
    assert result.result_summary.retryable is True


def test_rag_foundation_returns_visible_citation_and_evidence_refs() -> None:
    """命中可见资料时应返回 citation、evidence item 和下游 evidence refs。"""
    service = RAGService(
        adapter=InMemoryRAGAdapter(
            resources=[
                KnowledgeResource(
                    resource_id="doc-private",
                    owner_id="owner-a",
                    visibility=KnowledgeVisibility.PRIVATE,
                    source_type=RAGSourceType.PRIVATE_DOCUMENT,
                    source_label="项目经历材料",
                    content_summary="FastAPI 服务边界和测试策略经验",
                    chunk_ref="chunk-1",
                    source_version="v1",
                ),
                KnowledgeResource(
                    resource_id="doc-hidden",
                    owner_id="owner-b",
                    visibility=KnowledgeVisibility.PRIVATE,
                    source_type=RAGSourceType.PRIVATE_DOCUMENT,
                    source_label="其他用户材料",
                    content_summary="不可见资源不应泄露",
                    chunk_ref="chunk-hidden",
                    source_version="v1",
                ),
            ]
        )
    )

    result = service.retrieve(
        actor_id="owner-a",
        query_text="FastAPI service testing",
        selected_resource_ids=["doc-private", "doc-hidden"],
        evidence_target=EvidenceTarget.REVIEW,
        top_k=5,
    )

    assert result.degraded is False
    assert result.result_summary.hit_count == 1
    assert result.query_summary.top_k == 5
    assert result.query_summary.visibility_filter == "owner_or_public"
    assert result.citations[0].source_ref == "doc-private"
    assert result.citations[0].visibility_snapshot == "private:owner-a"
    assert result.evidence_items[0].evidence_ref == "evidence:doc-private:chunk-1"
    assert result.evidence_items[0].used_by == EvidenceTarget.REVIEW
    assert result.downstream_refs["review"] == ["evidence:doc-private:chunk-1"]
    assert result.permission_filtered_count == 1


def test_rag_foundation_marks_permission_filtered_empty_as_degraded_gap() -> None:
    """权限过滤后为空时应返回 degraded evidence gap，不泄露不可见资源。"""
    service = RAGService(
        adapter=InMemoryRAGAdapter(
            resources=[
                KnowledgeResource(
                    resource_id="doc-hidden",
                    owner_id="owner-b",
                    visibility=KnowledgeVisibility.PRIVATE,
                    source_type=RAGSourceType.PRIVATE_DOCUMENT,
                    source_label="其他用户材料",
                    content_summary="不可见资源不应泄露",
                    chunk_ref="chunk-hidden",
                    source_version="v1",
                )
            ]
        )
    )

    result = service.retrieve(
        actor_id="owner-a",
        query_text="testing strategy",
        selected_resource_ids=["doc-hidden"],
        evidence_target=EvidenceTarget.SCORE,
    )

    assert result.degraded is True
    assert result.result_summary.hit_count == 0
    assert result.result_summary.empty_reason == "permission_filtered_empty"
    assert result.evidence_gap.reason == "permission_filtered_empty"
    assert result.evidence_gap.retryable is False
    assert result.evidence_gap.safe_message == "当前可见范围内没有可引用资料。"
    assert result.permission_filtered_count == 1
    assert result.citations == []
    assert result.downstream_refs["score"] == []
