"""ST13_10 RAG foundation 服务边界与 adapter skeleton。"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Protocol
from uuid import uuid4

from app.persistence import TraceabilityStore
from app.rag.models import (
    Citation,
    EvidenceGap,
    EvidenceItem,
    EvidenceTarget,
    KnowledgeResource,
    RAGFoundationResult,
    RetrievalQuerySummary,
    RetrievalResultSummary,
)
from app.traceability import TRACE_TYPE_RAG_EVIDENCE, TraceabilityRecord, TraceabilityStatus

DEFAULT_TOP_K = 3
MAX_QUERY_SUMMARY_LENGTH = 120
VISIBILITY_FILTER_OWNER_OR_PUBLIC = "owner_or_public"

EMPTY_REASON_NO_RESULT = "no_result"
EMPTY_REASON_PERMISSION_FILTERED = "permission_filtered_empty"
EMPTY_REASON_RAG_UNAVAILABLE = "rag_unavailable"

SAFE_MESSAGE_NO_RESULT = "当前检索没有命中可引用资料。"
SAFE_MESSAGE_PERMISSION_FILTERED = "当前可见范围内没有可引用资料。"
SAFE_MESSAGE_RAG_UNAVAILABLE = "RAG 服务暂不可用，主链路可继续。"


class RAGUnavailableError(RuntimeError):
    """RAG adapter 暂不可用。"""


class RAGRetrievalAdapter(Protocol):
    """RAG 检索 adapter 的最小协议。"""

    def search(self, query_summary: RetrievalQuerySummary) -> Sequence[KnowledgeResource]:
        """根据脱敏 query summary 返回候选知识资源。"""


class InMemoryRAGAdapter:
    """面向 RAG foundation 测试的内存 adapter skeleton。"""

    def __init__(self, *, resources: Iterable[KnowledgeResource], available: bool = True) -> None:
        self._resources = tuple(resources)
        self._available = available

    def search(self, query_summary: RetrievalQuerySummary) -> Sequence[KnowledgeResource]:
        """返回满足 selected ids 或 query token 的候选资源。"""
        if not self._available:
            raise RAGUnavailableError("rag adapter unavailable")

        selected_ids = set(query_summary.selected_resource_ids)
        if selected_ids:
            return [resource for resource in self._resources if resource.resource_id in selected_ids]

        tokens = _query_tokens(query_summary.query_summary)
        if not tokens:
            return list(self._resources[: query_summary.top_k])
        return [
            resource
            for resource in self._resources
            if any(token in resource.content_summary.lower() for token in tokens)
        ][: query_summary.top_k]


class RAGService:
    """R1 RAG foundation 的纯服务边界。"""

    def __init__(
        self,
        *,
        adapter: RAGRetrievalAdapter,
        trace_store: TraceabilityStore | None = None,
    ) -> None:
        self.adapter = adapter
        self.trace_store = trace_store

    def retrieve(
        self,
        *,
        actor_id: str,
        query_text: str,
        selected_resource_ids: Iterable[str] | None = None,
        evidence_target: EvidenceTarget = EvidenceTarget.REVIEW,
        top_k: int = DEFAULT_TOP_K,
        trigger: str = "interview",
    ) -> RAGFoundationResult:
        """执行最小检索并返回 citation、evidence 和 evidence gap。"""
        query_summary = RetrievalQuerySummary(
            query_summary=_summarize_query(query_text),
            actor_id=actor_id,
            selected_resource_ids=tuple(selected_resource_ids or ()),
            top_k=max(top_k, 1),
            trigger=trigger,
            visibility_filter=VISIBILITY_FILTER_OWNER_OR_PUBLIC,
        )

        try:
            candidates = tuple(self.adapter.search(query_summary))
        except RAGUnavailableError:
            result = _gap_result(
                query_summary=query_summary,
                reason=EMPTY_REASON_RAG_UNAVAILABLE,
                safe_message=SAFE_MESSAGE_RAG_UNAVAILABLE,
                retryable=True,
                permission_filtered_count=0,
            )
            self._record_trace(actor_id=actor_id, result=result, trigger=trigger)
            return result

        visible_resources = tuple(resource for resource in candidates if resource.is_visible_to(actor_id))
        permission_filtered_count = len(candidates) - len(visible_resources)
        selected_hits = visible_resources[: query_summary.top_k]

        if not selected_hits:
            reason = (
                EMPTY_REASON_PERMISSION_FILTERED
                if candidates and permission_filtered_count == len(candidates)
                else EMPTY_REASON_NO_RESULT
            )
            safe_message = (
                SAFE_MESSAGE_PERMISSION_FILTERED
                if reason == EMPTY_REASON_PERMISSION_FILTERED
                else SAFE_MESSAGE_NO_RESULT
            )
            result = _gap_result(
                query_summary=query_summary,
                reason=reason,
                safe_message=safe_message,
                retryable=False,
                permission_filtered_count=permission_filtered_count,
            )
            self._record_trace(actor_id=actor_id, result=result, trigger=trigger)
            return result

        citations = [_citation_from_resource(resource) for resource in selected_hits]
        evidence_items = [
            _evidence_from_citation(citation=citation, used_by=evidence_target)
            for citation in citations
        ]
        evidence_refs = [item.evidence_ref for item in evidence_items]
        result = RAGFoundationResult(
            query_summary=query_summary,
            result_summary=RetrievalResultSummary(
                hit_count=len(citations),
                hit_summary=tuple(citation.snippet_summary for citation in citations),
                empty_reason=None,
                degraded=False,
                retryable=False,
            ),
            citations=citations,
            evidence_items=evidence_items,
            evidence_gap=None,
            downstream_refs=_downstream_refs(evidence_target=evidence_target, evidence_refs=evidence_refs),
            permission_filtered_count=permission_filtered_count,
            degraded=False,
        )
        self._record_trace(actor_id=actor_id, result=result, trigger=trigger)
        return result

    def _record_trace(
        self,
        *,
        actor_id: str,
        result: RAGFoundationResult,
        trigger: str,
    ) -> None:
        if self.trace_store is None:
            return

        gap_reason = result.evidence_gap.reason if result.evidence_gap is not None else None
        status = TraceabilityStatus.COMPLETED
        if result.result_summary.retryable:
            status = TraceabilityStatus.RETRYABLE
        elif result.degraded:
            status = TraceabilityStatus.DEGRADED

        self.trace_store.create_trace(
            TraceabilityRecord(
                owner_id=actor_id,
                trace_type=TRACE_TYPE_RAG_EVIDENCE,
                status=status,
                request_id=f"rag-{uuid4().hex}",
                operation_id=f"rag.retrieve:{trigger}",
                retrieval_query_ref=f"rag-query:{result.query_summary.query_summary}",
                retrieval_result_ref=(
                    f"rag-result:{result.result_summary.hit_count}:{gap_reason or 'hit'}"
                ),
                citation_refs=tuple(citation.citation_ref for citation in result.citations),
                evidence_refs=tuple(item.evidence_ref for item in result.evidence_items),
                evidence_gap_ref=f"gap:{gap_reason}" if gap_reason else None,
                source_snapshot_ref=_source_snapshot_ref(result),
                retryable=result.result_summary.retryable,
                failure_reason=gap_reason,
                content_version="r1-rag-trace-v1",
                metadata={
                    "operation": "rag.retrieve",
                    "trigger": trigger,
                    "hit_count": result.result_summary.hit_count,
                    "permission_filtered_count": result.permission_filtered_count,
                    "degraded": result.degraded,
                },
            )
        )


def _gap_result(
    *,
    query_summary: RetrievalQuerySummary,
    reason: str,
    safe_message: str,
    retryable: bool,
    permission_filtered_count: int,
) -> RAGFoundationResult:
    gap = EvidenceGap(reason=reason, safe_message=safe_message, retryable=retryable)
    return RAGFoundationResult(
        query_summary=query_summary,
        result_summary=RetrievalResultSummary(
            hit_count=0,
            hit_summary=(),
            empty_reason=reason,
            degraded=True,
            retryable=retryable,
        ),
        citations=[],
        evidence_items=[],
        evidence_gap=gap,
        downstream_refs=_downstream_refs(evidence_target=None, evidence_refs=[]),
        permission_filtered_count=permission_filtered_count,
        degraded=True,
    )


def _citation_from_resource(resource: KnowledgeResource) -> Citation:
    citation_ref = f"citation:{resource.resource_id}:{resource.chunk_ref}"
    return Citation(
        citation_ref=citation_ref,
        source_ref=resource.resource_id,
        chunk_ref=resource.chunk_ref,
        source_label=resource.source_label,
        source_type=resource.source_type,
        snippet_summary=resource.content_summary,
        source_version=resource.source_version,
        visibility_snapshot=resource.visibility_snapshot(),
    )


def _evidence_from_citation(*, citation: Citation, used_by: EvidenceTarget) -> EvidenceItem:
    return EvidenceItem(
        evidence_ref=f"evidence:{citation.source_ref}:{citation.chunk_ref}",
        evidence_summary=citation.snippet_summary,
        citation_refs=(citation.citation_ref,),
        confidence_label="medium",
        used_by=used_by,
        source_snapshot_ref=f"{citation.source_ref}@{citation.source_version}",
    )


def _downstream_refs(
    *,
    evidence_target: EvidenceTarget | None,
    evidence_refs: list[str],
) -> dict[str, list[str]]:
    refs = {target.value: [] for target in EvidenceTarget}
    if evidence_target is not None:
        refs[evidence_target.value] = list(evidence_refs)
    return refs


def _source_snapshot_ref(result: RAGFoundationResult) -> str | None:
    refs = [item.source_snapshot_ref for item in result.evidence_items]
    return ",".join(refs) if refs else None


def _summarize_query(query_text: str) -> str:
    normalized = " ".join(str(query_text).split())
    if len(normalized) <= MAX_QUERY_SUMMARY_LENGTH:
        return normalized
    return normalized[: MAX_QUERY_SUMMARY_LENGTH - 3].rstrip() + "..."


def _query_tokens(query_summary: str) -> tuple[str, ...]:
    return tuple(
        token
        for token in query_summary.lower().replace("/", " ").replace("-", " ").split()
        if len(token) >= 3
    )
