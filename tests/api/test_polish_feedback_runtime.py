from __future__ import annotations

import pytest
from sqlalchemy import text

from app.api.v1 import polish as polish_api
from app.application.llm.types import LlmTransportRequest
from app.infrastructure.db.repositories.polish import SqlAlchemyPolishRepository
from app.infrastructure.llm.fake_transport import FakeLlmTransport
from tests.api.asgi_client import call_json
from tests.api.test_polish_api import (
    ACTOR_A,
    OWNER_A,
    _collect_keys,
    _generate_initial_progress_tree,
    _isolated_polish_app,
    _seed_polish_sources,
    _session_factory,
    _run_inline_threadpool,
)


@pytest.fixture(autouse=True)
def _patch_polish_run_in_threadpool(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(polish_api, "run_in_threadpool", _run_inline_threadpool)


class _FeedbackUnavailableTransport:
    def __init__(self) -> None:
        self._fake = FakeLlmTransport()

    def generate(self, request: LlmTransportRequest):
        if request.task_type == "polish_feedback_generation":
            raise RuntimeError("feedback provider unavailable")
        return self._fake.generate(request)


class _RecordingFeedbackTransport:
    def __init__(self) -> None:
        self._fake = FakeLlmTransport()
        self.feedback_request: LlmTransportRequest | None = None

    def generate(self, request: LlmTransportRequest):
        if request.task_type == "polish_feedback_generation":
            self.feedback_request = request
        return self._fake.generate(request)


def test_feedback_runtime_generates_and_persists_fake_payload() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(session_factory, OWNER_A)
    llm_transport = _RecordingFeedbackTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=llm_transport)
    _, create_body = call_json(
        app,
        "/api/v1/polish-sessions",
        "POST",
        json_body={
            "resume_job_binding_id": binding_id,
            "topic_id": "topic_technical_depth",
        },
    )
    session_id = create_body["data"]["session_id"]
    _, generate_body = _generate_initial_progress_tree(app, session_id)
    progress_node_ref = generate_body["data"]["progress_tree_state"]["current_priority"][
        "progress_node_ref"
    ]
    _, question_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/questions",
        "POST",
        json_body={"progress_node_ref": progress_node_ref},
    )
    question_id = question_body["data"]["result_ref"]["trace_ref_id"]
    _, answer_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/answers",
        "POST",
        json_body={
            "question_id": question_id,
            "answer_text": "我会说明异步解耦、失败补偿、幂等键和观测指标。",
        },
    )
    answer_id = answer_body["data"]["answer_id"]

    status_code, pending_detail_body = call_json(app, f"/api/v1/polish-sessions/{session_id}")
    assert status_code == 200
    pending_answer = next(
        answer
        for turn in pending_detail_body["data"]["turns"]
        for answer in turn["answers"]
        if answer["answer_id"] == answer_id
    )
    assert pending_answer["feedback_payload"]["status"] == "pending"
    assert llm_transport.feedback_request is None

    status_code, feedback_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
    )

    assert status_code == 202
    data = feedback_body["data"]
    assert data["task_type"] == "polish_feedback_generation"
    assert data["status"] == "succeeded"
    assert data["retryable"] is False
    assert data["feedback_status"] == "generated"
    assert data["candidate_refs"] == []
    assert data["suggestion_refs"] == []
    payload = data["feedback_payload"]
    assert payload["status"] == "generated"
    assert payload["feedback_metadata"]["llm_called"] is True
    assert payload["score_result"]["score_value"] == 82
    assert payload["loss_points"]
    assert payload["reference_answer"]["sections"]
    first_loss_point_id = payload["loss_points"][0]["loss_point_id"]
    assert any(
        first_loss_point_id in section.get("addresses_loss_point_ids", [])
        for section in payload["reference_answer"]["sections"]
    )
    assert payload["knowledge_points"] == ["事务消息", "幂等设计", "失败补偿"]
    assert payload["technical_principles"] == ["先定义失败恢复边界，再选择消息队列和补偿策略。"]
    assert payload["next_recommended_actions"] == ["围绕失败恢复终止条件再追问一轮"]
    assert llm_transport.feedback_request is not None
    prompt_asset = llm_transport.feedback_request.evidence_bundle
    assert prompt_asset["task_type"] == "polish_feedback_generation"
    assert prompt_asset["input_contract"]["raw_model_io_storage"] is False
    input_data = prompt_asset["input_data"]
    assert input_data["current_question"]["question_id"] == question_id
    assert input_data["current_answer"]["answer_id"] == answer_id
    assert input_data["same_question_answers"] == []
    assert input_data["same_project_turns"] == []
    assert input_data["project_asset_summaries"] == []
    assert input_data["session_recent_turns"]
    assert input_data["context_snapshots"]["job_snapshot"]["job_id"]
    assert input_data["context_snapshots"]["resume_snapshot"]["resume_id"]
    assert "markdown_text" not in input_data["context_snapshots"]["resume_snapshot"]
    assert input_data["context_snapshots"]["progress_node_snapshot"]["node_ref"]
    for forbidden_key in ("prompt", "completion", "provider_payload", "raw_prompt", "raw_completion"):
        assert forbidden_key not in _collect_keys(feedback_body)

    status_code, generated_detail_body = call_json(app, f"/api/v1/polish-sessions/{session_id}")
    assert status_code == 200
    generated_answer = next(
        answer
        for turn in generated_detail_body["data"]["turns"]
        for answer in turn["answers"]
        if answer["answer_id"] == answer_id
    )
    assert generated_answer["feedback_payload"]["status"] == "generated"
    assert generated_answer["feedback_payload"]["feedback_metadata"]["llm_called"] is True
    assert generated_answer["feedback_payload"]["score_result"]["score_value"] == 82

    with session_factory() as db:
        for table_name in (
            "weaknesses",
            "weakness_candidates",
            "assets",
            "asset_versions",
            "training_recommendations",
        ):
            assert db.execute(text(f"select count(*) from {table_name}")).scalar_one() == 0


def test_feedback_runtime_provider_unavailable_fails_without_generated_feedback() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(session_factory, OWNER_A)
    app = _isolated_polish_app(
        session_factory,
        ACTOR_A,
        llm_transport=_FeedbackUnavailableTransport(),
    )
    _, create_body = call_json(
        app,
        "/api/v1/polish-sessions",
        "POST",
        json_body={
            "resume_job_binding_id": binding_id,
            "topic_id": "topic_technical_depth",
        },
    )
    session_id = create_body["data"]["session_id"]
    _, generate_body = _generate_initial_progress_tree(app, session_id)
    progress_node_ref = generate_body["data"]["progress_tree_state"]["current_priority"][
        "progress_node_ref"
    ]
    _, question_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/questions",
        "POST",
        json_body={"progress_node_ref": progress_node_ref},
    )
    question_id = question_body["data"]["result_ref"]["trace_ref_id"]
    _, answer_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/answers",
        "POST",
        json_body={
            "question_id": question_id,
            "answer_text": "我会说明异步解耦、失败补偿、幂等键和观测指标。",
        },
    )
    answer_id = answer_body["data"]["answer_id"]

    status_code, feedback_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
    )

    assert status_code == 202
    data = feedback_body["data"]
    assert data["status"] == "generation_failed"
    assert data["retryable"] is True
    assert data["validation_errors"] == ["llm_transport_generation_failed"]
    assert data["feedback_id"] is None
    assert data["feedback_status"] == "pending"
    assert data["feedback_payload"]["status"] == "pending"
    assert "feedback_metadata" not in data["feedback_payload"]
    repository = SqlAlchemyPolishRepository(session_factory)
    assert repository.list_feedbacks_for_session(OWNER_A, session_id) == ()

    status_code, detail_body = call_json(app, f"/api/v1/polish-sessions/{session_id}")
    assert status_code == 200
    detail_answer = next(
        answer
        for turn in detail_body["data"]["turns"]
        for answer in turn["answers"]
        if answer["answer_id"] == answer_id
    )
    assert detail_answer["feedback_payload"]["status"] == "pending"
