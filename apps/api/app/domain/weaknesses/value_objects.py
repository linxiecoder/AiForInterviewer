"""Weakness value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WeaknessTitle:
    normalized_title: str

