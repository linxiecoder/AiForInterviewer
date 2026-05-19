"""Job match ports."""

from dataclasses import dataclass
from typing import Protocol
from typing import Any

from app.application.job_match.entities import JobMatchAnalysis
from app.domain.shared.refs import ResourceRef
from app.schemas.job_match import JobMatchResultPayload, JobMatchSourceBundle


@dataclass(frozen=True)
class JobMatchAnalyzerOutput:
    payload: JobMatchResultPayload | dict[str, Any]
    prompt_version: str
    model_name: str


class JobMatchAnalyzerUnavailableError(RuntimeError):
    """Raised when the configured LLM provider cannot generate an analysis."""


class JobMatchAnalyzer(Protocol):
    def analyze(self, source_bundle: JobMatchSourceBundle) -> JobMatchAnalyzerOutput: ...


class JobMatchRepository(Protocol):
    def add(self, analysis: JobMatchAnalysis) -> None: ...

    def get(self, analysis_id: str) -> JobMatchAnalysis | None: ...

    def get_latest_by_binding(self, owner_id: str, binding_id: str) -> JobMatchAnalysis | None: ...

    def get_ref(self, analysis_id: str) -> ResourceRef | None: ...
