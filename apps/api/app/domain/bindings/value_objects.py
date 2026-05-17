"""Binding value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BindingStatus:
    value: str

