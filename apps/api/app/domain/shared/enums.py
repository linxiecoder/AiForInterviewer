"""Canonical enums shared by F5 backend modules."""

from enum import Enum


class StrEnum(str, Enum):
    """String enum base for stable API/domain values."""

    def __str__(self) -> str:
        return self.value


class ApiStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    LOW_CONFIDENCE = "low_confidence"
    ACCEPTED = "accepted"
    QUEUED = "queued"
    RUNNING = "running"
    VALIDATION_FAILED = "validation_failed"
    GENERATION_FAILED = "generation_failed"


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT = "insufficient"


class ValidationStatus(StrEnum):
    VALID = "valid"
    VALID_WITH_WARNINGS = "valid_with_warnings"
    INVALID = "invalid"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class SourceAvailability(StrEnum):
    SOURCE_AVAILABLE = "source_available"
    SOURCE_ARCHIVED = "source_archived"
    SOURCE_DELETED = "source_deleted"
    SOURCE_DISABLED = "source_disabled"
    SOURCE_UNAVAILABLE = "source_unavailable"


class AiTaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    LOW_CONFIDENCE = "low_confidence"
    VALIDATION_FAILED = "validation_failed"
    SOURCE_UNAVAILABLE = "source_unavailable"
    GENERATION_FAILED = "generation_failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


class ScoreType(StrEnum):
    JOB_MATCH = "job_match"
    POLISH_ANSWER = "polish_answer"
    POLISH_REPORT = "polish_report"
    PRESSURE_SESSION = "pressure_session"
    REPORT_SECTION = "report_section"


class PassTendencyLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CAUTION = "caution"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


API_ERROR_CODES = frozenset(
    {
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
    }
)

