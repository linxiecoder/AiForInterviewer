from __future__ import annotations

import inspect
from dataclasses import fields, is_dataclass

import pytest

import app.application.agents.contracts as agent_contracts
import app.application.agents.handoff as agent_handoff
from app.application.agents.contracts import ToolDefinition
from app.application.ai_runtime.contracts import (
    AgentCandidatePayload,
    AgentCommandEnvelope,
    AgentGraphRunner,
    AgentRunContext,
    AgentRunResult,
    AgentRunStatus,
    AgentTaskStatusRef,
    AgentRunTimelinePage,
    AgentTimelineEvent,
    GraphDisabledError,
    OwnerScopeError,
    RuntimeConflictError,
    RuntimePolicyError,
    RuntimeUnavailableError,
    RuntimeValidationError,
)
from app.application.ai_runtime.handoff import AgentPersistenceHandoff, HandoffRequest
from app.application.ai_runtime.llm_trace import LlmBeforeCallTracePolicy, LlmPayloadCapturePolicy, LlmTraceContext
from app.application.ai_runtime.registry import AgentGraphRegistry
from app.application.ai_runtime.side_effect_guard import AgentSideEffectGuard
from app.application.ai_runtime.trace_bridge import AgentTraceBridge


FORBIDDEN_TERMS = (
    "lang" + "graph",
    "lang" + "chain",
    "State" + "Graph",
    "Compiled" + "Graph",
    "Agent" + "State",
    "checkpoint_" + "payload",
    "raw" + "_prompt",
    "raw" + "_completion",
    "provider_" + "payload",
)
RAW_KEY = "raw" + "_prompt"
PROVIDER_KEY = "provider_" + "payload"
FULL_ASSET_BODY_KEY = "full" + "_asset" + "_body"


def test_contract_dtos_are_project_owned_dataclasses_without_runtime_internals() -> None:
    dto_types = (
        AgentRunContext,
        AgentCommandEnvelope,
        AgentCandidatePayload,
        AgentRunResult,
        AgentRunStatus,
        AgentTaskStatusRef,
        AgentRunTimelinePage,
        AgentTimelineEvent,
    )

    for dto_type in dto_types:
        assert is_dataclass(dto_type)
        field_text = " ".join(field.name for field in fields(dto_type))
        annotation_text = " ".join(str(field.type) for field in fields(dto_type))
        combined = f"{dto_type.__name__} {field_text} {annotation_text}"
        for forbidden in FORBIDDEN_TERMS:
            assert forbidden not in combined


def test_runner_protocol_exposes_required_methods_without_concrete_runtime_types() -> None:
    for method_name in ("start", "resume", "replay", "get_status", "get_timeline", "cancel"):
        method = getattr(AgentGraphRunner, method_name)
        signature_text = str(inspect.signature(method))
        assert "self" in signature_text
        for forbidden in FORBIDDEN_TERMS:
            assert forbidden not in signature_text


def test_runtime_errors_share_runtime_error_base() -> None:
    for error_type in (
        GraphDisabledError,
        OwnerScopeError,
        RuntimeValidationError,
        RuntimeConflictError,
        RuntimePolicyError,
        RuntimeUnavailableError,
    ):
        assert issubclass(error_type, RuntimeError)


def test_agent_candidate_payload_rejects_raw_payload_and_keeps_sanitized_candidate() -> None:
    payload = AgentCandidatePayload(
        candidate_ref="question_candidate_ref_1",
        candidate_type="polish_question_candidate",
        payload_schema_id="polish_question_candidate.v1",
        payload={"question_text": "请介绍支付链路一致性经验", "nested": {"safe": "ok"}},
        trace_refs=("trace_1",),
        validation_refs=("validation_1",),
        low_confidence_flags=("limited_context",),
    )

    assert payload.status == "accepted"
    assert payload.payload == {"question_text": "请介绍支付链路一致性经验", "nested": {"safe": "ok"}}
    assert payload.trace_refs == ("trace_1",)
    try:
        AgentCandidatePayload(
            candidate_ref="question_candidate_ref_2",
            candidate_type="polish_question_candidate",
            payload_schema_id="polish_question_candidate.v1",
            payload={RAW_KEY: "hidden prompt"},
        )
    except RuntimePolicyError as exc:
        assert "candidate payload contains sensitive content" in str(exc)
    else:
        raise AssertionError("raw candidate payload was accepted")
    try:
        AgentCandidatePayload(
            candidate_ref="asset_update_candidate_ref_1",
            candidate_type="asset_update_candidate",
            payload_schema_id="polish_asset_update_candidate.v1",
            payload={FULL_ASSET_BODY_KEY: {"title": "must stay out of runtime handoff"}},
        )
    except RuntimePolicyError as exc:
        assert "candidate payload contains sensitive content" in str(exc)
    else:
        raise AssertionError("raw asset body candidate payload was accepted")


def test_agent_run_result_and_task_status_ref_carry_candidate_payloads() -> None:
    payload = AgentCandidatePayload(
        candidate_ref="question_candidate_ref_1",
        candidate_type="polish_question_candidate",
        payload_schema_id="polish_question_candidate.v1",
        payload={"question_text": "请介绍支付链路一致性经验"},
    )

    result = AgentRunResult(
        run_id="arun_1",
        status="succeeded",
        output_refs=("question_candidate_ref_1",),
        candidate_payloads=(payload,),
    )
    status_ref = AgentTaskStatusRef(
        ai_task_id="aitask_1",
        agent_run_id=result.run_id,
        status=result.status,
        candidate_refs=result.output_refs,
        candidate_payloads=result.candidate_payloads,
    )

    assert result.candidate_payloads == (payload,)
    assert status_ref.candidate_payloads == (payload,)
    assert status_ref.candidate_refs == ("question_candidate_ref_1",)


def test_registry_descriptors_are_default_off_and_reject_unsupported_outputs() -> None:
    registry = AgentGraphRegistry.default()
    polish = registry.get_graph_descriptor("polish_question_generation")
    job_match = registry.get_graph_descriptor("job_match_analysis")
    resume = registry.get_graph_descriptor("resume_analysis")

    assert polish.default_enabled is False
    assert polish.lifecycle_status == "active"
    assert job_match.lifecycle_status == "deferred"
    assert resume.lifecycle_status == "deferred"
    assert registry.validate_requested_outputs("polish_question_generation", ("candidate_refs",)) == (
        "candidate_refs",
    )
    try:
        registry.validate_requested_outputs("polish_question_generation", ("formal_question",))
    except RuntimeValidationError as exc:
        assert "unsupported output" in str(exc)
    else:
        raise AssertionError("unsupported output was accepted")
    assert registry.resolve_resume_schema_descriptor("user_confirmation")["schema_id"].startswith("agent.resume.")


def test_trace_bridge_records_sanitized_refs_and_rejects_sensitive_llm_summary() -> None:
    bridge = AgentTraceBridge()

    started = bridge.record_run_started(
        owner_id="owner_1",
        run_id="arun_1",
        ai_task_id="aitask_1",
        graph_name="polish_question_graph",
    )
    checkpoint = bridge.record_checkpoint_ref(
        owner_id="owner_1",
        run_id="arun_1",
        checkpoint_ref="ackpt_1",
        metadata={
            "checkpoint_namespace": "agent_runtime",
            "thread_id": "thread_1",
            "state_hash": "sha256:demo",
        },
    )

    assert started.trace_ref_id.startswith("atrace_")
    assert checkpoint.metadata["checkpoint_id"] == "ackpt_1"
    assert checkpoint.metadata["checkpoint_namespace"] == "agent_runtime"
    assert checkpoint.metadata["state_hash"] == "sha256:demo"
    assert "payload" not in checkpoint.metadata
    try:
        bridge.record_llm_call(
            owner_id="owner_1",
            run_id="arun_1",
            llm_call_id="llmc_1",
            summary={PROVIDER_KEY: {"secret": "hidden"}},
        )
    except RuntimePolicyError as exc:
        assert "sensitive" in str(exc)
    else:
        raise AssertionError("sensitive LLM summary was accepted")


def test_trace_bridge_rejects_unknown_non_dto_runtime_statuses() -> None:
    bridge = AgentTraceBridge()

    failed = bridge.record_node_finished(
        owner_id="owner_1",
        run_id="arun_1",
        node_name="validator",
        status="validation_failed",
        output_refs=("validation_ref_1",),
    )

    assert failed.metadata["status"] == "validation_failed"
    try:
        bridge.record_node_finished(
            owner_id="owner_1",
            run_id="arun_1",
            node_name="validator",
            status="doneish",
            output_refs=("candidate_ref_1",),
        )
    except RuntimeValidationError as exc:
        assert "unknown runtime status" in str(exc)
    else:
        raise AssertionError("unknown node status was accepted")
    try:
        bridge.record_run_finished(
            owner_id="owner_1",
            run_id="arun_1",
            status="write_enabled_replay",
            result_refs=("candidate_ref_1",),
        )
    except RuntimeValidationError as exc:
        assert "unknown runtime status" in str(exc)
    else:
        raise AssertionError("unknown run status was accepted")


def test_side_effect_guard_blocks_sensitive_payloads_unconfirmed_formal_write_and_replay_write() -> None:
    guard = AgentSideEffectGuard()

    assert guard.assert_no_sensitive_payload({"safe": "ok"}) == {"safe": "ok"}
    try:
        guard.assert_no_sensitive_payload({RAW_KEY: "hidden"})
    except RuntimePolicyError:
        pass
    else:
        raise AssertionError("sensitive payload was accepted")

    try:
        guard.authorize_handoff(target_type="question", user_confirmed=False, replay_mode=False)
    except RuntimePolicyError as exc:
        assert "confirmation" in str(exc)
    else:
        raise AssertionError("unconfirmed formal write was accepted")

    try:
        guard.authorize_handoff(target_type="candidate", user_confirmed=True, replay_mode=True)
    except RuntimePolicyError as exc:
        assert "replay" in str(exc)
    else:
        raise AssertionError("replay write was accepted")


def test_runtime_loop_policy_fails_closed_and_guard_validates_tool_contract() -> None:
    policy_cls = getattr(agent_contracts, "AgentRuntimeLoopPolicy", None)
    assert policy_cls is not None

    with pytest.raises(ValueError, match="max_steps"):
        policy_cls(
            max_steps=0,
            max_retries=1,
            timeout_seconds=5,
            stop_conditions=("timeout",),
            allowed_tools=("evidence_selection",),
            allowed_callers=("polish_question_agent",),
            side_effect_policy="candidate_write",
        )
    with pytest.raises(ValueError, match="stop_conditions"):
        policy_cls(
            max_steps=3,
            max_retries=1,
            timeout_seconds=5,
            stop_conditions=(),
            allowed_tools=("evidence_selection",),
            allowed_callers=("polish_question_agent",),
            side_effect_policy="candidate_write",
        )
    with pytest.raises(ValueError, match="missing required stop_conditions"):
        policy_cls(
            max_steps=3,
            max_retries=1,
            timeout_seconds=5,
            stop_conditions=("timeout", "tool_not_allowed", "formal_write_requested"),
            allowed_tools=("evidence_selection",),
            allowed_callers=("polish_question_agent",),
            side_effect_policy="candidate_write",
        )

    policy = policy_cls(
        max_steps=3,
        max_retries=1,
        timeout_seconds=5,
        stop_conditions=agent_contracts.P8_REQUIRED_RUNTIME_STOP_CONDITIONS,
        allowed_tools=("evidence_selection",),
        allowed_callers=("polish_question_agent",),
        side_effect_policy="candidate_write",
    )
    tool = ToolDefinition(
        tool_id="tool_evidence_selection",
        tool_name="evidence_selection",
        input_schema_id="schema.input.refs",
        output_schema_id="schema.output.candidate.refs",
        permission_scope="candidate_generation",
        owner_scope="same_owner",
        side_effect_policy="candidate_write",
        timeout_seconds=5,
        retry_policy="bounded_once",
        allowed_callers=("polish_question_agent",),
        forbidden_data=(RAW_KEY, PROVIDER_KEY, "raw_completion", "api_key"),
        trace_events=("tool_started", "tool_finished"),
    )
    guard = AgentSideEffectGuard()

    assert guard.authorize_tool_call(
        owner_id="owner_1",
        tool_name="evidence_selection",
        input_refs=("session_ref_1",),
        tool=tool,
        caller_id="polish_question_agent",
        permission_scope="candidate_generation",
        owner_scope="same_owner",
        side_effect_policy=policy.side_effect_policy,
        payload={"candidate_ref": "candidate_ref_1"},
    )
    with pytest.raises(RuntimePolicyError, match="caller"):
        guard.authorize_tool_call(
            owner_id="owner_1",
            tool_name="evidence_selection",
            input_refs=("session_ref_1",),
            tool=tool,
            caller_id="feedback_agent",
            permission_scope="candidate_generation",
            owner_scope="same_owner",
            side_effect_policy=policy.side_effect_policy,
        )
    with pytest.raises(RuntimePolicyError, match="side_effect_policy"):
        guard.authorize_tool_call(
            owner_id="owner_1",
            tool_name="evidence_selection",
            input_refs=("session_ref_1",),
            tool=tool,
            caller_id="polish_question_agent",
            permission_scope="candidate_generation",
            owner_scope="same_owner",
            side_effect_policy="formal_write",
        )
    with pytest.raises(RuntimePolicyError, match="owner_scope"):
        guard.authorize_tool_call(
            owner_id="owner_1",
            tool_name="evidence_selection",
            input_refs=("session_ref_1",),
            tool=tool,
            caller_id="polish_question_agent",
            permission_scope="candidate_generation",
            owner_scope="cross_owner",
            side_effect_policy=policy.side_effect_policy,
        )
    with pytest.raises(RuntimePolicyError, match="forbidden data"):
        guard.authorize_tool_call(
            owner_id="owner_1",
            tool_name="evidence_selection",
            input_refs=("session_ref_1",),
            tool=tool,
            caller_id="polish_question_agent",
            permission_scope="candidate_generation",
            owner_scope="same_owner",
            side_effect_policy=policy.side_effect_policy,
            payload={RAW_KEY: "hidden"},
        )
    with pytest.raises(RuntimePolicyError, match="ToolDefinition"):
        guard.authorize_tool_call(
            owner_id="owner_1",
            tool_name="evidence_selection",
            input_refs=("session_ref_1",),
            caller_id="polish_question_agent",
            permission_scope="candidate_generation",
            owner_scope="same_owner",
            side_effect_policy=policy.side_effect_policy,
            payload={"candidate_ref": "candidate_ref_1"},
        )


def test_typed_handoff_envelope_and_trace_keep_phase8_refs_without_raw_metadata() -> None:
    envelope_cls = getattr(agent_handoff, "AgentHandoffEnvelope", None)
    assert envelope_cls is not None

    handoff = envelope_cls(
        candidate_ref="candidate_ref_1",
        candidate_type="question_candidate",
        payload_schema_id="schema.question_candidate.v1",
        trace_refs=("trace_1",),
        validation_refs=("validation_1",),
        side_effect_key="side_effect_1",
        idempotency_key="idem_1",
        metadata={
            RAW_KEY: "hidden",
            FULL_ASSET_BODY_KEY: {"body": "hidden"},
            "safe": {
                "nested": "ok",
                RAW_KEY: "hidden",
                "items": [{"api_key": "secret", "allowed": "ref_ok"}],
            },
            "list": [{"full_asset_body": "hidden", "kept": "value"}],
        },
    )
    trace = agent_contracts.AgentExecutionTrace(
        trace_id="trace_1",
        run_id="arun_1",
        agent_id="polish_question_agent",
        agent_version="v1",
        ai_task_id="aitask_1",
        input_refs=("session_1",),
        candidate_refs=(handoff.candidate_ref,),
        validation_refs=handoff.validation_refs,
        handoff_refs=(handoff.handoff_ref,),
        low_confidence_flags=("source_gap",),
        failure_reason="validation_failed",
        fallback_reason="provider_disabled",
        metadata={
            PROVIDER_KEY: {"token": "secret"},
            "safe": {
                "provider": {PROVIDER_KEY: {"token": "secret"}, "kept_ref": "trace_ref_ok"},
                "items": [{"full_resume": "hidden", "kept": "value"}],
            },
        },
    )

    assert handoff.candidate_type == "question_candidate"
    assert handoff.payload_schema_id == "schema.question_candidate.v1"
    assert handoff.trace_refs == ("trace_1",)
    assert handoff.validation_refs == ("validation_1",)
    assert handoff.metadata == {
        "safe": {"nested": "ok", "items": [{"allowed": "ref_ok"}]},
        "list": [{"kept": "value"}],
    }
    assert trace.agent_version == "v1"
    assert trace.ai_task_id == "aitask_1"
    assert trace.low_confidence_flags == ("source_gap",)
    assert trace.failure_reason == "validation_failed"
    assert trace.fallback_reason == "provider_disabled"
    assert trace.metadata == {
        "safe": {"provider": {"kept_ref": "trace_ref_ok"}, "items": [{"kept": "value"}]}
    }


def test_checkpoint_metadata_uses_allowlist_and_rejects_payload_keys() -> None:
    guard = AgentSideEffectGuard()
    allowed = guard.verify_checkpoint_write(
        {
            "checkpoint_namespace": "agent_runtime",
            "thread_id": "thread_1",
            "checkpoint_id": "ackpt_1",
            "graph_name": "polish_question_graph",
            "graph_version": "pr3-contract",
            "node_name": "candidate_review",
            "version": "v1",
            "state_hash": "sha256:state",
            "created_at": "2026-05-24T00:00:00Z",
            "retention_ref": "retention_1",
        }
    )

    assert allowed["checkpoint_id"] == "ackpt_1"
    for forbidden_metadata in (
        {RAW_KEY: "hidden"},
        {"business_formal_object_payload": {"question": "body"}},
        {"checkpoint_" + "payload": {"state": "hidden"}},
    ):
        try:
            guard.verify_checkpoint_write(forbidden_metadata)
        except RuntimePolicyError:
            pass
        else:
            raise AssertionError("checkpoint metadata payload key was accepted")


def test_handoff_formal_write_stubs_fail_closed() -> None:
    handoff = AgentPersistenceHandoff()
    request = HandoffRequest(
        owner_id="owner_1",
        run_id="arun_1",
        target_type="question",
        candidate_refs=("candidate_1",),
        trace_refs=("trace_1",),
        validation_result_ref="validation_1",
        side_effect_key="side_effect_1",
    )

    plan = handoff.prepare_handoff(request)

    assert plan.formal_refs == ()
    for method_name in (
        "write_question_result",
        "write_feedback_result",
        "write_report_result",
        "write_review_result",
        "write_candidate_result",
        "finalize_after_confirmation",
    ):
        method = getattr(handoff, method_name)
        try:
            method(plan)
        except RuntimePolicyError as exc:
            assert "PR5+" in str(exc) or "later PR" in str(exc)
        else:
            raise AssertionError(f"{method_name} did not fail closed")


def test_llm_trace_policy_is_default_off_and_production_debug_capture_fails_closed() -> None:
    context = LlmTraceContext(
        owner_id="owner_1",
        ai_task_id="aitask_1",
        agent_run_id="arun_1",
        agent_node_run_id="anode_1",
        contract_ids=("P-POLISH-001",),
        replay_mode="production_resume",
    )

    policy = LlmPayloadCapturePolicy.resolve(
        settings={"debug_raw_enabled": True},
        context=context,
        environment="production",
    )

    assert policy.raw_enabled is False
    assert policy.sanitized_summary_required is True
    try:
        policy.capture_debug_raw_ref("object_ref")
    except RuntimePolicyError as exc:
        assert "disabled" in str(exc)
    else:
        raise AssertionError("debug capture was accepted")


def test_llm_before_call_trace_policy_requires_successful_trace_write_before_provider_invocation() -> None:
    policy = LlmBeforeCallTracePolicy.default()

    assert policy.before_call_trace_required is True
    assert policy.fail_closed_on_trace_write_failure is True
    try:
        policy.authorize_provider_invocation(llm_call_id="")
    except RuntimePolicyError as exc:
        assert "trace write" in str(exc)
    else:
        raise AssertionError("provider invocation was accepted without before-call trace")

    assert policy.authorize_provider_invocation(llm_call_id="llmc_1") is True
