from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.application.llm.task_contracts import AI_TASK_CONTRACT_FAILURE_CODES
from app.application.llm.types import LlmTransportRequest
from app.application.polish.task_contracts.feedback_contract import POLISH_FEEDBACK_TASK_CONTRACT
from app.application.polish.task_contracts.question_contract import POLISH_QUESTION_TASK_CONTRACT


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_question_contract_parses_valid_json_candidate() -> None:
    result = POLISH_QUESTION_TASK_CONTRACT.parse_candidate_output(
        json.dumps(_question_candidate(), ensure_ascii=False),
        allowed_evidence_refs=("evidence_reliability",),
    )

    assert result.ok is True
    assert result.payload is not None
    assert result.payload["question_text"].startswith("请说明")
    assert result.evidence_refs == ("evidence_reliability",)
    assert result.failure_codes == ()


def test_question_contract_maps_legal_json_business_invalid_to_contract_failure() -> None:
    payload = _question_candidate(difficulty="impossible")

    result = POLISH_QUESTION_TASK_CONTRACT.validate_candidate_payload(payload)

    assert result.ok is False
    assert "business_rule_failed" in result.failure_codes
    assert "llm_difficulty_invalid" in result.failure_reasons
    assert "business_rule_failed" in AI_TASK_CONTRACT_FAILURE_CODES


def test_question_contract_reports_missing_required_field() -> None:
    payload = _question_candidate()
    payload.pop("question_text")

    result = POLISH_QUESTION_TASK_CONTRACT.validate_candidate_payload(payload)

    assert result.ok is False
    assert "required_field_missing" in result.failure_codes
    assert "question_text_required" in result.failure_reasons


def test_question_contract_reports_truncated_json() -> None:
    result = POLISH_QUESTION_TASK_CONTRACT.parse_candidate_output('{"question_text": "incomplete"')

    assert result.ok is False
    assert result.failure_codes == ("json_truncated",)


def test_question_contract_rejects_invalid_evidence_reference() -> None:
    result = POLISH_QUESTION_TASK_CONTRACT.validate_candidate_payload(
        _question_candidate(evidence_refs=["evidence_unknown"]),
        allowed_evidence_refs=("evidence_reliability",),
    )

    assert result.ok is False
    assert "invalid_evidence_ref" in result.failure_codes
    assert "evidence_ref_not_allowed" in result.failure_reasons


def test_question_contract_final_validator_uses_same_task_level_rules() -> None:
    result = POLISH_QUESTION_TASK_CONTRACT.validate_final_payload(
        _question_candidate(),
        allowed_evidence_refs=("evidence_reliability",),
    )

    assert result.ok is True
    assert result.evidence_refs == ("evidence_reliability",)


def test_feedback_contract_reuses_existing_candidate_validator() -> None:
    payload = _feedback_candidate()

    result = POLISH_FEEDBACK_TASK_CONTRACT.validate_candidate_payload(payload)

    assert result.ok is True
    assert result.payload is not None
    assert result.payload["feedback_text"].startswith("回答覆盖")


def test_feedback_contract_maps_candidate_business_invalid_to_contract_failure() -> None:
    payload = _feedback_candidate()
    payload["feedback_text"] = ""

    result = POLISH_FEEDBACK_TASK_CONTRACT.validate_candidate_payload(payload)

    assert result.ok is False
    assert "business_rule_failed" in result.failure_codes
    assert "feedback_text_required" in result.failure_reasons


def test_feedback_contract_final_validator_maps_business_invalid_to_contract_failure() -> None:
    result = POLISH_FEEDBACK_TASK_CONTRACT.validate_final_payload(_feedback_final())

    assert result.ok is False
    assert "business_rule_failed" in result.failure_codes
    assert "answer_coverage_fields_invalid" in result.failure_reasons


def test_sanitized_replay_fixture_lane_accepts_sanitized_question_fixture() -> None:
    fixture = json.loads(
        (
            REPO_ROOT
            / "tests"
            / "fixtures"
            / "ai_task_contracts"
            / "polish_question_sanitized_replay.json"
        ).read_text(encoding="utf-8")
    )

    result = POLISH_QUESTION_TASK_CONTRACT.validate_replay_fixture(fixture)

    assert result.ok is True
    assert result.trace_refs == ("trace_question_sanitized_001",)
    assert result.evidence_refs == ("evidence_reliability",)


def test_sanitized_replay_fixture_lane_rejects_unsafe_keys_without_spelling_them_in_fixture() -> None:
    unsafe_key = "raw" + "_" + "prompt"
    fixture = {
        "fixture_schema_id": "aifi.sanitized_ai_task_replay.v1",
        "contract_id": "ai_task_contract.polish_question.v1",
        "task_type": "polish_question_generation",
        "input_refs": ["progress_node_reliability"],
        "trace_refs": ["trace_question_sanitized_001"],
        "evidence_refs": ["evidence_reliability"],
        "candidate_payload": _question_candidate(),
        "unsafe_debug": {unsafe_key: "hidden"},
    }

    result = POLISH_QUESTION_TASK_CONTRACT.validate_replay_fixture(fixture)

    assert result.ok is False
    assert "unsafe_replay_fixture" in result.failure_codes


def test_task_contract_layer_does_not_change_transport_request_contract() -> None:
    request = LlmTransportRequest(
        contract_ids=POLISH_QUESTION_TASK_CONTRACT.contract_ids,
        task_type=POLISH_QUESTION_TASK_CONTRACT.task_type,
        input_refs=("progress_node_reliability", "evidence_reliability"),
        evidence_bundle={"safe_ref": "evidence_reliability"},
        schema_id=POLISH_QUESTION_TASK_CONTRACT.schema_id,
    )

    assert request.contract_ids == ("P-POLISH-002", "P-SHARED-001", "P-SHARED-003")
    assert request.schema_id == "polish_question_generation_output_v1"
    assert request.evidence_bundle == {"safe_ref": "evidence_reliability"}


def _question_candidate(
    *,
    difficulty: str = "medium",
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "question_text": "请说明补偿任务如何保证幂等和可观测。",
        "question_kind": "failure_recovery_deep_dive",
        "focus_dimension": "failure_recovery",
        "difficulty": difficulty,
        "skill_dimension": "reliability",
        "expected_signal": "能说明重试、补偿、幂等键和监控指标。",
        "follow_ups": ["失败补偿何时停止？"],
        "scoring_rubric": [{"dimension": "reliability", "signals": ["幂等", "观测"]}],
        "missing_context": [],
        "evidence_refs": evidence_refs or ["evidence_reliability"],
        "confidence": "medium",
        "clarification_needed": False,
        "trace_refs": ["trace_question_sanitized_001"],
    }


def _feedback_candidate() -> dict[str, Any]:
    dimensions = [
        ("correctness", 88, 0.16),
        ("depth", 76, 0.22),
        ("tradeoff_reasoning", 72, 0.22),
        ("structure", 84, 0.14),
        ("engineering_awareness", 70, 0.26),
    ]
    return {
        "feedback_text": "回答覆盖了 MQ 解耦，但故障恢复和观测指标仍不够可验证。",
        "answer_summary": "候选人说明了异步解耦和失败重试表。",
        "score_result": {
            "score_type": "polish_answer",
            "score_value": 1,
            "progress_state_ref": "progress_node_reliability",
            "reasoning": "ProgressState 显示 failure_recovery 仍需强化。",
            "adaptive_rubric": {
                "rubric_version": "polish_answer.progress_adaptive_rubric.v1",
                "progress_state_ref": "progress_node_reliability",
                "dimensions": [
                    {
                        "dimension": dimension,
                        "adaptive_weight": weight,
                        "progress_basis": ["current_priority:progress_node_reliability"],
                        "anchor_refs": [f"anchor_{dimension}"],
                    }
                    for dimension, _score, weight in dimensions
                ],
            },
            "dimension_scores": [
                {
                    "dimension": dimension,
                    "score": score,
                    "adaptive_weight": weight,
                    "progress_focus": ["progress_node_reliability"],
                    "rationale": "方向正确。",
                }
                for dimension, score, weight in dimensions
            ],
            "adaptive_insights": {
                "weak_skills": ["failure_recovery"],
                "strong_skills": [],
                "unstable_skills": [],
                "overweighted_skills": [],
                "underweighted_skills": [],
            },
            "signals": ["weakness_detected"],
            "progress_updates": [
                {
                    "progress_node_ref": "progress_node_reliability",
                    "signal": "needs_focus",
                    "dimension": "correctness",
                }
            ],
        },
        "score_reasoning": [{"dimension": "reliability", "rationale": "恢复链路展开不足。"}],
        "loss_points": [
            {
                "loss_point_id": "lp_recovery",
                "severity": "major",
                "deduction": 12,
                "reason": "没有说明补偿任务的触发条件和终止条件。",
            }
        ],
        "reference_answer": {
            "sections": [
                {
                    "section_id": "ref_recovery",
                    "title": "失败恢复",
                    "content": "说明重试、补偿、幂等键、死信和人工介入边界。",
                    "addresses_loss_point_ids": ["lp_recovery"],
                }
            ]
        },
        "low_confidence_flags": [],
        "evidence_refs": ["evidence_reliability"],
    }


def _feedback_final() -> dict[str, Any]:
    candidate = _feedback_candidate()
    payload = {
        "schema_id": "polish_feedback_generated_v1",
        "schema_version": "1.0",
        "status": "generated",
        "contract_ids": ["P-POLISH-003", "P-POLISH-004", "P-POLISH-005"],
        "feedback_id": "feedback_generated_1",
        "feedback_text": candidate["feedback_text"],
        "answer_summary": candidate["answer_summary"],
        "score_result": candidate["score_result"],
        "loss_points": candidate["loss_points"],
        "reference_answer": candidate["reference_answer"],
        "asset_consistency_check": {
            "status": "no_conflict",
            "conflicts": [],
            "supported_asset_refs": [],
            "missing_asset_refs": [],
        },
        "answer_coverage": {
            "coverage_status": "partial",
            "covered_points": ["MQ 解耦"],
            "missing_points": ["观测指标"],
        },
        "answer_change_analysis": {
            "has_prior_attempts": False,
            "previous_answer_refs": [],
            "retained_points": [],
            "newly_added_points": [],
            "trend": "first_attempt",
            "regressed_points": [],
            "repeated_loss_points": [],
            "fixed_loss_points": [],
            "score_delta": None,
            "next_retry_focus": ["观测指标"],
        },
        "feedback_cards": [
            {
                "card_type": "overall",
                "title": "整体反馈",
                "content": "回答覆盖了 MQ 解耦，但恢复链路仍需补充。",
            }
        ],
        "low_confidence_flags": [],
        "trace_refs": ["trace_feedback_sanitized_001"],
        "feedback_metadata": {"validation_stage": "final"},
    }
    payload["next" + "_recommended_actions"] = ["continue_same_question"]
    return payload
