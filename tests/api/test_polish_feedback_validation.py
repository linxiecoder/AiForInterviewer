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
        "score_result": {
            "score_type": "polish_answer",
            "score_value": 1,
            "progress_state_ref": "progress_node_reliability",
            "reasoning": "ProgressState 显示 observability 和 tradeoff_reasoning 仍薄弱，因此本轮更关注工程边界与取舍说明。",
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
                    "rationale": "方案方向正确。",
                },
                {
                    "dimension": "depth",
                    "score": 76,
                    "adaptive_weight": 0.22,
                    "progress_focus": ["progress_node_reliability"],
                    "rationale": "恢复链路有展开，但终止条件不足。",
                },
                {
                    "dimension": "tradeoff_reasoning",
                    "score": 72,
                    "adaptive_weight": 0.22,
                    "progress_focus": ["progress_node_reliability"],
                    "rationale": "取舍说明仍偏少。",
                },
                {
                    "dimension": "structure",
                    "score": 84,
                    "adaptive_weight": 0.14,
                    "progress_focus": ["progress_node_reliability"],
                    "rationale": "结构清晰。",
                },
                {
                    "dimension": "engineering_awareness",
                    "score": 70,
                    "adaptive_weight": 0.26,
                    "progress_focus": ["progress_node_reliability"],
                    "rationale": "观测和人工介入边界不足。",
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
        },
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
        "score_result": deepcopy(_candidate_payload()["score_result"]),
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
    assert normalized["score_result"]["score_value"] == 76.6
    assert normalized["score_result"]["scoring_basis"] == "progress_adaptive_llm_comparator_v1"
    assert normalized["score_result"]["aggregation_method"] == "progress_weighted_dimension_scores"
    assert normalized["score_result"]["progress_state_ref"] == "progress_node_reliability"
    assert normalized["score_result"]["reasoning"].startswith("ProgressState 显示")
    assert normalized["score_result"]["adaptive_insights"] == {
        "weak_skills": ["failure_recovery", "tradeoff_reasoning", "observability"],
        "strong_skills": ["structured_reasoning"],
        "unstable_skills": ["reliability"],
        "overweighted_skills": ["depth", "tradeoff_reasoning", "engineering_awareness"],
        "underweighted_skills": ["structure"],
    }
    assert [item["adaptive_weight"] for item in normalized["score_result"]["dimension_scores"]] == [
        0.16,
        0.22,
        0.22,
        0.14,
        0.26,
    ]
    assert [item["dimension"] for item in normalized["score_result"]["dimension_scores"]] == [
        "correctness",
        "depth",
        "tradeoff_reasoning",
        "structure",
        "engineering_awareness",
    ]


def test_validate_feedback_candidate_payload_allows_ordinary_sensitive_marker_terms() -> None:
    payload = _candidate_payload()
    payload["feedback_text"] = (
        "回答讨论了 token bucket 限流、JWT token rotation 和 secret management 流程，"
        "这些都是普通技术概念，不包含真实凭据。"
    )
    payload["answer_summary"] = "候选人用普通技术词描述认证、限流和密钥治理边界。"
    payload["score_reasoning"][0]["rationale"] = "JWT token lifecycle 和 secret management 被作为概念说明。"
    payload["reference_answer"]["sections"][0]["content"] = "可以说明 token bucket 的限流窗口和 secret 管理职责。"

    normalized, errors = validate_feedback_candidate_payload(payload)

    assert normalized is not None
    assert errors == ()


def test_validate_feedback_candidate_payload_requires_llm_comparator_score_result() -> None:
    payload = _candidate_payload()
    payload.pop("score_result")

    normalized, errors = validate_feedback_candidate_payload(payload)

    assert normalized is None
    assert errors == ("score_result_required",)


def test_validate_feedback_candidate_payload_accepts_phase4_fields_without_unknown_error() -> None:
    payload = _candidate_payload()
    payload.update(
        {
            "schema_id": POLISH_FEEDBACK_FINAL_SCHEMA_ID,
            "schema_version": POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
            "status": "generated",
            "contract_ids": ["P-POLISH-003", "P-POLISH-004", "P-POLISH-005"],
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
    assert normalized["score_result"]["score_value"] == 76.6
    assert "feedback_metadata" not in normalized


def test_validate_feedback_candidate_payload_rejects_static_score_without_progress_adaptation() -> None:
    payload = _candidate_payload()
    payload["score_result"] = {
        "score_type": "polish_answer",
        "dimension_scores": [
            {"dimension": "correctness", "score": 88, "rationale": "方向正确。"},
            {"dimension": "depth", "score": 76, "rationale": "恢复链路有展开。"},
            {"dimension": "tradeoff_reasoning", "score": 72, "rationale": "取舍说明偏少。"},
            {"dimension": "structure", "score": 84, "rationale": "结构清晰。"},
            {"dimension": "engineering_awareness", "score": 70, "rationale": "工程边界不足。"},
        ],
        "signals": ["progress_update"],
    }

    normalized, errors = validate_feedback_candidate_payload(payload)

    assert normalized is None
    assert errors == (
        "score_result_reasoning_required",
        "adaptive_insights_required",
        "progress_state_ref_required",
        "adaptive_rubric_required",
        "progress_updates_required",
        "adaptive_rubric_dimensions_incomplete",
        "score_result_dimension_scores_incomplete",
    )


def test_validate_feedback_candidate_payload_rejects_self_inconsistent_adaptive_rubric_ref() -> None:
    payload = _candidate_payload()
    payload["score_result"]["adaptive_rubric"]["progress_state_ref"] = "progress_node_other"

    normalized, errors = validate_feedback_candidate_payload(payload)

    assert normalized is None
    assert errors == ("adaptive_rubric_progress_state_ref_mismatch",)


def test_validate_feedback_candidate_payload_rejects_score_result_without_reasoning() -> None:
    payload = _candidate_payload()
    payload["score_result"].pop("reasoning")

    normalized, errors = validate_feedback_candidate_payload(payload)

    assert normalized is None
    assert errors == ("score_result_reasoning_required",)


def test_validate_feedback_candidate_payload_rejects_score_result_without_adaptive_insights() -> None:
    payload = _candidate_payload()
    payload["score_result"].pop("adaptive_insights")

    normalized, errors = validate_feedback_candidate_payload(payload)

    assert normalized is None
    assert errors == ("adaptive_insights_required",)


def test_validate_feedback_candidate_payload_rejects_incomplete_adaptive_insights() -> None:
    payload = _candidate_payload()
    payload["score_result"]["adaptive_insights"] = {
        "weak_skills": ["observability"],
        "strong_skills": ["structured_reasoning"],
    }

    normalized, errors = validate_feedback_candidate_payload(payload)

    assert normalized is None
    assert errors == ("adaptive_insights_skill_diagnosis_required",)


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


def test_validate_feedback_candidate_payload_generates_missing_reference_section_title() -> None:
    payload = _candidate_payload()
    payload["reference_answer"]["sections"][0].pop("title")

    normalized, errors = validate_feedback_candidate_payload(payload)

    assert normalized is not None
    assert errors == ()
    assert "reference_answer_sections_invalid" not in errors
    assert normalized["reference_answer"]["sections"][0]["title"] == "参考回答 1"
    assert "reference_answer_section_title_generated" in normalized["feedback_metadata"]["validation_warnings"]


def test_validate_feedback_candidate_payload_generates_missing_reference_section_id() -> None:
    payload = _candidate_payload()
    payload["reference_answer"]["sections"][0].pop("section_id")

    normalized, errors = validate_feedback_candidate_payload(payload)

    assert normalized is not None
    assert errors == ()
    assert normalized["reference_answer"]["sections"][0]["section_id"] == "section_1"
    assert "reference_answer_section_id_generated" in normalized["feedback_metadata"]["validation_warnings"]


def test_validate_feedback_candidate_payload_drops_unknown_reference_loss_point_refs() -> None:
    payload = _candidate_payload()
    payload["reference_answer"]["sections"][0]["addresses_loss_point_ids"] = [
        "lp_observability",
        "lp_unknown",
    ]

    normalized, errors = validate_feedback_candidate_payload(payload)

    assert normalized is not None
    assert errors == ()
    section = normalized["reference_answer"]["sections"][0]
    assert section["addresses_loss_point_ids"] == ["lp_observability"]
    assert "reference_answer_unknown_loss_point_ref_removed" in normalized["feedback_metadata"]["validation_warnings"]


def test_validate_feedback_candidate_payload_defaults_missing_reference_addresses_to_empty_list() -> None:
    payload = _candidate_payload()
    payload["reference_answer"]["sections"][0].pop("addresses_loss_point_ids")

    normalized, errors = validate_feedback_candidate_payload(payload)

    assert normalized is not None
    assert errors == ()
    assert normalized["reference_answer"]["sections"][0]["addresses_loss_point_ids"] == []


def test_validate_feedback_candidate_payload_rejects_sections_without_any_content() -> None:
    payload = _candidate_payload()
    payload["reference_answer"]["sections"] = [
        {
            "section_id": "ref_empty",
            "title": "空参考回答",
            "content": " ",
            "addresses_loss_point_ids": ["lp_observability"],
        }
    ]

    normalized, errors = validate_feedback_candidate_payload(payload)

    assert normalized is None
    assert "reference_answer_sections_invalid" in errors


def test_validate_feedback_candidate_payload_rewrites_duplicate_reference_section_ids() -> None:
    payload = _candidate_payload()
    payload["reference_answer"]["sections"].append(
        {
            "section_id": "ref_observability",
            "title": "",
            "content": "补充说明恢复边界、重试停止条件和人工介入标准。",
        }
    )

    normalized, errors = validate_feedback_candidate_payload(payload)

    assert normalized is not None
    assert errors == ()
    section_ids = [section["section_id"] for section in normalized["reference_answer"]["sections"]]
    assert section_ids == ["ref_observability", "section_2"]
    assert "reference_answer_section_id_rewritten" in normalized["feedback_metadata"]["validation_warnings"]


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
