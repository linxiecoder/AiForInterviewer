"""Pure asset consistency policy for Polish feedback review."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


_CLAIM_MARKERS = (
    "我负责",
    "我主导",
    "我参与",
    "我们使用",
    "我们采用",
    "项目使用",
    "项目采用",
    "负责",
    "主导",
    "built",
    "owned",
    "led",
    "used",
    "implemented",
)
_RESPONSIBILITY_LOW_MARKERS = ("参与", "协助", "support", "contributed", "helped")
_RESPONSIBILITY_HIGH_MARKERS = ("主导", "独立负责", "owner", "owned", "led", "lead")
_TECH_GROUPS: dict[str, tuple[str, ...]] = {
    "framework": ("fastapi", "django", "flask", "spring", "express", "nestjs"),
    "database": ("postgresql", "postgres", "mysql", "mongodb", "mongo", "tidb", "sqlite"),
    "message_queue": ("kafka", "rabbitmq", "rocketmq", "pulsar", "sqs"),
    "cache": ("redis", "memcached"),
    "search": ("elasticsearch", "opensearch", "solr", "bm25"),
    "language": ("python", "java", "go", "golang", "typescript", "node"),
}
_METRIC_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:%|ms|s|qps|tps|w|k|m|万|千|秒|毫秒|天|月|年|人)\b",
    re.IGNORECASE,
)
_YEAR_PATTERN = re.compile(r"\b20\d{2}\b|20\d{2}\s*年")


class AssetConsistencyStatus(str, Enum):
    CONSISTENT = "consistent"
    CONFLICT = "conflict"
    INSUFFICIENT_ASSET_CONTEXT = "insufficient_asset_context"


@dataclass(frozen=True)
class CanonicalAssetItem:
    asset_id: str | None = None
    title: str | None = None
    summary: str | None = None
    content_excerpt: str | None = None


@dataclass(frozen=True)
class AssetConsistencyInput:
    answer_text: str
    asset_items: tuple[CanonicalAssetItem, ...] = ()
    canonical_assets_available: bool = False


@dataclass(frozen=True)
class AssetConsistencyConflict:
    conflict_type: str
    current_answer_claim: str
    asset_claim: str
    severity: str
    asset_ref: dict[str, str] | None = None
    clarification_question: str = "Clarify the project fact against canonical assets before continuing."

    def to_dict(self) -> dict[str, object]:
        return {
            "conflict_type": self.conflict_type,
            "current_answer_claim": self.current_answer_claim,
            "asset_claim": self.asset_claim,
            "severity": self.severity,
            "asset_ref": self.asset_ref,
            "clarification_question": self.clarification_question,
        }


@dataclass(frozen=True)
class UnsupportedAssetClaim:
    claim_type: str
    current_answer_claim: str
    reason: str
    asset_refs_checked: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_type": self.claim_type,
            "current_answer_claim": self.current_answer_claim,
            "reason": self.reason,
            "asset_refs_checked": list(self.asset_refs_checked),
        }


@dataclass(frozen=True)
class AssetConsistencyDecision:
    status: AssetConsistencyStatus
    checked_asset_refs: tuple[str, ...] = ()
    conflicts: tuple[AssetConsistencyConflict, ...] = ()
    unsupported_claims: tuple[UnsupportedAssetClaim, ...] = ()
    user_clarification_required: bool = False
    reason_codes: tuple[str, ...] = ()

    def to_legacy_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "checked_asset_refs": list(self.checked_asset_refs),
            "conflicts": [conflict.to_dict() for conflict in self.conflicts],
            "unsupported_claims": [claim.to_dict() for claim in self.unsupported_claims],
            "user_clarification_required": self.user_clarification_required,
        }


class AssetConsistencyPolicy:
    @classmethod
    def evaluate(cls, value: AssetConsistencyInput) -> AssetConsistencyDecision:
        if not value.canonical_assets_available or not value.asset_items:
            return AssetConsistencyDecision(
                status=AssetConsistencyStatus.INSUFFICIENT_ASSET_CONTEXT,
                reason_codes=("canonical_asset_context_missing",),
            )

        reason_codes: list[str] = []
        asset_text = " ".join(_asset_text(item) for item in value.asset_items)
        answer_tokens_by_group = _tech_tokens_by_group(value.answer_text)
        asset_tokens_by_group = _tech_tokens_by_group(asset_text)
        conflicts: list[AssetConsistencyConflict] = []
        unsupported_claims: list[UnsupportedAssetClaim] = []
        checked_refs = _checked_asset_refs(value.asset_items)

        for group_name, answer_tokens in answer_tokens_by_group.items():
            asset_tokens = asset_tokens_by_group.get(group_name, set())
            unsupported_tokens = sorted(token for token in answer_tokens if token not in asset_tokens)
            if not unsupported_tokens:
                continue
            if asset_tokens:
                reason_codes.append(f"{group_name}_technology_stack_conflict")
                conflicts.append(
                    _conflict(
                        "technology_stack_conflict",
                        current_answer_claim=", ".join(unsupported_tokens),
                        asset_claim=", ".join(sorted(asset_tokens)),
                        asset_item=value.asset_items[0],
                        severity="major",
                    )
                )
            elif _looks_like_project_claim(value.answer_text):
                reason_codes.append(f"{group_name}_unsupported_claim")
                for token in unsupported_tokens[:3]:
                    unsupported_claims.append(
                        UnsupportedAssetClaim(
                            claim_type="technology_stack",
                            current_answer_claim=token,
                            reason="not_supported_by_canonical_project_assets",
                            asset_refs_checked=checked_refs,
                        )
                    )

        metric_conflicts = _metric_conflicts(value.answer_text, value.asset_items)
        if metric_conflicts:
            reason_codes.append("metric_conflict")
            conflicts.extend(metric_conflicts)
        timeline_conflicts = _timeline_conflicts(value.answer_text, value.asset_items)
        if timeline_conflicts:
            reason_codes.append("timeline_conflict")
            conflicts.extend(timeline_conflicts)
        responsibility_conflicts = _responsibility_conflicts(value.answer_text, value.asset_items)
        if responsibility_conflicts:
            reason_codes.append("responsibility_conflict")
            conflicts.extend(responsibility_conflicts)

        unsupported_claims = list(_dedupe_claims(unsupported_claims))
        for claim in unsupported_claims:
            conflicts.append(
                _conflict(
                    "unsupported_claim",
                    current_answer_claim=_clean(claim.current_answer_claim, max_chars=240),
                    asset_claim="No supporting canonical project asset fact found.",
                    asset_item=value.asset_items[0],
                    severity="major",
                )
            )

        conflicts = list(_dedupe_conflicts(conflicts))
        status = AssetConsistencyStatus.CONFLICT if conflicts or unsupported_claims else AssetConsistencyStatus.CONSISTENT
        if status == AssetConsistencyStatus.CONSISTENT:
            reason_codes.append("canonical_assets_consistent")
        return AssetConsistencyDecision(
            status=status,
            checked_asset_refs=checked_refs,
            conflicts=tuple(conflicts),
            unsupported_claims=tuple(unsupported_claims),
            user_clarification_required=status == AssetConsistencyStatus.CONFLICT,
            reason_codes=tuple(dict.fromkeys(reason_codes)),
        )


def _metric_conflicts(
    answer_text: str,
    asset_items: tuple[CanonicalAssetItem, ...],
) -> list[AssetConsistencyConflict]:
    answer_metrics = set(_METRIC_PATTERN.findall(answer_text))
    if not answer_metrics:
        return []
    conflicts: list[AssetConsistencyConflict] = []
    for item in asset_items:
        asset_metrics = set(_METRIC_PATTERN.findall(_asset_text(item)))
        if asset_metrics and answer_metrics != asset_metrics:
            conflicts.append(
                _conflict(
                    "metric_conflict",
                    current_answer_claim=", ".join(sorted(answer_metrics)),
                    asset_claim=", ".join(sorted(asset_metrics)),
                    asset_item=item,
                    severity="major",
                )
            )
    return conflicts[:3]


def _timeline_conflicts(
    answer_text: str,
    asset_items: tuple[CanonicalAssetItem, ...],
) -> list[AssetConsistencyConflict]:
    answer_years = set(_YEAR_PATTERN.findall(answer_text))
    if not answer_years:
        return []
    conflicts: list[AssetConsistencyConflict] = []
    for item in asset_items:
        asset_years = set(_YEAR_PATTERN.findall(_asset_text(item)))
        if asset_years and answer_years != asset_years:
            conflicts.append(
                _conflict(
                    "timeline_conflict",
                    current_answer_claim=", ".join(sorted(answer_years)),
                    asset_claim=", ".join(sorted(asset_years)),
                    asset_item=item,
                    severity="major",
                )
            )
    return conflicts[:3]


def _responsibility_conflicts(
    answer_text: str,
    asset_items: tuple[CanonicalAssetItem, ...],
) -> list[AssetConsistencyConflict]:
    if not _contains_any(answer_text, _RESPONSIBILITY_HIGH_MARKERS):
        return []
    conflicts: list[AssetConsistencyConflict] = []
    for item in asset_items:
        if _contains_any(_asset_text(item), _RESPONSIBILITY_LOW_MARKERS):
            conflicts.append(
                _conflict(
                    "responsibility_conflict",
                    current_answer_claim="owned_or_led",
                    asset_claim="participated_or_supported",
                    asset_item=item,
                    severity="major",
                )
            )
    return conflicts[:3]


def _conflict(
    conflict_type: str,
    *,
    current_answer_claim: str,
    asset_claim: str,
    asset_item: CanonicalAssetItem,
    severity: str,
) -> AssetConsistencyConflict:
    asset_id = _clean(asset_item.asset_id, max_chars=120)
    return AssetConsistencyConflict(
        conflict_type=conflict_type,
        current_answer_claim=_clean(current_answer_claim, max_chars=400),
        asset_claim=_clean(asset_claim, max_chars=400),
        severity=severity,
        asset_ref={"resource_type": "asset", "resource_id": asset_id} if asset_id else None,
    )


def _dedupe_conflicts(conflicts: list[AssetConsistencyConflict]) -> tuple[AssetConsistencyConflict, ...]:
    seen: set[tuple[str, str, str]] = set()
    result: list[AssetConsistencyConflict] = []
    for conflict in conflicts:
        key = (
            _clean(conflict.conflict_type, max_chars=80),
            _clean(conflict.current_answer_claim, max_chars=120),
            _clean(conflict.asset_claim, max_chars=120),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(conflict)
    return tuple(result[:8])


def _dedupe_claims(claims: list[UnsupportedAssetClaim]) -> tuple[UnsupportedAssetClaim, ...]:
    seen: set[str] = set()
    result: list[UnsupportedAssetClaim] = []
    for claim in claims:
        key = _clean(claim.current_answer_claim, max_chars=160).casefold()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(claim)
    return tuple(result[:8])


def _tech_tokens_by_group(text: str) -> dict[str, set[str]]:
    lowered = text.casefold()
    result: dict[str, set[str]] = {}
    for group_name, terms in _TECH_GROUPS.items():
        found = {term for term in terms if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", lowered)}
        if found:
            result[group_name] = found
    return result


def _looks_like_project_claim(text: str) -> bool:
    lowered = text.casefold()
    return any(marker.casefold() in lowered for marker in _CLAIM_MARKERS)


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    lowered = text.casefold()
    return any(marker.casefold() in lowered for marker in markers)


def _asset_text(item: CanonicalAssetItem) -> str:
    return " ".join(
        value
        for value in (
            _clean(item.title, max_chars=240),
            _clean(item.summary, max_chars=800),
            _clean(item.content_excerpt, max_chars=800),
        )
        if value
    )


def _checked_asset_refs(asset_items: tuple[CanonicalAssetItem, ...]) -> tuple[str, ...]:
    return _unique(
        [
            _clean(item.asset_id, max_chars=120)
            for item in asset_items
            if _clean(item.asset_id, max_chars=120)
        ]
    )


def _unique(values: list[str]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return tuple(result)


def _clean(value: object, *, max_chars: int = 240) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text
