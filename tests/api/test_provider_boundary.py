from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pytest

from app.application.llm.provider_boundary import (
    P7_PROVIDER_FORBIDDEN_KEYS,
    ProviderRequestValidationError,
    ProviderRequestValidator,
)


@dataclass(frozen=True)
class _NestedDataclass:
    safe_ref: str
    raw_provider_payload: dict[str, Any]


class _PydanticLikeModel:
    def model_dump(self) -> dict[str, Any]:
        return {"safe_ref": "model-ref", "full_asset_body": "must-not-leak"}


def test_provider_boundary_catalog_matches_phase7_required_keys() -> None:
    assert P7_PROVIDER_FORBIDDEN_KEYS == frozenset(
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


def test_provider_boundary_rejects_forbidden_keys_recursively_across_supported_containers() -> None:
    payload = {
        "task_type": "polish_feedback_generation",
        "schema_id": "feedback_schema_v1",
        "prompt_version": "feedback_prompt_v1",
        "nested": [
            {"developer_prompt": "must-not-leak"},
            (_NestedDataclass(safe_ref="dataclass-ref", raw_provider_payload={"value": "must-not-leak"}),),
            {_PydanticLikeModel()},
        ],
    }

    with pytest.raises(ProviderRequestValidationError) as exc_info:
        ProviderRequestValidator().validate_evidence_bundle(payload)

    message = str(exc_info.value)
    assert "nested[0].developer_prompt" in message
    assert "nested[1][0].raw_provider_payload" in message
    assert "nested[2][0].full_asset_body" in message


def test_provider_boundary_redacts_sensitive_string_values_before_provider_invocation() -> None:
    payload = {
        "task_type": "polish_question_generation",
        "schema_id": "question_schema_v1",
        "prompt_version": "question_prompt_v1",
        "safe_excerpt": "api_key=sk-test token=raw-token cookie=session-id secret=plain Bearer live-token",
    }

    validated = ProviderRequestValidator().validate_evidence_bundle(payload)

    serialized = json.dumps(validated, ensure_ascii=False, sort_keys=True)
    assert "sk-test" not in serialized
    assert "raw-token" not in serialized
    assert "session-id" not in serialized
    assert "plain" not in serialized
    assert "live-token" not in serialized
    assert "[redacted]" in serialized


def test_provider_boundary_enforces_required_and_allowed_top_level_schema_keys() -> None:
    validator = ProviderRequestValidator(
        required_top_level_keys=("task_type", "schema_id", "prompt_version"),
        allowed_top_level_keys=("task_type", "schema_id", "prompt_version", "safe_refs"),
    )
    payload = {
        "task_type": "polish_question_generation",
        "schema_id": "question_schema_v1",
        "safe_refs": ["progress-node-1"],
        "input_data": {"safe_ref": "unexpected-full-context"},
    }

    with pytest.raises(ProviderRequestValidationError) as exc_info:
        validator.validate_evidence_bundle(payload)

    message = str(exc_info.value)
    assert "missing_provider_request_key:prompt_version" in message
    assert "unexpected_provider_request_key:input_data" in message
