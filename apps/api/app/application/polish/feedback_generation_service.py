from __future__ import annotations

from dataclasses import dataclass, field
from copy import deepcopy
from typing import Any

from app.application.llm.ports import LlmTransport
from app.application.polish.context_hygiene import build_context_hygiene_metadata
from app.application.polish.feedback_agent import FeedbackGenerationAgent
from app.application.polish.feedback_prompt_assets import build_feedback_prompt_asset
from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
    POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
    POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
    POLISH_FEEDBACK_TASK_TYPE,
)
from app.application.polish.feedback_rules import apply_feedback_core_rules
from app.application.polish.feedback_validation import (
    validate_feedback_candidate_payload,
    validate_final_feedback_payload,
)


FEEDBACK_GENERATION_SERVICE_VERSION = "polish_feedback_generation_service.v1"
_REQUIRED_CONTEXT_FIELDS = (
    "owner_id",
    "actor_id",
    "session_id",
    "question_id",
    "answer_id",
    "question_text",
    "answer_text",
)


@dataclass(frozen=True)
class FeedbackGenerationContext:
    owner_id: str
    actor_id: str
    session_id: str
    question_id: str
    answer_id: str
    question_text: str
    answer_text: str
    answer_round: int | None = None
    polish_theme: str = ""
    progress_node_ref: str = ""
    question_sources: tuple[dict[str, Any], ...] = ()
    evidence_refs: tuple[str, ...] = ()
    same_question_answers: tuple[dict[str, Any], ...] = ()
    same_project_turns: tuple[dict[str, Any], ...] = ()
    session_recent_turns: tuple[dict[str, Any], ...] = ()
    project_asset_summaries: tuple[dict[str, Any], ...] = ()
    canonical_project_assets: dict[str, Any] = field(default_factory=dict)
    question_metadata: dict[str, Any] = field(default_factory=dict)
    job_snapshot: dict[str, Any] = field(default_factory=dict)
    resume_snapshot: dict[str, Any] = field(default_factory=dict)
    progress_node_snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FeedbackGenerationResult:
    succeeded: bool
    payload: dict[str, Any] | None
    validation_errors: tuple[str, ...] = ()
    low_confidence_flags: tuple[str, ...] = ()
    trace_refs: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


class FeedbackGenerationService:
    def __init__(self, *, llm_transport: LlmTransport | None = None) -> None:
        self._llm_transport = llm_transport

    def generate(self, context: FeedbackGenerationContext | dict[str, Any]) -> FeedbackGenerationResult:
        normalized_context, context_errors = _normalize_context(context)
        metadata = _base_metadata()
        if context_errors:
            return FeedbackGenerationResult(
                succeeded=False,
                payload=None,
                validation_errors=context_errors,
                metadata=metadata
                | _feedback_context_hygiene_metadata(
                    None,
                    status="blocked",
                    validation_errors=context_errors,
                )
                | {"provider_status": "not_called", "llm_called": False},
            )

        prompt_asset = build_feedback_prompt_asset(normalized_context)
        metadata = metadata | {
            "prompt_version": prompt_asset["prompt_version"],
            "schema_id": prompt_asset["schema_id"],
            "schema_version": prompt_asset["schema_version"],
        }
        if self._llm_transport is None:
            return FeedbackGenerationResult(
                succeeded=False,
                payload=None,
                validation_errors=("llm_transport_unavailable",),
                metadata=metadata
                | _feedback_context_hygiene_metadata(
                    prompt_asset,
                    status="fallback",
                    fallback_reason="llm_transport_unavailable",
                    validation_errors=("llm_transport_unavailable",),
                )
                | {"provider_status": "not_configured", "llm_called": False},
            )
        if _is_fake_transport(self._llm_transport):
            return FeedbackGenerationResult(
                succeeded=False,
                payload=None,
                validation_errors=("fake_transport_not_runtime_provider",),
                metadata=metadata
                | _feedback_context_hygiene_metadata(
                    prompt_asset,
                    status="fallback",
                    fallback_reason="fake_transport_not_runtime_provider",
                    validation_errors=("fake_transport_not_runtime_provider",),
                )
                | {"provider_status": "fake_transport", "llm_called": False},
            )

        agent_result = FeedbackGenerationAgent(transport=self._llm_transport).generate(
            prompt_asset=prompt_asset,
            input_refs=_input_refs(normalized_context),
        )
        agent_metadata = metadata | _agent_envelope_metadata(agent_result)
        provider_status = str(agent_metadata.get("provider_status") or "not_called")
        llm_called = bool(agent_metadata.get("llm_called", False))
        if not agent_result.succeeded:
            return FeedbackGenerationResult(
                succeeded=False,
                payload=None,
                validation_errors=agent_result.validation_errors,
                low_confidence_flags=agent_result.low_confidence_flags,
                metadata=agent_metadata
                | _feedback_context_hygiene_metadata(
                    prompt_asset,
                    status="fallback",
                    fallback_reason=agent_result.validation_errors[0]
                    if agent_result.validation_errors
                    else provider_status,
                    validation_errors=agent_result.validation_errors,
                )
                | {
                    "validation_stage": "candidate",
                    "candidate_valid": False,
                    "llm_output_validation_status": "invalid",
                    "provider_status": provider_status,
                    "llm_called": llm_called,
                },
            )

        candidate_payload, validation_errors = validate_feedback_candidate_payload(agent_result.payload)
        if validation_errors:
            candidate_payload_metadata = agent_result.payload if isinstance(agent_result.payload, dict) else {}
            return FeedbackGenerationResult(
                succeeded=False,
                payload=None,
                validation_errors=validation_errors,
                low_confidence_flags=tuple(
                    _string_tuple(
                        (*agent_result.low_confidence_flags, *_string_tuple(candidate_payload_metadata.get("low_confidence_flags")))
                    )
                ),
                trace_refs=_string_tuple(agent_result.evidence_refs),
                metadata=agent_metadata
                | _feedback_context_hygiene_metadata(
                    prompt_asset,
                    status="blocked",
                    fallback_reason=validation_errors[0] if validation_errors else None,
                    validation_errors=validation_errors,
                )
                | {
                    "validation_stage": "candidate",
                    "candidate_valid": False,
                    "llm_output_validation_status": "invalid",
                    "provider_status": provider_status,
                    "llm_called": llm_called,
                },
            )

        assert candidate_payload is not None
        ruled_payload = apply_feedback_core_rules(candidate_payload, normalized_context)
        final_payload = self._build_final_payload(
            ruled_payload=ruled_payload,
            prompt_asset=prompt_asset,
            agent_trace_refs=agent_result.trace_refs,
            agent_low_confidence_flags=agent_result.low_confidence_flags,
        )
        normalized_payload, validation_errors = validate_final_feedback_payload(final_payload, require_feedback_id=False)
        if validation_errors:
            return FeedbackGenerationResult(
                succeeded=False,
                payload=None,
                validation_errors=validation_errors,
                low_confidence_flags=tuple(_string_tuple(normalized_payload.get("low_confidence_flags")))
                if normalized_payload is not None
                else tuple(),
                trace_refs=_string_tuple(normalized_payload.get("trace_refs")) if normalized_payload is not None else (),
                metadata=agent_metadata
                | _feedback_context_hygiene_metadata(
                    prompt_asset,
                    status="blocked",
                    fallback_reason=validation_errors[0] if validation_errors else None,
                    validation_errors=validation_errors,
                )
                | {
                    "validation_stage": "final",
                    "candidate_valid": True,
                    "llm_output_validation_status": "invalid",
                    "provider_status": provider_status,
                    "llm_called": llm_called,
                },
            )

        trace_refs = _string_tuple(normalized_payload.get("trace_refs"))
        low_confidence_flags = _string_tuple(normalized_payload.get("low_confidence_flags"))
        return FeedbackGenerationResult(
            succeeded=True,
            payload=normalized_payload,
            validation_errors=(),
            low_confidence_flags=low_confidence_flags,
            trace_refs=trace_refs,
            metadata=agent_metadata
            | _feedback_context_hygiene_metadata(prompt_asset, status="clean")
            | {
                "validation_stage": "final",
                "candidate_valid": True,
                "llm_output_validation_status": "valid",
                "provider_status": provider_status,
                "llm_called": llm_called,
            },
        )


    def _build_final_payload(
        self,
        *,
        ruled_payload: dict[str, Any],
        prompt_asset: dict[str, Any],
        agent_trace_refs: tuple[str, ...],
        agent_low_confidence_flags: tuple[str, ...],
    ) -> dict[str, Any]:
        trace_refs = _string_tuple(agent_trace_refs) + _string_tuple(ruled_payload.get("trace_refs"))
        final_payload: dict[str, Any] = {
            "schema_id": _clean(prompt_asset.get("schema_id"), max_chars=120),
            "schema_version": _clean(prompt_asset.get("schema_version"), max_chars=40),
            "status": _feedback_status(ruled_payload),
            "contract_ids": list(POLISH_FEEDBACK_FINAL_CONTRACT_IDS),
            "feedback_id": "",
            "feedback_text": _clean(ruled_payload.get("feedback_text"), max_chars=12000),
            "answer_summary": _clean(ruled_payload.get("answer_summary"), max_chars=4000),
            "score_result": deepcopy(ruled_payload.get("score_result")),
            "loss_points": deepcopy(ruled_payload.get("loss_points")),
            "reference_answer": deepcopy(ruled_payload.get("reference_answer")),
            "asset_consistency_check": deepcopy(ruled_payload.get("asset_consistency_check")),
            "answer_coverage": deepcopy(ruled_payload.get("answer_coverage")),
            "answer_change_analysis": deepcopy(ruled_payload.get("answer_change_analysis")),
            "feedback_cards": deepcopy(ruled_payload.get("feedback_cards")),
            "next_recommended_actions": list(_string_tuple(ruled_payload.get("next_recommended_actions"))),
            "low_confidence_flags": tuple(
                _string_tuple(
                    (
                        *agent_low_confidence_flags,
                        *_string_tuple(ruled_payload.get("low_confidence_flags")),
                    )
                )
            ),
            "trace_refs": list(dict.fromkeys(trace_refs)),
            "feedback_metadata": _final_feedback_metadata(ruled_payload)
            | _feedback_context_hygiene_metadata(prompt_asset, status="clean"),
        }
        return final_payload


def _feedback_status(ruled_payload: dict[str, Any]) -> str:
    status = _clean(ruled_payload.get("status"), max_chars=40)
    if status in {"generated", "partial", "low_confidence", "validation_failed"}:
        return status
    metadata = ruled_payload.get("feedback_metadata")
    validation_warnings = metadata.get("validation_warnings") if isinstance(metadata, dict) else None
    if isinstance(validation_warnings, list) and validation_warnings:
        return "partial"
    return "generated"


def _final_feedback_metadata(ruled_payload: dict[str, Any]) -> dict[str, Any]:
    metadata = ruled_payload.get("feedback_metadata")
    if isinstance(metadata, dict):
        return dict(metadata)
    return {}


def _agent_envelope_metadata(agent_result: object) -> dict[str, Any]:
    if not hasattr(agent_result, "to_payload_dict"):
        return {}
    envelope_payload = agent_result.to_payload_dict()
    metadata = envelope_payload.get("metadata")
    if not isinstance(metadata, dict):
        return {}
    return metadata


def _is_fake_transport(transport: object) -> bool:
    return getattr(transport, "status", None) == "deterministic_fake_only"


def _base_metadata() -> dict[str, Any]:
    return {
        "service_version": FEEDBACK_GENERATION_SERVICE_VERSION,
        "task_type": POLISH_FEEDBACK_TASK_TYPE,
        "prompt_version": POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
        "schema_id": POLISH_FEEDBACK_FINAL_SCHEMA_ID,
        "schema_version": POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
        "contract_ids": list(POLISH_FEEDBACK_FINAL_CONTRACT_IDS),
    }


def _feedback_context_hygiene_metadata(
    prompt_asset: dict[str, Any] | None,
    *,
    status: str,
    fallback_reason: str | None = None,
    validation_errors: tuple[str, ...] = (),
) -> dict[str, Any]:
    provider_prompt = (
        prompt_asset.get("provider_prompt")
        if isinstance(prompt_asset, dict) and isinstance(prompt_asset.get("provider_prompt"), dict)
        else {}
    )
    input_contract = provider_prompt.get("input_contract") if isinstance(provider_prompt, dict) else {}
    provider_metadata = provider_prompt.get("feedback_metadata") if isinstance(provider_prompt, dict) else {}
    input_contract = input_contract if isinstance(input_contract, dict) else {}
    provider_metadata = provider_metadata if isinstance(provider_metadata, dict) else {}
    safe_context_metadata = {
        "raw_model_io_storage": bool(input_contract.get("raw_model_io_storage", False)),
        "answer_text_policy": _clean(input_contract.get("answer_text_policy"), max_chars=120),
        "answer_text_max_chars": int(input_contract.get("answer_text_max_chars") or 0),
        "answer_text_is_bounded": bool(input_contract.get("answer_text_is_bounded", False)),
        "full_answer_forbidden": bool(input_contract.get("full_answer_forbidden", True)),
        "context_compaction_applied": bool(provider_metadata.get("context_compaction_applied", False)),
        "evidence_item_count": int(provider_metadata.get("evidence_item_count") or 0),
        "context_char_count": int(provider_metadata.get("prompt_char_count") or 0),
    }
    return build_context_hygiene_metadata(
        status=status,
        safe_context_metadata=safe_context_metadata,
        fallback_reason=fallback_reason,
        validation_errors=validation_errors,
    ).to_dict()


def _normalize_context(
    context: FeedbackGenerationContext | dict[str, Any],
) -> tuple[FeedbackGenerationContext | dict[str, Any], tuple[str, ...]]:
    if isinstance(context, FeedbackGenerationContext):
        missing = tuple(field_name for field_name in _REQUIRED_CONTEXT_FIELDS if not _clean(getattr(context, field_name)))
        if missing:
            return context, tuple(f"context_{field_name}_required" for field_name in missing)
        return context, ()
    if not isinstance(context, dict):
        return {}, ("feedback_context_invalid",)
    missing = tuple(field_name for field_name in _REQUIRED_CONTEXT_FIELDS if not _clean(context.get(field_name)))
    if missing:
        return context, tuple(f"context_{field_name}_required" for field_name in missing)
    return context, ()


def _input_refs(context: FeedbackGenerationContext | dict[str, Any]) -> tuple[str, ...]:
    refs = (
        _value(context, "session_id"),
        _value(context, "question_id"),
        _value(context, "answer_id"),
        _value(context, "progress_node_ref"),
        *_list_values(context, "evidence_refs"),
        *_canonical_asset_refs(context),
    )
    return tuple(ref for ref in refs if ref)


def _canonical_asset_refs(context: FeedbackGenerationContext | dict[str, Any]) -> tuple[str, ...]:
    value = context.get("canonical_project_assets") if isinstance(context, dict) else getattr(context, "canonical_project_assets", {})
    if not isinstance(value, dict):
        return ()
    items = value.get("items")
    if not isinstance(items, list):
        return ()
    refs: list[str] = []
    for item in items[:5]:
        if not isinstance(item, dict):
            continue
        asset_id = _clean(item.get("asset_id"))
        if asset_id:
            refs.append(asset_id)
    return tuple(refs)


def _value(context: FeedbackGenerationContext | dict[str, Any], field_name: str) -> str:
    if isinstance(context, dict):
        return _clean(context.get(field_name))
    return _clean(getattr(context, field_name, None))


def _list_values(context: FeedbackGenerationContext | dict[str, Any], field_name: str) -> tuple[str, ...]:
    value = context.get(field_name) if isinstance(context, dict) else getattr(context, field_name, ())
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(text for item in value if (text := _clean(item)))


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(text for item in value if (text := _clean(item)))


def _clean(value: object, *, max_chars: int = 240) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text
