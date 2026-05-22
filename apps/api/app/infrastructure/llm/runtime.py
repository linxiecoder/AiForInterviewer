"""Runtime wiring for LLM transports."""

from __future__ import annotations

import os

from app.infrastructure.llm.fake_transport import FakeLlmTransport
from app.infrastructure.llm.job_match import LlmJobMatchAnalyzer
from app.infrastructure.llm.openai_compatible import (
    LLM_PROVIDER_ENV,
    OpenAICompatibleLlmSettings,
    OpenAICompatibleLlmTransport,
)
from app.application.llm.ports import LlmTransport


def build_job_match_analyzer_from_env() -> LlmJobMatchAnalyzer:
    return LlmJobMatchAnalyzer(build_llm_transport_from_env())


def build_llm_transport_from_env() -> LlmTransport:
    provider = (os.getenv(LLM_PROVIDER_ENV) or "openai_compatible").strip().lower()
    if provider in {"openai", "openai_compatible", "openai-compatible", "deepseek"}:
        return OpenAICompatibleLlmTransport(OpenAICompatibleLlmSettings.from_env())
    if provider == "fake":
        return FakeLlmTransport()
    raise ValueError(
        f"Unsupported {LLM_PROVIDER_ENV}: {provider or '<blank>'}. "
        "Supported values: openai_compatible, deepseek, fake."
    )
