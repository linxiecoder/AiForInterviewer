from __future__ import annotations

import ast
from pathlib import Path

from app.application.ai_runtime.contracts import contains_sensitive_payload, sanitize_payload
from app.application.llm.provider_boundary import P7_PROVIDER_FORBIDDEN_KEYS


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "apps" / "api" / "app"
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


def test_production_llm_transport_requests_are_built_through_provider_boundary() -> None:
    allowed = {"application/llm/provider_boundary.py"}
    violations: list[str] = []

    for path in sorted(APP_ROOT.rglob("*.py")):
        relative_path = path.relative_to(APP_ROOT).as_posix()
        if relative_path in allowed:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _call_name(node.func) == "LlmTransportRequest":
                violations.append(f"{relative_path}:{node.lineno}")

    assert violations == []


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""
