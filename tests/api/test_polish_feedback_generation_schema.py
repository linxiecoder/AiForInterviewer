from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest


def _prompt_context() -> dict[str, Any]:
    return {
        "owner_id": "owner_001",
        "actor_id": "user_001",
        "session_id": "sess_001",
        "question_id": "question_001",
        "answer_id": "answer_001",
        "question_text": "请说明订单异步处理如何保证失败可恢复。",
        "answer_text": "我会用消息队列、幂等键、重试任务和告警恢复失败消息。",
        "evidence_refs": ["resume_project_payment"],
    }



def _schema_module():
    try:
        from app.application.polish import feedback_schema
    except ModuleNotFoundError as exc:  # pragma: no cover - schema import gate.
        pytest.fail(f"feedback schema module is missing: {exc}")
    return feedback_schema


def _validate(payload: object):
    try:
        from app.application.polish.feedback_validation import validate_final_feedback_payload
    except ModuleNotFoundError as exc:  # pragma: no cover - schema import gate.
        pytest.fail(f"feedback validator module is missing: {exc}")
    return validate_final_feedback_payload(payload)


def _valid_payload() -> dict[str, Any]:
    return {
        "schema_id": "polish_feedback_generated_v1",
        "schema_version": "1.0",
        "status": "generated",
        "contract_ids": ["P-POLISH-003", "P-POLISH-004", "P-POLISH-005"],
        "feedback_id": "feedback_001",
        "feedback_text": "回答覆盖了核心方案，但缺少一致性边界和故障恢复说明。",
        "answer_summary": "候选人说明了缓存和消息队列方案。",
        "score_result": {
            "score_value": 82,
            "score_type": "polish_answer",
        },
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
        "asset_consistency_check": {
            "status": "consistent",
            "checked_asset_refs": ["asset_payment"],
            "conflicts": [],
            "unsupported_claims": [],
            "user_clarification_required": False,
        },
        "answer_coverage": {
            "expected_points": ["一致性", "可观测性"],
            "covered_points": ["一致性", "可观测性"],
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
            "score_delta": 6,
            "trend": "improved",
        },
        "feedback_cards": [
            {"card_type": "overall", "status": "generated", "payload": {}},
            {"card_type": "next_actions", "status": "generated", "payload": {}},
        ],
        "next_recommended_actions": ["review_reference_answer"],
        "low_confidence_flags": [],
        "trace_refs": [
            {"resource_type": "llm_trace", "resource_id": "trace_001"},
        ],
        "feedback_metadata": {
            "prompt_version": "polish_feedback_agent_prompt.v1",
            "llm_called": True,
        },
    }


def _with_change(**changes: object) -> dict[str, Any]:
    payload = _valid_payload()
    payload.update(changes)
    return payload


def test_feedback_final_schema_constants_are_stable() -> None:
    schema = _schema_module()

    assert schema.POLISH_FEEDBACK_FINAL_SCHEMA_ID == "polish_feedback_generated_v1"
    assert schema.POLISH_FEEDBACK_FINAL_SCHEMA_VERSION == "1.0"
    assert schema.POLISH_FEEDBACK_AGENT_PROMPT_VERSION == "polish_feedback_agent_prompt.v1"
    assert schema.POLISH_FEEDBACK_TASK_TYPE == "polish_feedback_generation"
    assert schema.POLISH_FEEDBACK_FINAL_CONTRACT_IDS == (
        "P-POLISH-003",
        "P-POLISH-004",
        "P-POLISH-005",
    )


def test_feedback_payload_field_lists_are_explicit() -> None:
    schema = _schema_module()

    assert set(schema.POLISH_FEEDBACK_FINAL_PAYLOAD_FIELDS) == {
        "schema_id",
        "schema_version",
        "status",
        "contract_ids",
        "feedback_id",
        "feedback_text",
        "answer_summary",
        "score_result",
        "loss_points",
        "reference_answer",
        "asset_consistency_check",
        "answer_coverage",
        "answer_change_analysis",
        "feedback_cards",
        "next_recommended_actions",
        "low_confidence_flags",
        "trace_refs",
        "feedback_metadata",
    }
    assert set(schema.POLISH_FEEDBACK_CANDIDATE_PAYLOAD_FIELDS) == {
        "score_reasoning",
        "loss_points",
        "reference_answer",
        "same_question_effect",
        "project_asset_update_candidates",
        "low_confidence_flags",
        "evidence_refs",
        "feedback_text",
        "answer_summary",
    }


def test_feedback_payload_cross_layer_fields_are_explicitly_excluded() -> None:
    schema = _schema_module()

    shared_fields = {
        "feedback_text",
        "answer_summary",
        "loss_points",
        "reference_answer",
        "low_confidence_flags",
    }
    assert set(schema.POLISH_FEEDBACK_FINAL_PAYLOAD_FIELDS) & set(
        schema.POLISH_FEEDBACK_CANDIDATE_PAYLOAD_FIELDS
    ) == shared_fields


def test_provider_output_schema_keeps_reference_section_title_property() -> None:
    from app.application.polish.feedback_prompt_assets import build_feedback_prompt_asset

    output_schema = build_feedback_prompt_asset(_prompt_context())["provider_prompt"]["output_schema"]
    reference_section_schema = output_schema["$defs"]["ReferenceAnswerSection"]

    assert "title" in reference_section_schema["properties"]
    assert "title" not in reference_section_schema.get("required", [])


def test_provider_output_schema_has_no_required_fields_missing_from_properties() -> None:
    from app.application.polish.feedback_prompt_assets import build_feedback_prompt_asset

    output_schema = build_feedback_prompt_asset(_prompt_context())["provider_prompt"]["output_schema"]

    assert _required_missing_from_properties(output_schema) == []


def _required_missing_from_properties(schema: object, path: str = "$") -> list[str]:
    missing: list[str] = []
    if isinstance(schema, dict):
        properties = schema.get("properties")
        required = schema.get("required")
        if isinstance(properties, dict) and isinstance(required, list):
            for field_name in required:
                if field_name not in properties:
                    missing.append(f"{path}.required.{field_name}")
        for key, value in schema.items():
            missing.extend(_required_missing_from_properties(value, f"{path}.{key}"))
    elif isinstance(schema, list):
        for index, value in enumerate(schema):
            missing.extend(_required_missing_from_properties(value, f"{path}[{index}]"))
    return missing


def test_valid_feedback_payload_passes_and_does_not_mutate_input() -> None:
    payload = _valid_payload()
    original = deepcopy(payload)

    normalized, errors = _validate(payload)

    assert errors == ()
    assert normalized is not None
    assert normalized["schema_id"] == "polish_feedback_generated_v1"
    assert normalized["status"] == "generated"
    assert normalized["score_result"]["score_value"] == 82
    assert payload == original


def test_schema_id_invalid_fails() -> None:
    normalized, errors = _validate(_with_change(schema_id="wrong_schema"))

    assert normalized is None
    assert "feedback_schema_id_invalid" in errors


def test_feedback_text_empty_fails() -> None:
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

    assert normalized is not None
    assert errors == ()


def test_reference_section_points_to_unknown_loss_point_id_fails() -> None:
    payload = _valid_payload()
    payload["reference_answer"]["sections"][0]["addresses_loss_point_ids"] = ["lp_missing"]

    normalized, errors = _validate(payload)

    assert normalized is None
    assert "reference_answer_unknown_loss_point_ref" in errors


def test_project_asset_conflict_without_clarification_question_fails() -> None:
    payload = _valid_payload()
    payload["asset_consistency_check"] = {
        "status": "conflict",
        "conflicts": [
            {
                "conflict_type": "timeline",
                "current_answer_claim": "项目发生在 2025 年。",
                "asset_claim": "资产中记录为 2024 年。",
                "severity": "major",
            }
        ],
        "checked_asset_refs": ["asset_payment"],
        "unsupported_claims": [],
        "user_clarification_required": False,
    }

    normalized, errors = _validate(payload)

    assert normalized is None
    assert "asset_consistency_conflict_clarification_required" in errors


def test_unsafe_secret_or_token_value_fails() -> None:
    payload = _valid_payload()
    payload["feedback_metadata"]["provider_note"] = "token=raw-token should never leave the boundary"

    normalized, errors = _validate(payload)

    assert normalized is None
    assert "feedback_payload_unsafe_leakage" in errors


def test_low_confidence_payload_still_requires_reference_answer_sections() -> None:
    payload = _valid_payload()
    payload["status"] = "low_confidence"
    payload["feedback_text"] = "当前证据不足，先给出待完善项。"
    payload["loss_points"] = [
        {
            "loss_point_id": "lp_context_missing",
            "severity": "major",
            "reason": "缺少可验证项目上下文。",
            "deduction": 10,
        }
    ]
    payload["reference_answer"] = {"sections": []}
    payload["low_confidence_flags"] = ["reference_answer_source_unavailable"]
    payload["score_result"]["score_value"] = 0

    normalized, errors = _validate(payload)

    assert normalized is None
    assert "reference_answer_sections_required" in errors


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
