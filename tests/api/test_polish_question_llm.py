from __future__ import annotations

import json
import logging
from dataclasses import replace
from types import SimpleNamespace
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
    select_primary_question_evidence,
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
SENSITIVE_PROMPT_SENTINEL = "SENSITIVE_PROMPT_TEXT_SHOULD_NOT_APPEAR"
SENSITIVE_COMPLETION_SENTINEL = "SENSITIVE_COMPLETION_TEXT_SHOULD_NOT_APPEAR"
SENSITIVE_SOURCE_EXCERPT_SENTINEL = "SENSITIVE_SOURCE_EXCERPT_TEXT_SHOULD_NOT_APPEAR"
SENSITIVE_SECRET_SENTINEL = "SENSITIVE_API_KEY_TOKEN_SECRET_SHOULD_NOT_APPEAR"
QUESTION_LLM_LOGGER = "app"
INSUFFICIENT_PRIMARY_EVIDENCE_FALLBACK = (
    "当前材料不足以支撑具体业务场景。请先补充一个你真实参与的项目链路，"
    "包括业务入口、你的职责边界、一个失败案例和一个验证指标，再按技术深度和表达结构回答。"
)


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


def test_prompt_input_evidence_refs_match_validator_allowed_chunk_refs() -> None:
    deterministic = _deterministic_build()

    bundle = build_polish_question_generation_prompt_bundle(
        session=deterministic.session,
        context=deterministic.context,
        plan=deterministic.plan,
        state=deterministic.state,
        requested_ref=deterministic.requested_ref,
        deterministic_build=deterministic,
    )

    evidence_bundle = bundle["evidence_bundle"]
    input_evidence_refs = evidence_bundle["input_evidence_refs"]
    question_context_refs = list(deterministic.question_context.evidence_refs)
    selected_chunk_ids = [chunk.chunk_id for chunk in deterministic.question_context.evidence_chunks]
    input_source_refs = evidence_bundle["input_source_refs"]
    source_ref_ids = [source["ref_id"] for source in input_source_refs if source.get("ref_id")]

    assert isinstance(input_evidence_refs, list)
    assert input_evidence_refs
    assert all(isinstance(ref, str) for ref in input_evidence_refs)
    assert input_evidence_refs == question_context_refs
    assert input_evidence_refs == selected_chunk_ids
    assert input_source_refs
    assert source_ref_ids
    assert set(source_ref_ids).isdisjoint(input_evidence_refs)


def test_prompt_bundle_contains_primary_question_evidence_and_anti_repeat_contract() -> None:
    deterministic = _deterministic_build()

    bundle = build_polish_question_generation_prompt_bundle(
        session=deterministic.session,
        context=deterministic.context,
        plan=deterministic.plan,
        state=deterministic.state,
        requested_ref=deterministic.requested_ref,
        deterministic_build=deterministic,
    )

    evidence_bundle = bundle["evidence_bundle"]
    primary = evidence_bundle["primary_question_evidence"]

    assert primary["ref"] == "resume_project_001"
    assert primary["source_type"] == "resume_project"
    assert primary["claim_mode"] == "candidate_experience"
    assert "FastAPI 支付工作流" in primary["summary"]
    assert primary["ref"] in primary["allowed_source_refs"]
    assert set(primary["allowed_source_refs"]).issubset(set(evidence_bundle["input_evidence_refs"]))
    assert evidence_bundle["recent_question_usage"] == "anti_repeat_only"


def test_prompt_contract_describes_evidence_refs_allowed_and_forbidden_refs() -> None:
    deterministic = _deterministic_build()

    bundle = build_polish_question_generation_prompt_bundle(
        session=deterministic.session,
        context=deterministic.context,
        plan=deterministic.plan,
        state=deterministic.state,
        requested_ref=deterministic.requested_ref,
        deterministic_build=deterministic,
    )

    prompt_text = "\n".join(bundle["prompt"])
    schema_text = json.dumps(bundle["output_schema"], ensure_ascii=False, sort_keys=True)

    assert "input_evidence_refs" in prompt_text
    assert "evidence_refs" in prompt_text
    assert "string[]" in prompt_text
    assert "copy exactly" in prompt_text
    assert "do not use input_source_refs" in prompt_text
    assert "not object" in prompt_text
    assert "do not invent" in prompt_text
    assert "source refs" in prompt_text
    assert "progress refs" in prompt_text
    assert "array<string>" in schema_text
    assert "input_evidence_refs" in schema_text
    assert "source refs" in schema_text
    assert "progress refs" in schema_text
    assert "object refs" in schema_text
    assert "invented refs" in schema_text
    assert "natural language citations" in schema_text
    assert "comma-separated string" in schema_text


def test_prompt_contract_requires_pattern_required_elements_in_question_text() -> None:
    deterministic = _deterministic_build()

    bundle = build_polish_question_generation_prompt_bundle(
        session=deterministic.session,
        context=deterministic.context,
        plan=deterministic.plan,
        state=deterministic.state,
        requested_ref=deterministic.requested_ref,
        deterministic_build=deterministic,
    )

    evidence_bundle = bundle["evidence_bundle"]
    required_elements = evidence_bundle["question_pattern"]["required_question_elements"]
    prompt_text = "\n".join(bundle["prompt"])
    schema_text = json.dumps(bundle["output_schema"], ensure_ascii=False, sort_keys=True)
    contract_text = f"{prompt_text}\n{schema_text}"

    assert required_elements == list(deterministic.question_pattern.required_question_elements)
    assert "selected_question_pattern.required_question_elements" in contract_text
    assert "question_text" in contract_text
    assert "copy/include each required element" in contract_text
    assert "semantic validation" in contract_text
    assert "missing_pattern_required_elements" in contract_text
    assert "semantic validation target" in schema_text
    assert "all selected pattern required elements" in schema_text
    assert "question_pattern" in schema_text


def test_prompt_contract_grounds_business_constraint_on_primary_evidence() -> None:
    deterministic = _deterministic_build()

    bundle = build_polish_question_generation_prompt_bundle(
        session=deterministic.session,
        context=deterministic.context,
        plan=deterministic.plan,
        state=deterministic.state,
        requested_ref=deterministic.requested_ref,
        deterministic_build=deterministic,
    )

    evidence_bundle = bundle["evidence_bundle"]
    prompt_text = "\n".join(bundle["prompt"])
    schema_text = json.dumps(bundle["output_schema"], ensure_ascii=False, sort_keys=True)
    contract_text = f"{prompt_text}\n{schema_text}"

    assert evidence_bundle["primary_question_evidence"]["summary"]
    assert evidence_bundle["scenario_constraint"]["business_constraint"]
    assert "请只围绕 primary_question_evidence 生成题目" in contract_text
    assert "primary_question_evidence.summary" in contract_text
    assert "scenario_constraint 只是补充上下文" in contract_text
    assert "不能引入 primary_question_evidence 不支持的新业务场景" in contract_text
    assert "recent_question_texts 只用于避免重复" in contract_text
    assert "不得模仿其中的业务场景组合" in contract_text
    assert "claim_mode 是 job_gap_probe" in contract_text
    assert "claim_mode 是 clarification_needed" in contract_text
    assert "must include scenario_constraint.business_constraint" not in contract_text
    assert "business_constraint" in contract_text
    assert "scenario_constraint_summary" in contract_text
    assert "question_text" in contract_text
    assert "technical / mixed" in contract_text
    assert "业务约束" in contract_text
    assert "semantic validation" in contract_text


def test_feature_disabled_path_returns_deterministic_question_without_transport_call(caplog) -> None:
    deterministic = _deterministic_build()
    transport = _RecordingRealLikeTransport()

    with caplog.at_level(logging.INFO, logger=QUESTION_LLM_LOGGER):
        with patch.dict("os.environ", {"AIFI_POLISH_QUESTION_LLM_ENABLED": "false"}, clear=False):
            result = PolishQuestionLlmService(transport).generate_with_llm_or_fallback(
                session=deterministic.session,
                context=deterministic.context,
                plan=deterministic.plan,
                state=deterministic.state,
                requested_ref=deterministic.requested_ref,
                deterministic_builder=lambda: deterministic,
            )

    assert _has_log_record(
        caplog,
        "polish_question_llm_fallback",
        "feature_disabled",
        "deterministic_only",
    )

    assert transport.calls == []
    assert result.draft.question_text == deterministic.draft.question_text
    metadata = result.draft.question_metadata
    assert metadata["llm_generation_mode"] == "deterministic_only"
    assert metadata["fallback_reason"] == "feature_disabled"


def test_real_provider_is_not_used_unless_question_real_provider_flag_is_enabled(caplog) -> None:
    deterministic = _deterministic_build()
    transport = _RecordingRealLikeTransport()

    with caplog.at_level(logging.INFO, logger=QUESTION_LLM_LOGGER):
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

    assert _has_log_record(
        caplog,
        "polish_question_llm_fallback",
        "real_provider_disabled",
        "llm_fallback",
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
    assert metadata["primary_question_evidence_ref"] == "resume_project_001"
    assert metadata["claim_mode"] == "candidate_experience"
    assert metadata["grounding_gate_result"] == "passed"
    assert metadata["grounding_gate_issues"] == []
    assert metadata["primary_question_evidence"]["ref"] == "resume_project_001"
    _assert_no_raw_llm_payload(metadata)


def test_low_confidence_valid_fake_llm_output_is_accepted_with_visible_metadata_flags() -> None:
    deterministic = _deterministic_build(fixture_marker="low_confidence_valid")

    result = _generate_with_fake_llm(deterministic)

    metadata = result.draft.question_metadata
    assert metadata["llm_generation_mode"] == "llm_accepted"
    assert metadata["llm_output_validation_status"] == "valid"
    assert "llm_low_confidence" in metadata["low_confidence_flags"]
    assert metadata["confidence_level"] == "low"


def test_fake_llm_schema_invalid_output_falls_back_to_deterministic(caplog) -> None:
    deterministic = _deterministic_build(fixture_marker="schema_invalid")

    with caplog.at_level(logging.INFO, logger=QUESTION_LLM_LOGGER):
        result = _generate_with_fake_llm(deterministic)

    assert _has_log_record(
        caplog,
        "polish_question_llm_fallback",
        "schema_invalid",
        "llm_fallback",
    )

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


def test_source_ref_returned_as_evidence_ref_is_rejected_with_redacted_diagnostics() -> None:
    deterministic = _deterministic_build()
    allowed_refs = list(
        select_primary_question_evidence(
            session=deterministic.session,
            deterministic_build=deterministic,
        )["allowed_source_refs"]
    )
    source_ref = next(
        source.ref_id for source in deterministic.question_context.sources if source.ref_id not in allowed_refs
    )
    payload = _valid_llm_payload(evidence_refs=[allowed_refs[0], source_ref])

    result = _generate_with_static_transport(deterministic, payload)

    assert result.llm_output is None
    assert result.draft.question_text == deterministic.draft.question_text
    metadata = result.draft.question_metadata
    assert metadata["llm_generation_mode"] == "llm_fallback"
    assert metadata["llm_output_validation_status"] == "semantic_invalid"
    assert metadata["fallback_reason"] == "evidence_refs_invalid"
    error = metadata["validation_errors"][0]
    assert error["code"] == "evidence_refs_invalid"
    assert error["validation_error_code"] == "evidence_refs_invalid"
    assert error["fallback_reason"] == "evidence_refs_invalid"
    assert error["allowed_refs_sample"] == allowed_refs[:10]
    assert error["returned_refs_sample"] == [allowed_refs[0], source_ref]
    assert error["invalid_refs"] == [source_ref]
    _assert_redacted_diagnostics(metadata)


def test_object_ref_returned_as_evidence_ref_is_rejected_without_loose_conversion() -> None:
    deterministic = _deterministic_build()
    allowed_refs = list(deterministic.question_context.evidence_refs)
    object_ref = {
        "ref_id": allowed_refs[0],
        "prompt_text": SENSITIVE_PROMPT_SENTINEL,
        "model_output": SENSITIVE_COMPLETION_SENTINEL,
        "source_excerpt": SENSITIVE_SOURCE_EXCERPT_SENTINEL,
        "api_key": SENSITIVE_SECRET_SENTINEL,
        "token": SENSITIVE_SECRET_SENTINEL,
        "secret": SENSITIVE_SECRET_SENTINEL,
    }
    payload = _valid_llm_payload(evidence_refs=[object_ref])

    result = _generate_with_static_transport(deterministic, payload)

    assert result.llm_output is None
    assert result.draft.question_text == deterministic.draft.question_text
    metadata = result.draft.question_metadata
    assert metadata["llm_generation_mode"] == "llm_fallback"
    assert metadata["llm_output_validation_status"] == "semantic_invalid"
    assert metadata["fallback_reason"] == "evidence_refs_invalid"
    error = metadata["validation_errors"][0]
    assert error["code"] == "evidence_refs_invalid"
    assert error["returned_refs_sample"] == ["<dict>"]
    assert error["invalid_refs"] == ["<dict>"]
    assert allowed_refs[0] not in error["returned_refs_sample"]
    assert allowed_refs[0] not in error["invalid_refs"]
    _assert_redacted_diagnostics(metadata)


def test_empty_evidence_refs_are_rejected_with_redacted_diagnostics() -> None:
    deterministic = _deterministic_build()
    allowed_refs = list(
        select_primary_question_evidence(
            session=deterministic.session,
            deterministic_build=deterministic,
        )["allowed_source_refs"]
    )
    payload = _valid_llm_payload(evidence_refs=[])

    result = _generate_with_static_transport(deterministic, payload)

    assert result.llm_output is None
    assert result.draft.question_text == deterministic.draft.question_text
    metadata = result.draft.question_metadata
    assert metadata["llm_generation_mode"] == "llm_fallback"
    assert metadata["llm_output_validation_status"] == "semantic_invalid"
    assert metadata["fallback_reason"] == "evidence_refs_invalid"
    error = metadata["validation_errors"][0]
    assert error["code"] == "evidence_refs_empty"
    assert error["validation_error_code"] == "evidence_refs_empty"
    assert error["fallback_reason"] == "evidence_refs_invalid"
    assert error["allowed_refs_sample"] == allowed_refs[:10]
    assert error["returned_refs_sample"] == []
    assert error["invalid_refs"] == []
    _assert_redacted_diagnostics(metadata)


def test_semantic_invalid_includes_pattern_and_business_constraint_diagnostics() -> None:
    deterministic = _deterministic_build()
    evidence_refs = list(deterministic.question_context.evidence_refs)
    payload = _valid_llm_payload(evidence_refs=evidence_refs)
    payload["question_text"] = "LLM 合同测试题：围绕「支付链路一致性」，请说明接口幂等如何落地。[1]"

    result = _generate_with_static_transport(deterministic, payload)

    assert result.llm_output is None
    assert result.draft.question_text == deterministic.draft.question_text
    metadata = result.draft.question_metadata
    assert metadata["llm_generation_mode"] == "llm_fallback"
    assert metadata["llm_output_validation_status"] == "semantic_invalid"
    assert metadata["fallback_reason"] == "semantic_invalid"
    errors = {error["code"]: error for error in metadata["validation_errors"]}
    assert "missing_pattern_required_elements" in errors
    assert "missing_business_constraint" in errors

    required_error = errors["missing_pattern_required_elements"]
    assert required_error["validation_error_code"] == "missing_pattern_required_elements"
    assert required_error["fallback_reason"] == "semantic_invalid"
    assert required_error["selected_pattern_id"] == deterministic.question_pattern.pattern_id
    assert required_error["selected_pattern_name"] == deterministic.question_pattern.title
    assert required_error["theme"] == deterministic.question_context.strategy.theme
    assert required_error["missing_required_elements_sample"]
    assert required_error["required_elements_sample"] == list(deterministic.question_pattern.required_question_elements)[:10]

    business_error = errors["missing_business_constraint"]
    assert business_error["validation_error_code"] == "missing_business_constraint"
    assert business_error["fallback_reason"] == "semantic_invalid"
    assert business_error["selected_pattern_id"] == deterministic.question_pattern.pattern_id
    assert business_error["theme"] == deterministic.question_context.strategy.theme
    assert business_error["business_constraint_label"]
    assert business_error["business_constraint_marker_required"] == ["业务约束", "新业务约束"]
    assert "question_text" not in required_error
    assert "question_text" not in business_error
    _assert_redacted_diagnostics(metadata)


def test_llm_grounding_violation_falls_back_to_insufficient_primary_evidence_question() -> None:
    deterministic = _deterministic_build()
    deterministic = replace(
        deterministic,
        scenario_constraint=SimpleNamespace(
            business_constraint="1GB 日志上传、解析、切块、向量化、入库",
            failure_mode="日志解析失败或入库失败会导致链路卡住",
            scale_or_performance_constraint="1GB 日志从 15 秒优化到 3 秒",
            consistency_constraint="切块、向量化和入库状态必须一致",
            cost_constraint="向量化成本需要可控",
            observability_constraint="解析耗时、入库成功率和错误率",
            system_components=("日志上传", "解析", "切块", "向量化", "入库"),
            technical_entities=("日志", "向量化"),
            metrics=("1GB", "15 秒", "3 秒"),
            confidence_level="high",
            low_confidence_flags=(),
            evidence_refs=("match_gap_001",),
        ),
    )
    evidence_refs = list(deterministic.question_context.evidence_refs)
    payload = _valid_llm_payload(evidence_refs=evidence_refs)
    payload["question_text"] = (
        "围绕「分布式锁与事务消息最终一致性设计」，业务约束是 1GB 日志上传、解析、切块、向量化、入库。"
        "请从 Owner 视角说明库存扣减链路中 Redisson 分布式锁、RocketMQ 事务消息和日志向量化管道的失败路径、"
        "性能或成本约束、验证指标、可观测指标和核心 trade-off。"
    )

    result = _generate_with_static_transport(deterministic, payload)

    assert result.llm_output is None
    assert result.draft.question_text == INSUFFICIENT_PRIMARY_EVIDENCE_FALLBACK
    metadata = result.draft.question_metadata
    assert metadata["llm_generation_mode"] == "llm_fallback"
    assert metadata["llm_output_validation_status"] == "semantic_invalid"
    assert metadata["fallback_reason"] == "semantic_invalid"
    assert metadata["primary_question_evidence_ref"] == "resume_project_001"
    assert metadata["claim_mode"] == "candidate_experience"
    assert metadata["grounding_gate_result"] == "blocked"
    assert "primary_evidence_grounding_violation" in metadata["grounding_gate_issues"]
    assert any(error["code"] == "primary_evidence_grounding_violation" for error in metadata["validation_errors"])


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


def _assert_redacted_diagnostics(payload: object) -> None:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    forbidden = (
        "raw_prompt",
        "raw completion",
        "raw_completion",
        "raw_response",
        "api_key",
        "token",
        "secret",
        "source_excerpt",
        "provider_payload",
        "provider payload",
        RAW_RESUME_SENTINEL.strip(),
        RAW_JD_SENTINEL.strip(),
        SENSITIVE_PROMPT_SENTINEL,
        SENSITIVE_COMPLETION_SENTINEL,
        SENSITIVE_SOURCE_EXCERPT_SENTINEL,
        SENSITIVE_SECRET_SENTINEL,
    )
    assert not any(item in serialized for item in forbidden), serialized


def _has_log_record(caplog, *tokens: str) -> bool:
    return any(
        record.name == QUESTION_LLM_LOGGER and all(token in record.getMessage() for token in tokens)
        for record in caplog.records
    )
