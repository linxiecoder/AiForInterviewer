"""OpenAI-compatible Chat Completions transport."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import logging
import os
from time import perf_counter
from typing import Any
from urllib.parse import urlparse

import httpx

from app.domain.shared.enums import ConfidenceLevel, ValidationStatus
from app.domain.shared.ids import stable_resource_id
from app.application.llm.errors import (
    LlmTransportConfigurationError,
    LlmTransportResponseError,
    LlmTransportUnavailableError,
)
from app.infrastructure.llm.job_match import JOB_MATCH_PROMPT_VERSION
from app.application.llm.types import LlmTransportRequest, LlmTransportResult


DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_TIMEOUT_SECONDS = 45.0
DEFAULT_TEMPERATURE = 0.0
LLM_PROVIDER_ENV = "LLM_PROVIDER"
LLM_OPENAI_API_KEY_ENV = "LLM_OPENAI_API_KEY"
LLM_OPENAI_BASE_URL_ENV = "LLM_OPENAI_BASE_URL"
LLM_OPENAI_MODEL_ENV = "LLM_OPENAI_MODEL"
LLM_OPENAI_TIMEOUT_SECONDS_ENV = "LLM_OPENAI_TIMEOUT_SECONDS"
LLM_OPENAI_TEMPERATURE_ENV = "LLM_OPENAI_TEMPERATURE"
LLM_TRANSPORT_LOGGER_NAME = "app.llm.transport"

@dataclass(frozen=True)
class OpenAICompatibleLlmSettings:
    """OpenAI 协议运行配置，密钥只从环境变量读取，不进入前端响应或日志。"""

    api_key: str
    model: str = DEFAULT_OPENAI_MODEL
    base_url: str = DEFAULT_OPENAI_BASE_URL
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    temperature: float = DEFAULT_TEMPERATURE

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
    ) -> "OpenAICompatibleLlmSettings":
        """从环境变量（或传入字典）读取 LLM 配置。API 密钥只从环境变量读取，不进入前端响应或日志。"""
        values = environ or os.environ
        return cls(
            api_key=_env_optional(values, LLM_OPENAI_API_KEY_ENV)
            or _env_optional(values, "OPENAI_API_KEY")
            or "",
            model=_env_optional(values, LLM_OPENAI_MODEL_ENV)
            or _env_optional(values, "OPENAI_MODEL")
            or DEFAULT_OPENAI_MODEL,
            base_url=_normalize_base_url(
                _env_optional(values, LLM_OPENAI_BASE_URL_ENV)
                or _env_optional(values, "OPENAI_BASE_URL")
                or DEFAULT_OPENAI_BASE_URL,
            ),
            timeout_seconds=_env_float(
                values,
                LLM_OPENAI_TIMEOUT_SECONDS_ENV,
                DEFAULT_TIMEOUT_SECONDS,
            ),
            temperature=_env_float(
                values,
                LLM_OPENAI_TEMPERATURE_ENV,
                DEFAULT_TEMPERATURE,
            ),
        )


class OpenAICompatibleLlmTransport:
    """通过 OpenAI Chat Completions 协议调用模型，并只接收结构化 JSON。"""

    status = "openai_compatible"

    def __init__(
        self,
        settings: OpenAICompatibleLlmSettings,
        *,
        client: httpx.Client | None = None,
    ) -> None:
        """初始化传输层；可注入外部 httpx.Client（用于测试）。"""
        self._settings = settings
        self._client = client
        self._logger = _llm_transport_logger()

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        """调用 LLM provider 生成结果。密钥为空时抛出配置异常。"""
        if not self._settings.api_key.strip():
            raise LlmTransportConfigurationError(
                f"{LLM_OPENAI_API_KEY_ENV} 未配置，请在 .env 中设置 OpenAI 兼容模型密钥。"
            )

        # 这里刻意不记录 prompt、completion 或 provider payload，避免把简历和密钥边界外泄到日志。
        if self._client is not None:
            return self._generate_with_client(self._client, request)

        with httpx.Client(timeout=self._settings.timeout_seconds) as client:
            return self._generate_with_client(client, request)

    def _generate_with_client(
        self,
        client: httpx.Client,
        request: LlmTransportRequest,
    ) -> LlmTransportResult:
        """使用指定 httpx 客户端向 /chat/completions 发送请求并解析响应。"""
        started_at = perf_counter()
        self._log_request_start(request)
        try:
            response = client.post(
                f"{self._settings.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._settings.api_key}",
                    "Content-Type": "application/json",
                },
                json=_chat_completion_payload(self._settings, request),
                timeout=self._settings.timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            self._log_request_failed(request, started_at=started_at, error_type="timeout")
            raise LlmTransportUnavailableError("LLM provider 请求超时。") from exc
        except httpx.HTTPError as exc:
            self._log_request_failed(request, started_at=started_at, error_type=type(exc).__name__)
            raise LlmTransportUnavailableError("LLM provider 请求失败。") from exc

        if response.status_code in {401, 403}:
            self._log_request_failed(
                request,
                started_at=started_at,
                error_type="authentication_failed",
                status_code=response.status_code,
            )
            raise LlmTransportConfigurationError("LLM provider 鉴权失败，请检查 .env 中的模型密钥。")
        if response.status_code == 429:
            self._log_request_failed(
                request,
                started_at=started_at,
                error_type="rate_limited",
                status_code=response.status_code,
            )
            raise LlmTransportUnavailableError("LLM provider 当前限流，请稍后重试。")
        if response.status_code >= 500:
            self._log_request_failed(
                request,
                started_at=started_at,
                error_type="provider_unavailable",
                status_code=response.status_code,
            )
            raise LlmTransportUnavailableError("LLM provider 暂时不可用。")
        if response.status_code >= 400:
            self._log_request_failed(
                request,
                started_at=started_at,
                error_type="provider_http_error",
                status_code=response.status_code,
            )
            raise LlmTransportUnavailableError(f"LLM provider 返回 HTTP {response.status_code}。")

        response_json = _response_json(response)
        result = _parse_json_result(response_json)
        result.setdefault("prompt_version", _request_prompt_version(request))
        # model_name 用于审计和落库，只能来自 provider 外层响应或本地配置；
        # 不能信任模型正文里自报的 model_name，否则会出现"实际调用 deepseek，记录成 gpt-4"的偏差。
        result["model_name"] = _provider_model_name(response_json, self._settings.model)
        self._log_request_success(
            request,
            started_at=started_at,
            status_code=response.status_code,
            provider_model=result["model_name"],
        )
        return LlmTransportResult(
            result=result,
            validation_status=ValidationStatus.VALID,
            confidence_level=_confidence_level(result),
            low_confidence_flags=_low_confidence_flags(result),
            trace_refs=(_trace_ref(request, response_json),),
            evidence_refs=(_evidence_ref(request),),
        )

    def _log_request_start(self, request: LlmTransportRequest) -> None:
        """记录 LLM 请求启动日志（含 task_type / model / contract_ids 等关键字段）。"""
        self._logger.info(
            _json_log(
                {
                    "event": "llm_transport_request_start",
                    "task_type": request.task_type,
                    "model": self._settings.model,
                    "provider_base_host": _base_url_host(self._settings.base_url),
                    "contract_ids": list(request.contract_ids),
                    "input_ref_count": len(request.input_refs),
                    "timeout_seconds": self._settings.timeout_seconds,
                }
            )
        )

    def _log_request_success(
        self,
        request: LlmTransportRequest,
        *,
        started_at: float,
        status_code: int,
        provider_model: str,
    ) -> None:
        """记录 LLM 请求成功日志（含耗时和 provider 实际模型名）。"""
        self._logger.info(
            _json_log(
                {
                    "event": "llm_transport_request_success",
                    "task_type": request.task_type,
                    "model": self._settings.model,
                    "provider_model": provider_model,
                    "status_code": status_code,
                    "duration_ms": _duration_ms(started_at),
                }
            )
        )

    def _log_request_failed(
        self,
        request: LlmTransportRequest,
        *,
        started_at: float,
        error_type: str,
        status_code: int | None = None,
    ) -> None:
        """记录 LLM 请求失败日志（含错误类型和可选 HTTP 状态码）。"""
        record: dict[str, Any] = {
            "event": "llm_transport_request_failed",
            "task_type": request.task_type,
            "model": self._settings.model,
            "error_type": error_type,
            "duration_ms": _duration_ms(started_at),
        }
        if status_code is not None:
            record["status_code"] = status_code
        self._logger.info(_json_log(record))


def _chat_completion_payload(
    settings: OpenAICompatibleLlmSettings,
    request: LlmTransportRequest,
) -> dict[str, Any]:
    """构造 OpenAI Chat Completions 请求体，含 system prompt 和 evidence bundle。"""
    return {
        "model": settings.model,
        "temperature": settings.temperature,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": _system_prompt(request.task_type),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "task_type": request.task_type,
                        "contract_ids": list(request.contract_ids),
                        "input_refs": list(request.input_refs),
                        "evidence_bundle": request.evidence_bundle,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            },
        ],
    }


def _llm_transport_logger() -> logging.Logger:
    """获取 LLM 传输日志记录器（自动添加控制台 handler）。"""
    logger = logging.getLogger(LLM_TRANSPORT_LOGGER_NAME)
    if logger.level == logging.NOTSET:
        logger.setLevel(logging.INFO)
    _ensure_console_handler(logger)
    return logger


def _ensure_console_handler(logger: logging.Logger) -> None:
    """确保日志记录器已添加控制台 handler（避免重复添加）。"""
    if any(getattr(handler, "_aifi_llm_transport_handler", False) for handler in logger.handlers):
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler._aifi_llm_transport_handler = True  # type: ignore[attr-defined]
    logger.addHandler(handler)


def _json_log(record: dict[str, Any]) -> str:
    """将日志字典序列化为 JSON 字符串（中文不转义，key 排序）。"""
    return json.dumps(record, ensure_ascii=False, sort_keys=True)


def _duration_ms(started_at: float) -> float:
    """计算从 started_at 到当前时间的毫秒数。"""
    return round((perf_counter() - started_at) * 1000, 3)


def _base_url_host(base_url: str) -> str:
    """从 base_url 中提取主机名（用于日志脱敏）。"""
    parsed = urlparse(base_url)
    return parsed.netloc or parsed.path or "unknown"


def _system_prompt(task_type: str) -> str:
    """根据 task_type 构造 system prompt。job_match_analysis 使用专用 prompt，其余使用通用 prompt。"""
    if task_type == "job_match_analysis":
        return "\n".join(
            [
                "你是 AiForInterviewer 的岗位匹配分析器。",
                "必须使用中文输出，不要返回英文说明。",
                "只返回合法 JSON，不要 Markdown 包裹。",
                "根对象必须包含 prompt_version、job_match_result_payload；不要自行声明 model_name，服务端会记录 provider 实际模型。",
                "job_match_result_payload 必须包含 overall_score、overall_level、confidence、summary、dimension_scores、matched_requirements、missing_requirements、resume_evidence、risk_flags、interview_focus、suggested_questions、markdown_report。",
                "数组字段必须严格返回对象数组：dimension_scores、matched_requirements、missing_requirements、resume_evidence、risk_flags 都不能简写成字符串数组或字典。",
                "matched_requirements 每项必须包含 requirement_chunk_id、resume_evidence_chunk_ids、rationale、confidence；missing_requirements 每项必须包含 requirement_chunk_id、reason、confidence、evidence_insufficient。",
                "resume_evidence 每项必须包含 chunk_id、summary、confidence；risk_flags 每项必须包含 risk_type、description、severity、supporting_evidence。",
                "dimension_scores 必须且只能包含 requirement_alignment(30)、experience_evidence(25)、skill_coverage(20)、gap_risk(15)、readiness_actions(10)，各维度分数总和必须等于 overall_score。",
                "所有 evidence chunk_id 必须来自输入 evidence_bundle；不能编造来源。",
                "overall_score 必须基于简历证据与岗位要求的分析判断，不得固定为模板分。",
                "评分来源权重：岗位要求约占 65%，岗位职责约占 35%；岗位要求缺口应优先影响 requirement_alignment 与 gap_risk。",
                "overall_level 阈值：80 及以上 strong_match，60-79 medium_match，60 以下 weak_match；证据不足时用 insufficient_evidence。",
                f"prompt_version 固定为 {JOB_MATCH_PROMPT_VERSION}。",
            ]
        )
    return "\n".join(
        [
            "你是 AiForInterviewer 的结构化 JSON 任务执行器。",
            "必须使用中文输出，不要返回英文说明。",
            "只返回合法 JSON，不要 Markdown 包裹。",
            "必须严格遵守 user message 中 evidence_bundle.prompt、output_schema、schema_id 和 prompt_version。",
            "不得暴露 provider payload、secret、token 或原始 completion。",
        ]
    )


def _request_prompt_version(request: LlmTransportRequest) -> str:
    """从 evidence_bundle 中提取 prompt_version；若无则返回默认版本。"""
    if isinstance(request.evidence_bundle, dict):
        prompt_version = request.evidence_bundle.get("prompt_version")
        if isinstance(prompt_version, str) and prompt_version.strip():
            return prompt_version.strip()
    if request.task_type == "job_match_analysis":
        return JOB_MATCH_PROMPT_VERSION
    return "unversioned_llm_task"


def _response_json(response: httpx.Response) -> dict[str, Any]:
    """解析 HTTP 响应为 JSON 字典，非 JSON 或非对象时报错。"""
    try:
        data = response.json()
    except ValueError as exc:
        raise LlmTransportResponseError("LLM provider 返回的响应不是 JSON。") from exc
    if not isinstance(data, dict):
        raise LlmTransportResponseError("LLM provider 返回的 JSON 根节点不是对象。")
    return data


def _parse_json_result(response_json: dict[str, Any]) -> dict[str, Any]:
    """从 Chat Completions 响应中提取 choices[0].message.content 并解析为 JSON。"""
    choices = response_json.get("choices")
    if not isinstance(choices, list) or not choices:
        raise LlmTransportResponseError("LLM provider 响应缺少 choices。")
    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise LlmTransportResponseError("LLM provider choices[0] 不是对象。")
    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise LlmTransportResponseError("LLM provider 响应缺少 message。")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise LlmTransportResponseError("LLM provider 响应缺少文本内容。")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise LlmTransportResponseError("LLM provider 文本内容不是合法 JSON。") from exc
    if not isinstance(parsed, dict):
        raise LlmTransportResponseError("LLM provider 文本 JSON 根节点不是对象。")
    return parsed


def _provider_model_name(response_json: dict[str, Any], configured_model: str) -> str:
    """从 provider 响应中提取实际模型名；不存在则返回配置的模型名。"""
    model = response_json.get("model")
    if isinstance(model, str) and model.strip():
        return model.strip()
    return configured_model


def _confidence_level(result: dict[str, Any]) -> ConfidenceLevel:
    """从 LLM 结果中提取置信度等级；默认 MEDIUM。"""
    payload = result.get("job_match_result_payload")
    confidence = payload.get("confidence") if isinstance(payload, dict) else None
    try:
        return ConfidenceLevel(confidence)
    except ValueError:
        return ConfidenceLevel.MEDIUM


def _low_confidence_flags(result: dict[str, Any]) -> tuple[str, ...]:
    """根据置信度等级生成低置信度标记元组。"""
    confidence = _confidence_level(result)
    if confidence is ConfidenceLevel.LOW:
        return ("llm_low_confidence",)
    if confidence is ConfidenceLevel.INSUFFICIENT:
        return ("llm_insufficient_evidence",)
    return ()


def _trace_ref(request: LlmTransportRequest, response_json: dict[str, Any]) -> str:
    """生成 LLM 调用的 trace 引用 ID（基于 request 和 provider 响应）。"""
    seed = json.dumps(
        {
            "provider_response_id": response_json.get("id"),
            "model": response_json.get("model"),
            "task_type": request.task_type,
            "input_refs": sorted(request.input_refs),
        },
        ensure_ascii=True,
        sort_keys=True,
    )
    return stable_resource_id("trace", f"openai-compatible-trace:{seed}")


def _evidence_ref(request: LlmTransportRequest) -> str:
    """生成 LLM 调用的 evidence 引用 ID（基于 request 摘要）。"""
    seed = json.dumps(
        {
            "task_type": request.task_type,
            "input_refs": sorted(request.input_refs),
            "source_digest": request.evidence_bundle.get("source_digest"),
        },
        ensure_ascii=True,
        sort_keys=True,
    )
    return stable_resource_id("trace", f"openai-compatible-evidence:{seed}")


def _env_optional(values: Mapping[str, str], name: str) -> str | None:
    """从环境变量字典中读取可选字符串；不存在或空白时返回 None。"""
    value = values.get(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _env_float(values: Mapping[str, str], name: str, default: float) -> float:
    """从环境变量字典中读取浮点数；解析失败时返回默认值。"""
    value = _env_optional(values, name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _normalize_base_url(raw: str) -> str:
    """标准化 base_url：去除首尾空白和尾部斜杠，为空时返回默认值。"""
    return raw.strip().rstrip("/") or DEFAULT_OPENAI_BASE_URL
