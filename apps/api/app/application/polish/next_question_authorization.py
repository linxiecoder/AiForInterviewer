"""Additive next-question execution grant model for Polish follow-up intent."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from typing import Any, Callable, Iterable
from uuid import uuid4


NEXT_QUESTION_EXECUTION_GRANT_SNAPSHOT_SCHEMA_ID = "polish_next_question_execution_grant_snapshot"
NEXT_QUESTION_EXECUTION_GRANT_SNAPSHOT_SCHEMA_VERSION = "1"
NEXT_QUESTION_EXECUTION_GRANT_TTL_SECONDS = 300


@dataclass(frozen=True)
class NextQuestionExecutionGrant:
    grant_id: str
    session_id: str
    feedback_id: str
    answer_id: str
    parent_question_id: str
    freshness_marker: str
    issued_at: datetime
    expires_at: datetime
    selected_progress_node_ref: str | None = None
    allowed_progress_node_refs: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    consumed_at: datetime | None = None

    def lifecycle_state(self, *, now: datetime | None = None) -> str:
        if self.consumed_at is not None:
            return "consumed"
        if _as_utc(now) >= _as_utc(self.expires_at):
            return "expired"
        return "active"

    def to_snapshot(self, *, now: datetime | None = None) -> "NextQuestionExecutionGrantSnapshot":
        return NextQuestionExecutionGrantSnapshot.from_grant(self, now=now)


@dataclass(frozen=True)
class NextQuestionExecutionGrantSnapshot:
    grant_id: str
    session_id: str
    feedback_id: str
    answer_id: str
    parent_question_id: str
    freshness_marker: str
    issued_at: str
    expires_at: str
    lifecycle_state: str
    selected_progress_node_ref: str | None = None
    allowed_progress_node_refs: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    consumed_at: str | None = None
    schema_id: str = NEXT_QUESTION_EXECUTION_GRANT_SNAPSHOT_SCHEMA_ID
    schema_version: str = NEXT_QUESTION_EXECUTION_GRANT_SNAPSHOT_SCHEMA_VERSION

    @classmethod
    def from_grant(
        cls,
        grant: NextQuestionExecutionGrant,
        *,
        now: datetime | None = None,
    ) -> "NextQuestionExecutionGrantSnapshot":
        return cls(
            schema_id=NEXT_QUESTION_EXECUTION_GRANT_SNAPSHOT_SCHEMA_ID,
            schema_version=NEXT_QUESTION_EXECUTION_GRANT_SNAPSHOT_SCHEMA_VERSION,
            grant_id=grant.grant_id,
            session_id=grant.session_id,
            feedback_id=grant.feedback_id,
            answer_id=grant.answer_id,
            parent_question_id=grant.parent_question_id,
            selected_progress_node_ref=grant.selected_progress_node_ref,
            allowed_progress_node_refs=grant.allowed_progress_node_refs,
            freshness_marker=grant.freshness_marker,
            reason_codes=grant.reason_codes,
            issued_at=_isoformat_utc(grant.issued_at),
            expires_at=_isoformat_utc(grant.expires_at),
            consumed_at=_isoformat_utc(grant.consumed_at) if grant.consumed_at is not None else None,
            lifecycle_state=grant.lifecycle_state(now=now),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "grant_id": self.grant_id,
            "session_id": self.session_id,
            "feedback_id": self.feedback_id,
            "answer_id": self.answer_id,
            "parent_question_id": self.parent_question_id,
            "selected_progress_node_ref": self.selected_progress_node_ref,
            "allowed_progress_node_refs": list(self.allowed_progress_node_refs),
            "freshness_marker": self.freshness_marker,
            "reason_codes": list(self.reason_codes),
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "consumed_at": self.consumed_at,
            "lifecycle_state": self.lifecycle_state,
        }


@dataclass(frozen=True)
class NextQuestionExecutionGrantValidationResult:
    is_valid: bool
    grant: NextQuestionExecutionGrant | None = None
    reason: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


def build_next_question_execution_grant(
    *,
    session_id: str,
    feedback_id: str,
    answer_id: str,
    parent_question_id: str,
    freshness_marker: str,
    selected_progress_node_ref: str | None = None,
    allowed_progress_node_refs: Iterable[str] = (),
    reason_codes: Iterable[str] = (),
    grant_id: str | None = None,
    issued_at: datetime | None = None,
    expires_at: datetime | None = None,
    ttl_seconds: int = NEXT_QUESTION_EXECUTION_GRANT_TTL_SECONDS,
) -> NextQuestionExecutionGrant:
    issued = _as_utc(issued_at)
    expires = _as_utc(expires_at) if expires_at is not None else issued + timedelta(seconds=ttl_seconds)
    return NextQuestionExecutionGrant(
        grant_id=_required_text(grant_id, default_factory=lambda: f"nqg_{uuid4().hex}"),
        session_id=_required_text(session_id),
        feedback_id=_required_text(feedback_id),
        answer_id=_required_text(answer_id),
        parent_question_id=_required_text(parent_question_id),
        selected_progress_node_ref=_optional_text(selected_progress_node_ref),
        allowed_progress_node_refs=_string_tuple(allowed_progress_node_refs),
        freshness_marker=_required_text(freshness_marker),
        reason_codes=_string_tuple(reason_codes),
        issued_at=issued,
        expires_at=expires,
    )


def validate_next_question_intent(
    grant: NextQuestionExecutionGrant,
    *,
    session_id: str,
    feedback_id: str,
    answer_id: str,
    parent_question_id: str,
    selected_progress_node_ref: str | None = None,
    freshness_marker: str | None = None,
    now: datetime | None = None,
) -> NextQuestionExecutionGrantValidationResult:
    lifecycle_state = grant.lifecycle_state(now=now)
    if lifecycle_state == "expired":
        return _invalid("grant_expired", grant, lifecycle_state=lifecycle_state)
    if lifecycle_state == "consumed":
        return _invalid("grant_already_consumed", grant, lifecycle_state=lifecycle_state)
    actual_session_id = _optional_text(session_id)
    if actual_session_id != grant.session_id:
        return _invalid("session_mismatch", grant, expected=grant.session_id, actual=session_id)
    actual_feedback_id = _optional_text(feedback_id)
    if actual_feedback_id != grant.feedback_id:
        return _invalid("feedback_mismatch", grant, expected=grant.feedback_id, actual=feedback_id)
    actual_answer_id = _optional_text(answer_id)
    if actual_answer_id != grant.answer_id:
        return _invalid("answer_mismatch", grant, expected=grant.answer_id, actual=answer_id)
    actual_parent_question_id = _optional_text(parent_question_id)
    if actual_parent_question_id != grant.parent_question_id:
        return _invalid(
            "parent_question_mismatch",
            grant,
            expected=grant.parent_question_id,
            actual=parent_question_id,
        )
    actual_freshness_marker = _optional_text(freshness_marker)
    if actual_freshness_marker is not None and actual_freshness_marker != grant.freshness_marker:
        return _invalid(
            "feedback_freshness_mismatch",
            grant,
            expected=grant.freshness_marker,
            actual=freshness_marker,
        )

    selected_ref = _optional_text(selected_progress_node_ref)
    if (
        selected_ref is not None
        and grant.selected_progress_node_ref is not None
        and selected_ref != grant.selected_progress_node_ref
    ):
        return _invalid(
            "target_progress_node_mismatch",
            grant,
            expected=grant.selected_progress_node_ref,
            actual=selected_ref,
        )
    if selected_ref is not None and grant.allowed_progress_node_refs:
        if selected_ref not in grant.allowed_progress_node_refs:
            return _invalid(
                "target_progress_node_not_allowed",
                grant,
                allowed_progress_node_refs=list(grant.allowed_progress_node_refs),
                actual=selected_ref,
            )
    return NextQuestionExecutionGrantValidationResult(is_valid=True, grant=grant)


def consume_next_question_execution_grant(
    grant: NextQuestionExecutionGrant,
    *,
    now: datetime | None = None,
) -> NextQuestionExecutionGrantValidationResult:
    consumed_at = _as_utc(now)
    lifecycle_state = grant.lifecycle_state(now=consumed_at)
    if lifecycle_state == "expired":
        return _invalid("grant_expired", grant, lifecycle_state=lifecycle_state)
    if lifecycle_state == "consumed":
        return _invalid("grant_already_consumed", grant, lifecycle_state=lifecycle_state)
    return NextQuestionExecutionGrantValidationResult(
        is_valid=True,
        grant=replace(grant, consumed_at=consumed_at),
    )


def _invalid(
    reason: str,
    grant: NextQuestionExecutionGrant,
    **details: Any,
) -> NextQuestionExecutionGrantValidationResult:
    return NextQuestionExecutionGrantValidationResult(
        is_valid=False,
        grant=None,
        reason=reason,
        details={"grant_id": grant.grant_id, **details},
    )


def _as_utc(value: datetime | None = None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _isoformat_utc(value: datetime) -> str:
    return _as_utc(value).isoformat().replace("+00:00", "Z")


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _required_text(value: object, *, default_factory: Callable[[], object] | None = None) -> str:
    cleaned = _optional_text(value)
    if cleaned is not None:
        return cleaned
    if default_factory is not None:
        return str(default_factory())
    raise ValueError("next_question_execution_grant_required_field_empty")


def _string_tuple(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, str):
        values = (values,)
    result: list[str] = []
    for value in values:
        cleaned = _optional_text(value)
        if cleaned is not None and cleaned not in result:
            result.append(cleaned)
    return tuple(result)
