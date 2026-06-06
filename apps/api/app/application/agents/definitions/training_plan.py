"""Contract-only Phase 11 Training Plan Agent catalog definitions."""

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
    L5_CONTRACT_CATALOG_REVISION,
    L5_CONTRACT_LIFECYCLE_STATUS,
    L5_CONTRACT_MATURITY_LEVEL,
    TRAINING_PLAN_AGENT_VERSION,
)


TRAINING_PLAN_AGENT_ID = "training_plan_agent"
TRAINING_PLAN_EVAL_SUITE_ID = "phase12.training_plan_agent.eval_deferred.v1"
L5_PRODUCT_SLICE_TEST_REF = (
    "tests/application/agents/test_phase11_three_agent_product_slice.py::"
    "test_happy_path_creates_candidate_only_three_business_agent_workflow"
)

TRAINING_PLAN_SKILL_IDS = (
    "tpa_feedback_ref_alignment_skill",
    "tpa_asset_candidate_ref_alignment_skill",
    "tpa_training_plan_candidate_planning_skill",
    "tpa_training_plan_handoff_preparation_skill",
)

TRAINING_PLAN_TOOL_IDS = (
    "tpa_feedback_candidate_ref_reader",
    "tpa_asset_update_candidate_ref_reader",
    "tpa_training_policy_ref_checker",
    "tpa_training_plan_candidate_ref_builder",
)


def build_training_plan_agent_definition() -> AgentDefinition:
    """Build the L5 contract-only Training Plan Agent definition."""

    return AgentDefinition(
        agent_id=TRAINING_PLAN_AGENT_ID,
        agent_name="Training Plan Agent",
        domain="training_plan_orchestration",
        version=TRAINING_PLAN_AGENT_VERSION,
        maturity_level=L5_CONTRACT_MATURITY_LEVEL,
        lifecycle_status=L5_CONTRACT_LIFECYCLE_STATUS,
        mission="Prepare training plan candidate refs from feedback and asset candidate refs only.",
        user_goal="Review a training plan candidate without creating a formal training plan.",
        autonomous_goal="Compose a candidate training plan ref while preserving candidate/formal boundaries.",
        non_goals=(
            "no L5 release claim",
            "no runtime execution",
            "no direct DB or repository write",
            "no prompt rendering",
            "no provider or LLM call",
            "no formal training plan write",
            "no Phase 12 release gate implementation",
        ),
        input_contract="agent.training_plan.input_refs.v1",
        output_contract="agent.training_plan.output_candidate_refs.v1",
        candidate_outputs=("training_plan_candidate",),
        formal_write_boundary=(
            "direct formal writes disallowed; training_plan_candidate remains review-only "
            "until a separately authorized handoff"
        ),
        skills=TRAINING_PLAN_SKILL_IDS,
        tools=TRAINING_PLAN_TOOL_IDS,
        memory_state="refs_only_no_durable_state",
        planning_strategy="deterministic_candidate_ref_planning_only",
        guardrails=(
            "candidate_only",
            "formal_write_blocked",
            "trace_validation_refs_separated",
            "no_repository_or_db_tool_exposure",
        ),
        hitl_triggers=("formal_write_requested", "low_confidence", "validation_failed_partial_result"),
        failure_semantics="fail_closed_without_training_plan_candidate_or_formal_write",
        trace_contract=_build_training_plan_trace_contract(),
        eval_contract=EvalContract(
            contract_id="eval.training_plan_agent.v1",
            eval_suite_ids=(TRAINING_PLAN_EVAL_SUITE_ID,),
            metrics=("candidate_ref_shape", "handoff_ref_lineage", "forbidden_data_omission"),
            failure_policy="fail_closed",
            dataset_refs=("phase12.multi_agent_eval_dataset.deferred",),
            grader_refs=("phase12.multi_agent_grader.deferred",),
            regression_cases=("phase11.minimal_three_agent_candidate_slice",),
            minimum_pass_criteria="training plan candidate refs validate without formal write",
            ci_gate="deferred_phase_12",
            failure_triage_policy="record_gap_without_l5_release_claim",
        ),
        handoff_contract=build_handoff_contract(
            "handoff.training_plan_agent.v1",
            candidate_ref_types=("training_plan_candidate",),
            payload_schema_id="agent.training_plan.handoff_payload.v1",
            validation_refs=("training_policy_ref_checker", "asset_update_candidate_ref_reader"),
            quality_gate="training_plan_candidate_review_only",
            side_effect_key="training_plan_candidate_ref_handoff",
            idempotency_key="training_plan_candidate_ref",
            formal_write_preconditions=(
                "candidate_validated",
                "separately_authorized_application_handoff",
            ),
            allowed_formal_targets=(),
            user_confirmation_required=False,
        ),
        versioning_policy="semver_definition_version_with_l5_contract_catalog_revision",
        schema_version=AGENT_DEFINITION_SCHEMA_VERSION,
        catalog_revision=L5_CONTRACT_CATALOG_REVISION,
    )


def build_training_plan_skill_definitions() -> tuple[SkillDefinition, ...]:
    """Build Training Plan skill contracts without runtime execution."""

    return tuple(
        replace(skill, test_refs=(L5_PRODUCT_SLICE_TEST_REF,))
        for skill in (
            build_skill_definition(
                "tpa_feedback_ref_alignment_skill",
                "TrainingPlanFeedbackRefAlignmentSkill",
                owner_agent_id=TRAINING_PLAN_AGENT_ID,
                purpose="Align training plan candidate scope to feedback_candidate refs.",
                tool_refs=("tpa_feedback_candidate_ref_reader",),
                deterministic_policy_refs=("feedback_candidate_refs_only_policy",),
                eval_refs=(TRAINING_PLAN_EVAL_SUITE_ID, "phase12_multi_agent_eval_deferred"),
                output_summary="feedback refs are available for training plan candidate planning",
            ),
            build_skill_definition(
                "tpa_asset_candidate_ref_alignment_skill",
                "TrainingPlanAssetCandidateRefAlignmentSkill",
                owner_agent_id=TRAINING_PLAN_AGENT_ID,
                purpose="Align training plan candidate scope to asset_update_candidate refs.",
                tool_refs=("tpa_asset_update_candidate_ref_reader",),
                deterministic_policy_refs=("asset_update_candidate_refs_only_policy",),
                eval_refs=(TRAINING_PLAN_EVAL_SUITE_ID, "phase12_multi_agent_eval_deferred"),
                output_summary="asset update candidate refs are available for training plan planning",
            ),
            build_skill_definition(
                "tpa_training_plan_candidate_planning_skill",
                "TrainingPlanCandidatePlanningSkill",
                owner_agent_id=TRAINING_PLAN_AGENT_ID,
                purpose="Plan training_plan_candidate refs without formal training plan persistence.",
                tool_refs=("tpa_training_plan_candidate_ref_builder",),
                deterministic_policy_refs=("training_plan_candidate_only_policy",),
                eval_refs=(TRAINING_PLAN_EVAL_SUITE_ID, "phase12_multi_agent_eval_deferred"),
                output_summary="training plan candidate refs are prepared for review",
            ),
            build_skill_definition(
                "tpa_training_plan_handoff_preparation_skill",
                "TrainingPlanHandoffPreparationSkill",
                owner_agent_id=TRAINING_PLAN_AGENT_ID,
                purpose="Prepare refs-only handoff metadata for training plan candidates.",
                tool_refs=("tpa_training_policy_ref_checker",),
                deterministic_policy_refs=("candidate_handoff_refs_only_policy",),
                eval_refs=(TRAINING_PLAN_EVAL_SUITE_ID, "phase12_multi_agent_eval_deferred"),
                output_summary="training plan handoff refs are ready without formal output",
            ),
        )
    )


def build_training_plan_tool_definitions() -> tuple[ToolDefinition, ...]:
    """Build Training Plan tool contracts for project-level registration."""

    return (
        build_tool_definition(
            "tpa_feedback_candidate_ref_reader",
            "read_feedback_candidate_refs",
            allowed_callers=(TRAINING_PLAN_AGENT_ID,),
        ),
        build_tool_definition(
            "tpa_asset_update_candidate_ref_reader",
            "read_asset_update_candidate_refs",
            allowed_callers=(TRAINING_PLAN_AGENT_ID,),
        ),
        build_tool_definition(
            "tpa_training_policy_ref_checker",
            "check_training_policy_refs",
            allowed_callers=(TRAINING_PLAN_AGENT_ID,),
        ),
        build_tool_definition(
            "tpa_training_plan_candidate_ref_builder",
            "build_training_plan_candidate_refs",
            allowed_callers=(TRAINING_PLAN_AGENT_ID,),
            side_effect_policy="candidate_write",
        ),
    )


def _build_training_plan_trace_contract() -> TraceContract:
    return TraceContract(
        contract_id="trace.training_plan_agent.v1",
        input_refs=("training_plan_agent.input_refs",),
        plan_refs=("training_plan_agent.candidate_plan_ref",),
        skill_refs=("training_plan_agent.skill_refs",),
        tool_refs=("training_plan_agent.tool_refs",),
        policy_refs=("training_plan_agent.candidate_only_policy", "training_plan_agent.refs_lineage_policy"),
        provider_refs=(),
        candidate_refs=("training_plan_candidate",),
        validation_refs=("training_plan_agent.validation_refs",),
        handoff_refs=("training_plan_agent.handoff_refs",),
        output_refs=("training_plan_agent.candidate_output_refs",),
        events=(
            "training_plan_agent.refs_checked",
            "training_plan_agent.asset_candidate_ref_aligned",
            "training_plan_agent.candidate_ref_prepared",
            "training_plan_agent.handoff_ref_prepared",
        ),
    )


__all__ = [
    "TRAINING_PLAN_AGENT_ID",
    "TRAINING_PLAN_SKILL_IDS",
    "TRAINING_PLAN_TOOL_IDS",
    "build_training_plan_agent_definition",
    "build_training_plan_skill_definitions",
    "build_training_plan_tool_definitions",
]
