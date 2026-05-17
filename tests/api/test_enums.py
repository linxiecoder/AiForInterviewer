from app.domain.shared.enums import (
    API_ERROR_CODES,
    AiTaskStatus,
    ApiStatus,
    ConfidenceLevel,
    PassTendencyLevel,
    RiskLevel,
    ScoreType,
    SourceAvailability,
    ValidationStatus,
)


def test_canonical_enums_include_required_values() -> None:
    assert {item.value for item in ApiStatus} == {
        "success",
        "partial",
        "low_confidence",
        "accepted",
        "queued",
        "running",
        "validation_failed",
        "generation_failed",
    }
    assert {item.value for item in ConfidenceLevel} == {"high", "medium", "low", "insufficient"}
    assert {item.value for item in ValidationStatus} == {
        "valid",
        "valid_with_warnings",
        "invalid",
        "manual_review_required",
    }
    assert {item.value for item in SourceAvailability} == {
        "source_available",
        "source_archived",
        "source_deleted",
        "source_disabled",
        "source_unavailable",
    }
    assert {item.value for item in AiTaskStatus} == {
        "queued",
        "running",
        "succeeded",
        "partial",
        "low_confidence",
        "validation_failed",
        "source_unavailable",
        "generation_failed",
        "timed_out",
        "cancelled",
    }
    assert {item.value for item in ScoreType} == {
        "job_match",
        "polish_answer",
        "polish_report",
        "pressure_session",
        "report_section",
    }
    assert {item.value for item in PassTendencyLevel} == {
        "low",
        "medium",
        "high",
        "caution",
        "insufficient_evidence",
    }
    assert {item.value for item in RiskLevel} == {"low", "medium", "high", "unknown"}


def test_stable_error_codes_include_required_values() -> None:
    assert {
        "unauthenticated",
        "permission_denied",
        "owner_mismatch",
        "not_found_or_inaccessible",
        "validation_failed",
        "stale_version_conflict",
        "idempotency_required",
        "idempotency_conflict",
        "source_unavailable",
        "low_confidence",
        "generation_failed",
        "provider_unavailable",
        "task_timeout",
        "task_cancelled",
        "task_retry_not_allowed",
        "rate_limited",
        "copy_boundary_violation",
        "export_not_supported",
        "internal_error",
    }.issubset(API_ERROR_CODES)

