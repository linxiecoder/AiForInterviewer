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


_BLOCKED_METADATA_KEYS = (
    "raw_prompt",
    "system_prompt",
    "developer_prompt",
    "raw_completion",
    "provider_payload",
    "raw_provider_payload",
    "checkpoint_payload",
    "full_source_body",
    "full_resume",
    "full_jd",
    "full_answer",
    "full_asset_body",
    "hidden_rubric",
    "formal_refs",
    "api_key",
    "token",
    "cookie",
    "secret",
)

P8_REQUIRED_RUNTIME_STOP_CONDITIONS = (
    "max_steps_exceeded",
    "timeout",
    "validation_failed",
    "tool_not_allowed",
    "formal_write_requested",
    "interrupt_required",
    "provider_failed",
)

CROSS_AGENT_REQUIRED_FORBIDDEN_DATA = tuple(
    sorted(
        {
            "api_key",
            "api_keys",
            "checkpoint_payload",
            "cookie",
            "cookies",
            "developer_prompt",
            "full_answer",
            "full_asset_body",
            "full_jd",
            "full_resume",
            "full_source_body",
            "hidden_rubric",
            "provider_payload",
            "raw_completion",
            "raw_prompt",
            "raw_provider_payload",
            "secret",
            "secrets",
            "system_prompt",
            "token",
            "tokens",
        }
    )
)

CROSS_AGENT_ALLOWED_SIDE_EFFECT_POLICIES = (
    "read_only",
    "candidate_write",
    "formal_write_handoff_only",
)

CROSS_AGENT_HITL_TRIGGER_TYPES = (
    "asset_conflict",
    "formal_write_requested",
    "low_confidence",
    "ambiguous_ownership",
    "validation_failed_partial_result",
)

CROSS_AGENT_ALLOWED_RESUME_ACTIONS = (
    "continue",
    "approve_candidate",
    "reject_candidate",
    "request_revision",
    "cancel",
    "acknowledge",
)


def _safe_metadata(values: dict[str, Any] | None) -> dict[str, Any]:
    return _safe_metadata_value(dict(values or {}))


def _safe_metadata_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _safe_metadata_value(item)
            for key, item in value.items()
            if not _metadata_key_is_blocked(key)
        }
    if isinstance(value, list):
        return [_safe_metadata_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_safe_metadata_value(item) for item in value)
    if isinstance(value, set):
        return tuple(_safe_metadata_value(item) for item in sorted(value, key=str))
    return value


def _metadata_key_is_blocked(key: Any) -> bool:
    return any(item in str(key).lower() for item in _BLOCKED_METADATA_KEYS)


def _required_text(value: str, *, label: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{label} is required")
    return normalized


def _required_tuple(
    values: tuple[str, ...] | list[str] | set[str] | str | None,
    *,
    label: str,
) -> tuple[str, ...]:
    normalized = _tuple(values)
    if not normalized:
        raise ValueError(f"{label} are required")
    return normalized


@dataclass(frozen=True)
class HandoffContract:
    """Contract-only handoff metadata for candidate refs before any formal write."""

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
    cross_agent_route: CrossAgentHandoffRoute | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_ref_types", _tuple(self.candidate_ref_types))
        object.__setattr__(self, "allowed_formal_targets", _tuple(self.allowed_formal_targets))
        object.__setattr__(self, "validation_refs", _tuple(self.validation_refs))
        object.__setattr__(self, "formal_write_preconditions", _tuple(self.formal_write_preconditions))
        if self.user_confirmation_required is None:
            object.__setattr__(self, "user_confirmation_required", self.confirmation_required)
        if self.cross_agent_route is not None and not isinstance(self.cross_agent_route, CrossAgentHandoffRoute):
            raise ValueError("cross_agent_route must be CrossAgentHandoffRoute")


@dataclass(frozen=True)
class AgentHandoffEnvelope:
    """Typed candidate handoff envelope between AgentExecutor-compatible agents."""

    candidate_ref: str
    candidate_type: str
    payload_schema_id: str
    trace_refs: tuple[str, ...]
    validation_refs: tuple[str, ...]
    side_effect_key: str
    idempotency_key: str
    handoff_ref: str = ""
    asset_update_candidate_ref: str = ""
    asset_body_ref: str = ""
    asset_schema_id: str = ""
    formal_write_blocked_until: str = ""
    user_confirmation_required: bool | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.candidate_ref.strip():
            raise ValueError("candidate_ref is required")
        if not self.candidate_type.strip():
            raise ValueError("candidate_type is required")
        if not self.payload_schema_id.strip():
            raise ValueError("payload_schema_id is required")
        if not self.side_effect_key.strip():
            raise ValueError("side_effect_key is required")
        if not self.idempotency_key.strip():
            raise ValueError("idempotency_key is required")
        object.__setattr__(self, "trace_refs", _tuple(self.trace_refs))
        object.__setattr__(self, "validation_refs", _tuple(self.validation_refs))
        object.__setattr__(self, "asset_update_candidate_ref", str(self.asset_update_candidate_ref).strip())
        object.__setattr__(self, "asset_body_ref", str(self.asset_body_ref).strip())
        object.__setattr__(self, "asset_schema_id", str(self.asset_schema_id).strip())
        object.__setattr__(self, "formal_write_blocked_until", str(self.formal_write_blocked_until).strip())
        if not self.trace_refs:
            raise ValueError("trace_refs are required")
        if not self.validation_refs:
            raise ValueError("validation_refs are required")
        if self.candidate_type == "asset_update_candidate":
            if not self.asset_update_candidate_ref:
                object.__setattr__(self, "asset_update_candidate_ref", self.candidate_ref)
            if self.user_confirmation_required is None:
                object.__setattr__(self, "user_confirmation_required", True)
            if not self.formal_write_blocked_until:
                object.__setattr__(self, "formal_write_blocked_until", "user_confirmation")
        if not self.handoff_ref:
            object.__setattr__(self, "handoff_ref", f"handoff_{self.candidate_ref}")
        object.__setattr__(self, "metadata", _safe_metadata(self.metadata))


@dataclass(frozen=True)
class EvalContract:
    """Contract-only evaluation metadata for agent catalog gates, not an eval runner."""

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
    """Contract-only trace shape for candidate-producing agent workflows."""

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
    """Agent catalog contract for candidate production without direct formal writes."""

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
    schema_version: str = "agent-definition.v1"
    catalog_revision: str = ""

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
    """Skill catalog contract for planned capability slices with no runtime execution."""

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
    purpose: str = ""
    implementation_ref: str = ""
    preconditions: tuple[str, ...] = field(default_factory=tuple)
    postconditions: tuple[str, ...] = field(default_factory=tuple)
    fallback_policy: str = ""
    lifecycle_status: str = "contract_only"
    definition_version: str = "1.0.0"
    schema_version: str = "skill-definition.v1"
    test_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "owner_agent_ids", _tuple(self.owner_agent_ids))
        object.__setattr__(self, "deterministic_policy_refs", _tuple(self.deterministic_policy_refs))
        object.__setattr__(self, "llm_refs", _tuple(self.llm_refs))
        object.__setattr__(self, "tool_refs", _tuple(self.tool_refs))
        object.__setattr__(self, "trace_events", _tuple(self.trace_events))
        object.__setattr__(self, "eval_refs", _tuple(self.eval_refs))
        object.__setattr__(self, "preconditions", _tuple(self.preconditions))
        object.__setattr__(self, "postconditions", _tuple(self.postconditions))
        object.__setattr__(self, "test_refs", _tuple(self.test_refs))


@dataclass(frozen=True)
class AgentRuntimeLoopPolicy:
    """Fail-closed runtime loop bounds for AgentExecutor-compatible runs."""

    max_steps: int
    max_retries: int
    timeout_seconds: int | float
    stop_conditions: tuple[str, ...]
    allowed_tools: tuple[str, ...]
    allowed_callers: tuple[str, ...]
    side_effect_policy: str
    repair_strategy: str = "retry_within_bounds_then_fail_closed"
    fallback_semantics: str = "candidate_only_blocked_or_failed_never_generated_success"

    def __post_init__(self) -> None:
        if self.max_steps <= 0:
            raise ValueError("max_steps must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        object.__setattr__(self, "stop_conditions", _tuple(self.stop_conditions))
        object.__setattr__(self, "allowed_tools", _tuple(self.allowed_tools))
        object.__setattr__(self, "allowed_callers", _tuple(self.allowed_callers))
        if not self.stop_conditions:
            raise ValueError("stop_conditions are required")
        missing_stop_conditions = tuple(
            condition for condition in P8_REQUIRED_RUNTIME_STOP_CONDITIONS if condition not in self.stop_conditions
        )
        if missing_stop_conditions:
            raise ValueError(
                "missing required stop_conditions: " + ", ".join(missing_stop_conditions)
            )
        if not self.allowed_tools:
            raise ValueError("allowed_tools are required")
        if not self.allowed_callers:
            raise ValueError("allowed_callers are required")
        if not str(self.repair_strategy).strip():
            raise ValueError("repair_strategy is required")
        if not str(self.fallback_semantics).strip():
            raise ValueError("fallback_semantics is required")
        if self.side_effect_policy not in {
            "read_only",
            "candidate_write",
            "formal_write_handoff_only",
            "forbidden",
        }:
            raise ValueError(f"invalid side_effect_policy: {self.side_effect_policy}")


@dataclass(frozen=True)
class ToolDefinition:
    """Tool catalog contract for permitted agent calls without direct repository exposure."""

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
class CrossAgentPlanStep:
    """Contract-only step within a cross-agent plan; it does not execute agents."""

    step_id: str
    target_agent_id: str
    handoff_contract_id: str
    input_refs: tuple[str, ...] = field(default_factory=tuple)
    required_candidate_types: tuple[str, ...] = field(default_factory=tuple)
    output_candidate_types: tuple[str, ...] = field(default_factory=tuple)
    depends_on_step_ids: tuple[str, ...] = field(default_factory=tuple)
    policy_refs: tuple[str, ...] = field(default_factory=tuple)
    validation_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "step_id", _required_text(self.step_id, label="step_id"))
        object.__setattr__(self, "target_agent_id", _required_text(self.target_agent_id, label="target_agent_id"))
        object.__setattr__(
            self,
            "handoff_contract_id",
            _required_text(self.handoff_contract_id, label="handoff_contract_id"),
        )
        object.__setattr__(self, "input_refs", _tuple(self.input_refs))
        object.__setattr__(self, "required_candidate_types", _tuple(self.required_candidate_types))
        object.__setattr__(
            self,
            "output_candidate_types",
            _required_tuple(self.output_candidate_types, label="output_candidate_types"),
        )
        object.__setattr__(self, "depends_on_step_ids", _tuple(self.depends_on_step_ids))
        object.__setattr__(self, "policy_refs", _tuple(self.policy_refs))
        object.__setattr__(
            self,
            "validation_refs",
            _required_tuple(self.validation_refs, label="validation_refs"),
        )


@dataclass(frozen=True)
class CrossAgentHandoffRoute:
    """Contract-only route for candidate refs between agents, not runtime wiring."""

    route_id: str
    source_agent_id: str
    target_agent_id: str
    payload_schema_id: str
    side_effect_policy: str
    allowed_candidate_types: tuple[str, ...] = field(default_factory=tuple)
    required_trace_refs: tuple[str, ...] = field(default_factory=tuple)
    required_validation_refs: tuple[str, ...] = field(default_factory=tuple)
    user_confirmation_required_when: tuple[str, ...] = field(default_factory=tuple)
    forbidden_data: tuple[str, ...] = CROSS_AGENT_REQUIRED_FORBIDDEN_DATA

    def __post_init__(self) -> None:
        object.__setattr__(self, "route_id", _required_text(self.route_id, label="route_id"))
        object.__setattr__(self, "source_agent_id", _required_text(self.source_agent_id, label="source_agent_id"))
        object.__setattr__(self, "target_agent_id", _required_text(self.target_agent_id, label="target_agent_id"))
        object.__setattr__(
            self,
            "allowed_candidate_types",
            _required_tuple(self.allowed_candidate_types, label="allowed_candidate_types"),
        )
        object.__setattr__(self, "payload_schema_id", _required_text(self.payload_schema_id, label="payload_schema_id"))
        object.__setattr__(
            self,
            "required_trace_refs",
            _required_tuple(self.required_trace_refs, label="required_trace_refs"),
        )
        object.__setattr__(
            self,
            "required_validation_refs",
            _required_tuple(self.required_validation_refs, label="required_validation_refs"),
        )
        side_effect_policy = _required_text(self.side_effect_policy, label="side_effect_policy")
        if side_effect_policy not in CROSS_AGENT_ALLOWED_SIDE_EFFECT_POLICIES:
            raise ValueError("side_effect_policy is not allowed for cross-agent handoff")
        object.__setattr__(self, "side_effect_policy", side_effect_policy)
        trigger_types = _tuple(self.user_confirmation_required_when)
        unknown_triggers = tuple(
            trigger
            for trigger in trigger_types
            if trigger not in CROSS_AGENT_HITL_TRIGGER_TYPES and not trigger.endswith("_candidate")
        )
        if unknown_triggers:
            raise ValueError("unsupported HITL trigger for cross-agent handoff route")
        object.__setattr__(
            self,
            "user_confirmation_required_when",
            trigger_types,
        )
        object.__setattr__(self, "forbidden_data", _required_tuple(self.forbidden_data, label="forbidden_data"))


@dataclass(frozen=True)
class CrossAgentStateContract:
    """Contract-only state/checkpoint/replay policy for orchestration control state."""

    state_schema_id: str
    checkpoint_policy: str
    replay_policy: str
    resume_policy: str
    owner_scope_policy: str
    durable_state_refs: tuple[str, ...] = field(default_factory=tuple)
    ephemeral_state_refs: tuple[str, ...] = field(default_factory=tuple)
    forbidden_data: tuple[str, ...] = CROSS_AGENT_REQUIRED_FORBIDDEN_DATA

    def __post_init__(self) -> None:
        object.__setattr__(self, "state_schema_id", _required_text(self.state_schema_id, label="state_schema_id"))
        object.__setattr__(
            self,
            "checkpoint_policy",
            _required_text(self.checkpoint_policy, label="checkpoint_policy"),
        )
        object.__setattr__(self, "replay_policy", _required_text(self.replay_policy, label="replay_policy"))
        object.__setattr__(self, "resume_policy", _required_text(self.resume_policy, label="resume_policy"))
        object.__setattr__(
            self,
            "durable_state_refs",
            _required_tuple(self.durable_state_refs, label="durable_state_refs"),
        )
        object.__setattr__(self, "ephemeral_state_refs", _tuple(self.ephemeral_state_refs))
        object.__setattr__(
            self,
            "owner_scope_policy",
            _required_text(self.owner_scope_policy, label="owner_scope_policy"),
        )
        object.__setattr__(self, "forbidden_data", _required_tuple(self.forbidden_data, label="forbidden_data"))


@dataclass(frozen=True)
class CrossAgentTraceContract:
    """Contract-only trace/timeline policy for cross-agent candidate handoffs."""

    trace_schema_id: str
    required_trace_refs: tuple[str, ...] = field(default_factory=tuple)
    timeline_event_types: tuple[str, ...] = field(default_factory=tuple)
    plan_refs: tuple[str, ...] = field(default_factory=tuple)
    skill_refs: tuple[str, ...] = field(default_factory=tuple)
    tool_refs: tuple[str, ...] = field(default_factory=tuple)
    policy_refs: tuple[str, ...] = field(default_factory=tuple)
    handoff_refs: tuple[str, ...] = field(default_factory=tuple)
    validation_refs: tuple[str, ...] = field(default_factory=tuple)
    candidate_refs: tuple[str, ...] = field(default_factory=tuple)
    forbidden_data: tuple[str, ...] = CROSS_AGENT_REQUIRED_FORBIDDEN_DATA

    def __post_init__(self) -> None:
        object.__setattr__(self, "trace_schema_id", _required_text(self.trace_schema_id, label="trace_schema_id"))
        object.__setattr__(
            self,
            "required_trace_refs",
            _required_tuple(self.required_trace_refs, label="required_trace_refs"),
        )
        object.__setattr__(
            self,
            "timeline_event_types",
            _required_tuple(self.timeline_event_types, label="timeline_event_types"),
        )
        object.__setattr__(self, "plan_refs", _required_tuple(self.plan_refs, label="plan_refs"))
        object.__setattr__(self, "skill_refs", _required_tuple(self.skill_refs, label="skill_refs"))
        object.__setattr__(self, "tool_refs", _required_tuple(self.tool_refs, label="tool_refs"))
        object.__setattr__(self, "policy_refs", _required_tuple(self.policy_refs, label="policy_refs"))
        object.__setattr__(self, "handoff_refs", _required_tuple(self.handoff_refs, label="handoff_refs"))
        object.__setattr__(
            self,
            "validation_refs",
            _required_tuple(self.validation_refs, label="validation_refs"),
        )
        object.__setattr__(self, "candidate_refs", _required_tuple(self.candidate_refs, label="candidate_refs"))
        object.__setattr__(self, "forbidden_data", _required_tuple(self.forbidden_data, label="forbidden_data"))


@dataclass(frozen=True)
class CrossAgentPlan:
    """Contract-only orchestration plan; it is never executed by this catalog."""

    plan_id: str
    orchestrator_agent_id: str
    owner_id: str
    objective: str
    state_ref: str
    trace_ref: str
    handoff_policy: str
    participant_agent_ids: tuple[str, ...] = field(default_factory=tuple)
    steps: tuple[CrossAgentPlanStep, ...] = field(default_factory=tuple)
    max_steps: int = 1
    max_retries: int = 0
    timeout_seconds: int | float = 1
    stop_conditions: tuple[str, ...] = field(default_factory=tuple)
    handoff_routes: tuple[CrossAgentHandoffRoute, ...] = field(default_factory=tuple)
    state_contract: CrossAgentStateContract | None = None
    trace_contract: CrossAgentTraceContract | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_id", _required_text(self.plan_id, label="plan_id"))
        object.__setattr__(
            self,
            "orchestrator_agent_id",
            _required_text(self.orchestrator_agent_id, label="orchestrator_agent_id"),
        )
        object.__setattr__(self, "owner_id", _required_text(self.owner_id, label="owner_id"))
        object.__setattr__(self, "objective", _required_text(self.objective, label="objective"))
        object.__setattr__(
            self,
            "participant_agent_ids",
            _required_tuple(self.participant_agent_ids, label="participant_agent_ids"),
        )
        steps = tuple(self.steps)
        if not steps:
            raise ValueError("steps are required")
        if any(not isinstance(step, CrossAgentPlanStep) for step in steps):
            raise ValueError("steps must contain CrossAgentPlanStep")
        object.__setattr__(self, "steps", steps)
        if self.max_steps <= 0:
            raise ValueError("max_steps must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        object.__setattr__(self, "stop_conditions", _required_tuple(self.stop_conditions, label="stop_conditions"))
        object.__setattr__(self, "state_ref", _required_text(self.state_ref, label="state_ref"))
        object.__setattr__(self, "trace_ref", _required_text(self.trace_ref, label="trace_ref"))
        object.__setattr__(self, "handoff_policy", _required_text(self.handoff_policy, label="handoff_policy"))
        routes = tuple(self.handoff_routes)
        if any(not isinstance(route, CrossAgentHandoffRoute) for route in routes):
            raise ValueError("handoff_routes must contain CrossAgentHandoffRoute")
        object.__setattr__(self, "handoff_routes", routes)
        if self.state_contract is not None and not isinstance(self.state_contract, CrossAgentStateContract):
            raise ValueError("state_contract must be CrossAgentStateContract")
        if self.trace_contract is not None and not isinstance(self.trace_contract, CrossAgentTraceContract):
            raise ValueError("trace_contract must be CrossAgentTraceContract")
        object.__setattr__(self, "metadata", _safe_metadata(self.metadata))


@dataclass(frozen=True)
class AgentExecutionPlan:
    """Contract-only execution plan metadata for future AgentExecutor slices."""

    plan_id: str
    agent_id: str
    owner_id: str
    objective: str
    run_id: str = ""
    ai_task_id: str = ""
    actor_id: str = ""
    graph_name: str = ""
    graph_version: str = ""
    input_refs: tuple[str, ...] = field(default_factory=tuple)
    requested_outputs: tuple[str, ...] = field(default_factory=tuple)
    idempotency_key: str = ""
    runtime_loop_policy: AgentRuntimeLoopPolicy | None = None
    steps: tuple[str, ...] = field(default_factory=tuple)
    candidate_output_refs: tuple[str, ...] = field(default_factory=tuple)
    handoff_contract: HandoffContract | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_refs", _tuple(self.input_refs))
        object.__setattr__(self, "requested_outputs", _tuple(self.requested_outputs))
        object.__setattr__(self, "steps", _tuple(self.steps))
        object.__setattr__(self, "candidate_output_refs", _tuple(self.candidate_output_refs))
        object.__setattr__(self, "metadata", _metadata(self.metadata))


@dataclass(frozen=True)
class AgentExecutionTrace:
    """Contract-only trace record for candidate, validation, and handoff references."""

    trace_id: str
    run_id: str
    agent_id: str
    agent_version: str = ""
    ai_task_id: str = ""
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
    low_confidence_flags: tuple[str, ...] = field(default_factory=tuple)
    failure_reason: str = ""
    fallback_reason: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "events", _tuple(self.events))
        object.__setattr__(self, "candidate_refs", _tuple(self.candidate_refs))
        object.__setattr__(self, "handoff_refs", _tuple(self.handoff_refs))
        object.__setattr__(self, "metadata", _safe_metadata(self.metadata))
        object.__setattr__(self, "input_refs", _tuple(self.input_refs))
        object.__setattr__(self, "plan_refs", _tuple(self.plan_refs))
        object.__setattr__(self, "skill_refs", _tuple(self.skill_refs))
        object.__setattr__(self, "tool_refs", _tuple(self.tool_refs))
        object.__setattr__(self, "policy_refs", _tuple(self.policy_refs))
        object.__setattr__(self, "provider_refs", _tuple(self.provider_refs))
        object.__setattr__(self, "validation_refs", _tuple(self.validation_refs))
        object.__setattr__(self, "output_refs", _tuple(self.output_refs))
        object.__setattr__(self, "low_confidence_flags", _tuple(self.low_confidence_flags))


@dataclass(frozen=True)
class AgentExecutionResult:
    """Contract-only execution result that exposes candidate refs before handoff."""

    run_id: str
    status: str
    candidate_refs: tuple[str, ...]
    trace: AgentExecutionTrace
    output_refs: tuple[str, ...] = field(default_factory=tuple)
    interrupt_refs: tuple[str, ...] = field(default_factory=tuple)
    candidate_payloads: tuple[Any, ...] = field(default_factory=tuple)
    handoff_refs: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_refs", _tuple(self.candidate_refs))
        object.__setattr__(self, "output_refs", _tuple(self.output_refs))
        object.__setattr__(self, "interrupt_refs", _tuple(self.interrupt_refs))
        object.__setattr__(self, "candidate_payloads", tuple(self.candidate_payloads))
        object.__setattr__(self, "handoff_refs", _tuple(self.handoff_refs))
        object.__setattr__(self, "metadata", _metadata(self.metadata))


@dataclass(frozen=True)
class AgentExecutionStatus:
    """Contract-only status snapshot for non-formal agent execution progress."""

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
    """Contract-only timeline wrapper for trace events, not a runtime store."""

    run_id: str
    events: tuple[AgentExecutionTrace, ...] = field(default_factory=tuple)
    cursor: str | None = None
    has_more: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "events", tuple(self.events))


__all__ = [
    "AgentDefinition",
    "CROSS_AGENT_ALLOWED_RESUME_ACTIONS",
    "CROSS_AGENT_ALLOWED_SIDE_EFFECT_POLICIES",
    "CROSS_AGENT_HITL_TRIGGER_TYPES",
    "CROSS_AGENT_REQUIRED_FORBIDDEN_DATA",
    "CrossAgentHandoffRoute",
    "CrossAgentPlan",
    "CrossAgentPlanStep",
    "CrossAgentStateContract",
    "CrossAgentTraceContract",
    "AgentExecutionPlan",
    "AgentExecutionResult",
    "AgentExecutionStatus",
    "AgentExecutionTimeline",
    "AgentExecutionTrace",
    "AgentHandoffEnvelope",
    "AgentRuntimeLoopPolicy",
    "EvalContract",
    "HandoffContract",
    "P8_REQUIRED_RUNTIME_STOP_CONDITIONS",
    "SkillDefinition",
    "ToolDefinition",
    "TraceContract",
]
