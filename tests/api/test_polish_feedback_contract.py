from __future__ import annotations

from app.application.polish.feedback_contracts import (
    FEEDBACK_SCHEMA_ID,
    FEEDBACK_SCHEMA_VERSION,
    ScoringDimension,
)
from app.application.polish.feedback_quality import (
    compute_score_result_from_dimensions,
    normalize_feedback_payload,
    validate_feedback_consistency,
)


def _base_payload() -> dict:
    return {
        "schema_id": FEEDBACK_SCHEMA_ID,
        "schema_version": FEEDBACK_SCHEMA_VERSION,
        "status": "generated",
        "feedback_id": "fb_consistency_base",
        "feedback_text": "本轮回答完整度较高。",
        "feedback_summary": "本轮反馈完整度较高。",
        "answer_diagnosis": {},
        "scoring_dimensions": [
            {
                "dimension_id": "technical",
                "score_value": 80,
                "max_score": 100,
                "weight": 2.0,
            },
            {
                "dimension_id": "expression",
                "score_value": 70,
                "max_score": 100,
                "weight": 1.0,
            },
        ],
        "score_result": {
            "score_result_id": "sr_base",
            "score_type": "polish_answer",
            "score_value": 77,
            "score_version": FEEDBACK_SCHEMA_VERSION,
            "confidence_level": "medium",
        },
        "positive_evidence_points": [
            {
                "point_id": "pe1",
                "title": "技术闭环",
                "evidence_excerpt": "失败路径",
                "dimension_id": "technical",
                "location": "both",
            }
        ],
        "loss_points": [
            {
                "loss_point_id": "lp1",
                "title": "技术细节不足",
                "deducted_points": 10,
                "reason": "建议补充异常路径和收敛机制。",
                "critical": False,
                "dimension_id": "technical",
            }
        ],
        "missing_answer_dimensions": [],
        "interview_intent": "evaluate_depth",
        "p7_reference_answer": "回答应覆盖失败路径、收敛机制和验证指标。",
        "reference_answer_requirements": [],
        "oral_script": "我先说背景，再讲失败路径、收敛机制、验证指标。",
        "oral_script_requirements": [],
        "knowledge_points": [],
        "technical_principles": [],
        "technical_gaps": [],
        "communication_gaps": [],
        "next_recommended_actions": ["continue_same_question"],
        "weakness_candidates": [],
        "asset_candidates": [],
        "validation_result_ref": {"resource_type": "validation_result", "resource_id": "vr"},
        "trace_refs": [],
        "low_confidence_flags": [],
        "feedback_metadata": {},
        "score_delta": 0,
        "dimension_delta": {},
        "improved_points": [],
        "remaining_gaps": ["收敛机制"],
        "repeated_loss_points": [],
        "regressed_points": [],
        "mastery_status": "in_progress",
        "should_continue_same_question": True,
        "should_generate_next_question": False,
        "next_retry_focus": [{"focus_area": "收敛机制", "priority": 1}],
    }


def test_scoring_dimensions_score_result_consistency() -> None:
    payload = _base_payload()
    normalized_result = compute_score_result_from_dimensions(
        [
            ScoringDimension(dimension_id="technical", score_value=80, max_score=100, weight=2.0),
            ScoringDimension(dimension_id="expression", score_value=70, max_score=100, weight=1.0),
        ]
    )
    payload["score_result"]["score_value"] = normalized_result["score_value"]

    validation = validate_feedback_consistency(payload)
    assert validation["allow_emit"] is True
    assert not validation["blocking_issues"]

    payload["score_result"]["score_value"] = 60
    validation = validate_feedback_consistency(payload)
    assert not validation["allow_emit"]
    assert any("score_result_inconsistent" in issue for issue in validation["blocking_issues"])


def test_loss_points_cover_reference_answer() -> None:
    payload = _base_payload()
    payload["loss_points"] = [
        {
            "loss_point_id": "lp_critical_1",
            "title": "关键风险未覆盖",
            "deducted_points": 12,
            "reason": "需要补充重试收敛",
            "critical": True,
            "required_reference_terms": ["重试收敛"],
            "dimension_id": "technical",
        }
    ]
    payload["p7_reference_answer"] = "需补充重试收敛机制以及 fallback 验证。"
    payload["positive_evidence_points"] = [
        {
            "point_id": "pe_retry",
            "title": "重试收敛",
            "evidence_excerpt": "重试收敛",
            "dimension_id": "technical",
            "location": "both",
        }
    ]
    payload["oral_script"] = "口语化收束我需要补充。"
    payload["score_result"]["score_value"] = compute_score_result_from_dimensions(payload["scoring_dimensions"])["score_value"]

    validation = validate_feedback_consistency(payload)
    assert validation["allow_emit"] is True
    assert not any("critical_loss_point_not_covered_by_p7_reference_answer" in issue for issue in validation["blocking_issues"])

    payload["p7_reference_answer"] = "请直接给结论，不要写收敛机制。"
    validation = validate_feedback_consistency(payload)
    assert not validation["allow_emit"]
    assert any("critical_loss_point_not_covered_by_p7_reference_answer" in issue for issue in validation["blocking_issues"])


def test_loss_points_cover_oral_script() -> None:
    payload = _base_payload()
    payload["loss_points"] = [
        {
            "loss_point_id": "lp_critical_oral",
            "title": "关键口语修正",
            "deducted_points": 12,
            "reason": "口语化收束不足",
            "critical": True,
            "required_oral_terms": ["口语化收束"],
            "dimension_id": "expression",
        }
    ]
    payload["p7_reference_answer"] = "口语化收束和失败路径均要覆盖。"
    payload["oral_script"] = "口语化收束方面我会说明..."
    payload["score_result"]["score_value"] = compute_score_result_from_dimensions(payload["scoring_dimensions"])["score_value"]

    validation = validate_feedback_consistency(payload)
    assert validation["allow_emit"] is True

    payload["oral_script"] = "先讲背景，再讲技术细节和结论。"
    validation = validate_feedback_consistency(payload)
    assert not validation["allow_emit"]
    assert any("critical_loss_point_not_covered_by_oral_script" in issue for issue in validation["blocking_issues"])


def test_positive_evidence_points_retained_in_oral_script() -> None:
    payload = _base_payload()
    payload["positive_evidence_points"] = [
        {
            "point_id": "pe_retained",
            "title": "可观察指标",
            "evidence_excerpt": "上线后用监控指标验证",
            "dimension_id": "technical",
            "location": "oral_script",
        }
    ]
    payload["oral_script"] = "我会在上线后用监控指标验证策略是否生效。"
    payload["score_result"]["score_value"] = compute_score_result_from_dimensions(payload["scoring_dimensions"])["score_value"]

    validation = validate_feedback_consistency(payload)
    assert validation["allow_emit"] is True

    payload["oral_script"] = "我只给一个大概结论。"
    validation = validate_feedback_consistency(payload)
    assert not validation["allow_emit"]
    assert any("positive_point_not_retained_in_oral" in issue for issue in validation["blocking_issues"])


def test_validator_blocks_isolated_reference_answer() -> None:
    payload = {
        "schema_id": FEEDBACK_SCHEMA_ID,
        "schema_version": FEEDBACK_SCHEMA_VERSION,
        "status": "generated",
        "feedback_id": "fb_isolated",
        "feedback_text": "仅有参考答案文本。",
        "feedback_summary": "仅有参考答案文本。",
        "answer_diagnosis": {},
        "scoring_dimensions": [],
        "score_result": {"score_value": 0, "score_type": "polish_answer"},
        "positive_evidence_points": [],
        "loss_points": [],
        "missing_answer_dimensions": [],
        "interview_intent": "evaluate_depth",
        "p7_reference_answer": "先给一个通用模板答案。",
        "reference_answer_requirements": [],
        "oral_script": "",
        "oral_script_requirements": [],
        "knowledge_points": [],
        "technical_principles": [],
        "technical_gaps": [],
        "communication_gaps": [],
        "next_recommended_actions": [],
        "weakness_candidates": [],
        "asset_candidates": [],
        "validation_result_ref": None,
        "trace_refs": [],
        "low_confidence_flags": [],
        "feedback_metadata": {},
        "score_delta": 0,
        "dimension_delta": {},
        "improved_points": [],
        "remaining_gaps": [],
        "repeated_loss_points": [],
        "regressed_points": [],
        "mastery_status": "in_progress",
        "should_continue_same_question": False,
        "should_generate_next_question": False,
        "next_retry_focus": [],
    }

    validation = validate_feedback_consistency(payload)
    assert not validation["allow_emit"]
    assert "isolated_reference_answer" in validation["blocking_issues"]


def test_validator_blocks_oral_script_without_critical_loss_fix() -> None:
    payload = _base_payload()
    payload["loss_points"] = [
        {
            "loss_point_id": "lp_critical_oral_2",
            "title": "缺口修复不足",
            "deducted_points": 12,
            "reason": "口头版未体现失败补偿。",
            "critical": True,
            "required_oral_terms": ["失败补偿"],
            "dimension_id": "expression",
        }
    ]
    payload["oral_script"] = "我先说我的职责和目标。"
    payload["score_result"]["score_value"] = compute_score_result_from_dimensions(payload["scoring_dimensions"])["score_value"]

    validation = validate_feedback_consistency(payload)
    assert not validation["allow_emit"]
    assert any("critical_loss_point_not_covered_by_oral_script" in issue for issue in validation["blocking_issues"])


def test_validator_blocks_raw_prompt_and_completion_fields() -> None:
    payload = _base_payload()
    payload["prompt"] = "你是一个面试官..."
    payload["score_result"]["score_value"] = compute_score_result_from_dimensions(payload["scoring_dimensions"])["score_value"]

    validation = validate_feedback_consistency(payload)
    assert not validation["allow_emit"]
    assert any("prompt_present" in issue for issue in validation["blocking_issues"])


def test_safe_fallback_emits_compatible_payload() -> None:
    payload = _base_payload()
    payload["provider_payload"] = {"model": "gpt-4", "temperature": 0.7}
    payload["loss_points"] = []
    payload["score_result"]["score_value"] = compute_score_result_from_dimensions(payload["scoring_dimensions"])["score_value"]

    validation = validate_feedback_consistency(payload)
    fallback = validation["normalized_feedback_payload"]
    assert validation["allow_emit"] is False
    assert fallback["status"] == "blocked"
    assert fallback["score_result"]["score_value"] == 0
    assert "fallback_reason" in fallback["feedback_metadata"]


def test_old_feedback_payload_normalization_compatibility() -> None:
    legacy_payload = {
        "schema_id": FEEDBACK_SCHEMA_ID,
        "schema_version": FEEDBACK_SCHEMA_VERSION,
        "status": "generated",
        "contract_id": "P-POLISH-005",
        "feedback_id": "fb_legacy",
        "feedback_text": "legacy feedback",
        "feedback_summary": "legacy feedback",
        "score_result": {
            "score_value": 58,
            "score_type": "polish_answer",
            "score_version": "legacy",
        },
        "loss_points": [
            {
                "loss_point_id": "legacy_lp_1",
                "title": "legacy gap",
                "deducted_points": 20,
                "reason": "legacy reason",
            }
        ],
        "reference_answer": {
            "summary": "legacy reference answer summary",
            "outline": ["context", "decision", "trade-off"],
        },
        "interview_intent": "technical_depth",
        "question_text": "请描述一次项目故障时的处理过程。",
        "answer_id": "answer_legacy",
        "answer_text": "我当时先...。",
        "answer_diagnosis": {"strengths": ["clear architecture"]},
        "missing_answer_dimensions": [],
        "p7_reference_answer": "",
        "oral_script": "我会按 STAR 方式回答。",
        "knowledge_points": [],
        "technical_principles": [],
        "technical_gaps": [],
        "communication_gaps": [],
        "next_recommended_actions": ["answer_again"],
        "weakness_candidates": [],
        "asset_candidates": [],
        "trace_refs": [],
        "low_confidence_flags": [],
        "feedback_metadata": {},
        "remaining_gaps": [],
        "repeated_loss_points": [],
        "regressed_points": [],
    }

    normalized = normalize_feedback_payload(legacy_payload)
    assert normalized["p7_reference_answer"] == "legacy reference answer summary"
    assert isinstance(normalized["scoring_dimensions"], list)
    assert normalized["score_result"]["score_value"] == 58
