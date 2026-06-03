"""Pure follow-up coverage policy for Polish question generation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256


class FollowUpCoverageAction(str, Enum):
    ALLOW_FOLLOW_UP = "allow_follow_up"
    COMPLETE = "complete"
    DOWNGRADE = "downgrade"
    BLOCK = "block"


@dataclass(frozen=True)
class FollowUpAssetConflict:
    conflict_type: str | None = None
    current_answer_claim: str | None = None
    asset_claim: str | None = None
    severity: str | None = None


@dataclass(frozen=True)
class FollowUpCoverageInput:
    expected_points: tuple[str, ...] = ()
    covered_points: tuple[str, ...] = ()
    missing_points: tuple[str, ...] = ()
    weak_points: tuple[str, ...] = ()
    contradicted_points: tuple[str, ...] = ()
    regressed_points: tuple[str, ...] = ()
    fixed_loss_points: tuple[str, ...] = ()
    repeated_loss_points: tuple[str, ...] = ()
    asset_conflicts: tuple[FollowUpAssetConflict, ...] = ()
    completed_focus_refs: tuple[str, ...] = ()
    used_focus_refs: tuple[str, ...] = ()
    coverage_available: bool = False


@dataclass(frozen=True)
class FollowUpFocusDecision:
    focus_key: str
    focus_source: str
    target_dimension: str
    follow_up_reason: str
    recommended_action: str
    completion_status: str
    reason_codes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, str]:
        return {
            "focus_key": self.focus_key,
            "focus_source": self.focus_source,
            "target_dimension": self.target_dimension,
            "follow_up_reason": self.follow_up_reason,
            "recommended_action": self.recommended_action,
            "completion_status": self.completion_status,
        }


@dataclass(frozen=True)
class FollowUpCoverageDecision:
    action: FollowUpCoverageAction
    matrix: dict[str, object]
    focus: FollowUpFocusDecision
    reason_codes: tuple[str, ...] = ()

    def to_legacy_dict(self) -> dict[str, object]:
        return {"coverage_matrix": dict(self.matrix), "focus": self.focus.to_dict()}


class FollowUpCoveragePolicy:
    @classmethod
    def decide(cls, coverage: FollowUpCoverageInput) -> FollowUpCoverageDecision:
        reason_codes: list[str] = []
        covered_points = _unique_texts(coverage.covered_points)
        missing_points = _filter_covered_points(_unique_texts(coverage.missing_points), covered_points)
        weak_points = _filter_covered_points(_unique_texts(coverage.weak_points), covered_points)
        contradicted_points = _filter_covered_points(_unique_texts(coverage.contradicted_points), covered_points)
        completed_refs = list(_unique_texts(coverage.completed_focus_refs, max_chars=160))
        completed_refs.extend(_completed_refs_for_covered_points(covered_points, reason_codes=reason_codes))
        completed_refs.extend(
            _completed_refs_for_loss_points(
                (*coverage.fixed_loss_points, *coverage.repeated_loss_points),
                reason_codes=reason_codes,
            )
        )
        matrix: dict[str, object] = {
            "expected_points": list(_unique_texts(coverage.expected_points)),
            "covered_points": list(covered_points),
            "missing_points": list(missing_points),
            "weak_points": list(weak_points),
            "contradicted_points": list(contradicted_points),
            "regressed_points": list(_unique_texts(coverage.regressed_points)),
            "fixed_loss_points": list(_unique_texts(coverage.fixed_loss_points, max_chars=120)),
            "repeated_loss_points": list(_unique_texts(coverage.repeated_loss_points, max_chars=120)),
            "asset_conflicts": [_asset_conflict_to_dict(item) for item in coverage.asset_conflicts],
            "completed_focus_refs": list(_unique_texts(completed_refs, max_chars=160)),
            "used_focus_refs": list(_unique_texts(coverage.used_focus_refs, max_chars=160)),
            "focus_key": None,
            "coverage_available": coverage.coverage_available,
        }
        focus, focus_reason_codes = _select_follow_up_focus(matrix)
        reason_codes.extend(focus_reason_codes)
        matrix["focus_key"] = focus.focus_key
        matrix["focus_source"] = focus.focus_source
        matrix["recommended_action"] = focus.recommended_action
        return FollowUpCoverageDecision(
            action=(
                FollowUpCoverageAction.COMPLETE
                if focus.completion_status == "all_focus_completed"
                else FollowUpCoverageAction.ALLOW_FOLLOW_UP
            ),
            matrix=matrix,
            focus=focus,
            reason_codes=tuple(dict.fromkeys(reason_codes)),
        )


def follow_up_focus_key(source_type: str, value: str) -> str:
    safe_source = _string_or_none(source_type, max_chars=80) or "controlled_fallback"
    seed_value = _string_or_none(value, max_chars=240) or "follow_up"
    seed = f"{safe_source}:{seed_value}"
    return f"focus_{safe_source}_{sha256(seed.encode('utf-8')).hexdigest()[:12]}"


def _select_follow_up_focus(matrix: dict[str, object]) -> tuple[FollowUpFocusDecision, tuple[str, ...]]:
    reason_codes: list[str] = []
    completed_refs = set(_string_list(matrix.get("completed_focus_refs"), max_item_chars=160))
    completed_refs.update(_string_list(matrix.get("used_focus_refs"), max_item_chars=160))
    candidates: list[tuple[FollowUpFocusDecision, str]] = []
    for conflict in _dict_list(matrix.get("asset_conflicts")):
        candidates.append(
            (
                _follow_up_focus_candidate(
                    source_type="asset_conflict",
                    target_dimension=_asset_conflict_focus_text(conflict),
                    follow_up_reason="asset_conflict",
                    recommended_action="clarify_asset_conflict",
                    completion_status="focus_pending",
                ),
                "asset_conflict_focus_selected",
            )
        )
    candidates.extend(
        _follow_up_point_candidates(
            matrix.get("regressed_points"),
            source_type="regressed_point",
            follow_up_reason="regressed_point",
            recommended_action="retry_same_question_preserve_regressed_points",
            reason_code="regressed_point_focus_selected",
        )
    )
    candidates.extend(
        _follow_up_point_candidates(
            matrix.get("missing_points"),
            source_type="missing_point",
            follow_up_reason="missing_point",
            recommended_action="continue_same_question",
            reason_code="missing_point_focus_selected",
        )
    )
    candidates.extend(
        _follow_up_point_candidates(
            matrix.get("weak_points"),
            source_type="weak_point",
            follow_up_reason="weak_point",
            recommended_action="continue_same_question",
            reason_code="weak_point_focus_selected",
        )
    )
    prior_focus_points = [
        *_string_list(matrix.get("regressed_points")),
        *_string_list(matrix.get("missing_points")),
        *_string_list(matrix.get("weak_points")),
        *_string_list(matrix.get("contradicted_points")),
    ]
    expected_uncovered = [
        point
        for point in _string_list(matrix.get("expected_points"))
        if not _contains_similar_text(_string_list(matrix.get("covered_points")), point)
        and not _contains_similar_text(prior_focus_points, point)
    ]
    candidates.extend(
        _follow_up_point_candidates(
            expected_uncovered,
            source_type="expected_point",
            follow_up_reason="expected_point",
            recommended_action="continue_same_question",
            reason_code="expected_point_focus_selected",
        )
    )
    if candidates:
        for candidate, reason_code in candidates:
            if candidate.focus_key not in completed_refs:
                return candidate, tuple((*reason_codes, reason_code))
            if candidate.focus_key in _string_list(matrix.get("completed_focus_refs"), max_item_chars=160):
                reason_codes.append("completed_focus_ref_skipped")
            if candidate.focus_key in _string_list(matrix.get("used_focus_refs"), max_item_chars=160):
                reason_codes.append("used_focus_ref_skipped")
        return _completed_follow_up_focus(), tuple((*reason_codes, "all_candidate_focus_completed"))
    if matrix.get("coverage_available") and matrix.get("expected_points"):
        return _completed_follow_up_focus(), ("all_expected_points_completed",)
    fallback = _follow_up_focus_candidate(
        source_type="controlled_fallback",
        target_dimension="失败路径、边界和验证指标",
        follow_up_reason="category_uncovered_direction",
        recommended_action="continue_same_question",
        completion_status="focus_pending",
    )
    return fallback, ("coverage_unavailable_fallback", "controlled_fallback_focus_selected")


def _completed_follow_up_focus() -> FollowUpFocusDecision:
    return _follow_up_focus_candidate(
        source_type="completed",
        target_dimension="所有追问焦点已完成",
        follow_up_reason="all_focus_completed",
        recommended_action="ready_for_next_question",
        completion_status="all_focus_completed",
    )


def _follow_up_point_candidates(
    value: object,
    *,
    source_type: str,
    follow_up_reason: str,
    recommended_action: str,
    reason_code: str,
) -> list[tuple[FollowUpFocusDecision, str]]:
    return [
        (
            _follow_up_focus_candidate(
                source_type=source_type,
                target_dimension=point,
                follow_up_reason=follow_up_reason,
                recommended_action=recommended_action,
                completion_status="focus_pending",
            ),
            reason_code,
        )
        for point in _string_list(value)
    ]


def _follow_up_focus_candidate(
    *,
    source_type: str,
    target_dimension: str,
    follow_up_reason: str,
    recommended_action: str,
    completion_status: str,
) -> FollowUpFocusDecision:
    target = _compact_follow_up_target(target_dimension) or "失败路径、边界和验证指标"
    return FollowUpFocusDecision(
        focus_key=follow_up_focus_key(source_type, target),
        focus_source=source_type,
        target_dimension=target,
        follow_up_reason=follow_up_reason,
        recommended_action=recommended_action,
        completion_status=completion_status,
    )


def _completed_refs_for_covered_points(points: tuple[str, ...], *, reason_codes: list[str]) -> tuple[str, ...]:
    refs: list[str] = []
    for point in points:
        reason_codes.append("covered_point_removed_from_missing_or_weak")
        refs.extend(
            (
                follow_up_focus_key("missing_point", point),
                follow_up_focus_key("weak_point", point),
                follow_up_focus_key("expected_point", point),
            )
        )
    return tuple(refs)


def _completed_refs_for_loss_points(points: tuple[str, ...], *, reason_codes: list[str]) -> tuple[str, ...]:
    refs: list[str] = []
    for point in _unique_texts(points, max_chars=120):
        reason_codes.append("fixed_loss_focus_marked_completed")
        reason_codes.append("repeated_loss_focus_marked_completed")
        refs.append(follow_up_focus_key("loss_point", point))
    return tuple(refs)


def _asset_conflict_to_dict(conflict: FollowUpAssetConflict) -> dict[str, str]:
    compact = {
        "conflict_type": _string_or_none(conflict.conflict_type, max_chars=120),
        "current_answer_claim": _string_or_none(conflict.current_answer_claim, max_chars=160),
        "asset_claim": _string_or_none(conflict.asset_claim, max_chars=160),
        "severity": _string_or_none(conflict.severity, max_chars=80),
    }
    return {key: value for key, value in compact.items() if value}


def _asset_conflict_focus_text(conflict: dict[str, object]) -> str:
    parts = [
        _string_or_none(conflict.get("current_answer_claim"), max_chars=120),
        _string_or_none(conflict.get("asset_claim"), max_chars=120),
        _string_or_none(conflict.get("conflict_type"), max_chars=80),
    ]
    return " / ".join(part for part in parts if part) or "资产事实冲突"


def _filter_covered_points(points: tuple[str, ...], covered_points: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(point for point in points if not _contains_similar_text(list(covered_points), point))


def _contains_similar_text(values: list[str], point: str) -> bool:
    normalized = _string_or_none(point, max_chars=240)
    if not normalized:
        return False
    for value in values:
        current = _string_or_none(value, max_chars=240)
        if current and (current in normalized or normalized in current):
            return True
    return False


def _compact_follow_up_target(value: object) -> str | None:
    return _string_or_none(value, max_chars=80)


def _unique_texts(values: object, *, max_chars: int = 240) -> tuple[str, ...]:
    return tuple(dict.fromkeys(_string_list(values, max_item_chars=max_chars)))


def _dict_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _string_list(value: object, *, max_item_chars: int = 240) -> list[str]:
    if value is None:
        return []
    raw_items = value if isinstance(value, (list, tuple, set)) else [value]
    items: list[str] = []
    for item in raw_items:
        text = _string_or_none(item, max_chars=max_item_chars)
        if text:
            items.append(text)
    return items


def _string_or_none(value: object, *, max_chars: int = 240) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return text[:max_chars]
