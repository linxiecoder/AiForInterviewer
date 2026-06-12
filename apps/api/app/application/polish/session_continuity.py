"""Application-level session continuity contract for Polish sessions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.domain.shared.clock import utc_now


class ContinuityStatus(str, Enum):
    READY = "ready"
    PARTIAL = "partial"
    STALE = "stale"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


_RUNNING_SESSION_STATUSES = frozenset({"running", "active"})
_REFRESH_FALLBACK_STATUSES = frozenset({"refresh_failed", "failed"})
_PARTIAL_PROGRESS_STATUSES = frozenset({"pending", "generating", "insufficient_context"})


@dataclass(frozen=True)
class SessionContinuitySnapshot:
    session_status: str
    progress_tree_status: str
    progress_tree_plan: dict[str, Any] | None = None
    progress_tree_state: dict[str, Any] | None = None
    turn_count: int = 0
    active_question_id: str | None = None
    active_progress_node_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()
    context_digest: str | None = None
    question_metadata_items: tuple[object, ...] = ()
    has_legacy_or_malformed_metadata: bool = False


@dataclass(frozen=True)
class SessionContinuitySummary:
    restored_turn_count: int
    has_progress_plan: bool
    has_progress_state: bool
    progress_tree_status: str
    fallback_reason: str | None
    warnings: tuple[str, ...]
    computed_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "restored_turn_count": self.restored_turn_count,
            "has_progress_plan": self.has_progress_plan,
            "has_progress_state": self.has_progress_state,
            "progress_tree_status": self.progress_tree_status,
            "fallback_reason": self.fallback_reason,
            "warnings": list(self.warnings),
            "computed_at": self.computed_at,
        }


@dataclass(frozen=True)
class SessionRestoredRefs:
    current_question_id: str | None
    current_progress_node_ref: str | None
    evidence_refs: tuple[str, ...]
    context_digest: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_question_id": self.current_question_id,
            "current_progress_node_ref": self.current_progress_node_ref,
            "evidence_refs": list(self.evidence_refs),
            "context_digest": self.context_digest,
        }


@dataclass(frozen=True)
class SessionContinuityResult:
    status: ContinuityStatus
    summary: SessionContinuitySummary
    restored_refs: SessionRestoredRefs

    def to_response_payload(self) -> dict[str, Any]:
        return {
            "continuity_status": self.status.value,
            "continuity_summary": self.summary.to_dict(),
            "restored_refs": self.restored_refs.to_dict(),
        }


def compute_session_continuity(
    snapshot: SessionContinuitySnapshot,
    *,
    computed_at: str | None = None,
) -> SessionContinuityResult:
    progress_status = _clean(snapshot.progress_tree_status)
    has_progress_plan = _has_progress_plan(snapshot.progress_tree_plan)
    has_progress_state = _has_progress_state(snapshot.progress_tree_state)
    malformed_metadata_present = snapshot.has_legacy_or_malformed_metadata or any(
        is_legacy_or_malformed_question_metadata(metadata)
        for metadata in snapshot.question_metadata_items
    )
    fallback_reason = _fallback_reason(
        session_status=_clean(snapshot.session_status),
        progress_status=progress_status,
        has_progress_plan=has_progress_plan,
        has_progress_state=has_progress_state,
        malformed_metadata_present=malformed_metadata_present,
    )
    status = _continuity_status(
        session_status=_clean(snapshot.session_status),
        progress_status=progress_status,
        has_progress_plan=has_progress_plan,
        has_progress_state=has_progress_state,
        malformed_metadata_present=malformed_metadata_present,
    )
    summary = SessionContinuitySummary(
        restored_turn_count=max(0, int(snapshot.turn_count)),
        has_progress_plan=has_progress_plan,
        has_progress_state=has_progress_state,
        progress_tree_status=progress_status,
        fallback_reason=fallback_reason,
        warnings=(fallback_reason,) if fallback_reason else (),
        computed_at=computed_at or utc_now().isoformat(),
    )
    restored_refs = SessionRestoredRefs(
        current_question_id=_clean(snapshot.active_question_id) or None,
        current_progress_node_ref=_clean(snapshot.active_progress_node_ref) or None,
        evidence_refs=tuple(ref for item in snapshot.evidence_refs if (ref := _clean(item))),
        context_digest=_clean(snapshot.context_digest) or None,
    )
    return SessionContinuityResult(
        status=status,
        summary=summary,
        restored_refs=restored_refs,
    )


def is_legacy_or_malformed_question_metadata(metadata: object) -> bool:
    if not isinstance(metadata, dict):
        return True
    return (
        metadata.get("context_hygiene_status") == "unknown"
        and metadata.get("question_pattern") is None
        and metadata.get("source_availability") is None
    )


def _continuity_status(
    *,
    session_status: str,
    progress_status: str,
    has_progress_plan: bool,
    has_progress_state: bool,
    malformed_metadata_present: bool,
) -> ContinuityStatus:
    if session_status not in _RUNNING_SESSION_STATUSES:
        return ContinuityStatus.BLOCKED
    if malformed_metadata_present:
        return ContinuityStatus.UNKNOWN
    if progress_status in _REFRESH_FALLBACK_STATUSES:
        return ContinuityStatus.STALE
    if has_progress_plan and not has_progress_state:
        return ContinuityStatus.STALE
    if progress_status in _PARTIAL_PROGRESS_STATUSES:
        return ContinuityStatus.PARTIAL
    if progress_status == "ready" and has_progress_plan and has_progress_state:
        return ContinuityStatus.READY
    if not progress_status:
        return ContinuityStatus.UNKNOWN
    return ContinuityStatus.PARTIAL


def _fallback_reason(
    *,
    session_status: str,
    progress_status: str,
    has_progress_plan: bool,
    has_progress_state: bool,
    malformed_metadata_present: bool,
) -> str | None:
    if session_status not in _RUNNING_SESSION_STATUSES:
        return "session_not_running"
    if malformed_metadata_present:
        return "legacy_or_malformed_metadata"
    if progress_status in _REFRESH_FALLBACK_STATUSES:
        return progress_status
    if has_progress_plan and not has_progress_state:
        return "refresh_failed"
    if progress_status == "insufficient_context":
        return "insufficient_context"
    if progress_status in {"pending", "generating"}:
        return progress_status
    if not progress_status:
        return "legacy_or_malformed_metadata"
    return None


def _has_progress_plan(plan: object) -> bool:
    nodes = plan.get("nodes") if isinstance(plan, dict) else None
    return isinstance(nodes, list) and len(nodes) > 0


def _has_progress_state(state: object) -> bool:
    node_states = state.get("node_states") if isinstance(state, dict) else None
    return isinstance(node_states, list) and len(node_states) > 0


def _clean(value: object, *, max_chars: int = 240) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text
