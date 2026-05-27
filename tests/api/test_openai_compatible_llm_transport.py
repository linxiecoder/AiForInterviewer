import json
import logging

import httpx
import pytest

from app.domain.shared.enums import ConfidenceLevel, ValidationStatus
from app.infrastructure.llm.errors import (
    LlmTransportConfigurationError,
    LlmTransportResponseError,
    LlmTransportUnavailableError,
)
from app.infrastructure.llm.job_match import JOB_MATCH_PROMPT_VERSION
from app.infrastructure.llm.openai_compatible import (
    OpenAICompatibleLlmSettings,
    OpenAICompatibleLlmTransport,
)
from app.infrastructure.llm.types import LlmTransportRequest


def test_openai_compatible_transport_calls_chat_completions_with_json_contract() -> None:
    observed: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        observed["url"] = str(request.url)
        observed["authorization"] = request.headers.get("Authorization")
        observed["payload"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl_test",
                "model": "gpt-test",
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "prompt_version": JOB_MATCH_PROMPT_VERSION,
                                    "model_name": "gpt-test",
                                    "job_match_result_payload": {
                                        "overall_score": 60,
                                        "overall_level": "medium_match",
                                        "confidence": "medium",
                                        "summary": "基于模型分析生成的中文岗位匹配摘要。",
                                        "dimension_scores": [],
                                        "matched_requirements": [],
                                        "missing_requirements": [],
                                        "resume_evidence": [],
                                        "risk_flags": [],
                                        "interview_focus": ["继续核实候选人的项目深度。"],
                                        "suggested_questions": ["请说明最能对应岗位要求的经历。"],
                                        "markdown_report": "# 岗位匹配分析",
                                    },
                                },
                                ensure_ascii=False,
                            )
                        }
                    }
                ],
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = OpenAICompatibleLlmTransport(
        OpenAICompatibleLlmSettings(
            api_key="test-key",
            model="gpt-test",
            base_url="https://llm.example/v1",
        ),
        client=client,
    )

    result = transport.generate(
        LlmTransportRequest(
            contract_ids=("P-JOBMATCH-001",),
            task_type="job_match_analysis",
            input_refs=("resume_version:res_ver_1", "job_version:job_ver_1"),
            evidence_bundle={
                "source_digest": "sha256:test",
                "resume_chunks": [{"chunk_id": "resume:summary:001", "text": "FastAPI"}],
                "job_requirement_chunks": [{"chunk_id": "job:requirement:001", "text": "FastAPI"}],
            },
        )
    )

    assert observed["url"] == "https://llm.example/v1/chat/completions"
    assert observed["authorization"] == "Bearer test-key"
    payload = observed["payload"]
    assert isinstance(payload, dict)
    assert payload["model"] == "gpt-test"
    assert payload["temperature"] == 0.0
    assert payload["max_tokens"] == 8000
    assert payload["response_format"] == {"type": "json_object"}
    assert "必须使用中文输出" in payload["messages"][0]["content"]
    assert "test-key" not in json.dumps(payload, ensure_ascii=False)
    user_payload = json.loads(payload["messages"][1]["content"])
    assert "contract_ids" not in user_payload
    assert user_payload["input_refs"] == ["resume_version:res_ver_1", "job_version:job_ver_1"]
    assert result.validation_status is ValidationStatus.VALID
    assert result.confidence_level is ConfidenceLevel.MEDIUM
    assert result.result["job_match_result_payload"]["summary"].startswith("基于模型分析")


def test_openai_compatible_transport_uses_configured_max_tokens_from_env() -> None:
    observed: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        observed["payload"] = json.loads(request.content.decode("utf-8"))
        return _successful_job_match_response()

    settings = OpenAICompatibleLlmSettings.from_env(
        {
            "LLM_OPENAI_API_KEY": "test-key",
            "LLM_OPENAI_BASE_URL": "https://llm.example/v1",
            "LLM_OPENAI_MODEL": "gpt-test",
            "LLM_OPENAI_TIMEOUT_SECONDS": "90",
            "LLM_OPENAI_TEMPERATURE": "0.2",
            "LLM_OPENAI_MAX_TOKENS": "8000",
        }
    )
    transport = OpenAICompatibleLlmTransport(
        settings,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    transport.generate(
        LlmTransportRequest(
            contract_ids=("P-JOBMATCH-001",),
            task_type="job_match_analysis",
        )
    )

    payload = observed["payload"]
    assert isinstance(payload, dict)
    assert payload["max_tokens"] == 8000
    assert payload["temperature"] == 0.2
    assert payload["response_format"] == {"type": "json_object"}
    assert settings.timeout_seconds == 90.0


def test_openai_compatible_transport_uses_progress_tree_token_budget_and_json_mode() -> None:
    observed: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        observed["payload"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl_progress_tree",
                "model": "deepseek-v4-pro",
                "choices": [{"finish_reason": "stop", "message": {"content": '{"status":"success"}'}}],
            },
        )

    settings = OpenAICompatibleLlmSettings(
        api_key="test-key",
        model="deepseek-v4-pro",
        base_url="https://llm.example/v1",
        max_tokens=8000,
    )
    transport = OpenAICompatibleLlmTransport(
        settings,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    transport.generate(
        LlmTransportRequest(
            contract_ids=("P-POLISH-PROGRESS-QUALITY-FIRST-MENU",),
            task_type="polish_progress_quality_first_menu",
        )
    )

    payload = observed["payload"]
    assert isinstance(payload, dict)
    assert payload["max_tokens"] == 12000
    assert payload["response_format"] == {"type": "json_object"}
    assert "stream" not in payload
    system_prompt = payload["messages"][0]["content"]
    assert "用最精简的步骤完成思考" in system_prompt
    assert "最终输出必须是一个合法、完整的 JSON 对象" in system_prompt


def test_openai_compatible_transport_uses_progress_tree_max_tokens_env_override() -> None:
    observed: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        observed["payload"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl_progress_tree",
                "model": "deepseek-v4-pro",
                "choices": [{"finish_reason": "stop", "message": {"content": '{"status":"success"}'}}],
            },
        )

    settings = OpenAICompatibleLlmSettings.from_env(
        {
            "LLM_OPENAI_API_KEY": "test-key",
            "LLM_OPENAI_BASE_URL": "https://llm.example/v1",
            "LLM_OPENAI_MODEL": "deepseek-v4-pro",
            "LLM_OPENAI_MAX_TOKENS": "7000",
            "LLM_PROGRESS_TREE_MAX_TOKENS": "11000",
        }
    )
    transport = OpenAICompatibleLlmTransport(
        settings,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    transport.generate(
        LlmTransportRequest(
            contract_ids=("P-POLISH-PROGRESS-QUALITY-FIRST-MENU",),
            task_type="polish_progress_quality_first_menu",
        )
    )

    payload = observed["payload"]
    assert isinstance(payload, dict)
    assert payload["max_tokens"] == 11000


@pytest.mark.parametrize("raw_value", ["", "not-an-int", "0", "-1"])
def test_openai_compatible_settings_fallbacks_invalid_max_tokens(raw_value: str) -> None:
    settings = OpenAICompatibleLlmSettings.from_env(
        {
            "LLM_OPENAI_API_KEY": "test-key",
            "LLM_OPENAI_MAX_TOKENS": raw_value,
        }
    )

    assert settings.max_tokens == 8000


def test_openai_compatible_transport_raises_truncated_error_for_length_finish_reason() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl_truncated",
                "model": "deepseek-v4-pro",
                "choices": [
                    {
                        "finish_reason": "length",
                        "message": {"content": '{"status":"success"'},
                    }
                ],
            },
        )

    transport = OpenAICompatibleLlmTransport(
        OpenAICompatibleLlmSettings(
            api_key="test-key",
            model="deepseek-v4-pro",
            base_url="https://llm.example/v1",
        ),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(LlmTransportResponseError, match="输出被截断") as exc_info:
        transport.generate(
            LlmTransportRequest(
                contract_ids=("P-POLISH-PROGRESS-QUALITY-FIRST-MENU",),
                task_type="polish_progress_quality_first_menu",
            )
        )

    assert getattr(exc_info.value, "error_type") == "provider_output_truncated"


def test_openai_compatible_transport_keeps_invalid_json_error_for_non_length_finish_reason() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl_invalid_json",
                "model": "deepseek-v4-pro",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": '{"status":"success"'},
                    }
                ],
            },
        )

    transport = OpenAICompatibleLlmTransport(
        OpenAICompatibleLlmSettings(
            api_key="test-key",
            model="deepseek-v4-pro",
            base_url="https://llm.example/v1",
        ),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(LlmTransportResponseError, match="不是合法 JSON") as exc_info:
        transport.generate(
            LlmTransportRequest(
                contract_ids=("P-POLISH-PROGRESS-QUALITY-FIRST-MENU",),
                task_type="polish_progress_quality_first_menu",
            )
        )

    assert getattr(exc_info.value, "error_type", None) != "provider_output_truncated"


def test_openai_compatible_transport_requires_env_api_key() -> None:
    transport = OpenAICompatibleLlmTransport(
        OpenAICompatibleLlmSettings(api_key="", model="gpt-test")
    )

    with pytest.raises(LlmTransportConfigurationError, match="LLM_OPENAI_API_KEY"):
        transport.generate(
            LlmTransportRequest(
                contract_ids=("P-JOBMATCH-001",),
                task_type="job_match_analysis",
            )
        )


def test_openai_compatible_transport_records_provider_model_not_model_claim() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl_model_test",
                "model": "deepseek-v4-flash",
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "prompt_version": JOB_MATCH_PROMPT_VERSION,
                                    "model_name": "gpt-4",
                                    "job_match_result_payload": {
                                        "overall_score": 60,
                                        "overall_level": "medium_match",
                                        "confidence": "medium",
                                        "summary": "基于模型分析生成的中文岗位匹配摘要。",
                                        "dimension_scores": [],
                                        "matched_requirements": [],
                                        "missing_requirements": [],
                                        "resume_evidence": [],
                                        "risk_flags": [],
                                        "interview_focus": ["继续核实候选人的项目深度。"],
                                        "suggested_questions": ["请说明最能对应岗位要求的经历。"],
                                        "markdown_report": "# 岗位匹配分析",
                                    },
                                },
                                ensure_ascii=False,
                            )
                        }
                    }
                ],
            },
        )

    transport = OpenAICompatibleLlmTransport(
        OpenAICompatibleLlmSettings(
            api_key="test-key",
            model="deepseek-v4-flash",
            base_url="https://llm.example/v1",
        ),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = transport.generate(
        LlmTransportRequest(
            contract_ids=("P-JOBMATCH-001",),
            task_type="job_match_analysis",
        )
    )

    assert result.result["model_name"] == "deepseek-v4-flash"


def test_openai_compatible_transport_logs_progress_without_sensitive_payload(caplog) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl_log_test",
                "model": "deepseek-v4-flash",
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "prompt_version": JOB_MATCH_PROMPT_VERSION,
                                    "job_match_result_payload": {
                                        "overall_score": 60,
                                        "overall_level": "medium_match",
                                        "confidence": "medium",
                                        "summary": "基于模型分析生成的中文岗位匹配摘要。",
                                        "dimension_scores": [],
                                        "matched_requirements": [],
                                        "missing_requirements": [],
                                        "resume_evidence": [],
                                        "risk_flags": [],
                                        "interview_focus": ["继续核实候选人的项目深度。"],
                                        "suggested_questions": ["请说明最能对应岗位要求的经历。"],
                                        "markdown_report": "# 岗位匹配分析",
                                    },
                                },
                                ensure_ascii=False,
                            )
                        }
                    }
                ],
            },
        )

    transport = OpenAICompatibleLlmTransport(
        OpenAICompatibleLlmSettings(
            api_key="secret-test-key",
            model="deepseek-v4-flash",
            base_url="https://llm.example/v1",
        ),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with caplog.at_level(logging.INFO, logger="app.llm.transport"):
        transport.generate(
            LlmTransportRequest(
                contract_ids=("P-JOBMATCH-001",),
                task_type="job_match_analysis",
                input_refs=("resume_version:res_ver_1",),
                evidence_bundle={"raw_prompt_like_text": "不应进入日志的简历正文"},
            )
        )

    llm_records = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "app.llm.transport"
    ]
    assert [record["event"] for record in llm_records] == [
        "llm_transport_request_start",
        "llm_transport_request_success",
    ]
    assert llm_records[0]["task_type"] == "job_match_analysis"
    assert llm_records[0]["model"] == "deepseek-v4-flash"
    assert llm_records[0]["input_ref_count"] == 1
    joined_logs = "\n".join(record.message for record in caplog.records)
    assert "secret-test-key" not in joined_logs
    assert "不应进入日志的简历正文" not in joined_logs
    assert "provider_payload" not in joined_logs
    assert "raw_completion" not in joined_logs


def test_openai_compatible_transport_maps_rate_limit_to_provider_unavailable() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(429, json={}))
    )
    transport = OpenAICompatibleLlmTransport(
        OpenAICompatibleLlmSettings(
            api_key="test-key",
            model="gpt-test",
            base_url="https://llm.example/v1",
        ),
        client=client,
    )

    with pytest.raises(LlmTransportUnavailableError, match="限流"):
        transport.generate(
            LlmTransportRequest(
                contract_ids=("P-JOBMATCH-001",),
                task_type="job_match_analysis",
            )
        )


def _successful_job_match_response() -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "chatcmpl_test",
            "model": "gpt-test",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "prompt_version": JOB_MATCH_PROMPT_VERSION,
                                "job_match_result_payload": {
                                    "overall_score": 60,
                                    "overall_level": "medium_match",
                                    "confidence": "medium",
                                    "summary": "基于模型分析生成的中文岗位匹配摘要。",
                                    "dimension_scores": [],
                                    "matched_requirements": [],
                                    "missing_requirements": [],
                                    "resume_evidence": [],
                                    "risk_flags": [],
                                    "interview_focus": ["继续核实候选人的项目深度。"],
                                    "suggested_questions": ["请说明最能对应岗位要求的经历。"],
                                    "markdown_report": "# 岗位匹配分析",
                                },
                            },
                            ensure_ascii=False,
                        )
                    }
                }
            ],
        },
    )
