from __future__ import annotations

import json
import logging
from dataclasses import asdict

import pytest

import app.application.ai_runtime.business_graphs.polish_question_graph as question_graph
from app.application.ai_runtime.business_graphs.polish_question_graph import (
    MAX_AGENT_STEPS,
    MAX_RETRIES,
    POLISH_QUESTION_AGENT_PHASES,
    QUESTION_AGENT_BACKOFF_SECONDS,
    QUESTION_AGENT_TIMEOUT_SECONDS,
    POLISH_QUESTION_GRAPH_FLAG,
    POLISH_QUESTION_GRAPH_NAME,
    POLISH_QUESTION_GRAPH_VERSION,
    TOOL_SCHEMAS,
    PolishQuestionAgentConfig,
    build_polish_question_candidate_readonly,
    execute_polish_question_agent,
    run_polish_question_agent,
)
from app.application.ai_runtime.contracts import (
    AgentCandidatePayload,
    AgentCommandEnvelope,
    AgentRunContext,
    AgentRunResult,
    RuntimeValidationError,
    contains_sensitive_payload,
)
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.infrastructure.observability.logging import BackendLogSettings, LogUtil
from app.infrastructure.ai_runtime.langgraph.in_memory_runtime import InMemoryLangGraphRuntime
from app.infrastructure.ai_runtime.langgraph.polish_question_runtime import PolishQuestionGraphRuntime
from app.infrastructure.ai_runtime.langgraph import polish_question_runtime as polish_question_runtime_module


RAW_PROMPT_KEY = "raw" + "_prompt"
RAW_COMPLETION_KEY = "raw" + "_completion"
PROVIDER_PAYLOAD_KEY = "provider" + "_payload"
CHECKPOINT_PAYLOAD_KEY = "checkpoint" + "_payload"
FULL_RESUME_KEY = "full" + "_resume"
FULL_JD_KEY = "full" + "_jd"
FULL_ANSWER_KEY = "full" + "_answer"
HIDDEN_RUBRIC_KEY = "hidden" + "_rubric"
API_KEY = "api" + "_key"
FORBIDDEN_MARKERS = (
    RAW_PROMPT_KEY,
    RAW_COMPLETION_KEY,
    PROVIDER_PAYLOAD_KEY,
    CHECKPOINT_PAYLOAD_KEY,
    FULL_RESUME_KEY,
    FULL_JD_KEY,
    FULL_ANSWER_KEY,
    HIDDEN_RUBRIC_KEY,
    "token",
    "secret",
    "cookie",
    API_KEY,
)


def test_in_memory_runtime_polish_question_emits_agent_candidate_payload() -> None:
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_runtime_with_question_graph_flag())
    context = _context()

    result = runtime.start(context, context.command)

    assert result.status == "agent_orchestration_succeeded"
    assert len(result.candidate_payloads) == 1
    candidate_payload = result.candidate_payloads[0]
    assert candidate_payload.candidate_type == "polish_question_candidate"
    assert candidate_payload.payload_schema_id == "polish_question_candidate.v1"
    assert candidate_payload.status == "accepted"
    assert candidate_payload.candidate_ref in result.output_refs
    assert candidate_payload.payload["candidate_ref"] == candidate_payload.candidate_ref
    assert candidate_payload.validation_refs
    assert result.formal_refs == ()
    assert result.metadata["provider_calls"] == 0
    assert result.metadata["db_business_writes"] == 0
    assert result.metadata["formal_business_writes"] == 0
    assert result.metadata["accepted_candidate_payload"] is True


def test_in_memory_runtime_polish_question_executes_phase_tool_chain_with_provider_off_fallback() -> None:
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_runtime_with_question_graph_flag())
    context = _context()

    result = runtime.start(context, context.command)

    metadata = result.metadata
    assert metadata["provider_status"] == "disabled"
    assert metadata["fallback_reason"] == "provider_disabled_deterministic_drafting_tool"
    assert metadata["max_agent_steps"] == MAX_AGENT_STEPS
    assert metadata["max_retries"] == MAX_RETRIES
    assert metadata["timeout_seconds"] == QUESTION_AGENT_TIMEOUT_SECONDS
    assert metadata["backoff_seconds"] == QUESTION_AGENT_BACKOFF_SECONDS
    assert [item["phase"] for item in metadata["phase_results"]] == list(POLISH_QUESTION_AGENT_PHASES)
    assert {item["tool_name"] for item in metadata["tool_results"]} == {
        schema.tool_name for schema in TOOL_SCHEMAS
    }
    assert metadata["validator_result"]["passed"] is True
    assert all(item["status"] in {"succeeded", "skipped"} for item in metadata["phase_results"])
    assert any(item.get("retry_delay_seconds") == QUESTION_AGENT_BACKOFF_SECONDS for item in metadata["phase_results"])
    assert contains_sensitive_payload(metadata) is False

    candidate_metadata = result.candidate_payloads[0].payload["question_metadata"]
    assert candidate_metadata["provider_status"] == "disabled"
    assert candidate_metadata["fallback_reason"] == "provider_disabled_deterministic_drafting_tool"
    assert [item["phase"] for item in candidate_metadata["phase_results"]] == list(POLISH_QUESTION_AGENT_PHASES)
    assert {item["tool_name"] for item in candidate_metadata["tool_results"]} == {
        schema.tool_name for schema in TOOL_SCHEMAS
    }
    assert candidate_metadata["validator_result"]["passed"] is True


def test_run_polish_question_agent_accepts_provider_draft_operation_when_provider_enabled() -> None:
    calls: list[dict[str, object]] = []

    def provider_draft_operation(**kwargs):
        calls.append(kwargs)
        context = kwargs["context"]
        retrieved_context = kwargs["retrieved_context"]
        scenario = kwargs["scenario"]
        candidate = build_polish_question_candidate_readonly(
            owner_id=context.owner_id,
            run_id=context.run_id,
            ai_task_id=context.ai_task_id,
            session_ref=str(retrieved_context["session_ref"]),
            scenario=scenario,
            progress_node_ref=str(retrieved_context.get("progress_node_ref") or ""),
            context_digest=str(retrieved_context.get("context_digest") or ""),
        )
        candidate["question_metadata"] = {
            "provider_marker": "injected_provider_operation",
            "provider_status": "enabled",
        }
        return {"candidate": candidate}

    resolver = RuntimeFlagResolver(
        test_overrides={
            POLISH_QUESTION_GRAPH_FLAG: True,
            "AIFI_REAL_PROVIDER_ENABLED": True,
        }
    )

    result = run_polish_question_agent(
        context=_context(),
        command=_command(),
        flag_resolver=resolver,
        provider_draft_operation=provider_draft_operation,
    )

    assert len(calls) == 1
    assert result.status == "agent_orchestration_succeeded"
    assert result.metadata["provider_status"] == "enabled"
    assert result.metadata["provider_calls"] == 1
    assert result.candidate_payloads[0].payload["question_metadata"]["provider_marker"] == (
        "injected_provider_operation"
    )


def test_polish_question_runtime_uses_public_agent_runner_with_provider_operation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    flags = RuntimeFlagResolver(
        test_overrides={
            "AIFI_AI_RUNTIME_ENABLED": True,
            "AIFI_AI_RUNTIME_LANGGRAPH_ENABLED": True,
            POLISH_QUESTION_GRAPH_FLAG: True,
            "AIFI_REAL_PROVIDER_ENABLED": True,
        }
    )
    calls: list[dict[str, object]] = []

    def fail_direct_executor(**_: object) -> None:
        pytest.fail("PolishQuestionGraphRuntime must call run_polish_question_agent")

    def recording_runner(
        context: AgentRunContext,
        command: AgentCommandEnvelope,
        flag_resolver: RuntimeFlagResolver | None = None,
        provider_draft_operation: object | None = None,
    ) -> AgentRunResult:
        calls.append(
            {
                "context": context,
                "command": command,
                "flag_resolver": flag_resolver,
                "provider_draft_operation": provider_draft_operation,
            }
        )
        candidate_ref = "question_candidate_ref_public_runner"
        payload = AgentCandidatePayload(
            candidate_ref=candidate_ref,
            candidate_type="polish_question_candidate",
            payload_schema_id="polish_question_candidate.v1",
            payload={
                "candidate_ref": candidate_ref,
                "question_text": "请说明一次支付链路一致性治理的边界、补偿和验证指标。",
                "quality_gate": {"passed": True, "status": "accepted"},
                "low_confidence_flags": (),
                "sanitized": True,
            },
            trace_refs=("validation_ref_public_runner",),
            validation_refs=("validation_ref_public_runner",),
        )
        return AgentRunResult(
            run_id=context.run_id,
            status="agent_orchestration_succeeded",
            output_refs=("question_result_ref_public_runner", candidate_ref),
            trace_refs=("validation_ref_public_runner",),
            interrupt_refs=(),
            formal_refs=(),
            candidate_payloads=(payload,),
            metadata={
                "graph_name": POLISH_QUESTION_GRAPH_NAME,
                "graph_version": POLISH_QUESTION_GRAPH_VERSION,
                "provider_status": "enabled",
                "provider_calls": 1,
                "validator_result": {"passed": True},
                "accepted_candidate_payload": True,
                "sanitized": True,
            },
        )

    monkeypatch.setattr(
        polish_question_runtime_module,
        "execute_polish_question_agent",
        fail_direct_executor,
        raising=False,
    )
    monkeypatch.setattr(
        polish_question_runtime_module,
        "run_polish_question_agent",
        recording_runner,
        raising=False,
    )
    runtime = PolishQuestionGraphRuntime(flag_resolver=flags)
    context = _context()

    result = runtime.start(context, context.command)

    assert result.status == "agent_orchestration_succeeded"
    assert len(calls) == 1
    assert calls[0]["context"] == context
    assert calls[0]["command"] == context.command
    assert calls[0]["flag_resolver"] is flags
    assert calls[0]["provider_draft_operation"] is not None
    assert callable(calls[0]["provider_draft_operation"])


def test_in_memory_runtime_polish_question_emits_structured_agent_logs(caplog) -> None:
    LogUtil.configure(BackendLogSettings(console_enabled=True, file_enabled=False))
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_runtime_with_question_graph_flag())
    context = _context()

    with caplog.at_level(logging.INFO, logger="app.agent.runtime"):
        runtime.start(context, context.command)

    records = [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "app.agent.runtime"
    ]
    assert records
    assert any(
        record["event"] == "agent_runtime_step"
        and record["task_type"] == "polish_question_generation"
        and record["graph_name"] == POLISH_QUESTION_GRAPH_NAME
        and record["phase"] == "plan_task"
        and record["tool_name"] == "context_retrieval"
        and record["status"] == "succeeded"
        for record in records
    )
    serialized = json.dumps(records, ensure_ascii=False)
    for marker in FORBIDDEN_MARKERS:
        assert marker not in serialized


def test_execute_polish_question_agent_retries_tool_failure_with_bounded_backoff(
    monkeypatch: pytest.MonkeyPatch, caplog
) -> None:
    LogUtil.configure(BackendLogSettings(console_enabled=True, file_enabled=False))
    sleeps: list[float] = []
    calls = 0
    original = question_graph._tool_evidence_selection

    def flaky_evidence_selection(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeValidationError("temporary evidence selection failure")
        return original(**kwargs)

    monkeypatch.setattr(question_graph, "_tool_evidence_selection", flaky_evidence_selection)
    monkeypatch.setattr(question_graph, "sleep", lambda seconds: sleeps.append(seconds), raising=False)

    with caplog.at_level(logging.INFO, logger="app.agent.runtime"):
        execution = execute_polish_question_agent(
            context=_context(),
            command=_command(),
            runtime_flag_source="test_override",
            provider_enabled=False,
            provider_flag_source="test_override",
            config=PolishQuestionAgentConfig(max_retries=1, backoff_seconds=0.01),
        )

    assert execution.status == "agent_orchestration_succeeded"
    assert calls == 2
    assert sleeps == [0.01]
    evidence_tool = next(
        item for item in execution.metadata["tool_results"] if item["tool_name"] == "evidence_selection"
    )
    assert evidence_tool["attempts"] == 2
    records = [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "app.agent.runtime"
    ]
    assert any(
        record["event"] == "agent_runtime_step"
        and record["phase"] == "retrieve_context"
        and record["tool_name"] == "evidence_selection"
        and record["status"] == "retry_scheduled"
        and record["retry_delay_seconds"] == 0.01
        for record in records
    )


def test_execute_polish_question_agent_times_out_slow_tool_without_false_success(
    monkeypatch: pytest.MonkeyPatch, caplog
) -> None:
    LogUtil.configure(BackendLogSettings(console_enabled=True, file_enabled=False))
    original = question_graph._tool_context_retrieval

    def slow_context_retrieval(command):
        question_graph.sleep(0.03)
        return original(command)

    monkeypatch.setattr(question_graph, "_tool_context_retrieval", slow_context_retrieval)

    with caplog.at_level(logging.INFO, logger="app.agent.runtime"):
        with pytest.raises(RuntimeValidationError, match="context_retrieval timed out"):
            execute_polish_question_agent(
                context=_context(),
                command=_command(),
                runtime_flag_source="test_override",
                provider_enabled=False,
                provider_flag_source="test_override",
                config=PolishQuestionAgentConfig(max_retries=0, timeout_seconds=0.01),
            )

    records = [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "app.agent.runtime"
    ]
    assert any(
        record["event"] == "agent_runtime_step"
        and record["phase"] == "plan_task"
        and record["tool_name"] == "context_retrieval"
        and record["status"] == "failed"
        and record["error_type"] == "TimeoutError"
        for record in records
    )


def test_execute_polish_question_agent_fails_when_max_steps_exhausted() -> None:
    with pytest.raises(RuntimeValidationError, match="exceeded max_agent_steps"):
        execute_polish_question_agent(
            context=_context(),
            command=_command(),
            runtime_flag_source="test_override",
            provider_enabled=False,
            provider_flag_source="test_override",
            config=PolishQuestionAgentConfig(max_agent_steps=1, max_retries=0),
        )


def test_execute_polish_question_agent_repairs_validation_failure_with_bounded_transform(
    monkeypatch,
) -> None:
    original_drafting = question_graph._tool_question_drafting

    def contaminated_drafting(**kwargs):
        output = original_drafting(**kwargs)
        candidate = dict(output["candidate"])
        scenario = dict(candidate["scenario"])
        scenario["forbidden_entities"] = ("硬件测试知识库",)
        candidate["scenario"] = scenario
        candidate["question_text"] = f"{candidate['question_text']} 请结合硬件测试知识库展开。"
        candidate["quality_gate"] = question_graph.question_candidate_quality_gate(candidate)
        return {**output, "candidate": candidate}

    monkeypatch.setattr(question_graph, "_tool_question_drafting", contaminated_drafting)

    execution = execute_polish_question_agent(
        context=_context(),
        command=_command(),
        runtime_flag_source="test_override",
        provider_enabled=False,
        provider_flag_source="test_override",
        config=PolishQuestionAgentConfig(max_retries=1),
    )

    repair_phase = next(
        phase for phase in execution.metadata["phase_results"] if phase["phase"] == "repair_or_retry"
    )
    assert execution.status == "agent_orchestration_succeeded"
    assert repair_phase["status"] == "repaired"
    assert repair_phase["attempts"] == 1
    assert execution.metadata["validator_result"]["passed"] is True
    assert "硬件测试知识库" not in execution.candidate["question_text"]
    assert execution.candidate["question_metadata"]["repair_strategy"] == "safe_grounding_transform"


def test_in_memory_runtime_polish_question_candidate_payload_is_sanitized() -> None:
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_runtime_with_question_graph_flag())
    command = _command(
        metadata={
            "request_digest": "digest_ref_1",
            "idempotency_key_hash": "idem_hash_ref_1",
            "context_digest": "ctx_ref_1",
            RAW_PROMPT_KEY: "hidden prompt",
            RAW_COMPLETION_KEY: "hidden completion",
            PROVIDER_PAYLOAD_KEY: {"token": "secret"},
            CHECKPOINT_PAYLOAD_KEY: {"state": "hidden"},
            FULL_RESUME_KEY: "hidden resume",
            FULL_JD_KEY: "hidden jd",
            FULL_ANSWER_KEY: "hidden answer",
            HIDDEN_RUBRIC_KEY: "hidden rubric",
            "cookie": "hidden cookie",
            API_KEY: "hidden api key",
        }
    )
    context = _context(command=command)

    result = runtime.start(context, command)
    payload = result.candidate_payloads[0].payload

    assert contains_sensitive_payload(payload) is False
    serialized = repr(asdict(result.candidate_payloads[0]))
    for marker in FORBIDDEN_MARKERS:
        assert marker not in serialized


def test_in_memory_runtime_polish_question_timeline_is_sanitized() -> None:
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_runtime_with_question_graph_flag())
    context = _context()

    runtime.start(context, context.command)
    timeline = runtime.get_timeline(context.run_id, context.owner_id)

    assert [event.event_type for event in timeline.events] == [
        "run_started",
        "checkpoint_recorded",
        "validation_recorded",
        "candidate_payload_emitted",
        "run_succeeded",
    ]
    serialized = repr(asdict(timeline))
    assert "question_text" not in serialized
    for marker in FORBIDDEN_MARKERS:
        assert marker not in serialized


def test_in_memory_runtime_polish_question_status_has_refs_only() -> None:
    runtime = InMemoryLangGraphRuntime(flag_resolver=_enabled_runtime_with_question_graph_flag())
    context = _context()

    result = runtime.start(context, context.command)
    status = runtime.get_status(context.run_id, context.owner_id)

    assert status.status == "agent_orchestration_succeeded"
    assert status.output_refs == result.output_refs
    assert result.candidate_payloads[0].candidate_ref in status.output_refs
    assert status.trace_refs == result.trace_refs
    assert any(ref.startswith("ackpt_") for ref in status.trace_refs)
    assert any(ref.startswith("validation_ref_") for ref in status.trace_refs)
    assert status.formal_write_blocked is True
    assert status.metadata["sanitized"] is True
    assert status.metadata["accepted_candidate_payload"] is True
    assert "candidate" not in status.metadata
    assert "payload" not in status.metadata


def _enabled_runtime_with_question_graph_flag() -> RuntimeFlagResolver:
    return RuntimeFlagResolver(
        test_overrides={
            "AIFI_AI_RUNTIME_ENABLED": True,
            "AIFI_AI_RUNTIME_LANGGRAPH_ENABLED": True,
            POLISH_QUESTION_GRAPH_FLAG: True,
        }
    )


def _context(command: AgentCommandEnvelope | None = None) -> AgentRunContext:
    command = command or _command()
    return AgentRunContext(
        owner_id="owner_pr5_c2",
        actor_id="owner_pr5_c2",
        run_id="arun_pr5_c2_fake_question",
        ai_task_id="aitask_pr5_c2_fake_question",
        graph_name=POLISH_QUESTION_GRAPH_NAME,
        graph_version=POLISH_QUESTION_GRAPH_VERSION,
        command=command,
    )


def _command(*, metadata: dict[str, object] | None = None) -> AgentCommandEnvelope:
    return AgentCommandEnvelope(
        entrypoint="start",
        input_refs=("session_ref_1", "progress_node_payment_consistency", "completed_focus_ref_1"),
        requested_outputs=("candidate_refs",),
        idempotency_key="idem_pr5_c2_fake_question",
        metadata=metadata
        or {
            "request_digest": "digest_ref_1",
            "idempotency_key_hash": "idem_hash_ref_1",
            "context_digest": "ctx_ref_1",
        },
    )
