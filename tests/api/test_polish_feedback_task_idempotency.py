from __future__ import annotations

from sqlalchemy import text

import app.api.v1.polish as polish_api
from tests.api.asgi_client import call_json
from tests.api.test_polish_api import (
    ACTOR_A,
    _isolated_polish_app,
    _run_inline_threadpool,
    _session_factory,
)
from tests.api.test_polish_feedback_runtime import (
    _RecordingFeedbackTransport,
    _create_answer_ready_for_feedback,
)


def test_feedback_requires_idempotency_key_before_generation(monkeypatch) -> None:
    monkeypatch.setattr(polish_api, "run_in_threadpool", _run_inline_threadpool)
    session_factory = _session_factory()
    llm_transport = _RecordingFeedbackTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=llm_transport)
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)

    status, body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
    )

    assert status == 400
    assert body["error"]["code"] == "idempotency_required"
    assert body["error"]["details"]["field"] == "Idempotency-Key"
    assert body["error"]["retryable"] is True
    assert len(llm_transport.feedback_requests) == 0
    assert _count_rows(session_factory, "ai_tasks", "target_ref_id", answer_id) == 0
    assert _count_rows(session_factory, "feedback", "answer_id", answer_id) == 0


def test_feedback_idempotency_key_replays_task_result_without_second_generation(monkeypatch) -> None:
    monkeypatch.setattr(polish_api, "run_in_threadpool", _run_inline_threadpool)
    session_factory = _session_factory()
    llm_transport = _RecordingFeedbackTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=llm_transport)
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)

    first_status, first_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
        headers={"Idempotency-Key": "feedback-replay-key-001"},
    )
    calls_after_first_request = len(llm_transport.feedback_requests)
    second_status, second_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
        headers={"Idempotency-Key": "feedback-replay-key-001"},
    )

    assert first_status == 202
    for retired_top_level_key in ("feedback_text", "score_result", "low_confidence_flags", "trace_refs"):
        assert retired_top_level_key not in first_body["data"]
    assert first_body["data"]["summary"] == first_body["data"]["feedback_payload"]["feedback_text"]
    assert "score_ref" in first_body["data"]
    assert "loss_point_refs" in first_body["data"]
    assert second_status == 202
    for retired_top_level_key in ("feedback_text", "score_result", "low_confidence_flags", "trace_refs"):
        assert retired_top_level_key not in second_body["data"]
    assert second_body["data"]["ai_task_id"] == first_body["data"]["ai_task_id"]
    assert second_body["data"]["feedback_id"] == first_body["data"]["feedback_id"]
    assert second_body["data"]["feedback_payload"]["feedback_id"] == first_body["data"]["feedback_id"]
    assert calls_after_first_request > 0
    assert len(llm_transport.feedback_requests) == calls_after_first_request
    assert _count_rows(session_factory, "ai_tasks", "target_ref_id", answer_id) == 1
    assert _count_rows(session_factory, "feedback", "answer_id", answer_id) == 1
    assert _count_rows(session_factory, "ai_task_results", "ai_task_id", first_body["data"]["ai_task_id"]) == 1


def test_feedback_idempotency_key_conflict_rejects_different_body_without_second_write(monkeypatch) -> None:
    monkeypatch.setattr(polish_api, "run_in_threadpool", _run_inline_threadpool)
    session_factory = _session_factory()
    llm_transport = _RecordingFeedbackTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=llm_transport)
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)

    first_status, first_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
        headers={"Idempotency-Key": "feedback-conflict-key-001"},
    )
    calls_after_first_request = len(llm_transport.feedback_requests)
    conflict_status, conflict_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={
            "answer_id": answer_id,
            "scoring_context": {"rubric_version": "different-request-body"},
        },
        headers={"Idempotency-Key": "feedback-conflict-key-001"},
    )

    assert first_status == 202
    assert first_body["data"]["feedback_status"] == "generated"
    assert conflict_status == 409
    assert conflict_body["error"]["code"] == "idempotency_conflict"
    assert calls_after_first_request > 0
    assert len(llm_transport.feedback_requests) == calls_after_first_request
    assert _count_rows(session_factory, "ai_tasks", "target_ref_id", answer_id) == 1
    assert _count_rows(session_factory, "feedback", "answer_id", answer_id) == 1


def _count_rows(session_factory, table_name: str, column_name: str, value: str) -> int:
    with session_factory() as db:
        return int(
            db.execute(
                text(f"select count(*) from {table_name} where {column_name} = :value"),
                {"value": value},
            ).scalar_one()
        )
