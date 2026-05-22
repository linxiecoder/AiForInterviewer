from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from app.application.polish.candidates import (
    CandidateExtractionInput,
    CandidateType,
    extract_asset_candidates,
    extract_feedback_candidates,
    extract_training_suggestion_candidates,
    extract_weakness_candidates,
)


def _candidate_input(
    *,
    owner_id: str = "usr_candidate_owner_a",
    feedback_payload: dict[str, Any] | None = None,
) -> CandidateExtractionInput:
    return CandidateExtractionInput(
        owner_id=owner_id,
        session_id="psess_candidate_001",
        question_id="ques_candidate_001",
        answer_id="ans_candidate_001",
        feedback_id="trc_candidate_feedback_001",
        score_result_id="score_candidate_001",
        feedback_payload=feedback_payload or _structured_feedback_payload(),
        question_metadata={
            "question_pattern": "failure_handling_design",
            "expected_answer_dimensions": ["failure handling", "idempotency"],
            "quality_score": 88,
        },
        created_at=datetime(2026, 5, 22, 10, 30, tzinfo=UTC),
    )


def _structured_feedback_payload() -> dict[str, Any]:
    return {
        "schema_id": "polish_feedback_payload_v1",
        "schema_version": "1.0",
        "status": "generated",
        "feedback_id": "trc_candidate_feedback_001",
        "answer_id": "ans_candidate_001",
        "question_id": "ques_candidate_001",
        "question_text": "请说明一次故障兜底方案。",
        "answer_text": "完整原始回答不应进入 merge_key 或候选对象。",
        "feedback_text": "结构化反馈",
        "feedback_summary": "结构化反馈",
        "polish_session_ref": {"resource_type": "polish_session", "resource_id": "psess_candidate_001"},
        "question_ref": {"resource_type": "question", "resource_id": "ques_candidate_001"},
        "answer_ref": {"resource_type": "answer", "resource_id": "ans_candidate_001"},
        "score_result_ref": {"resource_type": "score_result", "resource_id": "score_candidate_001"},
        "score_result": {
            "score_result_id": "score_candidate_001",
            "score_value": 64,
            "confidence_level": "medium",
        },
        "scoring_dimensions": [
            {"dimension_id": "technical_depth", "score_value": 55, "confidence_level": "medium"},
            {"dimension_id": "answer_structure", "score_value": 58, "confidence_level": "medium"},
            {"dimension_id": "business_impact", "score_value": 86, "confidence_level": "medium"},
        ],
        "loss_points": [
            {
                "loss_point_id": "loss_failure_handling",
                "dimension_id": "technical_depth",
                "title": "故障兜底与失败收敛表达不足",
                "reason": "缺少失败路径、补偿策略和上线验证指标。",
                "deducted_points": 14,
                "critical": True,
                "answer_excerpt": "只讲了成功路径。",
            },
            {
                "loss_point_id": "loss_structure",
                "dimension_id": "answer_structure",
                "title": "项目表达结构不清晰",
                "reason": "结论、约束、方案、结果没有分层。",
                "deducted_points": 8,
                "critical": False,
            },
        ],
        "repeated_loss_points": ["loss_failure_handling"],
        "remaining_gaps": ["loss_failure_handling", "状态机与幂等闭环不足"],
        "technical_gaps": ["状态机与幂等闭环不足"],
        "communication_gaps": ["项目表达结构不清晰"],
        "positive_evidence_points": [
            {
                "point_id": "pos_business_metric",
                "dimension_id": "business_impact",
                "title": "能说明业务指标",
                "evidence_excerpt": "提到了告警压降和恢复时间。",
                "confidence_level": "medium",
            }
        ],
        "answer_diagnosis": {"strengths": ["能说明业务指标"], "weaknesses": ["故障兜底不足"]},
        "oral_script": "我会先说故障背景，再说明兜底策略、状态机、幂等和验证指标。",
        "p7_reference_answer": "高阶参考答案：先界定失败场景，再给补偿、回滚、监控和指标。",
        "next_retry_focus": [
            {"focus_id": "retry_failure_handling", "title": "补齐失败兜底", "reason": "重复缺失"},
        ],
        "mastery_status": "stuck",
        "should_continue_same_question": True,
        "should_generate_next_question": False,
        "feedback_metadata": {"question_pattern": "failure_handling_design"},
        "trace_refs": [
            {"trace_ref_id": "ans_candidate_001", "trace_type": "answer"},
            {"trace_ref_id": "trc_candidate_feedback_001", "trace_type": "feedback"},
        ],
        "candidate_refs": [{"resource_type": "weakness_candidate", "resource_id": "legacy_weakness_ref"}],
    }


def _collect_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            keys.add(str(key))
            keys.update(_collect_keys(nested))
    elif isinstance(value, list):
        for nested in value:
            keys.update(_collect_keys(nested))
    return keys


def _string_values(value: Any) -> list[str]:
    values: list[str] = []
    if isinstance(value, dict):
        for nested in value.values():
            values.extend(_string_values(nested))
    elif isinstance(value, list):
        for nested in value:
            values.extend(_string_values(nested))
    elif isinstance(value, str):
        values.append(value)
    return values


def _refs_by_type(candidate: dict[str, Any], ref_field: str) -> dict[str, set[str]]:
    refs: dict[str, set[str]] = {}
    for ref in candidate[ref_field]:
        refs.setdefault(str(ref["resource_type"]), set()).add(str(ref["resource_id"]))
    return refs


def test_feedback_extracts_candidate_payload_fields_and_refs() -> None:
    payload = extract_feedback_candidates(_candidate_input())

    assert payload["weakness_candidates"]
    assert payload["asset_candidates"]
    assert payload["training_suggestion_candidates"]
    assert payload["oral_script_candidates"]
    assert payload["polished_answer_candidates"]
    assert payload["candidate_refs"][0]["resource_type"] == "weakness_candidate"
    assert {ref["resource_type"] for ref in payload["candidate_refs"]} >= {
        "weakness_candidate",
        "asset_candidate",
        "training_suggestion_candidate",
        "oral_script_candidate",
        "polished_answer_candidate",
    }

    all_candidates = (
        payload["weakness_candidates"]
        + payload["asset_candidates"]
        + payload["training_suggestion_candidates"]
        + payload["oral_script_candidates"]
        + payload["polished_answer_candidates"]
    )
    assert all(candidate["status"] == "candidate" for candidate in all_candidates)
    assert all(candidate["user_confirmation_required"] is True for candidate in all_candidates)
    assert all(candidate["target_formal_ref"] is None for candidate in all_candidates)
    assert "weaknesses" not in payload
    assert "assets" not in payload
    assert "training_recommendations" not in payload

    weakness = payload["weakness_candidates"][0]
    assert weakness["candidate_type"] == "weakness_candidate"
    source_refs = _refs_by_type(weakness, "source_refs")
    trace_refs = _refs_by_type(weakness, "trace_refs")
    assert {"polish_session", "question", "answer", "feedback", "score_result", "loss_point"} <= set(source_refs)
    assert {"question", "answer", "feedback"} <= set(trace_refs)
    assert weakness["merge_key"]
    assert "完整原始回答" not in weakness["merge_key"]


def test_specific_extractors_generate_expected_candidate_types() -> None:
    extraction_input = _candidate_input()

    weakness_candidates = extract_weakness_candidates(extraction_input)
    asset_candidates = extract_asset_candidates(extraction_input)
    training_candidates = extract_training_suggestion_candidates(extraction_input)

    assert weakness_candidates
    assert all(candidate.candidate_type == CandidateType.WEAKNESS for candidate in weakness_candidates)
    assert weakness_candidates[0].evidence_refs[0]["resource_id"] == "loss_failure_handling"
    assert {candidate.candidate_type for candidate in asset_candidates} == {
        CandidateType.ASSET,
        CandidateType.ORAL_SCRIPT,
        CandidateType.POLISHED_ANSWER,
    }
    assert [candidate.candidate_type for candidate in training_candidates] == [
        CandidateType.TRAINING_SUGGESTION
    ]
    assert weakness_candidates[0].confidence_level == "high"
    assert any(candidate.candidate_payload.get("model_suggested") is True for candidate in asset_candidates)
    assert any(
        candidate.candidate_payload.get("fact_source") == "model_suggested_phrasing"
        for candidate in asset_candidates
    )


def test_repeated_loss_points_are_prioritized_over_single_minor_loss_points() -> None:
    payload = _structured_feedback_payload()
    payload["repeated_loss_points"] = ["loss_failure_handling"]
    payload["loss_points"][1]["critical"] = False
    payload["loss_points"][1]["deducted_points"] = 2

    candidates = extract_weakness_candidates(_candidate_input(feedback_payload=payload))

    assert candidates[0].evidence_refs[0]["resource_id"] == "loss_failure_handling"
    assert candidates[0].confidence_level == "high"
    assert all(candidate.confidence_level != "high" for candidate in candidates[1:])


def test_training_candidate_uses_remaining_gaps_and_retry_focus() -> None:
    payload = extract_feedback_candidates(_candidate_input())
    candidate = payload["training_suggestion_candidates"][0]

    assert candidate["candidate_type"] == "training_suggestion_candidate"
    assert candidate["confidence_level"] in {"medium", "high"}
    assert "同题" in candidate["summary"] or "重答" in candidate["summary"]
    assert _refs_by_type(candidate, "source_refs")["loss_point"]


def test_merge_key_is_stable_and_owner_isolated() -> None:
    first = extract_feedback_candidates(_candidate_input())
    second = extract_feedback_candidates(_candidate_input())
    other_owner = extract_feedback_candidates(_candidate_input(owner_id="usr_candidate_owner_b"))

    first_key = first["weakness_candidates"][0]["merge_key"]
    assert first_key == second["weakness_candidates"][0]["merge_key"]
    assert first_key != other_owner["weakness_candidates"][0]["merge_key"]
    assert "完整原始回答" not in first_key


@pytest.mark.parametrize(
    "payload",
    [
        {"status": "pending", "feedback_text": "本轮反馈尚未生成"},
        {"status": "generated", "feedback_text": "legacy feedback text", "candidate_refs": []},
    ],
)
def test_pending_and_old_feedback_payloads_do_not_create_invalid_candidates(payload: dict[str, Any]) -> None:
    result = extract_feedback_candidates(_candidate_input(feedback_payload=payload))

    assert result["weakness_candidates"] == []
    assert result["asset_candidates"] == []
    assert result["training_suggestion_candidates"] == []
    assert result["oral_script_candidates"] == []
    assert result["polished_answer_candidates"] == []
    assert result["candidate_refs"] == []


def test_candidate_payload_sanitizes_raw_prompt_completion_and_provider_payload() -> None:
    payload = _structured_feedback_payload()
    payload["raw_prompt"] = "raw prompt must not be returned"
    payload["completion"] = "raw completion must not be returned"
    payload["provider_payload"] = {"api_key": "secret"}
    payload["loss_points"][0]["hidden_rubric"] = "internal scoring rule"
    payload["positive_evidence_points"][0]["full_evidence_text"] = "full answer evidence"
    payload["loss_points"][0]["answer_excerpt"] = "raw prompt must not be returned"
    payload["positive_evidence_points"][0]["evidence_excerpt"] = "full evidence text must not be returned"
    payload["technical_gaps"] = ["cookie=session-secret must not be returned"]
    payload["oral_script"] = "provider payload must not be returned"
    payload["p7_reference_answer"] = "api_key=sk-test-secret must not be returned"
    result = extract_feedback_candidates(_candidate_input(feedback_payload=payload))

    forbidden = {
        "raw_prompt",
        "completion",
        "raw_completion",
        "provider_payload",
        "hidden_rubric",
        "full_evidence_text",
        "api_key",
        "cookie",
        "secret",
        "token",
    }
    assert not (_collect_keys(result) & forbidden)
    serialized_values = "\n".join(_string_values(result)).lower()
    for forbidden_text in (
        "raw prompt must not be returned",
        "full evidence text must not be returned",
        "cookie=session-secret must not be returned",
        "provider payload must not be returned",
        "api_key=sk-test-secret must not be returned",
    ):
        assert forbidden_text not in serialized_values
