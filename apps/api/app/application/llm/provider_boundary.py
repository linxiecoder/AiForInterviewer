"""Compact provider request validation for application LLM calls."""

from __future__ import annotations

import re
from collections.abc import Collection, Mapping
from dataclasses import fields, is_dataclass
from typing import Any

from app.application.llm.types import LlmTransportRequest

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

_SENSITIVE_VALUE_PATTERN = re.compile(
    r"(?i)(?:\b(?:api[_-]?key|token|secret|cookie)\s*[:=]\s*[^\s,;]+|\bbearer\s+[^\s,;]+|\bsk-[a-z0-9._-]+)"
)


class ProviderRequestValidationError(ValueError):
    """Raised when a provider-facing request is unsafe or not compact."""

    def __init__(self, errors: Collection[str]) -> None:
        self.errors = tuple(dict.fromkeys(str(error) for error in errors if str(error).strip()))
        super().__init__(", ".join(self.errors) or "provider_request_validation_failed")


class ProviderRequestValidator:
    """Validate and sanitize compact provider-facing payloads before transport."""

    def __init__(
        self,
        *,
        required_top_level_keys: Collection[str] = (),
        allowed_top_level_keys: Collection[str] | None = None,
    ) -> None:
        self._required_top_level_keys = frozenset(str(key) for key in required_top_level_keys)
        self._allowed_top_level_keys = (
            frozenset(str(key) for key in allowed_top_level_keys) if allowed_top_level_keys is not None else None
        )

    def validate_evidence_bundle(self, payload: object) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            raise ProviderRequestValidationError(("provider_request_payload_not_mapping",))
        normalized = _to_plain_data(payload, path="$")
        if not isinstance(normalized, dict):
            raise ProviderRequestValidationError(("provider_request_payload_not_mapping",))

        errors: list[str] = []
        for key in sorted(self._required_top_level_keys):
            if key not in normalized:
                errors.append(f"missing_provider_request_key:{key}")
        if self._allowed_top_level_keys is not None:
            for key in normalized:
                if key not in self._allowed_top_level_keys:
                    errors.append(f"unexpected_provider_request_key:{key}")
        errors.extend(f"forbidden_provider_request_key:{path}" for path in _forbidden_key_paths(normalized))
        if errors:
            raise ProviderRequestValidationError(errors)
        return _redact_sensitive_values(normalized)


def build_validated_transport_request(
    *,
    contract_ids: tuple[str, ...],
    task_type: str,
    input_refs: tuple[str, ...],
    evidence_bundle: object,
    prompt_version: str | None = None,
    schema_id: str | None = None,
    required_evidence_keys: Collection[str] = (),
    allowed_evidence_keys: Collection[str] | None = None,
) -> LlmTransportRequest:
    validated_bundle = ProviderRequestValidator(
        required_top_level_keys=required_evidence_keys,
        allowed_top_level_keys=allowed_evidence_keys,
    ).validate_evidence_bundle(evidence_bundle)
    return LlmTransportRequest(
        contract_ids=contract_ids,
        task_type=task_type,
        input_refs=input_refs,
        evidence_bundle=validated_bundle,
        prompt_version=prompt_version,
        schema_id=schema_id,
    )


def is_forbidden_provider_key(key: object) -> bool:
    return _normalize_key(key) in P7_PROVIDER_FORBIDDEN_KEYS


def _forbidden_key_paths(value: object, *, path: str = "") -> tuple[str, ...]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            item_path = f"{path}.{key_text}" if path else key_text
            if is_forbidden_provider_key(key):
                paths.append(item_path)
            paths.extend(_forbidden_key_paths(item, path=item_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_forbidden_key_paths(item, path=f"{path}[{index}]"))
    return tuple(paths)


def _to_plain_data(value: object, *, path: str) -> object:
    if isinstance(value, Mapping):
        return {str(key): _to_plain_data(item, path=f"{path}.{key}") for key, item in value.items()}
    if isinstance(value, tuple):
        return [_to_plain_data(item, path=f"{path}[{index}]") for index, item in enumerate(value)]
    if isinstance(value, list):
        return [_to_plain_data(item, path=f"{path}[{index}]") for index, item in enumerate(value)]
    if isinstance(value, set):
        return [_to_plain_data(item, path=f"{path}[{index}]") for index, item in enumerate(value)]
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _to_plain_data(getattr(value, field.name), path=f"{path}.{field.name}") for field in fields(value)}
    if hasattr(value, "model_dump") and callable(value.model_dump):
        return _to_plain_data(value.model_dump(), path=path)
    if hasattr(value, "dict") and callable(value.dict):
        return _to_plain_data(value.dict(), path=path)
    return value


def _redact_sensitive_values(value: object) -> Any:
    if isinstance(value, dict):
        return {str(key): _redact_sensitive_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_sensitive_values(item) for item in value]
    if isinstance(value, str):
        return _SENSITIVE_VALUE_PATTERN.sub("[redacted]", value)
    return value


def _normalize_key(key: object) -> str:
    return str(key).strip().lower().replace("-", "_").replace(" ", "_")
