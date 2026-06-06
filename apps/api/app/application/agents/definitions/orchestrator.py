"""Contract-only Phase 11 Supervisor / Orchestrator catalog definitions."""

from __future__ import annotations

from dataclasses import replace

from app.application.agents.contracts import (
    AgentDefinition,
    CrossAgentHandoffRoute,
    CrossAgentPlan,
    CrossAgentPlanStep,
    CrossAgentStateContract,
    CrossAgentTraceContract,
    EvalContract,
    SkillDefinition,
    ToolDefinition,
)
from app.application.agents.definitions.common import FORBIDDEN_DATA, build_skill_definition, build_tool_definition
from app.application.agents.definitions.versions import (
    AGENT_DEFINITION_SCHEMA_VERSION,
    INTERVIEW_ORCHESTRATOR_AGENT_VERSION,
    L5_CONTRACT_CATALOG_REVISION,
    L5_CONTRACT_LIFECYCLE_STATUS,
    L5_CONTRACT_MATURITY_LEVEL,
)


INTERVIEW_ORCHESTRATOR_AGENT_ID = "interview_orchestrator_agent"
ORCHESTRATOR_EVAL_SUITE_ID = "eval.interview_orchestrator_agent.contract_deferred.v1"
L5_ARCHITECTURE_TEST_REF = (
    "tests/architecture/test_agent_platform_l5_orchestrator_contract.py::"
    "test_phase11_l5_catalog_registers_orchestrator_without_replacing_c1"
)

ORCHESTRATOR_SKILL_IDS = (
    "orch_goal_decomposition_skill",
    "orch_agent_route_planning_skill",
    "orch_cross_agent_handoff_validation_skill",
    "orch_state_checkpoint_planning_skill",
    "orch_trace_timeline_planning_skill",
    "orch_hitl_trigger_planning_skill",
)
ORCHESTRATOR_TOOL_IDS = (
    "orch_read_agent_catalog_contract",
    "orch_validate_cross_agent_plan_contract",
    "orch_validate_cross_agent_handoff_contract",
    "orch_validate_cross_agent_state_contract",
    "orch_validate_cross_agent_trace_contract",
    "orch_validate_hitl_trigger_contract",
)
ORCHESTRATOR_CANDIDATE_OUTPUTS = (
    "cross_agent_plan_candidate",
    "cross_agent_handoff_candidate",
    "cross_agent_state_candidate",
    "cross_agent_trace_candidate",
)
ORCHESTRATOR_HITL_TRIGGERS = (
    "asset_conflict",
    "formal_write_requested",
    "low_confidence",
    "ambiguous_ownership",
    "validation_failed_partial_result",
)


def build_interview_orchestrator_agent_definition() -> AgentDefinition:
    """Build the Option D default-off local Orchestrator Agent definition."""

    plan_contract, handoff_route, state_contract, trace_contract = _build_cross_agent_contracts()
    return AgentDefinition(
        agent_id=INTERVIEW_ORCHESTRATOR_AGENT_ID,
        agent_name="Interview Orchestrator Agent",
        domain="interview_orchestration",
        version=INTERVIEW_ORCHESTRATOR_AGENT_VERSION,
        maturity_level=L5_CONTRACT_MATURITY_LEVEL,
        lifecycle_status=L5_CONTRACT_LIFECYCLE_STATUS,
        mission="Plan and execute default-off local cross-agent candidate handoffs.",
        user_goal="Prepare reviewable orchestration plan, handoff, state and trace candidates.",
        autonomous_goal="Validate refs-only local multi-agent orchestration without formal writes.",
        non_goals=(
            "no L5 release claim",
            "no default-on runtime execution",
            "no production product workflow execution",
            "no direct DB or repository write",
            "no prompt/provider/API/DB/domain behavior change",
            "no real-provider quality certification",
            "no Phase 12 release gate implementation",
        ),
        input_contract=plan_contract,
        output_contract="agent.interview_orchestrator.output_candidates.v1",
        candidate_outputs=ORCHESTRATOR_CANDIDATE_OUTPUTS,
        formal_write_boundary=(
            "direct formal writes disallowed; Application Service -> Domain Policy -> "
            "Handoff remains the formal write boundary"
        ),
        skills=ORCHESTRATOR_SKILL_IDS,
        tools=ORCHESTRATOR_TOOL_IDS,
        memory_state="contract_refs_only_no_runtime_state",
        planning_strategy="contract_first_cross_agent_plan_only",
        guardrails=(
            "candidate_only",
            "no_runtime_wiring",
            "no_product_workflow_execution",
            "no_repository_or_db_tool_exposure",
        ),
        hitl_triggers=ORCHESTRATOR_HITL_TRIGGERS,
        failure_semantics="fail_closed_without_runtime_execution_or_formal_write",
        trace_contract=trace_contract,
        eval_contract=EvalContract(
            contract_id="eval.interview_orchestrator_agent.v1",
            eval_suite_ids=(ORCHESTRATOR_EVAL_SUITE_ID,),
            metrics=("contract_shape", "no_runtime_wiring", "forbidden_data_omission"),
            failure_policy="fail_closed",
            dataset_refs=("phase12.multi_agent_eval_dataset.deferred",),
            grader_refs=("phase12.multi_agent_grader.deferred",),
            regression_cases=("phase11.contract_architecture_gate",),
            minimum_pass_criteria="contract catalog validates without runtime execution",
            ci_gate="deferred_remote_ci_gap",
            failure_triage_policy="record_gap_without_l5_release_claim",
        ),
        handoff_contract=handoff_route,
        versioning_policy="semver_definition_version_with_l5_contract_catalog_revision",
        task_types=(),
        schema_version=AGENT_DEFINITION_SCHEMA_VERSION,
        catalog_revision=L5_CONTRACT_CATALOG_REVISION,
    )


def build_interview_orchestrator_skill_definitions() -> tuple[SkillDefinition, ...]:
    """Build contract-only skill definitions owned by the Orchestrator."""

    return (
        _build_orchestrator_skill(
            "orch_goal_decomposition_skill",
            "OrchestratorGoalDecompositionSkill",
            purpose="Describe the user objective as refs-only cross-agent plan candidates.",
            tool_refs=("orch_read_agent_catalog_contract", "orch_validate_cross_agent_plan_contract"),
            policy_refs=("candidate_only_goal_decomposition_policy",),
        ),
        _build_orchestrator_skill(
            "orch_agent_route_planning_skill",
            "OrchestratorAgentRoutePlanningSkill",
            purpose="Select candidate-producing agent routes from registered contract metadata only.",
            tool_refs=("orch_read_agent_catalog_contract", "orch_validate_cross_agent_plan_contract"),
            policy_refs=("registered_agent_route_policy",),
        ),
        _build_orchestrator_skill(
            "orch_cross_agent_handoff_validation_skill",
            "OrchestratorCrossAgentHandoffValidationSkill",
            purpose="Validate cross-agent handoff route refs before any future runtime handoff.",
            tool_refs=("orch_validate_cross_agent_handoff_contract",),
            policy_refs=("candidate_handoff_refs_only_policy",),
        ),
        _build_orchestrator_skill(
            "orch_state_checkpoint_planning_skill",
            "OrchestratorStateCheckpointPlanningSkill",
            purpose="Plan orchestration control state, checkpoint and replay contracts without persistence.",
            tool_refs=("orch_validate_cross_agent_state_contract",),
            policy_refs=("state_refs_only_policy", "read_only_replay_policy"),
        ),
        _build_orchestrator_skill(
            "orch_trace_timeline_planning_skill",
            "OrchestratorTraceTimelinePlanningSkill",
            purpose="Plan trace and timeline refs required for future cross-agent auditability.",
            tool_refs=("orch_validate_cross_agent_trace_contract",),
            policy_refs=("trace_refs_only_policy",),
        ),
        _build_orchestrator_skill(
            "orch_hitl_trigger_planning_skill",
            "OrchestratorHitlTriggerPlanningSkill",
            purpose="Plan HITL trigger refs for asset conflict, formal write and validation partial results.",
            tool_refs=("orch_validate_hitl_trigger_contract",),
            policy_refs=("hitl_required_policy",),
        ),
    )


def build_interview_orchestrator_tool_definitions() -> tuple[ToolDefinition, ...]:
    """Build contract-only tool definitions for Orchestrator validation."""

    return (
        _build_orchestrator_tool("orch_read_agent_catalog_contract", "read_agent_catalog_contract"),
        _build_orchestrator_tool("orch_validate_cross_agent_plan_contract", "validate_cross_agent_plan_contract"),
        _build_orchestrator_tool(
            "orch_validate_cross_agent_handoff_contract",
            "validate_cross_agent_handoff_contract",
        ),
        _build_orchestrator_tool("orch_validate_cross_agent_state_contract", "validate_cross_agent_state_contract"),
        _build_orchestrator_tool("orch_validate_cross_agent_trace_contract", "validate_cross_agent_trace_contract"),
        _build_orchestrator_tool("orch_validate_hitl_trigger_contract", "validate_hitl_trigger_contract"),
    )


def _build_cross_agent_contracts() -> tuple[
    CrossAgentPlan,
    CrossAgentHandoffRoute,
    CrossAgentStateContract,
    CrossAgentTraceContract,
]:
    handoff_route = CrossAgentHandoffRoute(
        route_id="route.orch.question_to_feedback.contract.v1",
        source_agent_id="polish_question_agent",
        target_agent_id="polish_feedback_agent",
        allowed_candidate_types=("question_candidate",),
        payload_schema_id="agent.orch.question_feedback.handoff_payload.v1",
        required_trace_refs=("trace.polish_question_agent.v1", "trace.interview_orchestrator_agent.v1"),
        required_validation_refs=("question_grounding_validator", "follow_up_coverage_evaluator"),
        side_effect_policy="candidate_write",
        user_confirmation_required_when=("asset_update_candidate", "formal_write_requested"),
    )
    state_contract = CrossAgentStateContract(
        state_schema_id="state.interview_orchestrator.contract.v1",
        checkpoint_policy="checkpoint_refs_only_no_payload",
        replay_policy="read_only_formal_write_blocked",
        resume_policy="checkpoint_ref_base_version_idempotency_required",
        durable_state_refs=("orchestrator_plan_state_ref", "orchestrator_checkpoint_ref"),
        ephemeral_state_refs=("orchestrator_scratch_ref",),
        owner_scope_policy="same_owner_only",
    )
    trace_contract = CrossAgentTraceContract(
        trace_schema_id="trace.interview_orchestrator.timeline.v1",
        required_trace_refs=("trace.plan.created", "trace.handoff.validated"),
        timeline_event_types=("plan_created", "step_validated", "handoff_validated", "hitl_required"),
        plan_refs=("cross_agent_plan_ref",),
        skill_refs=ORCHESTRATOR_SKILL_IDS,
        tool_refs=ORCHESTRATOR_TOOL_IDS,
        policy_refs=("candidate_only_policy", "state_refs_only_policy", "hitl_required_policy"),
        handoff_refs=(handoff_route.route_id,),
        validation_refs=("cross_agent_plan_validation", "cross_agent_handoff_validation"),
        candidate_refs=ORCHESTRATOR_CANDIDATE_OUTPUTS,
    )
    plan_step = CrossAgentPlanStep(
        step_id="step.orch.question_candidate_to_feedback_candidate.v1",
        target_agent_id="polish_feedback_agent",
        input_refs=("question_candidate_ref",),
        required_candidate_types=("question_candidate",),
        output_candidate_types=("feedback_candidate", "asset_update_candidate"),
        depends_on_step_ids=("step.orch.question_candidate.v1",),
        handoff_contract_id=handoff_route.route_id,
        policy_refs=("candidate_only_policy",),
        validation_refs=("cross_agent_handoff_validation",),
    )
    plan_contract = CrossAgentPlan(
        plan_id="plan.interview_orchestrator.contract.v1",
        orchestrator_agent_id=INTERVIEW_ORCHESTRATOR_AGENT_ID,
        owner_id="owner_ref",
        objective="contract-only cross-agent orchestration plan",
        participant_agent_ids=("polish_question_agent", "polish_feedback_agent"),
        steps=(plan_step,),
        max_steps=4,
        max_retries=1,
        timeout_seconds=30,
        stop_conditions=(
            "max_steps_exceeded",
            "timeout",
            "validation_failed",
            "handoff_validation_failed",
            "hitl_required",
            "formal_write_requested",
        ),
        state_ref="orchestrator_plan_state_ref",
        trace_ref="trace.interview_orchestrator.timeline.v1",
        handoff_policy="candidate_only_handoff_default_off_local_runtime",
        handoff_routes=(handoff_route,),
        state_contract=state_contract,
        trace_contract=trace_contract,
    )
    return plan_contract, handoff_route, state_contract, trace_contract


def _build_orchestrator_skill(
    skill_id: str,
    skill_name: str,
    *,
    purpose: str,
    tool_refs: tuple[str, ...],
    policy_refs: tuple[str, ...],
) -> SkillDefinition:
    skill = build_skill_definition(
        skill_id,
        skill_name,
        owner_agent_id=INTERVIEW_ORCHESTRATOR_AGENT_ID,
        purpose=purpose,
        tool_refs=tool_refs,
        deterministic_policy_refs=policy_refs,
        eval_refs=(ORCHESTRATOR_EVAL_SUITE_ID, "phase12_multi_agent_eval_deferred"),
        output_summary="orchestration refs are validated for default-off local runtime execution",
    )
    return replace(skill, test_refs=(L5_ARCHITECTURE_TEST_REF,))


def _build_orchestrator_tool(tool_id: str, tool_name: str, *, side_effect_policy: str = "read_only") -> ToolDefinition:
    tool = build_tool_definition(
        tool_id,
        tool_name,
        allowed_callers=(INTERVIEW_ORCHESTRATOR_AGENT_ID,),
        side_effect_policy=side_effect_policy,
    )
    return replace(
        tool,
        permission_scope="agent_catalog_contract_read" if tool_id.endswith("catalog_contract") else "contract_validation",
        owner_scope="orchestrator_contract_only",
        trace_events=(f"tool.{tool_id}.contract_validated",),
        forbidden_data=FORBIDDEN_DATA,
    )


__all__ = [
    "INTERVIEW_ORCHESTRATOR_AGENT_ID",
    "ORCHESTRATOR_CANDIDATE_OUTPUTS",
    "ORCHESTRATOR_SKILL_IDS",
    "ORCHESTRATOR_TOOL_IDS",
    "build_interview_orchestrator_agent_definition",
    "build_interview_orchestrator_skill_definitions",
    "build_interview_orchestrator_tool_definitions",
]
