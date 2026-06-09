"""Phase 0 guards for skeleton-vs-implemented capability claims."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = REPO_ROOT / "docs/03-delivery/refactor/BASELINE_30f7237_CAPABILITY_MAP.md"
MATRIX_PATH = REPO_ROOT / "docs/03-delivery/refactor/CAPABILITY_PRESERVATION_MATRIX.md"

ALLOWED_STATUSES = {"implemented", "partial", "skeleton", "设计-only", "missing", "unknown"}
SKELETON_CAPABILITIES = {"Pressure", "Reviews", "Reports", "Scoring", "ai-tasks"}
IMPLEMENTED_FORBIDDEN_MARKERS = (
    "_skeleton",
    " skeleton",
    "bootstrap returns skeleton",
    "repository pass",
    "route prefix only",
    "disabled navigation declared as implemented",
    "TODO implement",
    "placeholder",
)
FORBIDDEN_STATUS_WORDS = ("基本完成", "差不多", "已接入", "待联调", "后续完善")
REQUIRED_BASELINE_GUARDRAILS = (
    "route prefix 存在不等于能力实现",
    "DB model 存在不等于产品流程实现",
    "disabled frontend nav 不等于页面存在",
    "fake/replay/deterministic eval 不等于 real-provider quality",
)


def test_phase0_baseline_and_matrix_documents_exist() -> None:
    assert BASELINE_PATH.exists()
    assert MATRIX_PATH.exists()


def test_capability_matrix_uses_only_allowed_statuses() -> None:
    rows = _matrix_rows()

    assert rows
    for row in rows:
        assert row["current_status"] in ALLOWED_STATUSES, row


def test_skeleton_capabilities_are_never_declared_implemented() -> None:
    rows_by_capability = {row["capability"]: row for row in _matrix_rows()}

    for capability in SKELETON_CAPABILITIES:
        assert capability in rows_by_capability
        assert rows_by_capability[capability]["current_status"] == "skeleton"


def test_declared_implemented_capabilities_do_not_use_skeleton_evidence() -> None:
    for row in _matrix_rows():
        if row["current_status"] != "implemented":
            continue
        row_text = " ".join(row.values()).lower()
        assert not [marker for marker in IMPLEMENTED_FORBIDDEN_MARKERS if marker.lower() in row_text], row


def test_baseline_guardrails_and_status_language_are_preserved() -> None:
    baseline = BASELINE_PATH.read_text(encoding="utf-8")
    matrix = MATRIX_PATH.read_text(encoding="utf-8")
    combined = f"{baseline}\n{matrix}"

    for guardrail in REQUIRED_BASELINE_GUARDRAILS:
        assert guardrail in baseline
    for forbidden in FORBIDDEN_STATUS_WORDS:
        assert forbidden not in combined
    for capability in SKELETON_CAPABILITIES:
        assert capability in baseline


def _matrix_rows() -> list[dict[str, str]]:
    text = MATRIX_PATH.read_text(encoding="utf-8")
    table_lines = [
        line
        for line in text.splitlines()
        if line.startswith("|") and not set(line.replace("|", "").strip()) <= {"-", ":"}
    ]
    assert table_lines, "Capability matrix table is missing"

    headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    assert "capability" in headers
    assert "current_status" in headers

    rows: list[dict[str, str]] = []
    for line in table_lines[1:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        rows.append(dict(zip(headers, cells)))
    return rows
