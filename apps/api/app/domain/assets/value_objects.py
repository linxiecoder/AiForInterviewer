"""Asset value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AssetTitle:
    normalized_title: str

