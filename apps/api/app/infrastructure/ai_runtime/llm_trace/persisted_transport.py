"""Fail-closed persisted LLM transport for PR4 runtime infrastructure."""

from __future__ import annotations

import hashlib
import json

from sqlalchemy.orm import Session, sessionmaker

from app.application.ai_runtime.contracts import RuntimePolicyError, contains_sensitive_payload, sanitize_payload
from app.application.ai_runtime.llm_trace import LlmBeforeCallTracePolicy, LlmTraceContext
from app.application.ai_runtime.runtime_flags import RuntimeFlagResolver
from app.application.llm.types import LlmTransportRequest, LlmTransportResult
from app.infrastructure.db.repositories.ai_runtime import LlmCallRepository


class FailClosedPersistedLlmTransport:
    """Persists sanitized trace intent and fails before any provider invocation."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session] | None = None,
        flag_resolver: RuntimeFlagResolver | None = None,
        before_call_policy: LlmBeforeCallTracePolicy | None = None,
    ) -> None:
        self._calls = LlmCallRepository(session_factory)
        self._flag_resolver = flag_resolver or RuntimeFlagResolver()
        self._before_call_policy = before_call_policy or LlmBeforeCallTracePolicy.default()

    def plan_call(self, request: LlmTransportRequest, trace_context: LlmTraceContext) -> str:
        if contains_sensitive_payload(request.evidence_bundle):
            raise RuntimePolicyError("LLM trace request must be sanitized before planning")
        request_hash = _hash_request(request)
        call = self._calls.create_planned_call(
            owner_id=trace_context.owner_id,
            actor_id=None,
            ai_task_id=trace_context.ai_task_id,
            agent_run_id=trace_context.agent_run_id,
            agent_node_run_id=trace_context.agent_node_run_id,
            graph_name=request.task_type,
            node_name="pr4_persisted_transport",
            contract_ids_json=list(trace_context.contract_ids or request.contract_ids),
            configured_model="provider-disabled",
            provider_model=None,
            prompt_version="pr4-fail-closed",
            schema_id=None,
            request_hash=request_hash,
        )
        return str(call["id"])

    def mark_call_running(self, llm_call_id: str, trace_context: LlmTraceContext) -> None:
        call = self._calls.get_summary_for_owner(trace_context.owner_id, llm_call_id)
        if call is None:
            raise RuntimePolicyError("LLM call not found for owner")
        self._calls.mark_running(trace_context.owner_id, llm_call_id, base_record_version=call["record_version"])

    def generate(self, request: LlmTransportRequest, trace_context: LlmTraceContext) -> LlmTransportResult:
        llm_call_id = self.plan_call(request, trace_context)
        self._before_call_policy.authorize_provider_invocation(llm_call_id=llm_call_id)
        decision = self._flag_resolver.is_real_provider_enabled(actor_id=trace_context.owner_id)
        call = self._calls.get_summary_for_owner(trace_context.owner_id, llm_call_id)
        if call is None:
            raise RuntimePolicyError("LLM call trace disappeared before provider gate")
        if not decision.enabled:
            self._calls.mark_failed(
                trace_context.owner_id,
                llm_call_id,
                base_record_version=call["record_version"],
                error_summary_json={"category": "provider_disabled", "provider_invoked": False},
                fallback_reason="provider_disabled_fail_closed",
            )
            raise RuntimePolicyError("provider disabled before invocation")
        self._calls.mark_failed(
            trace_context.owner_id,
            llm_call_id,
            base_record_version=call["record_version"],
            error_summary_json={"category": "provider_unavailable", "provider_invoked": False},
            fallback_reason="provider_unavailable_fail_closed",
        )
        raise RuntimePolicyError("provider invocation unavailable in PR4 runtime transport")

    def get_llm_call_summary(self, owner_id: str, llm_call_id: str) -> dict[str, object]:
        summary = self._calls.get_summary_for_owner(owner_id, llm_call_id)
        if summary is None:
            raise RuntimePolicyError("LLM call not found for owner")
        return sanitize_payload(summary)


def _hash_request(request: LlmTransportRequest) -> str:
    body = {
        "contract_ids": request.contract_ids,
        "task_type": request.task_type,
        "input_refs": request.input_refs,
        "evidence_bundle": sanitize_payload(request.evidence_bundle),
    }
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()
