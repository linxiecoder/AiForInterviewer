"""Pure source support classification policy for Polish question context."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class SourceSupportLevel(str, Enum):
    DIRECT_PROJECT_EVIDENCE = "direct_project_evidence"
    ADJACENT_PROJECT_EVIDENCE = "adjacent_project_evidence"
    JOB_GAP_ONLY = "job_gap_only"
    INSUFFICIENT_CONTEXT = "insufficient_context"


SOURCE_SUPPORT_LEVEL_VALUES = tuple(level.value for level in SourceSupportLevel)

PROJECT_EVIDENCE_SOURCE_TYPES = frozenset(
    {
        "asset_summary",
        "resume_project",
        "resume_project_contribution",
        "resume_work_experience",
        "resume_skill",
        "turn_answer",
        "turn_feedback",
    }
)

JOB_GAP_SOURCE_TYPES = frozenset({"job_requirement", "job_responsibility", "match_gap", "match_focus"})

DIRECT_SUPPORT_TERMS = (
    "Redis",
    "RocketMQ",
    "Kafka",
    "RabbitMQ",
    "MinIO",
    "FastAPI",
    "PostgreSQL",
    "MySQL",
    "Elasticsearch",
    "OpenSearch",
    "分布式锁",
    "事务消息",
    "半消息回查",
    "最终一致性",
    "支付链路",
    "库存扣减",
    "幂等",
    "失败补偿",
    "异常恢复",
    "上线验证",
    "大文件",
    "分片",
    "状态机",
    "异步",
)

GENERIC_SUPPORT_TERMS = frozenset({"设计", "能力", "项目", "说明", "验证", "技术", "链路"})

LEGACY_SOURCE_SUPPORT_LEVELS = {
    "canonical_asset_available": SourceSupportLevel.DIRECT_PROJECT_EVIDENCE,
    "direct_implemented": SourceSupportLevel.DIRECT_PROJECT_EVIDENCE,
    "adjacent_implemented": SourceSupportLevel.ADJACENT_PROJECT_EVIDENCE,
    "conceptual_only": SourceSupportLevel.JOB_GAP_ONLY,
    "unsupported": SourceSupportLevel.INSUFFICIENT_CONTEXT,
}


@dataclass(frozen=True)
class SourceSupportTarget:
    title: str = ""
    expected_capability: str = ""
    missing_points: tuple[str, ...] = ()

    @property
    def support_text(self) -> str:
        return " ".join(
            item
            for item in (
                self.title,
                self.expected_capability,
                " ".join(self.missing_points),
            )
            if item
        )


@dataclass(frozen=True)
class SourceSupportEvidence:
    source_type: str
    text: str
    ref: str | None = None


@dataclass(frozen=True)
class SourceSupportDecision:
    level: SourceSupportLevel
    reason_codes: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    @property
    def legacy_source_support_level(self) -> str:
        return self.level.value


class SourceSupportPolicy:
    @classmethod
    def classify_canonical_assets(
        cls,
        *,
        canonical_project_assets_available: bool,
        canonical_project_asset_count: int,
    ) -> SourceSupportDecision:
        if canonical_project_assets_available and canonical_project_asset_count > 0:
            return SourceSupportDecision(
                level=SourceSupportLevel.DIRECT_PROJECT_EVIDENCE,
                reason_codes=("canonical_project_assets_available",),
            )
        return SourceSupportDecision(
            level=SourceSupportLevel.INSUFFICIENT_CONTEXT,
            reason_codes=("canonical_project_assets_unavailable",),
        )

    @classmethod
    def classify_question_context(
        cls,
        *,
        target: SourceSupportTarget,
        evidence: Iterable[SourceSupportEvidence] = (),
        canonical_project_assets_available: bool = False,
        canonical_project_asset_texts: Iterable[str] = (),
        existing_level: object | None = None,
    ) -> SourceSupportDecision:
        normalized_existing_level = cls.normalize_level(existing_level)
        if normalized_existing_level in {
            SourceSupportLevel.DIRECT_PROJECT_EVIDENCE,
            SourceSupportLevel.ADJACENT_PROJECT_EVIDENCE,
        }:
            return SourceSupportDecision(
                level=normalized_existing_level,
                reason_codes=("canonical_pack_source_support_level",),
            )

        source_evidence = tuple(evidence)
        if not source_evidence and not canonical_project_assets_available:
            return SourceSupportDecision(
                level=SourceSupportLevel.INSUFFICIENT_CONTEXT,
                reason_codes=("no_source_context",),
            )

        project_evidence = tuple(item for item in source_evidence if item.source_type in PROJECT_EVIDENCE_SOURCE_TYPES)
        job_gap_evidence = tuple(item for item in source_evidence if item.source_type in JOB_GAP_SOURCE_TYPES)
        project_evidence_text = " ".join(
            tuple(item.text for item in project_evidence) + tuple(canonical_project_asset_texts)
        )

        if canonical_project_assets_available or project_evidence:
            evidence_refs = _evidence_refs(project_evidence)
            if cls.has_direct_project_support(target_text=target.support_text, evidence_text=project_evidence_text):
                return SourceSupportDecision(
                    level=SourceSupportLevel.DIRECT_PROJECT_EVIDENCE,
                    reason_codes=("direct_project_term_overlap",),
                    evidence_refs=evidence_refs,
                )
            return SourceSupportDecision(
                level=SourceSupportLevel.ADJACENT_PROJECT_EVIDENCE,
                reason_codes=("project_evidence_without_direct_overlap",),
                evidence_refs=evidence_refs,
            )

        if job_gap_evidence:
            return SourceSupportDecision(
                level=SourceSupportLevel.JOB_GAP_ONLY,
                reason_codes=("job_gap_evidence_only",),
                evidence_refs=_evidence_refs(job_gap_evidence),
            )
        return SourceSupportDecision(
            level=SourceSupportLevel.INSUFFICIENT_CONTEXT,
            reason_codes=("no_supported_source_context",),
        )

    @classmethod
    def normalize_level(cls, value: object) -> SourceSupportLevel | None:
        text = _clean(value)
        for level in SourceSupportLevel:
            if text == level.value:
                return level
        return LEGACY_SOURCE_SUPPORT_LEVELS.get(text)

    @classmethod
    def has_direct_project_support(cls, *, target_text: str, evidence_text: str) -> bool:
        target_terms = _support_terms(target_text)
        evidence_terms = _support_terms(evidence_text)
        return bool(target_terms & evidence_terms)


def _support_terms(value: object) -> set[str]:
    normalized = str(value or "").lower()
    terms = {term.lower() for term in DIRECT_SUPPORT_TERMS if term.lower() in normalized}
    terms.update(token for token in normalized.replace("/", " ").replace("、", " ").split() if len(token) >= 2)
    return {term for term in terms if term not in GENERIC_SUPPORT_TERMS}


def _evidence_refs(evidence: Iterable[SourceSupportEvidence]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(ref for item in evidence if (ref := _clean(item.ref))))


def _clean(value: object) -> str:
    return str(value or "").strip()
