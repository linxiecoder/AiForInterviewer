"""AI Runtime persistence handoff contract and PR3 fail-closed stubs."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.ai_runtime.contracts import RuntimePolicyError, RuntimeValidationError


@dataclass(frozen=True)
class HandoffRequest:
    owner_id: str
    run_id: str
    target_type: str
    candidate_refs: tuple[str, ...] = field(default_factory=tuple)
    trace_refs: tuple[str, ...] = field(default_factory=tuple)
    validation_result_ref: str | None = None
    side_effect_key: str | None = None


@dataclass(frozen=True)
class HandoffPlan:
    owner_id: str
    run_id: str
    target_type: str
    candidate_refs: tuple[str, ...]
    trace_refs: tuple[str, ...]
    validation_result_ref: str
    side_effect_key: str
    formal_refs: tuple[str, ...] = field(default_factory=tuple)


class AgentPersistenceHandoff:
    def prepare_handoff(self, request: HandoffRequest) -> HandoffPlan:
        if not request.trace_refs:
            raise RuntimeValidationError("handoff requires trace refs")
        if not request.validation_result_ref:
            raise RuntimeValidationError("handoff requires validation result ref")
        if not request.side_effect_key:
            raise RuntimeValidationError("handoff requires side effect key")
        return HandoffPlan(
            owner_id=request.owner_id,
            run_id=request.run_id,
            target_type=request.target_type,
            candidate_refs=request.candidate_refs,
            trace_refs=request.trace_refs,
            validation_result_ref=request.validation_result_ref,
            side_effect_key=request.side_effect_key,
            formal_refs=(),
        )

    def write_question_result(self, plan: HandoffPlan) -> None:
        self._fail_closed(plan)

    def write_feedback_result(self, plan: HandoffPlan) -> None:
        self._fail_closed(plan)

    def write_report_result(self, plan: HandoffPlan) -> None:
        self._fail_closed(plan)

    def write_review_result(self, plan: HandoffPlan) -> None:
        self._fail_closed(plan)

    def write_candidate_result(self, plan: HandoffPlan) -> None:
        self._fail_closed(plan)

    def finalize_after_confirmation(self, plan: HandoffPlan) -> None:
        self._fail_closed(plan)

    def _fail_closed(self, plan: HandoffPlan) -> None:
        raise RuntimePolicyError(f"{plan.target_type} formal write is PR5+ or later PR only")

