"""Default-off runtime flag resolver for AI Runtime PR3."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from app.application.ai_runtime.contracts import RuntimePolicyError
from app.application.ai_runtime.registry import GraphDescriptor


@dataclass(frozen=True)
class RuntimeFlagDecision:
    flag_key: str
    enabled: bool
    source: str
    audit_summary: dict[str, Any] = field(default_factory=dict)
    rollback_behavior: str = "disabled_fail_closed_or_adapter_only"


class RuntimeFlagResolver:
    _allowed_callers = frozenset({"facade", "registry", "runner_entry"})

    def __init__(
        self,
        *,
        test_overrides: dict[str, bool] | None = None,
        settings_overrides: dict[str, bool] | None = None,
        persisted_config: dict[str, bool] | None = None,
        allow_persisted_config: bool = False,
    ) -> None:
        self._test_overrides = dict(test_overrides or {})
        self._settings_overrides = dict(settings_overrides or {})
        self._persisted_config = dict(persisted_config or {})
        self._allow_persisted_config = allow_persisted_config

    def resolve_runtime_flag(
        self, flag_key: str, *, actor_id: str, graph_descriptor: GraphDescriptor | None = None
    ) -> RuntimeFlagDecision:
        return self._resolve(flag_key, actor_id=actor_id, graph_descriptor=graph_descriptor)

    def resolve_graph_flag(
        self, graph_descriptor: GraphDescriptor, *, actor_id: str, caller: str
    ) -> RuntimeFlagDecision:
        if caller not in self._allowed_callers:
            raise RuntimePolicyError("runtime flags may only be read at facade, registry, or runner entry")
        return self._resolve(
            graph_descriptor.runtime_flag_key,
            actor_id=actor_id,
            graph_descriptor=graph_descriptor,
        )

    def is_real_provider_enabled(self, *, actor_id: str, provider_key: str = "AIFI_REAL_PROVIDER_ENABLED") -> RuntimeFlagDecision:
        return self._resolve(provider_key, actor_id=actor_id, graph_descriptor=None)

    def explain_flag_decision(self, decision: RuntimeFlagDecision) -> dict[str, Any]:
        return {
            "flag_key": decision.flag_key,
            "enabled": decision.enabled,
            "source": decision.source,
            "rollback_behavior": decision.rollback_behavior,
        }

    def _resolve(
        self, flag_key: str, *, actor_id: str, graph_descriptor: GraphDescriptor | None
    ) -> RuntimeFlagDecision:
        if flag_key in self._test_overrides:
            return self._decision(flag_key, bool(self._test_overrides[flag_key]), "test_override", actor_id)

        env_value = os.getenv(flag_key)
        if env_value is not None:
            return self._decision(flag_key, _parse_bool(env_value), "environment", actor_id)

        if flag_key in self._settings_overrides:
            return self._decision(flag_key, bool(self._settings_overrides[flag_key]), "settings", actor_id)

        if self._allow_persisted_config and flag_key in self._persisted_config:
            return self._decision(flag_key, bool(self._persisted_config[flag_key]), "persisted_graph_config", actor_id)

        default_value = bool(graph_descriptor.default_enabled) if graph_descriptor else False
        return self._decision(flag_key, default_value, "hardcoded_default", actor_id)

    def _decision(self, flag_key: str, enabled: bool, source: str, actor_id: str) -> RuntimeFlagDecision:
        return RuntimeFlagDecision(
            flag_key=flag_key,
            enabled=enabled,
            source=source,
            audit_summary={
                "flag_key": flag_key,
                "enabled": enabled,
                "source": source,
                "actor_id": actor_id,
            },
        )


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}

