"""Source support summary construction for Polish interview context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from app.application.polish.canonical_evidence import SourceSupportSummary


PROJECT_EVIDENCE_SOURCE_TYPES = {
    "asset_summary",
    "resume_project",
    "resume_project_contribution",
    "resume_work_experience",
    "resume_skill",
    "turn_answer",
    "turn_feedback",
}
JOB_GAP_SOURCE_TYPES = {"job_requirement", "job_responsibility", "match_gap", "match_focus"}


@dataclass(frozen=True)
class SourceSupportBuildResult:
    summary: SourceSupportSummary
    blocking_issues: tuple[dict[str, str], ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_support_summary": self.summary.to_dict(),
            "blocking_issues": [dict(item) for item in self.blocking_issues],
            "warnings": list(self.warnings),
        }


class SourceSupportSummaryService:
    def build(
        self,
        *,
        canonical_project_assets: dict[str, Any] | None = None,
        evidence_chunks: Iterable[object] = (),
        job_gap_refs: Iterable[object] = (),
        current_answer_refs: Iterable[object] = (),
        asset_conflicts: Iterable[object] = (),
        focus_target: object | None = None,
    ) -> SourceSupportBuildResult:
        canonical_assets = canonical_project_assets if isinstance(canonical_project_assets, dict) else {}
        current_answer_ref_tuple = _ref_tuple(current_answer_refs)
        warnings = ("current_answer_not_canonical_evidence",) if current_answer_ref_tuple else ()

        if _has_asset_conflict(canonical_assets, asset_conflicts=asset_conflicts):
            return SourceSupportBuildResult(
                summary=SourceSupportSummary(
                    level="insufficient_context",
                    missing_context=("asset_conflict_human_review",),
                    reason_codes=("asset_conflict_requires_human_review",),
                    confidence="low",
                ),
                blocking_issues=(
                    {
                        "issue_type": "asset_conflict_requires_human_review",
                        "severity": "blocking",
                        "hitl_required": "true",
                    },
                ),
                warnings=warnings,
            )

        primary_refs = _confirmed_asset_refs(canonical_assets)
        if primary_refs:
            return SourceSupportBuildResult(
                summary=SourceSupportSummary(
                    level="direct_project_evidence",
                    primary_evidence_refs=primary_refs,
                    reason_codes=("canonical_asset_confirmed",),
                    confidence="high",
                ),
                warnings=warnings,
            )

        chunks = tuple(evidence_chunks)
        direct_chunk_refs = _matching_project_chunk_refs(chunks, focus_target=focus_target)
        if direct_chunk_refs:
            return SourceSupportBuildResult(
                summary=SourceSupportSummary(
                    level="direct_project_evidence",
                    primary_evidence_refs=direct_chunk_refs,
                    reason_codes=("matching_project_evidence",),
                    confidence="high",
                ),
                warnings=warnings,
            )

        adjacent_refs = _chunk_refs(chunks, PROJECT_EVIDENCE_SOURCE_TYPES)
        if adjacent_refs:
            return SourceSupportBuildResult(
                summary=SourceSupportSummary(
                    level="adjacent_project_evidence",
                    adjacent_evidence_refs=adjacent_refs,
                    reason_codes=("project_evidence_without_confirmed_canonical_asset",),
                    confidence="medium",
                ),
                warnings=warnings,
            )

        gap_refs = _chunk_refs(chunks, JOB_GAP_SOURCE_TYPES) + _ref_tuple(job_gap_refs)
        if gap_refs:
            return SourceSupportBuildResult(
                summary=SourceSupportSummary(
                    level="job_gap_only",
                    job_gap_refs=gap_refs,
                    reason_codes=("job_gap_without_project_evidence",),
                    confidence="medium",
                ),
                warnings=warnings,
            )

        return SourceSupportBuildResult(
            summary=SourceSupportSummary(
                level="insufficient_context",
                missing_context=("confirmed_project_evidence",),
                reason_codes=("no_confirmed_canonical_asset",),
                confidence="low",
            ),
            warnings=warnings,
        )


def _confirmed_asset_refs(canonical_assets: dict[str, Any]) -> tuple[dict[str, str], ...]:
    items = canonical_assets.get("items") if isinstance(canonical_assets.get("items"), list) else []
    refs: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if _clean(item.get("status")) != "asset_confirmed":
            continue
        asset_id = _clean(item.get("asset_id"), max_chars=160)
        if not asset_id:
            continue
        ref = {"resource_type": "asset", "resource_id": asset_id}
        if ref not in refs:
            refs.append(ref)
    return tuple(refs)


def _chunk_refs(chunks: Iterable[object], source_types: set[str]) -> tuple[dict[str, str], ...]:
    refs: list[dict[str, str]] = []
    for chunk in chunks:
        source_type = _clean(_value(chunk, "source_type"), max_chars=120)
        if source_type not in source_types:
            continue
        chunk_id = _clean(_value(chunk, "chunk_id") or _value(chunk, "ref"), max_chars=160)
        if not chunk_id:
            continue
        ref = {"resource_type": source_type, "resource_id": chunk_id}
        if ref not in refs:
            refs.append(ref)
    return tuple(refs)


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


def _matching_project_chunk_refs(
    chunks: Iterable[object],
    *,
    focus_target: object | None,
) -> tuple[dict[str, str], ...]:
    if focus_target is None:
        return ()
    target_text = _focus_target_text(focus_target)
    if not target_text:
        return ()
    refs: list[dict[str, str]] = []
    for chunk in chunks:
        if _clean(_value(chunk, "source_type"), max_chars=120) not in PROJECT_EVIDENCE_SOURCE_TYPES:
            continue
        if not _has_direct_project_support(target_text=target_text, evidence_text=_chunk_text(chunk)):
            continue
        chunk_id = _clean(_value(chunk, "chunk_id") or _value(chunk, "ref"), max_chars=160)
        if not chunk_id:
            continue
        ref = {"resource_type": _clean(_value(chunk, "source_type"), max_chars=120), "resource_id": chunk_id}
        if ref not in refs:
            refs.append(ref)
    return tuple(refs)


def _focus_target_text(focus_target: object) -> str:
    missing_points = _value(focus_target, "missing_points")
    if isinstance(missing_points, (list, tuple)):
        missing_text = " ".join(str(item) for item in missing_points if item)
    else:
        missing_text = str(missing_points or "")
    return " ".join(
        item
        for item in (
            str(_value(focus_target, "title") or ""),
            str(_value(focus_target, "expected_capability") or ""),
            missing_text,
        )
        if item
    )


def _chunk_text(chunk: object) -> str:
    return " ".join(
        str(value)
        for value in (
            _value(chunk, "text"),
            _value(chunk, "title"),
            _value(chunk, "summary"),
            _value(chunk, "content_excerpt"),
        )
        if value
    )


def _has_direct_project_support(*, target_text: str, evidence_text: str) -> bool:
    target_terms = _support_terms(target_text)
    evidence_terms = _support_terms(evidence_text)
    return bool(target_terms & evidence_terms)


def _support_terms(value: object) -> set[str]:
    text = str(value or "")
    normalized = text.lower()
    terms = {term.lower() for term in DIRECT_SUPPORT_TERMS if term.lower() in normalized}
    terms.update(token for token in normalized.replace("/", " ").replace("、", " ").split() if len(token) >= 2)
    return {term for term in terms if term not in {"设计", "能力", "项目", "说明", "验证", "技术", "链路"}}


def _has_asset_conflict(canonical_assets: dict[str, Any], *, asset_conflicts: Iterable[object]) -> bool:
    if tuple(asset_conflicts):
        return True
    items = canonical_assets.get("items") if isinstance(canonical_assets.get("items"), list) else []
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("conflict_refs") or item.get("conflict_type") or item.get("conflict_reason"):
            return True
    return False


def _ref_tuple(value: Iterable[object]) -> tuple[dict[str, str], ...]:
    refs: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        resource_type = _clean(item.get("resource_type"), max_chars=120)
        resource_id = _clean(item.get("resource_id"), max_chars=160)
        if not resource_type or not resource_id:
            continue
        ref = {"resource_type": resource_type, "resource_id": resource_id}
        if ref not in refs:
            refs.append(ref)
    return tuple(refs)


def _value(source: object, key: str) -> object:
    if isinstance(source, dict):
        return source.get(key)
    return getattr(source, key, None)


def _clean(value: object, *, max_chars: int = 480) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text
