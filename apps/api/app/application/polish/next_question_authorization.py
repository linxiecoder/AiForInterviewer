"""Additive next-question execution grant model for Polish follow-up intent."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any, Callable, Iterable
from uuid import uuid4


NEXT_QUESTION_EXECUTION_GRANT_SNAPSHOT_SCHEMA_ID = "polish_next_question_execution_grant_snapshot"
NEXT_QUESTION_EXECUTION_GRANT_SNAPSHOT_SCHEMA_VERSION = "1"
NEXT_QUESTION_EXECUTION_GRANT_TTL_SECONDS = 300
NEXT_QUESTION_AUTHORIZATION_DIGEST_METADATA_KEY = "next_question_authorization_digest"
NEXT_QUESTION_AUTHORIZATION_DIGEST_VERSION_METADATA_KEY = "next_question_authorization_digest_version"
NEXT_QUESTION_AUTHORIZATION_DIGEST_VERSION = "1"
_AUTHORIZATION_PAYLOAD_KEYS = (
    "feedback_id",
    "status",
    "asset_consistency_check",
    "answer_coverage",
    "answer_change_analysis",
    "project_asset_update_candidates",
    "low_confidence_flags",
)
_AUTHORIZATION_METADATA_KEYS = (
    "generated",
    "llm_called",
    "task_type",
    "answer_id",
    "question_id",
    "session_id",
)


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


def feedback_next_question_authorization_metadata(payload: dict[str, Any]) -> dict[str, str]:
    return {
        NEXT_QUESTION_AUTHORIZATION_DIGEST_VERSION_METADATA_KEY: NEXT_QUESTION_AUTHORIZATION_DIGEST_VERSION,
        NEXT_QUESTION_AUTHORIZATION_DIGEST_METADATA_KEY: feedback_next_question_authorization_digest(payload),
    }


def feedback_next_question_authorization_digest(payload: dict[str, Any]) -> str:
    digest_payload = _feedback_next_question_authorization_digest_payload(payload)
    encoded = json.dumps(
        digest_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def validate_feedback_next_question_authorization_payload(
    payload: object,
    *,
    feedback_id: str,
    session_id: str,
    answer_id: str,
    parent_question_id: str,
) -> NextQuestionExecutionGrantValidationResult:
    if not isinstance(payload, dict):
        return NextQuestionExecutionGrantValidationResult(
            is_valid=False,
            reason="feedback_payload_missing",
            details={"field": "feedback_summary"},
        )

    metadata = payload.get("feedback_metadata") if isinstance(payload.get("feedback_metadata"), dict) else {}
    expected_identity = {
        "feedback_id": feedback_id,
        "session_id": session_id,
        "answer_id": answer_id,
        "question_id": parent_question_id,
    }
    actual_identity = {
        "feedback_id": _optional_text(payload.get("feedback_id")),
        "session_id": _optional_text(metadata.get("session_id")),
        "answer_id": _optional_text(metadata.get("answer_id")),
        "question_id": _optional_text(metadata.get("question_id")),
    }
    for field_name, expected in expected_identity.items():
        if _optional_text(expected) != actual_identity[field_name]:
            return NextQuestionExecutionGrantValidationResult(
                is_valid=False,
                reason="feedback_payload_identity_mismatch",
                details={
                    "field": field_name,
                    "expected": expected,
                    "actual": actual_identity[field_name],
                },
            )

    digest_version = _optional_text(metadata.get(NEXT_QUESTION_AUTHORIZATION_DIGEST_VERSION_METADATA_KEY))
    if digest_version != NEXT_QUESTION_AUTHORIZATION_DIGEST_VERSION:
        return NextQuestionExecutionGrantValidationResult(
            is_valid=False,
            reason="feedback_payload_authorization_digest_missing",
            details={
                "field": NEXT_QUESTION_AUTHORIZATION_DIGEST_VERSION_METADATA_KEY,
                "expected": NEXT_QUESTION_AUTHORIZATION_DIGEST_VERSION,
                "actual": digest_version,
            },
        )
    expected_digest = _optional_text(metadata.get(NEXT_QUESTION_AUTHORIZATION_DIGEST_METADATA_KEY))
    if expected_digest is None:
        return NextQuestionExecutionGrantValidationResult(
            is_valid=False,
            reason="feedback_payload_authorization_digest_missing",
            details={"field": NEXT_QUESTION_AUTHORIZATION_DIGEST_METADATA_KEY},
        )
    actual_digest = feedback_next_question_authorization_digest(payload)
    if actual_digest != expected_digest:
        return NextQuestionExecutionGrantValidationResult(
            is_valid=False,
            reason="feedback_payload_tamper_rejected",
            details={
                "field": NEXT_QUESTION_AUTHORIZATION_DIGEST_METADATA_KEY,
                "expected": expected_digest,
                "actual": actual_digest,
            },
        )
    return NextQuestionExecutionGrantValidationResult(is_valid=True)


def validate_consumed_next_question_execution_grant_snapshot(
    snapshot: object,
    *,
    session_id: str,
    feedback_id: str,
    answer_id: str,
    parent_question_id: str,
    selected_progress_node_ref: str | None = None,
) -> NextQuestionExecutionGrantValidationResult:
    source = _snapshot_dict(snapshot)
    grant_id = _optional_text(source.get("grant_id"))
    if grant_id is None:
        return NextQuestionExecutionGrantValidationResult(
            is_valid=False,
            reason="next_question_execution_grant_required",
            details={"field": "next_question_execution_grant"},
        )
    schema_id = _optional_text(source.get("schema_id"))
    if schema_id != NEXT_QUESTION_EXECUTION_GRANT_SNAPSHOT_SCHEMA_ID:
        return NextQuestionExecutionGrantValidationResult(
            is_valid=False,
            reason="grant_snapshot_schema_mismatch",
            details={
                "grant_id": grant_id,
                "field": "schema_id",
                "expected": NEXT_QUESTION_EXECUTION_GRANT_SNAPSHOT_SCHEMA_ID,
                "actual": schema_id,
            },
        )
    lifecycle_state = _optional_text(source.get("lifecycle_state"))
    if lifecycle_state == "expired":
        return NextQuestionExecutionGrantValidationResult(
            is_valid=False,
            reason="grant_expired",
            details={"grant_id": grant_id, "lifecycle_state": lifecycle_state},
        )
    if lifecycle_state != "consumed" or _optional_text(source.get("consumed_at")) is None:
        return NextQuestionExecutionGrantValidationResult(
            is_valid=False,
            reason="grant_not_consumed",
            details={
                "grant_id": grant_id,
                "lifecycle_state": lifecycle_state,
                "field": "consumed_at",
            },
        )

    expected_fields = {
        "session_id": session_id,
        "feedback_id": feedback_id,
        "answer_id": answer_id,
        "parent_question_id": parent_question_id,
    }
    for field_name, expected in expected_fields.items():
        actual = _optional_text(source.get(field_name))
        if _optional_text(expected) != actual:
            return NextQuestionExecutionGrantValidationResult(
                is_valid=False,
                reason=f"{field_name.removesuffix('_id')}_mismatch",
                details={
                    "grant_id": grant_id,
                    "field": field_name,
                    "expected": expected,
                    "actual": actual,
                },
            )

    selected_ref = _optional_text(selected_progress_node_ref)
    snapshot_selected_ref = _optional_text(source.get("selected_progress_node_ref"))
    if selected_ref is not None and snapshot_selected_ref != selected_ref:
        return NextQuestionExecutionGrantValidationResult(
            is_valid=False,
            reason="target_node_not_allowed",
            details={
                "grant_id": grant_id,
                "field": "selected_progress_node_ref",
                "expected": snapshot_selected_ref,
                "actual": selected_ref,
            },
        )
    allowed_refs = _string_tuple(source.get("allowed_progress_node_refs", ()))
    if selected_ref is not None and allowed_refs and selected_ref not in allowed_refs:
        return NextQuestionExecutionGrantValidationResult(
            is_valid=False,
            reason="target_node_not_allowed",
            details={
                "grant_id": grant_id,
                "field": "selected_progress_node_ref",
                "allowed_progress_node_refs": list(allowed_refs),
                "actual": selected_ref,
            },
        )
    return NextQuestionExecutionGrantValidationResult(is_valid=True)


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


def _feedback_next_question_authorization_digest_payload(payload: dict[str, Any]) -> dict[str, Any]:
    metadata = payload.get("feedback_metadata") if isinstance(payload.get("feedback_metadata"), dict) else {}
    return {
        "digest_version": NEXT_QUESTION_AUTHORIZATION_DIGEST_VERSION,
        "payload": {key: _stable_json_value(payload.get(key)) for key in _AUTHORIZATION_PAYLOAD_KEYS},
        "feedback_metadata": {
            key: _stable_json_value(metadata.get(key)) for key in _AUTHORIZATION_METADATA_KEYS
        },
    }


def _snapshot_dict(snapshot: object) -> dict[str, Any]:
    if isinstance(snapshot, dict):
        return snapshot
    to_dict = getattr(snapshot, "to_dict", None)
    if callable(to_dict):
        candidate = to_dict()
        return candidate if isinstance(candidate, dict) else {}
    return {}


def _stable_json_value(value: object) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {
            str(key): _stable_json_value(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    if isinstance(value, (list, tuple)):
        return [_stable_json_value(item) for item in value]
    if isinstance(value, set):
        return [_stable_json_value(item) for item in sorted(value, key=lambda item: str(item))]
    return str(value)
