from __future__ import annotations

import sys
from pathlib import Path

import pytest

API_SRC = Path(__file__).resolve().parents[2] / "apps" / "api"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from app.api.v1.polish import (
    REDACTED_SENSITIVE_FEEDBACK_DETAIL,
    _redact_forbidden_feedback_payload_response_text,
)
from app.application.polish.feedback_validation import _contains_unsafe_marker
from app.infrastructure.db.repositories.polish_candidates import _safe_candidate_text


@pytest.mark.parametrize(
    "text",
    (
        "token bucket rate limiting keeps burst control explicit",
        "JWT token rotation is discussed as an authentication concept",
        "secret management policy is part of platform operations",
    ),
)
def test_sensitive_marker_rules_allow_ordinary_technical_terms(text: str) -> None:
    assert _contains_unsafe_marker(text) is False
    assert _redact_forbidden_feedback_payload_response_text(text) == text
    assert _safe_candidate_text(text) == text


@pytest.mark.parametrize(
    "text",
    (
        "api_key=sk-test-secret must never leave the boundary",
        "Authorization: Bearer abc.def.ghi must never leave the boundary",
        "cookie=session-secret must never leave the boundary",
        "developer_prompt must never be exposed",
        "raw_prompt raw_completion and provider_payload must never be exposed",
        "hidden scoring rules must never be shown to the user",
    ),
)
def test_sensitive_marker_rules_fail_closed_for_leakage_values(text: str) -> None:
    assert _contains_unsafe_marker(text) is True
    assert _redact_forbidden_feedback_payload_response_text(text) == REDACTED_SENSITIVE_FEEDBACK_DETAIL
    assert _safe_candidate_text(text) == REDACTED_SENSITIVE_FEEDBACK_DETAIL


def test_sensitive_marker_rules_fail_closed_for_nested_raw_payload_keys() -> None:
    assert _contains_unsafe_marker({"safe": {"provider_payload": {"id": "raw-provider-response"}}}) is True
