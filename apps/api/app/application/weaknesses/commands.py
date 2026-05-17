"""Weakness commands."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateWeaknessCandidateTaskCommand:
    source_ref_id: str

