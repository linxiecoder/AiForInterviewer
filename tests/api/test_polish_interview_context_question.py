from __future__ import annotations

from typing import Any

import app.application.polish.question_generation_service as question_generation_service
from app.application.polish.context.source_support import SourceSupportBuildResult
from app.application.polish.canonical_evidence import SourceSupportSummary
from tests.api.test_polish_question_refactor_phase1 import (
    NODE_REF,
    _question_generation_inputs,
)


def test_interview_context_builder_adds_source_support_summary_to_question_context() -> None:
    from app.application.polish.context.interview_context import InterviewContextBuilder

    context = InterviewContextBuilder().build_question_context(
        {
            "content_digest": "ctx_question",
            "canonical_project_assets": {
                "available": True,
                "items": [
                    {
                        "asset_id": "asset_backend_workflow",
                        "status": "asset_confirmed",
                        "asset_type": "project_story",
                    }
                ],
            },
            "canonical_evidence_pack": {
                "schema_version": "canonical_evidence_pack.v1",
                "source_support_level": "insufficient_context",
                "context_digest": "canonical_digest",
            },
        }
    )

    assert context["source_support_summary"]["level"] == "direct_project_evidence"
    assert context["source_support_level"] == "direct_project_evidence"
    assert context["canonical_evidence_pack"]["source_support_summary"] == context["source_support_summary"]
    assert context["canonical_evidence_pack"]["source_support_level"] == "direct_project_evidence"


def test_question_evidence_scope_uses_shared_source_support_service(monkeypatch: Any) -> None:
    calls: list[dict[str, Any]] = []

    class _RecordingSourceSupportSummaryService:
        def build(self, **kwargs: Any) -> SourceSupportBuildResult:
            calls.append(kwargs)
            return SourceSupportBuildResult(
                summary=SourceSupportSummary(
                    level="job_gap_only",
                    job_gap_refs=({"resource_type": "match_gap", "resource_id": "forced_gap"},),
                    reason_codes=("forced_test_summary",),
                    confidence="medium",
                )
            )

    monkeypatch.setattr(
        question_generation_service,
        "SourceSupportSummaryService",
        _RecordingSourceSupportSummaryService,
    )
    _session, context, plan, state = _question_generation_inputs(
        primary_text="候选人简历提到 FastAPI 和 PostgreSQL 项目治理。",
        primary_source_type="resume_project",
    )

    scope = question_generation_service._build_evidence_scope(
        context=context,
        plan=plan,
        state=state,
        node=plan["nodes"][0],
        requested_ref=NODE_REF,
        source_priority_policy={},
    )

    assert calls
    assert calls[0]["evidence_chunks"]
    assert scope.source_support_level == "job_gap_only"
