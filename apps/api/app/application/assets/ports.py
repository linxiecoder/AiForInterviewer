"""Asset ports."""

from typing import Protocol

from app.domain.shared.refs import ResourceRef


class AssetRepository(Protocol):
    def get_ref(self, asset_id: str) -> ResourceRef | None: ...

