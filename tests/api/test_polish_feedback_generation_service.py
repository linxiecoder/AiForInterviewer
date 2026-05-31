from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from app.application.llm.types import LlmTransportRequest, LlmTransportResult
from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
    POLISH_FEEDBACK_GENERATED_CONTRACT_IDS,
    POLISH_FEEDBACK_GENERATED_SCHEMA_ID,
    POLISH_FEEDBACK_GENERATED_SCHEMA_VERSION,
    POLISH_FEEDBACK_TASK_TYPE,
)
from app.application.polish.feedback_validation import validate_generated_feedback_payload
from app.domain.shared.enums import ConfidenceLevel, ValidationStatus
from app.infrastructure.llm.fake_transport import FakeLlmTransport


def _context() -> dict[str, Any]:
    return {
        "owner_id": "owner_001",
        "actor_id": "user_001",
        "session_id": "sess_001",
        "question_id": "question_001",
        "answer_id": "answer_001",
        "question_text": "请说明你如何设计订单异步处理链路，并保证失败可恢复。",
        "answer_text": "我会用消息队列解耦下单和履约，并通过重试表恢复失败消息。",
        "answer_round": 2,
        "polish_theme": "支付系统可靠性",
        "progress_node_ref": "progress_node_reliability",
        "question_sources": [
            {"source_type": "progress_node", "source_ref": "progress_node_reliability"},
        ],
        "evidence_refs": ["resume_project_payment", "job_requirement_reliability"],
        "same_question_answers": [
            {
                "answer_id": "answer_prev",
                "answer_round": 1,
                "answer_summary": "上一轮只说明了 MQ 解耦，缺少幂等和观测。",
                "loss_point_ids": ["lp_observability"],
            }
        ],
        "same_project_turns": [
            {
                "question_id": "question_project",
                "answer_id": "answer_project",
                "feedback_summary": "项目表述里曾说明幂等键设计。",
            }
        ],
        "session_recent_turns": [
            {
                "question_id": "question_recent",
                "answer_id": "answer_recent",
                "feedback_summary": "最近一题已经扣过监控指标说明不足。",
            }
        ],
        "project_asset_summaries": [
            {
                "asset_id": "asset_payment",
                "summary": "支付项目已有事务消息、幂等键和补偿任务素材。",
            }
        ],
        "job_snapshot": {"job_id": "job_001", "requirements": ["高可用后端设计", "故障恢复"]},
        "resume_snapshot": {"resume_id": "resume_001", "projects": ["支付系统"]},
        "progress_node_snapshot": {"node_ref": "progress_node_reliability", "title": "可靠性设计"},
    }


def _generated_payload() -> dict[str, Any]:
    return {
        "schema_id": POLISH_FEEDBACK_GENERATED_SCHEMA_ID,
        "schema_version": POLISH_FEEDBACK_GENERATED_SCHEMA_VERSION,
        "status": "generated",
        "contract_ids": list(POLISH_FEEDBACK_GENERATED_CONTRACT_IDS),
        "feedback_text": "回答覆盖了 MQ 解耦，但故障恢复和观测指标仍不够可验证。",
        "answer_summary": "候选人说明了异步解耦和失败重试表。",
        "score_result": {
            "score_type": "polish_answer",
            "score_value": 82,
        },
        "explicit_score": 82,
        "implicit_score": 80,
        "scoring_dimensions": [
            {"dimension": "architecture", "score": 42},
            {"dimension": "reliability", "score": 40},
        ],
        "loss_points": [
            {
                "loss_point_id": "lp_recovery",
                "severity": "major",
                "deduction": 12,
                "reason": "没有说明补偿任务的触发条件和终止条件。",
            },
            {
                "loss_point_id": "lp_observability",
                "severity": "minor",
                "deducted_points": 6,
                "reason": "缺少失败率、堆积量和恢复耗时指标。",
            },
        ],
        "reference_answer": {
            "sections": [
                {
                    "section_id": "ref_recovery",
                    "title": "失败恢复",
                    "content": "说明重试、补偿、幂等键、死信和人工介入边界。",
                    "addresses_loss_point_ids": ["lp_recovery"],
                },
                {
                    "section_id": "ref_observability",
                    "title": "观测指标",
                    "content": "说明消息堆积、失败率、恢复耗时和告警阈值。",
                    "addresses_loss_point_ids": ["lp_observability"],
                },
            ]
        },
        "knowledge_points": ["事务消息", "幂等设计"],
        "technical_principles": ["先定义失败恢复边界，再选择队列和补偿策略。"],
        "same_question_effect": {
            "improved_points": ["补充了异步解耦"],
            "repeated_loss_point_ids": ["lp_observability"],
            "regressed_points": [],
            "next_retry_focus": ["补齐恢复指标"],
            "score_delta": 6,
        },
        "project_asset_consistency_check": {"status": "consistent", "conflicts": []},
        "session_similarity_check": {"status": "benign_reuse"},
        "project_asset_update_candidates": [
            {
                "candidate_type": "project_asset_update_candidate",
                "candidate_ref": "asset_candidate_payment_recovery",
                "user_confirmation_required": True,
                "target_asset_ref": {"resource_type": "asset", "resource_id": "asset_payment"},
                "summary": "补充支付系统失败恢复和观测指标素材。",
            }
        ],
        "next_recommended_actions": ["围绕补偿任务终止条件再练一题"],
        "low_confidence_flags": [],
        "trace_refs": [{"resource_type": "llm_trace", "resource_id": "trace_feedback_001"}],
        "feedback_metadata": {
            "prompt_version": POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
            "llm_called": True,
        },
    }


class _PayloadTransport:
    def __init__(self, payload: object) -> None:
        self.payload = payload
        self.requests: list[LlmTransportRequest] = []

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        self.requests.append(request)
        return LlmTransportResult(
            result=self.payload,  # type: ignore[arg-type]
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.MEDIUM,
            low_confidence_flags=(),
            trace_refs=("trace_provider_001",),
            evidence_refs=("evidence_provider_001",),
        )


class _RaisingTransport:
    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        raise TimeoutError("provider timed out")


def _service(llm_transport: object):
    from app.application.polish.feedback_generation_service import FeedbackGenerationService

    return FeedbackGenerationService(llm_transport=llm_transport)


def test_service_with_fake_transport_returns_succeeded_generated_payload() -> None:
    result = _service(FakeLlmTransport()).generate(_context())

    assert result.succeeded is True
    assert result.payload is not None
    assert result.payload["schema_id"] == POLISH_FEEDBACK_GENERATED_SCHEMA_ID
    assert result.payload["status"] == "generated"
    assert result.validation_errors == ()
    assert result.payload["loss_points"]


def test_fake_generated_payload_passes_phase2_validator() -> None:
    result = _service(FakeLlmTransport()).generate(_context())

    normalized, errors = validate_generated_feedback_payload(result.payload)

    assert errors == ()
    assert normalized is not None
    assert normalized["schema_id"] == POLISH_FEEDBACK_GENERATED_SCHEMA_ID


def test_service_metadata_includes_prompt_schema_llm_and_provider_status() -> None:
    result = _service(FakeLlmTransport()).generate(_context())

    assert result.metadata["prompt_version"] == POLISH_FEEDBACK_AGENT_PROMPT_VERSION
    assert result.metadata["schema_id"] == POLISH_FEEDBACK_GENERATED_SCHEMA_ID
    assert result.metadata["llm_called"] is True
    assert result.metadata["provider_status"] == "fake_transport"


def test_feedback_request_uses_compact_output_budget() -> None:
    transport = _PayloadTransport(_generated_payload())

    result = _service(transport).generate(_context())

    assert result.succeeded is True
    assert transport.requests
    assert getattr(transport.requests[-1], "max_tokens", 8000) < 2500


def test_feedback_request_uses_quick_provider_prompt_budget_and_evidence_limits() -> None:
    transport = _PayloadTransport(_generated_payload())
    context = _context()
    context["question_text"] = "请深入说明混合检索策略优化如何在召回率、精排质量和延迟之间做取舍。"
    context["answer_text"] = "我会先用关键词召回保证确定性，再用向量召回补语义覆盖，最后用重排模型统一打分。 " * 80
    context["evidence_refs"] = ["resume_project_hybrid_search", "question_source_hybrid_search"]
    context["question_sources"] = [
        {
            "ref": "question_source_hybrid_search",
            "source_type": "resume_project_contribution",
            "title": "混合检索策略优化",
            "excerpt": "通过 BM25、向量召回和 rerank 做多路召回融合。",
        },
        {
            "ref": "question_source_inventory",
            "source_type": "resume_project_contribution",
            "title": "物料库存处理工作流",
            "excerpt": "物料库存处理工作流包含库存冻结、调拨和盘点。",
        },
        {
            "ref": "question_source_large_file",
            "source_type": "resume_project_contribution",
            "title": "大文件异步处理管道",
            "excerpt": "大文件异步处理管道包含分片上传、解析和入库。",
        },
    ]
    context["same_question_answers"] = [
        {
            "answer_id": f"answer_prev_{index}",
            "answer_text": f"PREVIOUS_FULL_ANSWER_{index}_SHOULD_NOT_BE_INCLUDED " * 40,
            "answer_summary": f"上一轮摘要 {index}：缺少召回融合后的评估指标。" * 20,
        }
        for index in range(3)
    ]
    context["job_snapshot"] = {
        "job_id": "job_001",
        "requirements": [f"岗位要求 {index}" for index in range(6)],
        "full_jd": "FULL_JD_SHOULD_NOT_BE_INCLUDED",
    }
    context["resume_snapshot"] = {
        "resume_id": "resume_001",
        "projects": [
            "混合检索策略优化：负责 BM25、向量召回、rerank 和线上评估。",
            "物料库存处理工作流：负责库存冻结、调拨和盘点。",
            "大文件异步处理管道：负责分片上传、解析和入库。",
        ],
        "full_resume": "FULL_RESUME_SHOULD_NOT_BE_INCLUDED",
        "markdown_text": "RESUME_MARKDOWN_SHOULD_NOT_BE_INCLUDED",
        "work_experiences": ["WORK_EXPERIENCE_SHOULD_NOT_BE_INCLUDED"],
    }
    context["progress_node_snapshot"] = {
        "node_ref": "progress_node_hybrid_search",
        "title": "混合检索策略优化",
        "expected_capability": "说明多路召回、重排、评估指标和延迟取舍。" * 10,
        "related_resume_evidence": ["混合检索策略优化"],
    }

    result = _service(transport).generate(context)

    assert result.succeeded is True
    request = transport.requests[-1]
    provider_prompt = request.evidence_bundle
    serialized_provider_user = json.dumps(
        {
            "task_type": request.task_type,
            "input_refs": list(request.input_refs),
            "evidence_bundle": provider_prompt,
        },
        ensure_ascii=False,
        sort_keys=True,
    )

    assert provider_prompt["feedback_mode"] == "quick"
    assert provider_prompt["task"] == "polish_feedback_quick_v1"
    assert provider_prompt["prompt_version"] == POLISH_FEEDBACK_AGENT_PROMPT_VERSION
    assert provider_prompt["output_schema"]["schema_id"] == POLISH_FEEDBACK_GENERATED_SCHEMA_ID
    assert "Generate structured polish feedback" in provider_prompt["prompt"]
    assert "developer_constraints" not in provider_prompt
    assert "refusal_and_low_confidence_policy" not in provider_prompt
    assert len(serialized_provider_user) < 12000
    assert len(provider_prompt["evidence"]) <= 5
    assert len(provider_prompt["current_question"]["question_sources"]) <= 2
    assert len(provider_prompt["same_question_answers"]) <= 1
    assert "answer_text" not in provider_prompt["same_question_answers"][0]
    assert "PREVIOUS_FULL_ANSWER_0_SHOULD_NOT_BE_INCLUDED" not in serialized_provider_user
    serialized_provider_data = json.dumps(
        {key: value for key, value in provider_prompt.items() if key != "prompt"},
        ensure_ascii=False,
        sort_keys=True,
    )
    for forbidden_key in ("full_resume", "full_jd", "work_experiences", "markdown_text"):
        assert forbidden_key not in serialized_provider_data
    for forbidden in (
        "FULL_RESUME_SHOULD_NOT_BE_INCLUDED",
        "FULL_JD_SHOULD_NOT_BE_INCLUDED",
        "WORK_EXPERIENCE_SHOULD_NOT_BE_INCLUDED",
        "RESUME_MARKDOWN_SHOULD_NOT_BE_INCLUDED",
        "物料库存处理工作流",
        "大文件异步处理管道",
    ):
        assert forbidden not in serialized_provider_user
    assert provider_prompt["feedback_metadata"]["prompt_char_count"] < 12000
    assert provider_prompt["feedback_metadata"]["evidence_item_count"] <= 5
    assert provider_prompt["feedback_metadata"]["context_compaction_applied"] is True


def test_no_llm_transport_returns_failed_without_fake_feedback() -> None:
    result = _service(None).generate(_context())

    assert result.succeeded is False
    assert result.payload is None
    assert result.validation_errors == ("llm_transport_unavailable",)
    assert result.metadata["provider_status"] == "not_configured"
    assert result.metadata["llm_called"] is False


def test_provider_invalid_schema_returns_failed() -> None:
    payload = _generated_payload()
    payload["schema_id"] = "wrong_schema"

    result = _service(_PayloadTransport(payload)).generate(_context())

    assert result.succeeded is False
    assert result.payload is None
    assert "feedback_schema_id_invalid" in result.validation_errors


def test_provider_loss_reference_mapping_invalid_returns_failed() -> None:
    payload = _generated_payload()
    payload["reference_answer"]["sections"][0]["addresses_loss_point_ids"] = []

    result = _service(_PayloadTransport(payload)).generate(_context())

    assert result.succeeded is False
    assert result.payload is None
    assert "loss_point_reference_mapping_missing" in result.validation_errors


def test_unsafe_provider_payload_returns_failed() -> None:
    payload = _generated_payload()
    payload["feedback_metadata"]["raw_prompt"] = "hidden chain"

    result = _service(_PayloadTransport(payload)).generate(_context())

    assert result.succeeded is False
    assert result.payload is None
    assert "feedback_payload_unsafe_leakage" in result.validation_errors


def test_provider_exception_returns_failed() -> None:
    result = _service(_RaisingTransport()).generate(_context())

    assert result.succeeded is False
    assert result.payload is None
    assert result.validation_errors == ("llm_transport_timeout",)
    assert result.metadata["provider_status"] == "failed"
    assert result.metadata["provider_error_type"] == "timeout"


def test_provider_non_dict_payload_returns_failed() -> None:
    result = _service(_PayloadTransport(["not", "a", "dict"])).generate(_context())

    assert result.succeeded is False
    assert result.payload is None
    assert result.validation_errors == ("feedback_payload_schema_invalid",)


def test_prompt_asset_contains_current_question_and_answer_without_private_fields() -> None:
    from app.application.polish.feedback_prompt_assets import build_feedback_prompt_asset

    asset = build_feedback_prompt_asset(_context())

    assert asset["task_type"] == POLISH_FEEDBACK_TASK_TYPE
    assert asset["input_data"]["current_question"]["question_text"] == _context()["question_text"]
    assert asset["input_data"]["current_answer"]["answer_text"] == _context()["answer_text"]
    assert not _contains_forbidden_key(asset)


def test_prompt_asset_includes_same_question_answers() -> None:
    from app.application.polish.feedback_prompt_assets import build_feedback_prompt_asset

    asset = build_feedback_prompt_asset(_context())

    assert asset["input_data"]["same_question_answers"][0]["answer_id"] == "answer_prev"
    assert asset["input_data"]["same_question_answers"][0]["answer_summary"] == "上一轮只说明了 MQ 解耦，缺少幂等和观测。"
    assert asset["input_data"]["same_question_answers"][0]["loss_point_ids"] == ["lp_observability"]


def test_prompt_asset_compacts_resume_job_and_evidence_context() -> None:
    from app.application.polish.feedback_prompt_assets import build_feedback_prompt_asset

    context = _context()
    context["job_snapshot"] = {
        "job_id": "job_001",
        "title": "后端工程师",
        "full_jd": "FULL_JD_SHOULD_NOT_BE_INCLUDED",
        "requirements": [f"岗位要求 {index}" for index in range(8)],
        "responsibilities": [f"岗位职责 {index}" for index in range(8)],
        "content_digest": "job_digest_001",
    }
    context["resume_snapshot"] = {
        "resume_id": "resume_001",
        "summary": "候选人有支付系统可靠性经验。",
        "full_resume": "FULL_RESUME_SHOULD_NOT_BE_INCLUDED",
        "markdown_text": "RESUME_MARKDOWN_SHOULD_NOT_BE_INCLUDED",
        "projects": [f"项目全文 {index}" for index in range(8)],
        "work_experiences": ["WORK_EXPERIENCE_SHOULD_NOT_BE_INCLUDED"],
        "content_digest": "resume_digest_001",
    }
    context["question_sources"] = [
        {"source_type": "progress_node", "source_ref": f"node_{index}", "summary": f"节点摘要 {index}"}
        for index in range(8)
    ]
    context["same_question_answers"] = [
        {
            "answer_id": f"answer_prev_{index}",
            "answer_round": index,
            "answer_text": f"PREVIOUS_FULL_ANSWER_{index}_SHOULD_NOT_BE_INCLUDED",
            "answer_summary": f"上一轮摘要 {index}",
            "feedback_summary": f"上一轮反馈摘要 {index}",
            "loss_point_ids": [f"lp_{index}"],
        }
        for index in range(6)
    ]
    context["session_recent_turns"] = [
        {
            "question_id": f"question_recent_{index}",
            "answer_id": f"answer_recent_{index}",
            "answer_summary": f"最近回答摘要 {index}",
            "feedback_summary": f"最近反馈摘要 {index}",
        }
        for index in range(6)
    ]

    asset = build_feedback_prompt_asset(context)
    input_data = asset["input_data"]
    serialized = repr(asset)

    assert len(input_data["evidence_items"]) <= 12
    assert len(input_data["session_recent_turns"]) <= 3
    assert len(input_data["context_snapshots"]["job_snapshot"]["requirements"]) <= 5
    assert len(input_data["context_snapshots"]["job_snapshot"]["responsibilities"]) <= 5
    assert "full_jd" not in input_data["context_snapshots"]["job_snapshot"]
    assert "full_resume" not in input_data["context_snapshots"]["resume_snapshot"]
    assert "markdown_text" not in input_data["context_snapshots"]["resume_snapshot"]
    assert "work_experiences" not in input_data["context_snapshots"]["resume_snapshot"]
    assert "FULL_JD_SHOULD_NOT_BE_INCLUDED" not in serialized
    assert "FULL_RESUME_SHOULD_NOT_BE_INCLUDED" not in serialized
    assert "RESUME_MARKDOWN_SHOULD_NOT_BE_INCLUDED" not in serialized
    assert "WORK_EXPERIENCE_SHOULD_NOT_BE_INCLUDED" not in serialized


def test_prompt_asset_same_question_answers_do_not_repeat_full_answer_text() -> None:
    from app.application.polish.feedback_prompt_assets import build_feedback_prompt_asset

    context = _context()
    context["same_question_answers"] = [
        {
            "answer_id": "answer_prev_full",
            "answer_round": 1,
            "answer_text": "PREVIOUS_FULL_ANSWER_SHOULD_NOT_BE_INCLUDED",
            "answer_summary": "上一轮摘要：缺少观测指标。",
            "feedback_summary": "上一轮反馈：补充失败率和恢复耗时。",
            "loss_point_ids": ["lp_observability"],
        }
    ]

    asset = build_feedback_prompt_asset(context)
    previous_answer = asset["input_data"]["same_question_answers"][0]
    serialized = repr(asset)

    assert "answer_text" not in previous_answer
    assert "PREVIOUS_FULL_ANSWER_SHOULD_NOT_BE_INCLUDED" not in serialized
    assert previous_answer["answer_summary"] == "上一轮摘要：缺少观测指标。"


def test_prompt_asset_includes_project_asset_summaries() -> None:
    from app.application.polish.feedback_prompt_assets import build_feedback_prompt_asset

    asset = build_feedback_prompt_asset(_context())

    assert asset["input_data"]["project_asset_summaries"][0]["asset_id"] == "asset_payment"
    assert asset["input_data"]["project_asset_summaries"][0]["summary"] == "支付项目已有事务消息、幂等键和补偿任务素材。"


def _contains_forbidden_key(value: object) -> bool:
    forbidden = {
        "raw_prompt",
        "system_prompt",
        "developer_prompt",
        "completion",
        "raw_completion",
        "provider_payload",
        "raw_provider_payload",
        "provider_response",
        "raw_provider_response",
        "api_key",
        "token",
        "secret",
        "cookie",
    }
    if isinstance(value, dict):
        return any(str(key).lower() in forbidden or _contains_forbidden_key(nested) for key, nested in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_key(item) for item in value)
    return False
