"""Binding queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetBindingQuery:
    binding_id: str

