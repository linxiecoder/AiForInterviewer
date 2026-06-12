from __future__ import annotations

import inspect

import app.api.v1.polish as polish_api
from app.application.polish.session_continuity import (
    ContinuityStatus,
    SessionContinuitySnapshot,
    compute_session_continuity,
)


def test_compute_session_continuity_maps_refresh_failed_to_stale_payload() -> None:
    snapshot = SessionContinuitySnapshot(
        session_status="running",
        progress_tree_status="refresh_failed",
        progress_tree_plan={
            "status": "ready",
            "nodes": [{"progress_node_ref": "node_legacy", "children": []}],
        },
        progress_tree_state={
            "status": "refresh_failed",
            "node_states": [{"progress_node_ref": "node_legacy", "status": "pending"}],
        },
        turn_count=1,
        active_question_id="que_legacy",
        active_progress_node_ref="node_legacy",
        evidence_refs=("ev_1",),
        context_digest="digest_1",
        has_legacy_or_malformed_metadata=False,
    )

    result = compute_session_continuity(
        snapshot,
        computed_at="2026-06-12T00:00:00+00:00",
    )

    assert result.status is ContinuityStatus.STALE
    assert result.summary.fallback_reason == "refresh_failed"
    assert result.to_response_payload() == {
        "continuity_status": "stale",
        "continuity_summary": {
            "restored_turn_count": 1,
            "has_progress_plan": True,
            "has_progress_state": True,
            "progress_tree_status": "refresh_failed",
            "fallback_reason": "refresh_failed",
            "warnings": ["refresh_failed"],
            "computed_at": "2026-06-12T00:00:00+00:00",
        },
        "restored_refs": {
            "current_question_id": "que_legacy",
            "current_progress_node_ref": "node_legacy",
            "evidence_refs": ["ev_1"],
            "context_digest": "digest_1",
        },
    }


def test_polish_api_delegates_session_continuity_rules_to_application_helper() -> None:
    source = inspect.getsource(polish_api._session_response)

    assert "compute_session_continuity" in source
    assert not hasattr(polish_api, "_session_continuity_payload")
    assert not hasattr(polish_api, "_session_continuity_status")
    assert not hasattr(polish_api, "_session_continuity_fallback_reason")
