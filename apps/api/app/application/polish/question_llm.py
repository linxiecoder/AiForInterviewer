"""LLM wrapper for polish question generation with deterministic fallback."""

from __future__ import annotations

from dataclasses import dataclass, replace
import os
from typing import Any, Callable

from app.application.polish.entities import PolishQuestionDraft
from app.application.polish.question_metadata import build_question_metadata
from app.application.polish.question_prompts import (
    POLISH_QUESTION_GENERATION_CONTRACT_IDS,
    POLISH_QUESTION_GENERATION_PROMPT_VERSION,
    POLISH_QUESTION_GENERATION_SCHEMA_ID,
    POLISH_QUESTION_GENERATION_SCHEMA_VERSION,
    POLISH_QUESTION_GENERATION_TASK_TYPE,
    build_polish_question_generation_prompt_bundle,
)
from app.application.polish.question_quality import repair_question_text, validate_question_quality
from app.application.llm.errors import (
    LlmTransportConfigurationError,
    LlmTransportError,
    LlmTransportResponseError,
    LlmTransportUnavailableError,
)
from app.application.llm.ports import LlmTransport
from app.application.llm.types import LlmTransportRequest, LlmTransportResult
from app.application.common.logging import LogUtil


QUESTION_LLM_ENABLED_ENV = "AIFI_POLISH_QUESTION_LLM_ENABLED"
QUESTION_REAL_PROVIDER_ENABLED_ENV = "AIFI_POLISH_QUESTION_REAL_PROVIDER_ENABLED"

LLM_GENERATION_MODE_DETERMINISTIC_ONLY = "deterministic_only"
LLM_GENERATION_MODE_ACCEPTED = "llm_accepted"
LLM_GENERATION_MODE_FALLBACK = "llm_fallback"

LLM_VALIDATION_STATUS_NOT_REQUESTED = "not_requested"
LLM_VALIDATION_STATUS_VALID = "valid"
LLM_VALIDATION_STATUS_SCHEMA_INVALID = "schema_invalid"
LLM_VALIDATION_STATUS_SEMANTIC_INVALID = "semantic_invalid"

FALLBACK_FEATURE_DISABLED = "feature_disabled"
FALLBACK_REAL_PROVIDER_DISABLED = "real_provider_disabled"
FALLBACK_PROVIDER_UNAVAILABLE = "provider_unavailable"
FALLBACK_PROVIDER_TIMEOUT = "provider_timeout"
FALLBACK_TRANSPORT_CONFIGURATION_ERROR = "transport_configuration_error"
FALLBACK_SCHEMA_INVALID = "schema_invalid"
FALLBACK_SEMANTIC_INVALID = "semantic_invalid"
FALLBACK_FABRICATED_ENTITY = "fabricated_entity"
FALLBACK_ANSWER_LEAK = "answer_leak"
FALLBACK_QUALITY_SCORE_TOO_LOW = "quality_score_too_low"
FALLBACK_EVIDENCE_REFS_INVALID = "evidence_refs_invalid"
FALLBACK_PROMPT_INPUT_INSUFFICIENT = "prompt_input_insufficient"
FALLBACK_OUTPUT_TOO_BROAD = "output_too_broad"
FALLBACK_REPEATED_QUESTION = "repeated_question"

_TRUTHY = {"1", "true", "yes", "y", "on"}
_FORBIDDEN_OUTPUT_KEYS = {
    "reference_answer",
    "full_answer",
    "answer",
    "raw_prompt",
    "prompt",
    "raw_completion",
    "completion",
    "provider_payload",
    "hidden_rubric",
    "hidden_scoring_rules",
}
_REQUIRED_OUTPUT_FIELDS = (
    "schema_id",
    "schema_version",
    "status",
    "question_text",
    "question_pattern",
    "interview_intent",
    "scenario_constraint_summary",
    "expected_answer_dimensions",
    "evidence_refs",
    "source_availability",
    "confidence_level",
    "low_confidence_flags",
    "quality_hints",
    "requires_repair",
    "redaction_boundary",
)


@dataclass(frozen=True)
class PolishQuestionLlmOutput:
    question_text: str
    question_pattern: str
    interview_intent: str | None
    scenario_constraint_summary: str | None
    expected_answer_dimensions: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    source_availability: str
    confidence_level: str
    low_confidence_flags: tuple[str, ...]
    quality_hints: tuple[str, ...]
    requires_repair: bool
    redaction_boundary: str | dict[str, Any]
    pattern_was_aligned: bool = False


@dataclass(frozen=True)
class PolishQuestionLlmResult:
    draft: PolishQuestionDraft
    llm_output: PolishQuestionLlmOutput | None
    llm_generation_mode: str
    llm_output_validation_status: str
    fallback_reason: str | None
    repair_attempted: bool = False
    validation_errors: tuple[dict[str, Any], ...] = ()


class PolishQuestionLlmService:
    def __init__(self, transport: LlmTransport | None) -> None:
        self._transport = transport

    def generate_with_llm_or_fallback(
        self,
        *,
        session: Any,
        context: dict[str, Any],
        plan: dict[str, Any],
        state: dict[str, Any],
        requested_ref: str | None,
        deterministic_builder: Callable[[], Any],
    ) -> PolishQuestionLlmResult:
        deterministic_build = deterministic_builder()
        deterministic_draft = deterministic_build.draft
        provider_summary = _provider_summary(self._transport)

        if not should_enable_question_llm():
            LogUtil.polish_question_llm_fallback(
                fallback_reason=FALLBACK_FEATURE_DISABLED,
                mode=LLM_GENERATION_MODE_DETERMINISTIC_ONLY,
            )
            return _fallback_result(
                deterministic_draft,
                mode=LLM_GENERATION_MODE_DETERMINISTIC_ONLY,
                fallback_reason=FALLBACK_FEATURE_DISABLED,
                validation_status=LLM_VALIDATION_STATUS_NOT_REQUESTED,
                provider_summary=provider_summary,
                validation_errors=(),
            )
        if not deterministic_build.question_context.evidence_refs:
            LogUtil.polish_question_llm_fallback(
                fallback_reason=FALLBACK_PROMPT_INPUT_INSUFFICIENT,
                mode=LLM_GENERATION_MODE_FALLBACK,
            )
            return _fallback_result(
                deterministic_draft,
                mode=LLM_GENERATION_MODE_FALLBACK,
                fallback_reason=FALLBACK_PROMPT_INPUT_INSUFFICIENT,
                validation_status=LLM_VALIDATION_STATUS_SEMANTIC_INVALID,
                provider_summary=provider_summary,
                validation_errors=({"code": "prompt_input_insufficient", "message": "input evidence refs are empty"},),
            )
        if self._transport is None:
            LogUtil.polish_question_llm_fallback(
                fallback_reason=FALLBACK_PROVIDER_UNAVAILABLE,
                mode=LLM_GENERATION_MODE_FALLBACK,
            )
            return _fallback_result(
                deterministic_draft,
                mode=LLM_GENERATION_MODE_FALLBACK,
                fallback_reason=FALLBACK_PROVIDER_UNAVAILABLE,
                validation_status=LLM_VALIDATION_STATUS_NOT_REQUESTED,
                provider_summary=provider_summary,
                validation_errors=({"code": "provider_unavailable", "message": "llm transport is missing"},),
            )
        if _provider_kind(self._transport) != "fake" and not should_allow_real_question_provider(self._transport):
            LogUtil.polish_question_llm_fallback(
                fallback_reason=FALLBACK_REAL_PROVIDER_DISABLED,
                mode=LLM_GENERATION_MODE_FALLBACK,
            )
            return _fallback_result(
                deterministic_draft,
                mode=LLM_GENERATION_MODE_FALLBACK,
                fallback_reason=FALLBACK_REAL_PROVIDER_DISABLED,
                validation_status=LLM_VALIDATION_STATUS_NOT_REQUESTED,
                provider_summary=provider_summary,
                validation_errors=({"code": "real_provider_disabled", "message": "question real provider flag is off"},),
            )

        prompt_bundle = build_polish_question_generation_prompt_bundle(
            session=session,
            context=context,
            plan=plan,
            state=state,
            requested_ref=requested_ref,
            deterministic_build=deterministic_build,
        )
        try:
            transport_result = self._transport.generate(
                LlmTransportRequest(
                    contract_ids=POLISH_QUESTION_GENERATION_CONTRACT_IDS,
                    task_type=POLISH_QUESTION_GENERATION_TASK_TYPE,
                    input_refs=_input_refs(session=session, deterministic_build=deterministic_build),
                    evidence_bundle=prompt_bundle,
                )
            )
        except TimeoutError:
            LogUtil.polish_question_llm_fallback(
                fallback_reason=FALLBACK_PROVIDER_TIMEOUT,
                mode=LLM_GENERATION_MODE_FALLBACK,
            )
            return _fallback_result(
                deterministic_draft,
                mode=LLM_GENERATION_MODE_FALLBACK,
                fallback_reason=FALLBACK_PROVIDER_TIMEOUT,
                validation_status=LLM_VALIDATION_STATUS_NOT_REQUESTED,
                provider_summary=provider_summary,
                validation_errors=({"code": "provider_timeout", "message": "transport timed out"},),
            )
        except LlmTransportConfigurationError as exc:
            LogUtil.polish_question_llm_fallback(
                fallback_reason=FALLBACK_TRANSPORT_CONFIGURATION_ERROR,
                mode=LLM_GENERATION_MODE_FALLBACK,
            )
            return _fallback_result(
                deterministic_draft,
                mode=LLM_GENERATION_MODE_FALLBACK,
                fallback_reason=FALLBACK_TRANSPORT_CONFIGURATION_ERROR,
                validation_status=LLM_VALIDATION_STATUS_NOT_REQUESTED,
                provider_summary=provider_summary,
                validation_errors=({"code": "transport_configuration_error", "message": _safe_error(exc)},),
            )
        except LlmTransportUnavailableError as exc:
            LogUtil.polish_question_llm_fallback(
                fallback_reason=FALLBACK_PROVIDER_UNAVAILABLE,
                mode=LLM_GENERATION_MODE_FALLBACK,
            )
            return _fallback_result(
                deterministic_draft,
                mode=LLM_GENERATION_MODE_FALLBACK,
                fallback_reason=FALLBACK_PROVIDER_UNAVAILABLE,
                validation_status=LLM_VALIDATION_STATUS_NOT_REQUESTED,
                provider_summary=provider_summary,
                validation_errors=({"code": "provider_unavailable", "message": _safe_error(exc)},),
            )
        except LlmTransportResponseError as exc:
            LogUtil.polish_question_llm_fallback(
                fallback_reason=FALLBACK_SCHEMA_INVALID,
                mode=LLM_GENERATION_MODE_FALLBACK,
            )
            return _fallback_result(
                deterministic_draft,
                mode=LLM_GENERATION_MODE_FALLBACK,
                fallback_reason=FALLBACK_SCHEMA_INVALID,
                validation_status=LLM_VALIDATION_STATUS_SCHEMA_INVALID,
                provider_summary=provider_summary,
                validation_errors=({"code": "provider_response_invalid", "message": _safe_error(exc)},),
            )
        except LlmTransportError as exc:
            LogUtil.polish_question_llm_fallback(
                fallback_reason=FALLBACK_PROVIDER_UNAVAILABLE,
                mode=LLM_GENERATION_MODE_FALLBACK,
            )
            return _fallback_result(
                deterministic_draft,
                mode=LLM_GENERATION_MODE_FALLBACK,
                fallback_reason=FALLBACK_PROVIDER_UNAVAILABLE,
                validation_status=LLM_VALIDATION_STATUS_NOT_REQUESTED,
                provider_summary=provider_summary,
                validation_errors=({"code": "transport_error", "message": _safe_error(exc)},),
            )

        normalized = validate_llm_question_output(
            transport_result.result,
            deterministic_build=deterministic_build,
        )
        if isinstance(normalized, _InvalidLlmOutput):
            LogUtil.polish_question_llm_fallback(
                fallback_reason=normalized.fallback_reason,
                mode=LLM_GENERATION_MODE_FALLBACK,
            )
            return _fallback_result(
                deterministic_draft,
                mode=LLM_GENERATION_MODE_FALLBACK,
                fallback_reason=normalized.fallback_reason,
                validation_status=normalized.validation_status,
                provider_summary=_provider_summary(self._transport, result=transport_result),
                validation_errors=normalized.validation_errors,
            )

        adapted = adapt_llm_output_to_question_draft(
            normalized,
            deterministic_build=deterministic_build,
            transport_result=transport_result,
            provider_summary=_provider_summary(self._transport, result=transport_result),
        )
        if isinstance(adapted, _InvalidAdaptedQuestion):
            LogUtil.polish_question_llm_fallback(
                fallback_reason=adapted.fallback_reason,
                mode=LLM_GENERATION_MODE_FALLBACK,
            )
            return _fallback_result(
                deterministic_draft,
                mode=LLM_GENERATION_MODE_FALLBACK,
                fallback_reason=adapted.fallback_reason,
                validation_status=LLM_VALIDATION_STATUS_SEMANTIC_INVALID,
                provider_summary=_provider_summary(self._transport, result=transport_result),
                validation_errors=adapted.validation_errors,
                repair_attempted=adapted.repair_attempted,
            )
        return PolishQuestionLlmResult(
            draft=adapted.draft,
            llm_output=normalized,
            llm_generation_mode=LLM_GENERATION_MODE_ACCEPTED,
            llm_output_validation_status=LLM_VALIDATION_STATUS_VALID,
            fallback_reason=None,
            repair_attempted=adapted.repair_attempted,
            validation_errors=(),
        )


def generate_with_llm_or_fallback(*, transport: LlmTransport | None, **kwargs: Any) -> PolishQuestionLlmResult:
    return PolishQuestionLlmService(transport).generate_with_llm_or_fallback(**kwargs)


def should_enable_question_llm() -> bool:
    return _truthy(os.getenv(QUESTION_LLM_ENABLED_ENV))


def should_allow_real_question_provider(transport: LlmTransport | None = None) -> bool:
    if transport is not None and _provider_kind(transport) == "fake":
        return True
    return _truthy(os.getenv(QUESTION_REAL_PROVIDER_ENABLED_ENV))


def validate_llm_question_output(raw_output: object, *, deterministic_build: Any) -> PolishQuestionLlmOutput | Any:
    if not isinstance(raw_output, dict):
        return _invalid(FALLBACK_SCHEMA_INVALID, LLM_VALIDATION_STATUS_SCHEMA_INVALID, "root_not_object")
    forbidden = _forbidden_paths(raw_output)
    if forbidden:
        reason = FALLBACK_ANSWER_LEAK if any("answer" in item for item in forbidden) else FALLBACK_SCHEMA_INVALID
        return _invalid(reason, LLM_VALIDATION_STATUS_SCHEMA_INVALID, "forbidden_output_field", forbidden[0])
    missing_required = [field for field in _REQUIRED_OUTPUT_FIELDS if field not in raw_output]
    if missing_required:
        return _invalid(
            FALLBACK_SCHEMA_INVALID,
            LLM_VALIDATION_STATUS_SCHEMA_INVALID,
            "required_field_missing",
            missing_required[0],
        )
    if raw_output.get("schema_id") != POLISH_QUESTION_GENERATION_SCHEMA_ID:
        return _invalid(FALLBACK_SCHEMA_INVALID, LLM_VALIDATION_STATUS_SCHEMA_INVALID, "schema_id_mismatch")
    if raw_output.get("schema_version") != POLISH_QUESTION_GENERATION_SCHEMA_VERSION:
        return _invalid(FALLBACK_SCHEMA_INVALID, LLM_VALIDATION_STATUS_SCHEMA_INVALID, "schema_version_mismatch")

    status = _string_or_none(raw_output.get("status"), max_chars=80)
    if status is None:
        return _invalid(FALLBACK_SCHEMA_INVALID, LLM_VALIDATION_STATUS_SCHEMA_INVALID, "status_missing")
    question_text = _string_or_none(raw_output.get("question_text"), max_chars=900)
    if question_text is None:
        return _invalid(FALLBACK_SCHEMA_INVALID, LLM_VALIDATION_STATUS_SCHEMA_INVALID, "question_text_missing")
    evidence_refs_raw = raw_output.get("evidence_refs")
    if not isinstance(evidence_refs_raw, list):
        return _invalid(FALLBACK_SCHEMA_INVALID, LLM_VALIDATION_STATUS_SCHEMA_INVALID, "evidence_refs_not_list")
    evidence_refs = tuple(str(ref).strip() for ref in evidence_refs_raw if str(ref).strip())
    allowed_refs = tuple(deterministic_build.question_context.evidence_refs)
    if not evidence_refs:
        return _invalid(
            FALLBACK_EVIDENCE_REFS_INVALID,
            LLM_VALIDATION_STATUS_SEMANTIC_INVALID,
            "evidence_refs_empty",
            diagnostics=_evidence_ref_diagnostics(
                allowed_refs=allowed_refs,
                returned_refs=evidence_refs_raw,
                invalid_refs=(),
                validation_error_code="evidence_refs_empty",
                fallback_reason=FALLBACK_EVIDENCE_REFS_INVALID,
            ),
        )
    allowed_ref_set = set(allowed_refs)
    invalid_refs = tuple(
        ref for ref in evidence_refs_raw if str(ref).strip() and str(ref).strip() not in allowed_ref_set
    )
    if invalid_refs:
        return _invalid(
            FALLBACK_EVIDENCE_REFS_INVALID,
            LLM_VALIDATION_STATUS_SEMANTIC_INVALID,
            "evidence_refs_invalid",
            diagnostics=_evidence_ref_diagnostics(
                allowed_refs=allowed_refs,
                returned_refs=evidence_refs_raw,
                invalid_refs=invalid_refs,
                validation_error_code="evidence_refs_invalid",
                fallback_reason=FALLBACK_EVIDENCE_REFS_INVALID,
            ),
        )
    expected_dimensions_raw = raw_output.get("expected_answer_dimensions")
    if not isinstance(expected_dimensions_raw, list):
        return _invalid(
            FALLBACK_SCHEMA_INVALID,
            LLM_VALIDATION_STATUS_SCHEMA_INVALID,
            "expected_answer_dimensions_not_list",
        )
    expected_dimensions = tuple(_string_list(expected_dimensions_raw, limit=12))
    if not expected_dimensions:
        return _invalid(
            FALLBACK_SCHEMA_INVALID,
            LLM_VALIDATION_STATUS_SCHEMA_INVALID,
            "expected_answer_dimensions_empty",
        )
    low_flags = raw_output.get("low_confidence_flags")
    if not isinstance(low_flags, list):
        return _invalid(FALLBACK_SCHEMA_INVALID, LLM_VALIDATION_STATUS_SCHEMA_INVALID, "low_confidence_flags_not_list")
    quality_hints = raw_output.get("quality_hints")
    if not isinstance(quality_hints, list):
        return _invalid(FALLBACK_SCHEMA_INVALID, LLM_VALIDATION_STATUS_SCHEMA_INVALID, "quality_hints_not_list")
    requires_repair = raw_output.get("requires_repair")
    if not isinstance(requires_repair, bool):
        return _invalid(FALLBACK_SCHEMA_INVALID, LLM_VALIDATION_STATUS_SCHEMA_INVALID, "requires_repair_not_bool")
    redaction_boundary = raw_output.get("redaction_boundary")
    if redaction_boundary is None:
        return _invalid(FALLBACK_SCHEMA_INVALID, LLM_VALIDATION_STATUS_SCHEMA_INVALID, "redaction_boundary_missing")

    selected_pattern = deterministic_build.question_pattern.pattern_id
    raw_pattern = _string_or_none(raw_output.get("question_pattern"), max_chars=120)
    if raw_pattern is None:
        return _invalid(FALLBACK_SCHEMA_INVALID, LLM_VALIDATION_STATUS_SCHEMA_INVALID, "question_pattern_missing")
    pattern_was_aligned = raw_pattern != selected_pattern
    interview_intent = _string_or_none(raw_output.get("interview_intent"), max_chars=300)
    if interview_intent is None:
        return _invalid(FALLBACK_SCHEMA_INVALID, LLM_VALIDATION_STATUS_SCHEMA_INVALID, "interview_intent_missing")
    scenario_constraint_summary = _string_or_none(raw_output.get("scenario_constraint_summary"), max_chars=500)
    if scenario_constraint_summary is None:
        return _invalid(
            FALLBACK_SCHEMA_INVALID,
            LLM_VALIDATION_STATUS_SCHEMA_INVALID,
            "scenario_constraint_summary_missing",
        )
    source_availability = _string_or_none(raw_output.get("source_availability"), max_chars=80)
    if source_availability is None:
        return _invalid(FALLBACK_SCHEMA_INVALID, LLM_VALIDATION_STATUS_SCHEMA_INVALID, "source_availability_missing")
    confidence_level = _string_or_none(raw_output.get("confidence_level"), max_chars=40)
    if confidence_level is None:
        return _invalid(FALLBACK_SCHEMA_INVALID, LLM_VALIDATION_STATUS_SCHEMA_INVALID, "confidence_level_missing")
    return PolishQuestionLlmOutput(
        question_text=question_text,
        question_pattern=selected_pattern,
        interview_intent=interview_intent,
        scenario_constraint_summary=scenario_constraint_summary,
        expected_answer_dimensions=expected_dimensions,
        evidence_refs=evidence_refs,
        source_availability=source_availability,
        confidence_level=confidence_level,
        low_confidence_flags=tuple(_string_list(low_flags, limit=20)),
        quality_hints=tuple(_string_list(quality_hints, limit=20)),
        requires_repair=requires_repair,
        redaction_boundary=redaction_boundary,
        pattern_was_aligned=pattern_was_aligned,
    )


def adapt_llm_output_to_question_draft(
    llm_output: PolishQuestionLlmOutput,
    *,
    deterministic_build: Any,
    transport_result: LlmTransportResult,
    provider_summary: dict[str, Any],
) -> Any:
    pattern = deterministic_build.question_pattern
    question_context = deterministic_build.question_context
    quality = validate_question_quality(
        question_text=llm_output.question_text,
        selected_pattern=pattern,
        theme_strategy=question_context.strategy,
        scenario_constraint=deterministic_build.scenario_constraint,
        evidence_refs=llm_output.evidence_refs,
        recent_question_texts=_recent_question_texts(deterministic_build.context.get("turns", [])),
        source_availability=llm_output.source_availability,
        confidence_level=llm_output.confidence_level,
        evidence_signals=deterministic_build.evidence_signals,
    )
    repair_attempted = False
    question_text = llm_output.question_text
    if not quality.allow_emit:
        repair_attempted = True
        question_text = repair_question_text(
            question_text=llm_output.question_text,
            selected_pattern=pattern,
            theme_strategy=question_context.strategy,
            citations=question_context.citations,
        )
        quality = validate_question_quality(
            question_text=question_text,
            selected_pattern=pattern,
            theme_strategy=question_context.strategy,
            scenario_constraint=deterministic_build.scenario_constraint,
            evidence_refs=llm_output.evidence_refs,
            recent_question_texts=_recent_question_texts(deterministic_build.context.get("turns", [])),
            source_availability=llm_output.source_availability,
            confidence_level=llm_output.confidence_level,
            evidence_signals=deterministic_build.evidence_signals,
        )
    if not quality.allow_emit:
        fallback_reason = _quality_fallback_reason(quality)
        return _InvalidAdaptedQuestion(
            fallback_reason=fallback_reason,
            validation_errors=_quality_validation_errors(
                quality,
                deterministic_build=deterministic_build,
                question_text=question_text,
                fallback_reason=fallback_reason,
            ),
            repair_attempted=repair_attempted,
        )

    metadata_model = build_question_metadata(
        question_pattern=pattern.pattern_id,
        scenario_constraint=deterministic_build.scenario_constraint,
        expected_answer_dimensions=pattern.expected_answer_dimensions,
        quality_result=quality,
        evidence_signals=deterministic_build.evidence_signals,
        anti_repeat_refs=tuple(deterministic_build.draft.question_metadata.get("anti_repeat_refs", ())),
        additional_low_confidence_flags=llm_output.low_confidence_flags,
        source_availability=llm_output.source_availability,
    )
    metadata = metadata_model.to_dict()
    for metadata_key in (
        "focus_dimension",
        "focus_key",
        "template_signature",
        "blueprint_signature",
        "duplicate_gate_result",
        "similarity_checked",
        "max_similarity_in_same_category",
        "mastery_exception_used",
    ):
        if metadata_key in deterministic_build.draft.question_metadata:
            metadata[metadata_key] = deterministic_build.draft.question_metadata[metadata_key]
    metadata["confidence_level"] = llm_output.confidence_level
    metadata["expected_answer_dimensions"] = list(llm_output.expected_answer_dimensions or pattern.expected_answer_dimensions)
    metadata["low_confidence_flags"] = _dedupe(
        [*metadata.get("low_confidence_flags", []), *llm_output.low_confidence_flags]
    )
    metadata = _extend_llm_metadata(
        metadata,
        mode=LLM_GENERATION_MODE_ACCEPTED,
        validation_status=LLM_VALIDATION_STATUS_VALID,
        fallback_reason=None,
        provider_summary=provider_summary,
        model_summary=_model_summary(transport_result),
        validation_errors=(),
        repair_attempted=repair_attempted or llm_output.requires_repair or llm_output.pattern_was_aligned,
    )
    draft = replace(
        deterministic_build.draft,
        question_text=question_text,
        evidence_refs=llm_output.evidence_refs,
        question_pattern=pattern.pattern_id,
        quality_score=quality.quality_score,
        confidence_level=llm_output.confidence_level,
        low_confidence_flags=tuple(metadata.get("low_confidence_flags", ())),
        expected_answer_dimensions=tuple(metadata.get("expected_answer_dimensions", ())),
        question_metadata=metadata,
        evidence_signal_refs=metadata_model.evidence_signal_refs,
        builder_version=metadata_model.builder_version,
        validator_version=metadata_model.validator_version,
    )
    return _AdaptedQuestion(draft=draft, repair_attempted=repair_attempted)


@dataclass(frozen=True)
class _InvalidLlmOutput:
    fallback_reason: str
    validation_status: str
    validation_errors: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class _AdaptedQuestion:
    draft: PolishQuestionDraft
    repair_attempted: bool


@dataclass(frozen=True)
class _InvalidAdaptedQuestion:
    fallback_reason: str
    validation_errors: tuple[dict[str, Any], ...]
    repair_attempted: bool


def _fallback_result(
    draft: PolishQuestionDraft,
    *,
    mode: str,
    fallback_reason: str,
    validation_status: str,
    provider_summary: dict[str, Any],
    validation_errors: tuple[dict[str, Any], ...],
    repair_attempted: bool = False,
) -> PolishQuestionLlmResult:
    metadata = _extend_llm_metadata(
        dict(draft.question_metadata),
        mode=mode,
        validation_status=validation_status,
        fallback_reason=fallback_reason,
        provider_summary=provider_summary,
        model_summary={"kind": "not_requested"},
        validation_errors=validation_errors,
        repair_attempted=repair_attempted,
    )
    return PolishQuestionLlmResult(
        draft=replace(draft, question_metadata=metadata),
        llm_output=None,
        llm_generation_mode=mode,
        llm_output_validation_status=validation_status,
        fallback_reason=fallback_reason,
        repair_attempted=repair_attempted,
        validation_errors=validation_errors,
    )


def _extend_llm_metadata(
    metadata: dict[str, Any],
    *,
    mode: str,
    validation_status: str,
    fallback_reason: str | None,
    provider_summary: dict[str, Any],
    model_summary: dict[str, Any],
    validation_errors: tuple[dict[str, Any], ...],
    repair_attempted: bool,
) -> dict[str, Any]:
    metadata.update(
        {
            "llm_task_type": POLISH_QUESTION_GENERATION_TASK_TYPE,
            "prompt_version": POLISH_QUESTION_GENERATION_PROMPT_VERSION,
            "question_schema_version": POLISH_QUESTION_GENERATION_SCHEMA_VERSION,
            "llm_output_validation_status": validation_status,
            "llm_generation_mode": mode,
            "fallback_reason": fallback_reason,
            "repair_attempted": repair_attempted,
            "provider_summary": provider_summary,
            "model_summary": model_summary,
            "validation_errors": [dict(item) for item in validation_errors],
            "redaction_boundary": "safe_llm_summary_only",
        }
    )
    return metadata


def _invalid(
    reason: str,
    validation_status: str,
    code: str,
    detail: str | None = None,
    *,
    diagnostics: dict[str, Any] | None = None,
) -> _InvalidLlmOutput:
    error: dict[str, Any] = {"code": code, "message": detail or code}
    if diagnostics:
        error.update(diagnostics)
    return _InvalidLlmOutput(
        fallback_reason=reason,
        validation_status=validation_status,
        validation_errors=(error,),
    )


def _evidence_ref_diagnostics(
    *,
    allowed_refs: tuple[Any, ...],
    returned_refs: list[Any],
    invalid_refs: tuple[Any, ...],
    validation_error_code: str,
    fallback_reason: str,
) -> dict[str, Any]:
    return {
        "validation_error_code": validation_error_code,
        "fallback_reason": fallback_reason,
        "allowed_refs_sample": _safe_ref_sample(allowed_refs),
        "returned_refs_sample": _safe_ref_sample(tuple(returned_refs)),
        "invalid_refs": _safe_ref_sample(invalid_refs),
    }


def _quality_validation_errors(
    quality: Any,
    *,
    deterministic_build: Any,
    question_text: str,
    fallback_reason: str,
) -> tuple[dict[str, Any], ...]:
    return tuple(
        _quality_validation_error(
            issue,
            deterministic_build=deterministic_build,
            question_text=question_text,
            fallback_reason=fallback_reason,
        )
        for issue in quality.blocking_issues
    )


def _quality_validation_error(
    issue: str,
    *,
    deterministic_build: Any,
    question_text: str,
    fallback_reason: str,
) -> dict[str, Any]:
    pattern = deterministic_build.question_pattern
    scenario_constraint = deterministic_build.scenario_constraint
    theme = getattr(deterministic_build.question_context.strategy, "theme", None)
    error: dict[str, Any] = {
        "code": issue,
        "message": "question quality validator blocked LLM output",
        "validation_error_code": issue,
        "fallback_reason": fallback_reason,
        "selected_pattern_id": _safe_diagnostic_text(getattr(pattern, "pattern_id", None), max_chars=80),
        "selected_pattern_name": _safe_diagnostic_text(getattr(pattern, "title", None), max_chars=80),
        "theme": _safe_diagnostic_text(theme, max_chars=40),
    }
    if issue == "missing_pattern_required_elements":
        required_elements = tuple(getattr(pattern, "required_question_elements", ()))
        missing_required = tuple(element for element in required_elements if element not in question_text)
        error.update(
            {
                "required_elements_sample": _safe_token_sample(required_elements),
                "missing_required_elements_sample": _safe_token_sample(missing_required),
            }
        )
    if issue == "missing_business_constraint":
        error.update(
            {
                "business_constraint_label": _safe_diagnostic_text(
                    getattr(scenario_constraint, "business_constraint", None),
                    max_chars=120,
                ),
                "business_constraint_marker_required": ["业务约束", "新业务约束"],
            }
        )
    return error


def _safe_token_sample(values: tuple[Any, ...], *, limit: int = 10) -> list[str]:
    sample: list[str] = []
    for value in values:
        token = _safe_diagnostic_text(value, max_chars=80)
        if not token:
            continue
        sample.append(token)
        if len(sample) >= limit:
            break
    return sample


def _safe_diagnostic_text(value: Any, *, max_chars: int) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    lowered = text.lower()
    if any(
        marker in lowered
        for marker in (
            "prompt",
            "completion",
            "raw_response",
            "provider_payload",
            "api_key",
            "token",
            "secret",
        )
    ):
        return "<redacted>"
    if len(text) > max_chars:
        return f"{text[:max_chars].rstrip()}..."
    return text


def _safe_ref_sample(refs: tuple[Any, ...], *, limit: int = 10) -> list[str]:
    sample: list[str] = []
    for ref in refs:
        ref_id = _safe_ref_id(ref)
        if not ref_id:
            continue
        sample.append(ref_id)
        if len(sample) >= limit:
            break
    return sample


def _safe_ref_id(ref: Any) -> str:
    if not isinstance(ref, str):
        return f"<{type(ref).__name__}>"
    value = ref.strip()
    if not value:
        return ""
    lowered = value.lower()
    if any(
        marker in lowered
        for marker in (
            "prompt",
            "completion",
            "raw_response",
            "provider_payload",
            "api_key",
            "token",
            "secret",
        )
    ):
        return "<redacted_ref>"
    if len(value) > 160:
        return "<redacted_ref>"
    return value


def _quality_fallback_reason(quality: Any) -> str:
    issues = set(getattr(quality, "blocking_issues", ()))
    if "unsupported_entity_reference" in issues:
        return FALLBACK_FABRICATED_ENTITY
    if "answer_leak" in issues:
        return FALLBACK_ANSWER_LEAK
    if "question_too_broad" in issues:
        return FALLBACK_OUTPUT_TOO_BROAD
    if "highly_repeated_recent_question" in issues:
        return FALLBACK_REPEATED_QUESTION
    if issues:
        return FALLBACK_SEMANTIC_INVALID
    return FALLBACK_QUALITY_SCORE_TOO_LOW


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
        status = _string_or_none(getattr(transport, "status", None), max_chars=80)
        if status:
            summary["status"] = status
    if result is not None:
        summary["validation_status"] = str(result.validation_status.value)
        summary["confidence_level"] = str(result.confidence_level.value)
    return summary


def _model_summary(result: LlmTransportResult) -> dict[str, Any]:
    return {"kind": "safe_summary", "model_name": "not_recorded"}


def _input_refs(*, session: Any, deterministic_build: Any) -> tuple[str, ...]:
    refs = [
        getattr(session, "session_id", None),
        getattr(session, "job_version_id", None),
        getattr(session, "resume_version_id", None),
        deterministic_build.question_context.progress_node_ref,
        deterministic_build.question_context.context_digest,
    ]
    return tuple(str(ref) for ref in refs if ref)


def _forbidden_paths(value: object, *, prefix: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).strip().lower()
            path = f"{prefix}.{normalized}" if prefix else normalized
            if normalized in _FORBIDDEN_OUTPUT_KEYS:
                paths.append(path)
            paths.extend(_forbidden_paths(item, prefix=path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_forbidden_paths(item, prefix=f"{prefix}[{index}]"))
    return paths


def _recent_question_texts(turns: object) -> list[str]:
    if not isinstance(turns, list):
        return []
    result: list[str] = []
    for turn in turns[-5:]:
        if isinstance(turn, dict):
            text = _string_or_none(turn.get("question_text"), max_chars=400)
            if text:
                result.append(text)
    return result


def _string_list(value: object, *, limit: int, max_chars: int = 240) -> list[str]:
    if isinstance(value, str):
        raw_items: list[object] = [value]
    elif isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        return []
    result: list[str] = []
    for item in raw_items:
        text = _string_or_none(item, max_chars=max_chars)
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def _string_or_none(value: object, *, max_chars: int) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text[:max_chars] if text else None


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in _TRUTHY


def _safe_error(exc: Exception) -> str:
    return str(exc).strip()[:160] or exc.__class__.__name__
