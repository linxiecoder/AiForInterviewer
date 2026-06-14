from __future__ import annotations

from typing import Any

from app.application.llm.types import LlmTransportRequest, LlmTransportResult
from app.application.polish.feedback_generation_service import FeedbackGenerationService
from app.domain.shared.enums import ConfidenceLevel, ValidationStatus


def _context() -> dict[str, Any]:
    return {
        "owner_id": "owner_001",
        "actor_id": "user_001",
        "session_id": "sess_001",
        "question_id": "question_001",
        "answer_id": "answer_001",
        "question_text": "如何设计订单异步处理并保证失败可恢复？",
        "answer_text": "我会用消息队列解耦，并用幂等键、重试任务和告警恢复失败消息。",
        "answer_round": 2,
        "polish_theme": "可靠性设计",
        "progress_node_ref": "progress_node_reliability",
        "evidence_refs": ["resume_project_payment"],
        "same_question_answers": [],
        "job_snapshot": {"requirements": ["可靠性设计"]},
        "resume_snapshot": {"projects": ["支付系统"]},
        "progress_node_snapshot": {"node_ref": "progress_node_reliability", "title": "可靠性"},
        "progress_state": {
            "progress_state_ref": "progress_node_reliability",
            "current_priority": {
                "progress_node_ref": "progress_node_reliability",
                "title": "可靠性",
                "expected_capability": "补齐失败恢复和观测边界。",
            },
            "weak_skill_refs": ["recovery_boundaries", "observability"],
            "strong_skill_refs": ["queue_decoupling"],
            "node_states": [{"progress_node_ref": "progress_node_reliability", "status": "in_progress"}],
        },
    }


def _adaptive_score_result() -> dict[str, Any]:
    return {
        "score_type": "polish_answer",
        "score_value": 1,
        "progress_state_ref": "progress_node_reliability",
        "reasoning": "ProgressState 显示 recovery_boundaries 和 observability 仍需强化。",
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
                    "adaptive_weight": 0.24,
                    "progress_basis": ["weak_skill:recovery_boundaries"],
                    "anchor_refs": ["anchor_depth"],
                },
                {
                    "dimension": "tradeoff_reasoning",
                    "adaptive_weight": 0.20,
                    "progress_basis": ["weak_skill:observability"],
                    "anchor_refs": ["anchor_tradeoff_reasoning"],
                },
                {
                    "dimension": "structure",
                    "adaptive_weight": 0.14,
                    "progress_basis": ["strong_skill:queue_decoupling"],
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
                "score": 86,
                "adaptive_weight": 0.16,
                "progress_focus": ["progress_node_reliability"],
                "rationale": "方向正确。",
            },
            {
                "dimension": "depth",
                "score": 74,
                "adaptive_weight": 0.24,
                "progress_focus": ["progress_node_reliability"],
                "rationale": "恢复边界展开不足。",
            },
            {
                "dimension": "tradeoff_reasoning",
                "score": 70,
                "adaptive_weight": 0.20,
                "progress_focus": ["progress_node_reliability"],
                "rationale": "取舍不足。",
            },
            {
                "dimension": "structure",
                "score": 82,
                "adaptive_weight": 0.14,
                "progress_focus": ["progress_node_reliability"],
                "rationale": "表达结构清楚。",
            },
            {
                "dimension": "engineering_awareness",
                "score": 78,
                "adaptive_weight": 0.26,
                "progress_focus": ["progress_node_reliability"],
                "rationale": "有工程意识但观测不足。",
            },
        ],
        "adaptive_insights": {
            "weak_skills": ["recovery_boundaries", "observability"],
            "strong_skills": ["queue_decoupling"],
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


def _recoverable_candidate() -> dict[str, Any]:
    return {
        "feedback_text": "回答有可展示反馈：方向正确，但恢复边界还要补充。",
        "answer_summary": "候选人说明了队列、幂等、重试和告警。",
        "score_result": _adaptive_score_result(),
        "loss_points": [
            {
                "id": "lp_recovery",
                "severity": "major",
                "description": "没有说明重试终止条件和死信处理。",
            }
        ],
        "reference_answer": {
            "sections": [
                {
                    "id": "ref_recovery",
                    "title": "失败恢复",
                    "content": "说明重试、死信、补偿、幂等和人工介入边界。",
                    "addresses_loss_point_ids": ["lp_recovery"],
                }
            ]
        },
        "same_question_effect": "unchanged",
        "low_confidence_flags": [],
        "evidence_refs": ["resume_project_payment"],
        "model_name": "deepseek-chat",
        "prompt_version": "provider_prompt.v1",
        "provider_status": "called",
        "provider_model": "deepseek-chat",
        "provider_validation_status": "valid",
        "llm_called": True,
        "request_id": "req_001",
        "trace_id": "trace_001",
        "raw_io_ref": "raw_001",
    }


class _PayloadTransport:
    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result
        self.requests: list[LlmTransportRequest] = []

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        self.requests.append(request)
        return LlmTransportResult(
            result=self.result,
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.MEDIUM,
            low_confidence_flags=(),
            trace_refs=("trace_provider_001",),
            evidence_refs=("evidence_provider_001",),
            metadata={
                "model_name": "deepseek-chat",
                "provider_status": "called",
                "request_id": "req_001",
                "trace_id": "trace_001",
                "raw_io_ref": "raw_001",
            },
        )


def test_feedback_pipeline_strips_provider_metadata_and_generates_recoverable_candidate() -> None:
    result = FeedbackGenerationService(llm_transport=_PayloadTransport(_recoverable_candidate())).generate_feedback_v1(_context())

    assert result.succeeded is True
    assert result.payload is not None
    assert result.payload["status"] in {"generated", "partial"}
    assert result.payload["feedback_text"] == "回答有可展示反馈：方向正确，但恢复边界还要补充。"
    assert result.payload["loss_points"][0]["loss_point_id"] == "lp_recovery"
    assert result.payload["loss_points"][0]["reason"] == "没有说明重试终止条件和死信处理。"
    assert result.payload["reference_answer"]["sections"][0]["section_id"] == "ref_recovery"
    assert result.payload["score_result"]["score_type"] == "polish_answer"
    assert result.payload["reference_answer"]["sections"]
    assert result.metadata["provider_status"] == "called"
    for retired_error in (
        "feedback_candidate_unknown_fields",
        "loss_point_id_required",
        "same_question_effect_fields_invalid",
        "score_reasoning_required",
        "reference_answer_section_id_required",
    ):
        assert retired_error not in result.validation_errors


def test_feedback_pipeline_generates_recoverable_candidate_when_reference_title_missing() -> None:
    payload = _recoverable_candidate()
    payload["reference_answer"]["sections"][0].pop("title")

    result = FeedbackGenerationService(llm_transport=_PayloadTransport(payload)).generate_feedback_v1(_context())

    assert result.succeeded is True
    assert result.payload is not None
    assert result.payload["status"] in {"generated", "partial"}
    section = result.payload["reference_answer"]["sections"][0]
    assert section["section_id"] == "ref_recovery"
    assert section["title"] == "参考回答 1"
    assert section["content"] == "说明重试、死信、补偿、幂等和人工介入边界。"
    assert "reference_answer_sections_invalid" not in result.validation_errors


def test_feedback_pipeline_passes_normalized_candidate_to_core_rules(monkeypatch: Any) -> None:
    from app.application.polish import feedback_generation_service
    from app.application.polish.feedback_rules import apply_feedback_core_rules

    seen_payloads: list[dict[str, Any]] = []
    seen_contexts: list[object] = []

    def spy_apply_feedback_core_rules(payload: dict[str, Any], context: object) -> dict[str, Any]:
        seen_payloads.append(payload)
        seen_contexts.append(context)
        return apply_feedback_core_rules(payload, context)

    monkeypatch.setattr(feedback_generation_service, "apply_feedback_core_rules", spy_apply_feedback_core_rules)

    result = FeedbackGenerationService(llm_transport=_PayloadTransport(_recoverable_candidate())).generate_feedback_v1(_context())

    assert result.succeeded is True
    assert seen_payloads
    assert seen_contexts
    context_seen_by_rules = seen_contexts[0]
    assert isinstance(context_seen_by_rules, dict)
    assert context_seen_by_rules["structured_answer"]["parse_status"] == "parsed"
    assert context_seen_by_rules["answer_text"] != _context()["answer_text"]
    assert "Claims:" in context_seen_by_rules["answer_text"]
    candidate_seen_by_rules = seen_payloads[0]
    assert candidate_seen_by_rules["loss_points"][0]["loss_point_id"] == "lp_recovery"
    assert candidate_seen_by_rules["loss_points"][0]["reason"] == "没有说明重试终止条件和死信处理。"
    assert candidate_seen_by_rules["reference_answer"]["sections"][0]["section_id"] == "ref_recovery"
    assert isinstance(candidate_seen_by_rules["same_question_effect"], dict)
    assert candidate_seen_by_rules["score_reasoning"] == []
    for metadata_field in ("model_name", "provider_status", "request_id", "trace_id", "raw_io_ref"):
        assert metadata_field not in candidate_seen_by_rules
