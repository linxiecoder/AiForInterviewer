from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from evals.graders.code_rules import grade_case, grade_dataset, load_jsonl


REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE9_NON_PROVIDER_QUALITY_NON_CLAIMS = {
    "replay_mode_is_not_real_provider_quality_evidence",
    "fake_visible_eval_is_not_production_provider_quality_evidence",
    "phase9_is_l5_foundation_regression_evidence_only_not_l5_release",
}


def _runner_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join((".", "apps/api"))
    env.pop("LLM_PROVIDER", None)
    return env


def test_phase9_manifest_binds_capabilities_to_datasets_and_grader_refs() -> None:
    manifest = json.loads((REPO_ROOT / "evals" / "suites" / "phase9.json").read_text(encoding="utf-8"))

    assert manifest["suite_id"] == "phase9"
    assert manifest["ci_blocking"] is True
    assert manifest["minimum_pass_criteria"]["blocking_failures"] == 0
    assert {dataset["dataset_id"] for dataset in manifest["datasets"]} == {
        "canonical_evidence",
        "question_agent",
        "feedback_agent",
        "provider_boundary",
        "fake_gate",
        "handoff_trace",
        "runtime_foundation_contract",
    }
    assert all(dataset["capability_ids"] for dataset in manifest["datasets"])
    assert all(dataset["grader_version"] == "code_rules.v2" for dataset in manifest["datasets"])


def test_phase9_replay_fixture_and_fake_gate_are_not_live_provider_quality_claims() -> None:
    manifest = json.loads((REPO_ROOT / "evals" / "suites" / "phase9.json").read_text(encoding="utf-8"))
    runner_source = (REPO_ROOT / "scripts" / "evals" / "run_eval_gate.py").read_text(encoding="utf-8")
    dataset_ids = {dataset["dataset_id"] for dataset in manifest["datasets"]}

    assert manifest["mode"] == "replay"
    assert PHASE9_NON_PROVIDER_QUALITY_NON_CLAIMS <= set(manifest["non_claims"])
    assert "SUPPORTED_MODES = {\"replay\", \"fixture\"}" in runner_source
    assert {"fake_gate", "runtime_foundation_contract"} <= dataset_ids
    assert all(dataset["blocking"] is True for dataset in manifest["datasets"])


def test_phase9_builtin_datasets_pass_code_rules() -> None:
    manifest = json.loads((REPO_ROOT / "evals" / "suites" / "phase9.json").read_text(encoding="utf-8"))

    for dataset in manifest["datasets"]:
        summary = grade_dataset(REPO_ROOT / dataset["path"])
        assert summary["failed"] == 0, dataset["dataset_id"]
        assert summary["total"] > 0


def test_phase9_forbidden_key_scanner_normalizes_extended_sensitive_keys() -> None:
    result = grade_case(
        {
            "case_id": "normalized_forbidden_key",
            "task_type": "provider_boundary",
            "input": {"raw-provider-payload": {"id": "raw-provider-response"}},
            "expected": {"provider_request_status": "validation_failed", "fail_closed": True, "reason_codes": ["x"]},
            "must_have": [],
            "must_not_have": [],
            "grader_notes": "Hyphenated forbidden key names must be caught.",
        }
    )

    assert result["passed"] is False
    assert "forbidden_key:input.raw-provider-payload" in result["failures"]


def test_phase9_eval_gate_writes_json_and_markdown_reports(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/evals/run_eval_gate.py",
            "--suite",
            "phase9",
            "--mode",
            "replay",
            "--report-dir",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        env=_runner_env(),
        stdin=subprocess.DEVNULL,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["suite_id"] == "phase9"
    assert report["summary"]["blocking_failures"] == 0
    assert report["summary"]["deferred"] >= 1
    assert (tmp_path / "phase9_eval_report.json").exists()
    markdown = (tmp_path / "P9_EVAL_REPORT.md").read_text(encoding="utf-8")
    assert "P9 Eval Gate Report" in markdown
    assert "replay_mode_is_not_real_provider_quality_evidence" in markdown


def test_phase9_eval_gate_reports_to_docs_dir_without_docs_json(tmp_path: Path) -> None:
    docs_report_dir = tmp_path / "docs" / "goals" / "2026-06-06"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/evals/run_eval_gate.py",
            "--suite",
            "phase9",
            "--mode",
            "replay",
            "--report-dir",
            str(docs_report_dir),
        ],
        cwd=REPO_ROOT,
        env=_runner_env(),
        stdin=subprocess.DEVNULL,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (docs_report_dir / "P9_EVAL_REPORT.md").exists()
    assert (docs_report_dir / "phase9_eval_report.json").exists()


def test_phase9_negative_control_proves_blocking_failure() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/evals/run_eval_gate.py",
            "--suite",
            "phase9",
            "--mode",
            "replay",
            "--expect-fail-fixture",
        ],
        cwd=REPO_ROOT,
        env=_runner_env(),
        stdin=subprocess.DEVNULL,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["negative_control_result"]["checked"] is True
    assert report["negative_control_result"]["observed_expected_failure"] is True


def test_phase9_negative_control_dataset_fails_when_run_as_blocking_case() -> None:
    cases = load_jsonl(REPO_ROOT / "evals" / "datasets" / "phase9" / "negative_control.jsonl")

    result = grade_case(cases[0])

    assert result["passed"] is False
    assert any("must_not_have_present" in failure for failure in result["failures"])


def test_phase9_gate_default_mode_does_not_require_live_provider_credentials() -> None:
    env = _runner_env()
    env["LLM_PROVIDER"] = "fake"
    env.pop("OPENAI_API_KEY", None)

    result = subprocess.run(
        [sys.executable, "scripts/evals/run_eval_gate.py", "--suite", "phase9", "--mode", "replay"],
        cwd=REPO_ROOT,
        env=env,
        stdin=subprocess.DEVNULL,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["ci"]["default_requires_live_provider_credentials"] is False
    assert report["ci"]["mode_is_ci_safe"] is True
