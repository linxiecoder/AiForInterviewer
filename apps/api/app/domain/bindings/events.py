"""Binding domain events."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BindingCreated:
    binding_id: str

