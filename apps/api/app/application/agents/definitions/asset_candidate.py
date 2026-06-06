"""Contract-only Phase 11 Asset Candidate Agent catalog definitions."""

from __future__ import annotations

from dataclasses import replace

from app.application.agents.contracts import AgentDefinition, EvalContract, SkillDefinition, ToolDefinition, TraceContract
from app.application.agents.definitions.common import (
    build_handoff_contract,
    build_skill_definition,
    build_tool_definition,
)
from app.application.agents.definitions.versions import (
    AGENT_DEFINITION_SCHEMA_VERSION,
    ASSET_CANDIDATE_AGENT_VERSION,
    L5_CONTRACT_CATALOG_REVISION,
    L5_CONTRACT_LIFECYCLE_STATUS,
    L5_CONTRACT_MATURITY_LEVEL,
)


ASSET_CANDIDATE_AGENT_ID = "asset_candidate_agent"
ASSET_CANDIDATE_EVAL_SUITE_ID = "phase12.asset_candidate_agent.eval_deferred.v1"
L5_PRODUCT_SLICE_TEST_REF = (
    "tests/application/agents/test_phase11_three_agent_product_slice.py::"
    "test_happy_path_creates_candidate_only_three_business_agent_workflow"
)

ASSET_CANDIDATE_SKILL_IDS = (
    "aca_feedback_ref_review_skill",
    "aca_asset_update_candidate_planning_skill",
    "aca_asset_conflict_screening_skill",
    "aca_asset_handoff_preparation_skill",
)

ASSET_CANDIDATE_TOOL_IDS = (
    "aca_feedback_candidate_ref_reader",
    "aca_asset_policy_ref_checker",
    "aca_asset_conflict_ref_checker",
    "aca_asset_update_candidate_ref_builder",
)


def build_asset_candidate_agent_definition() -> AgentDefinition:
    """Build the L5 contract-only Asset Candidate Agent definition."""

    return AgentDefinition(
        agent_id=ASSET_CANDIDATE_AGENT_ID,
        agent_name="Asset Candidate Agent",
        domain="asset_candidate_orchestration",
        version=ASSET_CANDIDATE_AGENT_VERSION,
        maturity_level=L5_CONTRACT_MATURITY_LEVEL,
        lifecycle_status=L5_CONTRACT_LIFECYCLE_STATUS,
        mission="Prepare reviewable asset update candidate refs from feedback refs only.",
        user_goal="Review an asset update candidate before any durable asset change.",
        autonomous_goal="Detect asset conflicts and prepare candidate refs without formal writes.",
        non_goals=(
            "no L5 release claim",
            "no runtime execution",
            "no direct DB or repository write",
            "no prompt rendering",
            "no provider or LLM call",
            "no formal asset write",
            "no Phase 12 release gate implementation",
        ),
        input_contract="agent.asset_candidate.input_refs.v1",
        output_contract="agent.asset_candidate.output_candidate_refs.v1",
        candidate_outputs=("asset_update_candidate",),
        formal_write_boundary=(
            "direct formal writes disallowed; asset_update_candidate remains blocked until "
            "explicit user confirmation and a separately authorized handoff"
        ),
        skills=ASSET_CANDIDATE_SKILL_IDS,
        tools=ASSET_CANDIDATE_TOOL_IDS,
        memory_state="refs_only_no_durable_state",
        planning_strategy="deterministic_candidate_ref_planning_only",
        guardrails=(
            "candidate_only",
            "user_confirmation_required",
            "formal_write_blocked",
            "no_repository_or_db_tool_exposure",
        ),
        hitl_triggers=("asset_conflict", "formal_write_requested", "low_confidence"),
        failure_semantics="fail_closed_without_asset_candidate_or_formal_write",
        trace_contract=_build_asset_candidate_trace_contract(),
        eval_contract=EvalContract(
            contract_id="eval.asset_candidate_agent.v1",
            eval_suite_ids=(ASSET_CANDIDATE_EVAL_SUITE_ID,),
            metrics=("candidate_ref_shape", "asset_confirmation_boundary", "forbidden_data_omission"),
            failure_policy="fail_closed",
            dataset_refs=("phase12.multi_agent_eval_dataset.deferred",),
            grader_refs=("phase12.multi_agent_grader.deferred",),
            regression_cases=("phase11.minimal_three_agent_candidate_slice",),
            minimum_pass_criteria="candidate refs validate without formal asset write",
            ci_gate="deferred_phase_12",
            failure_triage_policy="record_gap_without_l5_release_claim",
        ),
        handoff_contract=build_handoff_contract(
            "handoff.asset_candidate_agent.v1",
            candidate_ref_types=("asset_update_candidate",),
            payload_schema_id="agent.asset_candidate.handoff_payload.v1",
            validation_refs=("asset_conflict_ref_checker", "asset_policy_ref_checker"),
            quality_gate="asset_update_candidate_requires_user_confirmation",
            side_effect_key="asset_update_candidate_ref_handoff",
            idempotency_key="asset_update_candidate_ref",
            formal_write_preconditions=(
                "candidate_validated",
                "asset_update_candidate_user_confirmed",
                "separately_authorized_application_handoff",
            ),
            allowed_formal_targets=(),
            user_confirmation_required=True,
        ),
        versioning_policy="semver_definition_version_with_l5_contract_catalog_revision",
        schema_version=AGENT_DEFINITION_SCHEMA_VERSION,
        catalog_revision=L5_CONTRACT_CATALOG_REVISION,
    )


def build_asset_candidate_skill_definitions() -> tuple[SkillDefinition, ...]:
    """Build Asset Candidate skill contracts without runtime execution."""

    return tuple(
        replace(skill, test_refs=(L5_PRODUCT_SLICE_TEST_REF,))
        for skill in (
            build_skill_definition(
                "aca_feedback_ref_review_skill",
                "AssetCandidateFeedbackRefReviewSkill",
                owner_agent_id=ASSET_CANDIDATE_AGENT_ID,
                purpose="Review feedback_candidate refs before asset candidate planning.",
                tool_refs=("aca_feedback_candidate_ref_reader",),
                deterministic_policy_refs=("feedback_candidate_refs_only_policy",),
                eval_refs=(ASSET_CANDIDATE_EVAL_SUITE_ID, "phase12_multi_agent_eval_deferred"),
                output_summary="feedback candidate refs are available for asset candidate planning",
            ),
            build_skill_definition(
                "aca_asset_update_candidate_planning_skill",
                "AssetUpdateCandidatePlanningSkill",
                owner_agent_id=ASSET_CANDIDATE_AGENT_ID,
                purpose="Plan asset_update_candidate refs without preparing a formal asset write.",
                tool_refs=("aca_asset_update_candidate_ref_builder",),
                deterministic_policy_refs=("asset_update_candidate_only_policy",),
                eval_refs=(ASSET_CANDIDATE_EVAL_SUITE_ID, "phase12_multi_agent_eval_deferred"),
                output_summary="asset update candidate refs are prepared for review",
            ),
            build_skill_definition(
                "aca_asset_conflict_screening_skill",
                "AssetConflictScreeningSkill",
                owner_agent_id=ASSET_CANDIDATE_AGENT_ID,
                purpose="Fail closed when asset conflict refs are present.",
                tool_refs=("aca_asset_conflict_ref_checker",),
                deterministic_policy_refs=("asset_conflict_hitl_policy",),
                eval_refs=(ASSET_CANDIDATE_EVAL_SUITE_ID, "phase12_multi_agent_eval_deferred"),
                output_summary="asset conflict refs are surfaced before candidate handoff",
            ),
            build_skill_definition(
                "aca_asset_handoff_preparation_skill",
                "AssetHandoffPreparationSkill",
                owner_agent_id=ASSET_CANDIDATE_AGENT_ID,
                purpose="Prepare refs-only handoff metadata for downstream training plan candidates.",
                tool_refs=("aca_asset_policy_ref_checker",),
                deterministic_policy_refs=("candidate_handoff_refs_only_policy",),
                eval_refs=(ASSET_CANDIDATE_EVAL_SUITE_ID, "phase12_multi_agent_eval_deferred"),
                output_summary="asset candidate handoff refs are ready without formal output",
            ),
        )
    )


def build_asset_candidate_tool_definitions() -> tuple[ToolDefinition, ...]:
    """Build Asset Candidate tool contracts for project-level registration."""

    return (
        build_tool_definition(
            "aca_feedback_candidate_ref_reader",
            "read_feedback_candidate_refs",
            allowed_callers=(ASSET_CANDIDATE_AGENT_ID,),
        ),
        build_tool_definition(
            "aca_asset_policy_ref_checker",
            "check_asset_policy_refs",
            allowed_callers=(ASSET_CANDIDATE_AGENT_ID,),
        ),
        build_tool_definition(
            "aca_asset_conflict_ref_checker",
            "check_asset_conflict_refs",
            allowed_callers=(ASSET_CANDIDATE_AGENT_ID,),
        ),
        build_tool_definition(
            "aca_asset_update_candidate_ref_builder",
            "build_asset_update_candidate_refs",
            allowed_callers=(ASSET_CANDIDATE_AGENT_ID,),
            side_effect_policy="candidate_write",
        ),
    )


def _build_asset_candidate_trace_contract() -> TraceContract:
    return TraceContract(
        contract_id="trace.asset_candidate_agent.v1",
        input_refs=("asset_candidate_agent.input_refs",),
        plan_refs=("asset_candidate_agent.candidate_plan_ref",),
        skill_refs=("asset_candidate_agent.skill_refs",),
        tool_refs=("asset_candidate_agent.tool_refs",),
        policy_refs=("asset_candidate_agent.candidate_only_policy", "asset_candidate_agent.confirmation_policy"),
        provider_refs=(),
        candidate_refs=("asset_update_candidate",),
        validation_refs=("asset_candidate_agent.validation_refs",),
        handoff_refs=("asset_candidate_agent.handoff_refs",),
        output_refs=("asset_candidate_agent.candidate_output_refs",),
        events=(
            "asset_candidate_agent.refs_checked",
            "asset_candidate_agent.conflict_screened",
            "asset_candidate_agent.candidate_ref_prepared",
            "asset_candidate_agent.handoff_ref_prepared",
        ),
    )


__all__ = [
    "ASSET_CANDIDATE_AGENT_ID",
    "ASSET_CANDIDATE_SKILL_IDS",
    "ASSET_CANDIDATE_TOOL_IDS",
    "build_asset_candidate_agent_definition",
    "build_asset_candidate_skill_definitions",
    "build_asset_candidate_tool_definitions",
]
