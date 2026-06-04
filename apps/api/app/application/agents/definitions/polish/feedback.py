"""Contract-only C1 definitions for the Polish Feedback Agent catalog slice."""

from __future__ import annotations

from app.application.agents.contracts import AgentDefinition, SkillDefinition, ToolDefinition
from app.application.agents.definitions.common import (
    build_eval_contract,
    build_handoff_contract,
    build_skill_definition,
    build_tool_definition,
    build_trace_contract,
)
from app.application.agents.definitions.versions import (
    AGENT_DEFINITION_SCHEMA_VERSION,
    C1_LIFECYCLE_STATUS,
    C1_MATURITY_LEVEL,
    CATALOG_REVISION,
    POLISH_FEEDBACK_AGENT_VERSION,
)


POLISH_FEEDBACK_AGENT_ID = "polish_feedback_agent"
FEEDBACK_EVAL_SUITE_ID = "eval.polish_feedback_agent.contract_refs.v1"

FEEDBACK_SKILL_IDS = (
    "fag_expected_point_building_skill",
    "fag_asset_consistency_review_skill",
    "fag_answer_coverage_review_skill",
    "fag_same_question_change_review_skill",
    "fag_scoring_skill",
    "fag_loss_point_extraction_skill",
    "fag_reference_answer_planning_skill",
    "fag_feedback_card_composition_skill",
    "fag_next_action_planning_skill",
    "fag_asset_candidate_proposal_skill",
)

FEEDBACK_TOOL_IDS = (
    "fag_canonical_evidence_pack",
    "fag_question_expected_points",
    "fag_same_question_attempts",
    "fag_asset_consistency_checker",
    "fag_answer_coverage_calculator",
    "fag_answer_attempt_comparator",
    "fag_feedback_card_composer",
    "fag_next_action_validator",
    "fag_asset_candidate_proposer",
)


def build_polish_feedback_agent_definition() -> AgentDefinition:
    """Build the C1 Feedback Agent contract with candidate outputs only."""

    return AgentDefinition(
        agent_id=POLISH_FEEDBACK_AGENT_ID,
        agent_name="Polish Feedback Agent",
        domain="polish",
        version=POLISH_FEEDBACK_AGENT_VERSION,
        maturity_level=C1_MATURITY_LEVEL,
        lifecycle_status=C1_LIFECYCLE_STATUS,
        mission="Generate structured feedback and asset update candidates.",
        user_goal="Receive actionable feedback and reviewable asset update candidates.",
        autonomous_goal="Prepare candidate feedback without directly confirming formal asset updates.",
        non_goals=(
            "direct formal feedback write",
            "direct asset confirmation",
            "prompt rewrite",
            "provider execution",
            "runtime migration",
        ),
        input_contract="agent.polish_feedback.input.v1",
        output_contract="agent.polish_feedback.output_candidate.v1",
        candidate_outputs=("feedback_candidate", "asset_update_candidate"),
        formal_write_boundary=(
            "direct formal writes disallowed; Application Service -> Domain Policy -> "
            "Handoff -> Repository / Transaction"
        ),
        skills=FEEDBACK_SKILL_IDS,
        tools=FEEDBACK_TOOL_IDS,
        memory_state="stateless_contract_refs",
        planning_strategy="planned_guarded_workflow_contract_only",
        guardrails=("candidate_only", "user_confirm_asset_update", "no_runtime_wiring"),
        hitl_triggers=("asset_conflict", "low_confidence", "user_confirmation_required"),
        failure_semantics="fail_closed_without_formal_write",
        trace_contract=build_trace_contract(
            "trace.polish_feedback_agent.v1",
            agent_prefix=POLISH_FEEDBACK_AGENT_ID,
            candidate_refs=("feedback_candidate", "asset_update_candidate"),
        ),
        eval_contract=build_eval_contract(
            "eval.polish_feedback_agent.v1",
            suite_id=FEEDBACK_EVAL_SUITE_ID,
        ),
        handoff_contract=build_handoff_contract(
            "handoff.polish_feedback_agent.v1",
            candidate_ref_types=("feedback_candidate", "asset_update_candidate"),
            payload_schema_id="agent.polish_feedback.handoff_payload.v1",
            validation_refs=(
                "asset_consistency_checker",
                "answer_coverage_calculator",
                "next_action_validator",
            ),
            quality_gate="user_confirmed_asset_update",
            side_effect_key="asset_update_candidate_handoff",
            idempotency_key="feedback_asset_update_candidate_ref",
            formal_write_preconditions=(
                "candidate_validated",
                "asset_update_candidate_user_confirmed",
                "application_service_handoff",
            ),
            allowed_formal_targets=("polish_feedback", "polish_asset"),
            user_confirmation_required=True,
        ),
        versioning_policy="semver_definition_version_with_catalog_revision",
        task_types=("polish_feedback_generation",),
        schema_version=AGENT_DEFINITION_SCHEMA_VERSION,
        catalog_revision=CATALOG_REVISION,
    )


def build_polish_feedback_skill_definitions() -> tuple[SkillDefinition, ...]:
    """Build the Feedback Agent skill contracts without runtime execution."""

    return (
        build_skill_definition(
            "fag_expected_point_building_skill",
            "ExpectedPointBuildingSkill",
            owner_agent_id=POLISH_FEEDBACK_AGENT_ID,
            purpose="Resolve expected answer points before coverage and scoring are evaluated.",
            tool_refs=("fag_question_expected_points",),
            eval_refs=(FEEDBACK_EVAL_SUITE_ID,),
            output_summary="expected-point context is available for feedback scoring",
        ),
        build_skill_definition(
            "fag_asset_consistency_review_skill",
            "AssetConsistencyReviewSkill",
            owner_agent_id=POLISH_FEEDBACK_AGENT_ID,
            purpose="Review whether the answer remains consistent with canonical asset evidence.",
            tool_refs=("fag_canonical_evidence_pack", "fag_asset_consistency_checker"),
            deterministic_policy_refs=("asset_consistency_policy",),
            eval_refs=(FEEDBACK_EVAL_SUITE_ID,),
            output_summary="asset consistency validation refs are ready for feedback candidate output",
        ),
        build_skill_definition(
            "fag_answer_coverage_review_skill",
            "AnswerCoverageReviewSkill",
            owner_agent_id=POLISH_FEEDBACK_AGENT_ID,
            purpose="Measure answer coverage against expected points for candidate feedback.",
            tool_refs=("fag_answer_coverage_calculator",),
            deterministic_policy_refs=("answer_coverage_policy",),
            eval_refs=(FEEDBACK_EVAL_SUITE_ID,),
            output_summary="answer coverage result is available for scoring and loss-point extraction",
        ),
        build_skill_definition(
            "fag_same_question_change_review_skill",
            "SameQuestionChangeReviewSkill",
            owner_agent_id=POLISH_FEEDBACK_AGENT_ID,
            purpose="Compare same-question attempts to identify meaningful answer changes.",
            tool_refs=("fag_same_question_attempts", "fag_answer_attempt_comparator"),
            deterministic_policy_refs=("same_question_change_policy",),
            eval_refs=(FEEDBACK_EVAL_SUITE_ID,),
            output_summary="attempt-change review is available for feedback candidate reasoning",
        ),
        build_skill_definition(
            "fag_scoring_skill",
            "ScoringSkill",
            owner_agent_id=POLISH_FEEDBACK_AGENT_ID,
            purpose="Prepare candidate scoring metadata from expected points and answer coverage.",
            tool_refs=("fag_question_expected_points", "fag_answer_coverage_calculator"),
            deterministic_policy_refs=("feedback_scoring_policy",),
            eval_refs=(FEEDBACK_EVAL_SUITE_ID,),
            output_summary="candidate score metadata is available without formal score persistence",
        ),
        build_skill_definition(
            "fag_loss_point_extraction_skill",
            "LossPointExtractionSkill",
            owner_agent_id=POLISH_FEEDBACK_AGENT_ID,
            purpose="Extract candidate loss points from coverage evidence.",
            tool_refs=("fag_answer_coverage_calculator",),
            llm_refs=("feedback_loss_point_prompt_contract",),
            eval_refs=(FEEDBACK_EVAL_SUITE_ID,),
            output_summary="loss-point candidate metadata is prepared for feedback composition",
        ),
        build_skill_definition(
            "fag_reference_answer_planning_skill",
            "ReferenceAnswerPlanningSkill",
            owner_agent_id=POLISH_FEEDBACK_AGENT_ID,
            purpose="Plan reference answer guidance from expected points and canonical evidence.",
            tool_refs=("fag_question_expected_points", "fag_canonical_evidence_pack"),
            llm_refs=("feedback_reference_answer_prompt_contract",),
            eval_refs=(FEEDBACK_EVAL_SUITE_ID,),
            output_summary="reference-answer guidance is attached to the feedback candidate contract",
        ),
        build_skill_definition(
            "fag_feedback_card_composition_skill",
            "FeedbackCardCompositionSkill",
            owner_agent_id=POLISH_FEEDBACK_AGENT_ID,
            purpose="Compose structured feedback cards from validated candidate evidence.",
            tool_refs=("fag_feedback_card_composer",),
            llm_refs=("feedback_card_prompt_contract",),
            eval_refs=(FEEDBACK_EVAL_SUITE_ID,),
            output_summary="feedback card candidate output is composed and ready for validation",
        ),
        build_skill_definition(
            "fag_next_action_planning_skill",
            "NextActionPlanningSkill",
            owner_agent_id=POLISH_FEEDBACK_AGENT_ID,
            purpose="Plan next actions that are valid for the current feedback candidate state.",
            tool_refs=("fag_next_action_validator",),
            deterministic_policy_refs=("feedback_next_action_policy",),
            eval_refs=(FEEDBACK_EVAL_SUITE_ID,),
            output_summary="next-action recommendations are validated for candidate feedback",
        ),
        build_skill_definition(
            "fag_asset_candidate_proposal_skill",
            "AssetCandidateProposalSkill",
            owner_agent_id=POLISH_FEEDBACK_AGENT_ID,
            purpose="Propose reviewable asset update candidates without confirming formal asset writes.",
            tool_refs=("fag_asset_candidate_proposer",),
            deterministic_policy_refs=("asset_candidate_confirmation_policy",),
            eval_refs=(FEEDBACK_EVAL_SUITE_ID,),
            output_summary="asset update candidate refs are prepared for explicit user confirmation",
        ),
    )


def build_polish_feedback_tool_definitions() -> tuple[ToolDefinition, ...]:
    """Build the Feedback Agent tool contracts for project-level registration."""

    return (
        build_tool_definition(
            "fag_canonical_evidence_pack",
            "get_canonical_evidence_pack",
            allowed_callers=(POLISH_FEEDBACK_AGENT_ID,),
        ),
        build_tool_definition(
            "fag_question_expected_points",
            "get_question_expected_points",
            allowed_callers=(POLISH_FEEDBACK_AGENT_ID,),
        ),
        build_tool_definition(
            "fag_same_question_attempts",
            "get_same_question_attempts",
            allowed_callers=(POLISH_FEEDBACK_AGENT_ID,),
        ),
        build_tool_definition(
            "fag_asset_consistency_checker",
            "check_asset_consistency",
            allowed_callers=(POLISH_FEEDBACK_AGENT_ID,),
        ),
        build_tool_definition(
            "fag_answer_coverage_calculator",
            "calculate_answer_coverage",
            allowed_callers=(POLISH_FEEDBACK_AGENT_ID,),
        ),
        build_tool_definition(
            "fag_answer_attempt_comparator",
            "compare_answer_attempts",
            allowed_callers=(POLISH_FEEDBACK_AGENT_ID,),
        ),
        build_tool_definition(
            "fag_feedback_card_composer",
            "compose_feedback_cards",
            allowed_callers=(POLISH_FEEDBACK_AGENT_ID,),
        ),
        build_tool_definition(
            "fag_next_action_validator",
            "validate_next_actions",
            allowed_callers=(POLISH_FEEDBACK_AGENT_ID,),
        ),
        build_tool_definition(
            "fag_asset_candidate_proposer",
            "propose_asset_candidates",
            allowed_callers=(POLISH_FEEDBACK_AGENT_ID,),
            side_effect_policy="candidate_write",
        ),
    )


__all__ = [
    "FEEDBACK_SKILL_IDS",
    "FEEDBACK_TOOL_IDS",
    "POLISH_FEEDBACK_AGENT_ID",
    "build_polish_feedback_agent_definition",
    "build_polish_feedback_skill_definitions",
    "build_polish_feedback_tool_definitions",
]
