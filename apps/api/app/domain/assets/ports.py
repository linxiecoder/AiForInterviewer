"""Asset domain ports."""

from typing import Protocol

from app.domain.assets.entities import Asset


class AssetReader(Protocol):
    def get(self, asset_id: str) -> Asset | None: ...

