"""Asset domain events."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AssetConfirmed:
    asset_id: str

