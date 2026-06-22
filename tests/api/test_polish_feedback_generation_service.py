from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from app.application.llm.types import LlmTransportRequest, LlmTransportResult
from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
    POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
    POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    POLISH_FEEDBACK_TASK_TYPE,
)
from app.domain.shared.enums import ConfidenceLevel, ValidationStatus
from app.application.polish.feedback_validation import validate_final_feedback_payload
from tests.fakes.llm_transport import FakeLlmTransport


def _context() -> dict[str, Any]:
    return {
        "owner_id": "owner_001",
        "actor_id": "user_001",
        "session_id": "sess_001",
        "question_id": "question_001",
        "answer_id": "answer_001",
        "question_text": "请说明你如何设计订单异步处理链路，并保证失败可恢复。",
        "answer_text": "我会用消息队列解耦下单和履约，并通过重试表恢复失败消息。",
        "answer_round": 2,
        "polish_theme": "支付系统可靠性",
        "progress_node_ref": "progress_node_reliability",
        "question_sources": [
            {"source_type": "progress_node", "source_ref": "progress_node_reliability"},
        ],
        "evidence_refs": ["resume_project_payment", "job_requirement_reliability"],
        "same_question_answers": [
            {
                "answer_id": "answer_prev",
                "answer_round": 1,
                "answer_summary": "上一轮只说明了 MQ 解耦，缺少幂等和观测。",
                "loss_point_ids": ["lp_observability"],
            }
        ],
        "same_project_turns": [
            {
                "question_id": "question_project",
                "answer_id": "answer_project",
                "feedback_summary": "项目表述里曾说明幂等键设计。",
            }
        ],
        "session_recent_turns": [
            {
                "question_id": "question_recent",
                "answer_id": "answer_recent",
                "feedback_summary": "最近一题已经扣过监控指标说明不足。",
            }
        ],
        "project_asset_summaries": [
            {
                "asset_id": "asset_payment",
                "summary": "支付项目已有事务消息、幂等键和补偿任务素材。",
            }
        ],
        "job_snapshot": {"job_id": "job_001", "requirements": ["高可用后端设计", "故障恢复"]},
        "resume_snapshot": {"resume_id": "resume_001", "projects": ["支付系统"]},
        "progress_node_snapshot": {"node_ref": "progress_node_reliability", "title": "可靠性设计"},
        "progress_state": {
            "progress_state_ref": "progress_node_reliability",
            "current_priority": {
                "progress_node_ref": "progress_node_reliability",
                "title": "可靠性设计",
                "expected_capability": "说明失败恢复、幂等和观测指标。",
            },
            "weak_skill_refs": ["failure_recovery", "tradeoff_reasoning", "observability"],
            "strong_skill_refs": ["structured_reasoning"],
            "node_states": [
                {"progress_node_ref": "progress_node_reliability", "status": "in_progress"},
                {"progress_node_ref": "progress_node_structure", "status": "completed"},
            ],
        },
    }


def _adaptive_score_result() -> dict[str, Any]:
    return {
        "score_type": "polish_answer",
        "score_value": 1,
        "progress_state_ref": "progress_node_reliability",
        "reasoning": "ProgressState 显示 failure_recovery、tradeoff_reasoning 和 observability 仍需强化。",
        "adaptive_rubric": {
            "rubric_version": "polish_answer.progress_adaptive_rubric.v1",
            "progress_state_ref": "progress_node_reliability",
            "dimensions": [
                {
                    "dimension": "correctness",
                    "adaptive_weight": 0.16,
                    "progress_basis": ["current_priority:progress_node_reliability"],
                    "anchor_refs": ["anchor_correctness"],
                },
                {
                    "dimension": "depth",
                    "adaptive_weight": 0.22,
                    "progress_basis": ["weak_skill:failure_recovery"],
                    "anchor_refs": ["anchor_depth"],
                },
                {
                    "dimension": "tradeoff_reasoning",
                    "adaptive_weight": 0.22,
                    "progress_basis": ["weak_skill:tradeoff_reasoning"],
                    "anchor_refs": ["anchor_tradeoff_reasoning"],
                },
                {
                    "dimension": "structure",
                    "adaptive_weight": 0.14,
                    "progress_basis": ["strong_skill:structured_reasoning"],
                    "anchor_refs": ["anchor_structure"],
                },
                {
                    "dimension": "engineering_awareness",
                    "adaptive_weight": 0.26,
                    "progress_basis": ["weak_skill:observability"],
                    "anchor_refs": ["anchor_engineering_awareness"],
                },
            ],
        },
        "dimension_scores": [
            {
                "dimension": "correctness",
                "score": 88,
                "adaptive_weight": 0.16,
                "progress_focus": ["progress_node_reliability"],
                "rationale": "方向正确，覆盖 MQ 解耦。",
            },
            {
                "dimension": "depth",
                "score": 76,
                "adaptive_weight": 0.22,
                "progress_focus": ["progress_node_reliability"],
                "rationale": "恢复链路展开不足。",
            },
            {
                "dimension": "tradeoff_reasoning",
                "score": 72,
                "adaptive_weight": 0.22,
                "progress_focus": ["progress_node_reliability"],
                "rationale": "延迟、可靠性和人工介入取舍不足。",
            },
            {
                "dimension": "structure",
                "score": 84,
                "adaptive_weight": 0.14,
                "progress_focus": ["progress_node_reliability"],
                "rationale": "结构清楚。",
            },
            {
                "dimension": "engineering_awareness",
                "score": 70,
                "adaptive_weight": 0.26,
                "progress_focus": ["progress_node_reliability"],
                "rationale": "观测指标和告警阈值不足。",
            },
        ],
        "adaptive_insights": {
            "weak_skills": ["failure_recovery", "tradeoff_reasoning", "observability"],
            "strong_skills": ["structured_reasoning"],
            "unstable_skills": ["reliability"],
            "overweighted_skills": ["depth", "tradeoff_reasoning", "engineering_awareness"],
            "underweighted_skills": ["structure"],
        },
        "signals": ["weakness_detected", "progress_update"],
        "progress_updates": [
            {
                "progress_node_ref": "progress_node_reliability",
                "signal": "needs_focus",
                "dimension": "engineering_awareness",
            }
        ],
    }


def _generated_payload() -> dict[str, Any]:
    return {
        "feedback_text": "回答覆盖了 MQ 解耦，但故障恢复和观测指标仍不够可验证。",
        "answer_summary": "候选人说明了异步解耦和失败重试表。",
        "score_result": _adaptive_score_result(),
        "score_reasoning": [
            {
                "dimension": "reliability",
                "rationale": "补偿触发与人工介入边界未全部覆盖。",
            }
        ],
        "loss_points": [
            {
                "loss_point_id": "lp_recovery",
                "severity": "major",
                "deduction": 12,
                "reason": "没有说明补偿任务的触发条件和终止条件。",
            },
            {
                "loss_point_id": "lp_observability",
                "severity": "minor",
                "deducted_points": 6,
                "reason": "缺少失败率、堆积量和恢复耗时指标。",
            },
        ],
        "reference_answer": {
            "sections": [
                {
                    "section_id": "ref_recovery",
                    "title": "失败恢复",
                    "content": "说明重试、补偿、幂等键、死信和人工介入边界。",
                    "addresses_loss_point_ids": ["lp_recovery"],
                },
                {
                    "section_id": "ref_observability",
                    "title": "观测指标",
                    "content": "说明消息堆积、失败率、恢复耗时和告警阈值。",
                    "addresses_loss_point_ids": ["lp_observability"],
                },
            ]
        },
        "same_question_effect": {
            "improved_points": ["补充了异步解耦"],
            "repeated_loss_point_ids": ["lp_observability"],
            "regressed_points": [],
            "next_retry_focus": ["补齐恢复指标"],
            "score_delta": 6,
        },
        "project_asset_update_candidates": [
            {
                "candidate_type": "project_asset_update_candidate",
                "candidate_ref": "asset_candidate_payment_recovery",
                "user_confirmation_required": True,
                "target_asset_ref": {"resource_type": "asset", "resource_id": "asset_payment"},
                "summary": "补充支付系统失败恢复和观测指标素材。",
            }
        ],
        "low_confidence_flags": [],
        "evidence_refs": ["resume_project_payment", "job_requirement_reliability"],
    }


class _PayloadTransport:
    def __init__(self, payload: object, *, projection_payload: object | None = None) -> None:
        self.payload = payload
        self.projection_payload = projection_payload
        self.requests: list[LlmTransportRequest] = []

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        self.requests.append(request)
        payload = (
            self.projection_payload
            if getattr(request, "stage", None) == "json_projection" and self.projection_payload is not None
            else _default_projection_payload(request)
            if getattr(request, "stage", None) == "json_projection"
            else self.payload
        )
        return LlmTransportResult(
            result=payload,  # type: ignore[arg-type]
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.MEDIUM,
            low_confidence_flags=(),
            trace_refs=("trace_provider_001",),
            evidence_refs=("evidence_provider_001",),
            metadata=_stage_transport_metadata(request),
        )


class _SequencePayloadTransport:
    def __init__(self, *payloads: object) -> None:
        self.payloads = list(payloads)
        self.requests: list[LlmTransportRequest] = []

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        self.requests.append(request)
        payload = self.payloads[min(len(self.requests) - 1, len(self.payloads) - 1)]
        return LlmTransportResult(
            result=payload,  # type: ignore[arg-type]
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.MEDIUM,
            low_confidence_flags=(),
            trace_refs=(f"trace_provider_{len(self.requests):03d}",),
            evidence_refs=(f"evidence_provider_{len(self.requests):03d}",),
            metadata=_stage_transport_metadata(request),
        )


class _RaisingTransport:
    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        raise TimeoutError("provider timed out")


class _StageTruncationTransport:
    def __init__(self, stage: str) -> None:
        self.stage = stage
        self.requests: list[LlmTransportRequest] = []

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        self.requests.append(request)
        if getattr(request, "stage", None) == self.stage:
            error = RuntimeError("provider output truncated")
            setattr(error, "error_type", "provider_output_truncated")
            setattr(
                error,
                "safe_metadata",
                {
                    "provider_error_type": "provider_output_truncated",
                    "stage": self.stage,
                    "finish_reason": "length",
                    "completion_tokens": 4800,
                    "reasoning_tokens": 512 if self.stage == "analysis_candidate" else 0,
                },
            )
            raise error
        payload = _default_projection_payload(request) if getattr(request, "stage", None) == "json_projection" else _generated_payload()
        return LlmTransportResult(
            result=payload,
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.MEDIUM,
            low_confidence_flags=(),
            trace_refs=(f"trace_provider_{len(self.requests):03d}",),
            evidence_refs=(f"evidence_provider_{len(self.requests):03d}",),
            metadata=_stage_transport_metadata(request),
        )


def _default_projection_payload(request: LlmTransportRequest) -> object:
    server_facts = request.evidence_bundle.get("server_facts") if isinstance(request.evidence_bundle, dict) else None
    if isinstance(server_facts, dict) and isinstance(server_facts.get("default_final_payload"), dict):
        return deepcopy(server_facts["default_final_payload"])
    return _generated_final_payload()


def _stage_transport_metadata(request: LlmTransportRequest) -> dict[str, Any]:
    stage = getattr(request, "stage", None)
    return {
        "stage": stage,
        "thinking_enabled": getattr(request, "thinking_enabled", None),
        "finish_reason": "stop",
        "completion_tokens": 320 if stage == "json_projection" else 900,
        "reasoning_tokens": 0 if stage == "json_projection" else 128,
    }


def _service(llm_transport: object):
    from app.application.polish.feedback_generation_service import FeedbackGenerationService

    return FeedbackGenerationService(llm_transport=llm_transport)


def test_feedback_generation_service_exposes_v1_entry_only() -> None:
    service = _service(_PayloadTransport(_generated_payload()))

    assert hasattr(service, "generate_feedback_v1")
    assert not hasattr(service, "generate")


def _generated_final_payload() -> dict[str, Any]:
    payload = _generated_payload()
    payload.pop("same_question_effect", None)
    payload.pop("project_asset_update_candidates", None)
    payload.pop("score_reasoning", None)
    payload.pop("evidence_refs", None)
    payload.update(
        {
            "schema_id": POLISH_FEEDBACK_FINAL_SCHEMA_ID,
            "schema_version": "1.0",
            "status": "generated",
            "contract_ids": list(POLISH_FEEDBACK_FINAL_CONTRACT_IDS),
            "feedback_id": "feedback_001",
            "trace_refs": [{"resource_type": "llm_trace", "resource_id": "trace_001"}],
            "feedback_metadata": {
                "prompt_version": POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
            },
            "asset_consistency_check": {
                "status": "consistent",
                "checked_asset_refs": [],
                "conflicts": [],
                "unsupported_claims": [],
                "user_clarification_required": False,
            },
            "answer_coverage": {
                "expected_points": [],
                "covered_points": [],
                "missing_points": [],
                "weak_points": [],
                "contradicted_points": [],
            },
            "answer_change_analysis": {
                "has_prior_attempts": False,
                "previous_answer_refs": [],
                "retained_points": [],
                "newly_added_points": [],
                "regressed_points": [],
                "repeated_loss_points": [],
                "fixed_loss_points": [],
                "score_delta": None,
                "trend": "first_attempt",
            },
            "feedback_cards": [{"card_type": "overall", "status": "generated", "payload": {}}],
            "next_recommended_actions": ["review_reference_answer"],
        }
    )
    return payload


def test_service_with_fake_transport_returns_blocked_non_success() -> None:
    result = _service(FakeLlmTransport()).generate_feedback_v1(_context())

    assert result.succeeded is False
    assert result.payload is None
    assert result.validation_errors == ("fake_transport_not_runtime_provider",)
    assert result.metadata["provider_status"] == "fake_transport"
    assert result.metadata["llm_called"] is False
    assert result.metadata["context_hygiene_status"] == "blocked"
    assert "fallback_reason" not in result.metadata


def test_fake_transport_fixture_payload_remains_available_for_explicit_tests() -> None:
    request = LlmTransportRequest(
        contract_ids=POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
        task_type=POLISH_FEEDBACK_TASK_TYPE,
        input_refs=("answer_001",),
        evidence_bundle={
            "current_question": {"question_text": "How would you recover failed async payment messages?"},
            "current_answer": {"answer_text": "I would use retry jobs and alerts."},
        },
        prompt_version=POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
        schema_id=POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    )

    fake_result = FakeLlmTransport().generate(request)
    payload = fake_result.result

    assert payload["feedback_text"]
    assert payload["answer_summary"]
    assert payload["score_reasoning"]
    assert payload["loss_points"]
    assert payload["reference_answer"]["sections"]
    assert payload["low_confidence_flags"] == []
    assert payload["evidence_refs"]
    assert "schema_id" not in payload
    assert "schema_version" not in payload
    assert "contract_ids" not in payload
    assert payload["score_result"]["progress_state_ref"] == "progress_node_reliability"
    assert payload["score_result"]["adaptive_rubric"]["progress_state_ref"] == "progress_node_reliability"
    assert {item["dimension"] for item in payload["score_result"]["dimension_scores"]} == {
        "correctness",
        "depth",
        "tradeoff_reasoning",
        "structure",
        "engineering_awareness",
    }
    assert "project_asset_update_candidates" in payload


def test_service_metadata_includes_prompt_schema_llm_and_provider_status() -> None:
    result = _service(FakeLlmTransport()).generate_feedback_v1(_context())

    assert result.metadata["prompt_version"] == POLISH_FEEDBACK_AGENT_PROMPT_VERSION
    assert result.metadata["schema_id"] == POLISH_FEEDBACK_FINAL_SCHEMA_ID
    assert result.metadata["llm_called"] is False
    assert result.metadata["provider_status"] == "fake_transport"
    assert result.metadata["context_hygiene_status"] == "blocked"
    assert result.metadata["safe_context_metadata"]["raw_model_io_storage"] is False
    assert "fallback_reason" not in result.metadata


def test_feedback_request_uses_structured_output_budget() -> None:
    transport = _PayloadTransport(_generated_payload())

    result = _service(transport).generate_feedback_v1(_context())

    assert result.succeeded is True
    assert transport.requests
    assert 4000 <= getattr(transport.requests[-1], "max_tokens", 8000) < 8000


def test_feedback_generation_two_stage_uses_thinking_for_analysis_and_non_thinking_for_json_projection() -> None:
    transport = _PayloadTransport(_generated_payload())

    result = _service(transport).generate_feedback_v1(_context())

    assert result.succeeded is True
    assert len(transport.requests) == 2
    analysis_request, projection_request = transport.requests
    assert analysis_request.stage == "analysis_candidate"
    assert analysis_request.thinking_enabled is True
    assert analysis_request.evidence_bundle["feedback_mode"] == "candidate_compact"
    assert projection_request.stage == "json_projection"
    assert projection_request.thinking_enabled is False
    assert projection_request.evidence_bundle["feedback_mode"] == "final_json_projection"
    assert projection_request.evidence_bundle["safe_candidate_summary"]["feedback_text"] == (
        "回答覆盖了 MQ 解耦，但故障恢复和观测指标仍不够可验证。"
    )
    assert projection_request.evidence_bundle["server_facts"]["default_final_payload"]["status"] == "generated"
    assert result.payload is not None
    score_result = result.payload["score_result"]
    assert score_result["score_value"] == 76.6
    assert score_result["signals"] == ["weakness_detected", "progress_update"]
    assert score_result["stability_layer"]["dual_pass_judging"] is False
    assert score_result["stability_layer"]["pass_count"] == 1
    assert score_result["stability_layer"]["score_value_passes"] == [76.6]
    assert score_result["stability_layer"]["variance_bounded"] is True
    assert score_result["stability_layer"]["numeric_variance_detected"] is False
    assert score_result["calibration_layer"]["semantic_adjustment_applied"] is False
    assert score_result["learning_control"]["hardcoded_thresholds_used"] is False
    assert score_result["learning_control"]["learning_rate"] == 0.5
    assert all(item["learning_rate"] == 0.5 for item in score_result["progress_updates"])
    assert "evaluation_drift_detected" not in result.payload["low_confidence_flags"]
    assert result.payload["feedback_metadata"]["phase5_pipeline"] == [
        "evaluate",
        "stability_layer",
        "calibration",
        "learning_control",
        "normalized_progress_update",
    ]
    assert "generation_stages" not in result.payload["feedback_metadata"]
    assert [stage["stage"] for stage in result.metadata["generation_stages"]] == [
        "analysis_candidate",
        "json_projection",
    ]
    assert result.metadata["generation_stages"][0]["thinking_enabled"] is True
    assert result.metadata["generation_stages"][1]["thinking_enabled"] is False


def test_feedback_request_marks_current_answer_as_bounded_primary_input() -> None:
    transport = _PayloadTransport(_generated_payload())
    context = _context()
    context["answer_text"] = "Short complete answer that is still the current primary task input."

    result = _service(transport).generate_feedback_v1(context)

    assert result.succeeded is True
    provider_prompt = transport.requests[0].evidence_bundle
    current_answer = provider_prompt["current_answer"]
    assert "answer_text" not in current_answer
    assert current_answer["structured_answer"]["parse_status"] == "parsed"
    assert current_answer["structured_answer"]["claims"][0]["text"] == context["answer_text"]
    assert current_answer["answer_text_policy"] == "structured_answer_signal_primary_input"
    assert current_answer["answer_text_max_chars"] == 1200
    assert current_answer["answer_text_is_bounded"] is True
    assert current_answer["full_answer_forbidden"] is True
    assert provider_prompt["input_contract"]["answer_text_policy"] == "structured_answer_signal_primary_input"
    assert provider_prompt["input_contract"]["answer_text_max_chars"] == 1200
    assert provider_prompt["input_contract"]["answer_text_is_bounded"] is True
    assert provider_prompt["input_contract"]["full_answer_forbidden"] is True


def test_feedback_generation_blocks_when_parser_fails(monkeypatch: Any) -> None:
    from app.application.polish import feedback_generation_service

    class RaisingParser:
        def parse(self, answer_text: str) -> object:
            raise RuntimeError("parser failed")

    monkeypatch.setattr(feedback_generation_service, "TranscriptSignalParser", RaisingParser)
    transport = _PayloadTransport(_generated_payload())
    context = _context()

    result = _service(transport).generate_feedback_v1(context)

    assert result.succeeded is False
    assert result.payload is None
    assert result.validation_errors == ("structured_answer_parse_failed",)
    assert transport.requests == []
    assert result.metadata["context_hygiene_status"] == "blocked"
    assert "fallback_reason" not in result.metadata


def test_feedback_request_uses_v1_provider_prompt_budget_and_evidence_limits() -> None:
    payload = _generated_payload()
    payload["score_result"]["progress_state_ref"] = "progress_node_hybrid_search"
    payload["score_result"]["adaptive_rubric"]["progress_state_ref"] = "progress_node_hybrid_search"
    for item in payload["score_result"]["dimension_scores"]:
        item["progress_focus"] = ["progress_node_hybrid_search"]
    for item in payload["score_result"]["progress_updates"]:
        item["progress_node_ref"] = "progress_node_hybrid_search"
    transport = _PayloadTransport(payload)
    context = _context()
    context["question_text"] = "请深入说明混合检索策略优化如何在召回率、精排质量和延迟之间做取舍。"
    context["answer_text"] = "我会先用关键词召回保证确定性，再用向量召回补语义覆盖，最后用重排模型统一打分。 " * 80
    context["evidence_refs"] = ["resume_project_hybrid_search", "question_source_hybrid_search"]
    context["question_sources"] = [
        {
            "ref": "question_source_hybrid_search",
            "source_type": "resume_project_contribution",
            "title": "混合检索策略优化",
            "excerpt": "通过 BM25、向量召回和 rerank 做多路召回融合。",
        },
        {
            "ref": "question_source_inventory",
            "source_type": "resume_project_contribution",
            "title": "物料库存处理工作流",
            "excerpt": "物料库存处理工作流包含库存冻结、调拨和盘点。",
        },
        {
            "ref": "question_source_large_file",
            "source_type": "resume_project_contribution",
            "title": "大文件异步处理管道",
            "excerpt": "大文件异步处理管道包含分片上传、解析和入库。",
        },
    ]
    context["same_question_answers"] = [
        {
            "answer_id": f"answer_prev_{index}",
            "answer_text": f"PREVIOUS_FULL_ANSWER_{index}_SHOULD_NOT_BE_INCLUDED " * 40,
            "answer_summary": f"上一轮摘要 {index}：缺少召回融合后的评估指标。" * 20,
        }
        for index in range(3)
    ]
    context["job_snapshot"] = {
        "job_id": "job_001",
        "requirements": [f"岗位要求 {index}" for index in range(6)],
        "full_jd": "FULL_JD_SHOULD_NOT_BE_INCLUDED",
    }
    context["resume_snapshot"] = {
        "resume_id": "resume_001",
        "projects": [
            "混合检索策略优化：负责 BM25、向量召回、rerank 和线上评估。",
            "物料库存处理工作流：负责库存冻结、调拨和盘点。",
            "大文件异步处理管道：负责分片上传、解析和入库。",
        ],
        "full_resume": "FULL_RESUME_SHOULD_NOT_BE_INCLUDED",
        "markdown_text": "RESUME_MARKDOWN_SHOULD_NOT_BE_INCLUDED",
        "work_experiences": ["WORK_EXPERIENCE_SHOULD_NOT_BE_INCLUDED"],
    }
    context["progress_node_snapshot"] = {
        "node_ref": "progress_node_hybrid_search",
        "title": "混合检索策略优化",
        "expected_capability": "说明多路召回、重排、评估指标和延迟取舍。" * 10,
        "related_resume_evidence": ["混合检索策略优化"],
    }
    context["progress_state"] = {
        "progress_state_ref": "progress_node_hybrid_search",
        "current_priority": {
            "progress_node_ref": "progress_node_hybrid_search",
            "title": "混合检索策略优化",
            "expected_capability": "说明多路召回、重排、评估指标和延迟取舍。",
        },
        "weak_skill_refs": ["latency_tradeoff", "evaluation_metrics"],
        "strong_skill_refs": ["retrieval_architecture"],
        "node_states": [{"progress_node_ref": "progress_node_hybrid_search", "status": "in_progress"}],
    }

    result = _service(transport).generate_feedback_v1(context)

    assert result.succeeded is True
    request = transport.requests[0]
    provider_prompt = request.evidence_bundle
    serialized_provider_user = json.dumps(
        {
            "task_type": request.task_type,
            "input_refs": list(request.input_refs),
            "evidence_bundle": provider_prompt,
        },
        ensure_ascii=False,
        sort_keys=True,
    )

    assert provider_prompt["feedback_mode"] == "candidate_compact"
    assert provider_prompt["input_contract"]["context_mode"] == "compact_v1"
    assert provider_prompt["progress_state"]["progress_state_ref"] == "progress_node_hybrid_search"
    assert provider_prompt["adaptive_rubric"]["weight_policy"] == "llm_judge_must_return_progress_derived_adaptive_weight"
    assert provider_prompt["task"] == "polish_feedback_candidate_v1"
    assert provider_prompt["prompt_version"] == POLISH_FEEDBACK_AGENT_PROMPT_VERSION
    assert provider_prompt["output_schema"]["schema_id"] == POLISH_FEEDBACK_FINAL_SCHEMA_ID
    assert "Generate structured polish feedback" in provider_prompt["prompt"]
    assert "developer_constraints" not in provider_prompt
    assert "refusal_and_low_confidence_policy" not in provider_prompt
    assert len(serialized_provider_user) < 12000
    assert len(provider_prompt["evidence"]) <= 5
    assert len(provider_prompt["current_question"]["question_sources"]) <= 2
    assert len(provider_prompt["same_question_answers"]) <= 1
    assert "answer_text" not in provider_prompt["same_question_answers"][0]
    assert not _contains_forbidden_key(provider_prompt)
    assert "PREVIOUS_FULL_ANSWER_0_SHOULD_NOT_BE_INCLUDED" not in serialized_provider_user
    serialized_provider_data = json.dumps(
        {key: value for key, value in provider_prompt.items() if key != "prompt"},
        ensure_ascii=False,
        sort_keys=True,
    )
    for forbidden_key in ("full_resume", "full_jd", "work_experiences", "markdown_text"):
        assert forbidden_key not in serialized_provider_data
    for forbidden in (
        "FULL_RESUME_SHOULD_NOT_BE_INCLUDED",
        "FULL_JD_SHOULD_NOT_BE_INCLUDED",
        "WORK_EXPERIENCE_SHOULD_NOT_BE_INCLUDED",
        "RESUME_MARKDOWN_SHOULD_NOT_BE_INCLUDED",
        "物料库存处理工作流",
        "大文件异步处理管道",
    ):
        assert forbidden not in serialized_provider_user
    assert provider_prompt["feedback_metadata"]["prompt_char_count"] < 12000
    assert provider_prompt["feedback_metadata"]["evidence_item_count"] <= 5
    assert provider_prompt["feedback_metadata"]["context_compaction_applied"] is True
    assert result.payload is not None
    metadata = result.payload["feedback_metadata"]
    assert metadata["context_hygiene_status"] == "clean"
    assert metadata["safe_context_metadata"]["context_compaction_applied"] is True
    assert metadata["safe_context_metadata"]["answer_text_is_bounded"] is True
    assert metadata["safe_context_metadata"]["evidence_item_count"] <= 5
    serialized_metadata = json.dumps(metadata, ensure_ascii=False, sort_keys=True)
    for forbidden in ("raw_prompt", "provider_payload", "full_resume", "full_jd"):
        assert forbidden not in serialized_metadata


def test_no_llm_transport_returns_failed_without_fake_feedback() -> None:
    result = _service(None).generate_feedback_v1(_context())

    assert result.succeeded is False
    assert result.payload is None
    assert result.validation_errors == ("llm_transport_unavailable",)
    assert result.metadata["provider_status"] == "not_configured"
    assert result.metadata["llm_called"] is False
    assert result.metadata["context_hygiene_status"] == "blocked"
    assert "fallback_reason" not in result.metadata


def test_provider_invalid_schema_returns_failed() -> None:
    payload = _generated_payload()
    payload["feedback_text"] = ""

    result = _service(_PayloadTransport(payload)).generate_feedback_v1(_context())

    assert result.succeeded is False
    assert result.payload is None
    assert result.metadata["validation_stage"] == "analysis_candidate"
    assert result.metadata["candidate_valid"] is False
    assert "feedback_text_required" in result.validation_errors


def test_provider_loss_reference_mapping_invalid_is_recovered_with_warning() -> None:
    payload = _generated_payload()
    payload["reference_answer"]["sections"][0]["addresses_loss_point_ids"] = ["lp_unknown"]

    result = _service(_PayloadTransport(payload)).generate_feedback_v1(_context())

    assert result.succeeded is True
    assert result.payload is not None
    assert result.payload["status"] == "partial"
    section = result.payload["reference_answer"]["sections"][0]
    assert section["addresses_loss_point_ids"] == []
    assert "reference_answer_unknown_loss_point_ref_removed" in result.payload["feedback_metadata"]["validation_warnings"]


def test_provider_reference_sections_without_titles_generate_feedback_with_default_titles() -> None:
    payload = _generated_payload()
    for section in payload["reference_answer"]["sections"]:
        section.pop("title")

    result = _service(_PayloadTransport(payload)).generate_feedback_v1(_context())

    assert result.succeeded is True
    assert result.payload is not None
    assert result.payload["status"] in {"generated", "partial"}
    titles = [section["title"] for section in result.payload["reference_answer"]["sections"]]
    assert titles == ["参考回答 1", "参考回答 2"]
    assert "reference_answer_sections_invalid" not in result.validation_errors


def test_provider_reference_sections_without_ids_generate_feedback_with_stable_ids() -> None:
    payload = _generated_payload()
    for section in payload["reference_answer"]["sections"]:
        section.pop("section_id")

    result = _service(_PayloadTransport(payload)).generate_feedback_v1(_context())

    assert result.succeeded is True
    assert result.payload is not None
    section_ids = [section["section_id"] for section in result.payload["reference_answer"]["sections"]]
    assert section_ids == ["section_1", "section_2"]
    assert "reference_answer_sections_invalid" not in result.validation_errors


def test_provider_phase4_fields_and_loss_point_id_alias_generate_feedback() -> None:
    payload = _generated_payload()
    payload["schema_id"] = POLISH_FEEDBACK_FINAL_SCHEMA_ID
    payload["schema_version"] = "1.0"
    payload["status"] = "generated"
    payload["contract_ids"] = list(POLISH_FEEDBACK_FINAL_CONTRACT_IDS)
    payload["explicit_score"] = 88
    payload["implicit_score"] = 83
    payload["scoring_dimensions"] = [{"dimension": "reliability", "score": 84}]
    payload["knowledge_points"] = ["失败恢复"]
    payload["technical_principles"] = ["幂等"]
    payload["loss_points"][0]["id"] = payload["loss_points"][0].pop("loss_point_id")
    payload["same_question_effect"] = "unchanged"
    payload["asset_consistency_check"] = {"status": "consistent"}
    payload["answer_coverage"] = {"covered_points": ["MQ"]}
    payload["answer_change_analysis"] = {"trend": "unchanged"}
    payload["feedback_cards"] = [{"card_type": "overall", "payload": {}}]
    payload["session_similarity_check"] = {"status": "not_applicable"}
    payload["next_recommended_actions"] = ["review_reference_answer"]
    payload["trace_refs"] = ["trace_model_001"]
    payload["feedback_metadata"] = {"provider": "deepseek-v4-pro"}

    result = _service(_PayloadTransport(payload)).generate_feedback_v1(_context())

    assert result.succeeded is True
    assert result.payload is not None
    assert result.payload["status"] == "generated"
    assert result.payload["loss_points"][0]["loss_point_id"] == "lp_recovery"
    assert "same_question_effect" not in result.payload
    assert "explicit_score" not in result.payload
    assert "session_similarity_check" not in result.payload
    assert isinstance(result.payload["answer_change_analysis"], dict)


def test_provider_invalid_enhancement_fields_are_warnings_not_generation_failure() -> None:
    payload = _generated_payload()
    payload["project_asset_update_candidates"] = "invalid-enhancement"
    payload["session_similarity_check"] = ["invalid-enhancement"]

    result = _service(_PayloadTransport(payload)).generate_feedback_v1(_context())

    assert result.succeeded is True
    assert result.payload is not None
    assert result.payload["status"] == "partial"
    metadata = result.payload["feedback_metadata"]
    assert "validation_warnings" in metadata
    assert "project_asset_update_candidates_invalid" in metadata["validation_warnings"]
    assert "session_similarity_check" not in result.payload


def test_unsafe_provider_payload_returns_failed() -> None:
    payload = _generated_payload()
    payload["feedback_text"] = "当前文本包含 token=hidden-chain，不应下沉。"

    result = _service(_PayloadTransport(payload)).generate_feedback_v1(_context())

    assert result.succeeded is False
    assert result.payload is None
    assert "feedback_payload_unsafe_leakage" in result.validation_errors
    assert result.metadata["context_hygiene_status"] == "blocked"
    assert "feedback_payload_unsafe_leakage" in result.metadata["validation_signals"]["validation_errors"]


def test_feedback_generation_stage_a_truncation_fails_closed() -> None:
    transport = _StageTruncationTransport("analysis_candidate")

    result = _service(transport).generate_feedback_v1(_context())

    assert result.succeeded is False
    assert result.payload is None
    assert result.validation_errors == ("provider_output_truncated",)
    assert len(transport.requests) == 1
    assert result.metadata["validation_stage"] == "analysis_candidate"
    assert result.metadata["stage"] == "analysis_candidate"
    assert result.metadata["finish_reason"] == "length"
    assert result.metadata["completion_tokens"] == 4800
    assert result.metadata["reasoning_tokens"] == 512
    stage = result.metadata["generation_stages"][0]
    assert stage["stage"] == "analysis_candidate"
    assert stage["finish_reason"] == "length"
    assert stage["failure_reason"] == "provider_output_truncated"


def test_feedback_generation_stage_b_truncation_fails_closed() -> None:
    transport = _StageTruncationTransport("json_projection")

    result = _service(transport).generate_feedback_v1(_context())

    assert result.succeeded is False
    assert result.payload is None
    assert result.validation_errors == ("provider_output_truncated",)
    assert len(transport.requests) == 2
    assert result.metadata["validation_stage"] == "json_projection"
    assert result.metadata["stage"] == "json_projection"
    assert result.metadata["finish_reason"] == "length"
    assert result.metadata["completion_tokens"] == 4800
    assert result.metadata["reasoning_tokens"] == 0
    assert [stage["stage"] for stage in result.metadata["generation_stages"]] == [
        "analysis_candidate",
        "json_projection",
    ]
    projection_stage = result.metadata["generation_stages"][1]
    assert projection_stage["finish_reason"] == "length"
    assert projection_stage["failure_reason"] == "provider_output_truncated"


def test_feedback_generation_stage_b_schema_invalid_reports_json_projection_failure() -> None:
    invalid_projection = _generated_final_payload()
    invalid_projection["status"] = "generation_failed"
    transport = _PayloadTransport(_generated_payload(), projection_payload=invalid_projection)

    result = _service(transport).generate_feedback_v1(_context())

    assert result.succeeded is False
    assert result.payload is None
    assert result.validation_errors[0] == "json_projection"
    assert "feedback_status_invalid" in result.validation_errors
    assert result.metadata["validation_stage"] == "json_projection"
    assert result.metadata["candidate_valid"] is True
    assert result.metadata["generation_stages"][1]["failure_reason"] == "json_projection"


def test_feedback_generation_filters_stage_a_unsafe_reasoning_raw_provider_and_full_completion_leakage() -> None:
    for unsafe_key in ("reasoning_content", "raw_prompt", "raw_provider", "full_completion"):
        payload = _generated_payload()
        payload[unsafe_key] = "must_not_leak"

        result = _service(_PayloadTransport(payload)).generate_feedback_v1(_context())

        assert result.succeeded is False
        assert result.payload is None
        assert result.validation_errors == ("feedback_candidate_forbidden_fields",) or (
            "feedback_payload_unsafe_leakage" in result.validation_errors
        )
        assert result.metadata["validation_stage"] == "analysis_candidate"
        assert "must_not_leak" not in json.dumps(result.metadata, ensure_ascii=False, sort_keys=True)


def test_service_candidate_invalid_metadata_marks_candidate_stage_and_llm_called() -> None:
    payload = _generated_payload()
    payload["feedback_text"] = ""

    result = _service(_PayloadTransport(payload)).generate_feedback_v1(_context())

    assert result.succeeded is False
    assert result.payload is None
    assert result.metadata["validation_stage"] == "analysis_candidate"
    assert result.metadata["candidate_valid"] is False
    assert result.metadata["llm_called"] is True


def test_service_final_validation_failure_marks_final_stage_and_candidate_valid(monkeypatch: Any) -> None:
    from app.application.polish import feedback_generation_service

    def fail_final(payload: object, *, require_feedback_id: bool = False):
        return None, ("force_invalid",)

    payload = _generated_payload()
    payload["loss_points"][0]["evidence_refs"] = ["resume_project_payment"]

    monkeypatch.setattr(feedback_generation_service, "validate_final_feedback_payload", fail_final)

    result = _service(_PayloadTransport(payload)).generate_feedback_v1(_context())

    assert result.succeeded is False
    assert result.payload is None
    assert result.metadata["validation_stage"] == "json_projection"
    assert result.metadata["candidate_valid"] is True
    assert result.validation_errors[0] == "json_projection"
    assert "force_invalid" in result.validation_errors
    assert "feedback_payload_schema_invalid" not in result.validation_errors


def test_provider_exception_returns_failed() -> None:
    result = _service(_RaisingTransport()).generate_feedback_v1(_context())

    assert result.succeeded is False
    assert result.payload is None
    assert result.validation_errors == ("llm_transport_timeout",)
    assert result.metadata["provider_status"] == "failed"
    assert result.metadata["provider_error_type"] == "timeout"


def test_provider_non_dict_payload_returns_failed() -> None:
    result = _service(_PayloadTransport(["not", "a", "dict"])).generate_feedback_v1(_context())

    assert result.succeeded is False
    assert result.payload is None
    assert result.validation_errors == ("feedback_payload_schema_invalid",)


def test_prompt_asset_contains_current_question_and_answer_without_private_fields() -> None:
    from app.application.polish.feedback_prompt_assets import build_feedback_prompt_asset

    asset = build_feedback_prompt_asset(_context())

    assert asset["task_type"] == POLISH_FEEDBACK_TASK_TYPE
    assert asset["input_data"]["current_question"]["question_text"] == _context()["question_text"]
    assert "answer_text" not in asset["input_data"]["current_answer"]
    assert asset["input_data"]["current_answer"]["structured_answer"]["claims"]
    assert not _contains_forbidden_key(asset)


def test_prompt_asset_includes_same_question_answers() -> None:
    from app.application.polish.feedback_prompt_assets import build_feedback_prompt_asset

    asset = build_feedback_prompt_asset(_context())

    assert asset["input_data"]["same_question_answers"][0]["answer_id"] == "answer_prev"
    assert asset["input_data"]["same_question_answers"][0]["answer_summary"] == "上一轮只说明了 MQ 解耦，缺少幂等和观测。"
    assert asset["input_data"]["same_question_answers"][0]["loss_point_ids"] == ["lp_observability"]


def test_prompt_asset_compacts_resume_job_and_evidence_context() -> None:
    from app.application.polish.feedback_prompt_assets import build_feedback_prompt_asset

    context = _context()
    context["job_snapshot"] = {
        "job_id": "job_001",
        "title": "后端工程师",
        "full_jd": "FULL_JD_SHOULD_NOT_BE_INCLUDED",
        "requirements": [f"岗位要求 {index}" for index in range(8)],
        "responsibilities": [f"岗位职责 {index}" for index in range(8)],
        "content_digest": "job_digest_001",
    }
    context["resume_snapshot"] = {
        "resume_id": "resume_001",
        "summary": "候选人有支付系统可靠性经验。",
        "full_resume": "FULL_RESUME_SHOULD_NOT_BE_INCLUDED",
        "markdown_text": "RESUME_MARKDOWN_SHOULD_NOT_BE_INCLUDED",
        "projects": [f"项目全文 {index}" for index in range(8)],
        "work_experiences": ["WORK_EXPERIENCE_SHOULD_NOT_BE_INCLUDED"],
        "content_digest": "resume_digest_001",
    }
    context["question_sources"] = [
        {"source_type": "progress_node", "source_ref": f"node_{index}", "summary": f"节点摘要 {index}"}
        for index in range(8)
    ]
    context["same_question_answers"] = [
        {
            "answer_id": f"answer_prev_{index}",
            "answer_round": index,
            "answer_text": f"PREVIOUS_FULL_ANSWER_{index}_SHOULD_NOT_BE_INCLUDED",
            "answer_summary": f"上一轮摘要 {index}",
            "feedback_summary": f"上一轮反馈摘要 {index}",
            "loss_point_ids": [f"lp_{index}"],
        }
        for index in range(6)
    ]
    context["session_recent_turns"] = [
        {
            "question_id": f"question_recent_{index}",
            "answer_id": f"answer_recent_{index}",
            "answer_summary": f"最近回答摘要 {index}",
            "feedback_summary": f"最近反馈摘要 {index}",
        }
        for index in range(6)
    ]

    asset = build_feedback_prompt_asset(context)
    input_data = asset["input_data"]
    serialized = repr(asset)

    assert len(input_data["evidence_items"]) <= 12
    assert len(input_data["session_recent_turns"]) <= 3
    assert len(input_data["context_snapshots"]["job_snapshot"]["requirements"]) <= 5
    assert len(input_data["context_snapshots"]["job_snapshot"]["responsibilities"]) <= 5
    assert "full_jd" not in input_data["context_snapshots"]["job_snapshot"]
    assert "full_resume" not in input_data["context_snapshots"]["resume_snapshot"]
    assert "markdown_text" not in input_data["context_snapshots"]["resume_snapshot"]
    assert "work_experiences" not in input_data["context_snapshots"]["resume_snapshot"]
    assert "FULL_JD_SHOULD_NOT_BE_INCLUDED" not in serialized
    assert "FULL_RESUME_SHOULD_NOT_BE_INCLUDED" not in serialized
    assert "RESUME_MARKDOWN_SHOULD_NOT_BE_INCLUDED" not in serialized
    assert "WORK_EXPERIENCE_SHOULD_NOT_BE_INCLUDED" not in serialized


def test_prompt_asset_same_question_answers_do_not_repeat_full_answer_text() -> None:
    from app.application.polish.feedback_prompt_assets import build_feedback_prompt_asset

    context = _context()
    context["same_question_answers"] = [
        {
            "answer_id": "answer_prev_full",
            "answer_round": 1,
            "answer_text": "PREVIOUS_FULL_ANSWER_SHOULD_NOT_BE_INCLUDED",
            "answer_summary": "上一轮摘要：缺少观测指标。",
            "feedback_summary": "上一轮反馈：补充失败率和恢复耗时。",
            "loss_point_ids": ["lp_observability"],
        }
    ]

    asset = build_feedback_prompt_asset(context)
    previous_answer = asset["input_data"]["same_question_answers"][0]
    serialized = repr(asset)

    assert "answer_text" not in previous_answer
    assert "PREVIOUS_FULL_ANSWER_SHOULD_NOT_BE_INCLUDED" not in serialized
    assert previous_answer["answer_summary"] == "上一轮摘要：缺少观测指标。"


def test_prompt_asset_does_not_fallback_to_historical_answer_text_when_summary_missing() -> None:
    from app.application.polish.feedback_prompt_assets import build_feedback_prompt_asset

    context = _context()
    context["same_question_answers"] = [
        {
            "answer_id": "answer_prev_raw_only",
            "answer_round": 1,
            "answer_text": "PREVIOUS_RAW_FULL_ANSWER_SHOULD_NOT_BE_INCLUDED",
        }
    ]

    asset = build_feedback_prompt_asset(context)
    previous_answer = asset["input_data"]["same_question_answers"][0]
    serialized = repr(asset)

    assert "answer_text" not in previous_answer
    assert "PREVIOUS_RAW_FULL_ANSWER_SHOULD_NOT_BE_INCLUDED" not in serialized


def test_prompt_asset_includes_project_asset_summaries() -> None:
    from app.application.polish.feedback_prompt_assets import build_feedback_prompt_asset

    asset = build_feedback_prompt_asset(_context())

    assert asset["input_data"]["project_asset_summaries"][0]["asset_id"] == "asset_payment"
    assert asset["input_data"]["project_asset_summaries"][0]["summary"] == "支付项目已有事务消息、幂等键和补偿任务素材。"



def _context_with_canonical_assets(*, answer_text: str, asset_status: str = "asset_confirmed") -> dict[str, Any]:
    context = _context()
    context["answer_text"] = answer_text
    context["question_metadata"] = {
        "expected_answer_dimensions": ["FastAPI APIs", "PostgreSQL persistence", "observability metrics"],
    }
    context["progress_node_snapshot"] = {
        "node_ref": "progress_node_backend_fact",
        "title": "Backend workflow automation",
        "expected_capability": "Explain FastAPI APIs, PostgreSQL persistence, and observability metrics.",
        "missing_points": ["observability metrics"],
    }
    context["canonical_project_assets"] = {
        "available": True,
        "selection_policy": "rule_based_keyword_overlap_v1",
        "items": [
            {
                "asset_id": "asset_backend_workflow",
                "status": asset_status,
                "asset_type": "project_story",
                "title": "Backend workflow automation",
                "summary": "Candidate built backend workflow automation with FastAPI and PostgreSQL.",
                "content_excerpt": "Owns FastAPI APIs, PostgreSQL persistence, retries, and observability metrics.",
            }
        ],
    }
    return context


def test_phase4_confirmed_asset_conflict_surfaces_first_card_and_blocks_feedback_question_intent() -> None:
    payload = _generated_payload()
    context = _context_with_canonical_assets(
        answer_text="I led the project with Django and MongoDB instead of the documented stack.",
        asset_status="asset_confirmed",
    )

    result = _service(_PayloadTransport(payload)).generate_feedback_v1(context)

    assert result.succeeded is True
    assert result.payload is not None
    asset_check = result.payload["asset_consistency_check"]
    assert asset_check["status"] == "conflict"
    assert {conflict["conflict_type"] for conflict in asset_check["conflicts"]} >= {
        "technology_stack_conflict"
    }
    assert result.payload["feedback_cards"][0]["card_type"] == "asset_consistency"


def test_phase4_archived_asset_is_not_used_as_canonical_conflict_source() -> None:
    payload = _generated_payload()
    context = _context_with_canonical_assets(
        answer_text="I led the project with Django and MongoDB instead of the documented stack.",
        asset_status="asset_archived",
    )

    result = _service(_PayloadTransport(payload)).generate_feedback_v1(context)

    assert result.succeeded is True
    assert result.payload is not None
    assert result.payload["asset_consistency_check"]["status"] == "insufficient_asset_context"


def test_phase4_confirmed_asset_unsupported_new_project_fact_is_candidate_claim() -> None:
    context = _context_with_canonical_assets(
        answer_text="I owned FastAPI APIs with PostgreSQL and introduced Redis cache for the project.",
        asset_status="asset_confirmed",
    )

    result = _service(_PayloadTransport(_generated_payload())).generate_feedback_v1(context)

    assert result.succeeded is True
    assert result.payload is not None
    unsupported_claims = result.payload["asset_consistency_check"]["unsupported_claims"]
    assert unsupported_claims
    assert any(claim["current_answer_claim"] == "redis" for claim in unsupported_claims)
    assert result.payload["asset_consistency_check"]["status"] == "conflict"


def test_phase4_missing_asset_consistency_from_llm_with_assets_gets_explicit_policy_warning() -> None:
    context = _context_with_canonical_assets(
        answer_text="I owned FastAPI APIs with PostgreSQL persistence.",
        asset_status="asset_confirmed",
    )

    result = _service(_PayloadTransport(_generated_payload())).generate_feedback_v1(context)

    assert result.succeeded is True
    assert result.payload is not None
    warnings = result.payload["feedback_metadata"]["phase4_validation_warnings"]
    assert "asset_consistency_check_missing_from_llm_policy_generated" in warnings
    assert result.payload["asset_consistency_check"]["checked_asset_refs"] == ["asset_backend_workflow"]


def test_phase4_rules_normalize_provider_aliases_before_validation() -> None:
    payload = _generated_payload()
    payload["loss_points"] = [
        {
            "loss_point_id": "loss_point_1",
            "severity": "major",
            "deduction": 20,
            "reason": "答案没有解释混合检索中 ES 与 KNN 结果的融合依据。",
        }
    ]
    payload["reference_answer"] = {
        "sections": [
            {
                "section_id": "section_1",
                "title": "检索融合策略",
                "content": "说明关键词检索、向量检索、重排和召回质量评估。",
                "addresses_loss_point_ids": ["loss_point_1"],
            }
        ]
    }
    result = _service(_PayloadTransport(payload)).generate_feedback_v1(_context())

    assert result.succeeded is True
    assert result.payload is not None
    loss_point = result.payload["loss_points"][0]
    assert loss_point["loss_point_id"] == "loss_point_1"
    assert loss_point["reason"] == "答案没有解释混合检索中 ES 与 KNN 结果的融合依据。"
    section = result.payload["reference_answer"]["sections"][0]
    assert section["section_id"] == "section_1"



def test_phase4_same_question_regression_and_fixed_loss_points_are_reported() -> None:
    payload = _generated_payload()
    payload["loss_points"] = [
        {
            "loss_point_id": "lp_recovery",
            "severity": "major",
            "deduction": 12,
            "reason": "没有说明补偿任务的触发条件和终止条件。",
        }
    ]
    payload["reference_answer"] = {
        "sections": [
            {
                "section_id": "ref_recovery",
                "title": "失败恢复",
                "content": "说明重试、补偿、幂等键、死信和人工介入边界。",
                "addresses_loss_point_ids": ["lp_recovery"],
            }
        ]
    }
    context = _context()
    context["answer_text"] = "本轮我补充失败补偿和幂等处理。"
    context["question_metadata"] = {"expected_answer_dimensions": ["失败补偿", "观测指标"]}
    context["same_question_answers"] = [
        {
            "answer_id": "answer_prev",
            "answer_round": 1,
            "answer_summary": "上一轮覆盖了观测指标，但缺少补偿任务。",
            "covered_points": ["观测指标"],
            "loss_point_ids": ["lp_observability"],
            "score_result": {"score_value": 80},
        }
    ]

    result = _service(_PayloadTransport(payload)).generate_feedback_v1(context)

    assert result.succeeded is True
    assert result.payload is not None
    change = result.payload["answer_change_analysis"]
    assert change["has_prior_attempts"] is True
    assert "观测指标" in change["regressed_points"]
    assert "lp_observability" in change["fixed_loss_points"]
    assert any(card["card_type"] == "answer_change" for card in result.payload["feedback_cards"])


def test_service_uses_llm_comparator_dimensions_and_does_not_rule_score_loss_points() -> None:
    payload = _generated_payload()
    payload["loss_points"][0]["deduction"] = 20
    payload["loss_points"][1]["deducted_points"] = 20

    result = _service(_PayloadTransport(payload)).generate_feedback_v1(_context())

    assert result.succeeded is True
    assert result.payload is not None
    assert result.payload["score_result"]["score_type"] == "polish_answer"
    assert result.payload["score_result"]["score_value"] == 76.6
    assert result.payload["score_result"]["scoring_basis"] == "progress_adaptive_llm_comparator_v1"
    assert result.payload["score_result"]["aggregation_method"] == "progress_weighted_dimension_scores"
    assert result.payload["score_result"]["progress_state_ref"] == "progress_node_reliability"
    assert result.payload["score_result"]["signals"] == ["weakness_detected", "progress_update"]
    assert result.payload["loss_points"][0]["deduction"] == 20
    assert "deduction" not in result.payload["loss_points"][1]


def test_service_missing_llm_comparator_score_fails_without_fallback_scoring() -> None:
    payload = _generated_payload()
    payload.pop("score_result")
    payload["loss_points"] = [
        {
            "loss_point_id": "lp_recovery",
            "severity": "critical",
            "reason": "没有说明恢复边界。",
        },
        {
            "loss_point_id": "lp_observability",
            "severity": "weirdness",
            "reason": "观察指标定义不完整，但 severity 未知。",
        },
    ]

    result = _service(_PayloadTransport(payload)).generate_feedback_v1(_context())

    assert result.succeeded is False
    assert result.payload is None
    assert result.validation_errors == ("score_result_required",)
    assert result.metadata["llm_output_validation_status"] == "invalid"


def test_phase4_missing_points_continue_same_question() -> None:
    payload = _generated_payload()
    context = _context()
    context["answer_text"] = "我只说明了 MQ 解耦。"
    context["question_metadata"] = {"expected_answer_dimensions": ["MQ 解耦", "幂等键", "观测指标"]}

    result = _service(_PayloadTransport(payload)).generate_feedback_v1(context)

    assert result.succeeded is True
    assert result.payload is not None
    assert result.payload["next_recommended_actions"][0] == "continue_same_question"


def test_phase4_next_action_regression_retries_same_question() -> None:
    payload = _generated_payload()
    context = _context()
    context["answer_text"] = "本轮补充了失败补偿。"
    context["question_metadata"] = {"expected_answer_dimensions": ["失败补偿"]}
    context["same_question_answers"] = [
        {
            "answer_id": "answer_prev",
            "covered_points": ["观测指标"],
            "score_result": {"score_value": 80},
        }
    ]

    result = _service(_PayloadTransport(payload)).generate_feedback_v1(context)

    assert result.succeeded is True
    assert result.payload is not None
    assert result.payload["next_recommended_actions"] == [
        "retry_same_question_preserve_regressed_points"
    ]


def test_phase4_asset_update_candidates_are_forced_to_user_confirmation() -> None:
    payload = _generated_payload()
    payload["project_asset_update_candidates"][0]["user_confirmation_required"] = False

    result = _service(_PayloadTransport(payload)).generate_feedback_v1(_context())

    assert result.succeeded is True
    assert result.payload is not None
    assert "project_asset_update_candidates" not in result.payload
    asset_candidate_cards = [
        card
        for card in result.payload["feedback_cards"]
        if card.get("card_type") == "asset_update_candidates"
    ]
    assert asset_candidate_cards
    assert asset_candidate_cards[0]["payload"][0]["user_confirmation_required"] is True
    assert "project_asset_candidate_user_confirmation_required" in result.payload["feedback_metadata"][
        "validation_warnings"
    ]


def test_phase4_required_fields_can_be_enforced_by_validator() -> None:
    _, errors = validate_final_feedback_payload(_generated_payload())

    assert "feedback_final_required_fields_missing" in errors

def _contains_forbidden_key(value: object) -> bool:
    forbidden = {
        "raw_prompt",
        "system_prompt",
        "developer_prompt",
        "completion",
        "raw_completion",
        "full_completion",
        "completion_text",
        "reasoning_content",
        "provider_payload",
        "raw_provider",
        "raw_provider_payload",
        "provider_response",
        "raw_provider_response",
        "full_answer",
        "full_asset_body",
        "api_key",
        "token",
        "secret",
        "cookie",
    }
    if isinstance(value, dict):
        return any(str(key).lower() in forbidden or _contains_forbidden_key(nested) for key, nested in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_key(item) for item in value)
    return False
