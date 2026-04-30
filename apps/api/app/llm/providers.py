"""ST13_11 provider 实现；不包含 interview main flow 业务。"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Protocol

import httpx

from app.llm.config import LLMProviderConfig, load_llm_provider_config
from app.llm.constants import (
    ERROR_LLM_PROVIDER_FAILED,
    ERROR_LLM_PROVIDER_INVALID,
    ERROR_LLM_PROVIDER_TIMEOUT,
    ERROR_LLM_PROVIDER_UNAVAILABLE,
    LLM_PROVIDER_DETERMINISTIC,
    LLM_PROVIDER_OPENAI,
)
from app.llm.errors import LLMProviderError
from app.llm.models import LLMGenerateRequest, LLMGenerateResult


class LLMProvider(Protocol):
    """后续 R0 主链路必须经由的单一生成边界。"""

    def generate(self, request: LLMGenerateRequest) -> LLMGenerateResult:
        """执行一次生成，失败时抛出稳定 provider error，不做 fallback。"""


class LLMTransport(Protocol):
    """HTTP-like 边界，使真实 provider 调用在测试中可替换。"""

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,
    ) -> Any:
        """在显式网络边界发起 post，并返回 response-like 对象。"""


class DeterministicLLMProvider:
    """仅限 test/dev 显式配置的稳定 provider，不代表真实 LLM 成功。"""

    def generate(self, request: LLMGenerateRequest) -> LLMGenerateResult:
        """只在 deterministic 被显式配置后返回可预测输出。"""
        job_title = _text_value(request.job, "title", default="unknown job")
        resume_summary = _text_value(request.resume, "summary", default="no resume")
        content = (
            f"deterministic {request.purpose} for {job_title}; "
            f"resume={resume_summary}; turn={request.turn_index}"
        )
        metadata = {
            **dict(request.metadata),
            "provider": LLM_PROVIDER_DETERMINISTIC,
            "deterministic": True,
            "session_id": request.session_id,
            "turn_index": request.turn_index,
            "prompt_version": request.prompt_version,
        }
        return LLMGenerateResult(
            provider=LLM_PROVIDER_DETERMINISTIC,
            model=LLM_PROVIDER_DETERMINISTIC,
            content=content,
            finish_reason="stop",
            request_id=request.request_id,
            metadata=metadata,
        )


class OpenAICompatibleLLMProvider:
    """OpenAI-compatible adapter；测试必须替换 transport 而不联网。"""

    def __init__(
        self,
        config: LLMProviderConfig,
        *,
        transport: LLMTransport | None = None,
    ) -> None:
        """创建 adapter，不校验真实 key，也不联系外部 provider。"""
        if config.provider != LLM_PROVIDER_OPENAI:
            raise LLMProviderError(
                code=ERROR_LLM_PROVIDER_INVALID,
                message=f"unsupported real provider config: {config.provider}",
            )
        self.config = config
        self.transport = transport or HttpxLLMTransport()

    def generate(self, request: LLMGenerateRequest) -> LLMGenerateResult:
        """调用已配置 provider，并禁止失败后退回 deterministic。"""
        try:
            response = self.transport.post(
                self.config.endpoint,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json=_openai_payload(request=request, model=self.config.model),
                timeout=self.config.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            return _openai_result(
                payload=payload,
                request=request,
                fallback_model=self.config.model,
            )
        except httpx.TimeoutException as exc:
            raise _provider_error(
                code=ERROR_LLM_PROVIDER_TIMEOUT,
                message="LLM provider timed out",
                request=request,
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise _provider_error(
                code=ERROR_LLM_PROVIDER_FAILED,
                message="LLM provider request failed",
                request=request,
                details={"status_code": exc.response.status_code},
            ) from exc
        except httpx.RequestError as exc:
            raise _provider_error(
                code=ERROR_LLM_PROVIDER_UNAVAILABLE,
                message="LLM provider is unavailable",
                request=request,
            ) from exc
        except (KeyError, TypeError, ValueError) as exc:
            raise _provider_error(
                code=ERROR_LLM_PROVIDER_FAILED,
                message="LLM provider response was invalid",
                request=request,
            ) from exc


class HttpxLLMTransport:
    """默认 runtime transport；单元测试应注入 fake transport。"""

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,
    ) -> httpx.Response:
        """只在 provider generate 边界发送一次 HTTP 请求。"""
        with httpx.Client() as client:
            return client.post(url, headers=headers, json=json, timeout=timeout)


def build_llm_provider(config: LLMProviderConfig | None = None) -> LLMProvider:
    """构造已配置 provider，不做静默 deterministic fallback。"""
    resolved_config = config or load_llm_provider_config()
    if resolved_config.provider == LLM_PROVIDER_DETERMINISTIC:
        return DeterministicLLMProvider()
    if resolved_config.provider == LLM_PROVIDER_OPENAI:
        return OpenAICompatibleLLMProvider(resolved_config)
    raise LLMProviderError(
        code=ERROR_LLM_PROVIDER_INVALID,
        message=f"unsupported LLM provider: {resolved_config.provider}",
    )


def _openai_payload(*, request: LLMGenerateRequest, model: str) -> dict[str, Any]:
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You generate concise interview assistant output for the "
                    "requested R0 interview purpose."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "purpose": request.purpose,
                        "job": request.job,
                        "resume": request.resume,
                        "history": request.history,
                        "last_answer": request.last_answer,
                        "metadata": request.metadata,
                        "request_id": request.request_id,
                        "session_id": request.session_id,
                        "turn_index": request.turn_index,
                        "prompt_version": request.prompt_version,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            },
        ],
    }


def _openai_result(
    *,
    payload: Mapping[str, Any],
    request: LLMGenerateRequest,
    fallback_model: str,
) -> LLMGenerateResult:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("provider response missing choices")
    first_choice = choices[0]
    if not isinstance(first_choice, Mapping):
        raise ValueError("provider choice is invalid")
    message = first_choice.get("message")
    if not isinstance(message, Mapping):
        raise ValueError("provider response missing message")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("provider response content is empty")
    finish_reason = first_choice.get("finish_reason")
    usage = payload.get("usage")
    provider_request_id = payload.get("id")
    return LLMGenerateResult(
        provider=LLM_PROVIDER_OPENAI,
        model=str(payload.get("model") or fallback_model),
        content=content,
        finish_reason=str(finish_reason or "unknown"),
        request_id=request.request_id,
        metadata={
            **dict(request.metadata),
            "provider": LLM_PROVIDER_OPENAI,
            "session_id": request.session_id,
            "turn_index": request.turn_index,
            "prompt_version": request.prompt_version,
        },
        usage=dict(usage) if isinstance(usage, Mapping) else None,
        provider_request_id=str(provider_request_id) if provider_request_id else None,
    )


def _provider_error(
    *,
    code: str,
    message: str,
    request: LLMGenerateRequest,
    details: dict[str, Any] | None = None,
) -> LLMProviderError:
    return LLMProviderError(
        code=code,
        message=message,
        request_id=request.request_id,
        details=details,
    )


def _text_value(mapping: Mapping[str, Any], key: str, *, default: str) -> str:
    value = mapping.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default
