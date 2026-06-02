from __future__ import annotations

import pytest

from app.application.ai_runtime.contracts import contains_sensitive_payload, sanitize_payload


P1_W3_PROVIDER_FORBIDDEN_KEYS = (
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


def test_provider_boundary_gate_catalog_contains_required_p1_w3_keys() -> None:
    assert set(P1_W3_PROVIDER_FORBIDDEN_KEYS) == {
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


@pytest.mark.parametrize(
    "key",
    [
        "raw_prompt",
        "system_prompt",
        pytest.param(
            "developer_prompt",
            marks=pytest.mark.xfail(
                reason="P1-W3 known gap: ai_runtime sanitizer does not yet block developer_prompt",
                strict=True,
            ),
        ),
        "raw_completion",
        "provider_payload",
        "raw_provider_payload",
        "full_resume",
        "full_jd",
        "full_answer",
        pytest.param(
            "full_asset_body",
            marks=pytest.mark.xfail(
                reason="P1-W3 known gap: ai_runtime sanitizer does not yet block full_asset_body",
                strict=True,
            ),
        ),
        "token",
        "secret",
        "cookie",
        "api_key",
    ],
)
def test_ai_runtime_provider_boundary_rejects_required_p1_w3_forbidden_keys(key: str) -> None:
    payload = {key: "sensitive-provider-value", "safe_ref": "candidate-ref-1"}

    assert contains_sensitive_payload(payload)
    assert sanitize_payload(payload) == {"safe_ref": "candidate-ref-1"}
