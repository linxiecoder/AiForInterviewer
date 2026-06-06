from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE12_SUITE = REPO_ROOT / "evals" / "suites" / "phase12.json"
PHASE12_DATASET_DIR = REPO_ROOT / "evals" / "datasets" / "phase12"
PHASE12_GRADER_CONTRACT = REPO_ROOT / "evals" / "graders" / "phase12_contract.json"
PHASE12_REPORT_SCHEMA = REPO_ROOT / "evals" / "schemas" / "phase12_release_report_schema.json"

REQUIRED_CASE_FIELDS = {
    "case_id",
    "capability_ids",
    "evidence_type",
    "input_refs",
    "expected_candidate_refs",
    "expected_handoff_refs",
    "expected_validation_refs",
    "expected_trace_refs",
    "expected_hitl_refs",
    "expected_failure_mode",
    "expected_non_claims",
    "grader_refs",
    "minimum_assertions",
    "forbidden_data",
    "owner_phase",
    "deferred_if_not_executable",
}

REQUIRED_CASE_CATEGORIES = {
    "happy_path_candidate_product_slice",
    "insufficient_context",
    "asset_conflict",
    "formal_write_requested",
    "low_confidence",
    "provider_failure",
    "validation_failure",
    "cross_agent_handoff_failure",
    "replay_mismatch",
    "forbidden_data",
    "fake_replay_non_claim",
    "release_non_claim",
}

REQUIRED_NON_CLAIMS = {
    "no_l5_release",
    "no_real_provider_quality_certification",
    "no_remote_ci_success",
    "no_phase12_release_gate_complete",
    "no_eval_runner_implementation",
    "no_release_report_generation",
}

FORBIDDEN_PAYLOAD_KEYS = {
    "raw_prompt",
    "raw_completion",
    "provider_payload",
    "raw_provider_payload",
    "full_resume",
    "full_jd",
    "full_answer",
    "full_asset_body",
    "api_key",
    "token",
    "secret",
    "cookie",
}

PROTECTED_PHASE9_AND_REPORT_PATHS = {
    "evals/suites/phase9.json",
    "evals/graders/code_rules.py",
    "evals/reports/P9_EVAL_REPORT.md",
    "evals/reports/phase9_eval_report.json",
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        payload = json.loads(raw_line)
        assert isinstance(payload, dict), f"{path}:{line_number}: case must be a JSON object"
        cases.append(payload)
    return cases


def _phase12_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in sorted(PHASE12_DATASET_DIR.glob("*.jsonl")):
        cases.extend(_load_jsonl(path))
    return cases


def _walk_dict_keys(value: Any, prefix: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            paths.append(path)
            paths.extend(_walk_dict_keys(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_walk_dict_keys(item, f"{prefix}[{index}]"))
    return paths


def _git_changed_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line[3:] for line in result.stdout.splitlines() if line.strip()]


def test_phase12_suite_manifest_is_contract_only_not_release_gate_complete() -> None:
    manifest = _load_json(PHASE12_SUITE)

    assert manifest["suite_id"] == "phase12"
    assert manifest["lifecycle_status"] == "contract_only"
    assert manifest["evidence_type"] == "contract_only_not_executable_release_gate"
    assert manifest["default_mode"] == "static_contract_review_no_live_provider"
    assert manifest["ci_gate_status"] in {"not_bound", "deferred"}
    assert manifest["provider_evidence_policy"]["live_provider_usage"] == "forbidden_in_p12_w1"
    assert manifest["provider_evidence_policy"]["real_provider_quality_certification"] == "not_claimed"
    assert "L5-006" in manifest["capability_ids"]
    assert "p12_w1_does_not_complete_phase12_release_gate" in manifest["non_claims"]
    assert manifest["minimum_pass_criteria"]["eval_runner_required"] is False
    assert manifest["minimum_pass_criteria"]["release_gate_pass_required"] is False


def test_phase12_dataset_jsonl_files_are_valid_and_manifest_bound() -> None:
    manifest = _load_json(PHASE12_SUITE)
    dataset_paths = {REPO_ROOT / dataset["path"] for dataset in manifest["dataset_refs"]}

    assert dataset_paths == set(PHASE12_DATASET_DIR.glob("*.jsonl"))
    for path in dataset_paths:
        cases = _load_jsonl(path)
        assert cases, path
        assert all(case["deferred_if_not_executable"] is True for case in cases)


def test_phase12_required_case_categories_exist() -> None:
    categories = {case.get("case_category") for case in _phase12_cases()}

    assert REQUIRED_CASE_CATEGORIES <= categories


def test_phase12_every_case_has_required_fields_and_non_claims() -> None:
    for case in _phase12_cases():
        assert REQUIRED_CASE_FIELDS <= set(case), case["case_id"]
        assert set(case["expected_non_claims"]) >= REQUIRED_NON_CLAIMS, case["case_id"]
        assert case["owner_phase"] == "Phase 12"
        assert case["evidence_type"] == "contract_only_case_skeleton"
        assert case["grader_refs"], case["case_id"]
        assert case["minimum_assertions"], case["case_id"]


def test_phase12_contract_artifacts_do_not_use_forbidden_payload_keys() -> None:
    artifacts: list[Any] = [
        _load_json(PHASE12_SUITE),
        _load_json(PHASE12_GRADER_CONTRACT),
        _load_json(PHASE12_REPORT_SCHEMA),
        *_phase12_cases(),
    ]
    offending_paths: list[str] = []

    for artifact in artifacts:
        for path in _walk_dict_keys(artifact):
            key = path.rsplit(".", 1)[-1]
            if key in FORBIDDEN_PAYLOAD_KEYS:
                offending_paths.append(path)

    assert offending_paths == []


def test_phase12_grader_contract_is_non_executable_contract_only() -> None:
    contract = _load_json(PHASE12_GRADER_CONTRACT)

    assert contract["grader_contract_id"] == "phase12_contract"
    assert contract["lifecycle_status"] == "contract_only"
    assert contract["evidence_type"] == "data_contract_only_not_python_grader"
    assert set(contract["required_case_fields"]) == REQUIRED_CASE_FIELDS
    assert "runner_or_ci_behavior_change_detected" in contract["blocking_assertion_types"]
    assert contract["deferred_implementation"]["python_grader"] == "not_created_in_p12_w1"
    assert contract["deferred_implementation"]["runner_integration"] == "not_created_in_p12_w1"


def test_phase12_release_report_schema_requires_release_decision_rollback_and_artifacts() -> None:
    schema = _load_json(PHASE12_REPORT_SCHEMA)
    top_level = set(schema["required_top_level_fields"])
    release_decision = set(schema["required_release_decision_fields"])
    artifacts = set(schema["required_artifact_fields"])

    assert schema["schema_id"] == "phase12_release_report_schema"
    assert schema["lifecycle_status"] == "contract_only"
    assert "release_decision" in top_level
    assert "accepted_risks" in top_level
    assert "rollback_policy_ref" in top_level
    assert "artifact_refs" in top_level
    assert "trace_report_refs" in top_level
    assert "rollback_policy_ref" in release_decision
    assert "remote_ci_artifact_ref" in artifacts
    assert schema["closure_criteria"]["p12_w1_satisfies_closure"] is False
    assert schema["deferred_implementation"]["report_file"] == "not_created_in_p12_w1"


def test_phase12_window_does_not_modify_reports_or_phase9_assets() -> None:
    changed_paths = _git_changed_paths()
    protected_hits = [
        path
        for path in changed_paths
        if path in PROTECTED_PHASE9_AND_REPORT_PATHS
        or path.startswith("evals/datasets/phase9/")
        or path.startswith("evals/reports/")
    ]

    assert protected_hits == []
