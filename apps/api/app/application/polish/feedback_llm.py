"""LLM wrapper for polish answer feedback with deterministic fallback."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import os
from typing import Any

from app.application.polish.feedback_contracts import (
    FEEDBACK_SCHEMA_ID,
    FEEDBACK_SCHEMA_VERSION,
    FeedbackInput,
    RetryFeedbackInput,
)
from app.application.polish.feedback_prompts import (
    POLISH_ANSWER_FEEDBACK_CONTRACT_IDS,
    POLISH_ANSWER_FEEDBACK_PROMPT_VERSION,
    POLISH_ANSWER_FEEDBACK_SCHEMA_VERSION,
    POLISH_ANSWER_FEEDBACK_TASK_TYPE,
    build_polish_feedback_prompt_bundle,
)
from app.application.polish.feedback_quality import (
    compute_score_result_from_dimensions,
    normalize_feedback_payload,
    validate_feedback_consistency,
)
from app.infrastructure.llm.errors import (
    LlmTransportConfigurationError,
    LlmTransportError,
    LlmTransportResponseError,
    LlmTransportUnavailableError,
)
from app.infrastructure.llm.ports import LlmTransport
from app.infrastructure.llm.types import LlmTransportRequest, LlmTransportResult


FEEDBACK_LLM_ENABLED_ENV = "AIFI_POLISH_FEEDBACK_LLM_ENABLED"
FEEDBACK_REAL_PROVIDER_ENABLED_ENV = "AIFI_POLISH_FEEDBACK_REAL_PROVIDER_ENABLED"

FEEDBACK_GENERATION_MODE_DETERMINISTIC = "deterministic_structured"
FEEDBACK_GENERATION_MODE_ACCEPTED = "llm_accepted"
FEEDBACK_GENERATION_MODE_FALLBACK = "llm_fallback"

LLM_OUTPUT_VALIDATION_STATUS_NOT_REQUESTED = "not_requested"
LLM_OUTPUT_VALIDATION_STATUS_VALID = "valid"
LLM_OUTPUT_VALIDATION_STATUS_SCHEMA_INVALID = "schema_invalid"
LLM_OUTPUT_VALIDATION_STATUS_CONSISTENCY_INVALID = "consistency_invalid"

CONSISTENCY_VALIDATION_STATUS_NOT_REQUESTED = "not_requested"
CONSISTENCY_VALIDATION_STATUS_VALID = "valid"
CONSISTENCY_VALIDATION_STATUS_INVALID = "invalid"

FALLBACK_FEATURE_DISABLED = "feature_disabled"
FALLBACK_REAL_PROVIDER_DISABLED = "real_provider_disabled"
FALLBACK_PROVIDER_UNAVAILABLE = "provider_unavailable"
FALLBACK_PROVIDER_TIMEOUT = "provider_timeout"
FALLBACK_TRANSPORT_CONFIGURATION_ERROR = "transport_configuration_error"
FALLBACK_SCHEMA_INVALID = "schema_invalid"
FALLBACK_CONSISTENCY_INVALID = "consistency_invalid"
FALLBACK_SCORE_DIMENSION_MISMATCH = "score_dimension_mismatch"
FALLBACK_RAW_PAYLOAD_LEAK = "raw_payload_leak"
FALLBACK_REPAIR_FAILED = "repair_failed"
FALLBACK_RETRY_DELTA_INVALID = "retry_delta_invalid"

_TRUTHY = {"1", "true", "yes", "y", "on"}
_REQUIRED_OUTPUT_FIELDS = (
    "schema_id",
    "schema_version",
    "status",
    "feedback_summary",
    "answer_diagnosis",
    "scoring_dimensions",
    "score_result",
    "positive_evidence_points",
    "loss_points",
    "missing_answer_dimensions",
    "p7_reference_answer",
    "reference_answer_requirements",
    "oral_script",
    "oral_script_requirements",
    "knowledge_points",
    "technical_principles",
    "technical_gaps",
    "communication_gaps",
    "next_recommended_actions",
    "low_confidence_flags",
    "feedback_metadata",
)
_RETRY_OUTPUT_FIELDS = (
    "score_delta",
    "dimension_delta",
    "improved_points",
    "remaining_gaps",
    "repeated_loss_points",
    "regressed_points",
    "mastery_status",
    "should_continue_same_question",
    "should_generate_next_question",
    "next_retry_focus",
    "updated_reference_answer",
    "updated_oral_script",
)
_FORBIDDEN_OUTPUT_KEYS = {
    "raw_prompt",
    "prompt",
    "system_prompt",
    "completion",
    "raw_completion",
    "provider_payload",
    "raw_provider_payload",
    "provider_response",
    "raw_provider_response",
    "full_evidence_text",
    "raw_evidence_text",
    "hidden_rubric",
    "hidden_scoring_rules",
    "pass_probability",
    "pass_prob",
    "precise_pass_probability",
    "unsupported_user_fact",
    "unsupported_user_facts",
    "fabricated_user_fact",
    "fabricated_user_facts",
    "formal_weakness",
    "formal_asset",
}
_FORBIDDEN_TEXT_MARKERS = (
    "raw_prompt",
    "raw prompt",
    "system_prompt",
    "system prompt",
    "raw_completion",
    "raw completion",
    "provider_payload",
    "provider payload",
    "provider_response",
    "provider response",
    "full_evidence_text",
    "raw_evidence_text",
    "hidden_rubric",
    "hidden rubric",
    "hidden_scoring_rules",
    "hidden scoring rules",
    "pass_probability",
    "precise_pass_probability",
    "pass probability",
    "unsupported_user_fact",
    "unsupported user fact",
    "fabricated_user_fact",
    "fabricated user fact",
    "api_key",
    "api key",
    "bearer ",
    "cookie=",
    "cookie:",
    "set-cookie",
    "token=",
    "token:",
    "secret=",
    "secret:",
)


@dataclass(frozen=True)
class PolishFeedbackLlmResult:
    feedback_payload: dict[str, Any]
    llm_generation_mode: str
    llm_output_validation_status: str
    consistency_validation_status: str
    fallback_reason: str | None
    repair_attempted: bool = False
    validation_errors: tuple[dict[str, str], ...] = ()


class PolishFeedbackLlmService:
    def __init__(self, transport: LlmTransport | None) -> None:
        self._transport = transport

    def generate_with_llm_or_fallback(
        self,
        *,
        feedback_input: FeedbackInput,
        deterministic_payload: dict[str, Any],
    ) -> PolishFeedbackLlmResult:
        provider_summary = _provider_summary(self._transport)
        if not should_enable_feedback_llm():
            return _fallback_result(
                deterministic_payload,
                mode=FEEDBACK_GENERATION_MODE_DETERMINISTIC,
                fallback_reason=FALLBACK_FEATURE_DISABLED,
                llm_validation_status=LLM_OUTPUT_VALIDATION_STATUS_NOT_REQUESTED,
                consistency_status=CONSISTENCY_VALIDATION_STATUS_NOT_REQUESTED,
                provider_summary=provider_summary,
                validation_errors=(),
            )
        if self._transport is None:
            return _fallback_result(
                deterministic_payload,
                mode=FEEDBACK_GENERATION_MODE_FALLBACK,
                fallback_reason=FALLBACK_PROVIDER_UNAVAILABLE,
                llm_validation_status=LLM_OUTPUT_VALIDATION_STATUS_NOT_REQUESTED,
                consistency_status=CONSISTENCY_VALIDATION_STATUS_NOT_REQUESTED,
                provider_summary=provider_summary,
                validation_errors=({"code": "provider_unavailable", "message": "llm transport is missing"},),
            )
        if _provider_kind(self._transport) != "fake" and not should_allow_real_feedback_provider(self._transport):
            return _fallback_result(
                deterministic_payload,
                mode=FEEDBACK_GENERATION_MODE_FALLBACK,
                fallback_reason=FALLBACK_REAL_PROVIDER_DISABLED,
                llm_validation_status=LLM_OUTPUT_VALIDATION_STATUS_NOT_REQUESTED,
                consistency_status=CONSISTENCY_VALIDATION_STATUS_NOT_REQUESTED,
                provider_summary=provider_summary,
                validation_errors=({"code": "real_provider_disabled", "message": "feedback real provider flag is off"},),
            )

        prompt_bundle = build_polish_feedback_prompt_bundle(
            feedback_input=feedback_input,
            deterministic_payload=deterministic_payload,
        )
        try:
            transport_result = self._transport.generate(
                LlmTransportRequest(
                    contract_ids=POLISH_ANSWER_FEEDBACK_CONTRACT_IDS,
                    task_type=POLISH_ANSWER_FEEDBACK_TASK_TYPE,
                    input_refs=_input_refs(feedback_input),
                    evidence_bundle=prompt_bundle,
                )
            )
        except TimeoutError:
            return _fallback_result(
                deterministic_payload,
                mode=FEEDBACK_GENERATION_MODE_FALLBACK,
                fallback_reason=FALLBACK_PROVIDER_TIMEOUT,
                llm_validation_status=LLM_OUTPUT_VALIDATION_STATUS_NOT_REQUESTED,
                consistency_status=CONSISTENCY_VALIDATION_STATUS_NOT_REQUESTED,
                provider_summary=provider_summary,
                validation_errors=({"code": "provider_timeout", "message": "transport timed out"},),
            )
        except LlmTransportConfigurationError as exc:
            return _fallback_result(
                deterministic_payload,
                mode=FEEDBACK_GENERATION_MODE_FALLBACK,
                fallback_reason=FALLBACK_TRANSPORT_CONFIGURATION_ERROR,
                llm_validation_status=LLM_OUTPUT_VALIDATION_STATUS_NOT_REQUESTED,
                consistency_status=CONSISTENCY_VALIDATION_STATUS_NOT_REQUESTED,
                provider_summary=provider_summary,
                validation_errors=({"code": "transport_configuration_error", "message": _safe_error(exc)},),
            )
        except LlmTransportUnavailableError as exc:
            return _fallback_result(
                deterministic_payload,
                mode=FEEDBACK_GENERATION_MODE_FALLBACK,
                fallback_reason=FALLBACK_PROVIDER_UNAVAILABLE,
                llm_validation_status=LLM_OUTPUT_VALIDATION_STATUS_NOT_REQUESTED,
                consistency_status=CONSISTENCY_VALIDATION_STATUS_NOT_REQUESTED,
                provider_summary=provider_summary,
                validation_errors=({"code": "provider_unavailable", "message": _safe_error(exc)},),
            )
        except LlmTransportResponseError as exc:
            return _fallback_result(
                deterministic_payload,
                mode=FEEDBACK_GENERATION_MODE_FALLBACK,
                fallback_reason=FALLBACK_SCHEMA_INVALID,
                llm_validation_status=LLM_OUTPUT_VALIDATION_STATUS_SCHEMA_INVALID,
                consistency_status=CONSISTENCY_VALIDATION_STATUS_NOT_REQUESTED,
                provider_summary=provider_summary,
                validation_errors=({"code": "provider_response_invalid", "message": _safe_error(exc)},),
            )
        except LlmTransportError as exc:
            return _fallback_result(
                deterministic_payload,
                mode=FEEDBACK_GENERATION_MODE_FALLBACK,
                fallback_reason=FALLBACK_PROVIDER_UNAVAILABLE,
                llm_validation_status=LLM_OUTPUT_VALIDATION_STATUS_NOT_REQUESTED,
                consistency_status=CONSISTENCY_VALIDATION_STATUS_NOT_REQUESTED,
                provider_summary=provider_summary,
                validation_errors=({"code": "transport_error", "message": _safe_error(exc)},),
            )

        normalized = validate_feedback_llm_output(
            transport_result.result,
            feedback_input=feedback_input,
        )
        if isinstance(normalized, _InvalidFeedbackOutput):
            return _fallback_result(
                deterministic_payload,
                mode=FEEDBACK_GENERATION_MODE_FALLBACK,
                fallback_reason=normalized.fallback_reason,
                llm_validation_status=normalized.validation_status,
                consistency_status=CONSISTENCY_VALIDATION_STATUS_NOT_REQUESTED,
                provider_summary=_provider_summary(self._transport, result=transport_result),
                validation_errors=normalized.validation_errors,
                repair_attempted=normalized.repair_attempted,
            )

        adapted = adapt_llm_output_to_structured_payload(
            normalized,
            feedback_input=feedback_input,
            deterministic_payload=deterministic_payload,
            transport_result=transport_result,
            provider_summary=_provider_summary(self._transport, result=transport_result),
        )
        if isinstance(adapted, _InvalidFeedbackOutput):
            return _fallback_result(
                deterministic_payload,
                mode=FEEDBACK_GENERATION_MODE_FALLBACK,
                fallback_reason=adapted.fallback_reason,
                llm_validation_status=adapted.validation_status,
                consistency_status=CONSISTENCY_VALIDATION_STATUS_INVALID,
                provider_summary=_provider_summary(self._transport, result=transport_result),
                validation_errors=adapted.validation_errors,
                repair_attempted=adapted.repair_attempted,
            )

        payload = _extend_feedback_metadata(
            adapted.payload,
            mode=FEEDBACK_GENERATION_MODE_ACCEPTED,
            llm_validation_status=LLM_OUTPUT_VALIDATION_STATUS_VALID,
            consistency_status=CONSISTENCY_VALIDATION_STATUS_VALID,
            fallback_reason=None,
            provider_summary=_provider_summary(self._transport, result=transport_result),
            model_summary=_model_summary(transport_result),
            validation_errors=(),
            repair_attempted=adapted.repair_attempted,
        )
        return PolishFeedbackLlmResult(
            feedback_payload=payload,
            llm_generation_mode=FEEDBACK_GENERATION_MODE_ACCEPTED,
            llm_output_validation_status=LLM_OUTPUT_VALIDATION_STATUS_VALID,
            consistency_validation_status=CONSISTENCY_VALIDATION_STATUS_VALID,
            fallback_reason=None,
            repair_attempted=adapted.repair_attempted,
            validation_errors=(),
        )


def generate_with_llm_or_fallback(*, transport: LlmTransport | None, **kwargs: Any) -> PolishFeedbackLlmResult:
    return PolishFeedbackLlmService(transport).generate_with_llm_or_fallback(**kwargs)


def should_enable_feedback_llm() -> bool:
    return _truthy(os.getenv(FEEDBACK_LLM_ENABLED_ENV))


def should_allow_real_feedback_provider(transport: LlmTransport | None = None) -> bool:
    if transport is not None and _provider_kind(transport) == "fake":
        return True
    return _truthy(os.getenv(FEEDBACK_REAL_PROVIDER_ENABLED_ENV))


def validate_feedback_llm_output(raw_output: object, *, feedback_input: FeedbackInput) -> dict[str, Any] | Any:
    if not isinstance(raw_output, dict):
        return _invalid(FALLBACK_SCHEMA_INVALID, LLM_OUTPUT_VALIDATION_STATUS_SCHEMA_INVALID, "root_not_object")
    forbidden = _forbidden_paths(raw_output)
    if forbidden:
        return _invalid(
            FALLBACK_RAW_PAYLOAD_LEAK,
            LLM_OUTPUT_VALIDATION_STATUS_SCHEMA_INVALID,
            "forbidden_output_field",
            "forbidden_llm_payload_field",
        )
    missing_required = [field for field in _REQUIRED_OUTPUT_FIELDS if field not in raw_output]
    if missing_required:
        return _invalid(
            FALLBACK_SCHEMA_INVALID,
            LLM_OUTPUT_VALIDATION_STATUS_SCHEMA_INVALID,
            "required_field_missing",
            missing_required[0],
        )
    if str(raw_output.get("schema_id")) != FEEDBACK_SCHEMA_ID:
        return _invalid(FALLBACK_SCHEMA_INVALID, LLM_OUTPUT_VALIDATION_STATUS_SCHEMA_INVALID, "schema_id_mismatch")
    if str(raw_output.get("schema_version")) != FEEDBACK_SCHEMA_VERSION:
        return _invalid(
            FALLBACK_SCHEMA_INVALID,
            LLM_OUTPUT_VALIDATION_STATUS_SCHEMA_INVALID,
            "schema_version_mismatch",
        )
    if feedback_input.answer_round > 1:
        missing_retry = [field for field in _RETRY_OUTPUT_FIELDS if field not in raw_output]
        if missing_retry:
            return _invalid(
                FALLBACK_RETRY_DELTA_INVALID,
                LLM_OUTPUT_VALIDATION_STATUS_SCHEMA_INVALID,
                "retry_field_missing",
                missing_retry[0],
            )
    return deepcopy(raw_output)


def adapt_llm_output_to_structured_payload(
    llm_output: dict[str, Any],
    *,
    feedback_input: FeedbackInput,
    deterministic_payload: dict[str, Any],
    transport_result: LlmTransportResult | None = None,
    provider_summary: dict[str, Any] | None = None,
) -> dict[str, Any] | Any:
    repair_attempted = False
    payload = normalize_feedback_payload(llm_output)
    payload = _merge_required_identity_fields(payload, deterministic_payload)
    if "feedback_text" not in llm_output or not str(llm_output.get("feedback_text") or "").strip():
        payload["feedback_text"] = str(payload.get("feedback_summary") or deterministic_payload.get("feedback_text") or "")
        repair_attempted = True
    payload.setdefault("feedback_summary", payload.get("feedback_text", ""))
    payload.setdefault("weakness_candidates", [])
    payload.setdefault("asset_candidates", [])
    payload["answer_id"] = deterministic_payload.get("answer_id", feedback_input.answer_id)
    payload["question_id"] = deterministic_payload.get("question_id", feedback_input.question_id)
    payload["question_text"] = deterministic_payload.get("question_text", feedback_input.question_text)
    payload["answer_text"] = deterministic_payload.get("answer_text", feedback_input.answer_text)

    score_result = payload.get("score_result")
    if not isinstance(score_result, dict):
        score_result = {}
    computed_score = compute_score_result_from_dimensions(payload.get("scoring_dimensions", ()))
    actual = _to_int(score_result.get("score_value"))
    expected = _to_int(computed_score.get("score_value"))
    if actual != expected:
        repair_attempted = True
        payload["score_result"] = {
            **score_result,
            **computed_score,
            "score_result_id": score_result.get("score_result_id")
            or _nested_get(deterministic_payload, "score_result", "score_result_id")
            or deterministic_payload.get("score_result_id"),
            "score_type": score_result.get("score_type") or "polish_answer",
            "score_version": score_result.get("score_version") or POLISH_ANSWER_FEEDBACK_SCHEMA_VERSION,
            "rubric_version": score_result.get("rubric_version") or "polish_round_score.llm.v1",
            "confidence_level": score_result.get("confidence_level") or _confidence_value(transport_result),
        }

    if feedback_input.answer_round > 1 and not _retry_delta_valid(payload):
        return _invalid(
            FALLBACK_RETRY_DELTA_INVALID,
            LLM_OUTPUT_VALIDATION_STATUS_SCHEMA_INVALID,
            "retry_delta_invalid",
            repair_attempted=repair_attempted,
        )

    validation = validate_feedback_consistency(payload)
    if not validation.get("allow_emit"):
        fallback_reason = FALLBACK_REPAIR_FAILED if repair_attempted else FALLBACK_CONSISTENCY_INVALID
        return _invalid(
            fallback_reason,
            LLM_OUTPUT_VALIDATION_STATUS_CONSISTENCY_INVALID,
            "consistency_invalid",
            "; ".join(str(item) for item in validation.get("blocking_issues", [])[:2]),
            repair_attempted=repair_attempted,
        )
    normalized = validation["normalized_feedback_payload"]
    if _forbidden_paths(normalized):
        return _invalid(
            FALLBACK_RAW_PAYLOAD_LEAK,
            LLM_OUTPUT_VALIDATION_STATUS_SCHEMA_INVALID,
            "forbidden_output_field_after_normalization",
            repair_attempted=repair_attempted,
        )
    return _AdaptedFeedbackPayload(payload=normalized, repair_attempted=repair_attempted)


@dataclass(frozen=True)
class _AdaptedFeedbackPayload:
    payload: dict[str, Any]
    repair_attempted: bool


@dataclass(frozen=True)
class _InvalidFeedbackOutput:
    fallback_reason: str
    validation_status: str
    validation_errors: tuple[dict[str, str], ...]
    repair_attempted: bool = False


def _fallback_result(
    deterministic_payload: dict[str, Any],
    *,
    mode: str,
    fallback_reason: str,
    llm_validation_status: str,
    consistency_status: str,
    provider_summary: dict[str, Any],
    validation_errors: tuple[dict[str, str], ...],
    repair_attempted: bool = False,
) -> PolishFeedbackLlmResult:
    payload = _extend_feedback_metadata(
        deepcopy(deterministic_payload),
        mode=mode,
        llm_validation_status=llm_validation_status,
        consistency_status=consistency_status,
        fallback_reason=fallback_reason,
        provider_summary=provider_summary,
        model_summary={"kind": "not_requested"},
        validation_errors=validation_errors,
        repair_attempted=repair_attempted,
    )
    return PolishFeedbackLlmResult(
        feedback_payload=payload,
        llm_generation_mode=mode,
        llm_output_validation_status=llm_validation_status,
        consistency_validation_status=consistency_status,
        fallback_reason=fallback_reason,
        repair_attempted=repair_attempted,
        validation_errors=validation_errors,
    )


def _extend_feedback_metadata(
    payload: dict[str, Any],
    *,
    mode: str,
    llm_validation_status: str,
    consistency_status: str,
    fallback_reason: str | None,
    provider_summary: dict[str, Any],
    model_summary: dict[str, Any],
    validation_errors: tuple[dict[str, str], ...],
    repair_attempted: bool,
) -> dict[str, Any]:
    result = deepcopy(payload)
    metadata = result.get("feedback_metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    metadata.update(
        {
            "feedback_generation_mode": mode,
            "feedback_llm_task_type": POLISH_ANSWER_FEEDBACK_TASK_TYPE,
            "prompt_version": POLISH_ANSWER_FEEDBACK_PROMPT_VERSION,
            "feedback_schema_version": POLISH_ANSWER_FEEDBACK_SCHEMA_VERSION,
            "llm_output_validation_status": llm_validation_status,
            "consistency_validation_status": consistency_status,
            "fallback_reason": fallback_reason,
            "repair_attempted": repair_attempted,
            "provider_summary": provider_summary,
            "model_summary": model_summary,
            "redaction_boundary": "compact_feedback_inputs_only",
            "validation_errors": [dict(item) for item in validation_errors],
        }
    )
    result["feedback_metadata"] = metadata
    return result


def _merge_required_identity_fields(payload: dict[str, Any], deterministic_payload: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(payload)
    for key in (
        "feedback_id",
        "ai_task_id",
        "contract_id",
        "contract_ids",
        "polish_theme",
        "polish_theme_label",
        "explicit_weight",
        "implicit_weight",
        "score_result_ref",
        "polish_session_ref",
        "question_ref",
        "answer_ref",
        "candidate_refs",
        "validation_result_ref",
        "trace_refs",
        "legacy_compatibility",
        "previous_loss_points",
    ):
        if key in deterministic_payload and (key not in merged or not merged.get(key)):
            merged[key] = deepcopy(deterministic_payload[key])
    merged["schema_id"] = FEEDBACK_SCHEMA_ID
    merged["schema_version"] = FEEDBACK_SCHEMA_VERSION
    return merged


def _retry_delta_valid(payload: dict[str, Any]) -> bool:
    if not isinstance(payload.get("dimension_delta"), dict):
        return False
    for key in (
        "improved_points",
        "remaining_gaps",
        "repeated_loss_points",
        "regressed_points",
        "next_retry_focus",
    ):
        if not isinstance(payload.get(key), list):
            return False
    if not isinstance(payload.get("should_continue_same_question"), bool):
        return False
    if not isinstance(payload.get("should_generate_next_question"), bool):
        return False
    if payload.get("should_continue_same_question") and payload.get("should_generate_next_question"):
        return False
    return bool(str(payload.get("mastery_status") or "").strip())


def _invalid(
    reason: str,
    validation_status: str,
    code: str,
    detail: str | None = None,
    *,
    repair_attempted: bool = False,
) -> _InvalidFeedbackOutput:
    error = {"code": code, "message": detail or code}
    return _InvalidFeedbackOutput(
        fallback_reason=reason,
        validation_status=validation_status,
        validation_errors=(error,),
        repair_attempted=repair_attempted,
    )


def _input_refs(feedback_input: FeedbackInput) -> tuple[str, ...]:
    refs = [
        feedback_input.session_id,
        feedback_input.question_id,
        feedback_input.answer_id,
        feedback_input.question_pattern,
        feedback_input.polish_theme,
    ]
    return tuple(str(ref) for ref in refs if ref)


def _forbidden_paths(value: object, *, prefix: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            path = f"{prefix}.{normalized}" if prefix else normalized
            if normalized in _FORBIDDEN_OUTPUT_KEYS:
                paths.append(path)
            paths.extend(_forbidden_paths(item, prefix=path))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            paths.extend(_forbidden_paths(item, prefix=f"{prefix}[{index}]"))
    elif isinstance(value, str) and _contains_forbidden_text_marker(value):
        paths.append(prefix or "<string>")
    return paths


def _provider_kind(transport: LlmTransport | None) -> str:
    if transport is None:
        return "unavailable"
    status = str(getattr(transport, "status", "")).lower()
    class_name = transport.__class__.__name__.lower()
    module_name = transport.__class__.__module__.lower()
    if "fake" in status or "fake" in class_name or module_name.endswith("fake_transport"):
        return "fake"
    return "real"


def _provider_summary(transport: LlmTransport | None, *, result: LlmTransportResult | None = None) -> dict[str, Any]:
    kind = _provider_kind(transport)
    summary: dict[str, Any] = {"kind": kind}
    if transport is not None:
        status = _safe_metadata_text(getattr(transport, "status", None), max_chars=80)
        if status:
            summary["status"] = status
    if result is not None:
        summary["validation_status"] = str(result.validation_status.value)
        summary["confidence_level"] = str(result.confidence_level.value)
    return summary


def _model_summary(result: LlmTransportResult) -> dict[str, Any]:
    return {"kind": "safe_summary", "model_name": "not_recorded"}


def _confidence_value(result: LlmTransportResult | None) -> str:
    if result is None:
        return "medium"
    return str(result.confidence_level.value)


def _safe_error(exc: BaseException) -> str:
    return _safe_metadata_text(str(exc), max_chars=200) or exc.__class__.__name__


def _safe_metadata_text(value: object, *, max_chars: int) -> str | None:
    text = _string_or_none(value, max_chars=max_chars)
    if text is None:
        return None
    if _contains_forbidden_text_marker(text):
        return "redacted_sensitive_detail"
    return text


def _contains_forbidden_text_marker(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in _FORBIDDEN_TEXT_MARKERS)


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in _TRUTHY


def _to_int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _nested_get(source: dict[str, Any], key: str, nested_key: str) -> Any:
    nested = source.get(key)
    if isinstance(nested, dict):
        return nested.get(nested_key)
    return None


def _string_or_none(value: object, *, max_chars: int) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:max_chars]
