from __future__ import annotations

import json
from copy import deepcopy
from typing import Any
from unittest.mock import patch

import pytest
from fastapi import FastAPI

import app.api.v1.polish as polish_api
from app.application.polish.feedback_contracts import (
    FEEDBACK_SCHEMA_ID,
    FEEDBACK_SCHEMA_VERSION,
    FeedbackInput,
    RetryFeedbackInput,
)
from app.application.polish.feedback_llm import PolishFeedbackLlmService
from app.application.polish.feedback_prompts import (
    POLISH_ANSWER_FEEDBACK_TASK_TYPE,
    build_polish_feedback_prompt_bundle,
)
from app.application.polish.feedback_quality import (
    compute_score_result_from_dimensions,
    validate_feedback_consistency,
)
from app.domain.shared.enums import ConfidenceLevel, ValidationStatus
from app.infrastructure.llm.errors import LlmTransportUnavailableError
from app.infrastructure.llm.fake_transport import FakeLlmTransport
from app.infrastructure.llm.types import LlmTransportRequest, LlmTransportResult
from tests.api.asgi_client import call_json
from tests.api.test_polish_api import (
    ACTOR_A,
    OWNER_A,
    _isolated_polish_app,
    _run_inline_threadpool,
    _seed_polish_sources,
    _session_factory,
)


RAW_RESUME_SENTINEL = "RAW_RESUME_SENTINEL_DO_NOT_PROMPT " * 80
RAW_JD_SENTINEL = "RAW_JD_SENTINEL_DO_NOT_PROMPT " * 80


@pytest.fixture(autouse=True)
def _patch_feedback_api_run_in_threadpool(monkeypatch):
    monkeypatch.setattr(polish_api, "run_in_threadpool", _run_inline_threadpool)


def test_prompt_bundle_uses_compact_feedback_inputs_only() -> None:
    feedback_input = _feedback_input(
        question_metadata={
            "question_pattern": "system_design_depth",
            "interview_intent": "验证候选人是否能说明异常路径和指标。",
            "expected_answer_dimensions": ["technical_depth", "answer_structure"],
            "raw_resume_markdown": RAW_RESUME_SENTINEL,
            "raw_jd": RAW_JD_SENTINEL,
            "feedback_llm_fixture": "valid_first",
        },
    )

    bundle = build_polish_feedback_prompt_bundle(
        feedback_input=feedback_input,
        deterministic_payload=_deterministic_payload(feedback_input=feedback_input),
    )

    serialized = json.dumps(bundle, ensure_ascii=False, sort_keys=True)
    assert bundle["task_type"] == POLISH_ANSWER_FEEDBACK_TASK_TYPE
    assert bundle["evidence_bundle"]["answer_round"] == 1
    assert bundle["evidence_bundle"]["question_pattern"] == "system_design_depth"
    assert bundle["evidence_bundle"]["expected_answer_dimensions"] == [
        "technical_depth",
        "answer_structure",
        "evidence_alignment",
    ]
    assert "raw_resume_markdown" not in serialized
    assert "raw_jd" not in serialized
    assert RAW_RESUME_SENTINEL.strip() not in serialized
    assert RAW_JD_SENTINEL.strip() not in serialized
    evidence_serialized = json.dumps(bundle["evidence_bundle"], ensure_ascii=False, sort_keys=True)
    assert "provider_payload" not in evidence_serialized
    assert "completion" not in evidence_serialized


def test_feature_disabled_path_uses_deterministic_feedback_without_transport_call() -> None:
    feedback_input = _feedback_input()
    deterministic = _deterministic_payload(feedback_input=feedback_input)
    transport = _RecordingRealLikeTransport()

    with patch.dict("os.environ", {"AIFI_POLISH_FEEDBACK_LLM_ENABLED": "false"}, clear=False):
        result = PolishFeedbackLlmService(transport).generate_with_llm_or_fallback(
            feedback_input=feedback_input,
            deterministic_payload=deterministic,
        )

    assert transport.calls == []
    assert result.feedback_payload["feedback_summary"] == deterministic["feedback_summary"]
    metadata = result.feedback_payload["feedback_metadata"]
    assert metadata["feedback_generation_mode"] == "deterministic_structured"
    assert metadata["fallback_reason"] == "feature_disabled"
    assert metadata["llm_output_validation_status"] == "not_requested"


def test_real_provider_disabled_gate_blocks_feedback_even_when_llm_is_enabled() -> None:
    feedback_input = _feedback_input()
    deterministic = _deterministic_payload(feedback_input=feedback_input)
    transport = _RecordingRealLikeTransport()

    with patch.dict(
        "os.environ",
        {
            "AIFI_POLISH_FEEDBACK_LLM_ENABLED": "true",
            "AIFI_POLISH_FEEDBACK_REAL_PROVIDER_ENABLED": "false",
        },
        clear=False,
    ):
        result = PolishFeedbackLlmService(transport).generate_with_llm_or_fallback(
            feedback_input=feedback_input,
            deterministic_payload=deterministic,
        )

    assert transport.calls == []
    metadata = result.feedback_payload["feedback_metadata"]
    assert metadata["feedback_generation_mode"] == "llm_fallback"
    assert metadata["fallback_reason"] == "real_provider_disabled"
    assert result.feedback_payload["feedback_summary"] == deterministic["feedback_summary"]


def test_valid_fake_first_answer_feedback_is_accepted_without_raw_payload() -> None:
    feedback_input = _feedback_input(fixture_marker="valid_first")
    result = _generate_with_fake_feedback_llm(feedback_input)

    payload = result.feedback_payload
    metadata = payload["feedback_metadata"]
    assert payload["feedback_summary"].startswith("LLM fake first feedback")
    assert metadata["feedback_generation_mode"] == "llm_accepted"
    assert metadata["feedback_llm_task_type"] == POLISH_ANSWER_FEEDBACK_TASK_TYPE
    assert metadata["fallback_reason"] is None
    assert metadata["provider_summary"]["kind"] == "fake"
    assert metadata["model_summary"] == {"kind": "safe_summary", "model_name": "not_recorded"}
    _assert_no_raw_llm_payload(payload)


def test_valid_fake_retry_feedback_is_accepted_with_delta_fields() -> None:
    feedback_input = _feedback_input(answer_round=2, fixture_marker="valid_retry")
    result = _generate_with_fake_feedback_llm(feedback_input)

    payload = result.feedback_payload
    metadata = payload["feedback_metadata"]
    assert metadata["feedback_generation_mode"] == "llm_accepted"
    assert metadata["fallback_reason"] is None
    assert payload["score_delta"] > 0
    assert payload["dimension_delta"]
    assert payload["improved_points"]
    assert payload["improved_points"] == [
        feedback_input.previous_loss_points[0]["loss_point_id"]
    ]
    assert payload["remaining_gaps"]
    assert payload["mastery_status"] in {"regressed", "stuck", "improving", "mastered"}
    assert payload["updated_reference_answer"] == payload["p7_reference_answer"]
    assert payload["updated_oral_script"] == payload["oral_script"]


def test_feedback_api_valid_fake_retry_is_accepted_with_previous_loss_point_delta() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(session_factory, OWNER_A)
    app = _isolated_feedback_app(session_factory)

    with patch.dict(
        "os.environ",
        {
            "AIFI_POLISH_FEEDBACK_LLM_ENABLED": "true",
            "AIFI_POLISH_FEEDBACK_REAL_PROVIDER_ENABLED": "false",
        },
        clear=False,
    ):
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
        progress_node_ref = create_body["data"]["progress_tree_state"]["current_priority"]["progress_node_ref"]
        status_code, question_body = call_json(
            app,
            f"/api/v1/polish-sessions/{session_id}/questions",
            "POST",
            json_body={"progress_node_ref": progress_node_ref},
        )
        assert status_code == 202
        question_id = question_body["data"]["result_ref"]["trace_ref_id"]

        status_code, first_answer_body = call_json(
            app,
            f"/api/v1/polish-sessions/{session_id}/answers",
            "POST",
            json_body={
                "question_id": question_id,
                "answer_text": "我会先说明系统背景，再补充幂等、失败路径、验证指标和权衡。",
            },
        )
        assert status_code == 201
        assert first_answer_body["data"]["answer_round"] == 1
        first_answer_id = first_answer_body["data"]["answer_id"]
        status_code, first_feedback_body = call_json(
            app,
            f"/api/v1/polish-sessions/{session_id}/feedback",
            "POST",
            json_body={"answer_id": first_answer_id},
        )
        assert status_code == 202
        first_payload = first_feedback_body["data"]["feedback_payload"]
        assert first_payload["feedback_metadata"]["feedback_generation_mode"] == "llm_accepted"
        assert first_payload["feedback_metadata"]["fallback_reason"] is None
        previous_loss_point_id = first_payload["loss_points"][0]["loss_point_id"]

        status_code, second_answer_body = call_json(
            app,
            f"/api/v1/polish-sessions/{session_id}/answers",
            "POST",
            json_body={
                "question_id": question_id,
                "answer_text": "第二轮我补充失败路径、补偿机制、验证指标、可观测指标和核心取舍。",
            },
        )
        assert status_code == 201
        assert second_answer_body["data"]["answer_round"] == 2
        second_answer_id = second_answer_body["data"]["answer_id"]
        status_code, second_feedback_body = call_json(
            app,
            f"/api/v1/polish-sessions/{session_id}/feedback",
            "POST",
            json_body={"answer_id": second_answer_id},
        )

    assert status_code == 202
    retry_payload = second_feedback_body["data"]["feedback_payload"]
    retry_metadata = retry_payload["feedback_metadata"]
    assert retry_metadata["feedback_generation_mode"] == "llm_accepted"
    assert retry_metadata["fallback_reason"] is None
    assert retry_payload["improved_points"] == [previous_loss_point_id]
    assert retry_payload["mastery_status"] in {"regressed", "stuck", "improving", "mastered"}
    assert retry_payload["score_delta"] > 0
    assert retry_payload["dimension_delta"]
    assert retry_payload["next_retry_focus"]
    _assert_no_raw_llm_payload(second_feedback_body)


def test_invalid_fake_retry_unknown_improved_point_still_falls_back() -> None:
    feedback_input = _feedback_input(
        answer_round=2,
        fixture_marker="invalid_retry_unknown_improved_point",
    )
    result = _generate_with_fake_feedback_llm(feedback_input)

    metadata = result.feedback_payload["feedback_metadata"]
    assert metadata["feedback_generation_mode"] == "llm_fallback"
    assert metadata["fallback_reason"] == "consistency_invalid"
    assert any(
        "improved_points_not_from_previous_loss_points" in error.get("message", "")
        for error in metadata["validation_errors"]
    )
    _assert_no_raw_llm_payload(result.feedback_payload)


def test_valid_retry_without_previous_loss_points_does_not_pretend_valid() -> None:
    feedback_input = _retry_feedback_input_without_previous_loss_points()
    result = _generate_with_fake_feedback_llm(feedback_input)

    metadata = result.feedback_payload["feedback_metadata"]
    assert metadata["feedback_generation_mode"] == "llm_fallback"
    assert metadata["fallback_reason"] == "consistency_invalid"
    assert any(
        "improved_points_without_previous_loss_points" in error.get("message", "")
        for error in metadata["validation_errors"]
    )


def test_feedback_consistency_keeps_improved_points_strict_to_previous_losses() -> None:
    feedback_input = _feedback_input(answer_round=2, fixture_marker="valid_retry")
    payload = _deterministic_payload(feedback_input=feedback_input)

    invalid_payload = {
        **payload,
        "improved_points": ["unknown_loss_point"],
        "previous_loss_points": list(feedback_input.previous_loss_points),
    }
    invalid_result = validate_feedback_consistency(invalid_payload)
    assert invalid_result["allow_emit"] is False
    assert invalid_result["blocking_issues"] == [
        "improved_points_not_from_previous_loss_points:unknown_loss_point"
    ]

    valid_payload = {
        **payload,
        "improved_points": [feedback_input.previous_loss_points[0]["loss_point_id"]],
        "previous_loss_points": list(feedback_input.previous_loss_points),
    }
    valid_result = validate_feedback_consistency(valid_payload)
    assert valid_result["allow_emit"] is True
    assert valid_result["blocking_issues"] == []


@pytest.mark.parametrize(
    ("fixture_marker", "fallback_reason"),
    [
        ("schema_invalid", "schema_invalid"),
        ("missing_critical_loss_coverage", "consistency_invalid"),
        ("oral_script_ignores_loss", "consistency_invalid"),
        ("raw_prompt_leak", "raw_payload_leak"),
        ("raw_prompt_value_leak", "raw_payload_leak"),
        ("metadata_full_evidence_leak", "raw_payload_leak"),
        ("unsupported_user_fact", "raw_payload_leak"),
        ("provider_unavailable", "provider_unavailable"),
        ("timeout", "provider_timeout"),
    ],
)
def test_invalid_fake_feedback_falls_back_to_deterministic_payload(
    fixture_marker: str,
    fallback_reason: str,
) -> None:
    feedback_input = _feedback_input(fixture_marker=fixture_marker)
    deterministic = _deterministic_payload(feedback_input=feedback_input)
    result = _generate_with_fake_feedback_llm(feedback_input, deterministic_payload=deterministic)

    payload = result.feedback_payload
    metadata = payload["feedback_metadata"]
    assert payload["feedback_summary"] == deterministic["feedback_summary"]
    assert metadata["feedback_generation_mode"] == "llm_fallback"
    assert metadata["fallback_reason"] == fallback_reason
    assert metadata["provider_summary"]["kind"] == "fake"
    _assert_no_raw_llm_payload(payload)


def test_score_mismatch_is_repaired_once_and_accepted() -> None:
    feedback_input = _feedback_input(fixture_marker="score_dimension_mismatch")
    result = _generate_with_fake_feedback_llm(feedback_input)

    payload = result.feedback_payload
    expected_score = compute_score_result_from_dimensions(payload["scoring_dimensions"])["score_value"]
    assert payload["score_result"]["score_value"] == expected_score
    assert payload["feedback_metadata"]["feedback_generation_mode"] == "llm_accepted"
    assert payload["feedback_metadata"]["repair_attempted"] is True
    assert payload["feedback_metadata"]["fallback_reason"] is None


def test_low_confidence_valid_output_is_accepted() -> None:
    feedback_input = _feedback_input(fixture_marker="low_confidence_valid")
    result = _generate_with_fake_feedback_llm(feedback_input)

    payload = result.feedback_payload
    assert payload["feedback_metadata"]["feedback_generation_mode"] == "llm_accepted"
    assert payload["score_result"]["confidence_level"] == "low"
    assert payload["low_confidence_flags"]
    assert payload["feedback_metadata"]["llm_output_validation_status"] == "valid"


def test_repair_then_fallback_records_repair_attempted_and_reason() -> None:
    feedback_input = _feedback_input(fixture_marker="repair_then_fallback")
    result = _generate_with_fake_feedback_llm(feedback_input)

    metadata = result.feedback_payload["feedback_metadata"]
    assert metadata["feedback_generation_mode"] == "llm_fallback"
    assert metadata["repair_attempted"] is True
    assert metadata["fallback_reason"] in {"repair_failed", "consistency_invalid"}


def test_feedback_api_response_omits_raw_prompt_completion_and_provider_payload() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(session_factory, OWNER_A)
    app = _isolated_feedback_app(session_factory)

    with patch.dict(
        "os.environ",
        {
            "AIFI_POLISH_FEEDBACK_LLM_ENABLED": "true",
            "AIFI_POLISH_FEEDBACK_REAL_PROVIDER_ENABLED": "false",
        },
        clear=False,
    ):
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
        progress_node_ref = create_body["data"]["progress_tree_state"]["current_priority"]["progress_node_ref"]
        status_code, question_body = call_json(
            app,
            f"/api/v1/polish-sessions/{session_id}/questions",
            "POST",
            json_body={"progress_node_ref": progress_node_ref},
        )
        assert status_code == 202
        question_id = question_body["data"]["result_ref"]["trace_ref_id"]
        status_code, answer_body = call_json(
            app,
            f"/api/v1/polish-sessions/{session_id}/answers",
            "POST",
            json_body={
                "question_id": question_id,
                "answer_text": "我会先说明系统背景，再补充幂等、失败路径、验证指标和权衡。",
            },
        )
        assert status_code == 201
        answer_id = answer_body["data"]["answer_id"]
        status_code, feedback_body = call_json(
            app,
            f"/api/v1/polish-sessions/{session_id}/feedback",
            "POST",
            json_body={"answer_id": answer_id},
        )
        assert status_code == 202
        status_code, detail_body = call_json(app, f"/api/v1/polish-sessions/{session_id}")

    assert status_code == 200
    payload = feedback_body["data"]["feedback_payload"]
    assert payload["feedback_metadata"]["feedback_generation_mode"] == "llm_accepted"
    assert payload["feedback_metadata"]["fallback_reason"] is None
    _assert_no_raw_llm_payload(feedback_body)
    _assert_no_raw_llm_payload(detail_body)


def test_transport_error_metadata_redacts_sensitive_provider_details() -> None:
    feedback_input = _feedback_input()
    deterministic = _deterministic_payload(feedback_input=feedback_input)

    with patch.dict(
        "os.environ",
        {
            "AIFI_POLISH_FEEDBACK_LLM_ENABLED": "true",
            "AIFI_POLISH_FEEDBACK_REAL_PROVIDER_ENABLED": "true",
        },
        clear=False,
    ):
        result = PolishFeedbackLlmService(_SensitiveUnavailableTransport()).generate_with_llm_or_fallback(
            feedback_input=feedback_input,
            deterministic_payload=deterministic,
        )

    metadata = result.feedback_payload["feedback_metadata"]
    assert metadata["feedback_generation_mode"] == "llm_fallback"
    assert metadata["fallback_reason"] == "provider_unavailable"
    serialized = json.dumps(metadata, ensure_ascii=False, sort_keys=True)
    assert "RAW_PROVIDER_PAYLOAD_SHOULD_NOT_ESCAPE" not in serialized
    assert "RAW_COMPLETION_SHOULD_NOT_ESCAPE" not in serialized
    assert "TOKEN_SHOULD_NOT_ESCAPE" not in serialized
    assert "provider_payload" not in serialized
    assert "raw_completion" not in serialized


class _RecordingRealLikeTransport:
    status = "openai_compatible"

    def __init__(self) -> None:
        self.calls: list[LlmTransportRequest] = []

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        self.calls.append(request)
        return LlmTransportResult(
            result=_fake_static_llm_payload(),
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.MEDIUM,
            low_confidence_flags=(),
            trace_refs=("trace_feedback_real_like",),
            evidence_refs=("evidence_feedback_real_like",),
        )


class _SensitiveUnavailableTransport:
    status = "openai_compatible provider_payload=RAW_PROVIDER_PAYLOAD_SHOULD_NOT_ESCAPE"

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        raise LlmTransportUnavailableError(
            "provider_payload=RAW_PROVIDER_PAYLOAD_SHOULD_NOT_ESCAPE "
            "raw_completion=RAW_COMPLETION_SHOULD_NOT_ESCAPE "
            "token=TOKEN_SHOULD_NOT_ESCAPE"
        )


def _generate_with_fake_feedback_llm(
    feedback_input: FeedbackInput,
    *,
    deterministic_payload: dict[str, Any] | None = None,
) -> Any:
    deterministic = deterministic_payload or _deterministic_payload(feedback_input=feedback_input)
    with patch.dict(
        "os.environ",
        {
            "AIFI_POLISH_FEEDBACK_LLM_ENABLED": "true",
            "AIFI_POLISH_FEEDBACK_REAL_PROVIDER_ENABLED": "false",
        },
        clear=False,
    ):
        return PolishFeedbackLlmService(FakeLlmTransport()).generate_with_llm_or_fallback(
            feedback_input=feedback_input,
            deterministic_payload=deterministic,
        )


def _isolated_feedback_app(session_factory) -> FastAPI:
    return _isolated_polish_app(session_factory, ACTOR_A, llm_transport=FakeLlmTransport())


def _feedback_input(
    *,
    answer_round: int = 1,
    fixture_marker: str | None = None,
    question_metadata: dict[str, Any] | None = None,
) -> FeedbackInput:
    metadata = {
        "question_pattern": "system_design_depth",
        "interview_intent": "验证异常路径、收敛机制和指标。",
        "expected_answer_dimensions": ["technical_depth", "answer_structure", "evidence_alignment"],
        "source_availability": "available",
        **(question_metadata or {}),
    }
    if fixture_marker is not None:
        metadata["feedback_llm_fixture"] = fixture_marker
    base_kwargs = {
        "owner_id": OWNER_A,
        "actor_id": OWNER_A,
        "session_id": "ses_feedback_llm",
        "question_id": "q_feedback_llm",
        "answer_id": f"ans_feedback_llm_{answer_round}",
        "answer_round": answer_round,
        "question_text": "如何设计支付链路的幂等、失败补偿和验证指标？",
        "question_metadata": metadata,
        "question_pattern": "system_design_depth",
        "expected_answer_dimensions": ("technical_depth", "answer_structure", "evidence_alignment"),
        "interview_intent": "验证异常路径、收敛机制和指标。",
        "question_sources": (
            {"source_type": "resume", "ref_id": "res_compact_1", "availability": "available"},
            {"source_type": "job", "ref_id": "job_compact_1", "availability": "available"},
        ),
        "evidence_refs": (
            {"resource_type": "evidence", "resource_id": "ev_feedback_1"},
            {"resource_type": "evidence", "resource_id": "ev_feedback_2"},
        ),
        "answer_text": "我会先说明背景，再补充幂等、失败路径、补偿机制、验证指标和技术取舍。",
        "polish_theme": "technical",
        "source_availability": "available",
        "low_confidence_flags": (),
        "feedback_generation_mode": "deterministic_retry" if answer_round > 1 else "deterministic_initial",
    }
    if answer_round <= 1:
        return FeedbackInput(**base_kwargs)
    return RetryFeedbackInput(
        **base_kwargs,
        previous_answer_rounds=(
            {
                "answer_id": "ans_feedback_llm_1",
                "answer_round": 1,
                "answer_text": "第一轮回答缺少验证指标。",
                "created_at": "2026-05-22T00:00:00+00:00",
            },
        ),
        previous_feedbacks=(_deterministic_payload(feedback_input=FeedbackInput(**{**base_kwargs, "answer_round": 1})),),
        previous_score_results=(),
        previous_dimension_scores=(),
        previous_loss_points=(
            {
                "loss_point_id": "lp_failure_path",
                "title": "失败路径仍需展开",
                "dimension_id": "technical_depth",
                "critical": True,
            },
        ),
        previous_reference_answer="需要覆盖失败路径和验证指标。",
        previous_oral_script="我会补充失败路径和验证指标。",
        repeated_gaps=("lp_failure_path",),
        fixed_gaps=(),
        regression_signals=(),
        mastery_threshold="score>=80_and_no_remaining_critical_loss",
    )


def _retry_feedback_input_without_previous_loss_points() -> RetryFeedbackInput:
    base = _feedback_input(answer_round=2, fixture_marker="valid_retry")
    return RetryFeedbackInput(
        owner_id=base.owner_id,
        actor_id=base.actor_id,
        session_id=base.session_id,
        question_id=base.question_id,
        answer_id=base.answer_id,
        answer_round=base.answer_round,
        question_text=base.question_text,
        question_metadata=base.question_metadata,
        question_pattern=base.question_pattern,
        expected_answer_dimensions=base.expected_answer_dimensions,
        interview_intent=base.interview_intent,
        question_sources=base.question_sources,
        evidence_refs=base.evidence_refs,
        answer_text=base.answer_text,
        polish_theme=base.polish_theme,
        source_availability=base.source_availability,
        low_confidence_flags=base.low_confidence_flags,
        feedback_generation_mode=base.feedback_generation_mode,
        previous_answer_rounds=base.previous_answer_rounds,
        previous_feedbacks=(),
        previous_score_results=(),
        previous_dimension_scores=(),
        previous_loss_points=(),
        previous_reference_answer="",
        previous_oral_script="",
        repeated_gaps=(),
        fixed_gaps=(),
        regression_signals=(),
        mastery_threshold=base.mastery_threshold,
    )


def _deterministic_payload(*, feedback_input: FeedbackInput) -> dict[str, Any]:
    dimensions = [
        {"dimension_id": "technical_depth", "score_value": 80, "max_score": 100, "weight": 2.0},
        {"dimension_id": "answer_structure", "score_value": 70, "max_score": 100, "weight": 1.0},
        {"dimension_id": "evidence_alignment", "score_value": 60, "max_score": 100, "weight": 1.0},
    ]
    score_result = {
        **compute_score_result_from_dimensions(dimensions),
        "score_result_id": "score_feedback_llm",
        "score_type": "polish_answer",
        "score_version": FEEDBACK_SCHEMA_VERSION,
        "rubric_version": "polish_round_score.structured.v1",
        "confidence_level": "medium",
    }
    payload = {
        "schema_id": FEEDBACK_SCHEMA_ID,
        "schema_version": FEEDBACK_SCHEMA_VERSION,
        "status": "generated",
        "feedback_id": "fb_feedback_llm",
        "feedback_text": "deterministic structured feedback",
        "feedback_summary": "deterministic structured feedback",
        "answer_diagnosis": {"strengths": ["结构清晰"], "weaknesses": ["指标不足"]},
        "scoring_dimensions": dimensions,
        "score_result": score_result,
        "positive_evidence_points": [
            {
                "point_id": "pe_metrics",
                "title": "覆盖验证指标",
                "evidence_excerpt": "验证指标",
                "dimension_id": "evidence_alignment",
                "location": "both",
            }
        ],
        "loss_points": [
            {
                "loss_point_id": "lp_failure_path",
                "title": "失败路径仍需展开",
                "deducted_points": 12,
                "reason": "需要补充失败路径、补偿机制和验证指标。",
                "critical": True,
                "dimension_id": "technical_depth",
                "required_reference_terms": ["失败路径", "验证指标"],
                "required_oral_terms": ["失败路径", "验证指标"],
            }
        ],
        "missing_answer_dimensions": [
            {"dimension": "technical_depth", "reason": "失败路径说明不足。"}
        ],
        "interview_intent": feedback_input.interview_intent,
        "p7_reference_answer": "回答应覆盖失败路径、补偿机制和验证指标，并保留验证指标作为证据。",
        "reference_answer_requirements": [],
        "oral_script": "我先说明背景，再讲失败路径、补偿机制、验证指标和取舍。",
        "oral_script_requirements": [],
        "knowledge_points": [],
        "technical_principles": [],
        "technical_gaps": ["失败路径仍需展开"],
        "communication_gaps": [],
        "next_recommended_actions": ["continue_same_question"],
        "weakness_candidates": [],
        "asset_candidates": [],
        "validation_result_ref": {"resource_type": "validation_result", "resource_id": "vr_feedback_llm"},
        "trace_refs": [],
        "low_confidence_flags": [],
        "feedback_metadata": {
            "feedback_input_type": type(feedback_input).__name__,
            "feedback_generation_mode": feedback_input.feedback_generation_mode,
        },
        "score_delta": 0,
        "dimension_delta": {},
        "improved_points": [],
        "remaining_gaps": ["lp_failure_path"],
        "repeated_loss_points": [],
        "regressed_points": [],
        "mastery_status": "stuck" if feedback_input.answer_round > 1 else None,
        "should_continue_same_question": True,
        "should_generate_next_question": False,
        "next_retry_focus": [{"focus_area": "lp_failure_path", "priority": 1}],
        "updated_reference_answer": None,
        "updated_oral_script": None,
        "previous_loss_points": [],
        "question_text": feedback_input.question_text,
        "answer_text": feedback_input.answer_text,
        "answer_id": feedback_input.answer_id,
        "question_id": feedback_input.question_id,
    }
    if isinstance(feedback_input, RetryFeedbackInput):
        previous_loss_point_id = (
            str(feedback_input.previous_loss_points[0]["loss_point_id"])
            if feedback_input.previous_loss_points
            else "lp_missing_previous_loss"
        )
        payload.update(
            {
                "score_delta": 8,
                "dimension_delta": {
                    "technical_depth": 10,
                    "answer_structure": 4,
                    "evidence_alignment": 8,
                },
                "improved_points": [previous_loss_point_id],
                "remaining_gaps": ["lp_failure_path"],
                "repeated_loss_points": [],
                "regressed_points": [],
                "mastery_status": "improving",
                "next_retry_focus": [{"focus_area": "lp_failure_path", "priority": 1}],
                "updated_reference_answer": payload["p7_reference_answer"],
                "updated_oral_script": payload["oral_script"],
                "previous_loss_points": list(feedback_input.previous_loss_points),
            }
        )
    return payload


def _fake_static_llm_payload() -> dict[str, Any]:
    feedback_input = _feedback_input()
    payload = deepcopy(_deterministic_payload(feedback_input=feedback_input))
    payload["feedback_summary"] = "LLM fake first feedback: accepted"
    payload["feedback_text"] = payload["feedback_summary"]
    return payload


def _assert_no_raw_llm_payload(value: Any) -> None:
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True)
    forbidden_tokens = (
        "raw_prompt",
        "raw_completion",
        "provider_payload",
        "provider_response",
        "hidden_rubric",
        "precise pass probability",
        "pass_probability",
    )
    for token in forbidden_tokens:
        assert token not in serialized
