"""Capability and non-claim guards for the active de-layered docs."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_INDEX_PATH = REPO_ROOT / "docs/00-governance/DOCS_INDEX.md"
SKILL_MODEL_PATH = REPO_ROOT / "docs/02-design/SKILL_MODEL_SPEC.md"
F5_NOTES_PATH = REPO_ROOT / "docs/03-implementation/F5_BACKEND_IMPLEMENTATION_NOTES.md"

REMOVED_STANDALONE_CAPABILITY_DOCS = (
    REPO_ROOT / "docs/03-delivery/refactor/BASELINE_30f7237_CAPABILITY_MAP.md",
    REPO_ROOT / "docs/03-delivery/refactor/CAPABILITY_PRESERVATION_MATRIX.md",
)

REQUIRED_DOCS_INDEX_FRAGMENTS = (
    "docs/03-implementation/",
    "F5_BACKEND_IMPLEMENTATION_NOTES.md",
    "不再承载已去层的 capability、spec 或 planning standalone 容器",
)

REQUIRED_STATUS_GUARD_FRAGMENTS = (
    "`partial`、`skeleton`、`设计-only`、`missing`、`default-off`、`validated_with_deferred_gaps`",
    "不得被改写为 `implemented`",
    "route prefix、DB model、disabled frontend nav、fallback",
    "deterministic/replay/fake/mock eval",
    "default-off graph",
    "不能单独证明产品能力已实现",
)

REQUIRED_CAPABILITY_BOUNDARY_FRAGMENTS = (
    "Polish module split",
    "仅代表 conservative UseCase / Repository facade / frontend component extraction slice",
    "aggregate Polish 仍是 `partial`",
    "G-003 只做 evaluation / feedback",
    "G-004 只做 transcript understanding",
    "Composition Layer 只做 envelope-level routing / packaging",
)

REQUIRED_TRAINING_AND_WEAKNESS_FRAGMENTS = (
    "Training independent product mode 仍是 intentionally excluded from MVP",
    "Weakness remediation target 仍是 Polish 或 Pressure/Mock，不是 Training",
    "不承诺真实招聘结果校准、精确通过概率、自动能力评级或全自动训练闭环",
)

REQUIRED_RUNTIME_NON_CLAIM_FRAGMENTS = (
    "No production L5 release is claimed.",
    "No real-provider production quality certification is claimed.",
    "No remote CI hard claim is made without visible passing GitHub Actions artifact evidence.",
    "P8 Runtime remains `validated_with_deferred_gaps` / partial foundation",
    "fake / replay evidence 只算 regression evidence",
)


def test_active_capability_docs_exist_and_standalone_refactor_docs_are_removed() -> None:
    assert DOCS_INDEX_PATH.exists()
    assert SKILL_MODEL_PATH.exists()
    assert F5_NOTES_PATH.exists()

    for path in REMOVED_STANDALONE_CAPABILITY_DOCS:
        assert not path.exists(), path


def test_docs_index_records_current_capability_de_layer_boundary() -> None:
    docs_index = DOCS_INDEX_PATH.read_text(encoding="utf-8")

    for fragment in REQUIRED_DOCS_INDEX_FRAGMENTS:
        assert fragment in docs_index


def test_capability_status_non_claim_language_is_preserved_in_active_docs() -> None:
    combined = _active_capability_docs_text()

    for fragment in REQUIRED_STATUS_GUARD_FRAGMENTS:
        assert fragment in combined


def test_implemented_capability_boundaries_stay_scoped() -> None:
    combined = _active_capability_docs_text()

    for fragment in REQUIRED_CAPABILITY_BOUNDARY_FRAGMENTS:
        assert fragment in combined


def test_training_and_weakness_non_claims_are_preserved() -> None:
    skill_model = SKILL_MODEL_PATH.read_text(encoding="utf-8")

    for fragment in REQUIRED_TRAINING_AND_WEAKNESS_FRAGMENTS:
        assert fragment in skill_model


def test_runtime_and_provider_quality_non_claims_are_preserved() -> None:
    f5_notes = F5_NOTES_PATH.read_text(encoding="utf-8")

    for fragment in REQUIRED_RUNTIME_NON_CLAIM_FRAGMENTS:
        assert fragment in f5_notes


def test_reports_retrieval_v1_remains_polish_summary_only_code_slice() -> None:
    route_source = (REPO_ROOT / "apps/api/app/api/v1/reports.py").read_text(encoding="utf-8")
    use_case_source = (REPO_ROOT / "apps/api/app/application/reports/use_cases.py").read_text(
        encoding="utf-8"
    )

    assert '@router.get("/{report_id}")' in route_source
    assert "@router.post" not in route_source
    assert "report_skeleton" in use_case_source
    assert 'report.report_type != "polish_summary"' in use_case_source
    assert "Only polish_summary reports can be retrieved in this slice." in use_case_source
    assert (REPO_ROOT / "tests/api/test_reports_api.py").exists()


def _active_capability_docs_text() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            SKILL_MODEL_PATH,
            F5_NOTES_PATH,
        )
    )
