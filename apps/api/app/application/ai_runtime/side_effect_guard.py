"""AI Runtime side-effect policy guard."""

from __future__ import annotations

from typing import Any

from app.application.agents.contracts import ToolDefinition
from app.application.ai_runtime.contracts import RuntimePolicyError, contains_sensitive_payload, sanitize_payload


_CHECKPOINT_METADATA_EXACT_KEYS = frozenset(
    {
        "checkpoint_namespace",
        "thread_id",
        "checkpoint_id",
        "graph_name",
        "graph_version",
        "node_name",
        "version",
        "hashes",
        "timestamps",
    }
)


class AgentSideEffectGuard:
    _formal_targets = frozenset(
        {"question", "feedback", "report", "review", "candidate", "weakness", "asset", "training"}
    )

    def authorize_node_start(self, *, declared_side_effects: tuple[str, ...], requested_side_effect: str | None) -> bool:
        if requested_side_effect and requested_side_effect not in declared_side_effects:
            raise RuntimePolicyError("undeclared side effect blocked")
        return True

    def assert_no_sensitive_payload(self, payload: Any) -> Any:
        if contains_sensitive_payload(payload):
            raise RuntimePolicyError("sensitive payload blocked")
        return sanitize_payload(payload)

    def assert_no_raw_payload(self, payload: Any) -> Any:
        return self.assert_no_sensitive_payload(payload)

    def authorize_handoff(self, *, target_type: str, user_confirmed: bool, replay_mode: bool, cancelled: bool = False) -> bool:
        if cancelled:
            raise RuntimePolicyError("late formal write blocked after cancel")
        if replay_mode:
            raise RuntimePolicyError("replay cannot write formal object")
        if target_type in self._formal_targets and not user_confirmed:
            raise RuntimePolicyError("user confirmation required before formal write")
        return True

    def authorize_tool_call(
        self,
        *,
        owner_id: str,
        tool_name: str,
        input_refs: tuple[str, ...],
        tool: ToolDefinition | None = None,
        caller_id: str | None = None,
        permission_scope: str | None = None,
        owner_scope: str | None = None,
        side_effect_policy: str | None = None,
        payload: Any | None = None,
    ) -> bool:
        if not owner_id or not tool_name:
            raise RuntimePolicyError("owner-scoped tool call required")
        if any(not ref for ref in input_refs):
            raise RuntimePolicyError("tool input refs must be explicit")
        if tool is None:
            raise RuntimePolicyError("registered ToolDefinition required for runtime tool call")
        if tool.tool_name != tool_name:
            raise RuntimePolicyError("tool_not_allowed")
        if caller_id not in tool.allowed_callers:
            raise RuntimePolicyError("caller not allowed for tool")
        if permission_scope is not None and permission_scope != tool.permission_scope:
            raise RuntimePolicyError("permission_scope mismatch")
        if owner_scope is not None and owner_scope != tool.owner_scope:
            raise RuntimePolicyError("owner_scope mismatch")
        if side_effect_policy is not None and side_effect_policy != tool.side_effect_policy:
            raise RuntimePolicyError("side_effect_policy mismatch")
        if tool.side_effect_policy == "forbidden":
            raise RuntimePolicyError("tool side_effect_policy is forbidden")
        if payload is not None and (
            contains_sensitive_payload(payload) or _contains_tool_forbidden_payload(payload, tool.forbidden_data)
        ):
            raise RuntimePolicyError("forbidden data payload blocked")
        return True

    def verify_checkpoint_write(self, metadata: dict[str, Any]) -> dict[str, Any]:
        return sanitize_checkpoint_metadata(metadata)


def sanitize_checkpoint_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        raise RuntimePolicyError("checkpoint metadata must be an object")
    blocked_keys = tuple(sorted(str(key) for key in metadata if not _is_allowed_checkpoint_metadata_key(str(key))))
    if blocked_keys:
        raise RuntimePolicyError(f"checkpoint metadata key not allowed: {', '.join(blocked_keys)}")
    if contains_sensitive_payload(metadata):
        raise RuntimePolicyError("checkpoint metadata cannot carry sensitive content")
    return sanitize_payload(metadata)


def _is_allowed_checkpoint_metadata_key(key: str) -> bool:
    return (
        key in _CHECKPOINT_METADATA_EXACT_KEYS
        or key.endswith("_hash")
        or key.endswith("_hashes")
        or key.endswith("_at")
        or key.endswith("_version")
        or (key.startswith("retention_") and (key.endswith("_ref") or key.endswith("_refs")))
    )


def _contains_tool_forbidden_payload(value: Any, forbidden_data: tuple[str, ...]) -> bool:
    forbidden_keys = frozenset(_normalize_payload_key(key) for key in forbidden_data)
    if not forbidden_keys:
        return False
    return _contains_forbidden_payload_key(value, forbidden_keys)


def _contains_forbidden_payload_key(value: Any, forbidden_keys: frozenset[str]) -> bool:
    if isinstance(value, dict):
        return any(
            _normalize_payload_key(key) in forbidden_keys or _contains_forbidden_payload_key(item, forbidden_keys)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_payload_key(item, forbidden_keys) for item in value)
    return False


def _normalize_payload_key(key: object) -> str:
    return str(key).strip().lower().replace("-", "_").replace(" ", "_")
