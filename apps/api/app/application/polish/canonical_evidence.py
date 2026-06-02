"""Canonical evidence selection for Polish question and feedback context."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Iterable

from app.application.assets.ports import AssetRepository


CANONICAL_EVIDENCE_PACK_SCHEMA_VERSION = "canonical_evidence_pack.v1"
CANONICAL_ASSET_SELECTION_POLICY = "rule_based_keyword_overlap_v1"
# Archived assets are historical/reference-only in the active product specs.
CANONICAL_ASSET_STATUS_POLICY = "asset_confirmed_only_v1"
CANONICAL_ASSET_STATUSES = ("asset_confirmed",)
CANONICAL_EXCLUDED_ASSET_STATUSES = {"asset_archived": "historical_reference_only"}
CANONICAL_ASSET_TYPES = (
    "project_story",
    "project_expression",
    "answer_material",
    "technical_note",
    "feedback_summary",
)
SOURCE_SUPPORT_LEVELS = (
    "direct_project_evidence",
    "adjacent_project_evidence",
    "job_gap_only",
    "insufficient_context",
)
SOURCE_SUPPORT_CONFIDENCE_LEVELS = ("high", "medium", "low")
SOURCE_SUPPORT_POLICY_VERSION = "source_support_summary.v1"
SOURCE_SUPPORT_COMPUTED_AT = "deterministic_context_v1"
MAX_CANONICAL_ASSETS = 5
MAX_ASSET_CANDIDATES = 80
MAX_ASSET_EXCERPT_CHARS = 480


@dataclass(frozen=True)
class SourceSupportSummary:
    level: str
    primary_evidence_refs: tuple[dict[str, str], ...] = ()
    adjacent_evidence_refs: tuple[dict[str, str], ...] = ()
    job_gap_refs: tuple[dict[str, str], ...] = ()
    missing_context: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    confidence: str = "low"
    policy_version: str = SOURCE_SUPPORT_POLICY_VERSION
    computed_at: str = SOURCE_SUPPORT_COMPUTED_AT

    def __post_init__(self) -> None:
        level = _clean(self.level, max_chars=80)
        if level not in SOURCE_SUPPORT_LEVELS:
            raise ValueError("source_support_level_invalid")

        primary_refs = _ref_tuple(self.primary_evidence_refs)
        adjacent_refs = _ref_tuple(self.adjacent_evidence_refs)
        job_gap_refs = _ref_tuple(self.job_gap_refs)
        missing_context = _text_tuple(self.missing_context, max_chars=160)
        reason_codes = _text_tuple(self.reason_codes, max_chars=160)
        confidence = _clean(self.confidence, max_chars=40) or "low"
        if confidence not in SOURCE_SUPPORT_CONFIDENCE_LEVELS:
            raise ValueError("source_support_confidence_invalid")
        policy_version = _clean(self.policy_version, max_chars=120) or SOURCE_SUPPORT_POLICY_VERSION
        computed_at = _clean(self.computed_at, max_chars=120) or SOURCE_SUPPORT_COMPUTED_AT

        if not reason_codes:
            raise ValueError("source_support_reason_codes_required")
        if level == "direct_project_evidence" and not primary_refs:
            raise ValueError("source_support_primary_refs_required")
        if level == "adjacent_project_evidence" and not adjacent_refs:
            raise ValueError("source_support_adjacent_refs_required")
        if level == "job_gap_only" and not job_gap_refs:
            raise ValueError("source_support_job_gap_refs_required")
        if level == "insufficient_context" and not missing_context:
            raise ValueError("source_support_missing_context_required")

        object.__setattr__(self, "level", level)
        object.__setattr__(self, "primary_evidence_refs", primary_refs)
        object.__setattr__(self, "adjacent_evidence_refs", adjacent_refs)
        object.__setattr__(self, "job_gap_refs", job_gap_refs)
        object.__setattr__(self, "missing_context", missing_context)
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "policy_version", policy_version)
        object.__setattr__(self, "computed_at", computed_at)

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "primary_evidence_refs": [dict(item) for item in self.primary_evidence_refs],
            "adjacent_evidence_refs": [dict(item) for item in self.adjacent_evidence_refs],
            "job_gap_refs": [dict(item) for item in self.job_gap_refs],
            "missing_context": list(self.missing_context),
            "reason_codes": list(self.reason_codes),
            "confidence": self.confidence,
            "policy_version": self.policy_version,
            "computed_at": self.computed_at,
        }


class CanonicalEvidenceService:
    def __init__(self, asset_repository: AssetRepository | None = None) -> None:
        self._asset_repository = asset_repository

    def build_pack(
        self,
        *,
        owner_id: str,
        session_id: str,
        job_id: str | None = None,
        job_version_id: str | None = None,
        resume_id: str | None = None,
        resume_version_id: str | None = None,
        progress_node_ref: str | None = None,
        query_inputs: Iterable[object] = (),
    ) -> dict[str, Any]:
        canonical_project_assets = self.select_project_assets(
            owner_id=owner_id,
            query_inputs=query_inputs,
        )
        source_support_summary = source_support_summary_from_canonical_assets(canonical_project_assets)
        source_support_level = source_support_level_from_summary(source_support_summary.to_dict())
        pack = {
            "schema_version": CANONICAL_EVIDENCE_PACK_SCHEMA_VERSION,
            "owner_ref": {"resource_type": "owner", "resource_id": owner_id},
            "session_ref": {"resource_type": "polish_session", "resource_id": session_id},
            "job_snapshot_ref": _version_ref("job", job_id, job_version_id),
            "resume_snapshot_ref": _version_ref("resume", resume_id, resume_version_id),
            "progress_node_ref": progress_node_ref,
            "canonical_project_assets": canonical_project_assets,
            "retrieved_rag_chunks": {"available": False, "items": []},
            "prior_answer_refs": [],
            "prior_feedback_refs": [],
            "answer_attempt_refs": [],
            "source_support_summary": source_support_summary.to_dict(),
            "source_support_level": source_support_level,
            "warnings": [],
            "blocking_issues": [],
        }
        pack["context_digest"] = stable_digest(_canonical_pack_digest_payload(pack))
        return pack

    def select_project_assets(
        self,
        *,
        owner_id: str,
        query_inputs: Iterable[object] = (),
    ) -> dict[str, Any]:
        empty = empty_canonical_project_assets()
        if self._asset_repository is None:
            return empty | {"warnings": ["asset_repository_absent"]}

        keywords = _keywords(query_inputs)
        if not keywords:
            return empty

        try:
            candidates = _owner_scoped_asset_candidates(self._asset_repository, owner_id=owner_id)
        except Exception:
            return empty | {"warnings": ["asset_repository_unavailable"]}

        ranked: list[tuple[int, dict[str, Any]]] = []
        for candidate in candidates:
            detail = _asset_detail(self._asset_repository, owner_id=owner_id, asset=candidate)
            if detail is None:
                detail = candidate
            scored = _canonical_asset_item(detail, keywords=keywords)
            if scored is None:
                continue
            ranked.append((int(scored["priority"]), scored))

        items = [
            item
            for _, item in sorted(
                ranked,
                key=lambda pair: (-pair[0], str(pair[1].get("asset_id") or "")),
            )[:MAX_CANONICAL_ASSETS]
        ]
        if not items:
            return empty
        return empty | {"available": True, "items": items}


def empty_canonical_project_assets() -> dict[str, Any]:
    return {
        "available": False,
        "selection_policy": CANONICAL_ASSET_SELECTION_POLICY,
        "status_policy": CANONICAL_ASSET_STATUS_POLICY,
        "excluded_statuses": dict(CANONICAL_EXCLUDED_ASSET_STATUSES),
        "items": [],
    }


def stable_digest(value: dict[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


def source_support_summary_from_canonical_assets(canonical_project_assets: dict[str, Any]) -> SourceSupportSummary:
    canonical_assets = canonical_project_assets if isinstance(canonical_project_assets, dict) else {}
    items = canonical_assets.get("items") if isinstance(canonical_assets.get("items"), list) else []
    asset_refs = tuple(
        ref
        for item in items[:MAX_CANONICAL_ASSETS]
        if isinstance(item, dict)
        and (ref := _asset_ref(item)) is not None
    )
    if canonical_assets.get("available") and asset_refs:
        return SourceSupportSummary(
            level="direct_project_evidence",
            primary_evidence_refs=asset_refs,
            reason_codes=("canonical_asset_confirmed",),
            confidence="high",
        )

    missing_context = ["confirmed_project_evidence"]
    warnings = _text_tuple(canonical_assets.get("warnings"))
    if "asset_repository_absent" in warnings:
        missing_context.append("asset_repository")
    if "asset_repository_unavailable" in warnings:
        missing_context.append("asset_repository_available")
    return SourceSupportSummary(
        level="insufficient_context",
        missing_context=tuple(missing_context),
        reason_codes=("no_confirmed_canonical_asset",),
        confidence="low",
    )


def source_support_level_from_summary(summary: SourceSupportSummary | dict[str, Any]) -> str:
    if isinstance(summary, SourceSupportSummary):
        return summary.level
    if isinstance(summary, dict):
        level = _clean(summary.get("level"), max_chars=80)
        if level in SOURCE_SUPPORT_LEVELS:
            return level
    return "insufficient_context"


def _owner_scoped_asset_candidates(
    repository: AssetRepository,
    *,
    owner_id: str,
) -> tuple[dict[str, Any], ...]:
    by_id: dict[str, dict[str, Any]] = {}
    for status in CANONICAL_ASSET_STATUSES:
        for asset_type in CANONICAL_ASSET_TYPES:
            for asset in repository.list_assets(owner_id=owner_id, status=status, asset_type=asset_type):
                asset_id = _clean(asset.get("asset_id"))
                if not asset_id or asset_id in by_id:
                    continue
                by_id[asset_id] = dict(asset)
                if len(by_id) >= MAX_ASSET_CANDIDATES:
                    return tuple(by_id.values())
    return tuple(by_id.values())


def _asset_detail(
    repository: AssetRepository,
    *,
    owner_id: str,
    asset: dict[str, Any],
) -> dict[str, Any] | None:
    asset_id = _clean(asset.get("asset_id"))
    if not asset_id:
        return None
    try:
        detail = repository.get_asset(owner_id=owner_id, asset_id=asset_id)
    except Exception:
        return None
    return detail if isinstance(detail, dict) else None


def _canonical_asset_item(asset: dict[str, Any], *, keywords: set[str]) -> dict[str, Any] | None:
    status = _clean(asset.get("status"))
    asset_type = _clean(asset.get("asset_type"))
    if status not in CANONICAL_ASSET_STATUSES or asset_type not in CANONICAL_ASSET_TYPES:
        return None
    title = _clean(asset.get("title"), max_chars=160)
    summary = _clean(asset.get("summary"), max_chars=360)
    content_excerpt = _clean(asset.get("content"), max_chars=MAX_ASSET_EXCERPT_CHARS)
    searchable = " ".join(value for value in (title, summary, content_excerpt) if value)
    matched_terms = sorted(term for term in keywords if term and term in searchable.casefold())[:8]
    if not matched_terms:
        return None
    status_priority = len(CANONICAL_ASSET_STATUSES) - CANONICAL_ASSET_STATUSES.index(status)
    type_priority = len(CANONICAL_ASSET_TYPES) - CANONICAL_ASSET_TYPES.index(asset_type)
    match_priority = min(len(matched_terms), 8)
    priority = status_priority * 100 + type_priority * 10 + match_priority
    return {
        "asset_id": _clean(asset.get("asset_id")),
        "status": status,
        "asset_type": asset_type,
        "title": title,
        "summary": summary,
        "content_excerpt": content_excerpt,
        "source_refs": _safe_refs(asset.get("source_refs")),
        "evidence_refs": _safe_refs(asset.get("evidence_refs")),
        "current_version_id": _clean(asset.get("current_version_id")),
        "priority": priority,
        "relevance_reason": f"keyword_overlap:{','.join(matched_terms[:5])}",
    }


def _keywords(values: Iterable[object]) -> set[str]:
    text = " ".join(_clean(value, max_chars=2000) for value in values if value is not None).casefold()
    raw_terms = re.findall(r"[a-z0-9_+#.-]{2,}|[\u4e00-\u9fff]{2,}", text)
    terms: list[str] = []
    for term in raw_terms:
        terms.append(term)
        if re.fullmatch(r"[\u4e00-\u9fff]{4,}", term):
            terms.extend(term[index : index + 2] for index in range(0, min(len(term) - 1, 18)))
            terms.extend(term[index : index + 4] for index in range(0, min(len(term) - 3, 16)))
    return set(terms[:80])


def _source_support_level(canonical_project_assets: dict[str, Any]) -> str:
    return source_support_level_from_summary(
        source_support_summary_from_canonical_assets(canonical_project_assets)
    )


def _version_ref(resource_type: str, resource_id: str | None, version_id: str | None) -> dict[str, str] | None:
    if not resource_id and not version_id:
        return None
    ref = {"resource_type": resource_type}
    if resource_id:
        ref["resource_id"] = resource_id
    if version_id:
        ref["version_id"] = version_id
    return ref


def _canonical_pack_digest_payload(pack: dict[str, Any]) -> dict[str, Any]:
    canonical_project_assets = pack.get("canonical_project_assets")
    return {
        "schema_version": pack.get("schema_version"),
        "owner_ref": pack.get("owner_ref"),
        "session_ref": pack.get("session_ref"),
        "job_snapshot_ref": pack.get("job_snapshot_ref"),
        "resume_snapshot_ref": pack.get("resume_snapshot_ref"),
        "progress_node_ref": pack.get("progress_node_ref"),
        "source_support_summary": pack.get("source_support_summary"),
        "source_support_level": source_support_level_from_summary(
            pack.get("source_support_summary") if isinstance(pack.get("source_support_summary"), dict) else {}
        ),
        "blocking_issues": pack.get("blocking_issues") if isinstance(pack.get("blocking_issues"), list) else [],
        "canonical_project_assets": canonical_project_assets if isinstance(canonical_project_assets, dict) else {},
    }


def _asset_ref(item: dict[str, Any]) -> dict[str, str] | None:
    asset_id = _clean(item.get("asset_id"), max_chars=160)
    if not asset_id:
        return None
    return {"resource_type": "asset", "resource_id": asset_id}


def _ref_tuple(value: object) -> tuple[dict[str, str], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    refs: list[dict[str, str]] = []
    for item in value[:20]:
        if not isinstance(item, dict):
            continue
        cleaned = {
            str(key): text
            for key, raw_value in item.items()
            if (text := _clean(raw_value, max_chars=160))
        }
        if cleaned and cleaned not in refs:
            refs.append(cleaned)
    return tuple(refs)


def _text_tuple(value: object, *, max_chars: int = 120) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    items: list[str] = []
    for item in value[:20]:
        text = _clean(item, max_chars=max_chars)
        if text and text not in items:
            items.append(text)
    return tuple(items)


def _safe_refs(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    refs: list[dict[str, str]] = []
    for item in value[:8]:
        if not isinstance(item, dict):
            continue
        cleaned = {
            str(key): text
            for key, raw_value in item.items()
            if (text := _clean(raw_value, max_chars=160))
        }
        if cleaned:
            refs.append(cleaned)
    return refs


def _clean(value: object, *, max_chars: int = 480) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text
