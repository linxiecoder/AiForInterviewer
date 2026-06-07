"""Application-level LLM transport DTOs."""

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any

from app.domain.shared.enums import ConfidenceLevel, ValidationStatus


P7_PROVIDER_FORBIDDEN_KEYS = frozenset(
    {
        "raw_prompt",
        "system_prompt",
        "developer_prompt",
        "raw_completion",
        "provider_payload",
        "raw_provider_payload",
        "full_resume",
        "full_jd",
        "full_answer",
        "full_asset_body",
        "token",
        "secret",
        "cookie",
        "api_key",
    }
)


class LlmTransportRequestValidationError(ValueError):
    def __init__(self, errors: tuple[str, ...]) -> None:
        self.errors = errors
        super().__init__(", ".join(errors))


@dataclass(frozen=True)
class LlmTransportRequest:
    """一次 LLM 调用的最小输入包，避免把无关上下文送入模型。"""

    contract_ids: tuple[str, ...]
    task_type: str
    input_refs: tuple[str, ...] = field(default_factory=tuple)
    evidence_bundle: dict[str, Any] = field(default_factory=dict)
    graph_name: str | None = None
    node_name: str | None = None
    prompt_version: str | None = None
    schema_id: str | None = None

    def __post_init__(self) -> None:
        errors = tuple(
            f"forbidden_provider_request_key:{path}"
            for path in _forbidden_provider_key_paths(self.evidence_bundle)
        )
        if errors:
            raise LlmTransportRequestValidationError(errors)


@dataclass(frozen=True)
class LlmTransportResult:
    """LLM 结构化输出包，只承载校验后的业务 JSON 和可追踪引用。"""

    result: dict[str, Any]
    validation_status: ValidationStatus
    confidence_level: ConfidenceLevel
    low_confidence_flags: tuple[str, ...]
    trace_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


def _forbidden_provider_key_paths(value: object, *, path: str = "$") -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _forbidden_provider_key_paths(asdict(value), path=path)
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()  # type: ignore[attr-defined]
        return _forbidden_provider_key_paths(dumped, path=path)
    if isinstance(value, Mapping):
        paths: list[str] = []
        for key, nested in value.items():
            key_text = str(key)
            nested_path = f"{path}.{key_text}"
            if _normalize_provider_key(key_text) in P7_PROVIDER_FORBIDDEN_KEYS:
                paths.append(nested_path)
            paths.extend(_forbidden_provider_key_paths(nested, path=nested_path))
        return tuple(paths)
    if isinstance(value, (list, tuple, set)):
        paths: list[str] = []
        for index, item in enumerate(value):
            paths.extend(_forbidden_provider_key_paths(item, path=f"{path}[{index}]"))
        return tuple(paths)
    return ()


def _normalize_provider_key(value: str) -> str:
    return value.strip().lower()
