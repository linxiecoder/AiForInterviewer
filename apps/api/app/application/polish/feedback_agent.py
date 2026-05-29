from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.application.llm.ports import LlmTransport
from app.application.llm.types import LlmTransportRequest, LlmTransportResult
from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
    POLISH_FEEDBACK_GENERATED_CONTRACT_IDS,
    POLISH_FEEDBACK_GENERATED_SCHEMA_ID,
    POLISH_FEEDBACK_TASK_TYPE,
)


@dataclass(frozen=True)
class FeedbackAgentResult:
    succeeded: bool
    payload: dict[str, Any] | None
    validation_errors: tuple[str, ...] = ()
    low_confidence_flags: tuple[str, ...] = ()
    trace_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


class FeedbackGenerationAgent:
    def __init__(self, *, transport: LlmTransport) -> None:
        self._transport = transport

    def generate(
        self,
        *,
        prompt_asset: dict[str, Any],
        input_refs: tuple[str, ...],
    ) -> FeedbackAgentResult:
        request = LlmTransportRequest(
            contract_ids=_contract_ids(prompt_asset),
            task_type=_text(prompt_asset.get("task_type")) or POLISH_FEEDBACK_TASK_TYPE,
            input_refs=input_refs,
            evidence_bundle=prompt_asset,
            prompt_version=_text(prompt_asset.get("prompt_version")) or POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
            schema_id=_text(prompt_asset.get("schema_id")) or POLISH_FEEDBACK_GENERATED_SCHEMA_ID,
        )
        try:
            provider_result = self._transport.generate(request)
        except Exception as exc:
            return FeedbackAgentResult(
                succeeded=False,
                payload=None,
                validation_errors=("llm_transport_generation_failed",),
                metadata={
                    "provider_status": "failed",
                    "provider_error_type": exc.__class__.__name__,
                    "llm_called": True,
                },
            )

        payload, extraction_errors = _extract_payload(provider_result)
        provider_status = _provider_status(provider_result, payload)
        metadata = {
            "provider_status": provider_status,
            "provider_validation_status": str(provider_result.validation_status),
            "provider_confidence_level": str(provider_result.confidence_level),
            "llm_called": True,
        }
        if extraction_errors:
            return FeedbackAgentResult(
                succeeded=False,
                payload=None,
                validation_errors=extraction_errors,
                low_confidence_flags=tuple(provider_result.low_confidence_flags),
                trace_refs=tuple(provider_result.trace_refs),
                evidence_refs=tuple(provider_result.evidence_refs),
                metadata=metadata,
            )
        return FeedbackAgentResult(
            succeeded=True,
            payload=payload,
            validation_errors=(),
            low_confidence_flags=tuple(provider_result.low_confidence_flags),
            trace_refs=tuple(provider_result.trace_refs),
            evidence_refs=tuple(provider_result.evidence_refs),
            metadata=metadata,
        )


def _extract_payload(result: LlmTransportResult) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    raw_payload = result.result
    if not isinstance(raw_payload, dict):
        return None, ("feedback_payload_schema_invalid",)
    for field_name in ("payload", "generated_feedback", "generated_feedback_payload"):
        nested = raw_payload.get(field_name)
        if nested is not None:
            if not isinstance(nested, dict):
                return None, ("feedback_payload_schema_invalid",)
            return dict(nested), ()
    return dict(raw_payload), ()


def _provider_status(result: LlmTransportResult, payload: dict[str, Any] | None) -> str:
    if isinstance(payload, dict) and payload.get("transport") == "fake":
        return "fake_transport"
    if isinstance(result.result, dict) and result.result.get("transport") == "fake":
        return "fake_transport"
    return "called"


def _contract_ids(prompt_asset: dict[str, Any]) -> tuple[str, ...]:
    value = prompt_asset.get("contract_ids")
    if not isinstance(value, (list, tuple)):
        return POLISH_FEEDBACK_GENERATED_CONTRACT_IDS
    result = tuple(text for item in value if (text := _text(item)))
    return result or POLISH_FEEDBACK_GENERATED_CONTRACT_IDS


def _text(value: object) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())
