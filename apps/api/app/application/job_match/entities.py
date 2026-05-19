"""Application entities for job match analyses."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class JobMatchAnalysis:
    analysis_id: str
    owner_id: str
    actor_id: str
    binding_id: str
    resume_id: str
    resume_version_id: str
    job_id: str
    job_version_id: str
    status: str
    overall_score: int | None
    overall_level: str | None
    confidence: str | None
    result_payload_json: dict[str, Any]
    markdown_report_text: str | None
    score_rule_version: str
    prompt_version: str
    model_name: str
    source_digest: str
    created_at: datetime
    updated_at: datetime
