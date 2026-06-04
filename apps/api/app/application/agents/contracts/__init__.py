from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _tuple(values: tuple[str, ...] | list[str] | set[str] | str | None) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str):
        return (values,)
    return tuple(values)


def _metadata(values: dict[str, Any] | None) -> dict[str, Any]:
    return dict(values or {})


@dataclass(frozen=True)
class HandoffContract:
    contract_id: str
    candidate_ref_types: tuple[str, ...] = field(default_factory=tuple)
    formal_write_policy: str = "handoff_required"
    allowed_formal_targets: tuple[str, ...] = field(default_factory=tuple)
    confirmation_required: bool = True
    payload_schema_id: str = ""
    validation_refs: tuple[str, ...] = field(default_factory=tuple)
    quality_gate: str = ""
    side_effect_key: str = ""
    idempotency_key: str = ""
    formal_write_preconditions: tuple[str, ...] = field(default_factory=tuple)
    rollback_policy: str = ""
    user_confirmation_required: bool | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_ref_types", _tuple(self.candidate_ref_types))
        object.__setattr__(self, "allowed_formal_targets", _tuple(self.allowed_formal_targets))
        object.__setattr__(self, "validation_refs", _tuple(self.validation_refs))
        object.__setattr__(self, "formal_write_preconditions", _tuple(self.formal_write_preconditions))
        if self.user_confirmation_required is None:
            object.__setattr__(self, "user_confirmation_required", self.confirmation_required)


@dataclass(frozen=True)
class EvalContract:
    contract_id: str
    eval_suite_ids: tuple[str, ...] = field(default_factory=tuple)
    metrics: tuple[str, ...] = field(default_factory=tuple)
    failure_policy: str = "fail_closed"
    dataset_refs: tuple[str, ...] = field(default_factory=tuple)
    grader_refs: tuple[str, ...] = field(default_factory=tuple)
    regression_cases: tuple[str, ...] = field(default_factory=tuple)
    minimum_pass_criteria: str = ""
    ci_gate: str = "not_bound"
    failure_triage_policy: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "eval_suite_ids", _tuple(self.eval_suite_ids))
        object.__setattr__(self, "metrics", _tuple(self.metrics))
        object.__setattr__(self, "dataset_refs", _tuple(self.dataset_refs))
        object.__setattr__(self, "grader_refs", _tuple(self.grader_refs))
        object.__setattr__(self, "regression_cases", _tuple(self.regression_cases))


@dataclass(frozen=True)
class TraceContract:
    contract_id: str
    input_refs: tuple[str, ...] = field(default_factory=tuple)
    plan_refs: tuple[str, ...] = field(default_factory=tuple)
    skill_refs: tuple[str, ...] = field(default_factory=tuple)
    tool_refs: tuple[str, ...] = field(default_factory=tuple)
    policy_refs: tuple[str, ...] = field(default_factory=tuple)
    provider_refs: tuple[str, ...] = field(default_factory=tuple)
    candidate_refs: tuple[str, ...] = field(default_factory=tuple)
    validation_refs: tuple[str, ...] = field(default_factory=tuple)
    handoff_refs: tuple[str, ...] = field(default_factory=tuple)
    output_refs: tuple[str, ...] = field(default_factory=tuple)
    events: tuple[str, ...] = field(default_factory=tuple)
    forbidden_data: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_refs", _tuple(self.input_refs))
        object.__setattr__(self, "plan_refs", _tuple(self.plan_refs))
        object.__setattr__(self, "skill_refs", _tuple(self.skill_refs))
        object.__setattr__(self, "tool_refs", _tuple(self.tool_refs))
        object.__setattr__(self, "policy_refs", _tuple(self.policy_refs))
        object.__setattr__(self, "provider_refs", _tuple(self.provider_refs))
        object.__setattr__(self, "candidate_refs", _tuple(self.candidate_refs))
        object.__setattr__(self, "validation_refs", _tuple(self.validation_refs))
        object.__setattr__(self, "handoff_refs", _tuple(self.handoff_refs))
        object.__setattr__(self, "output_refs", _tuple(self.output_refs))
        object.__setattr__(self, "events", _tuple(self.events))
        object.__setattr__(self, "forbidden_data", _tuple(self.forbidden_data))


@dataclass(frozen=True)
class AgentDefinition:
    agent_id: str
    agent_name: str
    domain: str
    version: str
    maturity_level: str
    lifecycle_status: str
    mission: str
    user_goal: str
    autonomous_goal: str
    non_goals: tuple[str, ...]
    input_contract: object
    output_contract: object
    candidate_outputs: tuple[str, ...]
    formal_write_boundary: str
    skills: tuple[str, ...]
    tools: tuple[str, ...]
    memory_state: str
    planning_strategy: str
    guardrails: tuple[str, ...]
    hitl_triggers: tuple[str, ...]
    failure_semantics: str
    trace_contract: object
    eval_contract: EvalContract
    handoff_contract: HandoffContract
    versioning_policy: str
    task_types: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "non_goals", _tuple(self.non_goals))
        object.__setattr__(self, "candidate_outputs", _tuple(self.candidate_outputs))
        object.__setattr__(self, "skills", _tuple(self.skills))
        object.__setattr__(self, "tools", _tuple(self.tools))
        object.__setattr__(self, "guardrails", _tuple(self.guardrails))
        object.__setattr__(self, "hitl_triggers", _tuple(self.hitl_triggers))
        object.__setattr__(self, "task_types", _tuple(self.task_types))


@dataclass(frozen=True)
class SkillDefinition:
    skill_id: str
    skill_name: str
    owner_agent_ids: tuple[str, ...]
    input_schema_id: str
    output_schema_id: str
    implementation_type: str
    deterministic_policy_refs: tuple[str, ...]
    llm_refs: tuple[str, ...]
    tool_refs: tuple[str, ...]
    timeout_policy: str
    retry_policy: str
    failure_semantics: str
    trace_events: tuple[str, ...]
    eval_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "owner_agent_ids", _tuple(self.owner_agent_ids))
        object.__setattr__(self, "deterministic_policy_refs", _tuple(self.deterministic_policy_refs))
        object.__setattr__(self, "llm_refs", _tuple(self.llm_refs))
        object.__setattr__(self, "tool_refs", _tuple(self.tool_refs))
        object.__setattr__(self, "trace_events", _tuple(self.trace_events))
        object.__setattr__(self, "eval_refs", _tuple(self.eval_refs))


@dataclass(frozen=True)
class ToolDefinition:
    tool_id: str
    tool_name: str
    input_schema_id: str
    output_schema_id: str
    permission_scope: str
    owner_scope: str
    side_effect_policy: str
    timeout_seconds: int
    retry_policy: str
    allowed_callers: tuple[str, ...]
    forbidden_data: tuple[str, ...]
    trace_events: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "allowed_callers", _tuple(self.allowed_callers))
        object.__setattr__(self, "forbidden_data", _tuple(self.forbidden_data))
        object.__setattr__(self, "trace_events", _tuple(self.trace_events))


@dataclass(frozen=True)
class AgentExecutionPlan:
    plan_id: str
    agent_id: str
    owner_id: str
    objective: str
    steps: tuple[str, ...] = field(default_factory=tuple)
    candidate_output_refs: tuple[str, ...] = field(default_factory=tuple)
    handoff_contract: HandoffContract | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "steps", _tuple(self.steps))
        object.__setattr__(self, "candidate_output_refs", _tuple(self.candidate_output_refs))
        object.__setattr__(self, "metadata", _metadata(self.metadata))


@dataclass(frozen=True)
class AgentExecutionTrace:
    trace_id: str
    run_id: str
    agent_id: str
    events: tuple[str, ...] = field(default_factory=tuple)
    candidate_refs: tuple[str, ...] = field(default_factory=tuple)
    handoff_refs: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)
    input_refs: tuple[str, ...] = field(default_factory=tuple)
    plan_refs: tuple[str, ...] = field(default_factory=tuple)
    skill_refs: tuple[str, ...] = field(default_factory=tuple)
    tool_refs: tuple[str, ...] = field(default_factory=tuple)
    policy_refs: tuple[str, ...] = field(default_factory=tuple)
    provider_refs: tuple[str, ...] = field(default_factory=tuple)
    validation_refs: tuple[str, ...] = field(default_factory=tuple)
    output_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "events", _tuple(self.events))
        object.__setattr__(self, "candidate_refs", _tuple(self.candidate_refs))
        object.__setattr__(self, "handoff_refs", _tuple(self.handoff_refs))
        object.__setattr__(self, "metadata", _metadata(self.metadata))
        object.__setattr__(self, "input_refs", _tuple(self.input_refs))
        object.__setattr__(self, "plan_refs", _tuple(self.plan_refs))
        object.__setattr__(self, "skill_refs", _tuple(self.skill_refs))
        object.__setattr__(self, "tool_refs", _tuple(self.tool_refs))
        object.__setattr__(self, "policy_refs", _tuple(self.policy_refs))
        object.__setattr__(self, "provider_refs", _tuple(self.provider_refs))
        object.__setattr__(self, "validation_refs", _tuple(self.validation_refs))
        object.__setattr__(self, "output_refs", _tuple(self.output_refs))


@dataclass(frozen=True)
class AgentExecutionResult:
    run_id: str
    status: str
    candidate_refs: tuple[str, ...]
    trace: AgentExecutionTrace
    handoff_refs: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_refs", _tuple(self.candidate_refs))
        object.__setattr__(self, "handoff_refs", _tuple(self.handoff_refs))
        object.__setattr__(self, "metadata", _metadata(self.metadata))


@dataclass(frozen=True)
class AgentExecutionStatus:
    run_id: str
    agent_id: str
    status: str
    candidate_refs: tuple[str, ...] = field(default_factory=tuple)
    trace_refs: tuple[str, ...] = field(default_factory=tuple)
    handoff_refs: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_refs", _tuple(self.candidate_refs))
        object.__setattr__(self, "trace_refs", _tuple(self.trace_refs))
        object.__setattr__(self, "handoff_refs", _tuple(self.handoff_refs))
        object.__setattr__(self, "metadata", _metadata(self.metadata))


@dataclass(frozen=True)
class AgentExecutionTimeline:
    run_id: str
    events: tuple[AgentExecutionTrace, ...] = field(default_factory=tuple)
    cursor: str | None = None
    has_more: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "events", tuple(self.events))


__all__ = [
    "AgentDefinition",
    "AgentExecutionPlan",
    "AgentExecutionResult",
    "AgentExecutionStatus",
    "AgentExecutionTimeline",
    "AgentExecutionTrace",
    "EvalContract",
    "HandoffContract",
    "SkillDefinition",
    "ToolDefinition",
    "TraceContract",
]
