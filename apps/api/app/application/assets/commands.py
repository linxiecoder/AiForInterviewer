"""Asset commands."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateAssetCandidateTaskCommand:
    source_ref_id: str

