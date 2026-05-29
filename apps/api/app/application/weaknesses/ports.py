"""Weakness ports."""

from typing import Any, Protocol

from app.domain.shared.refs import ResourceRef


class WeaknessActionError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class WeaknessRepository(Protocol):
    def get_ref(self, weakness_id: str) -> ResourceRef | None: ...

    def list_weaknesses(
        self,
        *,
        owner_id: str,
        status: str | None = None,
        severity: str | None = None,
        q: str | None = None,
    ) -> tuple[dict[str, Any], ...]: ...

    def get_weakness(self, *, owner_id: str, weakness_id: str) -> dict[str, Any] | None: ...

    def update_status(
        self,
        *,
        owner_id: str,
        actor_id: str,
        weakness_id: str,
        status: str,
    ) -> dict[str, Any]: ...

    def soft_delete(
        self,
        *,
        owner_id: str,
        actor_id: str,
        weakness_id: str,
    ) -> dict[str, Any]: ...
