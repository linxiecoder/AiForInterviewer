from __future__ import annotations

import json
import logging
from typing import Any

import pytest

import app.application.llm.agent_io as agent_io
from app.application.llm.errors import LlmTransportUnavailableError
from app.application.llm.agent_io import AgentFocusTarget
from app.application.llm.types import LlmTransportRequest, LlmTransportResult
from app.application.polish.commands import CreatePolishFeedbackTaskCommand
from app.application.polish.entities import PolishAnswer, PolishFeedback
from app.application.polish.feedback_generation_service import FeedbackGenerationResult
from app.application.polish.question_blueprint import EvidenceScope, QuestionBlueprint
from app.application.polish.next_question_agent import (
    NEXT_QUESTION_AGENT_PROMPT_VERSION,
    NEXT_QUESTION_AGENT_SCHEMA_ID,
    NEXT_QUESTION_AGENT_SCHEMA_VERSION,
)
from app.application.polish.queries import GetPolishSessionQuery
from app.application.polish.question_generation_prompts import (
    QUESTION_FOLLOW_UP_PROMPT_TASK_TYPE,
    build_question_prompt_asset,
    validate_question_prompt_anchor_contract,
)
from app.application.polish.question_generation_policy import (
    QuestionGenerationPolicyResolutionContext,
    QuestionGenerationRuntimePolicy,
)
from app.application.polish.question_generation_service import (
    QuestionGenerationService,
    _focus_target_from_progress_node,
    _parse_llm_question_payload,
)
from app.application.polish.question_metadata import normalize_question_metadata
from app.application.polish.use_cases import (
    PolishAnswerApplicationService,
    PolishFeedbackApplicationService,
    PolishProgressApplicationService,
    PolishQuestionApplicationService,
    PolishReportApplicationService,
    PolishSessionApplicationService,
)
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import AiTaskStatus, ConfidenceLevel, ValidationStatus
from app.infrastructure.observability.logging import BackendLogSettings, LogUtil
from app.infrastructure.llm.fake_transport import FakeLlmTransport

from tests.api.test_polish_question_graph_integration import (
    ACTOR_ID,
    NODE_REF,
    OWNER_ID,
    SESSION_ID,
    _command,
    _use_cases,
)


QUESTION_PROVIDER_REQUEST_TOP_LEVEL_KEYS = {
    "task_type",
    "schema_id",
    "schema_version",
    "prompt_version",
    "progress_node",
    "source_support_level",
    "canonical_evidence",
    "history_summary",
    "expected_output_contract",
    "safety_rules_summary",
}

QUESTION_PROMPT_ASSET_TOP_LEVEL_KEYS = {
    "asset_id",
    "prompt_version",
    "schema_id",
    "schema_version",
    "task_type",
    "policy_version",
    "policy_source",
    "policy_source_type",
    "policy_source_version",
    "policy_fallback",
    "prompt",
    "system_role",
    "developer_constraints",
    "user_task",
    "input_contract",
    "input_data",
    "evidence_retrieval_hints",
    "evidence_selection_policy",
    "output_schema",
    "examples",
    "citation_rules",
    "refusal_and_low_confidence_policy",
    "conflict_check",
}


class _FeedbackGenerationServiceStub:
    def __init__(self) -> None:
        self.contexts: list[Any] = []

    def generate(self, context: Any) -> FeedbackGenerationResult:
        self.contexts.append(context)
        return FeedbackGenerationResult(
            succeeded=True,
            payload={
                "schema_id": "polish_feedback_generated_v1",
                "schema_version": "1.0",
                "status": "generated",
                "contract_ids": ["P-POLISH-003", "P-POLISH-004", "P-POLISH-005"],
                "feedback_text": "真实反馈来自替换后的生成服务。",
                "answer_summary": "候选人说明了业务背景、一致性方案和验证指标。",
                "score_result": {"score_type": "polish_answer", "score_value": 88},
                "explicit_score": 88,
                "implicit_score": 86,
                "loss_points": [],
                "reference_answer": {"sections": []},
                "knowledge_points": [],
                "technical_principles": [],
                "same_question_effect": {
                    "improved_points": [],
                    "repeated_loss_point_ids": [],
                    "regressed_points": [],
                    "next_retry_focus": [],
                    "score_delta": 0,
                },
                "project_asset_consistency_check": {"status": "not_applicable"},
                "session_similarity_check": {"status": "not_applicable"},
                "project_asset_update_candidates": [],
                "next_recommended_actions": ["continue_same_question"],
                "low_confidence_flags": [],
                "trace_refs": [{"resource_type": "llm_trace", "resource_id": "trace_feedback_stub"}],
                "feedback_metadata": {"llm_called": True},
            },
            metadata={"llm_called": True},
        )


def test_polish_use_cases_facade_syncs_replaced_question_generation_service() -> None:
    transport = _RecordingQuestionTransport()
    use_cases, repository = _use_cases(ai_orchestration_facade=None)

    use_cases._question_generation_service = QuestionGenerationService(llm_transport=transport)
    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert isinstance(use_cases._session_service, PolishSessionApplicationService)
    assert isinstance(use_cases._question_service, PolishQuestionApplicationService)
    assert isinstance(use_cases._answer_service, PolishAnswerApplicationService)
    assert isinstance(use_cases._feedback_service, PolishFeedbackApplicationService)
    assert isinstance(use_cases._progress_service, PolishProgressApplicationService)
    assert isinstance(use_cases._report_service, PolishReportApplicationService)
    assert len(transport.requests) == 1
    assert len(repository.questions) == 1


def test_polish_use_cases_facade_syncs_replaced_feedback_generation_service() -> None:
    feedback_generation_service = _FeedbackGenerationServiceStub()
    use_cases, repository = _use_cases(ai_orchestration_facade=None)
    use_cases._feedback_generation_service = feedback_generation_service
    question_result = use_cases.create_question_task(_command())
    assert question_result.is_success
    question = repository.questions[0]
    answer = PolishAnswer(
        answer_id="ans_phase2_generated",
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        question_id=question.question_id,
        answer_round=1,
        answer_text="我会先说明业务背景，再说明一致性方案和验证指标。",
        status="saved",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    repository.answers = [answer]
    repository.feedbacks = []
    repository.get_answer = lambda owner_id, answer_id: next(
        (item for item in repository.answers if item.owner_id == owner_id and item.answer_id == answer_id),
        None,
    )
    repository.list_answers_for_session = lambda owner_id, session_id: tuple(
        item for item in repository.answers if item.owner_id == owner_id and item.session_id == session_id
    )
    repository.add_feedback = lambda feedback: repository.feedbacks.append(feedback)
    repository.list_feedbacks_for_session = lambda owner_id, session_id: tuple(
        item for item in repository.feedbacks if item.owner_id == owner_id and item.session_id == session_id
    )

    result = use_cases.create_feedback_task(
        CreatePolishFeedbackTaskCommand(
            owner_id=OWNER_ID,
            actor_id=ACTOR_ID,
            session_id=SESSION_ID,
            answer_id=answer.answer_id,
        )
    )

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.SUCCEEDED
    assert len(feedback_generation_service.contexts) == 1
    assert feedback_generation_service.contexts[0].answer_id == answer.answer_id
    assert len(repository.feedbacks) == 1
    feedback_payload = json.loads(repository.feedbacks[0].feedback_summary)
    assert feedback_payload["status"] == "generated"
    assert feedback_payload["feedback_text"] == "真实反馈来自替换后的生成服务。"
    assert feedback_payload["score_result"]["score_value"] == 88
    assert feedback_payload["feedback_metadata"]["llm_called"] is True
    assert feedback_payload["feedback_metadata"]["generated"] is True
    assert feedback_payload["feedback_metadata"]["task_type"] == "polish_feedback_generation"

    detail = use_cases.get_session(GetPolishSessionQuery(owner_id=OWNER_ID, session_id=SESSION_ID))

    assert detail.is_success
    detail_answer = detail.value.turns[0].answers[0]
    assert detail_answer.feedback_payload["status"] == "generated"
    assert detail_answer.feedback_payload["feedback_metadata"]["generated"] is True


def _question_output_blueprint() -> QuestionBlueprint:
    return QuestionBlueprint(
        question_kind="project_deep_dive",
        claim_mode="evidence_grounded",
        progress_node_ref=NODE_REF,
        node_title="支付链路一致性",
        expected_capability="说明支付链路一致性与失败补偿。",
        primary_evidence_ref="resume_project_001",
        primary_evidence_text="使用 Redis、RocketMQ 和本地事务保障一致性。",
        evidence_refs=("resume_project_001",),
    )


def _legacy_flat_question_payload() -> dict[str, Any]:
    return {
        "question_text": "请说明支付链路中幂等、失败补偿和上线验证指标是如何设计的。",
        "question_kind": "project_deep_dive",
        "focus_dimension": "project_deep_dive",
        "difficulty": "medium",
        "skill_dimension": "支付可靠性",
        "expected_signal": "能说明幂等、补偿和验证指标。",
        "follow_ups": ["失败补偿如何触发？", "如何证明方案有效？"],
        "scoring_rubric": [
            {"dimension": "grounding", "signals": ["引用证据", "不编造经历"]},
            {"dimension": "tradeoff", "signals": ["说明取舍", "说明边界"]},
        ],
        "missing_context": [],
        "evidence_refs": ["resume_project_001"],
        "confidence": "high",
        "clarification_needed": False,
    }


def _next_question_agent_output_payload() -> dict[str, Any]:
    return {
        "schema_id": NEXT_QUESTION_AGENT_SCHEMA_ID,
        "prompt_version": NEXT_QUESTION_AGENT_PROMPT_VERSION,
        "clarification_needed": False,
        "confidence": "medium",
        "missing_context": [],
        "decision": {
            "turn_intent": "project_implementation_deep_dive",
            "intent_reason": "根据当前证据选择实现追问。",
            "evidence_support_level": "direct_project_evidence",
            "evidence_support_reason": "简历项目直接支撑支付链路追问。",
            "main_question_style": "ask_how_implemented",
            "allowed_extension_depth": "main_question_allowed",
            "primary_evidence_refs": ["resume_project_001"],
            "secondary_evidence_refs": [],
            "unsupported_capability_claims": [],
            "risk_flags": [],
            "avoid_patterns_applied": ["unsupported_capability_as_fact"],
        },
        "question": {
            "question_text": "你在支付链路里如何实现幂等、失败补偿和上线验证？",
            "question_kind": "implementation_deep_dive",
            "difficulty": "medium",
            "skill_dimension": "支付链路一致性",
            "expected_signal": "能说明真实实现链路、异常处理和验证效果。",
            "follow_ups": ["失败补偿如何触发？", "如何证明方案有效？"],
            "scoring_rubric": [
                {"dimension": "grounding", "signals": ["引用证据", "不编造经历"]},
                {"dimension": "reasoning", "signals": ["说明链路", "说明取舍"]},
            ],
        },
        "persistence_hints": {
            "should_persist_decision": True,
            "should_update_progress": True,
            "next_focus_candidates": [NODE_REF],
            "trace_tags": ["next_question_agent", "direct_project_evidence"],
        },
        "evidence_refs": ["resume_project_001"],
        "post_check_hints": {
            "claims_to_verify": [],
            "unsupported_terms_in_question": [],
            "question_style_check": "pass",
            "evidence_grounding_check": "pass",
        },
    }


def test_agent_prompt_bundle_to_prompt_asset_dict_outputs_standard_prompt_asset() -> None:
    assert hasattr(agent_io, "AgentPromptBundle")
    bundle = agent_io.AgentPromptBundle(
        task_type="polish_question_generation",
        prompt_version="polish_next_question_agent_prompt.v1",
        schema_id="polish_next_question_agent_decision_v1",
        schema_version="v1",
        prompt="只输出 JSON。",
        input_data={"selected_node_title": "支付链路一致性"},
        output_schema={"type": "object"},
        system_role="你是一名技术面试题设计专家。",
        developer_constraints=("不得编造 evidence_refs 未支撑的事实。",),
        user_task="生成一个面试打磨问题。",
        input_contract={"required_context_fields": ["selected_node_title"]},
        extra_fields={
            "asset_id": "polish_question_generation",
            "policy_version": "polish_question_generation_policy.v1",
            "task_type": "should_not_override_standard_field",
        },
    )

    prompt_asset = bundle.to_prompt_asset_dict()

    assert prompt_asset["task_type"] == "polish_question_generation"
    assert prompt_asset["prompt_version"] == "polish_next_question_agent_prompt.v1"
    assert prompt_asset["schema_id"] == "polish_next_question_agent_decision_v1"
    assert prompt_asset["schema_version"] == "v1"
    assert prompt_asset["prompt"] == "只输出 JSON。"
    assert prompt_asset["input_data"] == {"selected_node_title": "支付链路一致性"}
    assert prompt_asset["output_schema"] == {"type": "object"}
    assert prompt_asset["system_role"] == "你是一名技术面试题设计专家。"
    assert prompt_asset["developer_constraints"] == ["不得编造 evidence_refs 未支撑的事实。"]
    assert prompt_asset["user_task"] == "生成一个面试打磨问题。"
    assert prompt_asset["input_contract"] == {"required_context_fields": ["selected_node_title"]}
    assert prompt_asset["asset_id"] == "polish_question_generation"
    assert prompt_asset["policy_version"] == "polish_question_generation_policy.v1"


def test_agent_prompt_bundle_omits_empty_optional_fields_and_unknown_extra_fields() -> None:
    assert hasattr(agent_io, "AgentPromptBundle")
    bundle = agent_io.AgentPromptBundle(
        task_type="polish_question_generation",
        prompt_version="polish_next_question_agent_prompt.v1",
        schema_id="polish_next_question_agent_decision_v1",
        schema_version="v1",
        prompt="只输出 JSON。",
        extra_fields={
            "asset_id": "polish_question_generation",
            "provider_payload": {"raw": "must_not_be_added"},
        },
    )

    prompt_asset = bundle.to_prompt_asset_dict()

    assert set(prompt_asset) == {
        "asset_id",
        "task_type",
        "prompt_version",
        "schema_id",
        "schema_version",
        "prompt",
        "input_data",
        "output_schema",
    }
    assert "provider_payload" not in prompt_asset
    assert "system_role" not in prompt_asset
    assert "developer_constraints" not in prompt_asset
    assert "user_task" not in prompt_asset
    assert "input_contract" not in prompt_asset


def test_question_payload_envelope_keeps_nested_next_question_agent_output_shape() -> None:
    from app.application.llm.agent_io import AgentOutputEnvelope
    from app.application.polish.question_generation_service import _question_payload_envelope

    blueprint = _question_output_blueprint()
    raw_payload = _next_question_agent_output_payload()

    envelope = _question_payload_envelope(raw_payload, blueprint=blueprint)
    parsed_payload, parse_errors = _parse_llm_question_payload(raw_payload, blueprint=blueprint)

    assert isinstance(envelope, AgentOutputEnvelope)
    assert envelope.succeeded is True
    assert envelope.task_type == "polish_question_generation"
    assert envelope.schema_id == NEXT_QUESTION_AGENT_SCHEMA_ID
    assert envelope.schema_version == NEXT_QUESTION_AGENT_SCHEMA_VERSION
    assert envelope.prompt_version == NEXT_QUESTION_AGENT_PROMPT_VERSION
    assert envelope.evidence_refs == ("resume_project_001",)
    assert parse_errors == ()
    assert parsed_payload == envelope.payload
    assert parsed_payload == {
        "question_text": "你在支付链路里如何实现幂等、失败补偿和上线验证？",
        "question_kind": "implementation_deep_dive",
        "focus_dimension": "implementation_deep_dive",
        "difficulty": "medium",
        "skill_dimension": "支付链路一致性",
        "expected_signal": "能说明真实实现链路、异常处理和验证效果。",
        "follow_ups": ["失败补偿如何触发？", "如何证明方案有效？"],
        "scoring_rubric": [
            {"dimension": "grounding", "signals": ["引用证据", "不编造经历"]},
            {"dimension": "reasoning", "signals": ["说明链路", "说明取舍"]},
        ],
        "missing_context": [],
        "evidence_refs": ["resume_project_001"],
        "confidence": "medium",
        "clarification_needed": False,
        "next_question_agent": {
            "schema_id": NEXT_QUESTION_AGENT_SCHEMA_ID,
            "schema_version": NEXT_QUESTION_AGENT_SCHEMA_VERSION,
            "prompt_version": NEXT_QUESTION_AGENT_PROMPT_VERSION,
            "clarification_needed": False,
            "confidence": "medium",
            "missing_context": [],
            "decision": {
                "turn_intent": "project_implementation_deep_dive",
                "intent_reason": "根据当前证据选择实现追问。",
                "evidence_support_level": "direct_project_evidence",
                "evidence_support_reason": "简历项目直接支撑支付链路追问。",
                "main_question_style": "ask_how_implemented",
                "allowed_extension_depth": "main_question_allowed",
                "primary_evidence_refs": ["resume_project_001"],
                "secondary_evidence_refs": [],
                "unsupported_capability_claims": [],
                "risk_flags": [],
                "avoid_patterns_applied": ["unsupported_capability_as_fact"],
            },
            "question": {
                "question_text": "你在支付链路里如何实现幂等、失败补偿和上线验证？",
                "question_kind": "implementation_deep_dive",
                "difficulty": "medium",
                "skill_dimension": "支付链路一致性",
                "expected_signal": "能说明真实实现链路、异常处理和验证效果。",
                "follow_ups": ["失败补偿如何触发？", "如何证明方案有效？"],
                "scoring_rubric": [
                    {"dimension": "grounding", "signals": ["引用证据", "不编造经历"]},
                    {"dimension": "reasoning", "signals": ["说明链路", "说明取舍"]},
                ],
            },
            "persistence_hints": {
                "should_persist_decision": True,
                "should_update_progress": True,
                "next_focus_candidates": [NODE_REF],
                "trace_tags": ["next_question_agent", "direct_project_evidence"],
            },
            "evidence_refs": ["resume_project_001"],
            "post_check_hints": {
                "claims_to_verify": [],
                "unsupported_terms_in_question": [],
                "question_style_check": "pass",
                "evidence_grounding_check": "pass",
            },
        },
    }


def test_question_payload_envelope_keeps_legacy_flat_payload_shape() -> None:
    from app.application.llm.agent_io import AgentOutputEnvelope
    from app.application.polish.question_generation_service import _question_payload_envelope

    blueprint = _question_output_blueprint()
    raw_payload = _legacy_flat_question_payload()

    envelope = _question_payload_envelope(raw_payload, blueprint=blueprint)
    parsed_payload, parse_errors = _parse_llm_question_payload(raw_payload, blueprint=blueprint)

    assert isinstance(envelope, AgentOutputEnvelope)
    assert envelope.succeeded is True
    assert envelope.task_type == "polish_question_generation"
    assert envelope.evidence_refs == ("resume_project_001",)
    assert parse_errors == ()
    assert parsed_payload == envelope.payload
    assert parsed_payload == raw_payload
    assert set(parsed_payload) == {
        "question_text",
        "question_kind",
        "focus_dimension",
        "difficulty",
        "skill_dimension",
        "expected_signal",
        "follow_ups",
        "scoring_rubric",
        "missing_context",
        "evidence_refs",
        "confidence",
        "clarification_needed",
    }


def test_question_payload_envelope_keeps_invalid_payload_error_codes() -> None:
    from app.application.polish.question_generation_service import _question_payload_envelope

    blueprint = _question_output_blueprint()
    raw_payload = {
        "question_text": "",
        "difficulty": "extreme",
        "confidence": "certain",
        "clarification_needed": "no",
    }

    envelope = _question_payload_envelope(raw_payload, blueprint=blueprint)
    parsed_payload, parse_errors = _parse_llm_question_payload(raw_payload, blueprint=blueprint)

    expected_errors = (
        "llm_question_text_required",
        "llm_difficulty_invalid",
        "llm_expected_signal_required",
        "llm_follow_ups_required",
        "llm_scoring_rubric_required",
        "llm_confidence_invalid",
        "llm_clarification_needed_required",
        "llm_evidence_refs_required",
    )
    assert envelope.succeeded is False
    assert envelope.validation_errors == expected_errors
    assert parsed_payload is None
    assert parse_errors == expected_errors


def test_build_question_prompt_asset_top_level_shape_stays_stable() -> None:
    blueprint = QuestionBlueprint(
        question_kind="project_deep_dive",
        claim_mode="evidence_grounded",
        progress_node_ref=NODE_REF,
        node_title="支付可靠性追问",
        expected_capability="验证候选人能否围绕支付链路说明设计、取舍和复盘。",
        primary_evidence_ref="resume_project_001",
        primary_evidence_text="支付链路需要覆盖幂等、失败补偿和上线验证指标。",
        evidence_refs=("resume_project_001",),
    )
    scope = EvidenceScope(
        progress_node_ref=NODE_REF,
        node_title="支付可靠性追问",
        expected_capability="验证候选人能否围绕支付可靠性说明设计、取舍和复盘。",
        primary_evidence_ref="resume_project_001",
        primary_evidence_text="支付链路需要覆盖幂等、失败补偿和上线验证指标。",
        primary_source_type="resume_project",
        evidence_refs=("resume_project_001",),
    )

    prompt_asset = build_question_prompt_asset(blueprint, scope)

    assert set(prompt_asset) == QUESTION_PROMPT_ASSET_TOP_LEVEL_KEYS


def test_agent_focus_target_from_progress_node_uses_title_and_safe_metadata() -> None:
    focus_target = _focus_target_from_progress_node(
        {
            "progress_node_ref": NODE_REF,
            "title": "支付链路一致性",
            "expected_capability": "能说明幂等、失败补偿和上线验证。",
            "missing_points": ["缺少故障恢复指标。", "", None],
            "category": "backend",
            "node_type": "leaf",
            "exam_point": "支付可靠性",
            "confidence_level": "medium",
            "basis_type": "mixed",
            "evidence_refs": ["resume_project_001"],
            "full_resume": "不应进入 focus metadata",
        },
        requested_ref="fallback_node_ref",
    )

    assert isinstance(focus_target, AgentFocusTarget)
    assert focus_target.ref == NODE_REF
    assert focus_target.title == "支付链路一致性"
    assert focus_target.expected_capability == "能说明幂等、失败补偿和上线验证。"
    assert focus_target.missing_points == ("缺少故障恢复指标。",)
    assert focus_target.metadata == {
        "category": "backend",
        "node_type": "leaf",
        "exam_point": "支付可靠性",
        "confidence_level": "medium",
        "basis_type": "mixed",
    }
    assert focus_target.to_prompt_dict() == {
        "ref": NODE_REF,
        "title": "支付链路一致性",
        "expected_capability": "能说明幂等、失败补偿和上线验证。",
        "missing_points": ["缺少故障恢复指标。"],
        "metadata": focus_target.metadata,
    }


def test_agent_focus_target_title_priority_keeps_display_title_before_title_and_exam_point() -> None:
    node = {
        "progress_node_ref": NODE_REF,
        "display_title": "展示标题优先",
        "title": "普通标题",
        "exam_point": "考点标题",
        "description": "描述兜底能力",
    }

    focus_target = _focus_target_from_progress_node(node, requested_ref="fallback_node_ref")

    assert focus_target.title == "展示标题优先"
    assert focus_target.expected_capability == "描述兜底能力"
    assert _focus_target_from_progress_node(
        {"progress_node_ref": NODE_REF, "title": "普通标题", "exam_point": "考点标题"},
        requested_ref="fallback_node_ref",
    ).title == "普通标题"
    assert _focus_target_from_progress_node(
        {"progress_node_ref": NODE_REF, "exam_point": "考点标题"},
        requested_ref="fallback_node_ref",
    ).title == "考点标题"


def test_phase1_question_service_blocks_inventory_evidence_from_log_vector_pipeline() -> None:
    service = QuestionGenerationService()
    session, context, plan, state = _question_generation_inputs(
        primary_text="库存扣减链路使用分布式锁、事务消息和本地事务保证一致性。",
        node_title="库存一致性与异常补偿",
        expected_capability="能说明库存扣减的一致性、异常补偿和验证指标。",
    )

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert result.succeeded
    assert result.draft is not None
    question_text = result.draft.question_text
    for job_gap_only in ("1GB 日志", "上传入口", "解析", "切块", "向量化", "入库", "15 秒到 3 秒"):
        assert job_gap_only not in question_text
    assert result.blueprint is not None
    assert result.blueprint.primary_evidence_ref in result.draft.evidence_refs


def test_phase1_question_service_keeps_job_gap_probe_from_claiming_candidate_experience() -> None:
    service = QuestionGenerationService()
    session, context, plan, state = _question_generation_inputs(
        primary_text="岗位要求候选人具备支付链路幂等、失败补偿和上线验证经验。",
        primary_source_type="job_requirement",
        node_title="岗位匹配缺口与技术深度防御",
        expected_capability="验证候选人是否能补齐岗位要求中的支付可靠性缺口。",
    )

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert result.succeeded
    assert result.blueprint is not None
    assert result.blueprint.claim_mode == "job_gap_probe"
    assert result.draft is not None
    for forbidden in ("你负责过", "你实现过", "你主导过", "你参与过"):
        assert forbidden not in result.draft.question_text


def test_phase1_question_service_clarification_question_requires_four_materials() -> None:
    service = QuestionGenerationService()
    session, _context, plan, state = _question_generation_inputs(primary_text="")
    context = {"content_digest": "ctx_phase1_empty", "turns": []}

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert result.succeeded
    assert result.blueprint is not None
    assert result.blueprint.claim_mode == "clarification_needed"
    assert result.draft is not None
    for required in ("业务入口", "职责边界", "失败案例", "验证指标"):
        assert required in result.draft.question_text


def test_phase1_question_metadata_records_prompt_asset_digest_without_prompt_body() -> None:
    service = QuestionGenerationService()
    session, context, plan, state = _question_generation_inputs(
        primary_text="支付链路需要覆盖幂等、失败补偿和上线验证指标。"
    )

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert result.succeeded
    assert result.draft is not None
    metadata = result.draft.question_metadata
    assert metadata["prompt_asset_version"] == NEXT_QUESTION_AGENT_PROMPT_VERSION
    assert metadata["prompt_schema_id"] == NEXT_QUESTION_AGENT_SCHEMA_ID
    assert metadata["prompt_input_digest"].startswith("sha256:")
    assert metadata["prompt_evidence_refs"] == list(result.draft.evidence_refs)
    for forbidden_key in (
        "surface_prompt",
        "input_data",
        "system_role",
        "developer_constraints",
        "user_task",
        "output_schema",
        "primary_evidence_text",
    ):
        assert forbidden_key not in metadata
    assert "支付链路需要覆盖幂等" not in json.dumps(metadata, ensure_ascii=False)


def test_question_service_sends_structured_prompt_asset_to_llm_transport() -> None:
    transport = _RecordingQuestionTransport()
    service = QuestionGenerationService(llm_transport=transport)
    session, context, plan, state = _question_generation_inputs(
        primary_text="支付链路需要覆盖幂等、失败补偿和上线验证指标。",
        node_title="支付可靠性追问",
        expected_capability="验证候选人能否围绕支付链路说明设计、取舍和复盘。",
    )

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert result.succeeded
    assert result.draft is not None
    assert result.draft.question_text == _RecordingQuestionTransport.QUESTION_TEXT
    assert len(transport.requests) == 1
    request = transport.requests[0]
    assert request.task_type == "polish_question_generation"
    assert request.contract_ids == ("P-POLISH-002", "P-SHARED-001", "P-SHARED-003")
    assert request.prompt_version == NEXT_QUESTION_AGENT_PROMPT_VERSION
    assert request.schema_id == NEXT_QUESTION_AGENT_SCHEMA_ID
    provider_request = request.evidence_bundle
    assert set(provider_request) == QUESTION_PROVIDER_REQUEST_TOP_LEVEL_KEYS
    assert provider_request["task_type"] == "polish_question_generation"
    assert provider_request["prompt_version"] == NEXT_QUESTION_AGENT_PROMPT_VERSION
    assert provider_request["schema_id"] == NEXT_QUESTION_AGENT_SCHEMA_ID
    assert provider_request["schema_version"] == NEXT_QUESTION_AGENT_SCHEMA_VERSION
    assert provider_request["progress_node"]["title"] == "支付可靠性追问"
    assert provider_request["source_support_level"] == "direct_project_evidence"
    canonical_evidence = provider_request["canonical_evidence"]
    assert canonical_evidence["evidence_refs"]
    assert canonical_evidence["evidence_summaries"][0]["ref"] in canonical_evidence["evidence_refs"]
    assert provider_request["expected_output_contract"]["generation_policy"] == {
        "question_kind": "tradeoff_design",
        "claim_mode": "evidence_grounded",
        "source_support_level": "direct_project_evidence",
    }
    assert provider_request["safety_rules_summary"]["input_is_untrusted"] is True
    serialized_provider_request = json.dumps(provider_request, ensure_ascii=False, sort_keys=True)
    for forbidden in (
        "raw_prompt",
        "system_prompt",
        "developer_prompt",
        "raw_completion",
        "provider_payload",
        "full_resume",
        "full_jd",
        "full_prompt_asset",
        "full_asset_body",
        "token",
        "secret",
        "cookie",
    ):
        assert forbidden not in serialized_provider_request
    assert "资深技术面试题设计专家" not in serialized_provider_request
    metadata = result.draft.question_metadata
    assert metadata["llm_generation_mode"] == "provider_structured_json"
    assert metadata["fallback_visible"] is False
    assert metadata["llm_trace_refs"] == ["trace_next_question_agent_prompt_v1"]
    assert metadata["llm_difficulty"] == "medium"
    assert metadata["llm_skill_dimension"] == "支付可靠性"
    assert metadata["llm_expected_signal"] == "能说明幂等、补偿、验证指标和复盘证据。"
    assert metadata["llm_confidence"] == "high"
    assert metadata["llm_missing_context"] == []
    assert metadata["llm_clarification_needed"] is False
    for envelope_key in (
        "agent_output_envelope",
        "output_envelope",
        "validation_errors",
        "provider_payload",
        "raw_completion",
    ):
        if envelope_key == "validation_errors":
            assert metadata[envelope_key] == []
        else:
            assert envelope_key not in metadata
    assert metadata["grounding_status"] == "passed"
    assert metadata["grounding_validation_errors"] == []
    assert metadata["manual_review_required"] is False

def test_question_provider_request_redacts_sensitive_values_from_compact_evidence() -> None:
    transport = _RecordingQuestionTransport()
    service = QuestionGenerationService(llm_transport=transport)
    session, context, plan, state = _question_generation_inputs(
        primary_text=(
            "支付链路需要覆盖幂等、失败补偿和上线验证指标 api_key=sk-test-secret "
            "token=raw-token cookie=session-secret secret=plain-secret。"
        ),
        node_title="支付可靠性追问",
        expected_capability="验证候选人能否围绕支付链路说明设计、取舍和复盘。",
    )

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert result.succeeded
    provider_request = transport.requests[0].evidence_bundle
    serialized_provider_request = json.dumps(provider_request, ensure_ascii=False, sort_keys=True)
    for forbidden in (
        "api_key=sk-test-secret",
        "token=raw-token",
        "cookie=session-secret",
        "secret=plain-secret",
        "sk-test-secret",
        "raw-token",
        "session-secret",
        "plain-secret",
    ):
        assert forbidden not in serialized_provider_request
    assert "[redacted]" in serialized_provider_request



def test_question_prompt_anchor_contract_rejects_legacy_skill_dimension_source() -> None:
    legacy_prompt_asset = {
        "input_contract": {
            "field_sources": {
                "skill_dimension": "progress node expected_capability",
            }
        },
        "input_data": {
            "progress_node": {
                "ref": NODE_REF,
                "title": "分布式锁与事务消息最终一致性设计",
                "expected_capability": (
                    "高阶深度目标：考察候选人面对高并发库存扣减时的方案选型、异常处理与数据恢复能力"
                ),
            },
            "skill_dimension": "高阶深度目标：考察候选人面对高并发库存扣减时的方案选型、异常处理与数据恢复能力",
        },
    }

    errors = validate_question_prompt_anchor_contract(legacy_prompt_asset)

    assert "prompt_contract_selected_node_title_missing" in errors
    assert "prompt_contract_anchor_policy_missing" in errors
    assert "prompt_contract_skill_dimension_not_title" in errors
    assert "prompt_contract_field_source_legacy_expected_capability" in errors
    assert "prompt_contract_skill_dimension_source_invalid" in errors


def test_question_service_blocks_legacy_prompt_contract_before_llm_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def legacy_prompt_asset(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            "prompt_version": "legacy",
            "schema_id": "legacy",
            "task_type": "polish_question_generation",
            "input_contract": {
                "field_sources": {
                    "skill_dimension": "progress node expected_capability",
                }
            },
            "input_data": {
                "progress_node": {
                    "ref": NODE_REF,
                    "title": "分布式锁与事务消息最终一致性设计",
                    "expected_capability": (
                        "高阶深度目标：考察候选人面对高并发库存扣减时的方案选型、异常处理与数据恢复能力"
                    ),
                },
                "skill_dimension": (
                    "高阶深度目标：考察候选人面对高并发库存扣减时的方案选型、异常处理与数据恢复能力"
                ),
                "evidence_refs": ["resume_project_001"],
            },
        }

    transport = _RecordingQuestionTransport()
    monkeypatch.setattr(
        "app.application.polish.question_generation_service.build_question_prompt_asset",
        legacy_prompt_asset,
    )
    service = QuestionGenerationService(llm_transport=transport)
    session, context, plan, state = _question_generation_inputs(
        primary_text="支付链路需要覆盖幂等、失败补偿和上线验证指标。",
        node_title="分布式锁与事务消息最终一致性设计",
        expected_capability=(
            "高阶深度目标：考察候选人面对高并发库存扣减时的方案选型、异常处理与数据恢复能力"
        ),
    )

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert not result.succeeded
    assert result.draft is None
    assert transport.requests == []
    assert "prompt_contract_anchor_policy_missing" in result.validation_errors
    assert "prompt_contract_field_source_legacy_expected_capability" in result.validation_errors


def test_question_service_blocks_grounding_failure_without_persisting_question() -> None:
    transport = _SoftGroundingWarningTransport()
    service = QuestionGenerationService(llm_transport=transport)
    session, context, plan, state = _question_generation_inputs(
        primary_text="支付链路需要覆盖幂等、失败补偿和上线验证指标。"
    )

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert not result.succeeded
    assert result.draft is None
    assert len(transport.requests) == 1
    assert result.grounding_result.blocking_errors
    assert "source_contamination_or_ungrounded_question" in result.validation_errors
    assert "grounding_blocking_bypassed" not in json.dumps(
        transport.requests[0].evidence_bundle,
        ensure_ascii=False,
    )

def test_question_service_anchors_skill_dimension_to_progress_node_title_not_expected_capability() -> None:
    transport = _RecordingQuestionTransport()
    service = QuestionGenerationService(llm_transport=transport)
    session, context, plan, state = _question_generation_inputs(
        primary_text="候选人做过消息驱动的订单状态同步，需要继续追问一致性边界。",
        node_title="分布式锁与事务消息最终一致性设计",
        expected_capability=(
            "高阶深度目标：考察候选人面对高并发库存扣减时的方案选型、异常处理与数据恢复能力"
        ),
    )

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert result.succeeded
    assert len(transport.requests) == 1
    provider_request = transport.requests[0].evidence_bundle
    input_data = _question_request_input_data(transport.requests[0])
    assert set(provider_request) == QUESTION_PROVIDER_REQUEST_TOP_LEVEL_KEYS
    assert "input_data" not in provider_request
    assert "input_contract" not in provider_request
    assert input_data["selected_node_title"] == "分布式锁与事务消息最终一致性设计"
    assert input_data["progress_node"]["title"] == "分布式锁与事务消息最终一致性设计"
    assert input_data["skill_dimension"] == "分布式锁与事务消息最终一致性设计"
    assert input_data["progress_node"]["expected_capability"] == (
        "高阶深度目标：考察候选人面对高并发库存扣减时的方案选型、异常处理与数据恢复能力"
    )
    assert provider_request["expected_output_contract"]["generation_policy"]["source_support_level"] in {
        "direct_project_evidence",
        "adjacent_project_evidence",
    }


def test_question_provider_request_keeps_weak_resume_evidence_compact_and_hypothetical() -> None:
    transport = _RecordingQuestionTransport()
    service = QuestionGenerationService(llm_transport=transport)
    session, context, plan, state = _distributed_lock_weak_evidence_inputs()

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert result.succeeded
    assert len(transport.requests) == 1
    provider_request = transport.requests[0].evidence_bundle
    assert set(provider_request) == QUESTION_PROVIDER_REQUEST_TOP_LEVEL_KEYS
    assert provider_request["source_support_level"] == "adjacent_project_evidence"
    assert provider_request["safety_rules_summary"]["adjacent_or_gap_requires_hypothetical_wording"] is True
    assert provider_request["expected_output_contract"]["generation_policy"] == {
        "question_kind": "failure_recovery_deep_dive",
        "claim_mode": "evidence_grounded",
        "source_support_level": "adjacent_project_evidence",
    }
    for forbidden_key in (
        "prompt",
        "system_role",
        "developer_constraints",
        "user_task",
        "input_data",
        "output_schema",
        "refusal_and_low_confidence_policy",
        "examples",
    ):
        assert forbidden_key not in provider_request

    evidence_summaries = provider_request["canonical_evidence"]["evidence_summaries"]
    assert any(
        item["ref"] == "resume_project_004"
        and "大文件异步处理管道" in item["excerpt"]
        and "Redis" in item["excerpt"]
        and "RocketMQ" in item["excerpt"]
        for item in evidence_summaries
    )
    serialized_provider_request = json.dumps(provider_request, ensure_ascii=False, sort_keys=True)
    for forbidden in (
        "资深技术面试题设计专家",
        "raw_prompt",
        "system_prompt",
        "developer_prompt",
        "provider_payload",
        "full_resume",
        "full_jd",
    ):
        assert forbidden not in serialized_provider_request

def test_question_provider_request_limits_clarification_to_compact_context() -> None:
    transport = _RecordingQuestionTransport()
    service = QuestionGenerationService(llm_transport=transport)
    session, context, plan, state = _distributed_lock_weak_evidence_inputs()

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert result.succeeded
    provider_request = transport.requests[0].evidence_bundle
    assert set(provider_request) == QUESTION_PROVIDER_REQUEST_TOP_LEVEL_KEYS
    assert provider_request["source_support_level"] == "adjacent_project_evidence"
    assert provider_request["history_summary"]["generation_mode"] == "new_question"
    assert "job" in provider_request["canonical_evidence"]["missing_context"]
    assert "resume" not in provider_request["canonical_evidence"]["missing_context"]
    serialized_provider_request = json.dumps(provider_request, ensure_ascii=False, sort_keys=True)
    assert "缺失岗位、简历、能力维度或证据时，必须在 missing_context 中标记，并生成澄清题" not in serialized_provider_request
    assert "低证据时输出 clarification_needed" not in serialized_provider_request
    assert "resume 和 evidence_refs 都不可用" not in serialized_provider_request
    assert "已有简历 evidence" not in serialized_provider_request

def test_question_service_rewrites_project_clarification_to_hypothetical_extension() -> None:
    transport = _ProjectClarificationQuestionTransport()
    service = QuestionGenerationService(llm_transport=transport)
    session, context, plan, state = _distributed_lock_weak_evidence_inputs()

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert result.succeeded
    assert result.draft is not None
    question_text = result.draft.question_text
    for forbidden in ("补充一个", "请分享一个您亲自负责", "请先补充", "未涉及分布式锁与事务消息"):
        assert forbidden not in question_text
    for fabricated_claim in ("你在项目中实现了分布式锁", "你主导过事务消息", "你已经落地了最终一致性"):
        assert fabricated_claim not in question_text
    assert "大文件异步处理管道" in question_text
    assert "Redis" in question_text or "RocketMQ" in question_text
    assert "如果" in question_text
    assert "你会如何" in question_text
    assert "关键链路" in question_text
    assert "效果验证" in question_text
    for job_gap_only_main_fact in ("分布式锁", "事务消息", "半消息回查", "状态回查"):
        assert job_gap_only_main_fact not in question_text

    metadata = result.draft.question_metadata
    assert metadata["question_text_rewritten_from_clarification"] is True
    assert metadata["question_text_rewrite_reason"] == "project_clarification_to_hypothetical_extension"
    assert metadata["question_text_rewrite_source_ref"] == "resume_project_004"
    assert metadata["manual_review_required"] is True
    assert metadata["llm_clarification_needed"] is True


def test_next_question_agent_direct_project_evidence_decision_can_anchor_main_question() -> None:
    transport = _NextQuestionDecisionTransport(
        turn_intent="project_implementation_deep_dive",
        evidence_support_level="direct_project_evidence",
        main_question_style="ask_how_implemented",
        allowed_extension_depth="main_question_allowed",
        question_kind="implementation_deep_dive",
        question_text="你在库存扣减链路中是怎么实现分布式锁和事务消息一致性的？请说明关键链路、失败处理和验证方式。",
        unsupported_capability_claims=(),
    )
    service = QuestionGenerationService(llm_transport=transport)
    session, context, plan, state = _question_generation_inputs(
        primary_text="库存扣减链路使用分布式锁、RocketMQ 事务消息和本地事务保证一致性。",
        node_title="分布式锁与事务消息最终一致性设计",
        expected_capability="能说明分布式锁、事务消息、最终一致性和异常恢复。",
    )

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert result.succeeded
    assert result.draft is not None
    metadata = result.draft.question_metadata
    decision = metadata["next_question_decision"]
    assert decision["evidence_support_level"] == "direct_project_evidence"
    assert decision["main_question_style"] == "ask_how_implemented"
    assert decision["unsupported_capability_claims"] == []
    assert "分布式锁" in result.draft.question_text
    assert metadata["next_question_question"]["question_kind"] == "implementation_deep_dive"

def test_next_question_agent_blocks_direct_fact_claim_conflicting_with_canonical_assets() -> None:
    transport = _NextQuestionDecisionTransport(
        turn_intent="project_implementation_deep_dive",
        evidence_support_level="direct_project_evidence",
        main_question_style="ask_how_implemented",
        allowed_extension_depth="main_question_allowed",
        question_kind="implementation_deep_dive",
        question_text="你实现了 FastAPI 工作流中的 Redis 分布式锁后，故障恢复怎么验证？",
        unsupported_capability_claims=("Redis 分布式锁",),
    )
    service = QuestionGenerationService(llm_transport=transport)
    session, context, plan, state = _question_generation_inputs(
        primary_text="Backend workflow automation uses FastAPI APIs and PostgreSQL persistence.",
        node_title="FastAPI PostgreSQL workflow reliability",
        expected_capability="Explain FastAPI and PostgreSQL workflow reliability decisions.",
    )
    context["canonical_project_assets"] = {
        "available": True,
        "selection_policy": "rule_based_keyword_overlap_v1",
        "items": [
            {
                "asset_id": "asset_backend_workflow",
                "status": "asset_confirmed",
                "asset_type": "project_story",
                "title": "Backend workflow automation",
                "summary": "Candidate built FastAPI APIs with PostgreSQL persistence.",
                "content_excerpt": "Owns FastAPI APIs, PostgreSQL persistence, retries, and observability.",
                "source_refs": [],
                "evidence_refs": [],
            }
        ],
    }
    context["canonical_evidence_pack"] = {
        "source_support_level": "direct_project_evidence",
        "context_digest": "digest_backend_workflow_assets",
    }

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert not result.succeeded
    assert result.draft is None
    assert "unsupported_technology_stack_as_completed_experience" in result.validation_errors
    assert "question_conflicts_with_canonical_assets" in result.validation_errors


def test_next_question_agent_ignores_archived_assets_as_canonical_conflict_source() -> None:
    transport = _NextQuestionDecisionTransport(
        turn_intent="project_implementation_deep_dive",
        evidence_support_level="direct_project_evidence",
        main_question_style="ask_how_implemented",
        allowed_extension_depth="main_question_allowed",
        question_kind="implementation_deep_dive",
        question_text="你实现了 FastAPI 工作流中的 Redis 分布式锁后，故障恢复怎么验证？",
        unsupported_capability_claims=("Redis 分布式锁",),
    )
    service = QuestionGenerationService(llm_transport=transport)
    session, context, plan, state = _question_generation_inputs(
        primary_text="Backend workflow automation uses FastAPI APIs and PostgreSQL persistence.",
        node_title="FastAPI PostgreSQL workflow reliability",
        expected_capability="Explain FastAPI and PostgreSQL workflow reliability decisions.",
    )
    context["canonical_project_assets"] = {
        "available": True,
        "selection_policy": "rule_based_keyword_overlap_v1",
        "items": [
            {
                "asset_id": "asset_backend_workflow",
                "status": "asset_archived",
                "asset_type": "project_story",
                "title": "Backend workflow automation",
                "summary": "Candidate built FastAPI APIs with PostgreSQL persistence.",
                "content_excerpt": "Owns FastAPI APIs, PostgreSQL persistence, retries, and observability.",
                "source_refs": [],
                "evidence_refs": [],
            }
        ],
    }
    context["canonical_evidence_pack"] = {
        "source_support_level": "direct_project_evidence",
        "context_digest": "digest_backend_workflow_assets",
    }

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert not result.succeeded
    assert result.draft is None
    assert "unsupported_technology_stack_as_completed_experience" in result.validation_errors
    assert "question_conflicts_with_canonical_assets" not in result.validation_errors



def test_next_question_agent_adjacent_project_evidence_uses_hypothetical_extension() -> None:
    transport = _NextQuestionDecisionTransport(
        turn_intent="extension_design_followup",
        evidence_support_level="adjacent_project_evidence",
        main_question_style="ask_hypothetical_design",
        allowed_extension_depth="main_question_allowed",
        question_kind="extension_design_followup",
        question_text=(
            "如果要在你做的大文件异步处理管道基础上引入分布式锁和事务消息，"
            "你会如何设计状态流转、异常补偿和验证指标？"
        ),
        unsupported_capability_claims=("分布式锁", "RocketMQ 事务消息", "半消息回查", "最终一致性状态机"),
        follow_ups=(
            "如果要避免重复合并，你会不会引入分布式锁，锁粒度怎么选？",
            "如果要把上传、解析、向量化做成最终一致状态机，你会如何设计幂等和补偿？",
        ),
    )
    use_cases, repository = _use_cases(ai_orchestration_facade=None)
    use_cases._question_generation_service = QuestionGenerationService(llm_transport=transport)

    result = use_cases.create_question_task(_command(selected_progress_node_ref=NODE_REF))

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.SUCCEEDED
    assert len(repository.questions) == 1
    question = repository.questions[0]
    question_text = question.question_text
    assert "如果" in question_text
    assert "你会如何" in question_text
    assert "大文件异步处理管道" in question_text
    assert "分布式锁" in question_text
    assert "事务消息" in question_text
    metadata = question.question_metadata
    decision = metadata["next_question_decision"]
    assert decision["evidence_support_level"] == "adjacent_project_evidence"
    assert decision["turn_intent"] == "extension_design_followup"
    assert decision["main_question_style"] == "ask_hypothetical_design"
    assert decision["allowed_extension_depth"] == "main_question_allowed"
    follow_ups = metadata["next_question_question"]["follow_ups"]
    assert any("分布式锁" in item and "如果" in item for item in follow_ups)
    assert any("最终一致状态机" in item and "如果" in item for item in follow_ups)
    assert metadata["next_question_persistence_hints"]["should_persist_decision"] is True


def test_next_question_agent_job_gap_only_role_requirement_uses_gap_probe() -> None:
    transport = _NextQuestionDecisionTransport(
        turn_intent="gap_compensation_design",
        evidence_support_level="job_gap_only",
        main_question_style="ask_hypothetical_design",
        allowed_extension_depth="main_question_allowed",
        question_kind="gap_compensation_design",
        question_text="假设你需要为一个上传解析链路补齐分布式一致性能力，你会如何设计幂等、补偿和验证指标？",
        unsupported_capability_claims=("分布式锁", "事务消息"),
        evidence_refs=(),
        confidence="low",
        missing_context=("resume",),
    )
    service = QuestionGenerationService(llm_transport=transport)
    session, context, plan, state = _question_generation_inputs(
        primary_text="岗位要求能设计分布式一致性、幂等和补偿机制。",
        primary_source_type="job_requirement",
        node_title="分布式锁与事务消息最终一致性设计",
        expected_capability="验证岗位要求中的分布式一致性设计能力。",
    )

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert result.succeeded
    assert result.draft is not None
    assert result.draft.question_metadata["next_question_decision"]["turn_intent"] == "gap_compensation_design"
    assert result.draft.question_metadata["next_question_decision"]["evidence_support_level"] == "job_gap_only"
    assert "假设" in result.draft.question_text
    for forbidden in ("你在项目中", "你当时实现", "你负责的项目"):
        assert forbidden not in result.draft.question_text


def test_next_question_agent_clarifies_when_materials_missing() -> None:
    transport = _NextQuestionDecisionTransport(
        turn_intent="clarification",
        evidence_support_level="insufficient_context",
        main_question_style="ask_clarification",
        allowed_extension_depth="none",
        question_kind="clarification",
        question_text="请先补充本轮要追问的简历项目、岗位要求、当前进度节点和可引用 evidence 后，我再继续出题。",
        unsupported_capability_claims=(),
        evidence_refs=(),
        confidence="low",
        missing_context=("resume", "job", "progress_node", "evidence_refs"),
        clarification_needed=True,
    )
    service = QuestionGenerationService(llm_transport=transport)
    session, _context, plan, state = _question_generation_inputs(primary_text="")
    context = {"content_digest": "ctx_phase1_empty", "turns": []}

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert result.succeeded
    assert result.draft is not None
    metadata = result.draft.question_metadata
    assert metadata["next_question_clarification_needed"] is True
    assert metadata["next_question_question"]["question_kind"] == "clarification"
    assert metadata["next_question_decision"]["turn_intent"] == "clarification"
    assert "请先补充" in result.draft.question_text


def test_next_question_agent_post_check_blocks_adjacent_unsupported_claim_as_fact() -> None:
    transport = _NextQuestionDecisionTransport(
        turn_intent="project_implementation_deep_dive",
        evidence_support_level="adjacent_project_evidence",
        main_question_style="ask_how_implemented",
        allowed_extension_depth="follow_up_only",
        question_kind="implementation_deep_dive",
        question_text="你设计了分布式锁和 RocketMQ 事务消息来保证最终一致性，当时半消息回查是怎么做的？",
        unsupported_capability_claims=("分布式锁", "RocketMQ 事务消息", "半消息回查", "最终一致性状态机"),
    )
    service = QuestionGenerationService(llm_transport=transport)
    session, context, plan, state = _distributed_lock_weak_evidence_inputs()

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert not result.succeeded
    assert result.draft is None
    assert "next_question_post_check_unsupported_claim_in_main_question" in result.validation_errors


def test_follow_up_question_service_sends_follow_up_prompt_to_llm_transport() -> None:
    transport = _RecordingQuestionTransport()
    service = QuestionGenerationService(llm_transport=transport)
    session, context, plan, state = _question_generation_inputs(
        primary_text="支付链路需要覆盖幂等、失败补偿和上线验证指标。",
        node_title="支付可靠性追问",
        expected_capability="验证候选人能否围绕支付可靠性说明设计、取舍和复盘。",
    )

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
        follow_up_context=_follow_up_context(),
    )

    assert result.succeeded
    assert result.draft is not None
    assert len(transport.requests) == 1
    request = transport.requests[0]
    assert request.task_type == QUESTION_FOLLOW_UP_PROMPT_TASK_TYPE
    assert request.prompt_version == "polish_question_follow_up_prompt.v1"
    assert request.schema_id == "polish_question_follow_up_generation_output_v1"
    provider_request = request.evidence_bundle
    assert set(provider_request) == QUESTION_PROVIDER_REQUEST_TOP_LEVEL_KEYS
    assert provider_request["task_type"] == QUESTION_FOLLOW_UP_PROMPT_TASK_TYPE
    assert provider_request["history_summary"]["generation_mode"] == "follow_up"
    follow_up = provider_request["history_summary"]["follow_up"]
    assert follow_up["parent_question_id"] == "que_parent"
    assert follow_up["parent_answer_id"] == "ans_parent"
    assert follow_up["parent_feedback_id"] == "fb_parent"
    assert follow_up["target_dimension"] == "失败处理和验证指标"
    serialized_provider_request = json.dumps(provider_request, ensure_ascii=False, sort_keys=True)
    for forbidden in ("资深技术面试追问设计专家", "角色：助手", "test_user", "test123", "固定候选人", "审计样本"):
        assert forbidden not in serialized_provider_request
    metadata = result.draft.question_metadata
    assert metadata["question_pattern"] == "follow_up_targeted"
    assert metadata["follow_up_reason"] == "missing_answer_dimension"
    assert metadata["follow_up_target_dimension"] == "失败处理和验证指标"
    assert metadata["llm_generation_mode"] == "provider_structured_json"
    assert metadata["fallback_visible"] is False


def test_question_service_uses_injected_runtime_policy_for_prompt_contract_ids() -> None:
    policy = QuestionGenerationRuntimePolicy(
        policy_version="tenant-test-policy.v9",
        prompt_asset_id="tenant_polish_question_generation",
        prompt_version="tenant_polish_question_prompt.v9",
        prompt_schema_id="tenant_polish_question_output_v9",
        prompt_schema_version="v9",
        task_type="tenant_polish_question_generation",
        contract_ids=("P-TENANT-POLISH-QUESTION", "P-TENANT-SHARED"),
        source="test_dependency_injection",
    )
    transport = _RecordingQuestionTransport()
    service = QuestionGenerationService(llm_transport=transport, runtime_policy=policy)
    session, context, plan, state = _question_generation_inputs(
        primary_text="支付链路需要覆盖幂等、失败补偿和上线验证指标。",
        node_title="支付可靠性追问",
        expected_capability="验证候选人能否围绕支付可靠性说明设计、取舍和复盘。",
    )

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert result.succeeded
    assert len(transport.requests) == 1
    request = transport.requests[0]
    assert request.contract_ids == ("P-TENANT-POLISH-QUESTION", "P-TENANT-SHARED")
    assert request.task_type == "tenant_polish_question_generation"
    assert request.prompt_version == "tenant_polish_question_prompt.v9"
    assert request.schema_id == "tenant_polish_question_output_v9"
    assert "contract_ids" not in request.evidence_bundle
    assert "policy_version" not in request.evidence_bundle
    assert set(request.evidence_bundle) == QUESTION_PROVIDER_REQUEST_TOP_LEVEL_KEYS
    metadata = result.draft.question_metadata
    assert metadata["prompt_asset_version"] == "tenant_polish_question_prompt.v9"
    assert metadata["prompt_schema_id"] == "tenant_polish_question_output_v9"
    assert metadata["prompt_policy_version"] == "tenant-test-policy.v9"
    assert metadata["prompt_policy_source"] == "test_dependency_injection"


def test_question_service_uses_injected_policy_for_source_priority_and_taxonomy() -> None:
    policy = QuestionGenerationRuntimePolicy(
        policy_version="tenant-source-taxonomy.v1",
        source_priority_by_purpose={
            "next_question": {"job_requirement": 1, "resume_project": 50},
        },
        question_kind_taxonomy={
            "project_deep_dive": {"schema_value": "project_deep_dive", "signals": ()},
            "technical_chain_deep_dive": {"schema_value": "technical_chain_deep_dive", "signals": ()},
            "failure_recovery_deep_dive": {
                "schema_value": "failure_recovery_deep_dive",
                "signals": ("支付可靠性追问",),
            },
            "tradeoff_design": {"schema_value": "tradeoff_design", "signals": ()},
            "clarification_needed": {"schema_value": "clarification_needed", "signals": ()},
        },
        source="test_dependency_injection",
    )
    transport = _RecordingQuestionTransport()
    service = QuestionGenerationService(llm_transport=transport, runtime_policy=policy)
    session, context, plan, state = _question_generation_inputs(
        primary_text="候选人简历中只有宽泛的接口开发经历。",
        node_title="支付可靠性追问",
        expected_capability="解释支付可靠性建设路径。",
    )
    context["job_snapshot"] = {
        "job_id": "job_policy_priority",
        "job_version_id": "jobver_policy_priority",
        "requirements": ["支付链路需要覆盖幂等、失败补偿和上线验证指标。"],
        "responsibilities": [],
    }

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert result.succeeded
    request = transport.requests[0]
    generation_policy = _question_request_input_data(request)["generation_policy"]
    assert generation_policy["claim_mode"] == "job_gap_probe"
    assert generation_policy["question_kind"] == "failure_recovery_deep_dive"
    assert result.draft.question_metadata["primary_source_type"] == "job_requirement"
    assert result.draft.question_metadata["prompt_policy_version"] == "tenant-source-taxonomy.v1"


def test_question_service_marks_fake_transport_as_deterministic_fake() -> None:
    service = QuestionGenerationService(llm_transport=FakeLlmTransport())
    session, context, plan, state = _question_generation_inputs(
        primary_text="支付链路需要覆盖幂等、失败补偿和上线验证指标。",
        node_title="支付可靠性追问",
        expected_capability="验证候选人能否围绕支付可靠性说明设计、取舍和复盘。",
    )

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert result.succeeded
    assert result.draft is not None
    metadata = result.draft.question_metadata
    assert metadata["llm_generation_mode"] == "deterministic_fake_transport"
    assert metadata["provider_status"] == "fake_transport"
    assert metadata["fallback_reason"] == "fake_transport_configured"
    assert metadata["fallback_visible"] is True


def test_follow_up_question_service_marks_fake_transport_as_fake_fallback() -> None:
    service = QuestionGenerationService(llm_transport=FakeLlmTransport())
    session, context, plan, state = _question_generation_inputs(
        primary_text="支付链路需要覆盖幂等、失败补偿和上线验证指标。",
        node_title="支付可靠性追问",
        expected_capability="验证候选人能否围绕支付可靠性说明设计、取舍和复盘。",
    )

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
        follow_up_context=_follow_up_context(),
    )

    assert result.succeeded
    assert result.draft is not None
    metadata = result.draft.question_metadata
    assert metadata["question_pattern"] == "follow_up_targeted"
    assert metadata["llm_generation_mode"] == "deterministic_fake_transport"
    assert metadata["provider_status"] == "fake_transport"
    assert metadata["fallback_reason"] == "fake_transport_configured"
    assert metadata["fallback_visible"] is True


def test_follow_up_question_service_marks_missing_transport_as_degraded_fallback() -> None:
    service = QuestionGenerationService()
    session, context, plan, state = _question_generation_inputs(
        primary_text="支付链路需要覆盖幂等、失败补偿和上线验证指标。",
        node_title="支付可靠性追问",
        expected_capability="验证候选人能否围绕支付可靠性说明设计、取舍和复盘。",
    )

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
        follow_up_context=_follow_up_context(),
    )

    assert result.succeeded
    assert result.draft is not None
    metadata = result.draft.question_metadata
    assert metadata["question_pattern"] == "follow_up_targeted"
    assert metadata["llm_generation_mode"] == "deterministic_degraded_generation"
    assert metadata["fallback_reason"] == "llm_transport_unavailable"
    assert metadata["fallback_visible"] is True
    assert metadata["provider_status"] != "called"


def test_question_service_rejects_llm_output_that_does_not_match_schema() -> None:
    service = QuestionGenerationService(llm_transport=_InvalidQuestionTransport())
    session, context, plan, state = _question_generation_inputs(
        primary_text="支付链路需要覆盖幂等、失败补偿和上线验证指标。"
    )

    result = service.generate(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=NODE_REF,
    )

    assert not result.succeeded
    assert result.draft is None
    assert "llm_question_text_required" in result.validation_errors


def test_question_service_retries_transient_llm_failure_with_structured_logs(
    caplog,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    LogUtil.configure(BackendLogSettings(console_enabled=True, file_enabled=False))
    sleeps: list[float] = []
    monkeypatch.setattr(
        "app.application.polish.question_generation_service.sleep",
        lambda seconds: sleeps.append(seconds),
        raising=False,
    )
    policy = QuestionGenerationRuntimePolicy(llm_max_retries=1, llm_retry_backoff_seconds=0.01)
    transport = _FlakyQuestionTransport()
    service = QuestionGenerationService(llm_transport=transport, runtime_policy=policy)
    session, context, plan, state = _question_generation_inputs(
        primary_text="支付链路需要覆盖幂等、失败补偿和上线验证指标。"
    )

    with caplog.at_level(logging.INFO, logger="app.agent.runtime"):
        result = service.generate(
            session=session,
            context=context,
            plan=plan,
            state=state,
            requested_ref=NODE_REF,
        )

    assert result.succeeded
    assert transport.calls == 2
    assert sleeps == [0.01]
    records = [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "app.agent.runtime"
    ]
    assert any(
        record["event"] == "agent_runtime_step"
        and record["phase"] == "llm_call"
        and record["status"] == "retry_scheduled"
        and record["retry_delay_seconds"] == 0.01
        and record["attempt"] == 1
        for record in records
    )


def test_question_task_persists_validation_failed_task_for_invalid_llm_output() -> None:
    use_cases, repository = _use_cases(ai_orchestration_facade=None)
    use_cases._question_generation_service = QuestionGenerationService(
        llm_transport=_InvalidQuestionTransport()
    )

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.VALIDATION_FAILED
    assert "llm_question_text_required" in result.value.validation_errors
    assert repository.questions == []
    assert len(repository.tasks) == 1


def test_follow_up_question_task_uses_llm_transport_request() -> None:
    transport = _RecordingQuestionTransport()
    use_cases, repository = _use_cases(ai_orchestration_facade=None)
    use_cases._question_generation_service = QuestionGenerationService()
    parent_result = use_cases.create_question_task(_command())
    assert parent_result.is_success
    parent_question = repository.questions[0]
    _attach_parent_answer_and_feedback(repository, parent_question.question_id)
    use_cases._question_generation_service = QuestionGenerationService(llm_transport=transport)
    transport.requests.clear()

    result = use_cases.create_question_task(
        _command(
            generation_mode="follow_up",
            selected_progress_node_ref=NODE_REF,
            parent_question_id=parent_question.question_id,
            parent_answer_id="ans_follow_parent",
            parent_feedback_id="fb_follow_parent",
        )
    )

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.SUCCEEDED
    assert len(transport.requests) == 1
    assert transport.requests[0].task_type == QUESTION_FOLLOW_UP_PROMPT_TASK_TYPE
    assert len(repository.questions) == 2
    follow_up_question = repository.questions[-1]
    metadata = follow_up_question.question_metadata
    assert metadata["generation_mode"] == "follow_up"
    assert metadata["question_pattern"] == "follow_up_targeted"
    assert metadata["llm_generation_mode"] == "provider_structured_json"
    assert metadata["follow_up_reason"] == "missing_answer_dimension"
    assert metadata["follow_up_target_dimension"] == "失败处理和验证指标"
    assert str(metadata["template_signature"]).startswith("llm:follow_up_prompt:")
    assert "上一轮回答" in follow_up_question.question_text


def test_follow_up_question_task_parse_failure_persists_failed_task_without_question() -> None:
    valid_transport = _RecordingQuestionTransport()
    use_cases, repository = _use_cases(ai_orchestration_facade=None)
    use_cases._question_generation_service = QuestionGenerationService()
    parent_result = use_cases.create_question_task(_command())
    assert parent_result.is_success
    parent_question = repository.questions[0]
    _attach_parent_answer_and_feedback(repository, parent_question.question_id)
    use_cases._question_generation_service = QuestionGenerationService(llm_transport=_InvalidQuestionTransport())

    result = use_cases.create_question_task(
        _command(
            generation_mode="follow_up",
            selected_progress_node_ref=NODE_REF,
            parent_question_id=parent_question.question_id,
            parent_answer_id="ans_follow_parent",
            parent_feedback_id="fb_follow_parent",
        )
    )

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.VALIDATION_FAILED
    assert "llm_question_text_required" in result.value.validation_errors
    assert len(repository.questions) == 1
    assert len(repository.tasks) == 2


def test_question_service_logs_llm_parse_failure_without_raw_output(caplog) -> None:
    LogUtil.configure(BackendLogSettings(console_enabled=True, file_enabled=False))
    service = QuestionGenerationService(llm_transport=_InvalidQuestionTransport())
    session, context, plan, state = _question_generation_inputs(
        primary_text="支付链路需要覆盖幂等、失败补偿和上线验证指标。"
    )

    with caplog.at_level(logging.INFO, logger="app.agent.runtime"):
        result = service.generate(
            session=session,
            context=context,
            plan=plan,
            state=state,
            requested_ref=NODE_REF,
        )

    assert not result.succeeded
    records = [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "app.agent.runtime"
    ]
    parse_record = next(
        record
        for record in records
        if record["event"] == "agent_runtime_step" and record["phase"] == "parse_output"
    )
    assert parse_record["status"] == "failed"
    assert "llm_question_text_required" in parse_record["error_type"]
    serialized = json.dumps(records, ensure_ascii=False)
    assert "unknown_ref" not in serialized
    assert "raw_prompt" not in serialized
    assert "raw_completion" not in serialized


def test_question_metadata_normalization_keeps_safe_prompt_asset_fields_only() -> None:
    normalized = normalize_question_metadata(
        {
            "question_pattern": "technical_chain_deep_dive",
            "prompt_asset_version": NEXT_QUESTION_AGENT_PROMPT_VERSION,
            "prompt_schema_id": NEXT_QUESTION_AGENT_SCHEMA_ID,
            "prompt_schema_version": "v2",
            "prompt_input_digest": "sha256:abc123",
            "prompt_evidence_refs": ["evidence_ref_1", "evidence_ref_2"],
            "prompt_safety_summary": {
                "input_data_untrusted": True,
                "raw_prompt_persisted": False,
                "provider_payload_persisted": False,
                "note": "safe summary",
            },
            "surface_prompt": "must be dropped",
            "raw_prompt": "must be dropped",
            "system_prompt": "must be dropped",
            "developer_prompt": "must be dropped",
            "user_prompt": "must be dropped",
            "primary_evidence_text": "full evidence must be dropped",
            "full_resume": "full resume must be dropped",
            "full_jd": "full jd must be dropped",
            "provider_payload": {"secret": "must be dropped"},
            "raw_completion": "must be dropped",
        }
    )

    assert normalized["prompt_asset_version"] == NEXT_QUESTION_AGENT_PROMPT_VERSION
    assert normalized["prompt_schema_id"] == NEXT_QUESTION_AGENT_SCHEMA_ID
    assert normalized["prompt_schema_version"] == "v2"
    assert normalized["prompt_input_digest"] == "sha256:abc123"
    assert normalized["prompt_evidence_refs"] == ["evidence_ref_1", "evidence_ref_2"]
    assert normalized["prompt_safety_summary"] == {
        "input_data_untrusted": True,
        "raw_prompt_persisted": False,
        "provider_payload_persisted": False,
    }
    for forbidden_key in (
        "surface_prompt",
        "raw_prompt",
        "system_prompt",
        "developer_prompt",
        "user_prompt",
        "primary_evidence_text",
        "full_resume",
        "full_jd",
        "provider_payload",
        "raw_completion",
    ):
        assert forbidden_key not in normalized


def test_question_task_metadata_uses_business_state_not_prototype_markers() -> None:
    use_cases, repository = _use_cases(ai_orchestration_facade=None)

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert repository.questions
    metadata = repository.questions[0].question_metadata
    serialized_metadata = json.dumps(metadata, ensure_ascii=False)
    assert metadata["llm_generation_mode"] == "deterministic_degraded_generation"
    assert metadata["fallback_reason"] == "llm_transport_unavailable"
    assert metadata["focus_dimension"] != "phase1_blueprint"
    assert not metadata["template_signature"].startswith("tpl:phase1_blueprint:")
    assert "phase1" not in serialized_metadata
    assert "local_blueprint_renderer" not in serialized_metadata


def test_question_task_default_policy_marks_fallback_source_and_resolution_context() -> None:
    use_cases, repository = _use_cases(ai_orchestration_facade=None)

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert repository.questions
    metadata = repository.questions[0].question_metadata
    assert metadata["prompt_policy_source"] == "fallback_default"
    assert metadata["prompt_policy_source_type"] == "fallback_default"
    assert metadata["prompt_policy_fallback"] is True
    context = metadata["prompt_policy_resolution_context"]
    assert context["owner_id"] == OWNER_ID
    assert context["actor_id"] == ACTOR_ID
    assert context["tenant_id"] == OWNER_ID
    assert context["session_id"] == SESSION_ID
    assert context["job_id"] == "job_pr5_q2"
    assert context["job_version_id"] == "jobver_pr5_q2"
    assert context["generation_mode"] == "new_question"
    assert context["requested_progress_node_ref"] == NODE_REF
    item_sources = metadata["prompt_policy_item_sources"]
    assert item_sources["contract_ids"] == {
        "source": "python_default",
        "version": "polish_question_generation_policy.v1",
        "override": "none",
    }
    assert item_sources["prompt_schema_id"]["source"] == "python_default"
    assert item_sources["source_priority_by_purpose"]["override"] == "none"


def test_question_task_uses_custom_policy_resolver_for_new_question() -> None:
    seen_contexts: list[QuestionGenerationPolicyResolutionContext] = []

    def resolver(
        context: QuestionGenerationPolicyResolutionContext,
        base_policy: QuestionGenerationRuntimePolicy | None,
    ) -> QuestionGenerationRuntimePolicy:
        seen_contexts.append(context)
        assert base_policy is not None
        return QuestionGenerationRuntimePolicy(
            policy_version="tenant-job-policy.v2",
            prompt_asset_id="tenant_job_question_generation",
            prompt_version="tenant_job_question_prompt.v2",
            prompt_schema_id="tenant_job_question_output_v2",
            prompt_schema_version="v2",
            task_type="tenant_job_question_generation",
            contract_ids=("P-TENANT-JOB-QUESTION", "P-TENANT-SHARED"),
            source="tenant_job_policy_resolver",
            source_type="tenant_job_resolver",
            source_version="tenant-policy-registry.v2",
            source_chain=("app_state.question_generation_runtime_policy_resolver",),
            fallback=False,
        )

    use_cases, repository = _use_cases(
        ai_orchestration_facade=None,
        question_generation_policy_resolver=resolver,
    )

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert seen_contexts
    assert seen_contexts[0].job_id == "job_pr5_q2"
    assert seen_contexts[0].job_version_id == "jobver_pr5_q2"
    assert result.value.contract_ids == ("P-TENANT-JOB-QUESTION", "P-TENANT-SHARED")
    metadata = repository.questions[0].question_metadata
    assert metadata["prompt_asset_version"] == "tenant_job_question_prompt.v2"
    assert metadata["prompt_schema_id"] == "tenant_job_question_output_v2"
    assert metadata["prompt_policy_source"] == "tenant_job_policy_resolver"
    assert metadata["prompt_policy_source_type"] == "tenant_job_resolver"
    assert metadata["prompt_policy_fallback"] is False
    assert metadata["prompt_policy_resolution_context"]["job_id"] == "job_pr5_q2"


def test_question_task_status_uses_injected_runtime_policy_contract_ids() -> None:
    policy = QuestionGenerationRuntimePolicy(
        policy_version="tenant-test-policy.v9",
        prompt_asset_id="tenant_polish_question_generation",
        prompt_version="tenant_polish_question_prompt.v9",
        prompt_schema_id="tenant_polish_question_output_v9",
        prompt_schema_version="v9",
        task_type="tenant_polish_question_generation",
        contract_ids=("P-TENANT-POLISH-QUESTION", "P-TENANT-SHARED"),
        source="test_dependency_injection",
    )
    use_cases, repository = _use_cases(ai_orchestration_facade=None, question_generation_policy=policy)

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert result.value is not None
    assert result.value.contract_ids == ("P-TENANT-POLISH-QUESTION", "P-TENANT-SHARED")
    assert repository.questions
    assert repository.questions[0].question_metadata["prompt_policy_version"] == "tenant-test-policy.v9"


def test_follow_up_question_task_uses_custom_policy_resolver() -> None:
    def resolver(
        context: QuestionGenerationPolicyResolutionContext,
        base_policy: QuestionGenerationRuntimePolicy | None,
    ) -> QuestionGenerationRuntimePolicy:
        assert context.generation_mode in {"new_question", "follow_up"}
        return QuestionGenerationRuntimePolicy(
            policy_version="tenant-follow-policy.v3",
            prompt_asset_id="tenant_follow_question_generation",
            prompt_version="tenant_follow_question_prompt.v3",
            prompt_schema_id="tenant_follow_question_output_v3",
            prompt_schema_version="v3",
            task_type="tenant_follow_question_generation",
            contract_ids=("P-TENANT-FOLLOW-QUESTION", "P-TENANT-SHARED"),
            source="tenant_follow_policy_resolver",
            source_type="tenant_job_resolver",
            source_version="tenant-policy-registry.v3",
            source_chain=("app_state.question_generation_runtime_policy_resolver",),
            fallback=False,
        )

    transport = _RecordingQuestionTransport()
    use_cases, repository = _use_cases(
        ai_orchestration_facade=None,
        question_generation_policy_resolver=resolver,
    )
    use_cases._question_generation_service = QuestionGenerationService()
    parent_result = use_cases.create_question_task(_command())
    assert parent_result.is_success
    parent_question = repository.questions[0]
    _attach_parent_answer_and_feedback(repository, parent_question.question_id)
    use_cases._question_generation_service = QuestionGenerationService(llm_transport=transport)

    result = use_cases.create_question_task(
        _command(
            generation_mode="follow_up",
            selected_progress_node_ref=NODE_REF,
            parent_question_id=parent_question.question_id,
            parent_answer_id="ans_follow_parent",
            parent_feedback_id="fb_follow_parent",
        )
    )

    assert result.is_success
    assert result.value.contract_ids == ("P-TENANT-FOLLOW-QUESTION", "P-TENANT-SHARED")
    request = transport.requests[0]
    assert request.contract_ids == ("P-TENANT-FOLLOW-QUESTION", "P-TENANT-SHARED")
    assert request.task_type == "tenant_follow_question_generation.follow_up"
    assert request.prompt_version == "tenant_follow_question_prompt.v3.follow_up"
    assert request.schema_id == "tenant_follow_question_output_v3.follow_up"
    metadata = repository.questions[-1].question_metadata
    assert metadata["generation_mode"] == "follow_up"
    assert metadata["prompt_policy_source"] == "tenant_follow_policy_resolver"
    assert metadata["prompt_policy_resolution_context"]["generation_mode"] == "follow_up"


def test_phase1_empty_question_text_persists_failed_task_without_question() -> None:
    use_cases, repository = _use_cases(ai_orchestration_facade=None)
    use_cases._question_generation_service = QuestionGenerationService(
        surface_question_builder=lambda _blueprint, _scope: " "
    )

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.VALIDATION_FAILED
    assert result.value.validation_errors
    assert repository.questions == []
    assert len(repository.tasks) == 1


def test_phase1_grounding_failure_persists_validation_failed_task_without_question() -> None:
    use_cases, repository = _use_cases(ai_orchestration_facade=None)
    use_cases._question_generation_service = QuestionGenerationService(
        llm_transport=_SoftGroundingWarningTransport()
    )

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.VALIDATION_FAILED
    assert not any(ref.resource_type == "question" for ref in result.value.candidate_refs)
    assert "adjacent_project_evidence_requires_hypothetical_extension" in result.value.validation_errors
    assert repository.questions == []
    assert len(repository.tasks) == 1

    detail = use_cases.get_session(GetPolishSessionQuery(owner_id=OWNER_ID, session_id=SESSION_ID))

    assert detail.is_success
    assert detail.value is not None
    assert detail.value.turns == ()

def test_question_task_blocks_unsafe_llm_question_text() -> None:
    use_cases, repository = _use_cases(ai_orchestration_facade=None)
    use_cases._question_generation_service = QuestionGenerationService(
        llm_transport=_UnsafeQuestionTransport("api_key=")
    )

    result = use_cases.create_question_task(_command())

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.VALIDATION_FAILED
    assert "llm_question_text_unsafe_leakage" in result.value.validation_errors
    assert repository.questions == []
    assert len(repository.tasks) == 1


def test_phase2_feedback_task_without_provider_returns_generation_failed_without_reserved_success() -> None:
    use_cases, repository = _use_cases(ai_orchestration_facade=None)
    question_result = use_cases.create_question_task(_command())
    assert question_result.is_success
    question = repository.questions[0]
    answer = PolishAnswer(
        answer_id="ans_phase1_reserved",
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        question_id=question.question_id,
        answer_round=1,
        answer_text="我会先说明业务背景，再说明一致性方案和验证指标。",
        status="saved",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    repository.answers = [answer]
    repository.feedbacks = []
    repository.get_answer = lambda owner_id, answer_id: next(
        (item for item in repository.answers if item.owner_id == owner_id and item.answer_id == answer_id),
        None,
    )
    repository.list_answers_for_session = lambda owner_id, session_id: tuple(
        item for item in repository.answers if item.owner_id == owner_id and item.session_id == session_id
    )
    repository.add_feedback = lambda feedback: repository.feedbacks.append(feedback)
    repository.list_feedbacks_for_session = lambda owner_id, session_id: tuple(
        item for item in repository.feedbacks if item.owner_id == owner_id and item.session_id == session_id
    )

    result = use_cases.create_feedback_task(
        CreatePolishFeedbackTaskCommand(
            owner_id=OWNER_ID,
            actor_id=ACTOR_ID,
            session_id=SESSION_ID,
            answer_id=answer.answer_id,
        )
    )

    assert result.is_success
    assert result.value is not None
    assert result.value.status == AiTaskStatus.GENERATION_FAILED
    assert result.value.retryable is True
    assert result.value.validation_errors == ("llm_transport_unavailable",)
    assert result.value.candidate_refs == ()
    assert len(repository.feedbacks) == 1
    feedback_payload = json.loads(repository.feedbacks[0].feedback_summary)
    assert feedback_payload["status"] == "generation_failed"
    assert feedback_payload["status"] != "reserved"
    assert feedback_payload["error"]["code"] == "llm_transport_unavailable"
    assert feedback_payload["score_result"] is None
    assert feedback_payload["candidate_refs"] == []
    assert feedback_payload["reference_answer"] is None
    assert "feedback_metadata" not in feedback_payload



def _question_request_input_data(request: LlmTransportRequest) -> dict[str, Any]:
    bundle = request.evidence_bundle if isinstance(request.evidence_bundle, dict) else {}
    input_data = bundle.get("input_data") if isinstance(bundle.get("input_data"), dict) else None
    if input_data is not None:
        return input_data
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
    history_summary = bundle.get("history_summary") if isinstance(bundle.get("history_summary"), dict) else {}
    follow_up = history_summary.get("follow_up") if isinstance(history_summary.get("follow_up"), dict) else {}
    result = {
        "progress_node": progress_node,
        "selected_node_title": progress_node.get("title"),
        "skill_dimension": progress_node.get("title"),
        "source_support_level": bundle.get("source_support_level"),
        "generation_policy": {
            "question_kind": generation_policy.get("question_kind") or "technical_chain_deep_dive",
            "claim_mode": generation_policy.get("claim_mode") or "evidence_grounded",
            "focus_dimension": generation_policy.get("question_kind") or "technical_chain_deep_dive",
        },
        "evidence_refs": canonical_evidence.get("evidence_refs") if isinstance(canonical_evidence.get("evidence_refs"), list) else [],
        "evidence_summaries": canonical_evidence.get("evidence_summaries") if isinstance(canonical_evidence.get("evidence_summaries"), list) else [],
        "canonical_project_assets": canonical_evidence.get("canonical_project_assets") if isinstance(canonical_evidence.get("canonical_project_assets"), dict) else {},
        "missing_context": canonical_evidence.get("missing_context") if isinstance(canonical_evidence.get("missing_context"), list) else [],
    }
    if follow_up:
        result["generation_mode"] = "follow_up"
        result["follow_up"] = follow_up
    return result

def _question_generation_inputs(
    *,
    primary_text: str,
    primary_source_type: str = "resume_project",
    node_title: str = "支付链路一致性",
    expected_capability: str = "能说明状态流转、幂等、失败补偿和上线验证。",
) -> tuple[Any, dict[str, Any], dict[str, Any], dict[str, Any]]:
    use_cases, repository = _use_cases(ai_orchestration_facade=None)
    detail = use_cases._build_session_detail(owner_id=OWNER_ID, session=repository.session)
    context = dict(detail.progress_context)
    if primary_source_type == "job_requirement":
        context["resume_snapshot"] = {
            "resume_id": "res_phase1_empty",
            "resume_version_id": "resver_phase1_empty",
            "summary": "",
            "project_experiences": [],
            "skills": [],
        }
        context["job_snapshot"] = {
            "job_id": "job_phase1",
            "job_version_id": "jobver_phase1",
            "requirements": [primary_text] if primary_text else [],
            "responsibilities": [],
        }
    else:
        context["resume_snapshot"] = {
            "resume_id": "res_phase1",
            "resume_version_id": "resver_phase1",
            "summary": "",
            "project_experiences": [primary_text] if primary_text else [],
            "skills": [],
        }
        context["job_snapshot"] = {
            "job_id": "job_phase1",
            "job_version_id": "jobver_phase1",
            "requirements": [],
            "responsibilities": [],
        }
    plan = {
        "status": "ready",
        "context_digest": "ctx_phase1",
        "nodes": [
            {
                "progress_node_ref": NODE_REF,
                "title": node_title,
                "expected_capability": expected_capability,
                "missing_points": ["需要补充验证指标。"],
                "children": [],
            }
        ],
    }
    state = {
        "status": "ready",
        "node_states": [],
        "current_priority": {"progress_node_ref": NODE_REF},
        "progress": {"progress_percent": 0},
    }
    return repository.session, context, plan, state


def _distributed_lock_weak_evidence_inputs() -> tuple[Any, dict[str, Any], dict[str, Any], dict[str, Any]]:
    session, context, plan, state = _question_generation_inputs(
        primary_text="硬件测试 AI 平台：完成测试流程自动化和报告生成。",
        node_title="分布式锁与事务消息最终一致性设计",
        expected_capability=(
            "高阶深度目标：考察候选人面对高并发库存扣减时的方案选型、异常处理与数据恢复能力"
        ),
    )
    context["resume_snapshot"]["project_experiences"] = [
        "硬件测试 AI 平台：完成测试流程自动化和报告生成。",
        "设备数据看板：负责采集链路、指标聚合和异常告警。",
        "混合检索：结合关键词和向量召回提升知识库问答命中率。",
        "大文件异步处理管道：Redis记录分片状态，MinIO存储分片与完整文件，RocketMQ解耦后续解析与向量化流程。",
    ]
    context["job_snapshot"] = {
        "job_id": "job_phase1_distributed_lock",
        "job_version_id": "jobver_phase1_distributed_lock",
        "requirements": [],
        "responsibilities": [],
    }
    return session, context, plan, state


def _follow_up_context() -> dict[str, Any]:
    return {
        "parent_question_id": "que_parent",
        "parent_question_excerpt": "请说明支付链路的一致性方案。",
        "parent_answer_id": "ans_parent",
        "parent_answer_excerpt": "我主要做了接口串联，但没有展开失败兜底和指标验证。",
        "parent_feedback_id": "fb_parent",
        "parent_feedback_excerpt": "缺少失败处理和验证指标。",
        "target_dimension": "失败处理和验证指标",
        "follow_up_reason": "missing_answer_dimension",
        "parent_evidence_refs": ["resume_project_001"],
    }


def _attach_parent_answer_and_feedback(repository: Any, question_id: str) -> None:
    now = utc_now()
    answer = PolishAnswer(
        answer_id="ans_follow_parent",
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        question_id=question_id,
        answer_round=1,
        answer_text="我主要做了接口串联，但没有展开失败兜底和指标验证。",
        status="saved",
        created_at=now,
        updated_at=now,
    )
    feedback = PolishFeedback(
        feedback_id="fb_follow_parent",
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        answer_id=answer.answer_id,
        ai_task_id="aitask_follow_feedback",
        score_result_id=None,
        feedback_summary=json.dumps(
            {
                "feedback_text": "缺少失败处理和验证指标。",
                "missing_answer_dimensions": [{"title": "失败处理和验证指标"}],
            },
            ensure_ascii=False,
        ),
        status="generated",
        created_at=now,
        updated_at=now,
    )
    repository.answers = [answer]
    repository.feedbacks = [feedback]
    repository.list_answers_for_session = lambda owner_id, session_id: tuple(repository.answers)
    repository.list_feedbacks_for_session = lambda owner_id, session_id: tuple(repository.feedbacks)


class _RecordingQuestionTransport:
    QUESTION_TEXT = "请围绕「支付链路需要覆盖幂等、失败补偿和上线验证指标」设计一次可评分追问，说明边界、取舍和复盘信号。"

    def __init__(self) -> None:
        self.requests: list[LlmTransportRequest] = []

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        self.requests.append(request)
        input_data = _question_request_input_data(request)
        generation_policy = input_data["generation_policy"]
        follow_up = input_data.get("follow_up") if isinstance(input_data.get("follow_up"), dict) else {}
        evidence_refs = tuple(input_data["evidence_refs"])
        evidence_summaries = input_data.get("evidence_summaries") if isinstance(input_data.get("evidence_summaries"), list) else []
        evidence_excerpt = next(
            (
                str(item.get("excerpt"))
                for item in evidence_summaries
                if isinstance(item, dict) and item.get("excerpt")
            ),
            "支付链路需要覆盖幂等、失败补偿和上线验证指标。",
        )
        question_text = self.QUESTION_TEXT
        if input_data.get("source_support_level") == "adjacent_project_evidence":
            question_text = (
                f"如果要围绕「{input_data.get('selected_node_title') or '当前训练节点'}」继续扩展，"
                f"并结合岗位/简历证据「{evidence_excerpt}」，你会如何设计边界、失败处理、验证指标和关键取舍？"
            )
        if input_data.get("generation_mode") == "follow_up":
            if input_data.get("source_support_level") == "adjacent_project_evidence":
                question_text = (
                    f"你上一轮回答中提到「{follow_up.get('previous_answer', '上一轮回答')}」，"
                    f"现在围绕「{follow_up.get('target_dimension', '追问目标')}」继续追问："
                    f"如果要结合上一题背景、岗位/简历证据「{evidence_excerpt}」和反馈缺口补齐这部分能力，"
                    "你会如何判断边界、设计失败处理、验证指标和关键取舍？"
                )
            else:
                question_text = (
                    f"你上一轮回答中提到「{follow_up.get('previous_answer', '上一轮回答')}」，"
                    f"现在围绕「{follow_up.get('target_dimension', '追问目标')}」继续追问："
                    f"请结合上一题背景、岗位/简历证据「{evidence_excerpt}」和反馈缺口，说明你的具体判断、边界、失败处理、验证指标和关键取舍。"
                )
        return LlmTransportResult(
            result={
                "question_text": question_text,
                "question_kind": generation_policy["question_kind"],
                "focus_dimension": generation_policy["focus_dimension"],
                "difficulty": "medium",
                "skill_dimension": "支付可靠性",
                "expected_signal": "能说明幂等、补偿、验证指标和复盘证据。",
                "follow_ups": ["失败补偿如何触发？", "如何证明方案有效？"],
                "scoring_rubric": [
                    {"dimension": "grounding", "signals": ["引用证据", "不编造经历"]},
                    {"dimension": "tradeoff", "signals": ["说明取舍", "说明边界"]},
                ],
                "missing_context": [],
                "evidence_refs": list(evidence_refs),
                "confidence": "high",
                "clarification_needed": False,
            },
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.HIGH,
            low_confidence_flags=(),
            trace_refs=("trace_next_question_agent_prompt_v1",),
            evidence_refs=evidence_refs,
        )


class _SoftGroundingWarningTransport:
    QUESTION_TEXT = "请提供一个您亲身参与的项目，该项目涉及分布式锁与事务消息的最终一致性设计，并说明故障恢复策略。"

    def __init__(self) -> None:
        self.requests: list[LlmTransportRequest] = []

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        self.requests.append(request)
        input_data = _question_request_input_data(request)
        generation_policy = input_data["generation_policy"]
        return LlmTransportResult(
            result={
                "question_text": self.QUESTION_TEXT,
                "question_kind": generation_policy["question_kind"],
                "focus_dimension": generation_policy["focus_dimension"],
                "difficulty": "clarification",
                "skill_dimension": "分布式一致性",
                "expected_signal": "能说明亲身项目、分布式锁、事务消息、最终一致性和故障恢复策略。",
                "follow_ups": ["故障恢复如何验证？", "最终一致性边界是什么？"],
                "scoring_rubric": [
                    {"dimension": "experience", "signals": ["说明亲身参与项目"]},
                    {"dimension": "recovery", "signals": ["说明故障恢复策略"]},
                ],
                "missing_context": ["缺少可锚定的候选人项目证据"],
                "evidence_refs": [],
                "confidence": "low",
                "clarification_needed": True,
            },
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.LOW,
            low_confidence_flags=("clarification_needed",),
            trace_refs=("trace_soft_grounding_warning",),
            evidence_refs=(),
        )


class _ProjectClarificationQuestionTransport(_SoftGroundingWarningTransport):
    QUESTION_TEXT = (
        "我看到您的简历中完成过硬件测试AI平台等项目，但未涉及分布式锁与事务消息。"
        "您能否补充一个项目案例？"
    )

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        self.requests.append(request)
        input_data = _question_request_input_data(request)
        generation_policy = input_data["generation_policy"]
        evidence_refs = tuple(input_data["evidence_refs"])
        return LlmTransportResult(
            result={
                "question_text": self.QUESTION_TEXT,
                "question_kind": generation_policy["question_kind"],
                "focus_dimension": generation_policy["focus_dimension"],
                "difficulty": "clarification",
                "skill_dimension": input_data["skill_dimension"],
                "expected_signal": "能说明迁移设计、并发控制、事务消息和失败恢复策略。",
                "follow_ups": ["锁超时如何处理？", "重复消费如何保证幂等？"],
                "scoring_rubric": [
                    {"dimension": "design", "signals": ["说明并发控制", "说明消息确认"]},
                    {"dimension": "recovery", "signals": ["说明失败补偿", "说明状态回查"]},
                ],
                "missing_context": ["缺少直接分布式锁项目经历"],
                "evidence_refs": list(evidence_refs),
                "confidence": "low",
                "clarification_needed": True,
            },
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.LOW,
            low_confidence_flags=("clarification_needed",),
            trace_refs=("trace_project_clarification_question",),
            evidence_refs=evidence_refs,
        )


class _NextQuestionDecisionTransport:
    def __init__(
        self,
        *,
        turn_intent: str,
        evidence_support_level: str,
        main_question_style: str,
        allowed_extension_depth: str,
        question_kind: str,
        question_text: str,
        unsupported_capability_claims: tuple[str, ...],
        follow_ups: tuple[str, ...] = ("这个链路如何验证效果？", "遇到失败时你怎么恢复？"),
        evidence_refs: tuple[str, ...] | None = None,
        confidence: str = "medium",
        missing_context: tuple[str, ...] = (),
        clarification_needed: bool = False,
        question_style_check: str = "pass",
        evidence_grounding_check: str = "pass",
    ) -> None:
        self.requests: list[LlmTransportRequest] = []
        self._turn_intent = turn_intent
        self._evidence_support_level = evidence_support_level
        self._main_question_style = main_question_style
        self._allowed_extension_depth = allowed_extension_depth
        self._question_kind = question_kind
        self._question_text = question_text
        self._unsupported_capability_claims = unsupported_capability_claims
        self._follow_ups = follow_ups
        self._evidence_refs = evidence_refs
        self._confidence = confidence
        self._missing_context = missing_context
        self._clarification_needed = clarification_needed
        self._question_style_check = question_style_check
        self._evidence_grounding_check = evidence_grounding_check

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        self.requests.append(request)
        input_data = _question_request_input_data(request)
        allowed_refs = tuple(input_data["evidence_refs"])
        evidence_refs = allowed_refs if self._evidence_refs is None else self._evidence_refs
        primary_ref = evidence_refs[0] if evidence_refs else None
        return LlmTransportResult(
            result={
                "schema_id": "polish_next_question_agent_decision_v1",
                "prompt_version": request.prompt_version,
                "clarification_needed": self._clarification_needed,
                "confidence": self._confidence,
                "missing_context": list(self._missing_context),
                "decision": {
                    "turn_intent": self._turn_intent,
                    "intent_reason": "根据当前证据和进度选择本轮追问意图。",
                    "evidence_support_level": self._evidence_support_level,
                    "evidence_support_reason": "证据与目标能力的直接性由本轮 Agent 判断。",
                    "main_question_style": self._main_question_style,
                    "allowed_extension_depth": self._allowed_extension_depth,
                    "primary_evidence_refs": [primary_ref] if primary_ref else [],
                    "secondary_evidence_refs": list(evidence_refs[1:]),
                    "unsupported_capability_claims": list(self._unsupported_capability_claims),
                    "risk_flags": [],
                    "avoid_patterns_applied": ["unsupported_capability_as_fact"],
                },
                "question": {
                    "question_text": self._question_text,
                    "question_kind": self._question_kind,
                    "difficulty": "clarification" if self._clarification_needed else "medium",
                    "skill_dimension": input_data["skill_dimension"],
                    "expected_signal": "能说明真实实现链路、设计原因、异常处理和验证效果。",
                    "follow_ups": list(self._follow_ups),
                    "scoring_rubric": [
                        {"dimension": "grounding", "signals": ["引用证据", "不伪造经历"]},
                        {"dimension": "reasoning", "signals": ["说明链路", "说明取舍和验证"]},
                    ],
                },
                "persistence_hints": {
                    "should_persist_decision": True,
                    "should_update_progress": True,
                    "next_focus_candidates": [input_data["progress_node"]["ref"]],
                    "trace_tags": ["next_question_agent", self._evidence_support_level],
                },
                "evidence_refs": list(evidence_refs),
                "post_check_hints": {
                    "claims_to_verify": list(self._unsupported_capability_claims),
                    "unsupported_terms_in_question": [],
                    "question_style_check": self._question_style_check,
                    "evidence_grounding_check": self._evidence_grounding_check,
                },
            },
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.LOW if self._confidence == "low" else ConfidenceLevel.MEDIUM,
            low_confidence_flags=tuple(self._missing_context),
            trace_refs=("trace_next_question_decision",),
            evidence_refs=evidence_refs,
        )


class _UnsafeQuestionTransport(_SoftGroundingWarningTransport):
    def __init__(self, marker: str) -> None:
        super().__init__()
        self._marker = marker

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        result = super().generate(request)
        result.result["question_text"] = f"请回答这道包含 {self._marker} 的题目。"
        return result


class _InvalidQuestionTransport:
    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        return LlmTransportResult(
            result={
                "question_text": "",
                "evidence_refs": ["unknown_ref"],
            },
            validation_status=ValidationStatus.INVALID,
            confidence_level=ConfidenceLevel.LOW,
            low_confidence_flags=("schema_invalid",),
            trace_refs=("trace_invalid_question_prompt_v3",),
            evidence_refs=(),
        )


class _FlakyQuestionTransport(_RecordingQuestionTransport):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        self.calls += 1
        if self.calls == 1:
            raise LlmTransportUnavailableError("temporary provider outage")
        return super().generate(request)
