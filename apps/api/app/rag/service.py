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
    KnowledgeDocument,
    KnowledgeIndexStatus,
    KnowledgeResource,
    RAGFoundationResult,
    RetrievalQuerySummary,
    RetrievalResultSummary,
)
from app.traceability import TRACE_TYPE_RAG_EVIDENCE, TraceabilityRecord, TraceabilityStatus

DEFAULT_TOP_K = 3
DEFAULT_CHUNK_TOKEN_LIMIT = 48
MAX_QUERY_SUMMARY_LENGTH = 120
VISIBILITY_FILTER_OWNER_OR_PUBLIC = "owner_or_public"

EMPTY_REASON_NO_RESULT = "no_result"
EMPTY_REASON_PERMISSION_FILTERED = "permission_filtered_empty"
EMPTY_REASON_RAG_UNAVAILABLE = "rag_unavailable"
EMPTY_REASON_INDEX_PENDING = "index_pending"
EMPTY_REASON_INDEX_FAILED = "index_failed"

SAFE_MESSAGE_NO_RESULT = "当前检索没有命中可引用资料。"
SAFE_MESSAGE_PERMISSION_FILTERED = "当前可见范围内没有可引用资料。"
SAFE_MESSAGE_RAG_UNAVAILABLE = "RAG 服务暂不可用，主链路可继续。"
SAFE_MESSAGE_INDEX_PENDING = "资料索引尚未完成，主链路可继续。"
SAFE_MESSAGE_INDEX_FAILED = "资料索引失败，暂不能引用。"


class RAGUnavailableError(RuntimeError):
    """RAG adapter 暂不可用。"""


class RAGRetrievalAdapter(Protocol):
    """RAG 检索 adapter 的最小协议。"""

    def search(self, query_summary: RetrievalQuerySummary) -> Sequence[KnowledgeResource]:
        """根据脱敏 query summary 返回候选知识资源。"""


class RAGPersistenceRecorder(Protocol):
    """RAG 检索结果持久化 adapter 的最小协议。"""

    def create_retrieval_record(
        self,
        *,
        owner_id: str,
        query_summary: RetrievalQuerySummary,
        result: RAGFoundationResult,
        trace_ref: str | None,
        request_id: str,
        operation_id: str,
        session_ref: str | None = None,
        turn_ref: str | None = None,
        answer_ref: str | None = None,
    ) -> dict[str, object]:
        """保存一次 retrieval 的安全摘要。"""


class InMemoryRAGAdapter:
    """面向 RAG foundation 测试的内存 adapter skeleton。"""

    def __init__(self, *, resources: Iterable[KnowledgeResource], available: bool = True) -> None:
        self._resources = tuple(resources)
        self._available = available

    @classmethod
    def from_documents(
        cls,
        *,
        documents: Iterable[KnowledgeDocument],
        chunk_token_limit: int = DEFAULT_CHUNK_TOKEN_LIMIT,
        available: bool = True,
    ) -> "InMemoryRAGAdapter":
        """从最小文档输入构建内存 chunk index。"""
        resources: list[KnowledgeResource] = []
        for document in documents:
            resources.extend(chunk_document(document, max_tokens=chunk_token_limit))
        return cls(resources=resources, available=available)

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
        rag_store: RAGPersistenceRecorder | None = None,
    ) -> None:
        self.adapter = adapter
        self.trace_store = trace_store
        self.rag_store = rag_store

    def retrieve(
        self,
        *,
        actor_id: str,
        query_text: str,
        selected_resource_ids: Iterable[str] | None = None,
        evidence_target: EvidenceTarget = EvidenceTarget.REVIEW,
        top_k: int = DEFAULT_TOP_K,
        trigger: str = "interview",
        session_ref: str | None = None,
        turn_ref: str | None = None,
        answer_ref: str | None = None,
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
            self._record_result(
                actor_id=actor_id,
                result=result,
                trigger=trigger,
                session_ref=session_ref,
                turn_ref=turn_ref,
                answer_ref=answer_ref,
            )
            return result

        visible_resources = tuple(resource for resource in candidates if resource.is_visible_to(actor_id))
        permission_filtered_count = len(candidates) - len(visible_resources)
        indexed_resources = tuple(resource for resource in visible_resources if _is_indexed(resource))

        if not indexed_resources:
            if visible_resources:
                reason, safe_message, retryable = _index_gap(visible_resources)
            else:
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
                retryable = False
            result = _gap_result(
                query_summary=query_summary,
                reason=reason,
                safe_message=safe_message,
                retryable=retryable,
                permission_filtered_count=permission_filtered_count,
            )
            self._record_result(
                actor_id=actor_id,
                result=result,
                trigger=trigger,
                session_ref=session_ref,
                turn_ref=turn_ref,
                answer_ref=answer_ref,
            )
            return result

        selected_hits = indexed_resources[: query_summary.top_k]

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
            self._record_result(
                actor_id=actor_id,
                result=result,
                trigger=trigger,
                session_ref=session_ref,
                turn_ref=turn_ref,
                answer_ref=answer_ref,
            )
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
        self._record_result(
            actor_id=actor_id,
            result=result,
            trigger=trigger,
            session_ref=session_ref,
            turn_ref=turn_ref,
            answer_ref=answer_ref,
        )
        return result

    def _record_result(
        self,
        *,
        actor_id: str,
        result: RAGFoundationResult,
        trigger: str,
        session_ref: str | None,
        turn_ref: str | None,
        answer_ref: str | None,
    ) -> None:
        trace = self._record_trace(
            actor_id=actor_id,
            result=result,
            trigger=trigger,
            session_ref=session_ref,
            turn_ref=turn_ref,
            answer_ref=answer_ref,
        )
        if self.rag_store is None:
            return

        request_id = str(trace["request_id"]) if trace is not None else f"rag-{uuid4().hex}"
        operation_id = str(trace["operation_id"]) if trace is not None else f"rag.retrieve:{trigger}"
        trace_ref = str(trace["id"]) if trace is not None else None
        self.rag_store.create_retrieval_record(
            owner_id=actor_id,
            query_summary=result.query_summary,
            result=result,
            trace_ref=trace_ref,
            request_id=request_id,
            operation_id=operation_id,
            session_ref=session_ref,
            turn_ref=turn_ref,
            answer_ref=answer_ref,
        )

    def _record_trace(
        self,
        *,
        actor_id: str,
        result: RAGFoundationResult,
        trigger: str,
        session_ref: str | None,
        turn_ref: str | None,
        answer_ref: str | None,
    ) -> dict[str, object] | None:
        if self.trace_store is None:
            return None

        gap_reason = result.evidence_gap.reason if result.evidence_gap is not None else None
        status = TraceabilityStatus.COMPLETED
        if result.result_summary.retryable:
            status = TraceabilityStatus.RETRYABLE
        elif result.degraded:
            status = TraceabilityStatus.DEGRADED

        return self.trace_store.create_trace(
            TraceabilityRecord(
                owner_id=actor_id,
                trace_type=TRACE_TYPE_RAG_EVIDENCE,
                status=status,
                request_id=f"rag-{uuid4().hex}",
                operation_id=f"rag.retrieve:{trigger}",
                session_ref=session_ref,
                turn_ref=turn_ref,
                answer_ref=answer_ref,
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
                    "gap_reason": gap_reason,
                },
            )
        )


def chunk_document(
    document: KnowledgeDocument,
    *,
    max_tokens: int = DEFAULT_CHUNK_TOKEN_LIMIT,
) -> list[KnowledgeResource]:
    """把最小文档输入切成稳定 chunk resources。"""
    limit = max(max_tokens, 1)
    if document.index_status != KnowledgeIndexStatus.INDEXED:
        return [_resource_from_unindexed_document(document)]

    spans = _word_spans(document.content)
    if not spans:
        return []

    chunks: list[KnowledgeResource] = []
    for chunk_index, start in enumerate(range(0, len(spans), limit)):
        chunk_spans = spans[start : start + limit]
        content_summary = " ".join(token for token, _, _ in chunk_spans)
        chunks.append(
            KnowledgeResource(
                resource_id=document.document_id,
                owner_id=document.owner_id,
                visibility=document.visibility,
                source_type=document.source_type,
                source_label=document.source_label,
                content_summary=content_summary,
                chunk_ref=f"{document.document_id}:chunk-{chunk_index}",
                source_version=document.source_version,
                index_status=KnowledgeIndexStatus.INDEXED,
                chunk_index=chunk_index,
                start_offset=chunk_spans[0][1],
                end_offset=chunk_spans[-1][2],
            )
        )
    return chunks


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
        chunk_index=resource.chunk_index,
        start_offset=resource.start_offset,
        end_offset=resource.end_offset,
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


def _resource_from_unindexed_document(document: KnowledgeDocument) -> KnowledgeResource:
    return KnowledgeResource(
        resource_id=document.document_id,
        owner_id=document.owner_id,
        visibility=document.visibility,
        source_type=document.source_type,
        source_label=document.source_label,
        content_summary="",
        chunk_ref=f"{document.document_id}:index-{document.index_status.value}",
        source_version=document.source_version,
        index_status=document.index_status,
        chunk_index=-1,
        start_offset=0,
        end_offset=0,
        failure_reason=document.failure_reason,
    )


def _is_indexed(resource: KnowledgeResource) -> bool:
    return resource.index_status == KnowledgeIndexStatus.INDEXED


def _index_gap(resources: Sequence[KnowledgeResource]) -> tuple[str, str, bool]:
    if any(resource.index_status == KnowledgeIndexStatus.PENDING for resource in resources):
        return EMPTY_REASON_INDEX_PENDING, SAFE_MESSAGE_INDEX_PENDING, True
    return EMPTY_REASON_INDEX_FAILED, SAFE_MESSAGE_INDEX_FAILED, False


def _word_spans(content: str) -> list[tuple[str, int, int]]:
    spans: list[tuple[str, int, int]] = []
    offset = 0
    for token in str(content).split():
        start = str(content).find(token, offset)
        if start < 0:
            start = offset
        end = start + len(token)
        spans.append((token, start, end))
        offset = end
    return spans
