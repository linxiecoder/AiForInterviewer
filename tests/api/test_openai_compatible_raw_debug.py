import json
from pathlib import Path

import httpx
import pytest

import app.infrastructure.llm.openai_compatible as openai_compatible
from app.infrastructure.llm.errors import LlmTransportResponseError, LlmTransportUnavailableError
from app.infrastructure.llm.openai_compatible import (
    LLM_OPENAI_TRUST_ENV_ENV,
    LOCAL_LLM_RAW_IO_DIR_ENV,
    LOCAL_LLM_RAW_IO_ENABLED_ENV,
    OpenAICompatibleLlmSettings,
    OpenAICompatibleLlmTransport,
)
from app.infrastructure.llm.types import LlmTransportRequest


def test_local_raw_llm_io_dump_disabled_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(LOCAL_LLM_RAW_IO_ENABLED_ENV, raising=False)
    monkeypatch.delenv(LOCAL_LLM_RAW_IO_DIR_ENV, raising=False)

    transport = _transport_with_response(_successful_provider_response())

    result = transport.generate(_raw_debug_request())

    assert result.result["question_text"] == "请结合 FastAPI 项目说明一次接口编排取舍。"
    assert not (tmp_path / ".local" / "llm-raw").exists()


@pytest.mark.parametrize("api_env", ["production", "shared"])
def test_local_raw_llm_io_dump_fails_closed_outside_local_environments(
    api_env: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dump_dir = tmp_path / "raw-dump"
    monkeypatch.setenv(LOCAL_LLM_RAW_IO_ENABLED_ENV, "true")
    monkeypatch.setenv(LOCAL_LLM_RAW_IO_DIR_ENV, str(dump_dir))
    monkeypatch.setenv("API_ENV", api_env)
    transport = _transport_with_response(_successful_provider_response())

    result = transport.generate(_raw_debug_request())

    assert result.result["question_text"] == "请结合 FastAPI 项目说明一次接口编排取舍。"
    assert not dump_dir.exists()


def test_local_raw_llm_io_dump_fails_closed_in_ci(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dump_dir = tmp_path / "raw-dump"
    monkeypatch.setenv(LOCAL_LLM_RAW_IO_ENABLED_ENV, "true")
    monkeypatch.setenv(LOCAL_LLM_RAW_IO_DIR_ENV, str(dump_dir))
    monkeypatch.setenv("CI", "true")
    transport = _transport_with_response(_successful_provider_response())

    result = transport.generate(_raw_debug_request())

    assert result.result["question_text"] == "请结合 FastAPI 项目说明一次接口编排取舍。"
    assert not dump_dir.exists()


def test_local_raw_llm_io_dump_writes_safe_diagnostics_without_raw_io(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dump_dir = tmp_path / "raw-dump"
    monkeypatch.setenv(LOCAL_LLM_RAW_IO_ENABLED_ENV, "true")
    monkeypatch.setenv(LOCAL_LLM_RAW_IO_DIR_ENV, str(dump_dir))
    transport = _transport_with_response(_provider_response_with_sensitive_marker())

    result = transport.generate(_raw_debug_request_with_sensitive_marker())

    dump = _single_dump_json(dump_dir)
    assert dump["schema_version"] == "local_llm_safe_io.v1"
    assert dump["task_type"] == "polish_question_generation"
    assert dump["contract_ids"] == ["P-POLISH-002", "P-SHARED-001", "P-SHARED-003"]
    assert dump["model"] == "deepseek-v4-pro"
    assert dump["base_url"] == "https://api.deepseek.com/v1"
    assert dump["provider_base_host"] == "api.deepseek.com"
    assert dump["timeout_seconds"] == 90.0
    assert dump["temperature"] == 0.0
    request_summary = dump["request"]
    assert request_summary["payload_sha256"].startswith("sha256:")
    assert request_summary["top_level_keys"] == ["max_tokens", "messages", "model", "response_format", "temperature"]
    assert request_summary["message_roles"] == ["system", "user"]
    assert request_summary["message_count"] == 2
    assert request_summary["max_tokens"] == 8000
    assert "chat_completion_payload" not in request_summary
    assert dump["response"]["status_code"] == 200
    assert dump["response"]["body_sha256"].startswith("sha256:")
    assert dump["response"]["json_top_level_keys"] == ["choices", "id", "model"]
    assert "body" not in dump["response"]
    assert dump["parsed_result"]["payload_sha256"].startswith("sha256:")
    assert dump["parsed_result"]["top_level_keys"] == ["confidence", "model_name", "question_text"]
    assert dump["trace_refs"] == list(result.trace_refs)
    assert dump["evidence_refs"] == list(result.evidence_refs)
    dump_text = _single_dump_path(dump_dir).read_text(encoding="utf-8")
    assert _sensitive_marker() not in dump_text
    assert "raw_prompt" not in dump_text
    assert "raw_completion" not in dump_text
    assert "provider_payload" not in dump_text


def test_local_raw_llm_io_dump_records_no_timeout_for_polish_feedback_generation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dump_dir = tmp_path / "raw-dump"
    monkeypatch.setenv(LOCAL_LLM_RAW_IO_ENABLED_ENV, "true")
    monkeypatch.setenv(LOCAL_LLM_RAW_IO_DIR_ENV, str(dump_dir))
    transport = _transport_with_response(_successful_provider_response())

    transport.generate(
        LlmTransportRequest(
            contract_ids=("P-POLISH-FEEDBACK-GENERATED",),
            task_type="polish_feedback_generation",
            input_refs=("answer:1",),
            evidence_bundle={"feedback_signal": "retry boundaries"},
        )
    )

    dump = _single_dump_json(dump_dir)
    assert dump["task_type"] == "polish_feedback_generation"
    assert dump["timeout_seconds"] is None


def test_local_raw_llm_io_dump_excludes_authorization_and_api_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dump_dir = tmp_path / "raw-dump"
    monkeypatch.setenv(LOCAL_LLM_RAW_IO_ENABLED_ENV, "true")
    monkeypatch.setenv(LOCAL_LLM_RAW_IO_DIR_ENV, str(dump_dir))
    transport = _transport_with_response(
        _successful_provider_response(),
        api_key="sk-test-secret-key",
    )

    transport.generate(_raw_debug_request())

    dump_text = _single_dump_path(dump_dir).read_text(encoding="utf-8")
    assert "Authorization" not in dump_text
    assert "Bearer" not in dump_text
    assert "api_key" not in dump_text
    assert "sk-test-secret-key" not in dump_text


def test_local_raw_llm_io_dump_writes_failed_provider_response(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dump_dir = tmp_path / "raw-dump"
    monkeypatch.setenv(LOCAL_LLM_RAW_IO_ENABLED_ENV, "true")
    monkeypatch.setenv(LOCAL_LLM_RAW_IO_DIR_ENV, str(dump_dir))
    transport = _transport_with_response(
        {"error": {"type": "rate_limit", "message": "too many requests"}},
        status_code=429,
    )

    with pytest.raises(LlmTransportUnavailableError, match="限流"):
        transport.generate(_raw_debug_request())

    dump = _single_dump_json(dump_dir)
    assert dump["response"]["status_code"] == 429
    assert dump["response"]["body_sha256"].startswith("sha256:")
    assert dump["response"]["json_top_level_keys"] == ["error"]
    assert "body" not in dump["response"]
    assert dump["error"]["type"] == "rate_limited"
    assert "限流" in dump["error"]["message"]
    assert dump["model"] == "deepseek-v4-pro"
    assert dump["parsed_result"] is None


def test_local_raw_llm_io_dump_marks_length_finish_reason_as_truncated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dump_dir = tmp_path / "raw-dump"
    monkeypatch.setenv(LOCAL_LLM_RAW_IO_ENABLED_ENV, "true")
    monkeypatch.setenv(LOCAL_LLM_RAW_IO_DIR_ENV, str(dump_dir))
    transport = _transport_with_response(_truncated_provider_response())

    with pytest.raises(LlmTransportResponseError, match="输出被截断"):
        transport.generate(_raw_debug_request())

    dump = _single_dump_json(dump_dir)
    assert dump["response"]["status_code"] == 200
    assert dump["response"]["body_sha256"].startswith("sha256:")
    assert dump["response"]["json_top_level_keys"] == ["choices", "id", "model"]
    assert dump["response"]["finish_reason"] == "length"
    assert "body" not in dump["response"]
    assert dump["error"]["type"] == "provider_output_truncated"
    assert "JSON 不完整" in dump["error"]["message"]
    assert dump["parsed_result"] is None


def test_local_raw_llm_io_dump_failure_does_not_break_transport(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dump_dir = tmp_path / "raw-dump"
    monkeypatch.setenv(LOCAL_LLM_RAW_IO_ENABLED_ENV, "true")
    monkeypatch.setenv(LOCAL_LLM_RAW_IO_DIR_ENV, str(dump_dir))
    transport = _transport_with_response(_successful_provider_response())

    def fail_write_text(self: Path, data: str, *, encoding: str | None = None) -> int:
        raise OSError("disk unavailable")

    monkeypatch.setattr(Path, "write_text", fail_write_text)

    result = transport.generate(_raw_debug_request())

    assert result.result["question_text"] == "请结合 FastAPI 项目说明一次接口编排取舍。"


def test_openai_compatible_settings_trust_env_requires_explicit_opt_in() -> None:
    settings = OpenAICompatibleLlmSettings.from_env(
        {
            "LLM_OPENAI_API_KEY": "test-key",
            "ALL_PROXY": "socks5://127.0.0.1:7890",
        }
    )

    assert settings.trust_env is False

    trusted_settings = OpenAICompatibleLlmSettings.from_env(
        {
            "LLM_OPENAI_API_KEY": "test-key",
            LLM_OPENAI_TRUST_ENV_ENV: "true",
        }
    )

    assert trusted_settings.trust_env is True


def test_openai_compatible_transport_disables_environment_proxy_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, object] = {}

    class ClientStub:
        def __init__(self, *args: object, **kwargs: object) -> None:
            observed.update(kwargs)

        def __enter__(self) -> "ClientStub":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def post(self, *args: object, **kwargs: object) -> httpx.Response:
            return httpx.Response(200, json=_successful_provider_response())

    monkeypatch.setattr(openai_compatible.httpx, "Client", ClientStub)

    result = OpenAICompatibleLlmTransport(
        OpenAICompatibleLlmSettings(
            api_key="test-key",
            model="deepseek-v4-pro",
            base_url="https://api.deepseek.com/v1",
        )
    ).generate(_raw_debug_request())

    assert result.result["question_text"] == "请结合 FastAPI 项目说明一次接口编排取舍。"
    assert observed["trust_env"] is False


def test_local_raw_llm_io_dump_writes_client_initialization_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dump_dir = tmp_path / "raw-dump"
    monkeypatch.setenv(LOCAL_LLM_RAW_IO_ENABLED_ENV, "true")
    monkeypatch.setenv(LOCAL_LLM_RAW_IO_DIR_ENV, str(dump_dir))

    def fail_client(*args: object, **kwargs: object) -> httpx.Client:
        assert kwargs["trust_env"] is True
        raise ImportError("Using SOCKS proxy, but the 'socksio' package is not installed.")

    monkeypatch.setattr(openai_compatible.httpx, "Client", fail_client)
    transport = OpenAICompatibleLlmTransport(
        OpenAICompatibleLlmSettings(
            api_key="test-key",
            model="deepseek-v4-pro",
            base_url="https://api.deepseek.com/v1",
            trust_env=True,
        )
    )

    with pytest.raises(LlmTransportUnavailableError, match="客户端初始化失败"):
        transport.generate(_raw_debug_request())

    dump = _single_dump_json(dump_dir)
    assert dump["trust_env"] is True
    assert dump["response"]["status_code"] is None
    assert dump["parsed_result"] is None
    assert dump["error"]["type"] == "client_initialization_failed"
    assert "SOCKS proxy support" in dump["error"]["message"]
    assert dump["model"] == "deepseek-v4-pro"
    assert dump["request"]["payload_sha256"].startswith("sha256:")
    assert "chat_completion_payload" not in dump["request"]


def _transport_with_response(
    response_body: dict[str, object],
    *,
    status_code: int = 200,
    api_key: str = "test-key",
) -> OpenAICompatibleLlmTransport:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(status_code, json=response_body)
        )
    )
    return OpenAICompatibleLlmTransport(
        OpenAICompatibleLlmSettings(
            api_key=api_key,
            model="deepseek-v4-pro",
            base_url="https://api.deepseek.com/v1",
            timeout_seconds=90.0,
            temperature=0.0,
        ),
        client=client,
    )


def _raw_debug_request() -> LlmTransportRequest:
    return LlmTransportRequest(
        contract_ids=("P-POLISH-002", "P-SHARED-001", "P-SHARED-003"),
        task_type="polish_question_generation",
        input_refs=("resume_chunk:1", "job_requirement:1"),
        evidence_bundle={
            "resume_signal": "FastAPI 接口编排",
            "quality_probe": {"must_keep": "完整审计输入"},
        },
    )


def _raw_debug_request_with_sensitive_marker() -> LlmTransportRequest:
    return LlmTransportRequest(
        contract_ids=("P-POLISH-002", "P-SHARED-001", "P-SHARED-003"),
        task_type="polish_question_generation",
        input_refs=("resume_chunk:1", "job_requirement:1"),
        evidence_bundle={
            "resume_signal": "FastAPI 接口编排",
            "quality_probe": {"must_keep": _sensitive_marker()},
        },
    )


def _successful_provider_response() -> dict[str, object]:
    return {
        "id": "chatcmpl_raw_debug",
        "model": "deepseek-v4-pro",
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "question_text": "请结合 FastAPI 项目说明一次接口编排取舍。",
                            "question_type": "behavioral",
                            "confidence": "high",
                        },
                        ensure_ascii=False,
                    )
                }
            }
        ],
    }


def _provider_response_with_sensitive_marker() -> dict[str, object]:
    return {
        "id": "chatcmpl_raw_debug_sensitive",
        "model": "deepseek-v4-pro",
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "question_text": _sensitive_marker(),
                            "confidence": "high",
                        },
                        ensure_ascii=False,
                    )
                }
            }
        ],
    }


def _truncated_provider_response() -> dict[str, object]:
    return {
        "id": "chatcmpl_raw_debug_truncated",
        "model": "deepseek-v4-pro",
        "choices": [
            {
                "finish_reason": "length",
                "message": {"content": '{"question_text":"请结合 FastAPI 项目说明'},
            }
        ],
    }


def _single_dump_path(dump_dir: Path) -> Path:
    dumps = sorted(dump_dir.glob("*.json"))
    assert len(dumps) == 1
    return dumps[0]


def _single_dump_json(dump_dir: Path) -> dict[str, object]:
    return json.loads(_single_dump_path(dump_dir).read_text(encoding="utf-8"))


def _sensitive_marker() -> str:
    return "_".join(("secret", "cookie", "token", "provider", "payload"))
