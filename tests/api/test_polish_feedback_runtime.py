from __future__ import annotations

import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import httpx
import pytest
from sqlalchemy import select, text

from app.api.v1 import polish as polish_api
from app.application.polish import feedback_application_service as feedback_app_service
from app.application.common.logging import LogUtil
from app.application.polish.feedback_rules import ALLOWED_FEEDBACK_RECOMMENDED_ACTIONS
from app.application.polish.feedback_schema import POLISH_FEEDBACK_CANDIDATE_PAYLOAD_FIELDS, POLISH_FEEDBACK_TASK_TYPE
from app.application.polish.commands import CreatePolishFeedbackTaskCommand
from app.application.polish.feedback_application_service import (
    _feedback_idempotency_record_id,
    _feedback_request_body_hash,
)
from app.application.polish.feedback_schema import POLISH_FEEDBACK_FINAL_CONTRACT_IDS
from app.application.llm.types import LlmTransportRequest, LlmTransportResult
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import AiTaskStatus, ConfidenceLevel, ValidationStatus
from app.infrastructure.db.models.ai_task import AiTask, AiTaskResult
from app.infrastructure.db.models.feedback import Feedback as FeedbackModel
from app.infrastructure.db.repositories.polish import SqlAlchemyPolishRepository
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema
from app.infrastructure.llm.openai_compatible import (
    OpenAICompatibleLlmSettings,
    OpenAICompatibleLlmTransport,
)
from app.infrastructure.observability.http_logging import HttpAccessLogMiddleware
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


def _feedback_headers(key: str) -> dict[str, str]:
    return {"Idempotency-Key": key}


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


class _TimeoutOnceFeedbackTransport:
    def __init__(self) -> None:
        self._fake = FakeLlmTransport()
        self.feedback_calls = 0

    def generate(self, request: LlmTransportRequest):
        if request.task_type == "polish_feedback_generation":
            self.feedback_calls += 1
            if self.feedback_calls == 1:
                raise TimeoutError("first feedback provider timeout")
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


class _TruncatedProviderFeedbackTransport:
    def __init__(self) -> None:
        self._fake = FakeLlmTransport()
        self.observed_payloads: list[dict[str, object]] = []
        self.observed_reasoning_tokens = 0
        self._provider = OpenAICompatibleLlmTransport(
            OpenAICompatibleLlmSettings(
                api_key="test-key",
                model="deepseek-v4-pro",
                base_url="https://llm.example/v1",
            ),
            client=httpx.Client(transport=httpx.MockTransport(self._handler)),
        )

    def generate(self, request: LlmTransportRequest):
        if request.task_type != "polish_feedback_generation":
            return _runtime_test_non_feedback_result(self._fake, request)
        return self._provider.generate(request)

    @property
    def feedback_payload(self) -> dict[str, object]:
        return self.observed_payloads[-1]

    def _handler(self, request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        assert isinstance(payload, dict)
        self.observed_payloads.append(payload)
        self.observed_reasoning_tokens = 3658
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl_feedback_truncated",
                "model": "deepseek-v4-pro",
                "choices": [
                    {
                        "finish_reason": "length",
                        "message": {"content": '{"feedback_text":"partial'},
                    }
                ],
                "usage": {
                    "prompt_tokens": 4200,
                    "completion_tokens": 4800,
                    "total_tokens": 9000,
                    "completion_tokens_details": {
                        "reasoning_tokens": self.observed_reasoning_tokens,
                    },
                },
            },
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
    overweighted_skills = _runtime_dimensions_by_weight(weights, high=True) or [
        _stable_dimension_name(progress_state_ref)
    ]
    underweighted_skills = _runtime_dimensions_by_weight(weights, high=False) or [
        next(dimension for dimension in weights if dimension != overweighted_skills[0])
    ]
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
            "overweighted_skills": overweighted_skills,
            "underweighted_skills": underweighted_skills,
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
    if request.task_type == "polish_feedback_generation" and request.stage == "json_projection":
        return LlmTransportResult(
            result=_runtime_feedback_projection_payload(request),
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.MEDIUM,
            low_confidence_flags=(),
            trace_refs=("trace_feedback_runtime_projection",),
            evidence_refs=("evidence_feedback_runtime_projection",),
            metadata={
                "stage": "json_projection",
                "thinking_enabled": False,
                "finish_reason": "stop",
                "completion_tokens": 320,
                "reasoning_tokens": 0,
            },
        )
    result = fake.generate(request)
    if request.task_type == "polish_feedback_generation":
        return LlmTransportResult(
            result=_runtime_feedback_candidate_payload(result.result, request),
            validation_status=result.validation_status,
            confidence_level=result.confidence_level,
            low_confidence_flags=result.low_confidence_flags,
            trace_refs=result.trace_refs,
            evidence_refs=result.evidence_refs,
            metadata={
                "stage": "analysis_candidate",
                "thinking_enabled": True,
                "finish_reason": "stop",
                "completion_tokens": 900,
                "reasoning_tokens": 128,
            },
        )
    return result


def _runtime_feedback_projection_payload(request: LlmTransportRequest) -> dict[str, object]:
    bundle = request.evidence_bundle if isinstance(request.evidence_bundle, dict) else {}
    server_facts = bundle.get("server_facts") if isinstance(bundle.get("server_facts"), dict) else {}
    default_payload = (
        server_facts.get("default_final_payload")
        if isinstance(server_facts, dict)
        and isinstance(server_facts.get("default_final_payload"), dict)
        else {}
    )
    return dict(default_payload)


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
        headers=_feedback_headers("feedback-runtime-generate-001"),
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
    assert set(payload["next_recommended_actions"]) <= ALLOWED_FEEDBACK_RECOMMENDED_ACTIONS
    assert [request.stage for request in llm_transport.feedback_requests] == [
        "analysis_candidate",
        "json_projection",
    ]
    analysis_request = llm_transport.feedback_requests[0]
    assert 4000 <= getattr(analysis_request, "max_tokens", 8000) < 8000
    provider_prompt = analysis_request.evidence_bundle
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
    assert succeeded_log["validation_stage"] == "json_projection"
    assert succeeded_log["candidate_valid"] is True
    assert [stage["stage"] for stage in succeeded_log["generation_stages"]] == [
        "analysis_candidate",
        "json_projection",
    ]
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
        headers=_feedback_headers("feedback-runtime-existing-001"),
    )
    second_status, second_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
        headers=_feedback_headers("feedback-runtime-existing-002"),
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
            headers=_feedback_headers("feedback-runtime-concurrent-001"),
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


def test_feedback_runtime_already_running_read_replays_running_task_without_second_provider_call() -> None:
    session_factory = _session_factory()
    llm_transport = _BlockingFeedbackTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=llm_transport)
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)
    idempotency_key = "feedback-runtime-running-read-001"

    first_status, first_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
        headers=_feedback_headers(idempotency_key),
    )

    assert first_status == 202
    assert llm_transport.first_feedback_entered.wait(timeout=2)
    assert first_body["data"]["status"] == "running"
    ai_task_id = first_body["data"]["ai_task_id"]

    second_status, second_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
        headers=_feedback_headers(idempotency_key),
    )

    assert second_status == 202
    assert second_body["data"]["status"] == "running"
    assert second_body["data"]["ai_task_id"] == ai_task_id
    provider_calls_before_release = llm_transport.feedback_calls
    assert provider_calls_before_release == 1

    llm_transport.release_feedback.set()
    repository = SqlAlchemyPolishRepository(session_factory)
    generated_feedbacks = []
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        generated_feedbacks = [
            feedback
            for feedback in repository.list_feedbacks_for_session(OWNER_A, session_id)
            if feedback.answer_id == answer_id and feedback.status == "generated"
        ]
        if generated_feedbacks:
            break
        time.sleep(0.02)

    assert len(generated_feedbacks) == 1
    replay_status, replay_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
        headers=_feedback_headers(idempotency_key),
    )
    assert replay_status == 202
    assert replay_body["data"]["status"] == "succeeded"
    assert replay_body["data"]["ai_task_id"] == ai_task_id
    assert replay_body["data"]["feedback_status"] == "generated"
    assert llm_transport.feedback_calls == provider_calls_before_release + 1


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
        headers=_feedback_headers("feedback-runtime-unavailable-001"),
    )

    assert status_code == 202
    data = feedback_body["data"]
    assert data["status"] == "generation_failed"
    assert data["retryable"] is True
    assert data["validation_errors"] == ["llm_transport_generation_failed"]
    assert data["feedback_id"]
    assert data["feedback_status"] == "generation_failed"
    assert data["user_visible_status"] == "反馈生成失败，可重试"
    assert data["summary"] == "反馈生成失败，可重试"
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
        headers=_feedback_headers("feedback-runtime-timeout-001"),
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


def test_feedback_runtime_retries_after_provider_timeout_with_new_idempotency_key() -> None:
    session_factory = _session_factory()
    llm_transport = _TimeoutOnceFeedbackTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=llm_transport)
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)

    first_status, first_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
        headers=_feedback_headers("feedback-runtime-timeout-retry-first"),
    )
    second_status, second_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
        headers=_feedback_headers("feedback-runtime-timeout-retry-second"),
    )

    assert first_status == 202
    assert first_body["data"]["status"] == "generation_failed"
    assert first_body["data"]["retryable"] is True
    assert first_body["data"]["feedback_payload"]["error"]["code"] == "llm_transport_timeout"
    assert second_status == 202
    assert second_body["data"]["status"] == "succeeded"
    assert second_body["data"]["feedback_status"] == "generated"
    assert second_body["data"]["feedback_payload"]["status"] == "generated"
    assert llm_transport.feedback_calls == 3
    repository = SqlAlchemyPolishRepository(session_factory)
    generated_feedbacks = [
        feedback
        for feedback in repository.list_feedbacks_for_session(OWNER_A, session_id)
        if feedback.answer_id == answer_id and feedback.status == "generated"
    ]
    assert len(generated_feedbacks) == 1


def test_feedback_runtime_deadline_read_materializes_timed_out_feedback_without_provider_call() -> None:
    session_factory = _session_factory()
    llm_transport = _RecordingFeedbackTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=llm_transport)
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)
    idempotency_key = "feedback-runtime-deadline-read-001"
    command = CreatePolishFeedbackTaskCommand(
        owner_id=OWNER_A,
        actor_id=ACTOR_A.actor_id,
        session_id=session_id,
        answer_id=answer_id,
        internal_scoring_context=None,
    )
    now = utc_now()
    ai_task_id = "task_feedback_deadline_read_001"

    with session_factory() as db:
        db.add(
            AiTask(
                id=ai_task_id,
                owner_id=OWNER_A,
                actor_id=ACTOR_A.actor_id,
                record_version=1,
                status=str(AiTaskStatus.RUNNING),
                trace_ref_ids=[ai_task_id],
                evidence_ref_ids=None,
                task_type=POLISH_FEEDBACK_TASK_TYPE,
                contract_ids=list(POLISH_FEEDBACK_FINAL_CONTRACT_IDS),
                idempotency_record_id=_feedback_idempotency_record_id(
                    idempotency_key,
                    _feedback_request_body_hash(command),
                ),
                target_ref_id=answer_id,
                timeout_at=now - timedelta(seconds=1),
                created_at=now,
                updated_at=now,
            )
        )
        db.commit()

    status_code, feedback_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
        headers=_feedback_headers(idempotency_key),
    )

    assert status_code == 202
    data = feedback_body["data"]
    assert data["ai_task_id"] == ai_task_id
    assert data["status"] == "timed_out"
    assert data["retryable"] is True
    assert data["feedback_status"] == "timed_out"
    assert data["feedback_payload"]["status"] == "timed_out"
    assert data["feedback_payload"]["retryable"] is True
    assert data["feedback_payload"]["error"]["code"] == "feedback_generation_deadline_exceeded"
    assert llm_transport.feedback_requests == []


def test_feedback_generation_truncated_provider_response_persists_safe_task_diagnostics() -> None:
    session_factory = _session_factory()
    llm_transport = _TruncatedProviderFeedbackTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=llm_transport)
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)

    status_code, feedback_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
        headers=_feedback_headers("feedback-runtime-truncated-001"),
    )

    assert status_code == 202
    data = feedback_body["data"]
    assert data["status"] == "generation_failed"
    assert data["retryable"] is True
    assert data["feedback_status"] == "generation_failed"
    assert data["feedback_payload"]["status"] == "generation_failed"
    error_code = data["feedback_payload"]["error"]["code"]
    assert error_code in {"llm_transport_generation_failed", "provider_output_truncated"}
    assert error_code not in {"LlmTransportResponseError", "length", "JSONDecodeError"}
    assert llm_transport.feedback_payload["max_tokens"] == 4800
    assert llm_transport.observed_reasoning_tokens > 0

    with session_factory() as db:
        stored_result = db.get(AiTaskResult, f"{data['ai_task_id']}_result")

    assert stored_result is not None
    diagnostic_payloads = [
        payload
        for payload in (
            stored_result.validation_errors_json,
            stored_result.safe_summary_json,
        )
        if payload
    ]
    assert diagnostic_payloads, (
        "expected feedback generation failure to persist safe diagnostics in "
        "ai_task_results.validation_errors_json or safe_summary_json"
    )
    serialized_diagnostics = json.dumps(diagnostic_payloads, ensure_ascii=False, sort_keys=True)
    assert "provider_output_truncated" in serialized_diagnostics
    assert "finish_reason" in serialized_diagnostics
    assert "length" in serialized_diagnostics
    assert "max_tokens" in serialized_diagnostics
    assert "4800" in serialized_diagnostics
    assert "reasoning_tokens" in serialized_diagnostics
    assert str(llm_transport.observed_reasoning_tokens) in serialized_diagnostics
    assert data["ai_task_id"] in serialized_diagnostics
    assert answer_id in serialized_diagnostics

    forbidden_markers = (
        "raw_prompt",
        "system_prompt",
        "developer_prompt",
        "raw_completion",
        "completion text",
        "provider_payload",
        "raw_provider_payload",
        "reasoning_content",
        "api_key",
        "secret",
        "cookie",
        "token=",
    )
    serialized_response = json.dumps(feedback_body, ensure_ascii=False, sort_keys=True)
    serialized_all = f"{serialized_response}\n{serialized_diagnostics}".lower()
    for marker in forbidden_markers:
        assert marker not in serialized_all


def test_feedback_generation_background_failure_logs_trace_and_task_context(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    LogUtil.configure()
    caplog.set_level(logging.INFO)
    request_id = "feedback-runtime-log-request-001"
    trace_id = "feedback-runtime-log-trace-001"

    session_factory = _session_factory()
    app = _isolated_polish_app(
        session_factory,
        ACTOR_A,
        llm_transport=_TruncatedProviderFeedbackTransport(),
    )
    app.add_middleware(HttpAccessLogMiddleware)
    session_id = _create_session_for_feedback_log_test(app, session_factory)
    question_id = _create_question_for_feedback_log_test(app, session_factory, session_id)
    answer_id = _create_answer_for_feedback_log_test(app, session_id, question_id)

    status_code, feedback_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
        headers={
            **_feedback_headers("feedback-runtime-logs-001"),
            "x-request-id": request_id,
            "x-trace-id": trace_id,
        },
    )

    assert status_code == 202
    ai_task_id = feedback_body["data"]["ai_task_id"]
    log_records = [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.getMessage().startswith("{")
    ]
    expected_context = {
        "request_id": request_id,
        "trace_id": trace_id,
        "ai_task_id": ai_task_id,
        "session_id": session_id,
        "question_id": question_id,
        "answer_id": answer_id,
    }
    started_log = next(record for record in log_records if record["event"] == "feedback_generation_started")
    transport_failed_log = next(
        record
        for record in log_records
        if record["event"] == "llm_transport_request_failed"
        and record["task_type"] == "polish_feedback_generation"
    )
    failed_log = next(record for record in log_records if record["event"] == "feedback_generation_failed")
    assert transport_failed_log["error_type"] == "provider_output_truncated"
    for log_record in (started_log, transport_failed_log, failed_log):
        for field_name, expected_value in expected_context.items():
            assert log_record[field_name] == expected_value

    caplog.clear()

    def raise_background_exception(*_args, **_kwargs):
        raise RuntimeError("synthetic background feedback failure")

    monkeypatch.setattr(
        feedback_app_service,
        "_complete_feedback_generation",
        raise_background_exception,
    )
    exception_session_factory = _session_factory()
    exception_app = _isolated_polish_app(exception_session_factory, ACTOR_A)
    exception_app.add_middleware(HttpAccessLogMiddleware)
    exception_session_id = _create_session_for_feedback_log_test(
        exception_app,
        exception_session_factory,
    )
    exception_question_id = _create_question_for_feedback_log_test(
        exception_app,
        exception_session_factory,
        exception_session_id,
    )
    exception_answer_id = _create_answer_for_feedback_log_test(
        exception_app,
        exception_session_id,
        exception_question_id,
    )
    exception_request_id = "feedback-runtime-log-request-002"
    exception_trace_id = "feedback-runtime-log-trace-002"

    call_json(
        exception_app,
        f"/api/v1/polish-sessions/{exception_session_id}/feedback",
        "POST",
        json_body={"answer_id": exception_answer_id},
        headers={
            **_feedback_headers("feedback-runtime-logs-002"),
            "x-request-id": exception_request_id,
            "x-trace-id": exception_trace_id,
        },
    )

    exception_log_records = [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.getMessage().startswith("{")
    ]
    exception_started_log = next(
        record for record in exception_log_records if record["event"] == "feedback_generation_started"
    )
    exception_expected_context = {
        "request_id": exception_request_id,
        "trace_id": exception_trace_id,
        "ai_task_id": exception_started_log["ai_task_id"],
        "session_id": exception_session_id,
        "question_id": exception_question_id,
        "answer_id": exception_answer_id,
    }
    exception_log = next(
        record
        for record in exception_log_records
        if record["event"] == "feedback_generation_background_exception"
    )
    assert exception_log["error_type"] == "RuntimeError"
    for field_name, expected_value in exception_expected_context.items():
        assert exception_log[field_name] == expected_value


def test_feedback_generation_delayed_background_exception_persists_failed_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started = threading.Event()
    release = threading.Event()
    persisted = threading.Event()

    def raise_after_sync_wait(*_args, **_kwargs):
        started.set()
        assert release.wait(timeout=2), "background feedback failure was not released"
        raise RuntimeError("synthetic delayed background feedback failure")

    monkeypatch.setattr(
        feedback_app_service,
        "_complete_feedback_generation",
        raise_after_sync_wait,
    )
    original_persist_background_exception = (
        feedback_app_service._persist_feedback_generation_background_exception
    )

    def persist_background_exception_and_signal(*args, **kwargs):
        result = original_persist_background_exception(*args, **kwargs)
        persisted.set()
        return result

    monkeypatch.setattr(
        feedback_app_service,
        "_persist_feedback_generation_background_exception",
        persist_background_exception_and_signal,
    )
    session_factory = _session_factory()
    app = _isolated_polish_app(session_factory, ACTOR_A)
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)
    idempotency_key = "feedback-runtime-delayed-background-exception-001"

    status_code, feedback_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
        headers=_feedback_headers(idempotency_key),
    )

    assert status_code == 202
    assert started.wait(timeout=2)
    assert feedback_body["data"]["status"] == "running"
    ai_task_id = feedback_body["data"]["ai_task_id"]

    release.set()
    assert persisted.wait(timeout=2), "background feedback failure was not persisted"
    detail_status, detail_body = call_json(app, f"/api/v1/polish-sessions/{session_id}")
    assert detail_status == 200
    terminal_answer = next(
        answer
        for turn in detail_body["data"]["turns"]
        for answer in turn["answers"]
        if answer["answer_id"] == answer_id
    )

    failed_payload = terminal_answer["feedback_payload"]
    assert failed_payload["status"] == "generation_failed"
    assert failed_payload["retryable"] is True
    assert failed_payload["error"]["code"] == "feedback_generation_background_exception"
    assert failed_payload["error"]["metadata"]["stage"] == "background_worker"
    assert failed_payload["error"]["metadata"]["error_type"] == "RuntimeError"

    replay_status, replay_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
        headers=_feedback_headers(idempotency_key),
    )
    assert replay_status == 202
    assert replay_body["data"]["status"] == "generation_failed"
    assert replay_body["data"]["feedback_payload"]["status"] == "generation_failed"
    assert replay_body["data"]["ai_task_id"] == ai_task_id

    with session_factory() as db:
        stored_task = db.get(AiTask, ai_task_id)
        stored_result = db.get(AiTaskResult, f"{ai_task_id}_result")
        stored_feedbacks = db.scalars(
            select(FeedbackModel).where(
                FeedbackModel.owner_id == OWNER_A,
                FeedbackModel.session_id == session_id,
                FeedbackModel.answer_id == answer_id,
                FeedbackModel.ai_task_id == ai_task_id,
            )
        ).all()

    assert stored_task is not None
    assert stored_task.status == "generation_failed"
    assert stored_result is not None
    assert stored_result.status == "generation_failed"
    assert [feedback.status for feedback in stored_feedbacks] == ["generation_failed"]
    serialized_diagnostics = json.dumps(
        [stored_result.validation_errors_json, stored_result.safe_summary_json],
        ensure_ascii=False,
        sort_keys=True,
    )
    assert "feedback_generation_background_exception" in serialized_diagnostics
    assert "background_worker" in serialized_diagnostics
    assert "RuntimeError" in serialized_diagnostics
    assert "synthetic delayed background feedback failure" not in serialized_diagnostics


def _create_session_for_feedback_log_test(app, session_factory) -> str:
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
    _generate_initial_progress_tree(app, session_id)
    return session_id


def _create_question_for_feedback_log_test(app, session_factory, session_id: str) -> str:
    _, detail_body = call_json(app, f"/api/v1/polish-sessions/{session_id}")
    progress_node_ref = detail_body["data"]["progress_tree_state"]["current_priority"][
        "progress_node_ref"
    ]
    return _seed_polish_question_for_session(
        session_factory,
        session_id=session_id,
        progress_node_ref=progress_node_ref,
    )


def _create_answer_for_feedback_log_test(app, session_id: str, question_id: str) -> str:
    _, answer_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/answers",
        "POST",
        json_body={
            "question_id": question_id,
            "answer_text": "我会说明异步解耦、失败补偿、幂等键和观测指标。",
        },
    )
    return answer_body["data"]["answer_id"]


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
        headers=_feedback_headers("feedback-runtime-fail-retry-001"),
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
        headers=_feedback_headers("feedback-runtime-fail-retry-002"),
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
        headers=_feedback_headers("feedback-runtime-validator-001"),
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
    assert data["feedback_payload"]["feedback_metadata"]["validation_stage"] == "analysis_candidate"
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
