"""Shared helpers for parsing trusted structured LLM output envelopes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


UNTRUSTED_STRUCTURED_METADATA_KEYS = frozenset(
    {"generated_at", "model_name", "session_id", "job_id", "resume_id"}
)


@dataclass(frozen=True)
class StructuredOutputValidationError:
    field: str
    code: str
    reason: str


@dataclass(frozen=True)
class StructuredOutputParseResult:
    ok: bool
    canonical_status: str | None
    warnings: tuple[str, ...]
    validation_errors: tuple[StructuredOutputValidationError, ...]


def normalize_structured_status(
    value: object,
) -> tuple[str | None, tuple[str, ...], tuple[StructuredOutputValidationError, ...]]:
    """Normalize provider status aliases before business payload validation."""

    raw_status = str(value or "").strip().lower()
    if raw_status == "success":
        return "success", (), ()
    if raw_status == "partial":
        return "partial", (), ()
    if raw_status == "ready":
        return "success", ("status_ready_normalized",), ()
    if raw_status == "ok":
        return "success", ("status_ok_normalized",), ()
    if raw_status == "done":
        return "success", ("status_done_normalized",), ()
    if not raw_status:
        return "success", ("status_missing_normalized",), ()
    if raw_status in {"failed", "fail", "error"}:
        return (
            None,
            (),
            (
                StructuredOutputValidationError(
                    field="status",
                    code="failed",
                    reason="Structured output status reports failure.",
                ),
            ),
        )
    return (
        None,
        (),
        (
            StructuredOutputValidationError(
                field="status",
                code="unsupported",
                reason="status must be success or partial.",
            ),
        ),
    )


def parse_structured_output_status(value: object) -> StructuredOutputParseResult:
    status, warnings, errors = normalize_structured_status(value)
    return StructuredOutputParseResult(
        ok=not errors,
        canonical_status=status,
        warnings=warnings,
        validation_errors=errors,
    )


def filter_untrusted_structured_metadata(metadata: object) -> tuple[dict[str, Any], tuple[str, ...]]:
    if not isinstance(metadata, dict):
        return {}, ()
    trusted = {
        key: value
        for key, value in metadata.items()
        if key not in UNTRUSTED_STRUCTURED_METADATA_KEYS
    }
    ignored = tuple(sorted(key for key in metadata if key in UNTRUSTED_STRUCTURED_METADATA_KEYS))
    return trusted, ignored


def structured_validation_errors_to_dicts(
    errors: tuple[StructuredOutputValidationError, ...],
) -> list[dict[str, str]]:
    return [
        {"field": error.field, "code": error.code, "reason": error.reason}
        for error in errors
    ]
