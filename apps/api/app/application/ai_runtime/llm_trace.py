"""LLM trace application contract for PR3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.application.ai_runtime.contracts import (
    RuntimePolicyError,
    RuntimeUnavailableError,
    contains_sensitive_payload,
    sanitize_payload,
)
from app.application.llm.types import LlmTransportRequest, LlmTransportResult


@dataclass(frozen=True)
class LlmTraceContext:
    owner_id: str
    ai_task_id: str
    agent_run_id: str
    agent_node_run_id: str
    contract_ids: tuple[str, ...]
    replay_mode: str


@dataclass(frozen=True)
class LlmBeforeCallTracePolicy:
    before_call_trace_required: bool = True
    fail_closed_on_trace_write_failure: bool = True

    @classmethod
    def default(cls) -> "LlmBeforeCallTracePolicy":
        return cls()

    def authorize_provider_invocation(self, *, llm_call_id: str) -> bool:
        if self.before_call_trace_required and not llm_call_id:
            raise RuntimePolicyError("before-call trace write must succeed before provider invocation")
        return True


@dataclass(frozen=True)
class LlmPayloadCapturePolicy:
    raw_enabled: bool
    sanitized_summary_required: bool
    capture_policy_version: str = "pr3-default-off"
    debug_capture_allowed: bool = False

    @classmethod
    def resolve(
        cls, *, settings: dict[str, object], context: LlmTraceContext, environment: str
    ) -> "LlmPayloadCapturePolicy":
        if not context.owner_id:
            raise RuntimePolicyError("owner is required for LLM trace capture")
        debug_requested = bool(settings.get("debug_raw_enabled"))
        debug_allowed = debug_requested and environment != "production" and context.replay_mode == "debug_replay"
        return cls(
            raw_enabled=False,
            sanitized_summary_required=True,
            debug_capture_allowed=debug_allowed,
        )

    def capture_debug_raw_ref(self, ref: str) -> None:
        if not self.raw_enabled:
            raise RuntimePolicyError("debug capture disabled in PR3")
        raise RuntimeUnavailableError(f"debug capture ref is unavailable: {ref}")

    def reuse_production_resume_summary(self, summary: dict[str, Any]) -> dict[str, Any]:
        if contains_sensitive_payload(summary):
            raise RuntimePolicyError("production resume summary must be sanitized")
        return sanitize_payload(summary)


class PersistedLlmTransport(Protocol):
    def plan_call(self, request: LlmTransportRequest, trace_context: LlmTraceContext) -> str: ...

    def mark_call_running(self, llm_call_id: str, trace_context: LlmTraceContext) -> None: ...

    def generate(self, request: LlmTransportRequest, trace_context: LlmTraceContext) -> LlmTransportResult: ...

    def get_llm_call_summary(self, owner_id: str, llm_call_id: str) -> dict[str, Any]: ...
