"""Versioned policies for polish question generation and progress evidence."""

from __future__ import annotations

from dataclasses import dataclass, field

QUESTION_GENERATION_POLICY_VERSION = "polish_question_generation_policy.v1"


@dataclass(frozen=True)
class QuestionGenerationRuntimePolicy:
    policy_version: str = QUESTION_GENERATION_POLICY_VERSION
    prompt_asset_id: str = "polish_question_generation"
    prompt_version: str = "polish_question_generation_prompt.v3"
    prompt_schema_id: str = "polish_question_generation_output_v2"
    prompt_schema_version: str = "v2"
    task_type: str = "polish_question_generation"
    contract_ids: tuple[str, ...] = ("P-POLISH-002", "P-SHARED-001", "P-SHARED-003")
    candidate_statuses: frozenset[str] = field(default_factory=lambda: frozenset({"accepted", "passed"}))
    candidate_types: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"polish_question", "question_candidate", "polish_question_candidate"}
        )
    )
    candidate_payload_schema_ids: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                "polish_question_candidate.v1",
                "polish_question_candidate_v1",
                "polish_question_generation_output_v1",
            }
        )
    )
    source_priority_by_purpose: dict[str, dict[str, int]] = field(
        default_factory=lambda: _copy_source_priority_policy()
    )
    question_kind_taxonomy: dict[str, dict[str, object]] = field(
        default_factory=lambda: _copy_question_kind_taxonomy()
    )
    source: str = "default_controlled_policy"

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


def _copy_source_priority_policy() -> dict[str, dict[str, int]]:
    policy = {purpose: dict(priority_map) for purpose, priority_map in SOURCE_PRIORITY_POLICY_BY_PURPOSE.items()}
    policy["next_question"] = {
        **policy.get("next_question", {}),
        "resume_project": 1,
        "resume_work_experience": 2,
        "resume_skill": 3,
        "job_requirement": 4,
        "match_gap": 5,
        "match_focus": 6,
    }
    return policy


def _copy_question_kind_taxonomy() -> dict[str, dict[str, object]]:
    return {
        kind: {
            "schema_value": str(item.get("schema_value") or kind),
            "signals": tuple(item.get("signals") or ()),
        }
        for kind, item in QUESTION_KIND_TAXONOMY.items()
    }


DEFAULT_QUESTION_GENERATION_RUNTIME_POLICY = QuestionGenerationRuntimePolicy()
