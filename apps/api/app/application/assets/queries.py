"""Asset queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetAssetQuery:
    asset_id: str

