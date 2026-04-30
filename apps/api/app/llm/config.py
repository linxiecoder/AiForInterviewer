"""仅服务于 provider 边界的环境变量配置读取。"""

from __future__ import annotations

import os
from dataclasses import dataclass

from app.boundary import DEFAULT_ENVIRONMENT, ENVIRONMENT_ENV
from app.llm.constants import (
    DEFAULT_LLM_TIMEOUT_SECONDS,
    DEFAULT_OPENAI_ENDPOINT,
    ERROR_LLM_PROVIDER_CONFIG_MISSING,
    ERROR_LLM_PROVIDER_INVALID,
    LLM_API_KEY_ENV,
    LLM_BASE_URL_ENV,
    LLM_MODEL_ENV,
    LLM_PROVIDER_DETERMINISTIC,
    LLM_PROVIDER_ENV,
    LLM_PROVIDER_OPENAI,
    LLM_TIMEOUT_SECONDS_ENV,
    SUPPORTED_LLM_PROVIDERS,
    TEST_DEV_ENVIRONMENTS,
)
from app.llm.errors import LLMProviderError


@dataclass(frozen=True)
class LLMProviderConfig:
    """已解析的 provider 配置，不在配置阶段触发网络调用。"""

    provider: str
    model: str
    timeout_seconds: float
    environment: str
    api_key: str | None = None
    endpoint: str = DEFAULT_OPENAI_ENDPOINT


def load_llm_provider_config() -> LLMProviderConfig:
    """读取 provider 环境变量，不校验真实 key，也不访问网络。"""
    provider = _env_optional(LLM_PROVIDER_ENV)
    environment = (_env_optional(ENVIRONMENT_ENV) or DEFAULT_ENVIRONMENT).lower()
    if provider is None:
        raise LLMProviderError(
            code=ERROR_LLM_PROVIDER_CONFIG_MISSING,
            message=f"{LLM_PROVIDER_ENV} is required",
        )

    normalized_provider = provider.lower()
    if normalized_provider not in SUPPORTED_LLM_PROVIDERS:
        raise LLMProviderError(
            code=ERROR_LLM_PROVIDER_INVALID,
            message=f"unsupported LLM provider: {provider}",
        )

    timeout_seconds = _env_float(LLM_TIMEOUT_SECONDS_ENV, DEFAULT_LLM_TIMEOUT_SECONDS)
    if normalized_provider == LLM_PROVIDER_DETERMINISTIC:
        if environment not in TEST_DEV_ENVIRONMENTS:
            raise LLMProviderError(
                code=ERROR_LLM_PROVIDER_INVALID,
                message="deterministic provider is only available for test/dev",
            )
        return LLMProviderConfig(
            provider=LLM_PROVIDER_DETERMINISTIC,
            model=LLM_PROVIDER_DETERMINISTIC,
            timeout_seconds=timeout_seconds,
            environment=environment,
        )

    api_key = _env_optional(LLM_API_KEY_ENV)
    model = _env_optional(LLM_MODEL_ENV)
    if normalized_provider == LLM_PROVIDER_OPENAI and (api_key is None or model is None):
        raise LLMProviderError(
            code=ERROR_LLM_PROVIDER_CONFIG_MISSING,
            message=f"{LLM_API_KEY_ENV} and {LLM_MODEL_ENV} are required for real provider",
        )

    return LLMProviderConfig(
        provider=normalized_provider,
        api_key=api_key,
        model=model or "",
        timeout_seconds=timeout_seconds,
        environment=environment,
        endpoint=_env_optional(LLM_BASE_URL_ENV) or DEFAULT_OPENAI_ENDPOINT,
    )


def _env_optional(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _env_float(name: str, default: float) -> float:
    value = _env_optional(name)
    if value is None:
        return default
    try:
        parsed = float(value)
    except ValueError:
        return default
    return parsed if parsed > 0 else default
