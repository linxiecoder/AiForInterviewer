"""ST13_11 R0 LLM provider 边界测试。"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import httpx
import pytest

API_ROOT = Path(__file__).resolve().parents[2] / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.boundary import ERROR_KEY, ERROR_REQUEST_ID_KEY, build_error_payload  # noqa: E402
from app.llm.config import LLMProviderConfig, load_llm_provider_config  # noqa: E402
from app.llm.constants import (  # noqa: E402
    DEFAULT_PROMPT_VERSION,
    ERROR_LLM_PROVIDER_CONFIG_MISSING,
    ERROR_LLM_PROVIDER_FAILED,
    ERROR_LLM_PROVIDER_INVALID,
    ERROR_LLM_PROVIDER_TIMEOUT,
    ERROR_LLM_PROVIDER_UNAVAILABLE,
    LLM_API_KEY_ENV,
    LLM_MODEL_ENV,
    LLM_PROVIDER_DETERMINISTIC,
    LLM_PROVIDER_ENV,
    LLM_PROVIDER_OPENAI,
    LLM_TIMEOUT_SECONDS_ENV,
    PURPOSE_QUESTION,
)
from app.llm.errors import LLMProviderError  # noqa: E402
from app.llm.models import LLMGenerateRequest  # noqa: E402
from app.llm.providers import (  # noqa: E402
    DeterministicLLMProvider,
    OpenAICompatibleLLMProvider,
    build_llm_provider,
)

from app.boundary import ENVIRONMENT_ENV  # noqa: E402


@pytest.fixture(autouse=True)
def clean_llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """隔离本地 shell 配置，避免 provider 测试依赖宿主环境。"""
    for key in (
        LLM_PROVIDER_ENV,
        LLM_API_KEY_ENV,
        LLM_MODEL_ENV,
        LLM_TIMEOUT_SECONDS_ENV,
        ENVIRONMENT_ENV,
    ):
        monkeypatch.delenv(key, raising=False)


def test_provider_config_missing_maps_to_stable_error() -> None:
    """缺少 provider 选择时应稳定失败，而不是静默 fallback。"""
    with pytest.raises(LLMProviderError) as exc_info:
        load_llm_provider_config()

    assert exc_info.value.code == ERROR_LLM_PROVIDER_CONFIG_MISSING
    assert exc_info.value.request_id is None


def test_invalid_provider_name_maps_to_stable_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """未知 provider name 应在构造 provider 前失败。"""
    monkeypatch.setenv(LLM_PROVIDER_ENV, "unknown-provider")

    with pytest.raises(LLMProviderError) as exc_info:
        load_llm_provider_config()

    assert exc_info.value.code == ERROR_LLM_PROVIDER_INVALID


def test_env_config_parsing_reads_real_provider_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """真实 provider 配置只做解析，不校验真实 key。"""
    monkeypatch.setenv(LLM_PROVIDER_ENV, LLM_PROVIDER_OPENAI)
    monkeypatch.setenv(LLM_API_KEY_ENV, "test-key")
    monkeypatch.setenv(LLM_MODEL_ENV, "test-model")
    monkeypatch.setenv(LLM_TIMEOUT_SECONDS_ENV, "1.5")

    config = load_llm_provider_config()

    assert config.provider == LLM_PROVIDER_OPENAI
    assert config.api_key == "test-key"
    assert config.model == "test-model"
    assert config.timeout_seconds == 1.5


def test_deterministic_provider_success_is_stable(monkeypatch: pytest.MonkeyPatch) -> None:
    """deterministic 生成必须显式、可预测且限于 test/dev。"""
    monkeypatch.setenv(ENVIRONMENT_ENV, "test")
    monkeypatch.setenv(LLM_PROVIDER_ENV, LLM_PROVIDER_DETERMINISTIC)
    provider = build_llm_provider()

    result = provider.generate(_request())

    assert isinstance(provider, DeterministicLLMProvider)
    assert result.provider == LLM_PROVIDER_DETERMINISTIC
    assert result.model == LLM_PROVIDER_DETERMINISTIC
    assert result.request_id == "req-provider-1"
    assert result.content == (
        "deterministic question for Backend Engineer; "
        "resume=Python API experience; turn=0"
    )
    assert result.metadata["provider"] == LLM_PROVIDER_DETERMINISTIC
    assert result.metadata["deterministic"] is True


def test_deterministic_provider_is_not_reported_as_real_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """deterministic 输出不得伪装成真实 LLM 调用。"""
    monkeypatch.setenv(ENVIRONMENT_ENV, "development")
    monkeypatch.setenv(LLM_PROVIDER_ENV, LLM_PROVIDER_DETERMINISTIC)

    result = build_llm_provider().generate(_request())

    assert result.provider != LLM_PROVIDER_OPENAI
    assert result.provider == LLM_PROVIDER_DETERMINISTIC
    assert result.provider_request_id is None


def test_deterministic_provider_is_rejected_outside_test_or_dev(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """production 配置不得使用 deterministic provider。"""
    monkeypatch.setenv(ENVIRONMENT_ENV, "production")
    monkeypatch.setenv(LLM_PROVIDER_ENV, LLM_PROVIDER_DETERMINISTIC)

    with pytest.raises(LLMProviderError) as exc_info:
        build_llm_provider()

    assert exc_info.value.code == ERROR_LLM_PROVIDER_INVALID


def test_real_provider_mocked_success_returns_provider_result() -> None:
    """真实 adapter 应支持通过 mock transport 验证成功路径。"""
    transport = FakeTransport(
        FakeResponse(
            {
                "id": "provider-req-123",
                "model": "test-model",
                "choices": [
                    {
                        "message": {"content": "What tradeoff did you make?"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"input_tokens": 10, "output_tokens": 6},
            }
        )
    )
    provider = OpenAICompatibleLLMProvider(_real_config(), transport=transport)

    result = provider.generate(_request())

    assert transport.calls
    assert result.provider == LLM_PROVIDER_OPENAI
    assert result.model == "test-model"
    assert result.content == "What tradeoff did you make?"
    assert result.finish_reason == "stop"
    assert result.usage == {"input_tokens": 10, "output_tokens": 6}
    assert result.provider_request_id == "provider-req-123"
    assert result.request_id == "req-provider-1"


def test_real_provider_mocked_failure_maps_to_stable_error() -> None:
    """Provider HTTP failure 应映射为稳定 provider error。"""
    provider = OpenAICompatibleLLMProvider(
        _real_config(),
        transport=FakeTransport(FakeResponse({"error": "bad request"}, status_code=400)),
    )

    with pytest.raises(LLMProviderError) as exc_info:
        provider.generate(_request())

    assert exc_info.value.code == ERROR_LLM_PROVIDER_FAILED
    assert exc_info.value.request_id == "req-provider-1"


def test_real_provider_timeout_maps_to_stable_error() -> None:
    """Transport timeout 应与通用失败区分。"""
    provider = OpenAICompatibleLLMProvider(
        _real_config(),
        transport=FakeTransport(exc=httpx.TimeoutException("timeout")),
    )

    with pytest.raises(LLMProviderError) as exc_info:
        provider.generate(_request())

    assert exc_info.value.code == ERROR_LLM_PROVIDER_TIMEOUT
    assert exc_info.value.request_id == "req-provider-1"


def test_real_provider_client_failure_maps_to_unavailable() -> None:
    """Client 连接失败不得被报告为 deterministic success。"""
    provider = OpenAICompatibleLLMProvider(
        _real_config(),
        transport=FakeTransport(exc=httpx.ConnectError("connection failed")),
    )

    with pytest.raises(LLMProviderError) as exc_info:
        provider.generate(_request())

    assert exc_info.value.code == ERROR_LLM_PROVIDER_UNAVAILABLE
    assert exc_info.value.request_id == "req-provider-1"


def test_tests_use_mock_transport_not_external_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """注入 transport 后不应构造真实 HTTP client。"""

    def fail_if_external_client_is_constructed(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("external network client should not be constructed")

    monkeypatch.setattr("app.llm.providers.httpx.Client", fail_if_external_client_is_constructed)
    provider = OpenAICompatibleLLMProvider(
        _real_config(),
        transport=FakeTransport(
            FakeResponse(
                {
                    "model": "test-model",
                    "choices": [{"message": {"content": "mocked"}, "finish_reason": "stop"}],
                }
            )
        ),
    )

    assert provider.generate(_request()).content == "mocked"


def test_provider_error_envelope_can_include_request_id() -> None:
    """Provider error 应兼容现有项目 error envelope。"""
    payload = build_error_payload(
        code=ERROR_LLM_PROVIDER_FAILED,
        message="provider failed",
        request_id="req-provider-1",
    )

    assert payload[ERROR_KEY][ERROR_REQUEST_ID_KEY] == "req-provider-1"


def _request() -> LLMGenerateRequest:
    return LLMGenerateRequest(
        purpose=PURPOSE_QUESTION,
        job={"title": "Backend Engineer"},
        resume={"summary": "Python API experience"},
        history=[{"question": "Tell me about persistence.", "answer": "Use sqlite."}],
        last_answer=None,
        metadata={"source": "unit"},
        request_id="req-provider-1",
        session_id="session-provider-1",
        turn_index=0,
        prompt_version=DEFAULT_PROMPT_VERSION,
    )


def _real_config() -> LLMProviderConfig:
    return LLMProviderConfig(
        provider=LLM_PROVIDER_OPENAI,
        api_key="test-key",
        model="test-model",
        timeout_seconds=1.5,
        environment="test",
    )


class FakeTransport:
    """证明 provider 测试不访问外部网络的 transport double。"""

    def __init__(
        self,
        response: "FakeResponse | None" = None,
        *,
        exc: Exception | None = None,
    ) -> None:
        """保存 adapter 边界使用的 fake response 或 exception。"""
        self.response = response or FakeResponse({})
        self.exc = exc
        self.calls: list[dict[str, Any]] = []

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,
    ) -> "FakeResponse":
        """记录 outbound request，而不是构造 HTTP client。"""
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "json": json,
                "timeout": timeout,
            }
        )
        if self.exc is not None:
            raise self.exc
        return self.response


class FakeResponse:
    """用于覆盖 adapter 解析和错误路径的最小 response double。"""

    def __init__(self, payload: dict[str, Any], *, status_code: int = 200) -> None:
        """记录返回给 provider adapter 的 payload 形状。"""
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        """模拟 httpx status handling，不发送网络请求。"""
        if self.status_code >= 400:
            request = httpx.Request("POST", "https://provider.test/generate")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("provider failed", request=request, response=response)

    def json(self) -> dict[str, Any]:
        """返回供 adapter 解析的 JSON payload。"""
        return self.payload
