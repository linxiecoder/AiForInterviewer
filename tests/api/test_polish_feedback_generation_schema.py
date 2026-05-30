from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest


def _schema_module():
    try:
        from app.application.polish import feedback_schema
    except ModuleNotFoundError as exc:  # pragma: no cover - RED signal before implementation exists.
        pytest.fail(f"feedback schema module is missing: {exc}")
    return feedback_schema


def _validate(payload: object):
    try:
        from app.application.polish.feedback_validation import validate_generated_feedback_payload
    except ModuleNotFoundError as exc:  # pragma: no cover - RED signal before implementation exists.
        pytest.fail(f"feedback validator module is missing: {exc}")
    return validate_generated_feedback_payload(payload)


def _valid_payload() -> dict[str, Any]:
    return {
        "schema_id": "polish_feedback_generated_v1",
        "schema_version": "1.0",
        "status": "generated",
        "contract_ids": ["P-POLISH-003", "P-POLISH-004", "P-POLISH-005"],
        "feedback_text": "回答覆盖了核心方案，但缺少一致性边界和故障恢复说明。",
        "answer_summary": "候选人说明了缓存和消息队列方案。",
        "score_result": {
            "score_value": 82,
            "score_type": "polish_answer",
        },
        "explicit_score": 82,
        "implicit_score": 80,
        "scoring_dimensions": [
            {"dimension": "architecture", "score": 40},
            {"dimension": "reliability", "score": 42},
        ],
        "loss_points": [
            {
                "loss_point_id": "lp_consistency",
                "severity": "major",
                "deduction": 12,
                "reason": "没有说明跨服务一致性策略。",
            },
            {
                "loss_point_id": "lp_observability",
                "severity": "minor",
                "deducted_points": 6,
                "reason": "监控指标说明不足。",
            },
        ],
        "reference_answer": {
            "sections": [
                {
                    "section_id": "ref_consistency",
                    "title": "一致性设计",
                    "content": "说明事务边界、幂等键和补偿机制。",
                    "addresses_loss_point_ids": ["lp_consistency"],
                },
                {
                    "section_id": "ref_observability",
                    "title": "观测与回滚",
                    "content": "说明核心指标、告警和回滚动作。",
                    "addresses_loss_point_ids": ["lp_observability"],
                },
            ]
        },
        "knowledge_points": ["事务消息", "幂等设计"],
        "technical_principles": ["先定义一致性边界，再选择中间件。"],
        "same_question_effect": {
            "improved_points": ["结构更清晰"],
            "repeated_loss_point_ids": ["lp_observability"],
            "regressed_points": [],
            "next_retry_focus": ["补齐监控指标"],
            "score_delta": 6,
        },
        "project_asset_consistency_check": {"status": "consistent", "conflicts": []},
        "session_similarity_check": {"status": "benign_reuse"},
        "project_asset_update_candidates": [
            {
                "candidate_type": "project_asset_update_candidate",
                "candidate_ref": "asset_candidate_001",
                "user_confirmation_required": True,
                "target_asset_ref": {"resource_type": "asset", "resource_id": "asset_001"},
                "summary": "补充支付项目的一致性治理素材。",
            }
        ],
        "next_recommended_actions": ["围绕故障恢复再练一题"],
        "low_confidence_flags": [],
        "trace_refs": [{"resource_type": "llm_trace", "resource_id": "trace_001"}],
        "feedback_metadata": {
            "prompt_version": "polish_feedback_agent_prompt.v1",
            "llm_called": True,
        },
    }


def _with_change(**changes: object) -> dict[str, Any]:
    payload = _valid_payload()
    payload.update(changes)
    return payload


def test_feedback_generated_schema_constants_are_stable() -> None:
    schema = _schema_module()

    assert schema.POLISH_FEEDBACK_GENERATED_SCHEMA_ID == "polish_feedback_generated_v1"
    assert schema.POLISH_FEEDBACK_GENERATED_SCHEMA_VERSION == "1.0"
    assert schema.POLISH_FEEDBACK_AGENT_PROMPT_VERSION == "polish_feedback_agent_prompt.v1"
    assert schema.POLISH_FEEDBACK_TASK_TYPE == "polish_feedback_generation"
    assert schema.POLISH_FEEDBACK_GENERATED_CONTRACT_IDS == (
        "P-POLISH-003",
        "P-POLISH-004",
        "P-POLISH-005",
    )


def test_feedback_generated_payload_field_list_covers_minimum_contract_shape() -> None:
    schema = _schema_module()

    assert set(schema.POLISH_FEEDBACK_GENERATED_PAYLOAD_FIELDS) >= {
        "schema_id",
        "schema_version",
        "status",
        "contract_ids",
        "feedback_text",
        "answer_summary",
        "score_result",
        "explicit_score",
        "implicit_score",
        "scoring_dimensions",
        "loss_points",
        "reference_answer",
        "knowledge_points",
        "technical_principles",
        "same_question_effect",
        "project_asset_consistency_check",
        "session_similarity_check",
        "project_asset_update_candidates",
        "next_recommended_actions",
        "low_confidence_flags",
        "trace_refs",
        "feedback_metadata",
    }


def test_valid_generated_payload_passes_and_does_not_mutate_input() -> None:
    payload = _valid_payload()
    original = deepcopy(payload)

    normalized, errors = _validate(payload)

    assert errors == ()
    assert normalized is not None
    assert normalized["schema_id"] == "polish_feedback_generated_v1"
    assert normalized["status"] == "generated"
    assert normalized["score_result"]["score_value"] == 82
    assert payload == original


def test_quick_generated_payload_allows_empty_future_sections_and_not_applicable_checks() -> None:
    payload = _valid_payload()
    payload["score_result"]["score_value"] = 88
    payload["explicit_score"] = 88
    payload["implicit_score"] = 86
    payload["loss_points"] = [
        {
            "loss_point_id": "lp_tradeoff",
            "severity": "major",
            "deduction": 12,
            "reason": "混合检索的召回、重排和延迟取舍没有展开。",
        }
    ]
    payload["reference_answer"] = {
        "sections": [
            {
                "section_id": "ref_tradeoff",
                "title": "混合检索取舍",
                "content": "说明关键词召回、向量召回、rerank、离线指标和线上延迟预算。",
                "addresses_loss_point_ids": ["lp_tradeoff"],
            }
        ]
    }
    payload["knowledge_points"] = []
    payload["technical_principles"] = []
    payload["project_asset_update_candidates"] = []
    payload["project_asset_consistency_check"] = {"status": "not_applicable"}
    payload["session_similarity_check"] = {"status": "not_applicable"}

    normalized, errors = _validate(payload)

    assert errors == ()
    assert normalized is not None
    assert normalized["knowledge_points"] == []
    assert normalized["technical_principles"] == []
    assert normalized["project_asset_consistency_check"] == {"status": "not_applicable"}
    assert normalized["session_similarity_check"] == {"status": "not_applicable"}


def test_schema_id_invalid_fails() -> None:
    normalized, errors = _validate(_with_change(schema_id="wrong_schema"))

    assert normalized is None
    assert "feedback_schema_id_invalid" in errors


def test_generated_feedback_text_empty_fails() -> None:
    normalized, errors = _validate(_with_change(feedback_text=" "))

    assert normalized is None
    assert "feedback_text_required" in errors


def test_score_out_of_range_fails() -> None:
    payload = _valid_payload()
    payload["score_result"]["score_value"] = 101

    normalized, errors = _validate(payload)

    assert normalized is None
    assert "score_value_out_of_range" in errors


def test_major_loss_point_without_reference_section_coverage_fails() -> None:
    payload = _valid_payload()
    payload["reference_answer"]["sections"][0]["addresses_loss_point_ids"] = []

    normalized, errors = _validate(payload)

    assert normalized is None
    assert "loss_point_reference_mapping_missing" in errors


def test_reference_section_points_to_unknown_loss_point_id_fails() -> None:
    payload = _valid_payload()
    payload["reference_answer"]["sections"][0]["addresses_loss_point_ids"] = [
        "lp_missing",
    ]

    normalized, errors = _validate(payload)

    assert normalized is None
    assert "reference_answer_unknown_loss_point_ref" in errors


def test_score_and_deduction_mismatch_fails() -> None:
    payload = _valid_payload()
    payload["score_result"]["score_value"] = 95

    normalized, errors = _validate(payload)

    assert normalized is None
    assert "score_loss_deduction_mismatch" in errors


def test_project_asset_conflict_without_clarification_question_fails() -> None:
    payload = _valid_payload()
    payload["project_asset_consistency_check"] = {
        "status": "conflict",
        "conflicts": [
            {
                "conflict_type": "timeline",
                "current_answer_claim": "项目发生在 2025 年。",
                "asset_claim": "资产中记录为 2024 年。",
                "severity": "major",
            }
        ],
    }

    normalized, errors = _validate(payload)

    assert normalized is None
    assert "project_asset_conflict_clarification_required" in errors


def test_project_asset_update_candidate_without_user_confirmation_fails() -> None:
    payload = _valid_payload()
    payload["project_asset_update_candidates"][0]["user_confirmation_required"] = False

    normalized, errors = _validate(payload)

    assert normalized is None
    assert "project_asset_candidate_user_confirmation_required" in errors


@pytest.mark.parametrize("unsafe_key", ("raw_prompt", "provider_payload"))
def test_unsafe_raw_prompt_or_provider_payload_key_fails(unsafe_key: str) -> None:
    payload = _valid_payload()
    payload["feedback_metadata"][unsafe_key] = "hidden prompt"

    normalized, errors = _validate(payload)

    assert normalized is None
    assert "feedback_payload_unsafe_leakage" in errors


def test_unsafe_secret_or_token_value_fails() -> None:
    payload = _valid_payload()
    payload["feedback_metadata"]["provider_note"] = "token=raw-token should never leave the boundary"

    normalized, errors = _validate(payload)

    assert normalized is None
    assert "feedback_payload_unsafe_leakage" in errors


def test_low_confidence_payload_can_pass_without_complete_reference_answer() -> None:
    payload = _valid_payload()
    payload["status"] = "low_confidence"
    payload["feedback_text"] = ""
    payload["loss_points"] = [
        {
            "loss_point_id": "lp_context_missing",
            "severity": "major",
            "reason": "缺少可验证项目上下文。",
        }
    ]
    payload["reference_answer"] = {"sections": []}
    payload["low_confidence_flags"] = ["reference_answer_source_unavailable"]
    payload["score_result"]["score_value"] = 0

    normalized, errors = _validate(payload)

    assert errors == ()
    assert normalized is not None
    assert normalized["status"] == "low_confidence"
    assert normalized["low_confidence_flags"] == ["reference_answer_source_unavailable"]


def test_contract_ids_missing_required_contracts_fails() -> None:
    normalized, errors = _validate(_with_change(contract_ids=["P-POLISH-003"]))

    assert normalized is None
    assert "feedback_contract_ids_missing_required" in errors


def test_duplicate_loss_point_id_fails() -> None:
    payload = _valid_payload()
    payload["loss_points"][1]["loss_point_id"] = "lp_consistency"

    normalized, errors = _validate(payload)

    assert normalized is None
    assert "loss_point_id_duplicate" in errors


def test_duplicate_reference_section_id_fails() -> None:
    payload = _valid_payload()
    payload["reference_answer"]["sections"][1]["section_id"] = "ref_consistency"

    normalized, errors = _validate(payload)

    assert normalized is None
    assert "reference_answer_section_id_duplicate" in errors
