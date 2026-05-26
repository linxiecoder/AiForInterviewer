"""Versioned policies for polish question generation and progress evidence."""

from __future__ import annotations

QUESTION_GENERATION_POLICY_VERSION = "polish_question_generation_policy.v1"

SOURCE_PRIORITY_POLICY_BY_PURPOSE: dict[str, dict[str, int]] = {
    "initial_plan": {
        "job_requirement": 1,
        "match_gap": 2,
        "match_focus": 3,
        "resume_project": 4,
        "resume_skill": 5,
        "job_responsibility": 6,
        "resume_work_experience": 7,
        "match_suggested_question": 8,
        "job_other_note": 9,
        "resume_summary": 10,
        "resume_education": 11,
        "turn_feedback": 12,
        "turn_question": 13,
        "turn_answer": 14,
        "asset_summary": 15,
        "weakness": 16,
    },
    "state_refresh": {
        "turn_feedback": 1,
        "match_gap": 2,
        "match_focus": 3,
        "resume_project": 4,
        "job_requirement": 5,
        "turn_question": 6,
        "turn_answer": 7,
        "resume_skill": 8,
        "job_responsibility": 9,
        "resume_work_experience": 10,
        "match_suggested_question": 11,
        "job_other_note": 12,
        "resume_summary": 13,
        "asset_summary": 14,
        "weakness": 15,
    },
    "next_question": {
        "match_gap": 1,
        "turn_feedback": 2,
        "job_requirement": 3,
        "resume_project": 4,
        "resume_skill": 5,
        "job_responsibility": 6,
        "turn_question": 7,
        "turn_answer": 8,
        "match_focus": 9,
        "match_suggested_question": 10,
        "resume_work_experience": 11,
        "job_other_note": 12,
        "resume_summary": 13,
    },
}

SEMANTIC_JOB_SOURCE_TYPES = frozenset({"job_requirement", "job_responsibility"})
SEMANTIC_RESUME_SOURCE_TYPES = frozenset({"resume_project", "resume_skill", "resume_work_experience"})

QUESTION_KIND_TAXONOMY = {
    "project_deep_dive": {"schema_value": "project_deep_dive", "signals": ()},
    "technical_chain_deep_dive": {"schema_value": "technical_chain_deep_dive", "signals": ("链路", "状态", "一致性", "事务", "锁", "技术")},
    "failure_recovery_deep_dive": {"schema_value": "failure_recovery_deep_dive", "signals": ("失败", "异常", "补偿", "降级", "恢复", "回滚")},
    "tradeoff_design": {"schema_value": "tradeoff_design", "signals": ("取舍", "设计", "方案", "架构", "权衡")},
    "clarification_needed": {"schema_value": "clarification_needed", "signals": ()},
}
