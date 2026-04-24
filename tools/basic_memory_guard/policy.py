from __future__ import annotations

from dataclasses import dataclass


DEFAULT_PROJECT = "AiForInterviewer"
DEFAULT_MEMORY_ROOT = "D:/.basic-memory/AiForInterviewer"
ALLOWED_WRITE_DIRECTORIES = frozenset(
    {
        "00-project",
        "20-decisions",
        "30-open-questions",
        "60-risks-constraints",
        "90-session-summaries",
    }
)
DECISION_ALLOWED_STATUSES = frozenset({"confirmed", "accepted", "approved"})


class PolicyError(ValueError):
    """Raised when a write request violates guard policy."""


@dataclass(frozen=True)
class NormalizedRequest:
    directory: str
    decision_status: str | None


def normalize_directory(directory: str) -> str:
    normalized = (directory or "").strip().replace("\\", "/").strip("/")
    if not normalized:
        raise PolicyError("禁止写入根目录或空目录。")
    if normalized == ".":
        raise PolicyError("禁止写入根目录或空目录。")
    lowered = normalized.lower()
    if lowered == "notes" or lowered.startswith("notes/"):
        raise PolicyError("禁止写入 notes/ 目录。")
    if normalized not in ALLOWED_WRITE_DIRECTORIES:
        allowed = ", ".join(sorted(ALLOWED_WRITE_DIRECTORIES))
        raise PolicyError(f"目录 `{normalized}` 不在白名单内。允许目录: {allowed}")
    return normalized


def normalize_decision_status(status: str | None) -> str | None:
    if status is None:
        return None
    normalized = status.strip().lower()
    return normalized or None


def validate_request(directory: str, decision_status: str | None) -> NormalizedRequest:
    normalized_directory = normalize_directory(directory)
    normalized_status = normalize_decision_status(decision_status)
    if (
        normalized_directory == "20-decisions"
        and normalized_status not in DECISION_ALLOWED_STATUSES
    ):
        allowed = ", ".join(sorted(DECISION_ALLOWED_STATUSES))
        raise PolicyError(
            "写入 `20-decisions` 前必须显式标记为已确认状态。"
            f" 允许状态: {allowed}"
        )
    return NormalizedRequest(
        directory=normalized_directory,
        decision_status=normalized_status,
    )

