"""Versioned policies for polish question generation and progress evidence."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace

QUESTION_GENERATION_POLICY_VERSION = "polish_question_generation_policy.v1"
QUESTION_GENERATION_POLICY_DEFAULT_SOURCE = "fallback_default"
QUESTION_GENERATION_POLICY_DEFAULT_SOURCE_TYPE = "fallback_default"
DEFAULT_QUESTION_GENERATION_POLICY_SOURCE_CHAIN = (
    "api_dependency:default_question_generation_runtime_policy",
    "python_default:QuestionGenerationRuntimePolicy",
)


@dataclass(frozen=True)
class QuestionGenerationPolicyResolutionContext:
    owner_id: str
    actor_id: str
    tenant_id: str | None = None
    session_id: str | None = None
    job_id: str | None = None
    job_version_id: str | None = None
    generation_mode: str | None = None
    requested_progress_node_ref: str | None = None
    selected_progress_node_ref: str | None = None
    request_source: str = "app.api.v1.polish.create_polish_question_task"

    def to_metadata(self) -> dict[str, str]:
        values = {
            "owner_id": self.owner_id,
            "actor_id": self.actor_id,
            "tenant_id": self.tenant_id or self.owner_id,
            "session_id": self.session_id,
            "job_id": self.job_id,
            "job_version_id": self.job_version_id,
            "generation_mode": self.generation_mode,
            "requested_progress_node_ref": self.requested_progress_node_ref,
            "selected_progress_node_ref": self.selected_progress_node_ref,
            "request_source": self.request_source,
        }
        return {key: str(value) for key, value in values.items() if value is not None and str(value)}


@dataclass(frozen=True)
class QuestionGenerationRuntimePolicy:
    policy_version: str = QUESTION_GENERATION_POLICY_VERSION
    prompt_asset_id: str = "polish_question_generation"
    prompt_version: str = "polish_question_generation_prompt.v3"
    prompt_schema_id: str = "polish_question_generation_output_v2"
    prompt_schema_version: str = "v2"
    task_type: str = "polish_question_generation"
    contract_ids: tuple[str, ...] = ("P-POLISH-002", "P-SHARED-001", "P-SHARED-003")
    llm_max_retries: int = 2
    llm_retry_backoff_seconds: float = 0.25
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
    source: str = QUESTION_GENERATION_POLICY_DEFAULT_SOURCE
    source_type: str = QUESTION_GENERATION_POLICY_DEFAULT_SOURCE_TYPE
    source_version: str = QUESTION_GENERATION_POLICY_VERSION
    source_chain: tuple[str, ...] = DEFAULT_QUESTION_GENERATION_POLICY_SOURCE_CHAIN
    fallback: bool = True
    resolution_context: dict[str, str] = field(default_factory=dict)
    policy_item_sources: dict[str, dict[str, str]] = field(
        default_factory=lambda: {
            key: {
                "source": "python_default",
                "version": QUESTION_GENERATION_POLICY_VERSION,
                "override": "none",
            }
            for key in (
                "contract_ids",
                "prompt_version",
                "prompt_schema_id",
                "candidate_statuses",
                "candidate_types",
                "candidate_payload_schema_ids",
                "source_priority_by_purpose",
                "question_kind_taxonomy",
            )
        }
    )

    def __post_init__(self) -> None:
        if (
            self.source != QUESTION_GENERATION_POLICY_DEFAULT_SOURCE
            and self.source_type == QUESTION_GENERATION_POLICY_DEFAULT_SOURCE_TYPE
            and self.fallback
        ):
            object.__setattr__(self, "source_type", "explicit_policy")
            object.__setattr__(self, "fallback", False)
            if self.source_chain == DEFAULT_QUESTION_GENERATION_POLICY_SOURCE_CHAIN:
                object.__setattr__(self, "source_chain", (f"explicit_policy:{self.source}",))


QuestionGenerationRuntimePolicyResolver = Callable[
    [QuestionGenerationPolicyResolutionContext, QuestionGenerationRuntimePolicy | None],
    QuestionGenerationRuntimePolicy,
]

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


def mark_question_generation_runtime_policy_source(
    policy: QuestionGenerationRuntimePolicy,
    *,
    source: str,
    source_type: str,
    fallback: bool,
    source_chain: tuple[str, ...],
    source_version: str | None = None,
) -> QuestionGenerationRuntimePolicy:
    return replace(
        policy,
        source=source,
        source_type=source_type,
        source_version=source_version or policy.policy_version,
        source_chain=source_chain,
        fallback=fallback,
        policy_item_sources=_policy_item_sources_for_source(
            policy,
            source=source,
            source_version=source_version or policy.policy_version,
            override=source_type if not fallback else "none",
        ),
    )


def resolve_question_generation_runtime_policy(
    context: QuestionGenerationPolicyResolutionContext,
    base_policy: QuestionGenerationRuntimePolicy | None = None,
) -> QuestionGenerationRuntimePolicy:
    policy = base_policy or DEFAULT_QUESTION_GENERATION_RUNTIME_POLICY
    if policy.fallback:
        policy = mark_question_generation_runtime_policy_source(
            policy,
            source=QUESTION_GENERATION_POLICY_DEFAULT_SOURCE,
            source_type=QUESTION_GENERATION_POLICY_DEFAULT_SOURCE_TYPE,
            fallback=True,
            source_chain=(
                context.request_source,
                "api_dependency:default_question_generation_runtime_policy",
                "python_default:QuestionGenerationRuntimePolicy",
            ),
            source_version=QUESTION_GENERATION_POLICY_VERSION,
        )
    return with_question_generation_policy_resolution(policy, context)


def with_question_generation_policy_resolution(
    policy: QuestionGenerationRuntimePolicy,
    context: QuestionGenerationPolicyResolutionContext,
) -> QuestionGenerationRuntimePolicy:
    chain = tuple(dict.fromkeys((context.request_source, *policy.source_chain)))
    item_sources = policy.policy_item_sources
    if (
        not policy.fallback
        and item_sources
        and all(value.get("source") == "python_default" for value in item_sources.values())
    ):
        item_sources = _policy_item_sources_for_source(
            policy,
            source=policy.source,
            source_version=policy.source_version,
            override=policy.source_type,
        )
    return replace(
        policy,
        source_chain=chain,
        resolution_context=context.to_metadata(),
        policy_item_sources=item_sources,
    )


def _default_policy_item_sources() -> dict[str, dict[str, str]]:
    item_source = {
        "source": "python_default",
        "version": QUESTION_GENERATION_POLICY_VERSION,
        "override": "none",
    }
    return {
        "contract_ids": dict(item_source),
        "prompt_version": dict(item_source),
        "prompt_schema_id": dict(item_source),
        "candidate_statuses": dict(item_source),
        "candidate_types": dict(item_source),
        "candidate_payload_schema_ids": dict(item_source),
        "source_priority_by_purpose": dict(item_source),
        "question_kind_taxonomy": dict(item_source),
    }


def _policy_item_sources_for_source(
    policy: QuestionGenerationRuntimePolicy,
    *,
    source: str,
    source_version: str,
    override: str,
) -> dict[str, dict[str, str]]:
    base_sources = policy.policy_item_sources or _default_policy_item_sources()
    sources: dict[str, dict[str, str]] = {}
    for key, item_source in base_sources.items():
        source_payload = dict(item_source)
        if override != "none":
            source_payload["source"] = source
            source_payload["version"] = source_version
            source_payload["override"] = override
        sources[str(key)] = {
            "source": str(source_payload.get("source") or source),
            "version": str(source_payload.get("version") or source_version),
            "override": str(source_payload.get("override") or override),
        }
    return sources
