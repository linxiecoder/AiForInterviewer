from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.application.llm.types import LlmTransportRequest, LlmTransportResult
from app.application.polish.feedback_generation_service import FeedbackGenerationService
from app.domain.shared.enums import ConfidenceLevel, ValidationStatus


acceptance_test_matrix: dict[str, dict[str, Any]] = {
    "AC-001": {
        "semantic": "same_answer_stability",
        "threshold_pending": {
            "total_score_max_delta": 5.0,
            "dimension_score_1_to_5_max_delta": 0.3,
        },
    },
    "AC-002": {
        "semantic": "improvement_trend",
        "threshold_pending": {"trend_window_runs": 10},
    },
    "AC-003": {
        "semantic": "reference_answer_replay",
        # Step4 fixture guardrail only; OQ-007/OQ-008 remain open and this is not a final product threshold.
        "threshold_pending": {"replay_score_floor": 90.0},
    },
    "AC-012": {"semantic": "failed_generation_must_not_expose_success"},
    **{
        candidate_id: {"status": "Deferred/Open Question", "threshold_pending": True}
        for candidate_id in ("C-049", "C-050", "C-051", "C-052", "C-053", "C-054")
    },
    **{
        open_question_id: {"status": "Open Question", "threshold_pending": True}
        for open_question_id in ("OQ-007", "OQ-008")
    },
}


class AcceptanceDeterministicTransport:
    """Scripted acceptance-test transport; not evidence of real provider quality."""

    def __init__(self, analysis_payloads: list[dict[str, Any]], *, fail_generation: bool = False) -> None:
        self._analysis_payloads = [deepcopy(payload) for payload in analysis_payloads]
        self._fail_generation = fail_generation
        self._analysis_calls = 0
        self.requests: list[LlmTransportRequest] = []

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        self.requests.append(request)
        if self._fail_generation:
            raise TimeoutError("acceptance deterministic transport timed out")
        payload = self._projection_payload(request) if request.stage == "json_projection" else self._analysis_payload()
        return LlmTransportResult(
            result=payload,
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.MEDIUM,
            low_confidence_flags=(),
            trace_refs=(f"trace_acceptance_{len(self.requests):03d}",),
            evidence_refs=(f"evidence_acceptance_{len(self.requests):03d}",),
            metadata={"stage": request.stage, "finish_reason": "stop"},
        )

    def _analysis_payload(self) -> dict[str, Any]:
        index = min(self._analysis_calls, len(self._analysis_payloads) - 1)
        self._analysis_calls += 1
        return deepcopy(self._analysis_payloads[index])

    @staticmethod
    def _projection_payload(request: LlmTransportRequest) -> dict[str, Any]:
        server_facts = request.evidence_bundle.get("server_facts")
        assert isinstance(server_facts, dict), "AC-012 projection requires server facts"
        default_payload = server_facts.get("default_final_payload")
        assert isinstance(default_payload, dict), "AC-012 projection cannot invent success payload"
        return deepcopy(default_payload)


def context(
    *,
    answer_id: str = "answer_acceptance_001",
    answer_text: str = "我会用消息队列异步解耦，并说明失败恢复、幂等键、观测指标和人工介入边界。",
    previous_answers: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "owner_id": "owner_acceptance",
        "actor_id": "actor_acceptance",
        "session_id": "session_acceptance",
        "question_id": "question_acceptance",
        "answer_id": answer_id,
        "question_text": "请说明你如何设计订单异步处理链路，并保证失败可恢复。",
        "answer_text": answer_text,
        "evidence_refs": ["resume_project_payment", "job_requirement_reliability"],
        "same_question_answers": previous_answers or [],
        "question_metadata": {
            "expected_answer_dimensions": ["异步解耦", "失败恢复", "幂等键", "观测指标", "人工介入边界"],
        },
        "progress_node_snapshot": {
            "node_ref": "progress_node_reliability",
            "title": "可靠性设计",
            "expected_capability": "说明失败恢复、幂等和观测指标。",
        },
        "progress_state": {
            "progress_state_ref": "progress_node_reliability",
            "current_priority": {
                "progress_node_ref": "progress_node_reliability",
                "title": "可靠性设计",
                "expected_capability": "说明失败恢复、幂等和观测指标。",
            },
            "weak_skill_refs": ["failure_recovery", "tradeoff_reasoning", "observability"],
            "strong_skill_refs": ["structured_reasoning"],
        },
    }


def candidate_payload(score: float, *, loss_ids: list[str] | None = None) -> dict[str, Any]:
    active_loss_ids = loss_ids if loss_ids is not None else ["lp_recovery", "lp_observability"]
    return {
        "feedback_text": "回答覆盖异步解耦，仍需明确失败恢复、幂等和观测指标。",
        "answer_summary": "候选人说明了异步解耦和失败重试。",
        "score_result": _score_result(score),
        "score_reasoning": [{"dimension": "reliability", "rationale": "按恢复链路完整度评分。"}],
        "loss_points": [_loss_point(loss_id) for loss_id in active_loss_ids],
        "reference_answer": _reference_answer(active_loss_ids),
        "answer_coverage": {
            "covered_points": [
                "异步解耦",
                "失败恢复",
                "幂等键",
                "观测指标",
                "人工介入边界",
                "说明失败恢复、幂等和观测指标。",
            ],
            "missing_points": [],
            "weak_points": [],
            "contradicted_points": [],
        },
    }


def _score_result(score: float) -> dict[str, Any]:
    dimensions = ["correctness", "depth", "tradeoff_reasoning", "structure", "engineering_awareness"]
    return {
        "score_type": "polish_answer",
        "score_value": score,
        "progress_state_ref": "progress_node_reliability",
        "reasoning": "基于 ProgressState 中的可靠性、权衡和观测弱项进行评分。",
        "adaptive_rubric": {
            "rubric_version": "polish_answer.progress_adaptive_rubric.v1",
            "progress_state_ref": "progress_node_reliability",
            "dimensions": [{"dimension": dimension, "adaptive_weight": 0.2} for dimension in dimensions],
        },
        "dimension_scores": [
            {
                "dimension": dimension,
                "score": score,
                "adaptive_weight": 0.2,
                "progress_focus": ["progress_node_reliability"],
                "rationale": "该维度跟随验收样本分数。",
            }
            for dimension in dimensions
        ],
        "adaptive_insights": {
            "weak_skills": ["failure_recovery", "tradeoff_reasoning", "observability"],
            "strong_skills": ["structured_reasoning"],
            "unstable_skills": ["reliability"],
            "overweighted_skills": ["depth", "engineering_awareness"],
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


def _loss_point(loss_id: str) -> dict[str, Any]:
    return {"loss_point_id": loss_id, "severity": "major", "deduction": 8, "reason": f"{loss_id} 仍需补足。"}


def _reference_answer(loss_ids: list[str]) -> dict[str, Any]:
    return {
        "sections": [
            {
                "section_id": "ref_recovery",
                "title": "失败恢复",
                "content": "说明消息队列异步解耦、失败恢复、重试、补偿、幂等键、死信和人工介入边界。",
                "addresses_loss_point_ids": ["lp_recovery"] if "lp_recovery" in loss_ids else [],
            },
            {
                "section_id": "ref_observability",
                "title": "观测指标",
                "content": "说明观测指标、消息堆积、失败率、恢复耗时和告警阈值。",
                "addresses_loss_point_ids": ["lp_observability"] if "lp_observability" in loss_ids else [],
            },
        ]
    }


def generate_payload(service: FeedbackGenerationService, value: dict[str, Any]) -> dict[str, Any]:
    result = service.generate_feedback_v1(value)
    assert result.succeeded is True, result.validation_errors
    assert result.payload is not None
    return result.payload


def score_value(payload: dict[str, Any]) -> float:
    score_result = payload["score_result"]
    assert isinstance(score_result, dict)
    score = score_result["score_value"]
    assert isinstance(score, (int, float))
    return float(score)


def dimension_scores_1_to_5(payload: dict[str, Any]) -> list[float]:
    score_result = payload["score_result"]
    assert isinstance(score_result, dict)
    dimension_scores = score_result["dimension_scores"]
    assert isinstance(dimension_scores, list)
    return [float(item["score"]) / 20 for item in dimension_scores if isinstance(item, dict)]


def loss_point_ids(payload: dict[str, Any]) -> set[str]:
    loss_points = payload["loss_points"]
    assert isinstance(loss_points, list)
    return {str(item["loss_point_id"]) for item in loss_points if isinstance(item, dict)}


def addressed_loss_point_ids(payload: dict[str, Any]) -> set[str]:
    reference_answer = payload["reference_answer"]
    assert isinstance(reference_answer, dict)
    sections = reference_answer["sections"]
    assert isinstance(sections, list)
    return {
        str(loss_id)
        for section in sections
        if isinstance(section, dict)
        for loss_id in section["addresses_loss_point_ids"]
    }


def reference_answer_text(payload: dict[str, Any]) -> str:
    reference_answer = payload["reference_answer"]
    assert isinstance(reference_answer, dict)
    sections = reference_answer["sections"]
    assert isinstance(sections, list)
    return " ".join(str(section["content"]) for section in sections if isinstance(section, dict))
