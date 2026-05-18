"""Binding query objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetBindingQuery:
    owner_id: str
    binding_id: str


@dataclass(frozen=True)
class ListBindingsByJobQuery:
    owner_id: str
    job_id: str
