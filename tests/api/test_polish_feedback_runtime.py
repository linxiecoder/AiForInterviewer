from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import text

from app.api.v1 import polish as polish_api
from app.application.common.logging import LogUtil
from app.application.polish.feedback_schema import POLISH_FEEDBACK_CANDIDATE_PAYLOAD_FIELDS, POLISH_FEEDBACK_TASK_TYPE
from app.application.llm.types import LlmTransportRequest, LlmTransportResult
from app.domain.shared.enums import ConfidenceLevel, ValidationStatus
from app.infrastructure.db.repositories.polish import SqlAlchemyPolishRepository
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema
from tests.fakes.llm_transport import FakeLlmTransport
from tests.api.asgi_client import call_json
from tests.api.test_polish_api import (
    ACTOR_A,
    OWNER_A,
    _collect_keys,
    _generate_initial_progress_tree,
    _isolated_polish_app,
    _seed_polish_sources,
    _seed_polish_question_for_session,
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
        return _runtime_test_non_feedback_result(self._fake, request)


class _TimeoutFeedbackTransport:
    def __init__(self) -> None:
        self._fake = FakeLlmTransport()

    def generate(self, request: LlmTransportRequest):
        if request.task_type == "polish_feedback_generation":
            raise TimeoutError("feedback provider timed out")
        return _runtime_test_non_feedback_result(self._fake, request)


class _RecordingFeedbackTransport:
    def __init__(self) -> None:
        self._fake = FakeLlmTransport()
        self.feedback_requests: list[LlmTransportRequest] = []

    def generate(self, request: LlmTransportRequest):
        if request.task_type == "polish_feedback_generation":
            self.feedback_requests.append(request)
        return _runtime_test_non_feedback_result(self._fake, request)

    @property
    def feedback_request(self) -> LlmTransportRequest | None:
        return self.feedback_requests[-1] if self.feedback_requests else None


class _BlockingFeedbackTransport:
    def __init__(self) -> None:
        self._fake = FakeLlmTransport()
        self.feedback_calls = 0
        self.first_feedback_entered = threading.Event()
        self.release_feedback = threading.Event()
        self._guard = threading.Lock()

    def generate(self, request: LlmTransportRequest):
        if request.task_type == "polish_feedback_generation":
            with self._guard:
                self.feedback_calls += 1
            self.first_feedback_entered.set()
            assert self.release_feedback.wait(timeout=2), "feedback generation was not released"
        return _runtime_test_non_feedback_result(self._fake, request)


class _FailOnceFeedbackTransport:
    def __init__(self) -> None:
        self._fake = FakeLlmTransport()
        self.feedback_calls = 0

    def generate(self, request: LlmTransportRequest):
        if request.task_type == "polish_feedback_generation":
            self.feedback_calls += 1
            if self.feedback_calls == 1:
                raise RuntimeError("first feedback provider failure")
        return _runtime_test_non_feedback_result(self._fake, request)


class _ValidatorFailedFeedbackTransport:
    def __init__(self) -> None:
        self._fake = FakeLlmTransport()
        self.feedback_calls = 0

    def generate(self, request: LlmTransportRequest):
        if request.task_type != "polish_feedback_generation":
            return _runtime_test_non_feedback_result(self._fake, request)
        self.feedback_calls += 1
        return LlmTransportResult(
            result={
                "schema_id": "polish_feedback_generated_v1",
                "schema_version": "1.0",
                "status": "generated",
                "feedback_text": "validator should reject missing generated fields",
            },
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.MEDIUM,
            low_confidence_flags=(),
            trace_refs=("trace_validator_failed_feedback",),
            evidence_refs=("evidence_validator_failed_feedback",),
        )


def test_fake_feedback_transport_changes_adaptive_focus_when_progress_state_changes() -> None:
    first = _fake_feedback_score_result_for_progress(
        {
            "progress_state_ref": "progress_latency",
            "weak_skill_refs": ["latency_tradeoff"],
            "strong_skill_refs": ["structured_answer"],
        }
    )
    second = _fake_feedback_score_result_for_progress(
        {
            "progress_state_ref": "progress_observability",
            "weak_skill_refs": ["observability"],
            "strong_skill_refs": ["structured_answer"],
        }
    )

    first_weights = _score_weights(first)
    second_weights = _score_weights(second)

    assert first_weights != second_weights
    assert first["adaptive_insights"]["overweighted_skills"] != second["adaptive_insights"]["overweighted_skills"]
    assert first["progress_state_ref"] == "progress_latency"
    assert second["progress_state_ref"] == "progress_observability"


def _fake_feedback_score_result_for_progress(progress_state: dict[str, object]) -> dict[str, object]:
    result = FakeLlmTransport().generate(
        LlmTransportRequest(
            contract_ids=("P-POLISH-003",),
            task_type=POLISH_FEEDBACK_TASK_TYPE,
            input_refs=("answer_001",),
            evidence_bundle={
                "current_question": {"question_text": "How do you recover failed async messages?"},
                "current_answer": {"answer_text": "Use queues, retries, idempotency, and alerts."},
                "progress_state": progress_state,
            },
        )
    )
    payload = result.result
    assert isinstance(payload, dict)
    score_result = payload["score_result"]
    assert isinstance(score_result, dict)
    return score_result


def _score_weights(score_result: dict[str, object]) -> dict[str, float]:
    rubric = score_result["adaptive_rubric"]
    assert isinstance(rubric, dict)
    dimensions = rubric["dimensions"]
    assert isinstance(dimensions, list)
    return {
        str(item["dimension"]): float(item["adaptive_weight"])
        for item in dimensions
        if isinstance(item, dict)
    }


def _runtime_feedback_candidate_payload(value: object, request: LlmTransportRequest) -> object:
    if not isinstance(value, dict):
        return value
    filtered = {
        key: value[key]
        for key in POLISH_FEEDBACK_CANDIDATE_PAYLOAD_FIELDS
        if key in value
    }
    filtered.pop("project_asset_update_candidates", None)
    filtered["score_result"] = _runtime_adaptive_score_result(request)
    loss_points = filtered.get("loss_points")
    if isinstance(loss_points, list) and len(loss_points) == 1:
        first = loss_points[0] if isinstance(loss_points[0], dict) else None
        if (
            isinstance(first, dict)
            and str(first.get("severity") or "").strip() == "major"
            and str(first.get("loss_point_id") or "").strip()
        ):
            filtered["loss_points"] = [
                first,
                {
                    "loss_point_id": "lp_feedback_minor_point",
                    "severity": "minor",
                    "reason": "补充可验证指标与异常边界说明。",
                },
            ]
    return filtered


def _runtime_adaptive_score_result(request: LlmTransportRequest) -> dict[str, object]:
    bundle = request.evidence_bundle if isinstance(request.evidence_bundle, dict) else {}
    progress_state = bundle.get("progress_state") if isinstance(bundle.get("progress_state"), dict) else {}
    progress_state_ref = str(progress_state.get("progress_state_ref") or "progress_node_reliability")
    weights = _runtime_progress_weights(progress_state)
    weak_skills = _string_list(progress_state.get("weak_skill_refs"))
    strong_skills = _string_list(progress_state.get("strong_skill_refs"))
    scores = {
        "correctness": (88, "方向正确。"),
        "depth": (80, "细节基本完整。"),
        "tradeoff_reasoning": (76, "取舍略少。"),
        "structure": (84, "结构清楚。"),
        "engineering_awareness": (82, "工程边界基本覆盖。"),
    }
    return {
        "score_type": "polish_answer",
        "score_value": 1,
        "progress_state_ref": progress_state_ref,
        "reasoning": "ProgressState 中的 weak_skill_refs 决定本轮 deterministic fake 的评估关注点。",
        "adaptive_rubric": {
            "rubric_version": "polish_answer.progress_adaptive_rubric.v1",
            "progress_state_ref": progress_state_ref,
            "dimensions": [
                {
                    "dimension": dimension,
                    "adaptive_weight": weight,
                    "progress_basis": _runtime_progress_basis(dimension, progress_state_ref, weak_skills, strong_skills),
                    "anchor_refs": [f"anchor_{dimension}"],
                }
                for dimension, weight in weights.items()
            ],
        },
        "dimension_scores": [
            {
                "dimension": dimension,
                "score": score,
                "adaptive_weight": weights[dimension],
                "progress_focus": [progress_state_ref],
                "rationale": rationale,
            }
            for dimension, (score, rationale) in scores.items()
        ],
        "adaptive_insights": {
            "weak_skills": weak_skills,
            "strong_skills": strong_skills,
            "unstable_skills": [progress_state_ref],
            "overweighted_skills": _runtime_dimensions_by_weight(weights, high=True),
            "underweighted_skills": _runtime_dimensions_by_weight(weights, high=False),
        },
        "signals": ["weakness_detected", "progress_update"],
        "progress_updates": [
            {
                "progress_node_ref": progress_state_ref,
                "signal": "needs_focus",
                "dimension": "engineering_awareness",
            }
        ],
    }


def _runtime_progress_weights(progress_state: dict[str, object]) -> dict[str, float]:
    dimensions = ("correctness", "depth", "tradeoff_reasoning", "structure", "engineering_awareness")
    weak_skills = _string_list(progress_state.get("weak_skill_refs"))
    strong_skills = _string_list(progress_state.get("strong_skill_refs"))
    weights = {dimension: 0.20 for dimension in dimensions}
    for skill in weak_skills:
        weights[dimensions[_stable_dimension_index(skill, len(dimensions))]] += 0.06
    for skill in strong_skills:
        weights[dimensions[_stable_dimension_index(skill, len(dimensions))]] = max(
            0.08,
            weights[dimensions[_stable_dimension_index(skill, len(dimensions))]] - 0.04,
        )
    total = sum(weights.values())
    return {dimension: round(weight / total, 6) for dimension, weight in weights.items()}


def _runtime_progress_basis(
    dimension: str,
    progress_state_ref: str,
    weak_skills: list[str],
    strong_skills: list[str],
) -> list[str]:
    basis = [f"current_priority:{progress_state_ref}"]
    basis.extend(f"weak_skill:{skill}" for skill in weak_skills if _stable_dimension_name(skill) == dimension)
    basis.extend(f"strong_skill:{skill}" for skill in strong_skills if _stable_dimension_name(skill) == dimension)
    return basis


def _runtime_dimensions_by_weight(weights: dict[str, float], *, high: bool) -> list[str]:
    pivot = sum(weights.values()) / len(weights)
    return [dimension for dimension, weight in weights.items() if (weight > pivot if high else weight < pivot)]


def _stable_dimension_name(value: str) -> str:
    dimensions = ("correctness", "depth", "tradeoff_reasoning", "structure", "engineering_awareness")
    return dimensions[_stable_dimension_index(value, len(dimensions))]


def _stable_dimension_index(value: str, modulo: int) -> int:
    return sum(ord(char) for char in value) % modulo


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _runtime_test_non_feedback_result(fake: FakeLlmTransport, request: LlmTransportRequest):
    if request.task_type == "polish_question_generation":
        return _runtime_test_question_provider_result(request)
    result = fake.generate(request)
    if request.task_type == "polish_feedback_generation":
        return LlmTransportResult(
            result=_runtime_feedback_candidate_payload(result.result, request),
            validation_status=result.validation_status,
            confidence_level=result.confidence_level,
            low_confidence_flags=result.low_confidence_flags,
            trace_refs=result.trace_refs,
            evidence_refs=result.evidence_refs,
        )
    return result


def _runtime_test_question_provider_result(request: LlmTransportRequest) -> LlmTransportResult:
    bundle = request.evidence_bundle if isinstance(request.evidence_bundle, dict) else {}
    canonical_evidence = bundle.get("canonical_evidence") if isinstance(bundle.get("canonical_evidence"), dict) else {}
    expected_contract = (
        bundle.get("expected_output_contract")
        if isinstance(bundle.get("expected_output_contract"), dict)
        else {}
    )
    generation_policy = (
        expected_contract.get("generation_policy")
        if isinstance(expected_contract.get("generation_policy"), dict)
        else {}
    )
    progress_node = bundle.get("progress_node") if isinstance(bundle.get("progress_node"), dict) else {}
    evidence_refs = tuple(ref for ref in canonical_evidence.get("evidence_refs", []) if isinstance(ref, str))
    summaries = (
        canonical_evidence.get("evidence_summaries")
        if isinstance(canonical_evidence.get("evidence_summaries"), list)
        else []
    )
    primary = next((item for item in summaries if isinstance(item, dict) and item.get("excerpt")), {})
    evidence_excerpt = str(primary.get("excerpt") or "Built backend workflow automation.").strip()
    question_kind = generation_policy.get("question_kind") or "technical_chain_deep_dive"
    return LlmTransportResult(
        result={
            "transport": "recording_provider",
            "question_text": (
                f"请围绕简历证据「{evidence_excerpt}」，说明后端工作流中异步解耦、失败补偿、"
                "幂等键和观测指标如何设计。"
            ),
            "question_kind": question_kind,
            "focus_dimension": question_kind,
            "difficulty": "medium",
            "skill_dimension": progress_node.get("expected_capability") or progress_node.get("title"),
            "expected_signal": "回答应说明异步链路、失败恢复、幂等和指标验证。",
            "follow_ups": ["失败恢复如何验证？"],
            "scoring_rubric": [{"dimension": "reliability", "signals": ["失败补偿", "指标验证"]}],
            "missing_context": [],
            "evidence_refs": list(evidence_refs),
            "confidence": "high",
            "clarification_needed": False,
            "trace_ref": "trace_feedback_runtime_question_provider",
        },
        validation_status=ValidationStatus.VALID,
        confidence_level=ConfidenceLevel.HIGH,
        low_confidence_flags=(),
        trace_refs=("trace_feedback_runtime_question_provider",),
        evidence_refs=evidence_refs,
    )


def _create_answer_ready_for_feedback(app, session_factory) -> tuple[str, str]:
    _, create_body = call_json(
        app,
        "/api/v1/polish-sessions",
        "POST",
        json_body={
            "resume_job_binding_id": _seed_polish_sources(session_factory, OWNER_A),
            "topic_id": "topic_technical_depth",
        },
    )
    session_id = create_body["data"]["session_id"]
    _, generate_body = _generate_initial_progress_tree(app, session_id)
    progress_node_ref = generate_body["data"]["progress_tree_state"]["current_priority"][
        "progress_node_ref"
    ]
    question_id = _seed_polish_question_for_session(
        session_factory,
        session_id=session_id,
        progress_node_ref=progress_node_ref,
    )
    _, answer_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/answers",
        "POST",
        json_body={
            "question_id": question_id,
            "answer_text": "我会说明异步解耦、失败补偿、幂等键和观测指标。",
        },
    )
    return session_id, answer_body["data"]["answer_id"]


def test_feedback_runtime_generates_and_persists_fake_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    succeeded_log_calls: list[dict] = []
    monkeypatch.setattr(
        LogUtil,
        "feedback_generation_succeeded",
        staticmethod(lambda **fields: succeeded_log_calls.append(fields)),
    )
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
    question_id = _seed_polish_question_for_session(
        session_factory,
        session_id=session_id,
        progress_node_ref=progress_node_ref,
    )
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
    feedback_candidate_ref = next(
        ref for ref in data["candidate_refs"] if ref["resource_type"] == "feedback_candidate"
    )
    assert data["suggestion_refs"] == []
    payload = data["feedback_payload"]
    assert payload["status"] == "generated"
    assert payload["feedback_metadata"]["llm_called"] is True
    assert payload["feedback_metadata"]["planned_workflow"] == "phase6_feedback_agent_l2"
    assert payload["feedback_metadata"]["handoff_contract"] == "handoff.polish_feedback_agent.v1"
    assert payload["feedback_metadata"]["candidate_ref"] == feedback_candidate_ref["resource_id"]
    assert payload["feedback_metadata"]["asset_update_formal_write_performed"] is False
    assert "candidate_refs" not in payload
    assert 70 <= payload["score_result"]["score_value"] <= 90
    assert payload["score_result"]["adaptive_insights"]["weak_skills"]
    assert payload["score_result"]["adaptive_insights"]["overweighted_skills"]
    assert payload["loss_points"]
    assert payload["reference_answer"]["sections"]
    first_loss_point_id = payload["loss_points"][0]["loss_point_id"]
    assert any(
        first_loss_point_id in section.get("addresses_loss_point_ids", [])
        for section in payload["reference_answer"]["sections"]
    )
    assert "project_asset_update_candidates" not in payload
    assert payload["next_recommended_actions"][0] == "continue_same_question"
    assert "围绕失败恢复终止条件再追问一轮" in payload["next_recommended_actions"]
    assert llm_transport.feedback_request is not None
    assert 4000 <= getattr(llm_transport.feedback_request, "max_tokens", 8000) < 8000
    provider_prompt = llm_transport.feedback_request.evidence_bundle
    assert provider_prompt["task_type"] == "polish_feedback_generation"
    assert provider_prompt["feedback_mode"] == "candidate_compact"
    assert provider_prompt["task"] == "polish_feedback_candidate_v1"
    assert provider_prompt["input_contract"]["raw_model_io_storage"] is False
    assert provider_prompt["current_question"]["question_id"] == question_id
    assert provider_prompt["current_answer"]["answer_id"] == answer_id
    assert provider_prompt["same_question_answers"] == []
    assert "same_project_turns" not in provider_prompt
    assert "project_asset_summaries" not in provider_prompt
    assert "session_recent_turns" not in provider_prompt
    assert provider_prompt["job_requirements"]
    assert provider_prompt["resume_projects"]
    assert "markdown_text" not in provider_prompt
    assert provider_prompt["progress_node_snapshot"]["node_ref"]
    assert len(provider_prompt["evidence"]) <= 5
    assert provider_prompt["feedback_metadata"]["prompt_char_count"] < 12000
    assert provider_prompt["feedback_metadata"]["evidence_item_count"] <= 5
    for forbidden_key in (
        "prompt",
        "completion",
        "provider_payload",
        "raw_prompt",
        "system_prompt",
        "developer_prompt",
        "raw_completion",
        "full_resume",
        "full_jd",
        "token",
        "secret",
        "cookie",
    ):
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
    assert 70 <= generated_answer["feedback_payload"]["score_result"]["score_value"] <= 90
    assert len(succeeded_log_calls) == 1
    succeeded_log = succeeded_log_calls[0]
    assert succeeded_log["session_id"] == session_id
    assert succeeded_log["question_id"] == question_id
    assert succeeded_log["answer_id"] == answer_id
    assert succeeded_log["llm_called"] is True
    assert succeeded_log["error_code"] is None
    assert succeeded_log["validation_stage"] == "final"
    assert succeeded_log["candidate_valid"] is True
    assert succeeded_log["duration_ms"] >= 0

    with session_factory() as db:
        for table_name in (
            "weaknesses",
            "weakness_candidates",
            "assets",
            "asset_versions",
            "training_recommendations",
        ):
            assert db.execute(text(f"select count(*) from {table_name}")).scalar_one() == 0


def test_feedback_runtime_returns_existing_generated_feedback_without_second_generation() -> None:
    session_factory = _session_factory()
    llm_transport = _RecordingFeedbackTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=llm_transport)
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)

    first_status, first_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
    )
    second_status, second_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
    )

    assert first_status == 202
    assert second_status == 202
    assert first_body["data"]["feedback_status"] == "generated"
    assert second_body["data"]["feedback_status"] == "generated"
    assert second_body["data"]["feedback_payload"]["status"] == "generated"
    assert second_body["data"]["feedback_id"] == first_body["data"]["feedback_id"]
    assert second_body["data"]["feedback_payload"]["feedback_id"] == first_body["data"]["feedback_id"]
    assert len(llm_transport.feedback_requests) == 2
    repository = SqlAlchemyPolishRepository(session_factory)
    generated_feedbacks = [
        feedback
        for feedback in repository.list_feedbacks_for_session(OWNER_A, session_id)
        if feedback.answer_id == answer_id and feedback.status == "generated"
    ]
    assert len(generated_feedbacks) == 1

    _, detail_body = call_json(app, f"/api/v1/polish-sessions/{session_id}")
    detail_answer = next(
        answer
        for turn in detail_body["data"]["turns"]
        for answer in turn["answers"]
        if answer["answer_id"] == answer_id
    )
    assert detail_answer["feedback_id"] == first_body["data"]["feedback_id"]
    assert detail_answer["feedback_payload"]["status"] == "generated"


def test_feedback_runtime_concurrent_duplicate_requests_write_one_generated_feedback(tmp_path) -> None:
    settings = DbSettings(database_url=f"sqlite+pysqlite:///{(tmp_path / 'feedback-runtime.sqlite').as_posix()}")
    session_factory = build_session_factory(settings)
    initialize_schema(session_factory=session_factory)
    llm_transport = _BlockingFeedbackTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=llm_transport)
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)

    def _request_feedback() -> tuple[int, dict]:
        return call_json(
            app,
            f"/api/v1/polish-sessions/{session_id}/feedback",
            "POST",
            json_body={"answer_id": answer_id},
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(_request_feedback)
        assert llm_transport.first_feedback_entered.wait(timeout=2)
        second_future = executor.submit(_request_feedback)
        time.sleep(0.05)
        llm_transport.release_feedback.set()
        first_status, first_body = first_future.result(timeout=2)
        second_status, second_body = second_future.result(timeout=2)

    assert {first_status, second_status} == {202}
    assert first_body["data"]["feedback_status"] == "generated"
    assert second_body["data"]["feedback_status"] == "generated"
    assert first_body["data"]["feedback_id"] == second_body["data"]["feedback_id"]
    assert llm_transport.feedback_calls == 2
    repository = SqlAlchemyPolishRepository(session_factory)
    generated_feedbacks = [
        feedback
        for feedback in repository.list_feedbacks_for_session(OWNER_A, session_id)
        if feedback.answer_id == answer_id and feedback.status == "generated"
    ]
    assert len(generated_feedbacks) == 1


def test_feedback_runtime_provider_unavailable_fails_without_generated_feedback(monkeypatch: pytest.MonkeyPatch) -> None:
    failed_log_calls: list[dict] = []
    monkeypatch.setattr(
        LogUtil,
        "feedback_generation_failed",
        staticmethod(lambda **fields: failed_log_calls.append(fields)),
    )
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
    question_id = _seed_polish_question_for_session(
        session_factory,
        session_id=session_id,
        progress_node_ref=progress_node_ref,
    )
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
    assert data["feedback_id"]
    assert data["feedback_status"] == "generation_failed"
    assert data["user_visible_status"] == "反馈生成失败，可重试"
    assert data["feedback_text"] == "反馈生成失败，可重试"
    assert data["feedback_payload"]["status"] == "generation_failed"
    assert data["feedback_payload"]["feedback_text"] == "反馈生成失败，可重试"
    assert data["feedback_payload"]["error"]["code"] == "llm_transport_generation_failed"
    assert data["feedback_payload"]["score_result"] is None
    assert data["feedback_payload"]["loss_points"] == []
    assert data["feedback_payload"]["reference_answer"] is None
    assert data["feedback_payload"]["feedback_metadata"]["llm_called"] is True
    assert data["feedback_payload"]["feedback_metadata"]["provider_status"] == "failed"
    repository = SqlAlchemyPolishRepository(session_factory)
    stored_feedbacks = repository.list_feedbacks_for_session(OWNER_A, session_id)
    assert not any(feedback.status == "generated" for feedback in stored_feedbacks)

    status_code, detail_body = call_json(app, f"/api/v1/polish-sessions/{session_id}")
    assert status_code == 200
    detail_answer = next(
        answer
        for turn in detail_body["data"]["turns"]
        for answer in turn["answers"]
        if answer["answer_id"] == answer_id
    )
    assert detail_answer["feedback_payload"]["status"] == "generation_failed"
    assert detail_answer["feedback_payload"]["error"]["code"] == "llm_transport_generation_failed"
    assert len(failed_log_calls) == 1
    failed_log = failed_log_calls[0]
    assert failed_log["session_id"] == session_id
    assert failed_log["question_id"] == question_id
    assert failed_log["answer_id"] == answer_id
    assert failed_log["llm_called"] is True
    assert failed_log["provider_status"] == "failed"
    assert failed_log["error_code"] == "llm_transport_generation_failed"
    assert failed_log["duration_ms"] >= 0


def test_feedback_runtime_provider_timeout_returns_failed_retryable_payload() -> None:
    session_factory = _session_factory()
    app = _isolated_polish_app(
        session_factory,
        ACTOR_A,
        llm_transport=_TimeoutFeedbackTransport(),
    )
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)

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
    assert data["feedback_status"] == "generation_failed"
    assert data["feedback_payload"]["status"] == "generation_failed"
    assert data["feedback_payload"]["feedback_text"] == "反馈生成失败，可重试"
    assert data["feedback_payload"]["error"]["code"] == "llm_transport_timeout"
    assert data["validation_errors"] == ["llm_transport_timeout"]
    repository = SqlAlchemyPolishRepository(session_factory)
    assert not any(
        feedback.status == "generated"
        for feedback in repository.list_feedbacks_for_session(OWNER_A, session_id)
    )


def test_feedback_runtime_provider_failure_does_not_block_retry() -> None:
    session_factory = _session_factory()
    llm_transport = _FailOnceFeedbackTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=llm_transport)
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)

    first_status, first_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
    )
    assert first_status == 202
    assert first_body["data"]["status"] == "generation_failed"
    assert first_body["data"]["retryable"] is True
    assert first_body["data"]["feedback_payload"]["status"] == "generation_failed"
    repository = SqlAlchemyPolishRepository(session_factory)
    assert not any(
        feedback.status == "generated"
        for feedback in repository.list_feedbacks_for_session(OWNER_A, session_id)
    )

    second_status, second_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
    )
    assert second_status == 202
    assert second_body["data"]["status"] == "succeeded"
    assert second_body["data"]["feedback_status"] == "generated"
    assert second_body["data"]["feedback_payload"]["status"] == "generated"
    assert llm_transport.feedback_calls == 3
    generated_feedbacks = [
        feedback
        for feedback in repository.list_feedbacks_for_session(OWNER_A, session_id)
        if feedback.answer_id == answer_id and feedback.status == "generated"
    ]
    assert len(generated_feedbacks) == 1


def test_feedback_runtime_validator_failed_does_not_write_generated_feedback_or_reserved() -> None:
    session_factory = _session_factory()
    llm_transport = _ValidatorFailedFeedbackTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=llm_transport)
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)

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
    assert data["feedback_id"]
    assert data["feedback_status"] == "generation_failed"
    assert data["feedback_payload"]["status"] == "generation_failed"
    assert data["feedback_payload"]["status"] != "reserved"
    assert data["feedback_payload"]["feedback_text"] == "反馈生成失败，可重试"
    assert data["feedback_payload"]["error"]["code"] in data["validation_errors"]
    assert data["validation_errors"]
    assert data["feedback_payload"]["feedback_metadata"]["llm_called"] is True
    assert data["feedback_payload"]["feedback_metadata"]["provider_status"] == "called"
    assert data["feedback_payload"]["feedback_metadata"]["candidate_valid"] is False
    assert data["feedback_payload"]["feedback_metadata"]["validation_stage"] == "candidate"
    repository = SqlAlchemyPolishRepository(session_factory)
    stored_feedbacks = repository.list_feedbacks_for_session(OWNER_A, session_id)
    assert not any(feedback.status == "generated" for feedback in stored_feedbacks)
    _, detail_body = call_json(app, f"/api/v1/polish-sessions/{session_id}")
    detail_answer = next(
        answer
        for turn in detail_body["data"]["turns"]
        for answer in turn["answers"]
        if answer["answer_id"] == answer_id
    )
    assert detail_answer["feedback_payload"]["status"] == "generation_failed"
