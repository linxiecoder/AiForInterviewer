"""Compact prompt bundle for polish answer feedback LLM generation."""

from __future__ import annotations

from typing import Any

from app.application.polish.feedback_contracts import (
    FEEDBACK_SCHEMA_ID,
    FEEDBACK_SCHEMA_VERSION,
    FeedbackInput,
    RetryFeedbackInput,
)
from app.application.polish.progress_context import truncate_text


POLISH_ANSWER_FEEDBACK_TASK_TYPE = "polish_answer_feedback_generation"
POLISH_ANSWER_FEEDBACK_PROMPT_VERSION = "polish_answer_feedback_prompt_v1"
POLISH_ANSWER_FEEDBACK_SCHEMA_ID = FEEDBACK_SCHEMA_ID
POLISH_ANSWER_FEEDBACK_SCHEMA_VERSION = FEEDBACK_SCHEMA_VERSION
POLISH_ANSWER_FEEDBACK_CONTRACT_IDS = ("P-POLISH-003", "P-POLISH-004", "P-POLISH-005", "P-POLISH-009")


def build_polish_feedback_prompt_bundle(
    *,
    feedback_input: FeedbackInput,
    deterministic_payload: dict[str, Any],
) -> dict[str, Any]:
    evidence_bundle = build_polish_feedback_evidence_bundle(
        feedback_input=feedback_input,
        deterministic_payload=deterministic_payload,
    )
    return {
        "task_type": POLISH_ANSWER_FEEDBACK_TASK_TYPE,
        "prompt_version": POLISH_ANSWER_FEEDBACK_PROMPT_VERSION,
        "schema_id": POLISH_ANSWER_FEEDBACK_SCHEMA_ID,
        "schema_version": POLISH_ANSWER_FEEDBACK_SCHEMA_VERSION,
        "contract_ids": list(POLISH_ANSWER_FEEDBACK_CONTRACT_IDS),
        "task_constraints": [
            "只基于 compact feedback input 生成结构化 JSON。",
            "不得输出 raw prompt、completion、provider payload、hidden rubric 或精确通过概率。",
            "不得写正式 ScoreResult、Weakness 或 Asset；仅返回反馈 payload 候选。",
            "同题重答必须返回 delta 字段。",
        ],
        "output_schema": _output_schema(feedback_input.answer_round),
        "evidence_bundle": evidence_bundle,
        "redaction_boundary": {
            "raw_prompt_persisted": False,
            "raw_completion_persisted": False,
            "provider_payload_persisted": False,
            "full_resume_or_jd_included": False,
            "full_previous_feedback_payload_included": False,
        },
    }


def build_polish_feedback_evidence_bundle(
    *,
    feedback_input: FeedbackInput,
    deterministic_payload: dict[str, Any],
) -> dict[str, Any]:
    metadata = feedback_input.question_metadata if isinstance(feedback_input.question_metadata, dict) else {}
    bundle: dict[str, Any] = {
        "question_text": truncate_text(feedback_input.question_text, max_chars=900),
        "question_metadata": _question_metadata_summary(metadata),
        "question_pattern": truncate_text(feedback_input.question_pattern, max_chars=120),
        "expected_answer_dimensions": _safe_string_list(feedback_input.expected_answer_dimensions, limit=12),
        "interview_intent": truncate_text(feedback_input.interview_intent, max_chars=300),
        "scenario_constraint_summary": _scenario_constraint_summary(metadata),
        "answer_text": truncate_text(feedback_input.answer_text, max_chars=1800),
        "answer_round": feedback_input.answer_round,
        "previous_answer_compact_summaries": [],
        "previous_feedback_compact_summaries": [],
        "scoring_rubric_summary": _scoring_rubric_summary(deterministic_payload),
        "positive_loss_extraction_hints": _positive_loss_extraction_hints(deterministic_payload),
        "source_availability": truncate_text(feedback_input.source_availability, max_chars=80),
        "low_confidence_flags": _compact_low_confidence_flags(feedback_input.low_confidence_flags),
        "polish_theme": truncate_text(feedback_input.polish_theme, max_chars=80),
        "answer_completeness_signals": _answer_completeness_signals(feedback_input.answer_text),
    }
    if isinstance(feedback_input, RetryFeedbackInput):
        bundle["previous_answer_compact_summaries"] = _previous_answer_summaries(feedback_input.previous_answer_rounds)
        bundle["previous_feedback_compact_summaries"] = _previous_feedback_summaries(feedback_input.previous_feedbacks)
    fixture_marker = _safe_text(metadata.get("feedback_llm_fixture"), max_chars=80)
    if fixture_marker:
        bundle["fixture_marker"] = fixture_marker
    return bundle


def _output_schema(answer_round: int) -> dict[str, Any]:
    required = [
        "schema_id",
        "schema_version",
        "status",
        "feedback_summary",
        "answer_diagnosis",
        "scoring_dimensions",
        "score_result",
        "positive_evidence_points",
        "loss_points",
        "missing_answer_dimensions",
        "p7_reference_answer",
        "reference_answer_requirements",
        "oral_script",
        "oral_script_requirements",
        "knowledge_points",
        "technical_principles",
        "technical_gaps",
        "communication_gaps",
        "next_recommended_actions",
        "low_confidence_flags",
        "feedback_metadata",
    ]
    if answer_round > 1:
        required.extend(
            [
                "score_delta",
                "dimension_delta",
                "improved_points",
                "remaining_gaps",
                "repeated_loss_points",
                "regressed_points",
                "mastery_status",
                "should_continue_same_question",
                "should_generate_next_question",
                "next_retry_focus",
                "updated_reference_answer",
                "updated_oral_script",
            ]
        )
    return {
        "schema_id": POLISH_ANSWER_FEEDBACK_SCHEMA_ID,
        "schema_version": POLISH_ANSWER_FEEDBACK_SCHEMA_VERSION,
        "required": required,
        "forbidden": [
            "raw_prompt",
            "prompt",
            "completion",
            "raw_completion",
            "provider_payload",
            "hidden_rubric",
            "hidden_scoring_rules",
            "pass_probability",
            "precise_pass_probability",
            "formal_weakness",
            "formal_asset",
        ],
    }


def _question_metadata_summary(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "question_pattern": _safe_text(metadata.get("question_pattern"), max_chars=120),
        "interview_intent": _safe_text(metadata.get("interview_intent"), max_chars=300),
        "expected_answer_dimensions": _safe_string_list(metadata.get("expected_answer_dimensions"), limit=12),
        "scenario_constraint_summary": _scenario_constraint_summary(metadata),
        "source_availability": _safe_text(metadata.get("source_availability"), max_chars=80),
        "low_confidence_flags": _safe_string_list(metadata.get("low_confidence_flags"), limit=20),
    }


def _scenario_constraint_summary(metadata: dict[str, Any]) -> str:
    for key in ("scenario_constraint_summary", "scenario_constraint", "interview_intent"):
        value = _safe_text(metadata.get(key), max_chars=400)
        if value:
            return value
    return ""


def _scoring_rubric_summary(payload: dict[str, Any]) -> dict[str, Any]:
    dimensions = []
    for dimension in _dict_list(payload.get("scoring_dimensions"))[:12]:
        dimensions.append(
            {
                "dimension_id": _safe_text(dimension.get("dimension_id"), max_chars=120),
                "max_score": dimension.get("max_score"),
                "weight": dimension.get("weight"),
                "is_critical": bool(dimension.get("is_critical", False)),
            }
        )
    return {
        "score_type": "polish_answer",
        "schema_version": POLISH_ANSWER_FEEDBACK_SCHEMA_VERSION,
        "dimensions": dimensions,
        "score_scale": "0-100",
    }


def _positive_loss_extraction_hints(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "positive_evidence_titles": [
            _safe_text(point.get("title"), max_chars=160)
            for point in _dict_list(payload.get("positive_evidence_points"))[:8]
            if _safe_text(point.get("title"), max_chars=160)
        ],
        "critical_loss_titles": [
            _safe_text(point.get("title"), max_chars=160)
            for point in _dict_list(payload.get("loss_points"))[:8]
            if point.get("critical") and _safe_text(point.get("title"), max_chars=160)
        ],
        "missing_dimensions": [
            _safe_text(item.get("dimension"), max_chars=120)
            for item in _dict_list(payload.get("missing_answer_dimensions"))[:8]
            if _safe_text(item.get("dimension"), max_chars=120)
        ],
    }


def _previous_answer_summaries(previous_answers: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    result = []
    for answer in previous_answers[-5:]:
        result.append(
            {
                "answer_id": _safe_text(answer.get("answer_id"), max_chars=120),
                "answer_round": answer.get("answer_round"),
                "answer_text_summary": truncate_text(answer.get("answer_text"), max_chars=500),
            }
        )
    return result


def _previous_feedback_summaries(previous_feedbacks: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    result = []
    for feedback in previous_feedbacks[-5:]:
        result.append(
            {
                "feedback_id": _safe_text(feedback.get("feedback_id"), max_chars=120),
                "score_result": _compact_score_result(feedback.get("score_result")),
                "scoring_dimensions": _compact_dimensions(feedback.get("scoring_dimensions")),
                "loss_points": _compact_loss_points(feedback.get("loss_points")),
                "reference_answer_summary": truncate_text(
                    feedback.get("reference_answer_summary") or feedback.get("p7_reference_answer"),
                    max_chars=500,
                ),
                "oral_script_summary": truncate_text(
                    feedback.get("oral_script_summary") or feedback.get("oral_script"),
                    max_chars=500,
                ),
            }
        )
    return result


def _compact_score_result(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        key: value[key]
        for key in ("score_type", "score_value", "score_version", "rubric_version", "confidence_level", "weight_total")
        if key in value
    }


def _compact_dimensions(value: object) -> list[dict[str, Any]]:
    return [
        {
            key: dimension[key]
            for key in ("dimension_id", "score_value", "max_score", "weight", "is_critical", "rationale")
            if key in dimension
        }
        for dimension in _dict_list(value)[:12]
    ]


def _compact_loss_points(value: object) -> list[dict[str, Any]]:
    return [
        {
            key: point[key]
            for key in ("loss_point_id", "title", "critical", "dimension_id", "required_reference_terms", "required_oral_terms")
            if key in point
        }
        for point in _dict_list(value)[:12]
    ]


def _compact_low_confidence_flags(value: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    flags = []
    for flag in value[:20]:
        flags.append(
            {
                "flag_id": _safe_text(flag.get("flag_id"), max_chars=120),
                "reason": _safe_text(flag.get("reason"), max_chars=240),
                "impact_scope": _safe_text(flag.get("impact_scope"), max_chars=200),
            }
        )
    return flags


def _answer_completeness_signals(answer_text: str) -> dict[str, Any]:
    text = answer_text or ""
    return {
        "char_count": len(text),
        "mentions_failure_path": any(term in text for term in ("失败", "异常", "补偿", "兜底")),
        "mentions_metrics": any(term in text for term in ("指标", "验证", "压测", "监控", "告警")),
        "mentions_tradeoff": any(term in text for term in ("取舍", "权衡", "成本", "一致性")),
    }


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, (list, tuple)):
        return []
    return [item for item in value if isinstance(item, dict)]


def _safe_string_list(value: object, *, limit: int, max_chars: int = 240) -> list[str]:
    if isinstance(value, str):
        items: list[object] = [value]
    elif isinstance(value, (list, tuple, set)):
        items = list(value)
    else:
        return []
    result: list[str] = []
    for item in items:
        text = _safe_text(item, max_chars=max_chars)
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def _safe_text(value: object, *, max_chars: int) -> str:
    if value is None:
        return ""
    return truncate_text(str(value).strip(), max_chars=max_chars)
