from __future__ import annotations

from typing import Any

from app.application.polish.feedback_models import (
    FeedbackCandidatePayload,
    FeedbackFinalPayload,
)
from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_CANDIDATE_PAYLOAD_FIELDS,
    POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
)


def _candidate_payload() -> dict[str, Any]:
    return {
        "feedback_text": "回答覆盖了 MQ 解耦，但恢复边界还不够完整。",
        "answer_summary": "候选人说明了队列、幂等和重试任务。",
        "score_result": {
            "score_type": "polish_answer",
            "score_value": 82,
            "dimension_scores": [
                {"dimension": "correctness", "score": 88, "rationale": "方向正确。"},
                {"dimension": "depth", "score": 80, "rationale": "细节基本完整。"},
                {"dimension": "tradeoff_reasoning", "score": 76, "rationale": "取舍略少。"},
                {"dimension": "structure", "score": 84, "rationale": "结构清楚。"},
                {"dimension": "engineering_awareness", "score": 82, "rationale": "工程边界基本覆盖。"},
            ],
        },
        "score_reasoning": [
            {"dimension": "reliability", "rationale": "恢复停止条件仍不明确。"},
        ],
        "loss_points": [
            {
                "loss_point_id": "lp_recovery",
                "severity": "major",
                "reason": "缺少恢复停止条件。",
            }
        ],
        "reference_answer": {
            "sections": [
                {
                    "section_id": "ref_recovery",
                    "title": "失败恢复",
                    "content": "说明重试、死信、补偿和人工介入边界。",
                    "addresses_loss_point_ids": ["lp_recovery"],
                }
            ]
        },
        "same_question_effect": {
            "trend": "improved",
            "improved_points": ["补充了幂等键"],
            "repeated_loss_point_ids": [],
            "regressed_points": [],
            "next_retry_focus": [],
            "score_delta": 4,
        },
        "project_asset_update_candidates": [
            {
                "candidate_type": "project_asset_update_candidate",
                "candidate_ref": "asset_candidate_001",
                "user_confirmation_required": True,
                "summary": "补充失败恢复素材。",
            }
        ],
        "low_confidence_flags": [],
        "evidence_refs": ["resume_project_payment"],
    }


def test_feedback_candidate_model_normalizes_loss_point_id_alias() -> None:
    payload = _candidate_payload()
    payload["loss_points"][0].pop("loss_point_id")
    payload["loss_points"][0]["id"] = "lp_recovery"

    candidate = FeedbackCandidatePayload.model_validate(payload)

    assert candidate.loss_points[0].loss_point_id == "lp_recovery"


def test_feedback_candidate_model_normalizes_loss_point_loss_id_alias() -> None:
    payload = _candidate_payload()
    payload["loss_points"][0].pop("loss_point_id")
    payload["loss_points"][0]["loss_id"] = "lp_recovery"

    candidate = FeedbackCandidatePayload.model_validate(payload)

    assert candidate.loss_points[0].loss_point_id == "lp_recovery"


def test_feedback_candidate_model_normalizes_loss_point_description_alias() -> None:
    payload = _candidate_payload()
    payload["loss_points"][0].pop("reason")
    payload["loss_points"][0]["description"] = "缺少恢复停止条件。"

    candidate = FeedbackCandidatePayload.model_validate(payload)

    assert candidate.loss_points[0].reason == "缺少恢复停止条件。"


def test_feedback_candidate_model_normalizes_reference_section_id_alias() -> None:
    payload = _candidate_payload()
    section = payload["reference_answer"]["sections"][0]
    section.pop("section_id")
    section["id"] = "ref_recovery"

    candidate = FeedbackCandidatePayload.model_validate(payload)

    assert candidate.reference_answer.sections[0].section_id == "ref_recovery"


def test_feedback_candidate_model_accepts_reference_section_id_canonical() -> None:
    candidate = FeedbackCandidatePayload.model_validate(_candidate_payload())

    assert candidate.reference_answer.sections[0].section_id == "ref_recovery"


def test_feedback_candidate_model_generates_missing_reference_section_title() -> None:
    payload = _candidate_payload()
    payload["reference_answer"]["sections"][0].pop("title")

    candidate = FeedbackCandidatePayload.model_validate(payload)

    assert candidate.reference_answer.sections[0].title == "参考回答 1"


def test_feedback_candidate_model_generates_missing_reference_section_id() -> None:
    payload = _candidate_payload()
    payload["reference_answer"]["sections"][0].pop("section_id")

    candidate = FeedbackCandidatePayload.model_validate(payload)

    assert candidate.reference_answer.sections[0].section_id == "section_1"


def test_feedback_candidate_model_normalizes_same_question_effect_string() -> None:
    payload = _candidate_payload()
    payload["same_question_effect"] = "unchanged"

    candidate = FeedbackCandidatePayload.model_validate(payload)

    assert candidate.same_question_effect is not None
    assert candidate.same_question_effect.trend == "unchanged"
    assert candidate.same_question_effect.improved_points == []


def test_feedback_candidate_model_missing_score_reasoning_is_warning_not_error() -> None:
    payload = _candidate_payload()
    payload.pop("score_reasoning")

    candidate = FeedbackCandidatePayload.model_validate(payload)

    assert candidate.score_reasoning == []
    assert "score_reasoning_missing" in candidate.validation_warnings


def test_feedback_candidate_model_strips_provider_metadata_fields() -> None:
    payload = _candidate_payload()
    payload.update(
        {
            "model_name": "deepseek-chat",
            "prompt_version": "provider_prompt.v1",
            "provider_status": "called",
            "provider_model": "deepseek-chat",
            "provider_validation_status": "valid",
            "llm_called": True,
            "request_id": "req_001",
            "trace_id": "trace_001",
            "trace_refs": ["trace_provider_001"],
            "raw_io_ref": "raw_001",
        }
    )

    candidate = FeedbackCandidatePayload.model_validate(payload)
    dumped = candidate.model_dump(mode="json", exclude_none=True)

    for field_name in (
        "model_name",
        "prompt_version",
        "schema_id",
        "schema_version",
        "provider_status",
        "provider_model",
        "provider_validation_status",
        "llm_called",
        "request_id",
        "trace_id",
        "trace_refs",
        "raw_io_ref",
    ):
        assert field_name not in dumped


def test_feedback_candidate_field_constant_is_derived_from_model_fields() -> None:
    assert set(POLISH_FEEDBACK_CANDIDATE_PAYLOAD_FIELDS) == set(FeedbackCandidatePayload.model_fields)


def test_feedback_final_payload_model_validates_service_payload() -> None:
    payload = {
        "schema_id": POLISH_FEEDBACK_FINAL_SCHEMA_ID,
        "schema_version": POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
        "status": "generated",
        "contract_ids": ["P-POLISH-003", "P-POLISH-004", "P-POLISH-005"],
        "feedback_id": "feedback_001",
        "feedback_text": "回答覆盖了核心方向。",
        "answer_summary": "候选人说明了队列和幂等。",
        "score_result": {"score_type": "polish_answer", "score_value": 82},
        "loss_points": [],
        "reference_answer": {"sections": [{"section_id": "ref_ok", "title": "参考", "content": "参考答案。", "addresses_loss_point_ids": []}]},
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
        "low_confidence_flags": [],
        "trace_refs": ["trace_provider_001"],
        "feedback_metadata": {"prompt_version": "polish_feedback_agent_prompt.v1"},
    }

    final_payload = FeedbackFinalPayload.model_validate(payload)

    assert final_payload.feedback_text == "回答覆盖了核心方向。"
    assert final_payload.reference_answer.sections[0].section_id == "ref_ok"
