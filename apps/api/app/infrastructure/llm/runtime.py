"""Runtime wiring for LLM transports."""

from __future__ import annotations

import os

from app.application.llm.errors import LlmTransportConfigurationError
from app.infrastructure.llm.job_match import LlmJobMatchAnalyzer
from app.infrastructure.llm.openai_compatible import (
    LLM_PROVIDER_ENV,
    OpenAICompatibleLlmSettings,
    OpenAICompatibleLlmTransport,
)
from app.infrastructure.observability.logging import LogUtil
from app.application.llm.ports import LlmTransport


def build_job_match_analyzer_from_env() -> LlmJobMatchAnalyzer:
    """从环境变量构建岗位匹配分析器（含 LLM 传输层）。"""
    return LlmJobMatchAnalyzer(build_llm_transport_from_env())


def build_llm_transport_from_env() -> LlmTransport:
    """从环境变量构建 LLM 传输层实例。支持 openai_compatible / deepseek。"""
    provider = (os.getenv(LLM_PROVIDER_ENV) or "openai_compatible").strip().lower()
    LogUtil.llm_provider_resolved(provider=provider)
    if provider in {"openai", "openai_compatible", "openai-compatible", "deepseek"}:
        LogUtil.llm_transport_built(kind="openai_compatible", provider=provider)
        return OpenAICompatibleLlmTransport(OpenAICompatibleLlmSettings.from_env())
    if provider == "fake":
        raise LlmTransportConfigurationError(
            "FakeLlmTransport is reserved for explicit test injection and cannot be "
            f"enabled through runtime env {LLM_PROVIDER_ENV}=fake."
        )
    raise ValueError(
        f"Unsupported {LLM_PROVIDER_ENV}: {provider or '<blank>'}."
        "Supported values: openai_compatible, deepseek."
    )
