"""AI Runtime side-effect policy guard."""

from __future__ import annotations

from typing import Any

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

    def authorize_tool_call(self, *, owner_id: str, tool_name: str, input_refs: tuple[str, ...]) -> bool:
        if not owner_id or not tool_name:
            raise RuntimePolicyError("owner-scoped tool call required")
        if any(not ref for ref in input_refs):
            raise RuntimePolicyError("tool input refs must be explicit")
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
