"""Additive task-level contracts for LLM-backed application tasks."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field as dataclass_field
from typing import Any

from app.application.llm.types import P7_PROVIDER_FORBIDDEN_KEYS


AI_TASK_CONTRACT_FAILURE_CODES = frozenset(
    {
        "json_output_not_text_or_object",
        "json_payload_not_object",
        "json_decode_failed",
        "json_truncated",
        "required_field_missing",
        "business_rule_failed",
        "invalid_evidence_ref",
        "unsafe_replay_fixture",
        "trace_ref_invalid",
    }
)
SANITIZED_REPLAY_FIXTURE_SCHEMA_ID = "aifi.sanitized_ai_task_replay.v1"

_RAW_OUTPUT_MARKERS = (
    "raw prompt",
    "raw completion",
    "provider replay raw",
)


@dataclass(frozen=True)
class AiTaskContractFailure:
    code: str
    reason: str
    field: str = ""
    details: dict[str, Any] = dataclass_field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = {"code": self.code, "reason": self.reason}
        if self.field:
            payload["field"] = self.field
        if self.details:
            payload["details"] = dict(self.details)
        return payload


@dataclass(frozen=True)
class AiTaskContractValidationContext:
    allowed_evidence_refs: tuple[str, ...] = ()
    metadata: dict[str, Any] = dataclass_field(default_factory=dict)


@dataclass(frozen=True)
class AiTaskContractValidationResult:
    ok: bool
    payload: dict[str, Any] | None = None
    failures: tuple[AiTaskContractFailure, ...] = ()
    warnings: tuple[str, ...] = ()
    trace_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    @property
    def failure_codes(self) -> tuple[str, ...]:
        return tuple(failure.code for failure in self.failures)

    @property
    def failure_reasons(self) -> tuple[str, ...]:
        return tuple(failure.reason for failure in self.failures)


@dataclass(frozen=True)
class AiTaskTracePolicy:
    trace_refs_required: bool = False
    allowed_trace_ref_prefixes: tuple[str, ...] = ()

    def validate_trace_refs(self, trace_refs: object) -> tuple[AiTaskContractFailure, ...]:
        refs = _string_tuple(trace_refs)
        if self.trace_refs_required and not refs:
            return (
                AiTaskContractFailure(
                    code="trace_ref_invalid",
                    field="trace_refs",
                    reason="trace_refs_required",
                ),
            )
        failures: list[AiTaskContractFailure] = []
        for ref in refs:
            lowered = ref.lower()
            if any(marker in lowered for marker in _RAW_OUTPUT_MARKERS):
                failures.append(
                    AiTaskContractFailure(
                        code="trace_ref_invalid",
                        field="trace_refs",
                        reason="trace_ref_contains_raw_output_marker",
                        details={"trace_ref": ref},
                    )
                )
            if self.allowed_trace_ref_prefixes and not ref.startswith(self.allowed_trace_ref_prefixes):
                failures.append(
                    AiTaskContractFailure(
                        code="trace_ref_invalid",
                        field="trace_refs",
                        reason="trace_ref_prefix_not_allowed",
                        details={
                            "trace_ref": ref,
                            "allowed_prefixes": list(self.allowed_trace_ref_prefixes),
                        },
                    )
                )
        return tuple(failures)


@dataclass(frozen=True)
class SanitizedReplayFixturePolicy:
    fixture_schema_id: str = SANITIZED_REPLAY_FIXTURE_SCHEMA_ID
    forbidden_keys: tuple[str, ...] = tuple(sorted(P7_PROVIDER_FORBIDDEN_KEYS | {"provider_replay_raw"}))

    def validate_fixture(self, fixture: object, *, contract: "AiTaskContract") -> AiTaskContractValidationResult:
        if not isinstance(fixture, Mapping):
            return _failed("json_payload_not_object", "fixture", "replay_fixture_not_mapping")
        payload = _plain_mapping(fixture)
        failures: list[AiTaskContractFailure] = []
        if payload.get("fixture_schema_id") != self.fixture_schema_id:
            failures.append(
                AiTaskContractFailure(
                    code="business_rule_failed",
                    field="fixture_schema_id",
                    reason="fixture_schema_id_mismatch",
                    details={"expected": self.fixture_schema_id, "actual": payload.get("fixture_schema_id")},
                )
            )
        if payload.get("contract_id") != contract.contract_id:
            failures.append(
                AiTaskContractFailure(
                    code="business_rule_failed",
                    field="contract_id",
                    reason="fixture_contract_id_mismatch",
                    details={"expected": contract.contract_id, "actual": payload.get("contract_id")},
                )
            )
        if payload.get("task_type") != contract.task_type:
            failures.append(
                AiTaskContractFailure(
                    code="business_rule_failed",
                    field="task_type",
                    reason="fixture_task_type_mismatch",
                    details={"expected": contract.task_type, "actual": payload.get("task_type")},
                )
            )
        failures.extend(
            AiTaskContractFailure(
                code="unsafe_replay_fixture",
                field=path,
                reason="replay_fixture_contains_forbidden_key",
            )
            for path in _forbidden_key_paths(payload, forbidden_keys=self.forbidden_keys)
        )
        failures.extend(
            AiTaskContractFailure(
                code="unsafe_replay_fixture",
                field=path,
                reason="replay_fixture_contains_raw_marker",
            )
            for path in _raw_marker_value_paths(payload)
        )
        trace_failures = contract.trace_policy.validate_trace_refs(payload.get("trace_refs"))
        failures.extend(trace_failures)

        candidate = payload.get("candidate_payload")
        candidate_result = contract.validate_candidate_payload(
            candidate,
            allowed_evidence_refs=_string_tuple(payload.get("evidence_refs")),
        )
        failures.extend(candidate_result.failures)
        if failures:
            return AiTaskContractValidationResult(ok=False, failures=tuple(failures))
        return AiTaskContractValidationResult(
            ok=True,
            payload=payload,
            trace_refs=_string_tuple(payload.get("trace_refs")),
            evidence_refs=_string_tuple(payload.get("evidence_refs")),
        )


BusinessValidator = Callable[
    [dict[str, Any], AiTaskContractValidationContext],
    tuple[AiTaskContractFailure, ...],
]


@dataclass(frozen=True)
class AiTaskContract:
    contract_id: str
    task_type: str
    schema_id: str
    schema_version: str
    contract_ids: tuple[str, ...] = ()
    required_candidate_fields: tuple[str, ...] = ()
    required_final_fields: tuple[str, ...] = ()
    candidate_validator: BusinessValidator | None = None
    final_validator: BusinessValidator | None = None
    trace_policy: AiTaskTracePolicy = dataclass_field(default_factory=AiTaskTracePolicy)
    replay_fixture_policy: SanitizedReplayFixturePolicy = dataclass_field(default_factory=SanitizedReplayFixturePolicy)

    def parse_candidate_output(
        self,
        raw_output: object,
        *,
        allowed_evidence_refs: tuple[str, ...] = (),
    ) -> AiTaskContractValidationResult:
        payload, failures = _parse_json_object(raw_output)
        if failures:
            return AiTaskContractValidationResult(ok=False, failures=failures)
        return self.validate_candidate_payload(payload, allowed_evidence_refs=allowed_evidence_refs)

    def validate_candidate_payload(
        self,
        payload: object,
        *,
        allowed_evidence_refs: tuple[str, ...] = (),
    ) -> AiTaskContractValidationResult:
        return self._validate_payload(
            payload,
            required_fields=self.required_candidate_fields,
            validator=self.candidate_validator,
            allowed_evidence_refs=allowed_evidence_refs,
        )

    def validate_final_payload(
        self,
        payload: object,
        *,
        allowed_evidence_refs: tuple[str, ...] = (),
    ) -> AiTaskContractValidationResult:
        return self._validate_payload(
            payload,
            required_fields=self.required_final_fields,
            validator=self.final_validator,
            allowed_evidence_refs=allowed_evidence_refs,
        )

    def validate_replay_fixture(self, fixture: object) -> AiTaskContractValidationResult:
        return self.replay_fixture_policy.validate_fixture(fixture, contract=self)

    def _validate_payload(
        self,
        payload: object,
        *,
        required_fields: tuple[str, ...],
        validator: BusinessValidator | None,
        allowed_evidence_refs: tuple[str, ...],
    ) -> AiTaskContractValidationResult:
        if not isinstance(payload, Mapping):
            return _failed("json_payload_not_object", "payload", "task_payload_not_mapping")
        normalized = _plain_mapping(payload)
        failures: list[AiTaskContractFailure] = []
        failures.extend(_missing_required_field_failures(normalized, required_fields))
        failures.extend(_invalid_evidence_ref_failures(normalized, allowed_evidence_refs=allowed_evidence_refs))
        failures.extend(self.trace_policy.validate_trace_refs(normalized.get("trace_refs")))
        if validator is not None:
            failures.extend(
                validator(
                    normalized,
                    AiTaskContractValidationContext(
                        allowed_evidence_refs=allowed_evidence_refs,
                    ),
                )
            )
        if failures:
            return AiTaskContractValidationResult(ok=False, payload=normalized, failures=tuple(failures))
        return AiTaskContractValidationResult(
            ok=True,
            payload=normalized,
            trace_refs=_string_tuple(normalized.get("trace_refs")),
            evidence_refs=_string_tuple(normalized.get("evidence_refs")),
        )


def business_rule_failure(reason: str, *, field: str = "", details: dict[str, Any] | None = None) -> AiTaskContractFailure:
    return AiTaskContractFailure(
        code="business_rule_failed",
        field=field,
        reason=reason,
        details=dict(details or {}),
    )


def _parse_json_object(raw_output: object) -> tuple[dict[str, Any] | None, tuple[AiTaskContractFailure, ...]]:
    if isinstance(raw_output, Mapping):
        return _plain_mapping(raw_output), ()
    if not isinstance(raw_output, str):
        return None, (
            AiTaskContractFailure(
                code="json_output_not_text_or_object",
                field="raw_output",
                reason="raw_output_not_text_or_mapping",
            ),
        )
    try:
        decoded = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        reason = "json_truncated" if _looks_truncated_json(raw_output) else "json_decode_failed"
        return None, (
            AiTaskContractFailure(
                code=reason,
                field="raw_output",
                reason=reason,
                details={"message": exc.msg, "position": exc.pos},
            ),
        )
    if not isinstance(decoded, Mapping):
        return None, (
            AiTaskContractFailure(
                code="json_payload_not_object",
                field="raw_output",
                reason="decoded_json_not_object",
            ),
        )
    return _plain_mapping(decoded), ()


def _failed(code: str, field_name: str, reason: str) -> AiTaskContractValidationResult:
    return AiTaskContractValidationResult(
        ok=False,
        failures=(AiTaskContractFailure(code=code, field=field_name, reason=reason),),
    )


def _missing_required_field_failures(
    payload: dict[str, Any],
    required_fields: tuple[str, ...],
) -> tuple[AiTaskContractFailure, ...]:
    failures: list[AiTaskContractFailure] = []
    for field_name in required_fields:
        if field_name not in payload:
            failures.append(
                AiTaskContractFailure(
                    code="required_field_missing",
                    field=field_name,
                    reason=f"{field_name}_required",
                )
            )
    return tuple(failures)


def _invalid_evidence_ref_failures(
    payload: dict[str, Any],
    *,
    allowed_evidence_refs: tuple[str, ...],
) -> tuple[AiTaskContractFailure, ...]:
    if not allowed_evidence_refs:
        return ()
    allowed = set(allowed_evidence_refs)
    failures: list[AiTaskContractFailure] = []
    for ref in _string_tuple(payload.get("evidence_refs")):
        if ref not in allowed:
            failures.append(
                AiTaskContractFailure(
                    code="invalid_evidence_ref",
                    field="evidence_refs",
                    reason="evidence_ref_not_allowed",
                    details={"evidence_ref": ref, "allowed_evidence_refs": list(allowed_evidence_refs)},
                )
            )
    return tuple(failures)


def _forbidden_key_paths(value: object, *, forbidden_keys: tuple[str, ...], path: str = "$") -> tuple[str, ...]:
    forbidden = {_normalize_key(key) for key in forbidden_keys}
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            nested_path = f"{path}.{key_text}"
            if _normalize_key(key_text) in forbidden:
                paths.append(nested_path)
            paths.extend(_forbidden_key_paths(item, forbidden_keys=forbidden_keys, path=nested_path))
    elif isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            paths.extend(_forbidden_key_paths(item, forbidden_keys=forbidden_keys, path=f"{path}[{index}]"))
    return tuple(paths)


def _raw_marker_value_paths(value: object, *, path: str = "$") -> tuple[str, ...]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            paths.extend(_raw_marker_value_paths(item, path=f"{path}.{key}"))
    elif isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            paths.extend(_raw_marker_value_paths(item, path=f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in _RAW_OUTPUT_MARKERS):
            paths.append(path)
    return tuple(paths)


def _string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    values: list[object]
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        return ()
    result: list[str] = []
    for item in values:
        text = str(item).strip()
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _plain_mapping(value: Mapping[object, object]) -> dict[str, Any]:
    return {str(key): _plain_data(item) for key, item in value.items()}


def _plain_data(value: object) -> Any:
    if isinstance(value, Mapping):
        return _plain_mapping(value)
    if isinstance(value, tuple):
        return [_plain_data(item) for item in value]
    if isinstance(value, list):
        return [_plain_data(item) for item in value]
    if isinstance(value, set):
        return [_plain_data(item) for item in sorted(value, key=lambda item: str(item))]
    return value


def _looks_truncated_json(value: str) -> bool:
    stripped = value.strip()
    return bool(stripped) and stripped[0] in "[{" and stripped[-1:] not in "]}"


def _normalize_key(value: object) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")
