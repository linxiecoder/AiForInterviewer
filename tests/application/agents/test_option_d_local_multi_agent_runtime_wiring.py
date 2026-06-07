from __future__ import annotations

import pytest

from app.application.ai_runtime.business_graphs.local_multi_agent_orchestrator import (
    LOCAL_MULTI_AGENT_GRAPH_FLAG,
    LOCAL_MULTI_AGENT_GRAPH_NAME,
)
from app.application.ai_runtime.contracts import (
    AgentCandidatePayload,
    GraphDisabledError,
    contains_sensitive_payload,
)
from app.application.ai_runtime.facade import AiOrchestrationFacade
from app.application.ai_runtime.registry import AgentGraphRegistry
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.infrastructure.ai_runtime.langgraph.in_memory_runtime import InMemoryLangGraphRuntime


def test_option_d_local_multi_agent_default_off_blocks_before_runtime_execution() -> None:
    facade = _facade(
        RuntimeFlagResolver(
            test_overrides={
                "AIFI_AI_RUNTIME_ENABLED": True,
                "AIFI_AI_RUNTIME_LANGGRAPH_ENABLED": True,
            }
        )
    )

    with pytest.raises(GraphDisabledError, match=LOCAL_MULTI_AGENT_GRAPH_NAME):
        facade.start_local_multi_agent_orchestration(**_start_kwargs("idem_default_off"))


def test_option_d_local_multi_agent_runtime_returns_refs_only_candidates_handoffs_and_interrupt() -> None:
    facade = _facade(_enabled_flags())

    status = facade.start_local_multi_agent_orchestration(**_start_kwargs("idem_runtime_happy"))

    assert status.status == "interrupted"
    assert status.formal_refs == ()
    assert status.interrupt_refs
    assert set(status.candidate_refs) == {
        "feedback_candidate_ref_option_d",
        _payload_by_type(status.candidate_payloads, "asset_update_candidate").candidate_ref,
        _payload_by_type(status.candidate_payloads, "training_plan_candidate").candidate_ref,
    }
    assert {payload.candidate_type for payload in status.candidate_payloads} == {
        "feedback_candidate",
        "asset_update_candidate",
        "training_plan_candidate",
    }
    for payload in status.candidate_payloads:
        assert payload.validation_refs == ("validation_ref_feedback", "validation_ref_asset")
        assert not contains_sensitive_payload(payload.payload)
        assert payload.payload["formal_write_blocked"] is True

    asset_payload = _payload_by_type(status.candidate_payloads, "asset_update_candidate")
    assert asset_payload.status == "requires_user_confirmation"
    assert asset_payload.payload["user_confirmation_required"] is True
    assert asset_payload.payload["handoff_refs"]

    run_status = facade.get_agent_run_status(run_id=status.agent_run_id, owner_id="owner_option_d")
    assert run_status.status == "interrupted"
    assert run_status.formal_write_blocked is True
    assert run_status.metadata["source_boundary"] == "AgentGraphRunner"
    assert run_status.metadata["graph_name"] == LOCAL_MULTI_AGENT_GRAPH_NAME
    assert run_status.metadata["orchestrator_agent_id"] == LOCAL_MULTI_AGENT_GRAPH_NAME
    assert set(run_status.metadata["participant_agent_ids"]) == {
        "polish_feedback_agent",
        "asset_candidate_agent",
        "training_plan_agent",
    }
    assert run_status.metadata["provider_calls"] == 0
    assert run_status.metadata["repository_writes"] == 0
    assert run_status.metadata["db_business_writes"] == 0
    assert run_status.metadata["formal_business_writes"] == 0
    assert tuple(run_status.metadata["validation_refs"]) == ("validation_ref_feedback", "validation_ref_asset")
    assert run_status.metadata["handoff_refs"]
    assert run_status.metadata["hitl_required"] is True

    timeline = facade.get_agent_run_timeline(run_id=status.agent_run_id, owner_id="owner_option_d")
    assert any(event.event_type.startswith("local_multi_agent_step_") for event in timeline.events)
    assert any(event.event_type == "interrupt_opened" for event in timeline.events)
    assert all(event.metadata["source_boundary"] == "AgentGraphRunner" for event in timeline.events)


def test_option_d_local_multi_agent_formal_write_request_blocks_without_candidates_or_formal_refs() -> None:
    facade = _facade(_enabled_flags())

    status = facade.start_local_multi_agent_orchestration(
        **_start_kwargs(
            "idem_formal_blocked",
            formal_write_requested_ref="formal_write_interrupt_ref_option_d",
        )
    )

    assert status.status == "blocked"
    assert status.candidate_refs == ()
    assert status.candidate_payloads == ()
    assert status.formal_refs == ()
    assert status.interrupt_refs == ("formal_write_interrupt_ref_option_d",)

    run_status = facade.get_agent_run_status(run_id=status.agent_run_id, owner_id="owner_option_d")
    assert run_status.metadata["hitl_triggers"] == ("formal_write_requested",)
    assert run_status.metadata["provider_calls"] == 0
    assert run_status.metadata["formal_business_writes"] == 0


def _facade(flag_resolver: RuntimeFlagResolver) -> AiOrchestrationFacade:
    runtime = InMemoryLangGraphRuntime(flag_resolver=flag_resolver)
    return AiOrchestrationFacade(
        runner=runtime,
        registry=AgentGraphRegistry.default(),
        flag_resolver=flag_resolver,
    )


def _enabled_flags() -> RuntimeFlagResolver:
    return RuntimeFlagResolver(
        test_overrides={
            "AIFI_AI_RUNTIME_ENABLED": True,
            "AIFI_AI_RUNTIME_LANGGRAPH_ENABLED": True,
            LOCAL_MULTI_AGENT_GRAPH_FLAG: True,
        }
    )


def _start_kwargs(idempotency_key: str, **overrides: object) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "owner_id": "owner_option_d",
        "actor_id": "actor_option_d",
        "session_ref": "session_ref_option_d",
        "feedback_candidate_ref": "feedback_candidate_ref_option_d",
        "answer_ref": "answer_ref_option_d",
        "question_ref": "question_ref_option_d",
        "evidence_refs": ("evidence_ref_1", "evidence_ref_2"),
        "source_trace_refs": ("trace_ref_feedback",),
        "validation_refs": ("validation_ref_feedback", "validation_ref_asset"),
        "idempotency_key": idempotency_key,
    }
    kwargs.update(overrides)
    return kwargs


def _payload_by_type(
    payloads: tuple[AgentCandidatePayload, ...],
    candidate_type: str,
) -> AgentCandidatePayload:
    return next(payload for payload in payloads if payload.candidate_type == candidate_type)
