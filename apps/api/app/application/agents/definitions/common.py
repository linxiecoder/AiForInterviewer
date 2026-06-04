"""Shared contract-only builders for Agent Platform C1 catalog definitions."""

from __future__ import annotations

from app.application.agents.contracts import EvalContract, HandoffContract, SkillDefinition, ToolDefinition, TraceContract
from app.application.agents.definitions.versions import SKILL_DEFINITION_SCHEMA_VERSION, TOOL_DEFINITION_SCHEMA_VERSION
from app.application.agents.registry import REQUIRED_TOOL_FORBIDDEN_DATA


FORBIDDEN_DATA = tuple(sorted(REQUIRED_TOOL_FORBIDDEN_DATA))
C1_ARCHITECTURE_TEST_REF = (
    "tests/architecture/test_agent_platform_c1_boundary.py::"
    "test_phase4_c1_catalog_uses_stable_versions_and_enriched_skill_contracts"
)


def build_trace_contract(contract_id: str, *, agent_prefix: str, candidate_refs: tuple[str, ...]) -> TraceContract:
    """Build trace metadata for candidate-only agent contracts."""

    return TraceContract(
        contract_id=contract_id,
        input_refs=(f"{agent_prefix}.input_contract",),
        plan_refs=(f"{agent_prefix}.planned_workflow",),
        skill_refs=(f"{agent_prefix}.skill_refs",),
        tool_refs=(f"{agent_prefix}.tool_refs",),
        policy_refs=(f"{agent_prefix}.domain_policy_refs",),
        provider_refs=(f"{agent_prefix}.provider_ref.contract_only",),
        candidate_refs=candidate_refs,
        validation_refs=(f"{agent_prefix}.validation_refs",),
        handoff_refs=(f"{agent_prefix}.handoff_contract",),
        output_refs=(f"{agent_prefix}.candidate_output_refs",),
        events=(
            f"{agent_prefix}.plan.created",
            f"{agent_prefix}.skill.checked",
            f"{agent_prefix}.tool.contract_checked",
            f"{agent_prefix}.candidate.validated",
            f"{agent_prefix}.handoff.prepared",
        ),
        forbidden_data=FORBIDDEN_DATA,
    )


def build_eval_contract(contract_id: str, *, suite_id: str) -> EvalContract:
    """Build deferred evaluation metadata for C1 architecture gates."""

    return EvalContract(
        contract_id=contract_id,
        eval_suite_ids=(suite_id,),
        metrics=("candidate_contract_shape", "forbidden_data_omission"),
        failure_policy="fail_closed",
        dataset_refs=(f"{suite_id}.dataset_refs.contract_only",),
        grader_refs=(f"{suite_id}.grader_refs.contract_only",),
        regression_cases=(f"{suite_id}.regression_cases.contract_only",),
        minimum_pass_criteria="contract references bind without runtime execution",
        ci_gate="deferred_phase_9",
        failure_triage_policy="record_gap_without_runtime_execution",
    )


def build_handoff_contract(
    contract_id: str,
    *,
    candidate_ref_types: tuple[str, ...],
    payload_schema_id: str,
    validation_refs: tuple[str, ...],
    quality_gate: str,
    side_effect_key: str,
    idempotency_key: str,
    formal_write_preconditions: tuple[str, ...],
    allowed_formal_targets: tuple[str, ...],
    user_confirmation_required: bool,
) -> HandoffContract:
    """Build handoff metadata that separates candidate refs from formal writes."""

    return HandoffContract(
        contract_id=contract_id,
        candidate_ref_types=candidate_ref_types,
        formal_write_policy="handoff_required",
        allowed_formal_targets=allowed_formal_targets,
        confirmation_required=user_confirmation_required,
        payload_schema_id=payload_schema_id,
        validation_refs=validation_refs,
        quality_gate=quality_gate,
        side_effect_key=side_effect_key,
        idempotency_key=idempotency_key,
        formal_write_preconditions=formal_write_preconditions,
        rollback_policy="discard_candidate_before_formal_write",
        user_confirmation_required=user_confirmation_required,
    )


def build_skill_definition(
    skill_id: str,
    skill_name: str,
    *,
    owner_agent_id: str,
    purpose: str,
    tool_refs: tuple[str, ...],
    output_summary: str,
    deterministic_policy_refs: tuple[str, ...] = (),
    llm_refs: tuple[str, ...] = (),
    eval_refs: tuple[str, ...] = (),
) -> SkillDefinition:
    """Build an enriched contract-only skill definition for the C1 catalog."""

    contract_refs = deterministic_policy_refs + llm_refs
    preconditions = (
        "owner agent contract is registered before this skill is resolved",
        f"registered tool refs available: {', '.join(tool_refs)}",
        f"contract refs available: {', '.join(contract_refs) if contract_refs else 'none'}",
    )
    return SkillDefinition(
        skill_id=skill_id,
        skill_name=skill_name,
        owner_agent_ids=(owner_agent_id,),
        input_schema_id=f"agent.{owner_agent_id}.{skill_id}.input.{SKILL_DEFINITION_SCHEMA_VERSION}",
        output_schema_id=f"agent.{owner_agent_id}.{skill_id}.output.{SKILL_DEFINITION_SCHEMA_VERSION}",
        implementation_type="contract_only",
        deterministic_policy_refs=deterministic_policy_refs,
        llm_refs=llm_refs,
        tool_refs=tool_refs,
        timeout_policy="no_runtime_execution",
        retry_policy="not_applicable",
        failure_semantics="fail_closed",
        trace_events=(f"skill.{skill_id}.contract_checked",),
        eval_refs=eval_refs,
        purpose=purpose,
        implementation_ref=f"contract_only:{owner_agent_id}:{skill_id}",
        preconditions=preconditions,
        postconditions=(
            output_summary,
            "candidate metadata only; no formal business object write",
        ),
        fallback_policy="fail_closed_without_candidate_output_or_formal_write",
        lifecycle_status="contract_only",
        definition_version="1.0.0",
        schema_version=SKILL_DEFINITION_SCHEMA_VERSION,
        test_refs=(C1_ARCHITECTURE_TEST_REF,),
    )


def build_tool_definition(
    tool_id: str,
    tool_name: str,
    *,
    allowed_callers: tuple[str, ...],
    side_effect_policy: str = "read_only",
) -> ToolDefinition:
    """Build a contract-only tool definition for project-level registry use."""

    return ToolDefinition(
        tool_id=tool_id,
        tool_name=tool_name,
        input_schema_id=f"agent.tool.{tool_id}.input.{TOOL_DEFINITION_SCHEMA_VERSION}",
        output_schema_id=f"agent.tool.{tool_id}.output.{TOOL_DEFINITION_SCHEMA_VERSION}",
        permission_scope="owner_scoped_contract",
        owner_scope="application_contract_only",
        side_effect_policy=side_effect_policy,
        timeout_seconds=5,
        retry_policy="none",
        allowed_callers=allowed_callers,
        forbidden_data=FORBIDDEN_DATA,
        trace_events=(f"tool.{tool_id}.contract_checked",),
    )


__all__ = [
    "C1_ARCHITECTURE_TEST_REF",
    "FORBIDDEN_DATA",
    "build_eval_contract",
    "build_handoff_contract",
    "build_skill_definition",
    "build_tool_definition",
    "build_trace_contract",
]
