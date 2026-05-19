from app.domain.shared.enums import ConfidenceLevel, ValidationStatus
from app.application.polish.progress_prompts import (
    POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
    POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID,
    POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
)
from app.infrastructure.llm.fake_transport import FakeLlmTransport
from app.infrastructure.llm.types import LlmTransportRequest
from app.schemas.job_match import JobRequirementChunk, ResumeChunk


def test_fake_llm_transport_is_deterministic() -> None:
    transport = FakeLlmTransport()
    resume_chunk = ResumeChunk(
        chunk_id="resume:summary:001",
        resume_version_id="res_ver_1",
        section_label="summary",
        text="Python FastAPI backend workflow automation.",
    )
    job_chunk = JobRequirementChunk(
        chunk_id="job:requirement:001",
        job_version_id="job_ver_1",
        requirement_type="requirement",
        text="Python and FastAPI backend experience.",
    )
    request = LlmTransportRequest(
        contract_ids=("P-JOBMATCH-001", "P-JOBMATCH-002"),
        task_type="job_match_analysis",
        input_refs=("res_1", "job_1"),
        evidence_bundle={
            "source_digest": "sha256:test",
            "resume_chunks": [resume_chunk.model_dump(mode="json")],
            "job_requirement_chunks": [job_chunk.model_dump(mode="json")],
        },
    )

    first = transport.generate(request)
    second = transport.generate(request)

    assert first == second
    assert first.validation_status is ValidationStatus.VALID
    assert first.confidence_level is ConfidenceLevel.MEDIUM
    assert first.low_confidence_flags == ()
    assert first.result["transport"] == "fake"
    assert first.result["model_name"] == "fake_llm_job_match_v1"
    assert first.result["job_match_result_payload"]["overall_score"] != 82
    assert "probability" not in first.result


def test_fake_llm_transport_marks_missing_evidence_as_low_confidence() -> None:
    result = FakeLlmTransport().generate(
        LlmTransportRequest(
            contract_ids=("P-REPORT-001",),
            task_type="report_generation",
            input_refs=("sess_1",),
        )
    )

    assert result.validation_status is ValidationStatus.VALID_WITH_WARNINGS
    assert result.confidence_level is ConfidenceLevel.LOW
    assert result.low_confidence_flags == ("evidence_missing",)


def test_fake_llm_transport_generates_polish_progress_tree_json() -> None:
    result = FakeLlmTransport().generate(
        LlmTransportRequest(
            contract_ids=("P-POLISH-001", "P-SHARED-001", "P-SHARED-003"),
            task_type="polish_progress_tree_plan",
            input_refs=("sess_1", "job_ver_1", "res_ver_1"),
            evidence_bundle={
                "source_digest": "sha256:test",
                "context": {
                    "job_snapshot": {
                        "requirements": ["Python and FastAPI experience."],
                        "responsibilities": ["Own backend APIs."],
                    },
                    "resume_snapshot": {
                        "project_experiences": ["Built backend workflow automation."],
                        "summary": "Backend resume",
                    },
                },
            },
        )
    )

    assert result.validation_status is ValidationStatus.VALID
    assert result.result["prompt_version"] == POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION
    assert result.result["schema_id"] == POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID
    assert result.result["schema_version"] == POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION
    assert result.result["progress_tree_plan"]["schema_id"] == POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID
    assert result.result["progress_tree_plan"]["schema_version"] == POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION
    assert result.result["progress_tree_state"]["schema_id"] == POLISH_PROGRESS_TREE_STATE_SCHEMA_ID
    assert result.result["progress_tree_state"]["schema_version"] == POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION
    assert result.result["progress_tree_plan"]["nodes"][0]["progress_node_ref"] == "fake_llm_progress_backend_api"
    assert result.result["progress_tree_state"]["current_priority"]["progress_node_ref"] == "fake_llm_progress_backend_api_fastapi"
