from __future__ import annotations

from dataclasses import dataclass, field, fields
from copy import deepcopy
from typing import Any

from app.application.llm.ports import LlmTransport
from app.application.polish.context_hygiene import build_context_hygiene_metadata
from app.application.polish.feedback_agent import (
    FEEDBACK_ANALYSIS_STAGE,
    FEEDBACK_PROJECTION_STAGE,
    FeedbackGenerationAgent,
)
from app.application.polish.feedback_prompt_assets import build_feedback_prompt_asset
from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
    POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
    POLISH_FEEDBACK_FINAL_PAYLOAD_FIELDS,
    POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
    POLISH_FEEDBACK_TASK_TYPE,
)
from app.application.polish.feedback_rules import apply_feedback_core_rules
from app.application.polish.feedback_validation import (
    validate_feedback_candidate_payload,
    validate_final_feedback_payload,
)
from app.application.polish.phase5_evaluation_controls import apply_phase5_evaluation_controls
from app.application.polish.transcript_signal_parser import (
    TranscriptSignalParser,
    structured_answer_to_evaluation_text,
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
    retrieved_rag_chunks: dict[str, Any] = field(default_factory=dict)
    question_metadata: dict[str, Any] = field(default_factory=dict)
    job_snapshot: dict[str, Any] = field(default_factory=dict)
    resume_snapshot: dict[str, Any] = field(default_factory=dict)
    progress_node_snapshot: dict[str, Any] = field(default_factory=dict)
    progress_state: dict[str, Any] = field(default_factory=dict)
    structured_answer: dict[str, Any] = field(default_factory=dict)


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

    def generate_feedback_v1(self, context: FeedbackGenerationContext | dict[str, Any]) -> FeedbackGenerationResult:
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

        evaluation_context, structured_answer_errors = _with_structured_answer(normalized_context)
        if structured_answer_errors:
            return FeedbackGenerationResult(
                succeeded=False,
                payload=None,
                validation_errors=structured_answer_errors,
                metadata=metadata
                | _feedback_context_hygiene_metadata(
                    None,
                    status="blocked",
                    validation_errors=structured_answer_errors,
                )
                | {"provider_status": "not_called", "llm_called": False},
            )
        prompt_asset = build_feedback_prompt_asset(evaluation_context)
        metadata = metadata | {
            "prompt_version": prompt_asset["prompt_version"],
            "schema_id": prompt_asset["schema_id"],
            "schema_version": prompt_asset["schema_version"],
            "structured_answer_parse_status": _structured_parse_status(evaluation_context),
        }
        if self._llm_transport is None:
            return FeedbackGenerationResult(
                succeeded=False,
                payload=None,
                validation_errors=("llm_transport_unavailable",),
                metadata=metadata
                | _feedback_context_hygiene_metadata(
                    prompt_asset,
                    status="blocked",
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
                    status="blocked",
                    validation_errors=("fake_transport_not_runtime_provider",),
                )
                | {"provider_status": "fake_transport", "llm_called": False},
            )

        agent = FeedbackGenerationAgent(transport=self._llm_transport)
        agent_result = agent.invoke_provider_v1(
            prompt_asset=prompt_asset,
            input_refs=_input_refs(evaluation_context),
            stage=FEEDBACK_ANALYSIS_STAGE,
            thinking_enabled=True,
        )
        agent_metadata = metadata | _agent_envelope_metadata(agent_result)
        provider_status = str(agent_metadata.get("provider_status") or "not_called")
        llm_called = bool(agent_metadata.get("llm_called", False))
        analysis_stage = _stage_diagnostic(
            FEEDBACK_ANALYSIS_STAGE,
            agent_metadata,
            validation_status="failed" if not agent_result.succeeded else "called",
            validation_errors=agent_result.validation_errors,
        )
        if not agent_result.succeeded:
            return FeedbackGenerationResult(
                succeeded=False,
                payload=None,
                validation_errors=agent_result.validation_errors,
                low_confidence_flags=agent_result.low_confidence_flags,
                metadata=agent_metadata
                | _feedback_context_hygiene_metadata(
                    prompt_asset,
                    status="blocked",
                    validation_errors=agent_result.validation_errors,
                )
                | {
                    "validation_stage": FEEDBACK_ANALYSIS_STAGE,
                    "stage": FEEDBACK_ANALYSIS_STAGE,
                    "candidate_valid": False,
                    "llm_output_validation_status": "invalid",
                    "provider_status": provider_status,
                    "llm_called": llm_called,
                    "generation_stages": [analysis_stage],
                },
            )

        candidate_payload, validation_errors = validate_feedback_candidate_payload(
            agent_result.payload,
            expected_progress_state_ref=_progress_state_ref(evaluation_context),
        )
        analysis_stage = _stage_diagnostic(
            FEEDBACK_ANALYSIS_STAGE,
            agent_metadata,
            validation_status="invalid" if validation_errors else "valid",
            validation_errors=validation_errors,
        )
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
                    validation_errors=validation_errors,
                )
                | {
                    "validation_stage": FEEDBACK_ANALYSIS_STAGE,
                    "stage": FEEDBACK_ANALYSIS_STAGE,
                    "candidate_valid": False,
                    "llm_output_validation_status": "invalid",
                    "provider_status": provider_status,
                    "llm_called": llm_called,
                    "generation_stages": [analysis_stage],
                },
            )

        assert candidate_payload is not None
        ruled_payload = apply_feedback_core_rules(candidate_payload, evaluation_context)
        controlled_payload = apply_phase5_evaluation_controls(
            ruled_payload,
        )
        server_projected_payload = self._build_final_payload(
            ruled_payload=controlled_payload,
            prompt_asset=prompt_asset,
            agent_trace_refs=agent_result.trace_refs,
            agent_low_confidence_flags=agent_result.low_confidence_flags,
        )
        projection_prompt_asset = _build_projection_prompt_asset(
            prompt_asset,
            safe_candidate_payload=controlled_payload,
            server_projected_payload=server_projected_payload,
        )
        projection_result = agent.invoke_provider_v1(
            prompt_asset=projection_prompt_asset,
            input_refs=_input_refs(evaluation_context),
            stage=FEEDBACK_PROJECTION_STAGE,
            thinking_enabled=False,
        )
        projection_metadata = metadata | _agent_envelope_metadata(projection_result)
        projection_stage = _stage_diagnostic(
            FEEDBACK_PROJECTION_STAGE,
            projection_metadata,
            validation_status="failed" if not projection_result.succeeded else "called",
            validation_errors=projection_result.validation_errors,
        )
        projection_provider_status = str(projection_metadata.get("provider_status") or "not_called")
        projection_llm_called = bool(projection_metadata.get("llm_called", False))
        generation_stages = [analysis_stage, projection_stage]
        if not projection_result.succeeded:
            return FeedbackGenerationResult(
                succeeded=False,
                payload=None,
                validation_errors=projection_result.validation_errors,
                low_confidence_flags=tuple(
                    dict.fromkeys((*agent_result.low_confidence_flags, *projection_result.low_confidence_flags))
                ),
                trace_refs=tuple(dict.fromkeys((*agent_result.trace_refs, *projection_result.trace_refs))),
                metadata=projection_metadata
                | _feedback_context_hygiene_metadata(
                    prompt_asset,
                    status="blocked",
                    validation_errors=projection_result.validation_errors,
                )
                | {
                    "validation_stage": FEEDBACK_PROJECTION_STAGE,
                    "stage": FEEDBACK_PROJECTION_STAGE,
                    "candidate_valid": True,
                    "llm_output_validation_status": "invalid",
                    "provider_status": projection_provider_status,
                    "llm_called": llm_called or projection_llm_called,
                    "generation_stages": generation_stages,
                },
            )

        projected_payload = _projected_payload_with_server_facts(
            projection_result.payload,
            server_projected_payload=server_projected_payload,
            projection_trace_refs=projection_result.trace_refs,
        )
        normalized_payload, validation_errors = validate_final_feedback_payload(
            projected_payload,
            require_feedback_id=False,
        )
        projection_stage = _stage_diagnostic(
            FEEDBACK_PROJECTION_STAGE,
            projection_metadata,
            validation_status="invalid" if validation_errors else "valid",
            validation_errors=("json_projection", *validation_errors) if validation_errors else (),
        )
        generation_stages = [analysis_stage, projection_stage]
        if validation_errors:
            projection_errors = ("json_projection", *validation_errors)
            return FeedbackGenerationResult(
                succeeded=False,
                payload=None,
                validation_errors=projection_errors,
                low_confidence_flags=tuple(_string_tuple(normalized_payload.get("low_confidence_flags")))
                if normalized_payload is not None
                else tuple(),
                trace_refs=_string_tuple(normalized_payload.get("trace_refs")) if normalized_payload is not None else (),
                metadata=projection_metadata
                | _feedback_context_hygiene_metadata(
                    prompt_asset,
                    status="blocked",
                    validation_errors=projection_errors,
                )
                | {
                    "validation_stage": FEEDBACK_PROJECTION_STAGE,
                    "stage": FEEDBACK_PROJECTION_STAGE,
                    "candidate_valid": True,
                    "llm_output_validation_status": "invalid",
                    "provider_status": projection_provider_status,
                    "llm_called": llm_called or projection_llm_called,
                    "generation_stages": generation_stages,
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
            metadata=projection_metadata
            | _feedback_context_hygiene_metadata(prompt_asset, status="clean")
            | {
                "validation_stage": FEEDBACK_PROJECTION_STAGE,
                "stage": FEEDBACK_PROJECTION_STAGE,
                "candidate_valid": True,
                "llm_output_validation_status": "valid",
                "provider_status": projection_provider_status,
                "llm_called": llm_called or projection_llm_called,
                "generation_stages": generation_stages,
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


def _build_projection_prompt_asset(
    prompt_asset: dict[str, Any],
    *,
    safe_candidate_payload: dict[str, Any],
    server_projected_payload: dict[str, Any],
) -> dict[str, Any]:
    projection_prompt = {
        "task": "polish_feedback_json_projection_v1",
        "task_type": POLISH_FEEDBACK_TASK_TYPE,
        "feedback_mode": "final_json_projection",
        "schema_id": _clean(prompt_asset.get("schema_id"), max_chars=120),
        "schema_version": _clean(prompt_asset.get("schema_version"), max_chars=40),
        "prompt_version": _clean(prompt_asset.get("prompt_version"), max_chars=120),
        "output_schema": {
            "schema_id": POLISH_FEEDBACK_FINAL_SCHEMA_ID,
            "schema_version": POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
            "fields": list(POLISH_FEEDBACK_FINAL_PAYLOAD_FIELDS),
            "status_allowed": ["generated", "partial", "low_confidence", "validation_failed"],
            "status_forbidden": ["generation_failed"],
        },
        "contract_ids": list(POLISH_FEEDBACK_FINAL_CONTRACT_IDS),
        "input_contract": {
            "source_stage": FEEDBACK_ANALYSIS_STAGE,
            "projection_stage": FEEDBACK_PROJECTION_STAGE,
            "raw_model_io_storage": False,
            "raw_candidate_storage": False,
            "candidate_is_safe_summary": True,
        },
        "required_json_schema": {
            "required_fields": list(POLISH_FEEDBACK_FINAL_PAYLOAD_FIELDS),
            "forbidden_statuses": ["generation_failed"],
            "forbidden_metadata_fields": [
                "generation_stages",
                "stage",
                "finish_reason",
                "completion_tokens",
                "reasoning_tokens",
                "provider_error_type",
                "thinking_enabled",
            ],
        },
        "safe_candidate_summary": deepcopy(safe_candidate_payload),
        "server_facts": {
            "schema_id": POLISH_FEEDBACK_FINAL_SCHEMA_ID,
            "schema_version": POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
            "contract_ids": list(POLISH_FEEDBACK_FINAL_CONTRACT_IDS),
            "default_final_payload": deepcopy(server_projected_payload),
        },
        "projection_contract": {
            "mode": "strict_json_projection_only",
            "analysis_forbidden": True,
            "thinking_required": False,
            "use_only_safe_candidate_summary_and_server_facts": True,
            "do_not_emit_failure_payload": True,
        },
        "feedback_metadata": {
            "stage": FEEDBACK_PROJECTION_STAGE,
            "source_stage": FEEDBACK_ANALYSIS_STAGE,
            "candidate_field_count": len(safe_candidate_payload),
            "final_field_count": len(POLISH_FEEDBACK_FINAL_PAYLOAD_FIELDS),
        },
    }
    return {
        "task_type": POLISH_FEEDBACK_TASK_TYPE,
        "prompt_version": _clean(prompt_asset.get("prompt_version"), max_chars=120)
        or POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
        "schema_id": POLISH_FEEDBACK_FINAL_SCHEMA_ID,
        "schema_version": POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
        "contract_ids": list(POLISH_FEEDBACK_FINAL_CONTRACT_IDS),
        "prompt": "Project the safe feedback candidate into the final Polish feedback JSON contract.",
        "input_contract": projection_prompt["input_contract"],
        "output_schema": projection_prompt["output_schema"],
        "feedback_mode": "final_json_projection",
        "provider_prompt": projection_prompt,
    }


def _projected_payload_with_server_facts(
    payload: object,
    *,
    server_projected_payload: dict[str, Any],
    projection_trace_refs: tuple[str, ...],
) -> object:
    if not isinstance(payload, dict):
        return payload
    projected = deepcopy(payload)
    for field_name in ("schema_id", "schema_version", "contract_ids", "feedback_id"):
        if field_name not in projected:
            projected[field_name] = deepcopy(server_projected_payload.get(field_name))
    projected["trace_refs"] = list(
        dict.fromkeys(
            (
                *_string_tuple(server_projected_payload.get("trace_refs")),
                *_string_tuple(projected.get("trace_refs")),
                *projection_trace_refs,
            )
        )
    )
    server_metadata = server_projected_payload.get("feedback_metadata")
    projected_metadata = projected.get("feedback_metadata")
    metadata = dict(server_metadata) if isinstance(server_metadata, dict) else {}
    if isinstance(projected_metadata, dict):
        metadata.update(projected_metadata)
    for field_name in _FINAL_PAYLOAD_DIAGNOSTIC_METADATA_FIELDS:
        metadata.pop(field_name, None)
    projected["feedback_metadata"] = metadata
    return projected


_FINAL_PAYLOAD_DIAGNOSTIC_METADATA_FIELDS = frozenset(
    {
        "generation_stages",
        "stage",
        "finish_reason",
        "max_tokens",
        "reasoning_tokens",
        "completion_tokens",
        "prompt_tokens",
        "total_tokens",
        "provider_error_type",
        "thinking_enabled",
    }
)


def _stage_diagnostic(
    stage: str,
    metadata: dict[str, Any],
    *,
    validation_status: str,
    validation_errors: tuple[str, ...],
) -> dict[str, Any]:
    source = metadata if isinstance(metadata, dict) else {}
    diagnostic: dict[str, Any] = {
        "stage": stage,
        "validation_status": validation_status,
        "finish_reason": _clean(source.get("finish_reason"), max_chars=80) or None,
        "completion_tokens": _metadata_int(source.get("completion_tokens")),
        "reasoning_tokens": _metadata_int(source.get("reasoning_tokens")),
    }
    provider_status = _clean(source.get("provider_status"), max_chars=80)
    if provider_status:
        diagnostic["provider_status"] = provider_status
    provider_error_type = _clean(source.get("provider_error_type"), max_chars=120)
    if provider_error_type:
        diagnostic["provider_error_type"] = provider_error_type
    thinking_enabled = source.get("thinking_enabled")
    if isinstance(thinking_enabled, bool):
        diagnostic["thinking_enabled"] = thinking_enabled
    for field_name in ("max_tokens", "prompt_tokens", "total_tokens"):
        value = _metadata_int(source.get(field_name))
        if value is not None:
            diagnostic[field_name] = value
    if validation_errors:
        safe_errors = [error for error in _string_tuple(validation_errors) if error]
        diagnostic["failure_reason"] = safe_errors[0] if safe_errors else "validation_failed"
        diagnostic["validation_errors"] = safe_errors
    elif provider_error_type:
        diagnostic["failure_reason"] = provider_error_type
    return diagnostic


def _metadata_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


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


def _with_structured_answer(
    context: FeedbackGenerationContext | dict[str, Any],
) -> tuple[dict[str, Any], tuple[str, ...]]:
    context_dict = _context_to_dict(context)
    raw_answer_text = _value(context, "answer_text")
    try:
        structured_answer = TranscriptSignalParser().parse(raw_answer_text).to_dict()
    except Exception:
        return context_dict, ("structured_answer_parse_failed",)
    context_dict["structured_answer"] = structured_answer
    context_dict["answer_text"] = structured_answer_to_evaluation_text(structured_answer)
    return context_dict, ()


def _context_to_dict(context: FeedbackGenerationContext | dict[str, Any]) -> dict[str, Any]:
    if isinstance(context, dict):
        return dict(context)
    return {field.name: getattr(context, field.name) for field in fields(FeedbackGenerationContext)}


def _structured_parse_status(context: dict[str, Any]) -> str:
    structured_answer = context.get("structured_answer")
    if not isinstance(structured_answer, dict):
        return ""
    return _clean(structured_answer.get("parse_status"), max_chars=80)


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


def _progress_state_ref(context: FeedbackGenerationContext | dict[str, Any]) -> str | None:
    value = context.get("progress_state") if isinstance(context, dict) else getattr(context, "progress_state", {})
    if not isinstance(value, dict):
        return None
    progress_state_ref = _clean(value.get("progress_state_ref"), max_chars=120)
    if progress_state_ref:
        return progress_state_ref
    current_priority = value.get("current_priority")
    if isinstance(current_priority, dict):
        return _clean(current_priority.get("progress_node_ref") or current_priority.get("node_ref"), max_chars=120) or None
    return None


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
