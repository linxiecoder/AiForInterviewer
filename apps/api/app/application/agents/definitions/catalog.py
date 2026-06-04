from __future__ import annotations

from dataclasses import dataclass

from app.application.agents.contracts import (
    AgentDefinition,
    EvalContract,
    HandoffContract,
    SkillDefinition,
    ToolDefinition,
    TraceContract,
)
from app.application.agents.registry import (
    AgentDefinitionRegistry,
    REQUIRED_TOOL_FORBIDDEN_DATA,
    SkillRegistry,
    ToolRegistry,
)


C1_VERSION = "p4.c1"
C1_MATURITY_LEVEL = "L2 planned guarded workflow"
C1_LIFECYCLE_STATUS = "planned_guarded_workflow"
_FORBIDDEN_DATA = tuple(sorted(REQUIRED_TOOL_FORBIDDEN_DATA))


@dataclass(frozen=True)
class AgentPlatformC1Registries:
    agent_definitions: AgentDefinitionRegistry
    skills: SkillRegistry
    tools: ToolRegistry


def _trace_contract(contract_id: str, *, agent_prefix: str, candidate_refs: tuple[str, ...]) -> TraceContract:
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
        forbidden_data=_FORBIDDEN_DATA,
    )


def _eval_contract(contract_id: str, *, suite_id: str) -> EvalContract:
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


def _handoff_contract(
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


def _skill(
    skill_id: str,
    skill_name: str,
    *,
    owner_agent_id: str,
    tool_refs: tuple[str, ...],
    deterministic_policy_refs: tuple[str, ...] = (),
    llm_refs: tuple[str, ...] = (),
    eval_refs: tuple[str, ...] = (),
) -> SkillDefinition:
    return SkillDefinition(
        skill_id=skill_id,
        skill_name=skill_name,
        owner_agent_ids=(owner_agent_id,),
        input_schema_id=f"agent.{owner_agent_id}.{skill_id}.input.{C1_VERSION}",
        output_schema_id=f"agent.{owner_agent_id}.{skill_id}.output.{C1_VERSION}",
        implementation_type="contract_only",
        deterministic_policy_refs=deterministic_policy_refs,
        llm_refs=llm_refs,
        tool_refs=tool_refs,
        timeout_policy="no_runtime_execution",
        retry_policy="not_applicable",
        failure_semantics="fail_closed",
        trace_events=(f"skill.{skill_id}.contract_checked",),
        eval_refs=eval_refs,
    )


def _tool(
    tool_id: str,
    tool_name: str,
    *,
    allowed_callers: tuple[str, ...],
    side_effect_policy: str = "read_only",
) -> ToolDefinition:
    return ToolDefinition(
        tool_id=tool_id,
        tool_name=tool_name,
        input_schema_id=f"agent.tool.{tool_id}.input.{C1_VERSION}",
        output_schema_id=f"agent.tool.{tool_id}.output.{C1_VERSION}",
        permission_scope="owner_scoped_contract",
        owner_scope="application_contract_only",
        side_effect_policy=side_effect_policy,
        timeout_seconds=5,
        retry_policy="none",
        allowed_callers=allowed_callers,
        forbidden_data=_FORBIDDEN_DATA,
        trace_events=(f"tool.{tool_id}.contract_checked",),
    )


def build_phase4_c1_agent_definitions() -> tuple[AgentDefinition, ...]:
    question_skills = (
        "qag_source_support_classification_skill",
        "qag_question_intent_planning_skill",
        "qag_question_kind_selection_skill",
        "qag_evidence_grounding_skill",
        "qag_follow_up_coverage_skill",
        "qag_anti_repetition_skill",
        "qag_expected_point_drafting_skill",
        "qag_rubric_drafting_skill",
    )
    question_tools = (
        "qag_canonical_evidence_pack",
        "qag_progress_node",
        "qag_prior_questions",
        "qag_prior_feedback",
        "qag_same_focus_history",
        "qag_source_support_classifier",
        "qag_question_grounding_validator",
        "qag_follow_up_coverage_evaluator",
    )
    feedback_skills = (
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
    feedback_tools = (
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

    return (
        AgentDefinition(
            agent_id="polish_question_agent",
            agent_name="Polish Question Agent",
            domain="polish",
            version=C1_VERSION,
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
            input_contract="agent.polish_question.input.p4.c1",
            output_contract="agent.polish_question.output_candidate.p4.c1",
            candidate_outputs=("question_candidate",),
            formal_write_boundary=(
                "direct formal writes disallowed; Application Service -> Domain Policy -> "
                "Handoff -> Repository / Transaction"
            ),
            skills=question_skills,
            tools=question_tools,
            memory_state="stateless_contract_refs",
            planning_strategy="planned_guarded_workflow_contract_only",
            guardrails=("candidate_only", "no_prompt_payload_leakage", "no_runtime_wiring"),
            hitl_triggers=("low_confidence", "insufficient_evidence", "handoff_required"),
            failure_semantics="fail_closed_without_formal_write",
            trace_contract=_trace_contract(
                "trace.polish_question_agent.p4.c1",
                agent_prefix="polish_question_agent",
                candidate_refs=("question_candidate",),
            ),
            eval_contract=_eval_contract(
                "eval.polish_question_agent.p4.c1",
                suite_id="eval.polish_question_agent.contract_refs.p4.c1",
            ),
            handoff_contract=_handoff_contract(
                "handoff.polish_question_agent.p4.c1",
                candidate_ref_types=("question_candidate",),
                payload_schema_id="agent.polish_question.handoff_payload.p4.c1",
                validation_refs=("question_grounding_validator", "follow_up_coverage_evaluator"),
                quality_gate="application_service_acceptance",
                side_effect_key="question_candidate_handoff",
                idempotency_key="question_candidate_ref",
                formal_write_preconditions=("candidate_validated", "application_service_handoff"),
                allowed_formal_targets=("polish_question",),
                user_confirmation_required=False,
            ),
            versioning_policy="phase_window_version_p4.c1",
            task_types=("polish_question_generation",),
        ),
        AgentDefinition(
            agent_id="polish_feedback_agent",
            agent_name="Polish Feedback Agent",
            domain="polish",
            version=C1_VERSION,
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
            input_contract="agent.polish_feedback.input.p4.c1",
            output_contract="agent.polish_feedback.output_candidate.p4.c1",
            candidate_outputs=("feedback_candidate", "asset_update_candidate"),
            formal_write_boundary=(
                "direct formal writes disallowed; Application Service -> Domain Policy -> "
                "Handoff -> Repository / Transaction"
            ),
            skills=feedback_skills,
            tools=feedback_tools,
            memory_state="stateless_contract_refs",
            planning_strategy="planned_guarded_workflow_contract_only",
            guardrails=("candidate_only", "user_confirm_asset_update", "no_runtime_wiring"),
            hitl_triggers=("asset_conflict", "low_confidence", "user_confirmation_required"),
            failure_semantics="fail_closed_without_formal_write",
            trace_contract=_trace_contract(
                "trace.polish_feedback_agent.p4.c1",
                agent_prefix="polish_feedback_agent",
                candidate_refs=("feedback_candidate", "asset_update_candidate"),
            ),
            eval_contract=_eval_contract(
                "eval.polish_feedback_agent.p4.c1",
                suite_id="eval.polish_feedback_agent.contract_refs.p4.c1",
            ),
            handoff_contract=_handoff_contract(
                "handoff.polish_feedback_agent.p4.c1",
                candidate_ref_types=("feedback_candidate", "asset_update_candidate"),
                payload_schema_id="agent.polish_feedback.handoff_payload.p4.c1",
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
            versioning_policy="phase_window_version_p4.c1",
            task_types=("polish_feedback_generation",),
        ),
    )


def build_phase4_c1_skill_definitions() -> tuple[SkillDefinition, ...]:
    return (
        _skill(
            "qag_source_support_classification_skill",
            "SourceSupportClassificationSkill",
            owner_agent_id="polish_question_agent",
            tool_refs=("qag_source_support_classifier",),
            deterministic_policy_refs=("source_support_classification_policy",),
            eval_refs=("eval.polish_question_agent.contract_refs.p4.c1",),
        ),
        _skill(
            "qag_question_intent_planning_skill",
            "QuestionIntentPlanningSkill",
            owner_agent_id="polish_question_agent",
            tool_refs=("qag_canonical_evidence_pack", "qag_progress_node"),
            eval_refs=("eval.polish_question_agent.contract_refs.p4.c1",),
        ),
        _skill(
            "qag_question_kind_selection_skill",
            "QuestionKindSelectionSkill",
            owner_agent_id="polish_question_agent",
            tool_refs=("qag_progress_node", "qag_same_focus_history"),
            eval_refs=("eval.polish_question_agent.contract_refs.p4.c1",),
        ),
        _skill(
            "qag_evidence_grounding_skill",
            "EvidenceGroundingSkill",
            owner_agent_id="polish_question_agent",
            tool_refs=("qag_canonical_evidence_pack", "qag_question_grounding_validator"),
            deterministic_policy_refs=("question_grounding_policy",),
            eval_refs=("eval.polish_question_agent.contract_refs.p4.c1",),
        ),
        _skill(
            "qag_follow_up_coverage_skill",
            "FollowUpCoverageSkill",
            owner_agent_id="polish_question_agent",
            tool_refs=("qag_prior_questions", "qag_follow_up_coverage_evaluator"),
            deterministic_policy_refs=("follow_up_coverage_policy",),
            eval_refs=("eval.polish_question_agent.contract_refs.p4.c1",),
        ),
        _skill(
            "qag_anti_repetition_skill",
            "AntiRepetitionSkill",
            owner_agent_id="polish_question_agent",
            tool_refs=("qag_prior_questions", "qag_same_focus_history"),
            deterministic_policy_refs=("question_anti_repetition_policy",),
            eval_refs=("eval.polish_question_agent.contract_refs.p4.c1",),
        ),
        _skill(
            "qag_expected_point_drafting_skill",
            "ExpectedPointDraftingSkill",
            owner_agent_id="polish_question_agent",
            tool_refs=("qag_canonical_evidence_pack",),
            llm_refs=("question_expected_point_prompt_contract",),
            eval_refs=("eval.polish_question_agent.contract_refs.p4.c1",),
        ),
        _skill(
            "qag_rubric_drafting_skill",
            "RubricDraftingSkill",
            owner_agent_id="polish_question_agent",
            tool_refs=("qag_canonical_evidence_pack", "qag_prior_feedback"),
            llm_refs=("question_rubric_prompt_contract",),
            eval_refs=("eval.polish_question_agent.contract_refs.p4.c1",),
        ),
        _skill(
            "fag_expected_point_building_skill",
            "ExpectedPointBuildingSkill",
            owner_agent_id="polish_feedback_agent",
            tool_refs=("fag_question_expected_points",),
            eval_refs=("eval.polish_feedback_agent.contract_refs.p4.c1",),
        ),
        _skill(
            "fag_asset_consistency_review_skill",
            "AssetConsistencyReviewSkill",
            owner_agent_id="polish_feedback_agent",
            tool_refs=("fag_canonical_evidence_pack", "fag_asset_consistency_checker"),
            deterministic_policy_refs=("asset_consistency_policy",),
            eval_refs=("eval.polish_feedback_agent.contract_refs.p4.c1",),
        ),
        _skill(
            "fag_answer_coverage_review_skill",
            "AnswerCoverageReviewSkill",
            owner_agent_id="polish_feedback_agent",
            tool_refs=("fag_answer_coverage_calculator",),
            deterministic_policy_refs=("answer_coverage_policy",),
            eval_refs=("eval.polish_feedback_agent.contract_refs.p4.c1",),
        ),
        _skill(
            "fag_same_question_change_review_skill",
            "SameQuestionChangeReviewSkill",
            owner_agent_id="polish_feedback_agent",
            tool_refs=("fag_same_question_attempts", "fag_answer_attempt_comparator"),
            deterministic_policy_refs=("same_question_change_policy",),
            eval_refs=("eval.polish_feedback_agent.contract_refs.p4.c1",),
        ),
        _skill(
            "fag_scoring_skill",
            "ScoringSkill",
            owner_agent_id="polish_feedback_agent",
            tool_refs=("fag_question_expected_points", "fag_answer_coverage_calculator"),
            deterministic_policy_refs=("feedback_scoring_policy",),
            eval_refs=("eval.polish_feedback_agent.contract_refs.p4.c1",),
        ),
        _skill(
            "fag_loss_point_extraction_skill",
            "LossPointExtractionSkill",
            owner_agent_id="polish_feedback_agent",
            tool_refs=("fag_answer_coverage_calculator",),
            llm_refs=("feedback_loss_point_prompt_contract",),
            eval_refs=("eval.polish_feedback_agent.contract_refs.p4.c1",),
        ),
        _skill(
            "fag_reference_answer_planning_skill",
            "ReferenceAnswerPlanningSkill",
            owner_agent_id="polish_feedback_agent",
            tool_refs=("fag_question_expected_points", "fag_canonical_evidence_pack"),
            llm_refs=("feedback_reference_answer_prompt_contract",),
            eval_refs=("eval.polish_feedback_agent.contract_refs.p4.c1",),
        ),
        _skill(
            "fag_feedback_card_composition_skill",
            "FeedbackCardCompositionSkill",
            owner_agent_id="polish_feedback_agent",
            tool_refs=("fag_feedback_card_composer",),
            llm_refs=("feedback_card_prompt_contract",),
            eval_refs=("eval.polish_feedback_agent.contract_refs.p4.c1",),
        ),
        _skill(
            "fag_next_action_planning_skill",
            "NextActionPlanningSkill",
            owner_agent_id="polish_feedback_agent",
            tool_refs=("fag_next_action_validator",),
            deterministic_policy_refs=("feedback_next_action_policy",),
            eval_refs=("eval.polish_feedback_agent.contract_refs.p4.c1",),
        ),
        _skill(
            "fag_asset_candidate_proposal_skill",
            "AssetCandidateProposalSkill",
            owner_agent_id="polish_feedback_agent",
            tool_refs=("fag_asset_candidate_proposer",),
            deterministic_policy_refs=("asset_candidate_confirmation_policy",),
            eval_refs=("eval.polish_feedback_agent.contract_refs.p4.c1",),
        ),
    )


def build_phase4_c1_tool_definitions() -> tuple[ToolDefinition, ...]:
    return (
        _tool(
            "qag_canonical_evidence_pack",
            "get_canonical_evidence_pack",
            allowed_callers=("polish_question_agent",),
        ),
        _tool("qag_progress_node", "get_progress_node", allowed_callers=("polish_question_agent",)),
        _tool("qag_prior_questions", "get_prior_questions", allowed_callers=("polish_question_agent",)),
        _tool("qag_prior_feedback", "get_prior_feedback", allowed_callers=("polish_question_agent",)),
        _tool("qag_same_focus_history", "get_same_focus_history", allowed_callers=("polish_question_agent",)),
        _tool(
            "qag_source_support_classifier",
            "classify_source_support",
            allowed_callers=("polish_question_agent",),
        ),
        _tool(
            "qag_question_grounding_validator",
            "validate_question_grounding",
            allowed_callers=("polish_question_agent",),
        ),
        _tool(
            "qag_follow_up_coverage_evaluator",
            "evaluate_follow_up_coverage",
            allowed_callers=("polish_question_agent",),
        ),
        _tool(
            "fag_canonical_evidence_pack",
            "get_canonical_evidence_pack",
            allowed_callers=("polish_feedback_agent",),
        ),
        _tool(
            "fag_question_expected_points",
            "get_question_expected_points",
            allowed_callers=("polish_feedback_agent",),
        ),
        _tool(
            "fag_same_question_attempts",
            "get_same_question_attempts",
            allowed_callers=("polish_feedback_agent",),
        ),
        _tool(
            "fag_asset_consistency_checker",
            "check_asset_consistency",
            allowed_callers=("polish_feedback_agent",),
        ),
        _tool(
            "fag_answer_coverage_calculator",
            "calculate_answer_coverage",
            allowed_callers=("polish_feedback_agent",),
        ),
        _tool(
            "fag_answer_attempt_comparator",
            "compare_answer_attempts",
            allowed_callers=("polish_feedback_agent",),
        ),
        _tool(
            "fag_feedback_card_composer",
            "compose_feedback_cards",
            allowed_callers=("polish_feedback_agent",),
        ),
        _tool(
            "fag_next_action_validator",
            "validate_next_actions",
            allowed_callers=("polish_feedback_agent",),
        ),
        _tool(
            "fag_asset_candidate_proposer",
            "propose_asset_candidates",
            allowed_callers=("polish_feedback_agent",),
            side_effect_policy="candidate_write",
        ),
    )


def build_default_agent_platform_c1_registries() -> AgentPlatformC1Registries:
    agent_registry = AgentDefinitionRegistry(build_phase4_c1_agent_definitions())
    skill_registry = SkillRegistry(build_phase4_c1_skill_definitions())
    tool_registry = ToolRegistry(build_phase4_c1_tool_definitions())
    agent_registry.validate_references(skill_registry, tool_registry)
    return AgentPlatformC1Registries(
        agent_definitions=agent_registry,
        skills=skill_registry,
        tools=tool_registry,
    )


__all__ = [
    "AgentPlatformC1Registries",
    "C1_LIFECYCLE_STATUS",
    "C1_MATURITY_LEVEL",
    "C1_VERSION",
    "build_default_agent_platform_c1_registries",
    "build_phase4_c1_agent_definitions",
    "build_phase4_c1_skill_definitions",
    "build_phase4_c1_tool_definitions",
]
