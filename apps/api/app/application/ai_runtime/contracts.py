"""Project-owned AI Runtime DTOs, ports, and errors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from app.application.llm.provider_boundary import P7_PROVIDER_FORBIDDEN_KEYS


class GraphDisabledError(RuntimeError):
    """Raised when runtime or graph enablement is disabled."""


class OwnerScopeError(RuntimeError):
    """Raised when a runtime action crosses owner scope."""


class RuntimeValidationError(RuntimeError):
    """Raised when runtime input violates the application contract."""


class RuntimeConflictError(RuntimeError):
    """Raised when idempotency or version checks conflict."""


class RuntimePolicyError(RuntimeError):
    """Raised when a runtime policy blocks the requested operation."""


class RuntimeUnavailableError(RuntimeError):
    """Raised when a required runtime contract dependency is unavailable."""


_SENSITIVE_KEYS = frozenset(
    {
        *P7_PROVIDER_FORBIDDEN_KEYS,
        "raw" + "_prompt",
        "raw" + "_completion",
        "raw" + "_provider" + "_payload",
        "provider" + "_payload",
        "checkpoint" + "_payload",
        "system" + "_prompt",
        "token",
        "cookie",
        "secret",
        "api_key",
        "full_source_body",
        "full_resume",
        "full_jd",
        "full_answer",
        "hidden_rubric",
    }
)
_SENSITIVE_VALUE_MARKERS = tuple(sorted(_SENSITIVE_KEYS | {"sk-", "bearer "}))


def is_sensitive_key(key: object) -> bool:
    normalized = str(key).strip().lower().replace("-", "_").replace(" ", "_")
    return normalized in _SENSITIVE_KEYS or any(marker in normalized for marker in ("token", "secret", "cookie"))


def contains_sensitive_payload(value: Any) -> bool:
    if isinstance(value, dict):
        return any(is_sensitive_key(key) or contains_sensitive_payload(item) for key, item in value.items())
    if isinstance(value, (list, tuple, set)):
        return any(contains_sensitive_payload(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        return any(marker in lowered for marker in _SENSITIVE_VALUE_MARKERS)
    return False


def sanitize_payload(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            if is_sensitive_key(key):
                continue
            sanitized[str(key)] = sanitize_payload(item)
        return sanitized
    if isinstance(value, tuple):
        return tuple(sanitize_payload(item) for item in value)
    if isinstance(value, list):
        return [sanitize_payload(item) for item in value]
    if isinstance(value, set):
        return sorted(sanitize_payload(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in _SENSITIVE_VALUE_MARKERS):
            return "[redacted]"
    return value


_RUNTIME_STATUS_EXACT_CATEGORIES = {
    "queued": "pending",
    "created": "pending",
    "planned": "pending",
    "captured": "pending",
    "started": "running",
    "running": "running",
    "retry_scheduled": "running",
    "delegated": "running",
    "resumed": "running",
    "succeeded": "succeeded",
    "completed": "succeeded",
    "generated": "succeeded",
    "accepted": "succeeded",
    "candidate": "succeeded",
    "passed": "succeeded",
    "ok": "succeeded",
    "saved": "succeeded",
    "repaired": "succeeded",
    "finalized": "succeeded",
    "failed": "failed",
    "validation_failed": "failed",
    "provider_failed": "failed",
    "provider_request_invalid": "failed",
    "blocked": "blocked",
    "skipped": "blocked",
    "interrupted": "interrupted",
    "requires_user_confirmation": "interrupted",
    "open": "interrupted",
    "replayed": "replayed",
    "replayed_debug": "replayed",
    "skeleton_replayed": "replayed",
    "replay_reused": "replayed",
    "cancelled": "cancelled",
    "canceled": "cancelled",
    "rejected": "cancelled",
    "expired": "cancelled",
}

_REPLAY_SIDE_EFFECT_COUNTER_KEYS = (
    "provider_calls",
    "tool_calls",
    "external_tool_calls",
    "repository_calls",
    "repository_reads",
    "repository_writes",
    "db_business_writes",
    "formal_business_writes",
)


def classify_agent_runtime_status(status: str) -> str:
    normalized = str(status).strip().lower()
    if not normalized:
        raise RuntimeValidationError("runtime status is required")
    exact = _RUNTIME_STATUS_EXACT_CATEGORIES.get(normalized)
    if exact is not None:
        return exact
    if any(marker in normalized for marker in ("failed", "failure", "invalid", "error")):
        return "failed"
    if any(marker in normalized for marker in ("blocked", "conflict")):
        return "blocked"
    if any(marker in normalized for marker in ("interrupt", "confirmation")):
        return "interrupted"
    if normalized.startswith("replay") or "replayed" in normalized:
        return "replayed"
    if any(marker in normalized for marker in ("cancel", "reject", "expired")):
        return "cancelled"
    if any(marker in normalized for marker in ("success", "succeeded", "accepted", "generated", "completed")):
        return "succeeded"
    raise RuntimeValidationError(f"unknown runtime status: {status}")


def validate_agent_runtime_status(status: str, metadata: dict[str, Any] | None = None) -> str:
    category = classify_agent_runtime_status(status)
    failure_reason = str(dict(metadata or {}).get("failure_reason") or "").strip()
    if failure_reason and category == "succeeded":
        raise RuntimeValidationError("runtime status cannot be success-like when failure_reason is set")
    return category


def validate_replay_side_effect_metadata(metadata: dict[str, Any]) -> None:
    for key in _REPLAY_SIDE_EFFECT_COUNTER_KEYS:
        if not _replay_side_effect_counter_is_zero(metadata.get(key)):
            raise RuntimeValidationError("replay cannot call providers, tools, or repositories")


def _replay_side_effect_counter_is_zero(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, bool):
        return value is False
    if isinstance(value, (int, float)):
        return value == 0
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return True
        try:
            return float(stripped) == 0
        except ValueError:
            return False
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


@dataclass(frozen=True)
class AgentCommandEnvelope:
    entrypoint: str
    input_refs: tuple[str, ...] = field(default_factory=tuple)
    requested_outputs: tuple[str, ...] = field(default_factory=tuple)
    idempotency_key: str | None = None
    replay_mode: str = "read_only"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", sanitize_payload(self.metadata))


@dataclass(frozen=True)
class AgentRunContext:
    owner_id: str
    actor_id: str
    run_id: str
    ai_task_id: str
    graph_name: str
    graph_version: str
    command: AgentCommandEnvelope


@dataclass(frozen=True)
class AgentCandidatePayload:
    candidate_ref: str
    candidate_type: str
    payload_schema_id: str
    payload: dict[str, Any]
    status: str = "accepted"
    trace_refs: tuple[str, ...] = field(default_factory=tuple)
    validation_refs: tuple[str, ...] = field(default_factory=tuple)
    low_confidence_flags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not str(self.candidate_ref).strip():
            raise RuntimeValidationError("candidate_ref is required")
        if not str(self.candidate_type).strip():
            raise RuntimeValidationError("candidate_type is required")
        if not str(self.payload_schema_id).strip():
            raise RuntimeValidationError("payload_schema_id is required")
        if not str(self.status).strip():
            raise RuntimeValidationError("status is required")
        validate_agent_runtime_status(str(self.status))
        if not isinstance(self.payload, dict):
            raise RuntimeValidationError("candidate payload must be a dict")
        if contains_sensitive_payload(self.payload):
            raise RuntimePolicyError("candidate payload contains sensitive content")
        object.__setattr__(self, "candidate_ref", str(self.candidate_ref).strip())
        object.__setattr__(self, "candidate_type", str(self.candidate_type).strip())
        object.__setattr__(self, "payload_schema_id", str(self.payload_schema_id).strip())
        object.__setattr__(self, "status", str(self.status).strip())
        object.__setattr__(self, "payload", sanitize_payload(self.payload))
        object.__setattr__(self, "trace_refs", tuple(self.trace_refs))
        object.__setattr__(self, "validation_refs", tuple(self.validation_refs))
        object.__setattr__(self, "low_confidence_flags", tuple(self.low_confidence_flags))


def _candidate_payload_tuple(payloads: tuple[AgentCandidatePayload, ...]) -> tuple[AgentCandidatePayload, ...]:
    candidate_payloads = tuple(payloads)
    if any(not isinstance(payload, AgentCandidatePayload) for payload in candidate_payloads):
        raise RuntimeValidationError("candidate_payloads must contain AgentCandidatePayload")
    return candidate_payloads


@dataclass(frozen=True)
class AgentRunResult:
    run_id: str
    status: str
    output_refs: tuple[str, ...] = field(default_factory=tuple)
    trace_refs: tuple[str, ...] = field(default_factory=tuple)
    interrupt_refs: tuple[str, ...] = field(default_factory=tuple)
    formal_refs: tuple[str, ...] = field(default_factory=tuple)
    candidate_payloads: tuple[AgentCandidatePayload, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        metadata = sanitize_payload(self.metadata)
        validate_agent_runtime_status(self.status, metadata)
        object.__setattr__(self, "status", str(self.status).strip())
        object.__setattr__(self, "candidate_payloads", _candidate_payload_tuple(self.candidate_payloads))
        object.__setattr__(self, "metadata", metadata)


@dataclass(frozen=True)
class AgentReplayResult:
    run_id: str
    status: str
    read_only: bool = True
    formal_write_blocked: bool = True
    output_refs: tuple[str, ...] = field(default_factory=tuple)
    trace_refs: tuple[str, ...] = field(default_factory=tuple)
    timeline_refs: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        metadata = sanitize_payload(self.metadata)
        validate_agent_runtime_status(self.status, metadata)
        validate_replay_side_effect_metadata(metadata)
        object.__setattr__(self, "status", str(self.status).strip())
        object.__setattr__(self, "output_refs", tuple(self.output_refs))
        object.__setattr__(self, "trace_refs", tuple(self.trace_refs))
        object.__setattr__(self, "timeline_refs", tuple(self.timeline_refs))
        object.__setattr__(self, "metadata", metadata)


@dataclass(frozen=True)
class AgentRunStatus:
    run_id: str
    status: str
    owner_id: str
    output_refs: tuple[str, ...] = field(default_factory=tuple)
    trace_refs: tuple[str, ...] = field(default_factory=tuple)
    interrupt_refs: tuple[str, ...] = field(default_factory=tuple)
    formal_write_blocked: bool = True
    cancellation_policy: str = "late_formal_write_blocked"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        metadata = sanitize_payload(self.metadata)
        validate_agent_runtime_status(self.status, metadata)
        object.__setattr__(self, "status", str(self.status).strip())
        object.__setattr__(self, "metadata", metadata)


@dataclass(frozen=True)
class AgentTimelineEvent:
    event_id: str
    event_type: str
    summary: str
    refs: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", sanitize_payload(self.metadata))


@dataclass(frozen=True)
class AgentRunTimelinePage:
    run_id: str
    events: tuple[AgentTimelineEvent, ...] = field(default_factory=tuple)
    next_cursor: str | None = None


@dataclass(frozen=True)
class AgentTaskStatusRef:
    ai_task_id: str
    agent_run_id: str
    status: str
    trace_refs: tuple[str, ...] = field(default_factory=tuple)
    candidate_refs: tuple[str, ...] = field(default_factory=tuple)
    interrupt_refs: tuple[str, ...] = field(default_factory=tuple)
    formal_refs: tuple[str, ...] = field(default_factory=tuple)
    candidate_payloads: tuple[AgentCandidatePayload, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        validate_agent_runtime_status(self.status)
        object.__setattr__(self, "status", str(self.status).strip())
        object.__setattr__(self, "candidate_payloads", _candidate_payload_tuple(self.candidate_payloads))


@dataclass(frozen=True)
class AgentInterruptRef:
    interrupt_id: str
    run_id: str
    owner_id: str
    interrupt_type: str
    resume_schema_id: str
    status: str
    record_version: int
    checkpoint_ref: str = ""
    drawer_payload: dict[str, Any] = field(default_factory=dict)
    trace_refs: tuple[str, ...] = field(default_factory=tuple)
    formal_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        validate_agent_runtime_status(self.status)
        object.__setattr__(self, "status", str(self.status).strip())
        object.__setattr__(self, "drawer_payload", sanitize_payload(self.drawer_payload))


class AgentGraphRunner(Protocol):
    def start(self, context: AgentRunContext, command: AgentCommandEnvelope) -> AgentRunResult: ...

    def resume(
        self, context: AgentRunContext, interrupt_ref: str, resume_payload: dict[str, object]
    ) -> AgentRunResult: ...

    def replay(self, context: AgentRunContext, checkpoint_ref: str) -> AgentReplayResult: ...

    def get_status(self, run_id: str, owner_id: str) -> AgentRunStatus: ...

    def get_timeline(
        self, run_id: str, owner_id: str, cursor: str | None = None, limit: int = 50
    ) -> AgentRunTimelinePage: ...

    def cancel(self, run_id: str, owner_id: str, reason: str, actor_id: str) -> AgentRunStatus: ...
