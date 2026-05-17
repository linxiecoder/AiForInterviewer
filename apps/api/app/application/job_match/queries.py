"""Job match queries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GetJobMatchAnalysisQuery:
    analysis_id: str

