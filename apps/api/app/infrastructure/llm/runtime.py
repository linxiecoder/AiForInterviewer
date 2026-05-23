"""Runtime wiring for LLM transports."""

from __future__ import annotations

import logging
import os

from app.infrastructure.llm.fake_transport import FakeLlmTransport
from app.infrastructure.llm.job_match import LlmJobMatchAnalyzer
from app.infrastructure.llm.openai_compatible import (
    LLM_PROVIDER_ENV,
    OpenAICompatibleLlmSettings,
    OpenAICompatibleLlmTransport,
)
from app.application.llm.ports import LlmTransport

logger = logging.getLogger(__name__)


def build_job_match_analyzer_from_env() -> LlmJobMatchAnalyzer:
    """从环境变量构建岗位匹配分析器（含 LLM 传输层）。"""
    return LlmJobMatchAnalyzer(build_llm_transport_from_env())


def build_llm_transport_from_env() -> LlmTransport:
    """从环境变量构建 LLM 传输层实例。支持 openai_compatible / deepseek / fake。"""
    provider = (os.getenv(LLM_PROVIDER_ENV) or "openai_compatible").strip().lower()
    logger.info("llm.provider.resolved provider=%s", provider)
    if provider in {"openai", "openai_compatible", "openai-compatible", "deepseek"}:
        logger.info("llm.transport.built kind=openai_compatible provider=%s", provider)
        return OpenAICompatibleLlmTransport(OpenAICompatibleLlmSettings.from_env())
    if provider == "fake":
        logger.info("llm.transport.built kind=fake provider=fake")
        return FakeLlmTransport()
    raise ValueError(
        f"Unsupported {LLM_PROVIDER_ENV}: {provider or '<blank>'}."
        "Supported values: openai_compatible, deepseek, fake."
    )
