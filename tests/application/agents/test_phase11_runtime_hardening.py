from __future__ import annotations

import pytest

import app.application.agents.handoff as agent_handoff
import app.application.agents.runtime as agent_runtime
from app.application.agents.contracts import (
    AgentExecutionResult,
    AgentExecutionTrace,
    AgentRuntimeLoopPolicy,
    CrossAgentHandoffRoute,
    HandoffContract,
    P8_REQUIRED_RUNTIME_STOP_CONDITIONS,
)
from app.application.ai_runtime.contracts import RuntimeValidationError


def test_cross_agent_handoff_fails_closed_on_missing_refs_invalid_type_and_mismatch() -> None:
    route = _route()
    contract = _contract(route)

    with pytest.raises(ValueError, match="trace refs"):
        agent_handoff.build_agent_handoff_plan(
            source_result=_source_result(descriptor_overrides={"trace_refs": ()}),
            handoff_contract=contract,
            target_plan_id="plan_missing_trace",
            target_agent_id="polish_feedback_agent",
            owner_id="owner_1",
            objective="reject missing trace refs",
            runtime_loop_policy=_runtime_loop_policy(),
        )

    invalid_type = _source_result(descriptor_overrides={"candidate_type": "feedback_candidate"})
    with pytest.raises(ValueError, match="candidate type"):
        agent_handoff.build_agent_handoff_plan(
            source_result=invalid_type,
            handoff_contract=contract,
            target_plan_id="plan_invalid_type",
            target_agent_id="polish_feedback_agent",
            owner_id="owner_1",
            objective="reject invalid candidate type",
            runtime_loop_policy=_runtime_loop_policy(),
        )

    source_mismatch = _source_result(source_agent_id="polish_feedback_agent")
    with pytest.raises(ValueError, match="source_agent_id"):
        agent_handoff.build_agent_handoff_plan(
            source_result=source_mismatch,
            handoff_contract=contract,
            target_plan_id="plan_source_mismatch",
            target_agent_id="polish_feedback_agent",
            owner_id="owner_1",
            objective="reject source mismatch",
            runtime_loop_policy=_runtime_loop_policy(),
        )

    with pytest.raises(ValueError, match="target_agent_id"):
        agent_handoff.build_agent_handoff_plan(
            source_result=_source_result(),
            handoff_contract=contract,
            target_plan_id="plan_target_mismatch",
            target_agent_id="resume_analysis_agent",
            owner_id="owner_1",
            objective="reject target mismatch",
            runtime_loop_policy=_runtime_loop_policy(),
        )


def test_cross_agent_handoff_rejects_formal_refs_unsafe_metadata_and_preserves_refs_only() -> None:
    route = _route()
    contract = _contract(route)

    with pytest.raises(ValueError, match="unsafe metadata"):
        agent_handoff.build_agent_handoff_plan(
            source_result=_source_result(descriptor_overrides={"formal_refs": ("formal_ref_1",)}),
            handoff_contract=contract,
            target_plan_id="plan_formal_refs",
            target_agent_id="polish_feedback_agent",
            owner_id="owner_1",
            objective="reject formal refs",
            runtime_loop_policy=_runtime_loop_policy(),
        )

    with pytest.raises(ValueError, match="unsafe metadata"):
        agent_handoff.build_agent_handoff_plan(
            source_result=_source_result(),
            handoff_contract=contract,
            target_plan_id="plan_raw_metadata",
            target_agent_id="polish_feedback_agent",
            owner_id="owner_1",
            objective="reject raw metadata",
            runtime_loop_policy=_runtime_loop_policy(),
            metadata={"raw_prompt": "hidden", "handoff_refs": ("handoff_ref_ok",)},
        )

    plan = agent_handoff.build_agent_handoff_plan(
        source_result=_source_result(),
        handoff_contract=contract,
        target_plan_id="plan_refs_only",
        target_agent_id="polish_feedback_agent",
        owner_id="owner_1",
        objective="preserve refs only",
        runtime_loop_policy=_runtime_loop_policy(),
        metadata={
            "plan_refs": ("plan_ref_1",),
            "note": "drop this non-ref prose",
            "owner_id": "owner_1",
        },
    )

    assert plan.input_refs == ("handoff_question_candidate_ref_1",)
    assert plan.metadata["plan_refs"] == ("plan_ref_1",)
    assert plan.metadata["owner_id"] == "owner_1"
    assert "note" not in plan.metadata
    assert plan.metadata["handoff_envelope"]["trace_refs"] == ("trace_ref_candidate",)
    assert plan.metadata["handoff_envelope"]["validation_refs"] == (
        "validation_ref_contract",
        "validation_ref_candidate",
    )


@pytest.mark.parametrize("missing_key", ("checkpoint_ref", "base_version", "idempotency_key"))
def test_cross_agent_resume_validation_requires_checkpoint_base_version_and_idempotency(
    missing_key: str,
) -> None:
    payload = _resume_payload()
    payload.pop(missing_key)

    with pytest.raises(ValueError, match=missing_key):
        agent_runtime.validate_cross_agent_resume_payload(
            payload,
            expected_owner_id="owner_1",
            interrupt_ref="interrupt_ref_1",
        )


def test_cross_agent_resume_validation_rejects_owner_mismatch_unsupported_action_and_raw_payload() -> None:
    with pytest.raises(ValueError, match="owner scope"):
        agent_runtime.validate_cross_agent_resume_payload(
            {**_resume_payload(), "owner_id": "owner_2"},
            expected_owner_id="owner_1",
            interrupt_ref="interrupt_ref_1",
        )
    with pytest.raises(ValueError, match="unsupported"):
        agent_runtime.validate_cross_agent_resume_payload(
            {**_resume_payload(), "resume_action": "write_formal_asset"},
            expected_owner_id="owner_1",
            interrupt_ref="interrupt_ref_1",
        )
    with pytest.raises(ValueError, match="unsafe metadata"):
        agent_runtime.validate_cross_agent_resume_payload(
            {**_resume_payload(), "full_resume": "hidden body"},
            expected_owner_id="owner_1",
            interrupt_ref="interrupt_ref_1",
        )


def test_cross_agent_replay_validation_blocks_non_read_only_formal_write_and_side_effects() -> None:
    assert agent_runtime.validate_cross_agent_replay_metadata(_replay_metadata())["read_only"] is True

    with pytest.raises(ValueError, match="read_only"):
        agent_runtime.validate_cross_agent_replay_metadata({**_replay_metadata(), "read_only": False})
    with pytest.raises(ValueError, match="formal_write_blocked"):
        agent_runtime.validate_cross_agent_replay_metadata(
            {**_replay_metadata(), "formal_write_blocked": False}
        )
    with pytest.raises(ValueError, match="providers"):
        agent_runtime.validate_cross_agent_replay_metadata({**_replay_metadata(), "provider_calls": 1})
    with pytest.raises(ValueError, match="unsafe metadata"):
        agent_runtime.validate_cross_agent_replay_metadata(
            {**_replay_metadata(), "formal_refs": ("formal_ref_1",)}
        )


def test_cross_agent_trace_timeline_mapping_requires_refs_only_and_keeps_refs_separate() -> None:
    mapped = agent_runtime.map_cross_agent_trace_timeline_refs(
        {
            "status": "requires_user_confirmation",
            "plan_refs": ("plan_ref_1",),
            "handoff_refs": ("handoff_ref_1",),
            "validation_refs": ("validation_ref_1",),
            "candidate_refs": ("question_candidate_ref_1",),
            "policy_refs": ("policy_ref_1",),
            "tool_refs": ("tool_ref_1",),
            "low_confidence_flags": ("source_gap",),
            "interrupt_refs": ("interrupt_ref_1",),
            "output_refs": ("feedback_candidate_ref_1",),
        }
    )

    assert mapped["plan_refs"] == ("plan_ref_1",)
    assert mapped["handoff_refs"] == ("handoff_ref_1",)
    assert mapped["validation_refs"] == ("validation_ref_1",)
    assert mapped["candidate_refs"] == ("question_candidate_ref_1",)
    assert mapped["output_refs"] == ("feedback_candidate_ref_1",)

    with pytest.raises(ValueError, match="collapsed"):
        agent_runtime.map_cross_agent_trace_timeline_refs(
            {
                "plan_refs": ("plan_ref_1",),
                "handoff_refs": ("handoff_ref_1",),
                "validation_refs": ("validation_ref_1",),
                "candidate_refs": ("question_candidate_ref_1",),
                "output_refs": ("validation_ref_1",),
            }
        )
    with pytest.raises(ValueError, match="unsafe metadata"):
        agent_runtime.map_cross_agent_trace_timeline_refs(
            {
                "plan_refs": ("plan_ref_1",),
                "handoff_refs": ("handoff_ref_1",),
                "validation_refs": ("validation_ref_1",),
                "candidate_refs": ("question_candidate_ref_1",),
                "raw_provider_payload": {"hidden": True},
            }
        )


def test_cross_agent_hitl_triggers_block_or_interrupt_and_reject_success_like_failures() -> None:
    for trigger_type in ("formal_write_requested", "asset_conflict"):
        with pytest.raises(ValueError, match="interrupt or block"):
            agent_runtime.validate_cross_agent_hitl_trigger(
                trigger_type=trigger_type,
                status="succeeded",
                metadata={"interrupt_refs": ("interrupt_ref_1",)},
            )
        validated = agent_runtime.validate_cross_agent_hitl_trigger(
            trigger_type=trigger_type,
            status="requires_user_confirmation",
            metadata={"interrupt_refs": ("interrupt_ref_1",), "handoff_refs": ("handoff_ref_1",)},
        )
        assert validated["interrupt_refs"] == ("interrupt_ref_1",)

    assert agent_runtime.validate_cross_agent_hitl_trigger(
        trigger_type="low_confidence",
        status="requires_user_confirmation",
        metadata={"low_confidence_flags": ("source_gap",), "interrupt_refs": ("interrupt_ref_1",)},
    )
    with pytest.raises(ValueError, match="trace-visible"):
        agent_runtime.validate_cross_agent_hitl_trigger(
            trigger_type="low_confidence",
            status="requires_user_confirmation",
            metadata={"interrupt_refs": ("interrupt_ref_1",)},
        )
    with pytest.raises(RuntimeValidationError, match="success-like"):
        agent_runtime.validate_cross_agent_hitl_trigger(
            trigger_type="validation_failed_partial_result",
            status="generated",
            metadata={"failure_reason": "validation_failed"},
        )
    with pytest.raises(ValueError, match="success"):
        agent_runtime.validate_cross_agent_hitl_trigger(
            trigger_type="validation_failed_partial_result",
            status="succeeded",
            metadata={},
        )


def _source_result(
    *,
    source_agent_id: str = "polish_question_agent",
    descriptor_overrides: dict[str, object] | None = None,
) -> AgentExecutionResult:
    descriptor = {
        "candidate_ref": "question_candidate_ref_1",
        "candidate_type": "question_candidate",
        "payload_schema_id": "schema.question_candidate.v1",
        "trace_refs": ("trace_ref_candidate",),
        "validation_refs": ("validation_ref_candidate",),
        **dict(descriptor_overrides or {}),
    }
    return AgentExecutionResult(
        run_id="arun_source",
        status="succeeded",
        candidate_refs=("question_candidate_ref_1",),
        trace=AgentExecutionTrace(
            trace_id="trace_arun_source",
            run_id="arun_source",
            agent_id=source_agent_id,
        ),
        metadata={"handoff_candidate_descriptors": (descriptor,)},
    )


def _route() -> CrossAgentHandoffRoute:
    return CrossAgentHandoffRoute(
        route_id="route.question_to_feedback.v1",
        source_agent_id="polish_question_agent",
        target_agent_id="polish_feedback_agent",
        payload_schema_id="schema.question_candidate.v1",
        side_effect_policy="candidate_write",
        allowed_candidate_types=("question_candidate",),
        required_trace_refs=("trace_ref_candidate",),
        required_validation_refs=("validation_ref_contract", "validation_ref_candidate"),
        user_confirmation_required_when=(
            "formal_write_requested",
            "asset_conflict",
            "low_confidence",
            "ambiguous_ownership",
            "validation_failed_partial_result",
        ),
    )


def _contract(route: CrossAgentHandoffRoute) -> HandoffContract:
    return HandoffContract(
        contract_id="handoff.question_to_feedback.v1",
        candidate_ref_types=("question_candidate",),
        payload_schema_id="schema.question_candidate.v1",
        validation_refs=("validation_ref_contract",),
        side_effect_key="side_effect_question_to_feedback",
        idempotency_key="idem_question_to_feedback",
        cross_agent_route=route,
    )


def _runtime_loop_policy() -> AgentRuntimeLoopPolicy:
    return AgentRuntimeLoopPolicy(
        max_steps=3,
        max_retries=1,
        timeout_seconds=5,
        stop_conditions=P8_REQUIRED_RUNTIME_STOP_CONDITIONS,
        allowed_tools=("question_drafting",),
        allowed_callers=("polish_question_agent",),
        side_effect_policy="candidate_write",
    )


def _resume_payload() -> dict[str, object]:
    return {
        "cross_agent_resume": True,
        "checkpoint_ref": "checkpoint_ref_1",
        "base_version": 1,
        "idempotency_key": "idem_resume_1",
        "owner_id": "owner_1",
        "interrupt_ref": "interrupt_ref_1",
        "resume_action": "continue",
    }


def _replay_metadata() -> dict[str, object]:
    return {
        "cross_agent_replay": True,
        "read_only": True,
        "formal_write_blocked": True,
        "provider_calls": 0,
        "external_tool_calls": 0,
        "repository_writes": 0,
        "db_business_writes": 0,
        "formal_business_writes": 0,
    }
