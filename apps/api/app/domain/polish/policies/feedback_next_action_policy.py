"""Pure next-action policy for Polish feedback review."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


ACTION_GENERATE_NEXT_QUESTION = "generate_next_question"
ACTION_CLARIFY_ASSET_CONFLICT = "clarify_asset_conflict"
ACTION_REVISE_CURRENT_ANSWER = "revise_current_answer"
ACTION_CONTINUE_SAME_QUESTION = "continue_same_question"
ACTION_RETRY_SAME_QUESTION = "retry_same_question"
ACTION_RETRY_PRESERVE_REGRESSED = "retry_same_question_preserve_regressed_points"
ACTION_CONFIRM_ASSET_UPDATE = "confirm_asset_update_candidate"

_SUCCESS_STATUSES = {"generated", "partial", "low_confidence"}


class FeedbackNextActionOutcome(str, Enum):
    GENERATE_NEXT_QUESTION_ALLOWED = "generate_next_question_allowed"
    ASK_USER_CONFIRMATION = "ask_user_confirmation"
    REQUEST_CLARIFICATION = "request_clarification"
    CONTINUE_SAME_QUESTION = "continue_same_question"
    RETRY_SAME_QUESTION = "retry_same_question"
    RETRY_OR_FAIL_CLOSED = "retry_or_fail_closed"
    NO_NEXT_QUESTION_DUE_TO_BLOCKER = "no_next_question_due_to_blocker"


@dataclass(frozen=True)
class FeedbackNextActionInput:
    existing_actions: tuple[str, ...] = ()
    generation_status: str | None = "generated"
    validation_failed: bool = False
    asset_status: str | None = None
    asset_conflict_count: int = 0
    unsupported_claim_count: int = 0
    asset_user_clarification_required: bool = False
    missing_points: tuple[str, ...] = ()
    weak_points: tuple[str, ...] = ()
    contradicted_points: tuple[str, ...] = ()
    regressed_points: tuple[str, ...] = ()
    has_asset_update_candidates: bool = False
    all_asset_update_candidates_require_confirmation: bool = True
    formal_asset_write_requested: bool = False
    low_confidence_flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class FeedbackNextActionDecision:
    actions: tuple[str, ...]
    outcome: FeedbackNextActionOutcome
    allow_generate_next_question: bool
    generated_success_allowed: bool = True
    candidate_confirmation_required: bool = False
    reason_codes: tuple[str, ...] = ()
    blocking_reason_codes: tuple[str, ...] = ()
    warning_reason_codes: tuple[str, ...] = ()

    def to_legacy_actions(self) -> list[str]:
        return list(self.actions)


class FeedbackNextActionPolicy:
    @classmethod
    def decide(cls, value: FeedbackNextActionInput) -> FeedbackNextActionDecision:
        existing = _unique_actions(value.existing_actions)
        blocking: list[str] = []
        warnings: list[str] = []
        candidate_confirmation_required = False

        if _clean(value.generation_status, max_chars=80) not in _SUCCESS_STATUSES:
            blocking.append("feedback_generation_not_successful")
            return _decision(
                actions=_fail_closed_actions(existing),
                outcome=FeedbackNextActionOutcome.RETRY_OR_FAIL_CLOSED,
                blocking=blocking,
                warnings=warnings,
                generated_success_allowed=False,
                candidate_confirmation_required=False,
            )

        if value.validation_failed:
            blocking.append("feedback_validation_failed")
            return _decision(
                actions=_fail_closed_actions(existing),
                outcome=FeedbackNextActionOutcome.RETRY_OR_FAIL_CLOSED,
                blocking=blocking,
                warnings=warnings,
                generated_success_allowed=False,
                candidate_confirmation_required=False,
            )

        non_terminal_actions = tuple(action for action in existing if action != ACTION_GENERATE_NEXT_QUESTION)
        if value.low_confidence_flags:
            warnings.append("low_confidence_flags_present")
        if value.asset_status == "insufficient_asset_context":
            warnings.append("asset_context_insufficient")
        if value.has_asset_update_candidates:
            candidate_confirmation_required = True
            warnings.append("asset_update_candidate_requires_user_confirmation")
            if not value.all_asset_update_candidates_require_confirmation:
                warnings.append("asset_update_candidate_confirmation_missing_before_adapter")
        if value.unsupported_claim_count > 0:
            warnings.append("unsupported_current_answer_fact_requires_confirmation")

        if value.formal_asset_write_requested:
            blocking.append("formal_asset_write_not_allowed")
            actions = _with_candidate_confirmation(
                (ACTION_CONFIRM_ASSET_UPDATE, *non_terminal_actions),
                has_asset_update_candidates=value.has_asset_update_candidates,
            )
            return _decision(
                actions=actions,
                outcome=FeedbackNextActionOutcome.NO_NEXT_QUESTION_DUE_TO_BLOCKER,
                blocking=blocking,
                warnings=warnings,
                candidate_confirmation_required=candidate_confirmation_required,
            )

        if (
            value.asset_status == "conflict"
            or value.asset_conflict_count > 0
            or value.asset_user_clarification_required
        ):
            blocking.append("asset_conflict_blocks_next_question")
            actions = _with_candidate_confirmation(
                (ACTION_CLARIFY_ASSET_CONFLICT, ACTION_REVISE_CURRENT_ANSWER, *non_terminal_actions),
                has_asset_update_candidates=value.has_asset_update_candidates,
            )
            return _decision(
                actions=actions,
                outcome=FeedbackNextActionOutcome.REQUEST_CLARIFICATION,
                blocking=blocking,
                warnings=warnings,
                candidate_confirmation_required=candidate_confirmation_required,
            )

        if value.regressed_points:
            blocking.append("answer_regression_blocks_next_question")
            actions = _with_candidate_confirmation(
                (ACTION_RETRY_PRESERVE_REGRESSED, *non_terminal_actions),
                has_asset_update_candidates=value.has_asset_update_candidates,
            )
            return _decision(
                actions=actions,
                outcome=FeedbackNextActionOutcome.RETRY_SAME_QUESTION,
                blocking=blocking,
                warnings=warnings,
                candidate_confirmation_required=candidate_confirmation_required,
            )

        if _has_unresolved_answer_points(value):
            blocking.append("unresolved_answer_points_block_next_question")
            actions = _with_candidate_confirmation(
                (ACTION_CONTINUE_SAME_QUESTION, *non_terminal_actions),
                has_asset_update_candidates=value.has_asset_update_candidates,
            )
            return _decision(
                actions=actions,
                outcome=FeedbackNextActionOutcome.CONTINUE_SAME_QUESTION,
                blocking=blocking,
                warnings=warnings,
                candidate_confirmation_required=candidate_confirmation_required,
            )

        actions = _with_candidate_confirmation(existing, has_asset_update_candidates=value.has_asset_update_candidates)
        outcome = (
            FeedbackNextActionOutcome.ASK_USER_CONFIRMATION
            if candidate_confirmation_required
            else (
                FeedbackNextActionOutcome.GENERATE_NEXT_QUESTION_ALLOWED
                if ACTION_GENERATE_NEXT_QUESTION in actions
                else FeedbackNextActionOutcome.NO_NEXT_QUESTION_DUE_TO_BLOCKER
            )
        )
        return _decision(
            actions=actions,
            outcome=outcome,
            blocking=blocking,
            warnings=warnings,
            candidate_confirmation_required=candidate_confirmation_required,
        )


def _decision(
    *,
    actions: tuple[str, ...],
    outcome: FeedbackNextActionOutcome,
    blocking: list[str],
    warnings: list[str],
    generated_success_allowed: bool = True,
    candidate_confirmation_required: bool,
) -> FeedbackNextActionDecision:
    clean_actions = _unique_actions(actions)
    blocking_codes = tuple(dict.fromkeys(blocking))
    warning_codes = tuple(dict.fromkeys(warnings))
    return FeedbackNextActionDecision(
        actions=clean_actions,
        outcome=outcome,
        allow_generate_next_question=(
            generated_success_allowed
            and not blocking_codes
            and ACTION_GENERATE_NEXT_QUESTION in clean_actions
        ),
        generated_success_allowed=generated_success_allowed,
        candidate_confirmation_required=candidate_confirmation_required,
        reason_codes=tuple(dict.fromkeys((*blocking_codes, *warning_codes))),
        blocking_reason_codes=blocking_codes,
        warning_reason_codes=warning_codes,
    )


def _with_candidate_confirmation(
    actions: tuple[str, ...],
    *,
    has_asset_update_candidates: bool,
) -> tuple[str, ...]:
    if not has_asset_update_candidates or ACTION_CONFIRM_ASSET_UPDATE in actions:
        return actions
    return (*actions, ACTION_CONFIRM_ASSET_UPDATE)


def _fail_closed_actions(existing: tuple[str, ...]) -> tuple[str, ...]:
    non_terminal = tuple(action for action in existing if action != ACTION_GENERATE_NEXT_QUESTION)
    return _unique_actions((ACTION_RETRY_SAME_QUESTION, ACTION_CONTINUE_SAME_QUESTION, *non_terminal))


def _has_unresolved_answer_points(value: FeedbackNextActionInput) -> bool:
    return bool(value.missing_points or value.weak_points or value.contradicted_points)


def _unique_actions(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = _clean(value, max_chars=160)
        if text and text not in result:
            result.append(text)
        if len(result) >= 20:
            break
    return tuple(result)


def _clean(value: object, *, max_chars: int = 240) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text
