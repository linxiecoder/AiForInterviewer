from app.domain.shared.enums import ConfidenceLevel, ValidationStatus
from app.application.polish.progress_prompts import (
    POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
)
from app.application.polish.progress_v2_prompts import POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE
from app.infrastructure.llm.contracts import SUPPORTED_FAKE_TASK_TYPES
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


def test_fake_quality_first_menu_does_not_branch_on_audit_hardware_sample() -> None:
    result = FakeLlmTransport().generate(
        LlmTransportRequest(
            contract_ids=("P-POLISH-001", "P-SHARED-001", "P-SHARED-003"),
            task_type=POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE,
            input_refs=("sess_1", "job_ver_1", "res_ver_1"),
            evidence_bundle={
                "context": {
                    "resume_markdown": (
                        "- 面向硬件测试部门构建智能辅助平台\n"
                        "- 设计设备日志采集、异常告警和质量复盘流程"
                    ),
                    "job_payload": {
                        "requirements": ["数据平台可靠性、告警治理和上线验证能力"],
                        "responsibilities": ["负责跨团队质量数据治理和指标复盘"],
                    },
                },
            },
        )
    )

    labels = [
        node["display_title"]
        for category in result.result["menu_categories"]
        for node in category["nodes"]
    ]
    assert "硬件测试智能辅助平台的服务端架构设计" not in labels
    assert "硬件测试知识库的切片与索引设计" not in labels
    assert any("硬件测试部门构建智能辅助平台" in label or "设备日志采集" in label for label in labels)


def test_fake_transport_advertises_only_canonical_progress_tree_generation_task() -> None:
    retired_progress_tasks = {
        "polish_progress_" + "global_understanding",
        "polish_progress_tree_" + "draft",
        "polish_progress_tree_" + "critic",
        "polish_progress_tree_" + "grounding",
    }

    assert POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE in SUPPORTED_FAKE_TASK_TYPES
    assert retired_progress_tasks.isdisjoint(SUPPORTED_FAKE_TASK_TYPES)
