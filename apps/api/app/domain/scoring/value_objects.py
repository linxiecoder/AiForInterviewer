"""Scoring value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreScale:
    value: str = "0_100_product_scale"

