"""OpenAI-compatible Chat Completions transport."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
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
from app.infrastructure.env_reader import EnvReader
from app.infrastructure.observability.logging import LogUtil, get_request_trace_context


DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_TIMEOUT_SECONDS = 45.0
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 8000
DEFAULT_PROGRESS_TREE_MAX_TOKENS = 12000
PROGRESS_TREE_QUALITY_FIRST_TASK_TYPE = "polish_progress_quality_first_menu"
NO_REQUEST_TIMEOUT_TASK_TYPES = frozenset({"polish_feedback_generation"})
PROVIDER_OUTPUT_TRUNCATED_ERROR_TYPE = "provider_output_truncated"
LLM_PROVIDER_ENV = "LLM_PROVIDER"
LLM_OPENAI_API_KEY_ENV = "LLM_OPENAI_API_KEY"
LLM_OPENAI_BASE_URL_ENV = "LLM_OPENAI_BASE_URL"
LLM_OPENAI_MODEL_ENV = "LLM_OPENAI_MODEL"
LLM_OPENAI_TIMEOUT_SECONDS_ENV = "LLM_OPENAI_TIMEOUT_SECONDS"
LLM_OPENAI_TEMPERATURE_ENV = "LLM_OPENAI_TEMPERATURE"
LLM_OPENAI_MAX_TOKENS_ENV = "LLM_OPENAI_MAX_TOKENS"
LLM_PROGRESS_TREE_MAX_TOKENS_ENV = "LLM_PROGRESS_TREE_MAX_TOKENS"
LLM_OPENAI_TRUST_ENV_ENV = "LLM_OPENAI_TRUST_ENV"
LOCAL_LLM_RAW_IO_ENABLED_ENV = "AIFI_LOCAL_LLM_RAW_IO_ENABLED"
LOCAL_LLM_RAW_IO_DIR_ENV = "AIFI_LOCAL_LLM_RAW_IO_DIR"
LOCAL_LLM_RAW_IO_INCLUDE_HEADERS_ENV = "AIFI_LOCAL_LLM_RAW_IO_INCLUDE_HEADERS"
DEFAULT_LOCAL_LLM_RAW_IO_DIR = ".local/llm-raw"
COMPACT_JSON_REASONING_CONSTRAINT = (
    "请在保证推理准确的前提下，用最精简的步骤完成思考，"
    "避免不必要的分点展开和重复验证。最终输出必须是一个合法、完整的 JSON 对象，"
    "不要包含任何额外说明。"
)


@dataclass(frozen=True)
class OpenAICompatibleLlmSettings:
    """OpenAI 协议运行配置，密钥只从环境变量读取，不进入前端响应或日志。"""

    api_key: str
    model: str = DEFAULT_OPENAI_MODEL
    base_url: str = DEFAULT_OPENAI_BASE_URL
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int = DEFAULT_MAX_TOKENS
    progress_tree_max_tokens: int = DEFAULT_PROGRESS_TREE_MAX_TOKENS
    trust_env: bool = False

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
    ) -> "OpenAICompatibleLlmSettings":
        """从环境变量（或传入字典）读取 LLM 配置。API 密钥只从环境变量读取，不进入前端响应或日志。"""
        env = EnvReader(os.environ if environ is None else environ)
        return cls(
            api_key=env.first_of(LLM_OPENAI_API_KEY_ENV, "OPENAI_API_KEY") or "",
            model=env.first_of(LLM_OPENAI_MODEL_ENV, "OPENAI_MODEL") or DEFAULT_OPENAI_MODEL,
            base_url=_normalize_base_url(
                env.first_of(LLM_OPENAI_BASE_URL_ENV, "OPENAI_BASE_URL")
                or DEFAULT_OPENAI_BASE_URL,
            ),
            timeout_seconds=env.float(LLM_OPENAI_TIMEOUT_SECONDS_ENV, DEFAULT_TIMEOUT_SECONDS),
            temperature=env.float(LLM_OPENAI_TEMPERATURE_ENV, DEFAULT_TEMPERATURE),
            max_tokens=env.int(LLM_OPENAI_MAX_TOKENS_ENV, DEFAULT_MAX_TOKENS),
            progress_tree_max_tokens=env.int(LLM_PROGRESS_TREE_MAX_TOKENS_ENV, DEFAULT_PROGRESS_TREE_MAX_TOKENS),
            trust_env=env.bool(LLM_OPENAI_TRUST_ENV_ENV, False),
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

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        """调用 LLM provider 生成结果。密钥为空时抛出配置异常。"""
        if not self._settings.api_key.strip():
            raise LlmTransportConfigurationError(
                f"{LLM_OPENAI_API_KEY_ENV} 未配置，请在 .env 中设置 OpenAI 兼容模型密钥。"
            )

        # 这里刻意不记录 prompt、completion 或 provider payload，避免把简历和密钥边界外泄到日志。
        if self._client is not None:
            return self._generate_with_client(self._client, request)

        try:
            client = httpx.Client(
                timeout=_request_timeout_seconds(self._settings, request),
                trust_env=self._settings.trust_env,
            )
        except ImportError as exc:
            self._dump_client_initialization_failed(request, exc)
            raise LlmTransportUnavailableError(
                "LLM provider 客户端初始化失败，请检查代理配置或依赖。"
            ) from exc
        with client:
            return self._generate_with_client(client, request)

    def _generate_with_client(
        self,
        client: httpx.Client,
        request: LlmTransportRequest,
    ) -> LlmTransportResult:
        """使用指定 httpx 客户端向 /chat/completions 发送请求并解析响应。"""
        started_at = perf_counter()
        started_at_wall = datetime.now(timezone.utc)
        chat_payload = _chat_completion_payload(self._settings, request)
        request_timeout_seconds = _request_timeout_seconds(self._settings, request)
        request_headers = {
            "Authorization": f"Bearer {self._settings.api_key}",
            "Content-Type": "application/json",
        }
        self._log_request_start(request)
        try:
            response = client.post(
                f"{self._settings.base_url}/chat/completions",
                headers=request_headers,
                json=chat_payload,
                timeout=request_timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            self._log_request_failed(request, started_at=started_at, error_type="timeout")
            _maybe_dump_local_raw_llm_io(
                request=request,
                settings=self._settings,
                started_at=started_at,
                started_at_wall=started_at_wall,
                chat_payload=chat_payload,
                request_headers=request_headers,
                response_status_code=None,
                response_body=None,
                response_text=None,
                parsed_result=None,
                trace_refs=(),
                evidence_refs=(),
                error_type="timeout",
                error_message="LLM provider 请求超时。",
            )
            raise LlmTransportUnavailableError("LLM provider 请求超时。") from exc
        except httpx.HTTPError as exc:
            error_type = type(exc).__name__
            self._log_request_failed(request, started_at=started_at, error_type=error_type)
            _maybe_dump_local_raw_llm_io(
                request=request,
                settings=self._settings,
                started_at=started_at,
                started_at_wall=started_at_wall,
                chat_payload=chat_payload,
                request_headers=request_headers,
                response_status_code=None,
                response_body=None,
                response_text=None,
                parsed_result=None,
                trace_refs=(),
                evidence_refs=(),
                error_type=error_type,
                error_message="LLM provider 请求失败。",
            )
            raise LlmTransportUnavailableError("LLM provider 请求失败。") from exc

        if response.status_code in {401, 403}:
            response_body, response_text = _response_body_for_dump(response)
            self._log_request_failed(
                request,
                started_at=started_at,
                error_type="authentication_failed",
                status_code=response.status_code,
            )
            _maybe_dump_local_raw_llm_io(
                request=request,
                settings=self._settings,
                started_at=started_at,
                started_at_wall=started_at_wall,
                chat_payload=chat_payload,
                request_headers=request_headers,
                response_status_code=response.status_code,
                response_body=response_body,
                response_text=response_text,
                parsed_result=None,
                trace_refs=(),
                evidence_refs=(),
                error_type="authentication_failed",
                error_message="LLM provider 鉴权失败，请检查 .env 中的模型密钥。",
            )
            raise LlmTransportConfigurationError("LLM provider 鉴权失败，请检查 .env 中的模型密钥。")
        if response.status_code == 429:
            response_body, response_text = _response_body_for_dump(response)
            self._log_request_failed(
                request,
                started_at=started_at,
                error_type="rate_limited",
                status_code=response.status_code,
            )
            _maybe_dump_local_raw_llm_io(
                request=request,
                settings=self._settings,
                started_at=started_at,
                started_at_wall=started_at_wall,
                chat_payload=chat_payload,
                request_headers=request_headers,
                response_status_code=response.status_code,
                response_body=response_body,
                response_text=response_text,
                parsed_result=None,
                trace_refs=(),
                evidence_refs=(),
                error_type="rate_limited",
                error_message="LLM provider 当前限流，请稍后重试。",
            )
            raise LlmTransportUnavailableError("LLM provider 当前限流，请稍后重试。")
        if response.status_code >= 500:
            response_body, response_text = _response_body_for_dump(response)
            self._log_request_failed(
                request,
                started_at=started_at,
                error_type="provider_unavailable",
                status_code=response.status_code,
            )
            _maybe_dump_local_raw_llm_io(
                request=request,
                settings=self._settings,
                started_at=started_at,
                started_at_wall=started_at_wall,
                chat_payload=chat_payload,
                request_headers=request_headers,
                response_status_code=response.status_code,
                response_body=response_body,
                response_text=response_text,
                parsed_result=None,
                trace_refs=(),
                evidence_refs=(),
                error_type="provider_unavailable",
                error_message="LLM provider 暂时不可用。",
            )
            raise LlmTransportUnavailableError("LLM provider 暂时不可用。")
        if response.status_code >= 400:
            response_body, response_text = _response_body_for_dump(response)
            self._log_request_failed(
                request,
                started_at=started_at,
                error_type="provider_http_error",
                status_code=response.status_code,
            )
            error_message = f"LLM provider 返回 HTTP {response.status_code}。"
            _maybe_dump_local_raw_llm_io(
                request=request,
                settings=self._settings,
                started_at=started_at,
                started_at_wall=started_at_wall,
                chat_payload=chat_payload,
                request_headers=request_headers,
                response_status_code=response.status_code,
                response_body=response_body,
                response_text=response_text,
                parsed_result=None,
                trace_refs=(),
                evidence_refs=(),
                error_type="provider_http_error",
                error_message=error_message,
            )
            raise LlmTransportUnavailableError(error_message)

        try:
            response_json = _response_json(response)
            result = _parse_json_result(response_json)
        except LlmTransportResponseError as exc:
            response_body, response_text = _response_body_for_dump(response)
            error_type = _llm_response_error_type(exc)
            self._log_request_failed(
                request,
                started_at=started_at,
                error_type=error_type,
                status_code=response.status_code,
            )
            _maybe_dump_local_raw_llm_io(
                request=request,
                settings=self._settings,
                started_at=started_at,
                started_at_wall=started_at_wall,
                chat_payload=chat_payload,
                request_headers=request_headers,
                response_status_code=response.status_code,
                response_body=response_body,
                response_text=response_text,
                parsed_result=None,
                trace_refs=(),
                evidence_refs=(),
                error_type=error_type,
                error_message=str(exc),
            )
            raise
        # model_name 用于审计和落库，只能来自本地配置的请求/provider 边界；
        # 不能信任 provider 响应正文或外层 model claim。
        provider_model = self._settings.model
        result["model_name"] = provider_model
        trace_ref = _trace_ref(request, response_json)
        evidence_ref = _evidence_ref(request)
        self._log_request_success(
            request,
            started_at=started_at,
            status_code=response.status_code,
            provider_model=provider_model,
        )
        _maybe_dump_local_raw_llm_io(
            request=request,
            settings=self._settings,
            started_at=started_at,
            started_at_wall=started_at_wall,
            chat_payload=chat_payload,
            request_headers=request_headers,
            response_status_code=response.status_code,
            response_body=response_json,
            response_text=None,
            parsed_result=result,
            trace_refs=(trace_ref,),
            evidence_refs=(evidence_ref,),
            error_type=None,
            error_message=None,
        )
        return LlmTransportResult(
            result=result,
            validation_status=ValidationStatus.VALID,
            confidence_level=_confidence_level(result),
            low_confidence_flags=_low_confidence_flags(result),
            trace_refs=(trace_ref,),
            evidence_refs=(evidence_ref,),
            metadata={
                "model_name": provider_model,
                "provider_model": provider_model,
                "prompt_version": _request_prompt_version(request),
                "provider_status": "called",
            },
        )

    def _dump_client_initialization_failed(
        self,
        request: LlmTransportRequest,
        exc: ImportError,
    ) -> None:
        started_at = perf_counter()
        started_at_wall = datetime.now(timezone.utc)
        _maybe_dump_local_raw_llm_io(
            request=request,
            settings=self._settings,
            started_at=started_at,
            started_at_wall=started_at_wall,
            chat_payload=_chat_completion_payload(self._settings, request),
            request_headers={
                "Authorization": f"Bearer {self._settings.api_key}",
                "Content-Type": "application/json",
            },
            response_status_code=None,
            response_body=None,
            response_text=None,
            parsed_result=None,
            trace_refs=(),
            evidence_refs=(),
            error_type="client_initialization_failed",
            error_message=_client_initialization_error_message(exc),
        )

    def _log_request_start(self, request: LlmTransportRequest) -> None:
        """记录 LLM 请求启动日志（含 task_type / model / contract_ids 等关键字段）。"""
        LogUtil.llm_transport_request_start(
            task_type=request.task_type,
            model=self._settings.model,
            provider_base_host=_base_url_host(self._settings.base_url),
            contract_ids=request.contract_ids,
            input_ref_count=len(request.input_refs),
            timeout_seconds=_request_timeout_seconds(self._settings, request),
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
        LogUtil.llm_transport_request_success(
            task_type=request.task_type,
            model=self._settings.model,
            provider_model=provider_model,
            status_code=status_code,
            duration_ms=_duration_ms(started_at),
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
        LogUtil.llm_transport_request_failed(
            task_type=request.task_type,
            model=self._settings.model,
            error_type=error_type,
            duration_ms=_duration_ms(started_at),
            status_code=status_code,
        )


def _chat_completion_payload(
    settings: OpenAICompatibleLlmSettings,
    request: LlmTransportRequest,
) -> dict[str, Any]:
    """构造 OpenAI Chat Completions 请求体，含 system prompt 和 evidence bundle。"""
    # Structured JSON tasks must wait for complete content before json.loads;
    # frontend streaming needs SSE/task state.
    return {
        "model": settings.model,
        "temperature": settings.temperature,
        "max_tokens": _max_tokens_for_request(settings, request),
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
                        "input_refs": list(request.input_refs),
                        "evidence_bundle": request.evidence_bundle,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            },
        ],
    }


def _max_tokens_for_request(
    settings: OpenAICompatibleLlmSettings,
    request: LlmTransportRequest,
) -> int:
    if request.task_type == PROGRESS_TREE_QUALITY_FIRST_TASK_TYPE:
        return settings.progress_tree_max_tokens
    return settings.max_tokens


def _request_timeout_seconds(
    settings: OpenAICompatibleLlmSettings,
    request: LlmTransportRequest,
) -> float | None:
    if request.task_type in NO_REQUEST_TIMEOUT_TASK_TYPES:
        return None
    return settings.timeout_seconds


def _duration_ms(started_at: float) -> float:
    """计算从 started_at 到当前时间的毫秒数。"""
    return round((perf_counter() - started_at) * 1000, 3)


def _base_url_host(base_url: str) -> str:
    """从 base_url 中提取主机名（用于日志脱敏）。"""
    parsed = urlparse(base_url)
    return parsed.netloc or parsed.path or "unknown"


def _local_raw_io_enabled(environ: Mapping[str, str] | None = None) -> bool:
    return EnvReader(environ).bool(LOCAL_LLM_RAW_IO_ENABLED_ENV, False)


def _local_raw_io_dir(environ: Mapping[str, str] | None = None) -> Path:
    return Path(EnvReader(environ).str(LOCAL_LLM_RAW_IO_DIR_ENV, DEFAULT_LOCAL_LLM_RAW_IO_DIR))


def _maybe_dump_local_raw_llm_io(
    *,
    request: LlmTransportRequest,
    settings: OpenAICompatibleLlmSettings,
    started_at: float,
    started_at_wall: datetime,
    chat_payload: dict[str, Any],
    request_headers: Mapping[str, str],
    response_status_code: int | None,
    response_body: Any,
    response_text: str | None,
    parsed_result: dict[str, Any] | None,
    trace_refs: tuple[str, ...],
    evidence_refs: tuple[str, ...],
    error_type: str | None,
    error_message: str | None,
) -> None:
    """把 raw LLM I/O 直接写入本地 JSON 文件；写入失败不得影响主流程。"""
    if not _local_raw_io_enabled():
        return

    try:
        dump_dir = _local_raw_io_dir()
        dump_dir.mkdir(parents=True, exist_ok=True)
        completed_at_wall = datetime.now(timezone.utc)
        trace_context = get_request_trace_context()
        request_id = trace_context.request_id if trace_context else None
        trace_id = trace_context.trace_id if trace_context else None
        response: dict[str, Any] = {
            "status_code": response_status_code,
            "body": response_body,
        }
        if response_body is None and response_text is not None:
            response["text"] = response_text

        dump_request: dict[str, Any] = {"chat_completion_payload": chat_payload}
        safe_headers = _local_raw_io_headers(request_headers)
        if safe_headers:
            dump_request["headers"] = safe_headers

        dump_payload = {
            "schema_version": "local_llm_raw_io.v1",
            "request_id": request_id,
            "trace_id": trace_id,
            "task_type": request.task_type,
            "contract_ids": list(request.contract_ids),
            "input_refs": list(request.input_refs),
            "graph_name": request.graph_name,
            "node_name": request.node_name,
            "schema_id": request.schema_id,
            "prompt_version": request.prompt_version or _request_prompt_version(request),
            "model": settings.model,
            "base_url": settings.base_url,
            "provider_base_host": _base_url_host(settings.base_url),
            "timeout_seconds": _request_timeout_seconds(settings, request),
            "trust_env": settings.trust_env,
            "temperature": settings.temperature,
            "started_at": _format_raw_io_timestamp(started_at_wall),
            "completed_at": _format_raw_io_timestamp(completed_at_wall),
            "duration_ms": _duration_ms(started_at),
            "request": dump_request,
            "response": response,
            "parsed_result": parsed_result,
            "trace_refs": list(trace_refs),
            "evidence_refs": list(evidence_refs),
            "error": (
                None
                if error_type is None
                else {
                    "type": error_type,
                    "message": error_message or "",
                }
            ),
        }
        dump_path = dump_dir / _local_raw_io_file_name(
            completed_at_wall=completed_at_wall,
            task_type=request.task_type,
            request_id=request_id,
            trace_id=trace_id,
            trace_refs=trace_refs,
            chat_payload=chat_payload,
            response_status_code=response_status_code,
            error_type=error_type,
        )
        dump_path.write_text(
            json.dumps(dump_payload, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
    except Exception:
        return


def _response_body_for_dump(response: httpx.Response) -> tuple[Any, str | None]:
    """返回 provider 响应用于 raw dump；JSON 可解析时保留 JSON，否则保留文本。"""
    try:
        return response.json(), None
    except ValueError:
        return None, response.text


def _local_raw_io_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """只在显式要求时输出非敏感请求头。"""
    if not _local_raw_io_include_headers():
        return {}
    safe_headers: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in {"content-type", "accept"}:
            safe_headers[key] = value
    return safe_headers


def _local_raw_io_include_headers(environ: Mapping[str, str] | None = None) -> bool:
    return EnvReader(environ).bool(LOCAL_LLM_RAW_IO_INCLUDE_HEADERS_ENV, False)


def _local_raw_io_file_name(
    *,
    completed_at_wall: datetime,
    task_type: str,
    request_id: str | None,
    trace_id: str | None,
    trace_refs: tuple[str, ...],
    chat_payload: dict[str, Any],
    response_status_code: int | None,
    error_type: str | None,
) -> str:
    digest = _local_raw_io_digest(
        chat_payload=chat_payload,
        response_status_code=response_status_code,
        error_type=error_type,
    )
    locator = trace_id or request_id or (trace_refs[0] if trace_refs else None)
    if locator:
        locator_slug = f"{_filename_component(locator)}-{digest[:8]}"
    else:
        locator_slug = f"no-trace-{digest[:8]}"
    timestamp = completed_at_wall.strftime("%Y%m%d-%H%M%S-%f")
    return f"{timestamp}-{_filename_component(task_type)}-{locator_slug}.json"


def _local_raw_io_digest(
    *,
    chat_payload: dict[str, Any],
    response_status_code: int | None,
    error_type: str | None,
) -> str:
    seed = json.dumps(
        {
            "chat_payload": chat_payload,
            "error_type": error_type,
            "response_status_code": response_status_code,
        },
        ensure_ascii=True,
        sort_keys=True,
    )
    return sha256(seed.encode("utf-8")).hexdigest()


def _filename_component(value: str) -> str:
    cleaned = "".join(
        char if char.isascii() and (char.isalnum() or char in {"-", "_", "."}) else "_"
        for char in value
    ).strip("._-")
    return cleaned[:96] or "unknown"


def _format_raw_io_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


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
    if task_type == PROGRESS_TREE_QUALITY_FIRST_TASK_TYPE:
        return "\n".join(
            [
                "你是 AiForInterviewer 的 Progress Tree 结构化 JSON 任务执行器。",
                "必须使用中文输出，不要返回英文说明。",
                "只返回合法 JSON，不要 Markdown 包裹。",
                COMPACT_JSON_REASONING_CONSTRAINT,
                "不要输出思考过程、分析过程、推理过程或额外说明。",
                "必须严格遵守 user message 中 evidence_bundle.prompt、output_schema、schema_id 和 prompt_version。",
                "不得暴露 provider payload、secret、token 或原始 completion。",
            ]
        )
    return "\n".join(
        [
            "你是 AiForInterviewer 的结构化 JSON 任务执行器。",
            "必须使用中文输出，不要返回英文说明。",
            "只返回合法 JSON，不要 Markdown 包裹。",
            COMPACT_JSON_REASONING_CONSTRAINT,
            "不要输出思考过程、分析过程、推理过程或额外说明。",
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
    if first_choice.get("finish_reason") == "length":
        raise _llm_response_error(
            "LLM provider 输出被截断，JSON 不完整。",
            error_type=PROVIDER_OUTPUT_TRUNCATED_ERROR_TYPE,
        )
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


def _llm_response_error(message: str, *, error_type: str) -> LlmTransportResponseError:
    error = LlmTransportResponseError(message)
    setattr(error, "error_type", error_type)
    return error


def _llm_response_error_type(exc: LlmTransportResponseError) -> str:
    error_type = getattr(exc, "error_type", None)
    if isinstance(error_type, str) and error_type.strip():
        return error_type.strip()
    return "provider_response_error"


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


def _normalize_base_url(raw: str) -> str:
    """标准化 base_url：去除首尾空白和尾部斜杠，为空时返回默认值。"""
    return raw.strip().rstrip("/") or DEFAULT_OPENAI_BASE_URL


def _client_initialization_error_message(exc: ImportError) -> str:
    message = str(exc)
    if "socksio" in message.lower():
        return "HTTP client initialization failed because SOCKS proxy support is unavailable."
    return "HTTP client initialization failed before provider request was sent."
