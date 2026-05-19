"""Job match queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetJobMatchAnalysisQuery:
    owner_id: str
    analysis_id: str


@dataclass(frozen=True)
class GetLatestJobMatchAnalysisQuery:
    owner_id: str
    binding_id: str
