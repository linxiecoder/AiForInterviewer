"""ST13_10 RAG foundation 内部领域模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class KnowledgeVisibility(StrEnum):
    """知识资源的最小可见性。"""

    PRIVATE = "private"
    PUBLIC = "public"


class RAGSourceType(StrEnum):
    """R1 RAG 最小来源类型。"""

    PRIVATE_DOCUMENT = "private_document"
    PUBLIC_KNOWLEDGE = "public_knowledge"
    JOB = "job"
    RESUME = "resume"
    HISTORY_ANSWER = "history_answer"


class KnowledgeIndexStatus(StrEnum):
    """R1 RAG 最小索引状态。"""

    PENDING = "pending"
    INDEXED = "indexed"
    FAILED = "failed"


class EvidenceTarget(StrEnum):
    """下游 evidence refs 预留消费面。"""

    SCORE = "score"
    REVIEW = "review"
    EXPORT = "export"
    HISTORY = "history"


@dataclass(frozen=True)
class KnowledgeDocument:
    """RAG 最小摄取输入，代表用户可见文档或文本资料。"""

    document_id: str
    owner_id: str
    visibility: KnowledgeVisibility
    source_type: RAGSourceType
    source_label: str
    content: str
    source_version: str
    index_status: KnowledgeIndexStatus = KnowledgeIndexStatus.INDEXED
    failure_reason: str | None = None


@dataclass(frozen=True)
class KnowledgeResource:
    """RAG foundation 使用的非持久化知识资源摘要。"""

    resource_id: str
    owner_id: str
    visibility: KnowledgeVisibility
    source_type: RAGSourceType
    source_label: str
    content_summary: str
    chunk_ref: str
    source_version: str
    index_status: KnowledgeIndexStatus = KnowledgeIndexStatus.INDEXED
    chunk_index: int = 0
    start_offset: int = 0
    end_offset: int = 0
    failure_reason: str | None = None

    def is_visible_to(self, actor_id: str) -> bool:
        """判断资源是否对当前 actor 可见。"""
        return self.visibility == KnowledgeVisibility.PUBLIC or self.owner_id == actor_id

    def visibility_snapshot(self) -> str:
        """返回可安全持久化或导出的可见性摘要。"""
        if self.visibility == KnowledgeVisibility.PUBLIC:
            return "public"
        return f"private:{self.owner_id}"


@dataclass(frozen=True)
class RetrievalQuerySummary:
    """脱敏后的检索请求摘要。"""

    query_summary: str
    actor_id: str
    selected_resource_ids: tuple[str, ...]
    top_k: int
    trigger: str
    visibility_filter: str = "owner_or_public"


@dataclass(frozen=True)
class Citation:
    """可解释引用，不暴露不可见资源原文。"""

    citation_ref: str
    source_ref: str
    chunk_ref: str
    source_label: str
    source_type: RAGSourceType
    snippet_summary: str
    source_version: str
    visibility_snapshot: str
    chunk_index: int = 0
    start_offset: int = 0
    end_offset: int = 0


@dataclass(frozen=True)
class EvidenceItem:
    """可供评分、复盘、导出和历史回看的证据项。"""

    evidence_ref: str
    evidence_summary: str
    citation_refs: tuple[str, ...]
    confidence_label: str
    used_by: EvidenceTarget
    source_snapshot_ref: str
    degraded: bool = False
    fallback_reason: str | None = None


@dataclass(frozen=True)
class EvidenceGap:
    """RAG 无结果、权限过滤或不可用时的证据缺口。"""

    reason: str
    safe_message: str
    retryable: bool
    confidence_label: str = "no_evidence"


@dataclass(frozen=True)
class RetrievalResultSummary:
    """检索结果的安全摘要。"""

    hit_count: int
    hit_summary: tuple[str, ...]
    empty_reason: str | None
    degraded: bool
    retryable: bool


@dataclass(frozen=True)
class RAGFoundationResult:
    """RAG foundation 对内统一返回结构。"""

    query_summary: RetrievalQuerySummary
    result_summary: RetrievalResultSummary
    citations: list[Citation]
    evidence_items: list[EvidenceItem]
    evidence_gap: EvidenceGap | None
    downstream_refs: dict[str, list[str]] = field(default_factory=dict)
    permission_filtered_count: int = 0
    degraded: bool = False
