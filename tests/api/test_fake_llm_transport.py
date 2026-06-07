from app.domain.shared.enums import ConfidenceLevel, ValidationStatus
from app.application.polish.feedback_schema import POLISH_FEEDBACK_CANDIDATE_PAYLOAD_FIELDS
from app.application.polish.progress_prompts import (
    POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
)
from tests.fakes.llm_transport import FakeLlmTransport, SUPPORTED_FAKE_TASK_TYPES
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


def test_fake_quality_first_menu_uses_current_quality_first_shape() -> None:
    result = FakeLlmTransport().generate(
        LlmTransportRequest(
            contract_ids=("P-POLISH-001", "P-SHARED-001", "P-SHARED-003"),
            task_type=POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE,
            input_refs=("sess_1", "job_ver_1", "res_ver_1"),
            evidence_bundle={
                "context": {
                    "resume_markdown": "\n".join(
                        [
                            "- 主导 FastAPI 服务编排与异步任务补偿",
                            "- 负责 RAG 检索质量评估和上线复盘",
                            "- 设计权限边界、异常降级和可观测性链路",
                            "- 推动跨团队指标治理和故障恢复演练",
                            "- 沉淀 AI Agent 工具调用和任务规划经验",
                            "- 建立服务端接口契约和回归测试策略",
                        ]
                    ),
                    "job_payload": {
                        "requirements": [
                            "Java 服务端高可用架构设计",
                            "AI Agent 工具调用机制",
                            "服务治理、性能瓶颈定位与灰度发布",
                            "RAG 评测和数据质量治理",
                            "跨团队工程协作与风险复盘",
                        ],
                        "responsibilities": ["负责 AI 面试训练平台的后端架构和质量治理"],
                    },
                },
            },
        )
    )

    categories = {
        category["category"]: category["nodes"]
        for category in result.result["menu_categories"]
    }
    metadata = result.result.get("metadata") or {}
    assert result.result["status"] == "success"
    assert 6 <= sum(len(nodes) for nodes in categories.values()) <= 9
    assert 4 <= len(categories["resume_deep_dive"]) <= 6
    assert 2 <= len(categories["jd_gap_learning"]) <= 4
    assert "quality_target" not in metadata


def test_fake_transport_advertises_only_canonical_progress_tree_generation_task() -> None:
    retired_progress_tasks = {
        "polish_progress_" + "global_understanding",
        "polish_progress_tree_" + "draft",
        "polish_progress_tree_" + "critic",
        "polish_progress_tree_" + "grounding",
    }

    assert POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE in SUPPORTED_FAKE_TASK_TYPES
    assert retired_progress_tasks.isdisjoint(SUPPORTED_FAKE_TASK_TYPES)


def test_fake_feedback_generation_prefers_agent_input_data_over_top_level_context() -> None:
    result = FakeLlmTransport().generate(
        LlmTransportRequest(
            contract_ids=("P-POLISH-003", "P-SHARED-001", "P-SHARED-003"),
            task_type="polish_feedback_generation",
            input_refs=("sess_fake_feedback", "ans_fake_feedback"),
            evidence_bundle={
                "current_question": {
                    "question_text": "TOP LEVEL QUESTION SHOULD NOT WIN",
                },
                "current_answer": {
                    "answer_text": "TOP LEVEL ANSWER SHOULD NOT WIN",
                },
                "input_data": {
                    "current_question": {
                        "question_text": "INPUT DATA QUESTION SHOULD WIN",
                    },
                    "current_answer": {
                        "answer_text": "INPUT DATA ANSWER SHOULD WIN",
                    },
                },
            },
        )
    )

    assert result.validation_status is ValidationStatus.VALID
    assert result.result["answer_summary"] == "候选人回答摘要：INPUT DATA ANSWER SHOULD WIN"
    assert "TOP LEVEL QUESTION" not in result.result["answer_summary"]
    assert "TOP LEVEL ANSWER" not in result.result["answer_summary"]


def test_fake_feedback_candidate_payload_passes_validator_without_future_sections() -> None:
    from app.application.polish.feedback_validation import validate_feedback_candidate_payload

    result = FakeLlmTransport().generate(
        LlmTransportRequest(
            contract_ids=("P-POLISH-003", "P-POLISH-004", "P-POLISH-005"),
            task_type="polish_feedback_generation",
            input_refs=("sess_fake_feedback", "ans_fake_feedback"),
            evidence_bundle={
                "feedback_mode": "candidate_compact",
                "input_data": {
                    "current_question": {"question_text": "如何设计混合检索策略？"},
                    "current_answer": {"answer_text": "我会结合关键词召回、向量召回和重排。"},
                },
            },
        )
    )

    candidate_payload = {key: result.result[key] for key in POLISH_FEEDBACK_CANDIDATE_PAYLOAD_FIELDS if key in result.result}
    normalized, errors = validate_feedback_candidate_payload(candidate_payload)

    assert errors == ()
    assert normalized is not None
    assert normalized["loss_points"]
    assert normalized["reference_answer"]["sections"]
    assert normalized["feedback_text"]
