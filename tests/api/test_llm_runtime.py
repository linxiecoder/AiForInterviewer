from app.infrastructure.llm.openai_compatible import OpenAICompatibleLlmTransport
from app.infrastructure.llm.runtime import build_llm_transport_from_env


def test_runtime_treats_blank_provider_as_openai_compatible(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "")

    transport = build_llm_transport_from_env()

    assert isinstance(transport, OpenAICompatibleLlmTransport)


def test_runtime_treats_deepseek_as_openai_compatible_provider(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")

    transport = build_llm_transport_from_env()

    assert isinstance(transport, OpenAICompatibleLlmTransport)
