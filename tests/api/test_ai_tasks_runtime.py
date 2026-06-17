from __future__ import annotations

import threading
import time

import pytest

import app.api.v1.ai_tasks as ai_tasks_api
import app.api.v1.polish as polish_api
from app.api.v1.ai_tasks import router as ai_tasks_router
from app.application.llm.types import LlmTransportRequest
from app.infrastructure.db.repositories.polish import SqlAlchemyPolishRepository
from tests.api.asgi_client import call_json
from tests.api.test_polish_api import (
    ACTOR_A,
    ACTOR_B,
    OWNER_A,
    _collect_keys,
    _isolated_polish_app,
    _run_inline_threadpool,
    _session_factory,
)
from tests.api.test_polish_feedback_runtime import (
    _RecordingFeedbackTransport,
    _create_answer_ready_for_feedback,
    _runtime_test_non_feedback_result,
)
from tests.fakes.llm_transport import FakeLlmTransport


@pytest.fixture(autouse=True)
def _patch_threadpools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(polish_api, "run_in_threadpool", _run_inline_threadpool)
    if hasattr(ai_tasks_api, "run_in_threadpool"):
        monkeypatch.setattr(ai_tasks_api, "run_in_threadpool", _run_inline_threadpool)


def _isolated_runtime_app(session_factory, actor, *, llm_transport=None):
    app = _isolated_polish_app(session_factory, actor, llm_transport=llm_transport)
    app.include_router(ai_tasks_router, prefix="/api/v1")
    return app


def test_ai_task_status_and_result_read_feedback_task_without_provider_payload() -> None:
    session_factory = _session_factory()
    app = _isolated_runtime_app(session_factory, ACTOR_A, llm_transport=_RecordingFeedbackTransport())
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)

    feedback_status, feedback_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
    )
    ai_task_id = feedback_body["data"]["ai_task_id"]

    status_code, status_body = call_json(app, f"/api/v1/ai-tasks/{ai_task_id}")
    result_code, result_body = call_json(app, f"/api/v1/ai-tasks/{ai_task_id}/result")

    assert feedback_status == 202
    assert status_code == 200
    assert status_body["resource_type"] == "ai_task"
    assert status_body["data"]["ai_task_id"] == ai_task_id
    assert status_body["data"]["status"] == "succeeded"
    assert status_body["data"]["user_visible_status"] == "反馈已生成"
    assert status_body["data"]["provider_payload"] is None

    assert result_code == 200
    assert result_body["resource_type"] == "ai_task_result"
    result = result_body["data"]
    assert result["ai_task_id"] == ai_task_id
    assert result["status"] == "succeeded"
    assert result["provider_payload"] is None
    assert result["result_payload"]["status"] == "generated"
    assert result["result_payload"]["feedback_id"] == feedback_body["data"]["feedback_id"]
    assert "provider_payload" not in _collect_keys(result["result_payload"])
    assert "raw_prompt" not in _collect_keys(result)

    cross_owner_app = _isolated_runtime_app(session_factory, ACTOR_B)
    cross_status, cross_body = call_json(cross_owner_app, f"/api/v1/ai-tasks/{ai_task_id}")
    assert cross_status == 404
    assert cross_body["error"]["code"] == "not_found_or_inaccessible"


class _BlockingFeedbackRuntimeTransport:
    def __init__(self) -> None:
        self._fake = FakeLlmTransport()
        self.feedback_entered = threading.Event()
        self.release_feedback = threading.Event()

    def generate(self, request: LlmTransportRequest):
        if request.task_type == "polish_feedback_generation":
            self.feedback_entered.set()
            assert self.release_feedback.wait(timeout=2), "feedback generation was not released"
        return _runtime_test_non_feedback_result(self._fake, request)


def test_feedback_task_returns_running_state_before_slow_provider_finishes() -> None:
    session_factory = _session_factory()
    llm_transport = _BlockingFeedbackRuntimeTransport()
    app = _isolated_runtime_app(session_factory, ACTOR_A, llm_transport=llm_transport)
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)

    started_at = time.perf_counter()
    feedback_status, feedback_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
    )
    elapsed = time.perf_counter() - started_at

    assert feedback_status == 202
    assert llm_transport.feedback_entered.is_set()
    assert elapsed < 0.75
    running_task = feedback_body["data"]
    assert running_task["status"] == "running"
    assert running_task["retryable"] is False
    assert running_task["user_visible_status"] == "反馈生成中"
    assert "provider_payload" not in _collect_keys(running_task)

    ai_task_id = running_task["ai_task_id"]
    status_code, status_body = call_json(app, f"/api/v1/ai-tasks/{ai_task_id}")
    assert status_code == 200
    assert status_body["data"]["status"] == "running"
    assert status_body["data"]["provider_payload"] is None

    llm_transport.release_feedback.set()
    final_result = _wait_for_ai_task_result(app, ai_task_id)
    assert final_result["status"] == "succeeded"
    assert final_result["provider_payload"] is None
    assert final_result["result_payload"]["status"] == "generated"

    repository = SqlAlchemyPolishRepository(session_factory)
    feedbacks = repository.list_feedbacks_for_session(OWNER_A, session_id)
    assert any(feedback.ai_task_id == ai_task_id and feedback.status == "generated" for feedback in feedbacks)


def _wait_for_ai_task_result(app, ai_task_id: str) -> dict:
    deadline = time.monotonic() + 2
    last_body: dict | None = None
    while time.monotonic() < deadline:
        status_code, body = call_json(app, f"/api/v1/ai-tasks/{ai_task_id}/result")
        last_body = body
        if status_code == 200 and body["data"]["status"] != "running":
            return body["data"]
        time.sleep(0.02)
    raise AssertionError(f"AI task did not reach final state: {last_body}")
