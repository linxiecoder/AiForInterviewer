from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from typing import Any

from app.application.llm.agent_io import (
    LegacyAgentOutputEnvelope,
)
from app.application.llm.ports import LlmTransport
from app.application.llm.provider_boundary import ProviderRequestValidationError, build_validated_transport_request
from app.application.llm.types import LlmTransportResult
from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
    POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
    POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
    POLISH_FEEDBACK_TASK_TYPE,
)

FEEDBACK_GENERATION_MAX_TOKENS = 4800
_FEEDBACK_PROVIDER_REQUEST_TOP_LEVEL_KEYS = frozenset(
    {
        "task",
        "task_type",
        "feedback_mode",
        "schema_id",
        "schema_version",
        "prompt_version",
        "prompt",
        "output_schema",
        "contract_ids",
        "input_contract",
        "required_json_schema",
        "current_question",
        "current_answer",
        "scoring_rules",
        "evidence",
        "canonical_project_assets",
        "same_question_answers",
        "progress_node_snapshot",
        "job_requirements",
        "resume_projects",
        "output_requirements",
        "feedback_metadata",
    }
)
_PROVIDER_METADATA_FIELDS = frozenset(
    {
        "model_name",
        "prompt_version",
        "schema_id",
        "schema_version",
        "provider_status",
        "provider_model",
        "provider_validation_status",
        "llm_called",
        "request_id",
        "trace_id",
        "trace_refs",
        "raw_io_ref",
    }
)


class FeedbackGenerationAgent:
    def __init__(self, *, transport: LlmTransport) -> None:
        self._transport = transport

    def generate(
        self,
        *,
        prompt_asset: dict[str, Any],
        input_refs: tuple[str, ...],
    ) -> LegacyAgentOutputEnvelope:
        try:
            request = build_validated_transport_request(
                contract_ids=_contract_ids(prompt_asset),
                task_type=_text(prompt_asset.get("task_type")) or POLISH_FEEDBACK_TASK_TYPE,
                input_refs=input_refs,
                evidence_bundle=_provider_prompt(prompt_asset),
                prompt_version=_text(prompt_asset.get("prompt_version")) or POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
                schema_id=_text(prompt_asset.get("schema_id")) or POLISH_FEEDBACK_FINAL_SCHEMA_ID,
                required_evidence_keys=_FEEDBACK_PROVIDER_REQUEST_TOP_LEVEL_KEYS,
                allowed_evidence_keys=_FEEDBACK_PROVIDER_REQUEST_TOP_LEVEL_KEYS,
            )
        except ProviderRequestValidationError as exc:
            return _provider_request_validation_failed(prompt_asset, exc)
        object.__setattr__(request, "max_tokens", FEEDBACK_GENERATION_MAX_TOKENS)
        try:
            with _temporary_transport_max_tokens(self._transport, FEEDBACK_GENERATION_MAX_TOKENS):
                provider_result = self._transport.generate(request)
        except Exception as exc:
            validation_error = _transport_validation_error(exc)
            return LegacyAgentOutputEnvelope(
                task_type=_text(prompt_asset.get("task_type")) or POLISH_FEEDBACK_TASK_TYPE,
                schema_id=_text(prompt_asset.get("schema_id")) or POLISH_FEEDBACK_FINAL_SCHEMA_ID,
                schema_version=_text(prompt_asset.get("schema_version")) or POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
                prompt_version=_text(prompt_asset.get("prompt_version")) or POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
                status="provider_failed",
                validation_errors=(validation_error,),
                metadata={
                    "provider_status": "failed",
                    "provider_error_type": "timeout" if validation_error == "llm_transport_timeout" else exc.__class__.__name__,
                    "llm_called": True,
                },
            )

        return _feedback_output_envelope(provider_result, prompt_asset=prompt_asset)


def _feedback_output_envelope(
    result: LlmTransportResult,
    *,
    prompt_asset: dict[str, Any],
) -> LegacyAgentOutputEnvelope:
    raw_payload = result.result if isinstance(result.result, dict) else {}
    payload, extracted_metadata, extraction_errors = _extract_payload(result)
    provider_status = _provider_status(result, payload)
    metadata = {
        **result.metadata,
        **extracted_metadata,
        "provider_status": provider_status,
        "provider_validation_status": str(result.validation_status),
        "provider_confidence_level": str(result.confidence_level),
        "llm_called": True,
    }
    if extraction_errors or payload is None:
        return LegacyAgentOutputEnvelope(
            task_type=_text(prompt_asset.get("task_type")) or POLISH_FEEDBACK_TASK_TYPE,
            schema_id=_text(raw_payload.get("schema_id")) or _text(prompt_asset.get("schema_id")) or POLISH_FEEDBACK_FINAL_SCHEMA_ID,
            schema_version=_text(raw_payload.get("schema_version"))
            or _text(prompt_asset.get("schema_version"))
            or POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
            prompt_version=_text(raw_payload.get("prompt_version"))
            or _text(prompt_asset.get("prompt_version"))
            or POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
            status="validation_failed",
            validation_errors=extraction_errors,
            low_confidence_flags=tuple(result.low_confidence_flags),
            trace_refs=tuple(result.trace_refs),
            evidence_refs=tuple(result.evidence_refs),
            metadata=metadata,
        )

    low_confidence_flags = tuple(
        dict.fromkeys(
            [
                *result.low_confidence_flags,
                *_string_tuple(payload.get("low_confidence_flags")),
            ]
        )
    )
    evidence_refs = tuple(
        dict.fromkeys(
            [
                *result.evidence_refs,
                *_string_tuple(payload.get("evidence_refs")),
            ]
        )
    )
    return LegacyAgentOutputEnvelope(
        task_type=_text(prompt_asset.get("task_type")) or POLISH_FEEDBACK_TASK_TYPE,
        schema_id=_text(prompt_asset.get("schema_id")) or POLISH_FEEDBACK_FINAL_SCHEMA_ID,
        schema_version=_text(prompt_asset.get("schema_version")) or POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
        prompt_version=_text(prompt_asset.get("prompt_version")) or POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
        status=None,
        payload=payload,
        low_confidence_flags=low_confidence_flags,
        trace_refs=tuple(result.trace_refs),
        evidence_refs=evidence_refs,
        metadata=metadata,
    )


def _extract_payload(result: LlmTransportResult) -> tuple[dict[str, Any] | None, dict[str, Any], tuple[str, ...]]:
    if not isinstance(result.result, dict):
        return None, {}, ("feedback_payload_schema_invalid",)
    raw_payload = dict(result.result)
    extracted_metadata = _extract_provider_metadata(raw_payload)
    for field_name in ("payload", "generated_feedback", "generated_feedback_payload"):
        nested = raw_payload.get(field_name)
        if nested is not None:
            if not isinstance(nested, dict):
                return None, extracted_metadata, ("feedback_payload_schema_invalid",)
            payload = dict(nested)
            extracted_metadata.update(_extract_provider_metadata(payload))
            return payload, extracted_metadata, ()
    payload = dict(raw_payload)
    extracted_metadata.update(_extract_provider_metadata(payload))
    return payload, extracted_metadata, ()


def _extract_provider_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    for field_name in _PROVIDER_METADATA_FIELDS:
        if field_name in payload:
            metadata[field_name] = payload.pop(field_name)
    return metadata


def _provider_status(result: LlmTransportResult, payload: dict[str, Any] | None) -> str:
    if isinstance(payload, dict) and payload.get("transport") == "fake":
        return "fake_transport"
    if isinstance(result.result, dict) and result.result.get("transport") == "fake":
        return "fake_transport"
    status = result.metadata.get("provider_status") if isinstance(result.metadata, dict) else None
    if isinstance(status, str) and status.strip():
        return status.strip()
    return "called"


@contextmanager
def _temporary_transport_max_tokens(transport: LlmTransport, max_tokens: int) -> Iterator[None]:
    settings = getattr(transport, "_settings", None)
    original_settings = settings
    changed = False
    current_max_tokens = getattr(settings, "max_tokens", None)
    if isinstance(current_max_tokens, int) and current_max_tokens > max_tokens:
        try:
            compact_settings = replace(settings, max_tokens=max_tokens)
            setattr(transport, "_settings", compact_settings)
            changed = True
        except (TypeError, AttributeError, ValueError):
            changed = False
    try:
        yield
    finally:
        if changed:
            setattr(transport, "_settings", original_settings)


def _transport_validation_error(exc: Exception) -> str:
    error_type = exc.__class__.__name__.lower()
    message = str(exc).lower()
    if isinstance(exc, TimeoutError) or "timeout" in error_type or "timed out" in message or "超时" in message:
        return "llm_transport_timeout"
    return "llm_transport_generation_failed"


def _provider_prompt(prompt_asset: dict[str, Any]) -> dict[str, Any]:
    provider_prompt = prompt_asset.get("provider_prompt")
    if isinstance(provider_prompt, dict):
        return provider_prompt
    raise ProviderRequestValidationError(("missing_provider_request_key:provider_prompt",))


def _provider_request_validation_failed(
    prompt_asset: dict[str, Any],
    exc: ProviderRequestValidationError,
) -> LegacyAgentOutputEnvelope:
    return LegacyAgentOutputEnvelope(
        task_type=_text(prompt_asset.get("task_type")) or POLISH_FEEDBACK_TASK_TYPE,
        schema_id=_text(prompt_asset.get("schema_id")) or POLISH_FEEDBACK_FINAL_SCHEMA_ID,
        schema_version=_text(prompt_asset.get("schema_version")) or POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
        prompt_version=_text(prompt_asset.get("prompt_version")) or POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
        status="provider_request_invalid",
        validation_errors=("provider_request_validation_failed",),
        metadata={
            "provider_status": "not_called",
            "llm_called": False,
            "provider_request_errors": exc.errors,
        },
    )


def _contract_ids(prompt_asset: dict[str, Any]) -> tuple[str, ...]:
    input_contract = prompt_asset.get("input_contract") if isinstance(prompt_asset.get("input_contract"), dict) else {}
    value = prompt_asset.get("contract_ids")
    if not isinstance(value, (list, tuple)):
        value = input_contract.get("contract_ids")
    if not isinstance(value, (list, tuple)):
        return POLISH_FEEDBACK_FINAL_CONTRACT_IDS
    result = tuple(text for item in value if (text := _text(item)))
    return result or POLISH_FEEDBACK_FINAL_CONTRACT_IDS


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(text for item in value if (text := _text(item)))


def _text(value: object) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())
