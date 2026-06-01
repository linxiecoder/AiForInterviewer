import pytest

from app.application.llm.errors import LlmTransportConfigurationError
from app.infrastructure.llm.fake_transport import FakeLlmTransport
from app.infrastructure.llm.openai_compatible import OpenAICompatibleLlmTransport
from app.infrastructure.llm.runtime import build_llm_transport_from_env
from app.main import create_app


def test_runtime_treats_blank_provider_as_openai_compatible(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "")

    transport = build_llm_transport_from_env()

    assert isinstance(transport, OpenAICompatibleLlmTransport)


def test_runtime_treats_deepseek_as_openai_compatible_provider(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")

    transport = build_llm_transport_from_env()

    assert isinstance(transport, OpenAICompatibleLlmTransport)


def test_runtime_rejects_disabled_provider(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "disabled")

    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER: disabled"):
        build_llm_transport_from_env()


def test_runtime_rejects_fake_provider_from_env(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    with pytest.raises(
        LlmTransportConfigurationError,
        match="FakeLlmTransport.*explicit test injection.*runtime env",
    ):
        build_llm_transport_from_env()


def test_create_app_rejects_fake_provider_from_env(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    with pytest.raises(
        LlmTransportConfigurationError,
        match="FakeLlmTransport.*explicit test injection.*runtime env",
    ):
        create_app()


def test_explicit_fake_transport_instantiation_remains_available() -> None:
    transport = FakeLlmTransport()

    assert transport.status == "deterministic_fake_only"
