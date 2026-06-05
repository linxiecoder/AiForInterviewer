from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest

from app.application.job_match.ports import JobMatchAnalyzerUnavailableError
from app.application.llm.types import LlmTransportRequest, LlmTransportResult
from app.application.polish import progress_tree
from app.domain.shared.enums import ConfidenceLevel, ValidationStatus
from app.infrastructure.llm import job_match


class _RecordingTransport:
    def __init__(self) -> None:
        self.requests: list[LlmTransportRequest] = []

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        self.requests.append(request)
        if request.task_type == "job_match_analysis":
            payload: dict[str, Any] = {
                "job_match_result_payload": {
                    "overall_score": 60,
                    "overall_level": "medium_match",
                    "confidence": "medium",
                    "summary": "基于测试 transport 的岗位匹配摘要。",
                    "dimension_scores": [],
                    "matched_requirements": [],
                    "missing_requirements": [],
                    "resume_evidence": [],
                    "risk_flags": [],
                    "interview_focus": [],
                    "suggested_questions": [],
                    "markdown_report": "",
                }
            }
        else:
            payload = {"status": "success", "menu_categories": []}
        return LlmTransportResult(
            result=payload,
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.MEDIUM,
            low_confidence_flags=(),
            trace_refs=(),
            evidence_refs=(),
        )


def test_direct_llm_transport_request_rejects_forbidden_keys() -> None:
    with pytest.raises(ValueError, match=r"forbidden_provider_request_key:.*full_answer"):
        LlmTransportRequest(
            contract_ids=("P-PROVIDER-BACKSTOP",),
            task_type="provider_backstop_probe",
            input_refs=("safe_ref",),
            evidence_bundle={"safe_ref": "safe", "nested": {"full_answer": "must not reach provider"}},
        )


def test_dataclass_replace_cannot_inject_forbidden_provider_payload() -> None:
    request = LlmTransportRequest(
        contract_ids=("P-PROVIDER-BACKSTOP",),
        task_type="provider_backstop_probe",
        input_refs=("safe_ref",),
        evidence_bundle={"safe_ref": "safe"},
    )

    with pytest.raises(ValueError, match=r"forbidden_provider_request_key:.*raw_provider_payload"):
        replace(request, evidence_bundle={"safe_ref": "safe", "raw_provider_payload": {"secret": "x"}})


def test_progress_tree_rejects_forbidden_provider_prompt_before_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = _RecordingTransport()
    monkeypatch.setattr(progress_tree, "has_sufficient_progress_context", lambda _context: True)
    monkeypatch.setattr(progress_tree, "_input_refs", lambda _context: ("polish_session:1",))
    monkeypatch.setattr(
        progress_tree,
        "build_progress_quality_first_menu_prompt",
        lambda _context: {
            "source_digest": "sha256:test",
            "task_type": "polish_progress_quality_first_menu",
            "prompt_version": "progress_tree_quality_first_menu.v1",
            "schema_id": "polish_progress_tree_quality_first_menu.v1",
            "schema_version": "v1",
            "prompt": "safe prompt",
            "context": {"safe_ref": "context_ref"},
            "output_schema": {"schema_id": "polish_progress_tree_quality_first_menu.v1"},
            "full_answer": "must not reach provider",
        },
    )

    result = progress_tree.PolishProgressTreeLlmService(transport).generate_initial(
        {"content_digest": "sha256:test"}
    )

    assert transport.requests == []
    assert result["status"] == progress_tree.PROGRESS_TREE_STATUS_FAILED
    assert result["progress_tree_plan"]["failure_reason"] == "provider_request_validation_failed"


def test_job_match_rejects_forbidden_provider_payload_before_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = _RecordingTransport()
    monkeypatch.setattr(job_match, "_source_input_refs", lambda _source_bundle: ("resume_version:1",))
    monkeypatch.setattr(
        job_match,
        "_evidence_bundle",
        lambda _source_bundle: {
            "source_digest": "sha256:test",
            "resume_chunks": [],
            "job_requirement_chunks": [],
            "full_resume": "must not reach provider",
        },
    )
    source_bundle = SimpleNamespace(
        resume_chunks=[
            SimpleNamespace(
                chunk_id="resume:summary:1",
                resume_version_id="resume_version_1",
                text="FastAPI backend automation.",
            )
        ],
        job_requirement_chunks=[
            SimpleNamespace(
                chunk_id="job:requirement:1",
                job_version_id="job_version_1",
                requirement_type="requirement",
                text="FastAPI backend experience.",
            )
        ],
    )

    with pytest.raises(JobMatchAnalyzerUnavailableError, match="provider_request_validation_failed"):
        job_match.LlmJobMatchAnalyzer(transport).analyze(source_bundle)  # type: ignore[arg-type]

    assert transport.requests == []
