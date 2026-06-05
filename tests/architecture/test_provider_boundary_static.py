from __future__ import annotations

from app.application.ai_runtime.contracts import contains_sensitive_payload, sanitize_payload
from app.application.llm.provider_boundary import P7_PROVIDER_FORBIDDEN_KEYS


P7_PROVIDER_FORBIDDEN_KEY_CATALOG = (
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
)


def test_provider_boundary_gate_catalog_contains_required_p7_keys() -> None:
    assert set(P7_PROVIDER_FORBIDDEN_KEY_CATALOG) == {
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
    assert P7_PROVIDER_FORBIDDEN_KEYS == frozenset(P7_PROVIDER_FORBIDDEN_KEY_CATALOG)


def test_ai_runtime_provider_boundary_rejects_required_p7_forbidden_keys() -> None:
    for key in P7_PROVIDER_FORBIDDEN_KEY_CATALOG:
        _assert_ai_runtime_provider_boundary_rejects_forbidden_key(key)


def _assert_ai_runtime_provider_boundary_rejects_forbidden_key(key: str) -> None:
    payload = {key: "sensitive-provider-value", "safe_ref": "candidate-ref-1"}

    assert contains_sensitive_payload(payload)
    assert sanitize_payload(payload) == {"safe_ref": "candidate-ref-1"}
