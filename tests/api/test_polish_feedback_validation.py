from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
)
from app.application.polish.feedback_validation import (
    validate_feedback_candidate_payload,
    validate_final_feedback_payload,
)


def _candidate_payload() -> dict[str, Any]:
    return {
        "feedback_text": "回答清晰地覆盖了核心方案和失败恢复。",
        "answer_summary": "候选人在异步链路上给出了可验证的补偿策略。",
        "score_reasoning": [
            {
                "dimension": "architecture",
                "rationale": "结构完整，覆盖 MQ、重试与幂等。",
            }
        ],
        "loss_points": [
            {
                "loss_point_id": "lp_observability",
                "severity": "major",
                "deduction": 12,
                "reason": "缺少失败恢复指标。",
                "evidence_refs": ["resume_observability"],
            }
        ],
        "reference_answer": {
            "sections": [
                {
                    "section_id": "ref_observability",
                    "title": "观测",
                    "content": "说明失败率、堆积量和恢复耗时的告警边界。",
                    "addresses_loss_point_ids": ["lp_observability"],
                }
            ]
        },
        "same_question_effect": {
            "improved_points": ["更关注边界指标"],
            "repeated_loss_point_ids": [],
            "regressed_points": [],
            "next_retry_focus": ["补充恢复耗时"],
        },
        "project_asset_update_candidates": [
            {
                "candidate_type": "project_asset_update_candidate",
                "candidate_ref": "candidate_project_asset_001",
                "user_confirmation_required": True,
                "target_asset_ref": {
                    "resource_type": "asset",
                    "resource_id": "asset_payment",
                },
                "summary": "补充支付项目一致性治理素材。",
            }
        ],
        "low_confidence_flags": [],
        "evidence_refs": ["resume_project_payment"],
    }


def _final_payload() -> dict[str, Any]:
    return {
        "schema_id": POLISH_FEEDBACK_FINAL_SCHEMA_ID,
        "schema_version": POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
        "status": "generated",
        "contract_ids": ["P-POLISH-003", "P-POLISH-004", "P-POLISH-005"],
        "feedback_id": "feedback_001",
        "feedback_text": "回答覆盖了失败恢复的关键边界。",
        "answer_summary": "候选人说明了重试、补偿和幂等策略。",
        "score_result": {"score_type": "polish_answer", "score_value": 82},
        "loss_points": [
            {
                "loss_point_id": "lp_observability",
                "severity": "major",
                "deduction": 12,
                "reason": "缺少失败恢复指标。",
            }
        ],
        "reference_answer": {
            "sections": [
                {
                    "section_id": "ref_observability",
                    "title": "观测",
                    "content": "说明失败率、堆积量和恢复耗时的告警边界。",
                    "addresses_loss_point_ids": ["lp_observability"],
                }
            ]
        },
        "asset_consistency_check": {
            "status": "consistent",
            "checked_asset_refs": ["asset_payment"],
            "conflicts": [],
            "unsupported_claims": [],
            "user_clarification_required": False,
        },
        "answer_coverage": {
            "expected_points": ["可观测性", "幂等"],
            "covered_points": ["可观测性"],
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
            "trend": "improved",
        },
        "feedback_cards": [
            {"card_type": "asset_consistency", "status": "generated", "payload": {"status": "consistent"}},
            {"card_type": "overall", "status": "generated", "payload": {"summary": "核心点通过"}},
            {"card_type": "answer_coverage", "status": "generated", "payload": {}},
            {"card_type": "loss_points", "status": "generated", "payload": []},
            {"card_type": "next_actions", "status": "generated", "payload": {"next": "review_reference_answer"}},
        ],
        "next_recommended_actions": ["review_reference_answer"],
        "low_confidence_flags": [],
        "trace_refs": [{"resource_type": "llm_trace", "resource_id": "trace_001"}],
        "feedback_metadata": {"prompt_version": "polish_feedback_agent_prompt.v1"},
    }


def test_validate_feedback_candidate_payload_accepts_valid_payload() -> None:
    payload = _candidate_payload()

    normalized, errors = validate_feedback_candidate_payload(payload)

    assert errors == ()
    assert normalized is not None
    assert normalized["feedback_text"]
    assert len(normalized["loss_points"]) == 1


def test_validate_feedback_candidate_payload_accepts_phase4_fields_without_unknown_error() -> None:
    payload = _candidate_payload()
    payload.update(
        {
            "schema_id": POLISH_FEEDBACK_FINAL_SCHEMA_ID,
            "schema_version": POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
            "status": "generated",
            "contract_ids": ["P-POLISH-003", "P-POLISH-004", "P-POLISH-005"],
            "score_result": {"score_type": "polish_answer", "score_value": 82},
            "explicit_score": 76,
            "implicit_score": 88,
            "scoring_dimensions": [{"dimension": "reliability", "score": 82}],
            "knowledge_points": ["消息重试"],
            "technical_principles": ["幂等"],
            "asset_consistency_check": {"status": "consistent"},
            "answer_coverage": {"covered_points": ["MQ"]},
            "answer_change_analysis": {"trend": "unchanged"},
            "feedback_cards": [{"card_type": "overall", "payload": {}}],
            "session_similarity_check": {"status": "not_applicable"},
            "next_recommended_actions": ["review_reference_answer"],
            "trace_refs": ["trace_provider_001"],
            "feedback_metadata": {"provider": "deepseek-v4-pro"},
        }
    )

    normalized, errors = validate_feedback_candidate_payload(payload)

    assert normalized is not None
    assert "feedback_candidate_unknown_fields" not in errors
    assert errors == ()
    assert "score_result" not in normalized
    assert "feedback_metadata" not in normalized


def test_validate_feedback_candidate_payload_normalizes_loss_point_id_alias() -> None:
    payload = _candidate_payload()
    payload["loss_points"][0].pop("loss_point_id")
    payload["loss_points"][0]["id"] = "lp_observability"

    normalized, errors = validate_feedback_candidate_payload(payload)

    assert normalized is not None
    assert "loss_point_id_required" not in errors
    assert errors == ()
    assert normalized["loss_points"][0]["loss_point_id"] == "lp_observability"


def test_validate_feedback_candidate_payload_normalizes_same_question_effect_string() -> None:
    payload = _candidate_payload()
    payload["same_question_effect"] = "unchanged"

    normalized, errors = validate_feedback_candidate_payload(payload)

    assert normalized is not None
    assert "same_question_effect_fields_invalid" not in errors
    assert errors == ()
    assert normalized["same_question_effect"]["trend"] == "unchanged"


def test_validate_feedback_candidate_payload_rejects_server_generated_feedback_id() -> None:
    payload = _candidate_payload()
    payload["feedback_id"] = "feedback_from_provider_should_not_be_trusted"

    normalized, errors = validate_feedback_candidate_payload(payload)

    assert normalized is None
    assert any("forbidden" in error for error in errors)


def test_validate_feedback_candidate_payload_rejects_unsafe_fields() -> None:
    payload = _candidate_payload()
    payload["cookie"] = "should_not_exist"

    normalized, errors = validate_feedback_candidate_payload(payload)

    assert normalized is None
    assert any("forbidden" in error or "unsafe" in error for error in errors)


def test_validate_feedback_candidate_payload_requires_reference_sections_list() -> None:
    payload = _candidate_payload()
    payload["reference_answer"] = {"sections": "not-a-list"}

    normalized, errors = validate_feedback_candidate_payload(payload)

    assert normalized is None
    assert "reference_answer_sections_required" in errors


def test_validate_final_feedback_payload_accepts_valid_payload() -> None:
    payload = _final_payload()

    normalized, errors = validate_final_feedback_payload(payload)

    assert errors == ()
    assert normalized is not None
    assert normalized["schema_id"] == POLISH_FEEDBACK_FINAL_SCHEMA_ID
    for field in _final_payload():
        assert field in normalized

def _with_final_change(**changes: object) -> dict[str, Any]:
    payload = _final_payload()
    payload.update(changes)
    return payload


def test_validate_final_feedback_payload_rejects_unknown_top_level_fields() -> None:
    payload = _with_final_change(retired_field={"value": True}, old_single_contract="P-OLD-001")

    normalized, errors = validate_final_feedback_payload(payload)

    assert normalized is None
    assert "feedback_final_unknown_fields" in errors


def test_validate_final_feedback_payload_rejects_candidate_only_fields() -> None:
    payload = _with_final_change(
        project_asset_update_candidates=[
            {
                "candidate_type": "project_asset_update_candidate",
                "candidate_ref": "asset_candidate_001",
                "user_confirmation_required": True,
            }
        ],
        same_question_effect={"improved_points": []},
    )

    normalized, errors = validate_final_feedback_payload(payload)

    assert normalized is None
    assert "feedback_final_unknown_fields" in errors
