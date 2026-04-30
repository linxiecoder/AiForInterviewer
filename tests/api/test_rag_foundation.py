"""ST13_10 RAG foundation 最小行为测试。"""

from __future__ import annotations

import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[2] / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.rag.models import (  # noqa: E402
    EvidenceTarget,
    KnowledgeResource,
    KnowledgeVisibility,
    RAGSourceType,
)
from app.rag.service import InMemoryRAGAdapter, RAGService  # noqa: E402


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
