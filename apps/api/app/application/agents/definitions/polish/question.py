"""Contract-only C1 definitions for the Polish Question Agent catalog slice."""

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
    POLISH_QUESTION_AGENT_VERSION,
)


POLISH_QUESTION_AGENT_ID = "polish_question_agent"
QUESTION_EVAL_SUITE_ID = "eval.polish_question_agent.contract_refs.v1"

QUESTION_SKILL_IDS = (
    "qag_source_support_classification_skill",
    "qag_question_intent_planning_skill",
    "qag_question_kind_selection_skill",
    "qag_evidence_grounding_skill",
    "qag_follow_up_coverage_skill",
    "qag_anti_repetition_skill",
    "qag_expected_point_drafting_skill",
    "qag_rubric_drafting_skill",
)

QUESTION_TOOL_IDS = (
    "qag_canonical_evidence_pack",
    "qag_progress_node",
    "qag_prior_questions",
    "qag_prior_feedback",
    "qag_same_focus_history",
    "qag_source_support_classifier",
    "qag_question_grounding_validator",
    "qag_follow_up_coverage_evaluator",
)


def build_polish_question_agent_definition() -> AgentDefinition:
    """Build the C1 Question Agent contract with question-candidate output only."""

    return AgentDefinition(
        agent_id=POLISH_QUESTION_AGENT_ID,
        agent_name="Polish Question Agent",
        domain="polish",
        version=POLISH_QUESTION_AGENT_VERSION,
        maturity_level=C1_MATURITY_LEVEL,
        lifecycle_status=C1_LIFECYCLE_STATUS,
        mission="Generate the next evidence-grounded interview question candidate.",
        user_goal="Receive a valuable, traceable, scoreable question candidate.",
        autonomous_goal="Prepare a candidate question without writing formal business facts.",
        non_goals=(
            "direct formal question write",
            "prompt rewrite",
            "provider execution",
            "runtime migration",
        ),
        input_contract="agent.polish_question.input.v1",
        output_contract="agent.polish_question.output_candidate.v1",
        candidate_outputs=("question_candidate",),
        formal_write_boundary=(
            "direct formal writes disallowed; Application Service -> Domain Policy -> "
            "Handoff -> Repository / Transaction"
        ),
        skills=QUESTION_SKILL_IDS,
        tools=QUESTION_TOOL_IDS,
        memory_state="stateless_contract_refs",
        planning_strategy="planned_guarded_workflow_contract_only",
        guardrails=("candidate_only", "no_prompt_payload_leakage", "no_runtime_wiring"),
        hitl_triggers=("low_confidence", "insufficient_evidence", "handoff_required"),
        failure_semantics="fail_closed_without_formal_write",
        trace_contract=build_trace_contract(
            "trace.polish_question_agent.v1",
            agent_prefix=POLISH_QUESTION_AGENT_ID,
            candidate_refs=("question_candidate",),
        ),
        eval_contract=build_eval_contract(
            "eval.polish_question_agent.v1",
            suite_id=QUESTION_EVAL_SUITE_ID,
        ),
        handoff_contract=build_handoff_contract(
            "handoff.polish_question_agent.v1",
            candidate_ref_types=("question_candidate",),
            payload_schema_id="agent.polish_question.handoff_payload.v1",
            validation_refs=("question_grounding_validator", "follow_up_coverage_evaluator"),
            quality_gate="application_service_acceptance",
            side_effect_key="question_candidate_handoff",
            idempotency_key="question_candidate_ref",
            formal_write_preconditions=("candidate_validated", "application_service_handoff"),
            allowed_formal_targets=("polish_question",),
            user_confirmation_required=False,
        ),
        versioning_policy="semver_definition_version_with_catalog_revision",
        task_types=("polish_question_generation",),
        schema_version=AGENT_DEFINITION_SCHEMA_VERSION,
        catalog_revision=CATALOG_REVISION,
    )


def build_polish_question_skill_definitions() -> tuple[SkillDefinition, ...]:
    """Build the Question Agent skill contracts without runtime execution."""

    return (
        build_skill_definition(
            "qag_source_support_classification_skill",
            "SourceSupportClassificationSkill",
            owner_agent_id=POLISH_QUESTION_AGENT_ID,
            purpose="Classify whether available sources can support the next question candidate.",
            tool_refs=("qag_source_support_classifier",),
            deterministic_policy_refs=("source_support_classification_policy",),
            eval_refs=(QUESTION_EVAL_SUITE_ID,),
            output_summary="source-support classification is available for downstream question planning",
        ),
        build_skill_definition(
            "qag_question_intent_planning_skill",
            "QuestionIntentPlanningSkill",
            owner_agent_id=POLISH_QUESTION_AGENT_ID,
            purpose="Choose the business intent for the next question from evidence and progress context.",
            tool_refs=("qag_canonical_evidence_pack", "qag_progress_node"),
            eval_refs=(QUESTION_EVAL_SUITE_ID,),
            output_summary="question intent plan is prepared as contract metadata",
        ),
        build_skill_definition(
            "qag_question_kind_selection_skill",
            "QuestionKindSelectionSkill",
            owner_agent_id=POLISH_QUESTION_AGENT_ID,
            purpose="Select the question kind while respecting progress state and same-focus history.",
            tool_refs=("qag_progress_node", "qag_same_focus_history"),
            eval_refs=(QUESTION_EVAL_SUITE_ID,),
            output_summary="question kind selection is available before candidate drafting",
        ),
        build_skill_definition(
            "qag_evidence_grounding_skill",
            "EvidenceGroundingSkill",
            owner_agent_id=POLISH_QUESTION_AGENT_ID,
            purpose="Ground the question candidate in canonical evidence before handoff.",
            tool_refs=("qag_canonical_evidence_pack", "qag_question_grounding_validator"),
            deterministic_policy_refs=("question_grounding_policy",),
            eval_refs=(QUESTION_EVAL_SUITE_ID,),
            output_summary="question candidate grounding has validation refs and evidence refs",
        ),
        build_skill_definition(
            "qag_follow_up_coverage_skill",
            "FollowUpCoverageSkill",
            owner_agent_id=POLISH_QUESTION_AGENT_ID,
            purpose="Check whether follow-up coverage satisfies the current focus and prior questions.",
            tool_refs=("qag_prior_questions", "qag_follow_up_coverage_evaluator"),
            deterministic_policy_refs=("follow_up_coverage_policy",),
            eval_refs=(QUESTION_EVAL_SUITE_ID,),
            output_summary="follow-up coverage decision is ready for candidate acceptance",
        ),
        build_skill_definition(
            "qag_anti_repetition_skill",
            "AntiRepetitionSkill",
            owner_agent_id=POLISH_QUESTION_AGENT_ID,
            purpose="Prevent repetitive question candidates for the same focus history.",
            tool_refs=("qag_prior_questions", "qag_same_focus_history"),
            deterministic_policy_refs=("question_anti_repetition_policy",),
            eval_refs=(QUESTION_EVAL_SUITE_ID,),
            output_summary="anti-repetition check has passed or failed closed",
        ),
        build_skill_definition(
            "qag_expected_point_drafting_skill",
            "ExpectedPointDraftingSkill",
            owner_agent_id=POLISH_QUESTION_AGENT_ID,
            purpose="Draft expected answer points for the candidate question contract.",
            tool_refs=("qag_canonical_evidence_pack",),
            llm_refs=("question_expected_point_prompt_contract",),
            eval_refs=(QUESTION_EVAL_SUITE_ID,),
            output_summary="expected points are attached to the question candidate contract",
        ),
        build_skill_definition(
            "qag_rubric_drafting_skill",
            "RubricDraftingSkill",
            owner_agent_id=POLISH_QUESTION_AGENT_ID,
            purpose="Draft the scoring rubric from evidence and prior feedback context.",
            tool_refs=("qag_canonical_evidence_pack", "qag_prior_feedback"),
            llm_refs=("question_rubric_prompt_contract",),
            eval_refs=(QUESTION_EVAL_SUITE_ID,),
            output_summary="rubric metadata is attached to the question candidate contract",
        ),
    )


def build_polish_question_tool_definitions() -> tuple[ToolDefinition, ...]:
    """Build the Question Agent tool contracts for project-level registration."""

    return (
        build_tool_definition(
            "qag_canonical_evidence_pack",
            "get_canonical_evidence_pack",
            allowed_callers=(POLISH_QUESTION_AGENT_ID,),
        ),
        build_tool_definition(
            "qag_progress_node",
            "get_progress_node",
            allowed_callers=(POLISH_QUESTION_AGENT_ID,),
        ),
        build_tool_definition(
            "qag_prior_questions",
            "get_prior_questions",
            allowed_callers=(POLISH_QUESTION_AGENT_ID,),
        ),
        build_tool_definition(
            "qag_prior_feedback",
            "get_prior_feedback",
            allowed_callers=(POLISH_QUESTION_AGENT_ID,),
        ),
        build_tool_definition(
            "qag_same_focus_history",
            "get_same_focus_history",
            allowed_callers=(POLISH_QUESTION_AGENT_ID,),
        ),
        build_tool_definition(
            "qag_source_support_classifier",
            "classify_source_support",
            allowed_callers=(POLISH_QUESTION_AGENT_ID,),
        ),
        build_tool_definition(
            "qag_question_grounding_validator",
            "validate_question_grounding",
            allowed_callers=(POLISH_QUESTION_AGENT_ID,),
        ),
        build_tool_definition(
            "qag_follow_up_coverage_evaluator",
            "evaluate_follow_up_coverage",
            allowed_callers=(POLISH_QUESTION_AGENT_ID,),
        ),
    )


__all__ = [
    "POLISH_QUESTION_AGENT_ID",
    "QUESTION_SKILL_IDS",
    "QUESTION_TOOL_IDS",
    "build_polish_question_agent_definition",
    "build_polish_question_skill_definitions",
    "build_polish_question_tool_definitions",
]
