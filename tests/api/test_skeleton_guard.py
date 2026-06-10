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
    "bootstrap skeleton",
    "bootstrap returns skeleton",
    "prefix only",
    "repository pass",
    "repository `pass`",
    "is `pass`",
    "route prefix only",
    "empty schema",
    "schema only",
    "schema-only",
    "disabled nav",
    "disabled `/review` nav",
    "disabled navigation declared as implemented",
    "TODO implement",
    "placeholder",
)
PREFIX_ONLY_CAPABILITIES = {"Pressure", "Reviews", "Reports", "Scoring", "ai-tasks"}
REPOSITORY_PASS_CAPABILITIES = {"Scoring", "ai-tasks"}
FORBIDDEN_STATUS_WORDS = ("基本完成", "差不多", "已接入", "待联调", "后续完善")
FORBIDDEN_AMBIGUOUS_STATUS_WORDS = (
    "done",
    "future-only",
    "blocked-by-missing-runtime",
)
REQUIRED_BASELINE_GUARDRAILS = (
    "route prefix 存在不等于能力实现",
    "DB model 存在不等于产品流程实现",
    "disabled frontend nav 不等于页面存在",
    "fake/replay/deterministic eval 不等于 real-provider quality",
)
REQUIRED_EVAL_RUNTIME_NON_CLAIM_FRAGMENTS = (
    "deterministic / replay / fixture / fake-provider / mock-transport / default-off graph evidence only regression/contract",
    "provider quality: missing",
    "live-provider verified: missing",
    "not implemented AI Runtime product capability",
    "no live-provider quality, no production quality, no real provider quality, no live LLM quality, no end-to-end provider quality",
)
REQUIRED_POLISH_AGGREGATE_GUARD_FRAGMENTS = (
    "API handler evidence = implemented",
    "aggregate remains partial until full API + UseCase + Repository/Model + Tests + frontend/user path + runtime quality evidence are independently proven",
    "use cases = partial unless full evidence exists",
    "tests = partial",
    "frontend user path = partial",
    "feedback generation, asset candidate boundary and weakness evidence boundary remain partial",
    "runtime graph = partial/default-off/non-product",
    "eval evidence = partial/deterministic-replay-fake-mock only",
    "route handler presence does not imply aggregate Polish implemented",
    "default-off graph != product runtime",
    "fallback path != live-provider quality",
    "deterministic/replay/fixture/fake-provider/mock-provider/default-off evidence != live-provider quality",
    "no Agent Runtime productization",
)
POLISH_PARTIAL_CAPABILITIES = (
    "Polish aggregate capability",
    "Polish question",
    "Polish feedback",
    "Polish progress tree",
    "Polish report",
    "Polish candidates",
    "Frontend interview workbench",
)
FORBIDDEN_RUNTIME_QUALITY_CLAIMS = (
    "live-provider verified",
    "live-provider quality",
    "production quality",
    "real provider quality",
    "live LLM quality",
    "end-to-end provider quality",
    "implemented AI Runtime product capability",
)
SAFE_RUNTIME_QUALITY_NON_CLAIM_MARKERS = (
    "no ",
    "not ",
    "missing",
    "not proven",
    "缺",
    "未证明",
    "does not prove",
    "do not certify",
    "!=",
    "不能",
    "不把",
)
REQUIRED_TRAINING_CORRECTION_FRAGMENTS = (
    "Training independent product mode = missing / intentionally excluded from MVP",
    "Training legacy endpoints = partial legacy preserve-only",
    "Weakness remediation target = Polish or Pressure/Mock, not Training",
    "Absence of full weakness-to-training loop is not an MVP gap",
    "Absence of full training loop is not an MVP gap",
    "No /training frontend route is required for MVP",
)
TRAINING_EXCLUSION_TERMS = (
    "full weakness-to-training loop",
    "full training loop",
    "Weakness -> Training",
    "Training -> Weakness resolved",
    "complete training " + "resolves weakness",
    "complete training == weakness resolved",
    "Training" + " Center",
    "Training" + " V1",
    "Training" + "Plan",
    "Training" + "Drill",
    "Training" + "Task",
)
SAFE_TRAINING_EXCLUSION_MARKERS = (
    "no ",
    "not ",
    "forbidden",
    "excluded",
    "intentionally excluded",
    "not allowed",
    "not required",
    "not a gap",
    "preserve-only",
    "out of mvp",
    "不得",
    "禁止",
)
GUARDED_NON_IMPLEMENTED_STATUS_EXPECTATIONS = {
    "Pressure": "skeleton",
    "Reviews": "skeleton",
    "Reports": "skeleton",
    "Scoring": "skeleton",
    "ai-tasks": "skeleton",
    "Training legacy endpoints, if present": "partial",
    "Training independent product mode": "missing",
    "Weakness -> Polish re-entry": "设计-only",
    "Weakness -> Pressure/Mock re-entry": "设计-only",
}
REQUIRED_MVP_WEAKNESS_REENTRY_CAPABILITIES = {
    "Weakness -> Polish re-entry",
    "Weakness -> Pressure/Mock re-entry",
}


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


def test_guarded_non_product_capabilities_keep_exact_non_implemented_status() -> None:
    rows_by_capability = {row["capability"]: row for row in _matrix_rows()}

    for capability, expected_status in GUARDED_NON_IMPLEMENTED_STATUS_EXPECTATIONS.items():
        assert capability in rows_by_capability
        assert rows_by_capability[capability]["current_status"] == expected_status


def test_prefix_only_capabilities_are_never_declared_implemented() -> None:
    rows_by_capability = {row["capability"]: row for row in _matrix_rows()}

    for capability in PREFIX_ONLY_CAPABILITIES:
        row = rows_by_capability[capability]
        assert row["current_status"] == "skeleton"
        assert "prefix only" in row["backend_api"]


def test_repository_pass_capabilities_are_never_declared_implemented() -> None:
    rows_by_capability = {row["capability"]: row for row in _matrix_rows()}

    for capability in REPOSITORY_PASS_CAPABILITIES:
        row = rows_by_capability[capability]
        assert row["current_status"] == "skeleton"
        assert "`pass`" in row["repository_or_db_model"]


def test_disabled_review_nav_is_not_page_existence_evidence() -> None:
    rows_by_capability = {row["capability"]: row for row in _matrix_rows()}
    reviews = rows_by_capability["Reviews"]

    assert reviews["current_status"] == "skeleton"
    assert "disabled `/review` nav" in reviews["frontend_path"]
    assert "no active route" in reviews["frontend_path"]


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
    for forbidden in FORBIDDEN_AMBIGUOUS_STATUS_WORDS:
        assert forbidden not in combined
    for capability in SKELETON_CAPABILITIES:
        assert capability in baseline


def test_polish_aggregate_capability_remains_partial_until_full_evidence() -> None:
    rows_by_capability = {row["capability"]: row for row in _matrix_rows()}
    aggregate = rows_by_capability["Polish aggregate capability"]
    aggregate_text = " ".join(aggregate.values())

    assert aggregate["current_status"] == "partial"
    for capability in POLISH_PARTIAL_CAPABILITIES:
        assert rows_by_capability[capability]["current_status"] == "partial"
    for fragment in REQUIRED_POLISH_AGGREGATE_GUARD_FRAGMENTS:
        assert fragment in aggregate_text


def test_runtime_and_eval_positive_quality_claims_stay_non_claims() -> None:
    baseline = BASELINE_PATH.read_text(encoding="utf-8")
    matrix = MATRIX_PATH.read_text(encoding="utf-8")
    combined_lines = f"{baseline}\n{matrix}".splitlines()

    for claim in FORBIDDEN_RUNTIME_QUALITY_CLAIMS:
        _assert_term_only_appears_in_safe_context(
            combined_lines,
            claim,
            SAFE_RUNTIME_QUALITY_NON_CLAIM_MARKERS,
        )


def test_training_product_correction_language_is_preserved() -> None:
    baseline = BASELINE_PATH.read_text(encoding="utf-8")
    matrix = MATRIX_PATH.read_text(encoding="utf-8")
    combined = f"{baseline}\n{matrix}"

    for fragment in REQUIRED_TRAINING_CORRECTION_FRAGMENTS:
        assert fragment in combined

    rows_by_capability = {row["capability"]: row for row in _matrix_rows()}
    training_legacy = rows_by_capability["Training legacy endpoints, if present"]
    training_mode = rows_by_capability["Training independent product mode"]

    assert training_legacy["current_status"] == "partial"
    assert "preserve-only legacy behavior" in training_legacy["known_gap"]
    assert "current code fact only, not MVP product target" in training_legacy["last_verified_commit"]
    assert training_mode["current_status"] == "missing"
    assert "intentionally excluded from MVP, not a gap to close" in training_mode["known_gap"]
    assert "no /training route" in training_mode["refactor_guard"]
    assert "no complete training == weakness resolved" in training_mode["refactor_guard"]


def test_weakness_reentry_allows_only_polish_and_pressure_mock_in_mvp_matrix() -> None:
    rows_by_capability = {row["capability"]: row for row in _matrix_rows()}
    weakness_reentry_rows = {
        row["capability"]: row
        for row in _matrix_rows()
        if row["capability"].startswith("Weakness ->")
    }

    assert set(weakness_reentry_rows) == REQUIRED_MVP_WEAKNESS_REENTRY_CAPABILITIES
    assert "Weakness -> Training" not in rows_by_capability
    assert weakness_reentry_rows["Weakness -> Polish re-entry"]["current_status"] == "设计-only"
    assert weakness_reentry_rows["Weakness -> Pressure/Mock re-entry"]["current_status"] == "设计-only"

    weakness = rows_by_capability["Weaknesses"]
    assert "remediation target is Polish re-entry or Pressure/Mock re-entry" in weakness["known_gap"]
    assert "no Weakness -> Training" in weakness["refactor_guard"]


def test_eval_runtime_non_claim_language_is_preserved_in_matrix() -> None:
    rows_by_capability = {row["capability"]: row for row in _matrix_rows()}
    ai_runtime = rows_by_capability["AI Runtime"]
    evals = rows_by_capability["Tests/Evals/CI"]
    combined = " ".join(
        (
            ai_runtime["known_gap"],
            ai_runtime["refactor_guard"],
            evals["known_gap"],
            evals["refactor_guard"],
        )
    )

    assert ai_runtime["current_status"] == "partial"
    assert evals["current_status"] == "partial"
    for fragment in REQUIRED_EVAL_RUNTIME_NON_CLAIM_FRAGMENTS:
        assert fragment in combined


def test_ai_tasks_product_runtime_stays_skeleton_in_matrix() -> None:
    rows_by_capability = {row["capability"]: row for row in _matrix_rows()}
    ai_tasks = rows_by_capability["ai-tasks"]

    assert ai_tasks["current_status"] == "skeleton"
    assert "prefix only" in ai_tasks["backend_api"]
    assert "ai_task_skeleton" in ai_tasks["application_use_case"]
    assert "`pass`" in ai_tasks["repository_or_db_model"]
    assert "no AiTask status/result/retry/cancel API flow" in ai_tasks["known_gap"]
    assert "route prefix 存在不等于能力实现" in ai_tasks["refactor_guard"]


def test_training_exclusion_terms_only_appear_in_safe_context() -> None:
    baseline = BASELINE_PATH.read_text(encoding="utf-8")
    matrix = MATRIX_PATH.read_text(encoding="utf-8")
    combined_lines = f"{baseline}\n{matrix}".splitlines()

    for term in TRAINING_EXCLUSION_TERMS:
        _assert_term_only_appears_in_safe_context(
            combined_lines,
            term,
            SAFE_TRAINING_EXCLUSION_MARKERS,
        )


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


def _assert_term_only_appears_in_safe_context(
    lines: list[str],
    term: str,
    safe_markers: tuple[str, ...],
) -> None:
    normalized_term = term.lower()
    matches = [
        (index, line)
        for index, line in enumerate(lines)
        if normalized_term in line.lower()
    ]

    for index, line in matches:
        context = " ".join(lines[max(0, index - 2) : index + 3]).lower()
        assert any(marker.lower() in context for marker in safe_markers), (
            term,
            line,
        )
