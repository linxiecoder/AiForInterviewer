from __future__ import annotations

from pathlib import Path

import pytest

from app.application.ai_runtime.business_graphs.local_multi_agent_orchestrator import (
    LOCAL_MULTI_AGENT_GRAPH_FLAG,
    LOCAL_MULTI_AGENT_GRAPH_NAME,
    LOCAL_MULTI_AGENT_TASK_TYPE,
)
from app.application.ai_runtime.registry import AgentGraphRegistry
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.application.ai_runtime.contracts import RuntimePolicyError


def test_runtime_and_graph_flags_default_false() -> None:
    resolver = RuntimeFlagResolver()
    descriptor = AgentGraphRegistry.default().get_graph_descriptor("polish_question_generation")

    assert resolver.resolve_runtime_flag("AIFI_AI_RUNTIME_ENABLED", actor_id="actor_1").enabled is False
    assert resolver.resolve_graph_flag(descriptor, actor_id="actor_1", caller="facade").enabled is False
    assert resolver.is_real_provider_enabled(actor_id="actor_1").enabled is False


def test_local_multi_agent_graph_flag_default_false_and_provider_independent() -> None:
    resolver = RuntimeFlagResolver()
    descriptor = AgentGraphRegistry.default().get_graph_descriptor(LOCAL_MULTI_AGENT_TASK_TYPE)

    assert descriptor.graph_name == LOCAL_MULTI_AGENT_GRAPH_NAME
    assert descriptor.runtime_flag_key == LOCAL_MULTI_AGENT_GRAPH_FLAG
    assert descriptor.default_enabled is False
    assert descriptor.provider_enabled is False
    assert descriptor.formal_write_targets == ()
    assert descriptor.db_business_write_targets == ()
    assert resolver.resolve_graph_flag(descriptor, actor_id="actor_1", caller="facade").enabled is False
    assert resolver.is_real_provider_enabled(actor_id="actor_1").enabled is False


def test_env_example_documents_langgraph_runtime_flag_default_off() -> None:
    env_example = Path(".env.example").read_text(encoding="utf-8")

    assert "AIFI_AI_RUNTIME_LANGGRAPH_ENABLED=false" in env_example


def test_flag_source_priority_uses_test_override_before_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AIFI_AI_RUNTIME_ENABLED", "false")
    resolver = RuntimeFlagResolver(test_overrides={"AIFI_AI_RUNTIME_ENABLED": True})

    decision = resolver.resolve_runtime_flag("AIFI_AI_RUNTIME_ENABLED", actor_id="actor_1")

    assert decision.enabled is True
    assert decision.source == "test_override"
    assert decision.audit_summary["enabled"] is True


def test_explicit_environment_is_used_before_pr6_persisted_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AIFI_AI_RUNTIME_ENABLED", "true")
    resolver = RuntimeFlagResolver(persisted_config={"AIFI_AI_RUNTIME_ENABLED": False})

    decision = resolver.resolve_runtime_flag("AIFI_AI_RUNTIME_ENABLED", actor_id="actor_1")

    assert decision.enabled is True
    assert decision.source == "environment"


def test_pr3_ignores_persisted_config_until_authorized() -> None:
    resolver = RuntimeFlagResolver(persisted_config={"AIFI_AI_RUNTIME_ENABLED": True})

    decision = resolver.resolve_runtime_flag("AIFI_AI_RUNTIME_ENABLED", actor_id="actor_1")

    assert decision.enabled is False
    assert decision.source == "hardcoded_default"


def test_graph_node_cannot_read_runtime_flag_directly() -> None:
    descriptor = AgentGraphRegistry.default().get_graph_descriptor("polish_question_generation")
    resolver = RuntimeFlagResolver(test_overrides={descriptor.runtime_flag_key: True})

    with pytest.raises(RuntimePolicyError):
        resolver.resolve_graph_flag(descriptor, actor_id="actor_1", caller="graph_node")


def test_real_provider_gate_is_independent_from_graph_enablement() -> None:
    resolver = RuntimeFlagResolver(
        test_overrides={"AIFI_AI_RUNTIME_ENABLED": True, "AIFI_GRAPH_POLISH_QUESTION_ENABLED": True}
    )

    assert resolver.resolve_runtime_flag("AIFI_AI_RUNTIME_ENABLED", actor_id="actor_1").enabled is True
    assert resolver.is_real_provider_enabled(actor_id="actor_1").enabled is False
