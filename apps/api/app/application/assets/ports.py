"""Asset ports."""

from typing import Any, Protocol

from app.domain.shared.refs import ResourceRef


class AssetActionError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class AssetRepository(Protocol):
    def get_ref(self, asset_id: str) -> ResourceRef | None: ...

    def list_assets(
        self,
        *,
        owner_id: str,
        status: str | None = None,
        asset_type: str | None = None,
        q: str | None = None,
    ) -> tuple[dict[str, Any], ...]: ...

    def get_asset(self, *, owner_id: str, asset_id: str) -> dict[str, Any] | None: ...

    def create_asset(
        self,
        *,
        owner_id: str,
        actor_id: str,
        title: str,
        asset_type: str,
        content: str,
        summary: str | None,
        rag_chunks: tuple[dict[str, Any], ...],
        embedding_model: str,
        embedding_dimension: int,
    ) -> dict[str, Any]: ...

    def update_status(
        self,
        *,
        owner_id: str,
        actor_id: str,
        asset_id: str,
        status: str,
        action: str,
    ) -> dict[str, Any]: ...
