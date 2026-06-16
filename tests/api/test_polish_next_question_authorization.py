from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.application.polish.next_question_authorization import (
    NEXT_QUESTION_EXECUTION_GRANT_SNAPSHOT_SCHEMA_ID,
    NextQuestionExecutionGrantSnapshot,
    build_next_question_execution_grant,
    consume_next_question_execution_grant,
    feedback_next_question_authorization_metadata,
    validate_consumed_next_question_execution_grant_snapshot,
    validate_feedback_next_question_authorization_payload,
    validate_next_question_intent,
)
from app.application.polish.question_metadata import (
    next_question_execution_grant_snapshot_to_metadata,
    question_metadata_to_dict,
)


def _grant(now: datetime | None = None):
    issued_at = now or datetime(2026, 6, 16, 1, 0, tzinfo=UTC)
    return build_next_question_execution_grant(
        session_id="session-1",
        feedback_id="feedback-1",
        answer_id="answer-1",
        parent_question_id="question-1",
        selected_progress_node_ref="node-allowed",
        allowed_progress_node_refs=("node-allowed", "node-peer"),
        freshness_marker="feedback-1:v1",
        reason_codes=("feedback_next_question_intent",),
        grant_id="nqg_unit_test",
        issued_at=issued_at,
        ttl_seconds=60,
    )


def test_build_next_question_execution_grant_carries_authorization_lock_set() -> None:
    now = datetime(2026, 6, 16, 1, 0, tzinfo=UTC)
    grant = _grant(now)

    assert grant.grant_id == "nqg_unit_test"
    assert grant.session_id == "session-1"
    assert grant.feedback_id == "feedback-1"
    assert grant.answer_id == "answer-1"
    assert grant.parent_question_id == "question-1"
    assert grant.selected_progress_node_ref == "node-allowed"
    assert grant.allowed_progress_node_refs == ("node-allowed", "node-peer")
    assert grant.freshness_marker == "feedback-1:v1"
    assert grant.reason_codes == ("feedback_next_question_intent",)
    assert grant.issued_at == now
    assert grant.expires_at == now + timedelta(seconds=60)
    assert grant.consumed_at is None
    assert grant.lifecycle_state(now=now) == "active"


def test_validate_next_question_intent_accepts_matching_current_intent() -> None:
    now = datetime(2026, 6, 16, 1, 0, tzinfo=UTC)
    result = validate_next_question_intent(
        _grant(now),
        session_id="session-1",
        feedback_id="feedback-1",
        answer_id="answer-1",
        parent_question_id="question-1",
        selected_progress_node_ref="node-allowed",
        freshness_marker="feedback-1:v1",
        now=now,
    )

    assert result.is_valid
    assert result.grant is not None
    assert result.reason is None


def test_validate_next_question_intent_rejects_expired_grant() -> None:
    now = datetime(2026, 6, 16, 1, 0, tzinfo=UTC)
    result = validate_next_question_intent(
        _grant(now),
        session_id="session-1",
        feedback_id="feedback-1",
        answer_id="answer-1",
        parent_question_id="question-1",
        selected_progress_node_ref="node-allowed",
        freshness_marker="feedback-1:v1",
        now=now + timedelta(seconds=61),
    )

    assert not result.is_valid
    assert result.reason == "grant_expired"
    assert result.details["lifecycle_state"] == "expired"


def test_validate_next_question_intent_rejects_consumed_grant() -> None:
    now = datetime(2026, 6, 16, 1, 0, tzinfo=UTC)
    consumed = consume_next_question_execution_grant(_grant(now), now=now)
    assert consumed.grant is not None

    result = validate_next_question_intent(
        consumed.grant,
        session_id="session-1",
        feedback_id="feedback-1",
        answer_id="answer-1",
        parent_question_id="question-1",
        selected_progress_node_ref="node-allowed",
        freshness_marker="feedback-1:v1",
        now=now,
    )

    assert not result.is_valid
    assert result.reason == "grant_already_consumed"
    assert result.details["lifecycle_state"] == "consumed"


def test_validate_next_question_intent_rejects_session_and_freshness_mismatch() -> None:
    now = datetime(2026, 6, 16, 1, 0, tzinfo=UTC)
    session_result = validate_next_question_intent(
        _grant(now),
        session_id="session-other",
        feedback_id="feedback-1",
        answer_id="answer-1",
        parent_question_id="question-1",
        selected_progress_node_ref="node-allowed",
        freshness_marker="feedback-1:v1",
        now=now,
    )
    freshness_result = validate_next_question_intent(
        _grant(now),
        session_id="session-1",
        feedback_id="feedback-1",
        answer_id="answer-1",
        parent_question_id="question-1",
        selected_progress_node_ref="node-allowed",
        freshness_marker="feedback-1:v0",
        now=now,
    )

    assert session_result.reason == "session_mismatch"
    assert freshness_result.reason == "feedback_freshness_mismatch"


def test_validate_next_question_intent_rejects_feedback_answer_and_parent_mismatch() -> None:
    now = datetime(2026, 6, 16, 1, 0, tzinfo=UTC)

    feedback_result = validate_next_question_intent(
        _grant(now),
        session_id="session-1",
        feedback_id="feedback-other",
        answer_id="answer-1",
        parent_question_id="question-1",
        selected_progress_node_ref="node-allowed",
        freshness_marker="feedback-1:v1",
        now=now,
    )
    answer_result = validate_next_question_intent(
        _grant(now),
        session_id="session-1",
        feedback_id="feedback-1",
        answer_id="answer-other",
        parent_question_id="question-1",
        selected_progress_node_ref="node-allowed",
        freshness_marker="feedback-1:v1",
        now=now,
    )
    parent_result = validate_next_question_intent(
        _grant(now),
        session_id="session-1",
        feedback_id="feedback-1",
        answer_id="answer-1",
        parent_question_id="question-other",
        selected_progress_node_ref="node-allowed",
        freshness_marker="feedback-1:v1",
        now=now,
    )

    assert feedback_result.reason == "feedback_mismatch"
    assert answer_result.reason == "answer_mismatch"
    assert parent_result.reason == "parent_question_mismatch"


def test_validate_next_question_intent_rejects_target_mismatch_and_not_allowed() -> None:
    now = datetime(2026, 6, 16, 1, 0, tzinfo=UTC)
    locked_target = validate_next_question_intent(
        _grant(now),
        session_id="session-1",
        feedback_id="feedback-1",
        answer_id="answer-1",
        parent_question_id="question-1",
        selected_progress_node_ref="node-other",
        freshness_marker="feedback-1:v1",
        now=now,
    )
    grant_without_selected_ref = build_next_question_execution_grant(
        session_id="session-1",
        feedback_id="feedback-1",
        answer_id="answer-1",
        parent_question_id="question-1",
        allowed_progress_node_refs=("node-allowed",),
        freshness_marker="feedback-1:v1",
        issued_at=now,
    )
    not_allowed = validate_next_question_intent(
        grant_without_selected_ref,
        session_id="session-1",
        feedback_id="feedback-1",
        answer_id="answer-1",
        parent_question_id="question-1",
        selected_progress_node_ref="node-other",
        freshness_marker="feedback-1:v1",
        now=now,
    )

    assert locked_target.reason == "target_progress_node_mismatch"
    assert not_allowed.reason == "target_progress_node_not_allowed"
    assert not_allowed.details["allowed_progress_node_refs"] == ["node-allowed"]


def test_consume_next_question_execution_grant_is_one_time_only() -> None:
    now = datetime(2026, 6, 16, 1, 0, tzinfo=UTC)
    first = consume_next_question_execution_grant(_grant(now), now=now)

    assert first.is_valid
    assert first.grant is not None
    assert first.grant.consumed_at == now

    second = consume_next_question_execution_grant(first.grant, now=now)
    assert not second.is_valid
    assert second.reason == "grant_already_consumed"


def test_next_question_execution_grant_snapshot_serializes_safe_metadata_shape() -> None:
    now = datetime(2026, 6, 16, 1, 0, tzinfo=UTC)
    consumed = consume_next_question_execution_grant(_grant(now), now=now)
    assert consumed.grant is not None
    snapshot = NextQuestionExecutionGrantSnapshot.from_grant(consumed.grant, now=now).to_dict()

    assert snapshot == {
        "schema_id": NEXT_QUESTION_EXECUTION_GRANT_SNAPSHOT_SCHEMA_ID,
        "schema_version": "1",
        "grant_id": "nqg_unit_test",
        "session_id": "session-1",
        "feedback_id": "feedback-1",
        "answer_id": "answer-1",
        "parent_question_id": "question-1",
        "selected_progress_node_ref": "node-allowed",
        "allowed_progress_node_refs": ["node-allowed", "node-peer"],
        "freshness_marker": "feedback-1:v1",
        "reason_codes": ["feedback_next_question_intent"],
        "issued_at": "2026-06-16T01:00:00Z",
        "expires_at": "2026-06-16T01:01:00Z",
        "consumed_at": "2026-06-16T01:00:00Z",
        "lifecycle_state": "consumed",
    }


def test_next_question_execution_grant_snapshot_metadata_helper_preserves_normalized_snapshot() -> None:
    now = datetime(2026, 6, 16, 1, 0, tzinfo=UTC)
    snapshot = _grant(now).to_snapshot(now=now)

    metadata = next_question_execution_grant_snapshot_to_metadata(snapshot)
    normalized = question_metadata_to_dict(metadata)

    assert normalized["next_question_execution_grant"]["schema_id"] == (
        NEXT_QUESTION_EXECUTION_GRANT_SNAPSHOT_SCHEMA_ID
    )
    assert normalized["next_question_execution_grant"]["grant_id"] == "nqg_unit_test"
    assert normalized["next_question_execution_grant"]["allowed_progress_node_refs"] == [
        "node-allowed",
        "node-peer",
    ]
    assert normalized["next_question_execution_grant"]["lifecycle_state"] == "active"


def test_validate_consumed_next_question_execution_grant_snapshot_rejects_missing_snapshot() -> None:
    result = validate_consumed_next_question_execution_grant_snapshot(
        None,
        session_id="session-1",
        feedback_id="feedback-1",
        answer_id="answer-1",
        parent_question_id="question-1",
        selected_progress_node_ref="node-allowed",
    )

    assert not result.is_valid
    assert result.reason == "next_question_execution_grant_required"
    assert result.details["field"] == "next_question_execution_grant"


def test_validate_consumed_next_question_execution_grant_snapshot_requires_consumed_state() -> None:
    now = datetime(2026, 6, 16, 1, 0, tzinfo=UTC)
    active_snapshot = _grant(now).to_snapshot(now=now).to_dict()
    expired_snapshot = _grant(now).to_snapshot(now=now + timedelta(seconds=61)).to_dict()

    active_result = validate_consumed_next_question_execution_grant_snapshot(
        active_snapshot,
        session_id="session-1",
        feedback_id="feedback-1",
        answer_id="answer-1",
        parent_question_id="question-1",
        selected_progress_node_ref="node-allowed",
    )
    expired_result = validate_consumed_next_question_execution_grant_snapshot(
        expired_snapshot,
        session_id="session-1",
        feedback_id="feedback-1",
        answer_id="answer-1",
        parent_question_id="question-1",
        selected_progress_node_ref="node-allowed",
    )

    assert active_result.reason == "grant_not_consumed"
    assert expired_result.reason == "grant_expired"


def test_validate_consumed_next_question_execution_grant_snapshot_accepts_trusted_snapshot() -> None:
    now = datetime(2026, 6, 16, 1, 0, tzinfo=UTC)
    consumed = consume_next_question_execution_grant(_grant(now), now=now)
    assert consumed.grant is not None

    result = validate_consumed_next_question_execution_grant_snapshot(
        consumed.grant.to_snapshot(now=now),
        session_id="session-1",
        feedback_id="feedback-1",
        answer_id="answer-1",
        parent_question_id="question-1",
        selected_progress_node_ref="node-allowed",
    )

    assert result.is_valid


def test_validate_feedback_next_question_authorization_payload_rejects_tamper() -> None:
    payload = {
        "feedback_id": "feedback-1",
        "status": "generated",
        "asset_consistency_check": {"status": "conflict", "conflicts": [{"conflict_type": "asset"}]},
        "answer_coverage": {"missing_points": ["缺少幂等失败处理"]},
        "answer_change_analysis": {"regressed_points": []},
        "project_asset_update_candidates": [],
        "low_confidence_flags": [],
        "feedback_metadata": {
            "generated": True,
            "llm_called": True,
            "task_type": "polish_feedback_generation",
            "answer_id": "answer-1",
            "question_id": "question-1",
            "session_id": "session-1",
        },
    }
    payload["feedback_metadata"].update(feedback_next_question_authorization_metadata(payload))

    valid = validate_feedback_next_question_authorization_payload(
        payload,
        feedback_id="feedback-1",
        session_id="session-1",
        answer_id="answer-1",
        parent_question_id="question-1",
    )
    payload["asset_consistency_check"] = {"status": "aligned", "conflicts": []}
    tampered = validate_feedback_next_question_authorization_payload(
        payload,
        feedback_id="feedback-1",
        session_id="session-1",
        answer_id="answer-1",
        parent_question_id="question-1",
    )

    assert valid.is_valid
    assert tampered.reason == "feedback_payload_tamper_rejected"
