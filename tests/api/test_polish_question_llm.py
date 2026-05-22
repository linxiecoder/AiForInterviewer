from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest

import app.api.v1.polish as polish_api
from app.application.polish.entities import PolishSession
from app.application.polish.progress_tree import build_deterministic_progress_node_question
from app.application.polish.question_llm import PolishQuestionLlmService
from app.application.polish.question_prompts import (
    POLISH_QUESTION_GENERATION_TASK_TYPE,
    build_polish_question_generation_prompt_bundle,
)
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import ConfidenceLevel, ValidationStatus
from app.infrastructure.llm.errors import LlmTransportConfigurationError
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
def _patch_question_api_run_in_threadpool(monkeypatch):
    monkeypatch.setattr(polish_api, "run_in_threadpool", _run_inline_threadpool)


def test_prompt_builder_excludes_raw_resume_and_jd_while_including_compact_signals() -> None:
    deterministic = _deterministic_build()

    bundle = build_polish_question_generation_prompt_bundle(
        session=deterministic.session,
        context=deterministic.context,
        plan=deterministic.plan,
        state=deterministic.state,
        requested_ref=deterministic.requested_ref,
        deterministic_build=deterministic,
    )

    serialized = json.dumps(bundle, ensure_ascii=False, sort_keys=True)
    assert bundle["task_type"] == POLISH_QUESTION_GENERATION_TASK_TYPE
    assert "resume_markdown" not in serialized
    assert "raw_jd" not in serialized
    assert RAW_RESUME_SENTINEL.strip() not in serialized
    assert RAW_JD_SENTINEL.strip() not in serialized
    assert bundle["evidence_bundle"]["evidence_signal_summary"]["source_availability"] == "available"
    assert bundle["evidence_bundle"]["selected_evidence_summaries"]
    assert bundle["evidence_bundle"]["progress_node_summary"]["progress_node_ref"] == "node_payment_consistency"


def test_feature_disabled_path_returns_deterministic_question_without_transport_call() -> None:
    deterministic = _deterministic_build()
    transport = _RecordingRealLikeTransport()

    with patch.dict("os.environ", {"AIFI_POLISH_QUESTION_LLM_ENABLED": "false"}, clear=False):
        result = PolishQuestionLlmService(transport).generate_with_llm_or_fallback(
            session=deterministic.session,
            context=deterministic.context,
            plan=deterministic.plan,
            state=deterministic.state,
            requested_ref=deterministic.requested_ref,
            deterministic_builder=lambda: deterministic,
        )

    assert transport.calls == []
    assert result.draft.question_text == deterministic.draft.question_text
    metadata = result.draft.question_metadata
    assert metadata["llm_generation_mode"] == "deterministic_only"
    assert metadata["fallback_reason"] == "feature_disabled"


def test_real_provider_is_not_used_unless_question_real_provider_flag_is_enabled() -> None:
    deterministic = _deterministic_build()
    transport = _RecordingRealLikeTransport()

    with patch.dict(
        "os.environ",
        {
            "AIFI_POLISH_QUESTION_LLM_ENABLED": "true",
            "AIFI_POLISH_QUESTION_REAL_PROVIDER_ENABLED": "false",
        },
        clear=False,
    ):
        result = PolishQuestionLlmService(transport).generate_with_llm_or_fallback(
            session=deterministic.session,
            context=deterministic.context,
            plan=deterministic.plan,
            state=deterministic.state,
            requested_ref=deterministic.requested_ref,
            deterministic_builder=lambda: deterministic,
        )

    assert transport.calls == []
    assert result.draft.question_text == deterministic.draft.question_text
    assert result.draft.question_metadata["llm_generation_mode"] == "llm_fallback"
    assert result.draft.question_metadata["fallback_reason"] == "real_provider_disabled"


def test_valid_fake_llm_output_is_accepted_and_persistable_without_raw_payload() -> None:
    deterministic = _deterministic_build(fixture_marker="valid_high_quality")

    result = _generate_with_fake_llm(deterministic)

    assert result.draft.question_text != deterministic.draft.question_text
    assert "LLM 合同测试题" in result.draft.question_text
    metadata = result.draft.question_metadata
    assert metadata["llm_generation_mode"] == "llm_accepted"
    assert metadata["llm_output_validation_status"] == "valid"
    assert metadata["fallback_reason"] is None
    _assert_no_raw_llm_payload(metadata)


def test_low_confidence_valid_fake_llm_output_is_accepted_with_visible_metadata_flags() -> None:
    deterministic = _deterministic_build(fixture_marker="low_confidence_valid")

    result = _generate_with_fake_llm(deterministic)

    metadata = result.draft.question_metadata
    assert metadata["llm_generation_mode"] == "llm_accepted"
    assert metadata["llm_output_validation_status"] == "valid"
    assert "llm_low_confidence" in metadata["low_confidence_flags"]
    assert metadata["confidence_level"] == "low"


def test_fake_llm_schema_invalid_output_falls_back_to_deterministic() -> None:
    deterministic = _deterministic_build(fixture_marker="schema_invalid")

    result = _generate_with_fake_llm(deterministic)

    assert result.draft.question_text == deterministic.draft.question_text
    metadata = result.draft.question_metadata
    assert metadata["llm_generation_mode"] == "llm_fallback"
    assert metadata["llm_output_validation_status"] == "schema_invalid"
    assert metadata["fallback_reason"] == "schema_invalid"


def test_fake_llm_fabricated_entity_evidence_ref_and_answer_leak_are_blocked() -> None:
    cases = {
        "fabricated_entity": "fabricated_entity",
        "evidence_refs_invalid": "evidence_refs_invalid",
        "answer_leak": "answer_leak",
    }
    for marker, expected_reason in cases.items():
        deterministic = _deterministic_build(fixture_marker=marker)

        result = _generate_with_fake_llm(deterministic)

        assert result.draft.question_text == deterministic.draft.question_text
        metadata = result.draft.question_metadata
        assert metadata["llm_generation_mode"] == "llm_fallback"
        assert metadata["fallback_reason"] == expected_reason
        _assert_no_raw_llm_payload(metadata)


def test_fake_llm_provider_unavailable_and_timeout_fall_back_to_deterministic() -> None:
    cases = {
        "provider_unavailable": "provider_unavailable",
        "timeout_or_transport_error": "provider_timeout",
    }
    for marker, expected_reason in cases.items():
        deterministic = _deterministic_build(fixture_marker=marker)

        result = _generate_with_fake_llm(deterministic)

        assert result.draft.question_text == deterministic.draft.question_text
        metadata = result.draft.question_metadata
        assert metadata["llm_generation_mode"] == "llm_fallback"
        assert metadata["fallback_reason"] == expected_reason


def test_fake_llm_semantic_invalid_and_repair_paths_are_deterministic() -> None:
    fallback_cases = {
        "semantic_invalid": "semantic_invalid",
        "repair_then_fallback": "output_too_broad",
    }
    for marker, expected_reason in fallback_cases.items():
        deterministic = _deterministic_build(fixture_marker=marker)

        result = _generate_with_fake_llm(deterministic)

        assert result.draft.question_text == deterministic.draft.question_text
        metadata = result.draft.question_metadata
        assert metadata["llm_generation_mode"] == "llm_fallback"
        assert metadata["fallback_reason"] == expected_reason
        _assert_no_raw_llm_payload(metadata)

    deterministic = _deterministic_build(fixture_marker="repair_then_valid")

    result = _generate_with_fake_llm(deterministic)

    metadata = result.draft.question_metadata
    assert metadata["llm_generation_mode"] == "llm_accepted"
    assert metadata["fallback_reason"] is None
    assert metadata["repair_attempted"] is True


def test_transport_configuration_error_falls_back_to_deterministic() -> None:
    deterministic = _deterministic_build()

    with patch.dict("os.environ", {"AIFI_POLISH_QUESTION_LLM_ENABLED": "true"}, clear=False):
        result = PolishQuestionLlmService(_ConfigurationErrorTransport()).generate_with_llm_or_fallback(
            session=deterministic.session,
            context=deterministic.context,
            plan=deterministic.plan,
            state=deterministic.state,
            requested_ref=deterministic.requested_ref,
            deterministic_builder=lambda: deterministic,
        )

    assert result.draft.question_text == deterministic.draft.question_text
    metadata = result.draft.question_metadata
    assert metadata["llm_generation_mode"] == "llm_fallback"
    assert metadata["fallback_reason"] == "transport_configuration_error"
    assert metadata["validation_errors"][0]["code"] == "transport_configuration_error"


def test_missing_required_and_unknown_fields_do_not_enter_metadata() -> None:
    deterministic = _deterministic_build()
    evidence_refs = list(deterministic.question_context.evidence_refs)
    missing_required_payload = _valid_llm_payload(evidence_refs=evidence_refs)
    missing_required_payload.pop("status")

    missing_result = _generate_with_static_transport(deterministic, missing_required_payload)

    assert missing_result.draft.question_text == deterministic.draft.question_text
    missing_metadata = missing_result.draft.question_metadata
    assert missing_metadata["llm_generation_mode"] == "llm_fallback"
    assert missing_metadata["fallback_reason"] == "schema_invalid"
    assert missing_metadata["validation_errors"][0] == {
        "code": "required_field_missing",
        "message": "status",
    }

    unknown_payload = _valid_llm_payload(evidence_refs=evidence_refs)
    unknown_payload["model_name"] = "raw-output-model-should-not-persist"
    unknown_payload["extra_unknown"] = {"nested": "unknown-output-field-should-not-persist"}

    accepted_result = _generate_with_static_transport(deterministic, unknown_payload)

    accepted_metadata = accepted_result.draft.question_metadata
    serialized = json.dumps(accepted_metadata, ensure_ascii=False, sort_keys=True)
    assert accepted_metadata["llm_generation_mode"] == "llm_accepted"
    assert accepted_metadata["model_summary"] == {"kind": "safe_summary", "model_name": "not_recorded"}
    assert "raw-output-model-should-not-persist" not in serialized
    assert "unknown-output-field-should-not-persist" not in serialized


def test_question_api_response_omits_raw_prompt_completion_and_provider_payload() -> None:
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(session_factory, OWNER_A)
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=FakeLlmTransport())

    with patch.dict(
        "os.environ",
        {
            "AIFI_POLISH_QUESTION_LLM_ENABLED": "true",
            "AIFI_POLISH_QUESTION_REAL_PROVIDER_ENABLED": "false",
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
        status_code, detail_body = call_json(app, f"/api/v1/polish-sessions/{session_id}")

    assert status_code == 200
    turn = detail_body["data"]["turns"][0]
    metadata = turn["question_metadata"]
    assert metadata["llm_generation_mode"] == "llm_accepted"
    assert question_body["data"]["status"] == "succeeded"
    _assert_no_raw_llm_payload(detail_body)


class _RecordingRealLikeTransport:
    status = "openai_compatible"

    def __init__(self) -> None:
        self.calls: list[LlmTransportRequest] = []

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        self.calls.append(request)
        evidence_refs = _input_evidence_refs(request)
        return LlmTransportResult(
            result=_valid_llm_payload(evidence_refs=evidence_refs),
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.MEDIUM,
            low_confidence_flags=(),
            trace_refs=("trace_real_like",),
            evidence_refs=tuple(evidence_refs),
        )


class _ConfigurationErrorTransport:
    status = "fake_question_configuration_error"

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        raise LlmTransportConfigurationError("fake question transport config error")


class _StaticQuestionTransport:
    status = "fake_static_question"

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        evidence_refs = _input_evidence_refs(request)
        return LlmTransportResult(
            result=self._payload,
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.MEDIUM,
            low_confidence_flags=(),
            trace_refs=("trace_static_question",),
            evidence_refs=tuple(evidence_refs),
        )


def _generate_with_fake_llm(deterministic) -> Any:
    with patch.dict(
        "os.environ",
        {
            "AIFI_POLISH_QUESTION_LLM_ENABLED": "true",
            "AIFI_POLISH_QUESTION_REAL_PROVIDER_ENABLED": "false",
        },
        clear=False,
    ):
        return PolishQuestionLlmService(FakeLlmTransport()).generate_with_llm_or_fallback(
            session=deterministic.session,
            context=deterministic.context,
            plan=deterministic.plan,
            state=deterministic.state,
            requested_ref=deterministic.requested_ref,
            deterministic_builder=lambda: deterministic,
        )


def _generate_with_static_transport(deterministic, payload: dict[str, Any]) -> Any:
    with patch.dict("os.environ", {"AIFI_POLISH_QUESTION_LLM_ENABLED": "true"}, clear=False):
        return PolishQuestionLlmService(_StaticQuestionTransport(payload)).generate_with_llm_or_fallback(
            session=deterministic.session,
            context=deterministic.context,
            plan=deterministic.plan,
            state=deterministic.state,
            requested_ref=deterministic.requested_ref,
            deterministic_builder=lambda: deterministic,
        )


def _deterministic_build(*, fixture_marker: str | None = None):
    session, context, plan, state, requested_ref = _question_inputs(fixture_marker=fixture_marker)
    return build_deterministic_progress_node_question(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=requested_ref,
    )


def _question_inputs(*, fixture_marker: str | None = None):
    now = utc_now()
    session = PolishSession(
        session_id="ses_question_llm",
        owner_id="usr_question_llm",
        actor_id="usr_question_llm",
        binding_id="bind_question_llm",
        resume_id="res_question_llm",
        resume_version_id="res_ver_question_llm",
        job_id="job_question_llm",
        job_version_id="job_ver_question_llm",
        status="running",
        topic_id="topic_technical_depth",
        subtopic_id=None,
        custom_topic_text_summary="支付链路一致性",
        created_at=now,
        updated_at=now,
        polish_theme="technical",
        progress_tree_status="ready",
    )
    node = {
        "progress_node_ref": "node_payment_consistency",
        "title": "支付链路一致性",
        "expected_capability": "能说明接口幂等、失败补偿、性能指标、成本控制和可观测性。",
        "related_job_requirements": ["要求能设计高可用后端链路、接口幂等、失败补偿和监控指标。"],
        "related_resume_evidence": ["候选人做过 FastAPI 支付工作流，关注接口幂等、失败重试和 trace 指标。"],
        "missing_points": ["需要补充异常状态收敛口径。"],
        "children": [],
    }
    context = {
        "content_digest": "question-llm-test-digest",
        "question_llm_fixture": fixture_marker,
        "resume_markdown": RAW_RESUME_SENTINEL,
        "job_payload": {"raw_jd": RAW_JD_SENTINEL},
        "job_snapshot": {
            "job_id": "job_question_llm",
            "job_version_id": "job_ver_question_llm",
            "requirements": ["要求能设计高可用后端链路、接口幂等、失败补偿和监控指标。"],
            "responsibilities": ["负责支付链路稳定性、性能成本和可观测建设。"],
        },
        "resume_snapshot": {
            "resume_id": "res_question_llm",
            "resume_version_id": "res_ver_question_llm",
            "summary": "后端工程师，做过支付工作流可靠性建设。",
            "project_experiences": ["FastAPI 支付工作流：接口幂等、失败重试、trace 指标和成本控制。"],
            "skills": ["FastAPI", "PostgreSQL"],
        },
        "match_context": {
            "analysis_id": "ana_question_llm",
            "missing_points": ["需要补充异常状态收敛口径。"],
        },
        "turns": [
            {
                "question_id": "que_recent_1",
                "question_text": "围绕支付链路，请说明一次接口幂等设计。",
            }
        ],
    }
    plan = {"status": "ready", "context_digest": "question-llm-test-digest", "nodes": [node]}
    state = {
        "status": "ready",
        "current_priority": {
            "progress_node_ref": "node_payment_consistency",
            "title": "支付链路一致性",
            "expected_capability": node["expected_capability"],
        },
        "node_states": [],
        "progress": {"progress_percent": 0},
    }
    return session, context, plan, state, "node_payment_consistency"


def _input_evidence_refs(request: LlmTransportRequest) -> list[str]:
    evidence_bundle = request.evidence_bundle.get("evidence_bundle", {})
    refs = evidence_bundle.get("input_evidence_refs", [])
    return [str(ref) for ref in refs]


def _valid_llm_payload(*, evidence_refs: list[str]) -> dict[str, Any]:
    return {
        "schema_id": "polish_question_generation_output_v1",
        "schema_version": 1,
        "status": "generated",
        "question_text": (
            "LLM 合同测试题：围绕「支付链路一致性」，请从 Owner 视角先限定业务约束，"
            "再选择一个失败路径说明性能或成本约束、验证指标、可观测指标和核心 trade-off；"
            "如果接口幂等、补偿或重试失败，如何让状态收敛？"
            "回答重点：业务边界、核心链路、失败路径、资源约束、验证指标、后续补材料。[1][2]"
        ),
        "question_pattern": "owner_tradeoff_system_design",
        "interview_intent": "验证候选人能否把支付链路异常收敛讲清楚。",
        "scenario_constraint_summary": "支付链路需要稳定性、成本和可观测性。",
        "expected_answer_dimensions": ["业务边界", "核心链路", "失败路径", "资源约束", "验证指标", "后续补材料"],
        "evidence_refs": evidence_refs,
        "source_availability": "available",
        "confidence_level": "medium",
        "low_confidence_flags": [],
        "quality_hints": ["绑定已选 progress_node_ref"],
        "requires_repair": False,
        "redaction_boundary": "no_raw_prompt_completion_provider_payload",
    }


def _assert_no_raw_llm_payload(payload: object) -> None:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    forbidden = (
        "raw_prompt",
        "raw completion",
        "raw_completion",
        "completion",
        "provider_payload",
        "provider payload",
        RAW_RESUME_SENTINEL.strip(),
        RAW_JD_SENTINEL.strip(),
    )
    assert not any(item in serialized for item in forbidden), serialized
