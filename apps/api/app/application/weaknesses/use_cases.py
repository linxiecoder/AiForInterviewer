"""Weakness use cases."""

from typing import Any

from app.application.common.result import ApplicationResult
from app.application.weaknesses.ports import WeaknessActionError, WeaknessRepository
from app.domain.shared.errors import DomainError


WEAKNESS_STATUSES = {
    "weakness_detected",
    "weakness_confirmed",
    "low_priority",
    "ignored",
    "resolved",
    "reopened",
}

WEAKNESS_SEVERITIES = {"low", "medium", "high", "critical"}
WEAKNESS_DELETED_STATUS = "deleted"


class WeaknessUseCases:
    def __init__(self, repository: WeaknessRepository) -> None:
        self._repository = repository

    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="weakness_skeleton")

    def list_weaknesses(
        self,
        *,
        owner_id: str,
        status: str | None = None,
        severity: str | None = None,
        q: str | None = None,
    ) -> ApplicationResult[tuple[dict[str, Any], ...]]:
        validation_error = _validate_filters(status=status, severity=severity)
        if validation_error is not None:
            return ApplicationResult(error=validation_error)
        return ApplicationResult(
            value=self._repository.list_weaknesses(
                owner_id=owner_id,
                status=status,
                severity=severity,
                q=_normalize_optional(q),
            )
        )

    def get_weakness(self, *, owner_id: str, weakness_id: str) -> ApplicationResult[dict[str, Any]]:
        weakness = self._repository.get_weakness(owner_id=owner_id, weakness_id=weakness_id)
        if weakness is None:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Weakness not found.")
            )
        return ApplicationResult(value=weakness)

    def update_status(
        self,
        *,
        owner_id: str,
        actor_id: str,
        weakness_id: str,
        status: str,
    ) -> ApplicationResult[dict[str, Any]]:
        if status not in WEAKNESS_STATUSES:
            return ApplicationResult(
                error=DomainError(code="validation_failed", message="Unsupported weakness status.")
            )
        try:
            return ApplicationResult(
                value=self._repository.update_status(
                    owner_id=owner_id,
                    actor_id=actor_id,
                    weakness_id=weakness_id,
                    status=status,
                )
            )
        except WeaknessActionError as exc:
            return ApplicationResult(error=DomainError(code=exc.code, message=exc.message))

    def soft_delete_weakness(
        self,
        *,
        owner_id: str,
        actor_id: str,
        weakness_id: str,
    ) -> ApplicationResult[dict[str, Any]]:
        try:
            return ApplicationResult(
                value=self._repository.soft_delete(
                    owner_id=owner_id,
                    actor_id=actor_id,
                    weakness_id=weakness_id,
                )
            )
        except WeaknessActionError as exc:
            return ApplicationResult(error=DomainError(code=exc.code, message=exc.message))


def _validate_filters(*, status: str | None, severity: str | None) -> DomainError | None:
    if status is not None and status not in WEAKNESS_STATUSES:
        return DomainError(code="validation_failed", message="Unsupported weakness status.")
    if severity is not None and severity not in WEAKNESS_SEVERITIES:
        return DomainError(code="validation_failed", message="Unsupported weakness severity.")
    return None


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
