from __future__ import annotations

import inspect
from dataclasses import fields, is_dataclass

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
