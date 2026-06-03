from __future__ import annotations

from app.domain.polish.policies.feedback_next_action_policy import (
    ACTION_CONFIRM_ASSET_UPDATE,
    ACTION_GENERATE_NEXT_QUESTION,
    FeedbackNextActionInput,
    FeedbackNextActionOutcome,
    FeedbackNextActionPolicy,
)


def test_asset_conflict_blocks_generate_next_question() -> None:
    decision = FeedbackNextActionPolicy.decide(
        FeedbackNextActionInput(
            existing_actions=(ACTION_GENERATE_NEXT_QUESTION, "answer_again"),
            asset_status="conflict",
            asset_conflict_count=1,
        )
    )

    assert decision.outcome == FeedbackNextActionOutcome.REQUEST_CLARIFICATION
    assert not decision.allow_generate_next_question
    assert ACTION_GENERATE_NEXT_QUESTION not in decision.actions
    assert decision.actions[:2] == ("clarify_asset_conflict", "revise_current_answer")
    assert "asset_conflict_blocks_next_question" in decision.blocking_reason_codes


def test_unresolved_coverage_continues_same_question() -> None:
    decision = FeedbackNextActionPolicy.decide(
        FeedbackNextActionInput(
            existing_actions=(ACTION_GENERATE_NEXT_QUESTION,),
            missing_points=("幂等键",),
        )
    )

    assert decision.outcome == FeedbackNextActionOutcome.CONTINUE_SAME_QUESTION
    assert decision.actions == ("continue_same_question",)
    assert not decision.allow_generate_next_question
    assert "unresolved_answer_points_block_next_question" in decision.reason_codes


def test_regressed_answer_retries_same_question_before_existing_actions() -> None:
    decision = FeedbackNextActionPolicy.decide(
        FeedbackNextActionInput(
            existing_actions=(ACTION_GENERATE_NEXT_QUESTION, "review_reference_answer"),
            regressed_points=("观测指标",),
        )
    )

    assert decision.outcome == FeedbackNextActionOutcome.RETRY_SAME_QUESTION
    assert decision.actions == (
        "retry_same_question_preserve_regressed_points",
        "review_reference_answer",
    )
    assert "answer_regression_blocks_next_question" in decision.blocking_reason_codes


def test_asset_update_candidate_requires_user_confirmation_without_formal_write() -> None:
    decision = FeedbackNextActionPolicy.decide(
        FeedbackNextActionInput(
            existing_actions=(ACTION_GENERATE_NEXT_QUESTION,),
            has_asset_update_candidates=True,
            unsupported_claim_count=1,
        )
    )

    assert decision.outcome == FeedbackNextActionOutcome.ASK_USER_CONFIRMATION
    assert decision.candidate_confirmation_required
    assert decision.actions == (ACTION_GENERATE_NEXT_QUESTION, ACTION_CONFIRM_ASSET_UPDATE)
    assert "asset_update_candidate_requires_user_confirmation" in decision.warning_reason_codes
    assert "unsupported_current_answer_fact_requires_confirmation" in decision.warning_reason_codes


def test_formal_asset_write_request_is_fail_closed_and_not_next_question() -> None:
    decision = FeedbackNextActionPolicy.decide(
        FeedbackNextActionInput(
            existing_actions=(ACTION_GENERATE_NEXT_QUESTION,),
            has_asset_update_candidates=True,
            formal_asset_write_requested=True,
        )
    )

    assert decision.outcome == FeedbackNextActionOutcome.NO_NEXT_QUESTION_DUE_TO_BLOCKER
    assert not decision.allow_generate_next_question
    assert ACTION_GENERATE_NEXT_QUESTION not in decision.actions
    assert ACTION_CONFIRM_ASSET_UPDATE in decision.actions
    assert "formal_asset_write_not_allowed" in decision.blocking_reason_codes


def test_provider_or_validation_failure_cannot_be_represented_as_success() -> None:
    provider_failure = FeedbackNextActionPolicy.decide(
        FeedbackNextActionInput(
            existing_actions=(ACTION_GENERATE_NEXT_QUESTION,),
            generation_status="provider_unavailable",
        )
    )
    validation_failure = FeedbackNextActionPolicy.decide(
        FeedbackNextActionInput(
            existing_actions=(ACTION_GENERATE_NEXT_QUESTION,),
            validation_failed=True,
        )
    )

    for decision in (provider_failure, validation_failure):
        assert decision.outcome == FeedbackNextActionOutcome.RETRY_OR_FAIL_CLOSED
        assert not decision.generated_success_allowed
        assert not decision.allow_generate_next_question
        assert ACTION_GENERATE_NEXT_QUESTION not in decision.actions
        assert decision.actions[:2] == ("retry_same_question", "continue_same_question")


def test_low_confidence_and_missing_asset_context_emit_reason_codes_without_behavior_change() -> None:
    decision = FeedbackNextActionPolicy.decide(
        FeedbackNextActionInput(
            existing_actions=(ACTION_GENERATE_NEXT_QUESTION,),
            generation_status="low_confidence",
            asset_status="insufficient_asset_context",
            low_confidence_flags=("reference_answer_source_unavailable",),
        )
    )

    assert decision.outcome == FeedbackNextActionOutcome.GENERATE_NEXT_QUESTION_ALLOWED
    assert decision.allow_generate_next_question
    assert decision.actions == (ACTION_GENERATE_NEXT_QUESTION,)
    assert "low_confidence_flags_present" in decision.warning_reason_codes
    assert "asset_context_insufficient" in decision.warning_reason_codes
