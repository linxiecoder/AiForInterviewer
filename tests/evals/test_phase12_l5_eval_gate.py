from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE12_L5_SUITE = REPO_ROOT / "tests" / "evals" / "phase12" / "suite.json"
REQUIRED_WINDOW_CATEGORIES = {
    "happy_path",
    "insufficient_context",
    "asset_conflict",
    "provider_failure",
    "validation_failure",
    "hitl",
    "replay",
    "cross_agent_handoff_failure",
}


def _runner_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = ".:apps/api"
    env.pop("LLM_PROVIDER", None)
    return env


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert all(isinstance(case, dict) for case in cases)
    return cases


def _phase12_l5_cases() -> list[dict[str, Any]]:
    manifest = _load_json(PHASE12_L5_SUITE)
    cases: list[dict[str, Any]] = []
    for dataset in manifest["datasets"]:
        cases.extend(_load_jsonl(REPO_ROOT / dataset["path"]))
    return cases


def test_phase12_l5_manifest_defines_blocking_eval_gate_and_quality_lanes() -> None:
    manifest = _load_json(PHASE12_L5_SUITE)

    assert manifest["suite_id"] == "phase12_l5"
    assert manifest["ci_blocking"] is True
    assert manifest["release_path_policy"]["eval_failure_blocks_l5_release_path"] is True
    assert manifest["release_path_policy"]["passing_deterministic_gate_is_not_l5_release"] is True
    assert manifest["quality_lanes"]["deterministic_regression"]["ci_blocking"] is True
    assert manifest["quality_lanes"]["replay_regression"]["ci_blocking"] is True
    assert manifest["quality_lanes"]["provider_quality"]["uses_live_provider"] is True
    assert manifest["quality_lanes"]["provider_quality"]["not_claimed_by_default"] is True
    assert set(manifest["minimum_pass_criteria"]["required_case_categories"]) == REQUIRED_WINDOW_CATEGORIES
    assert set(manifest["capability_ids"]) >= {"L5-006", "EVAL-001", "L5-002", "L5-003", "L5-004", "L5-005"}


def test_phase12_l5_datasets_cover_window_required_scenarios_and_case_metadata() -> None:
    cases = _phase12_l5_cases()
    categories = {case["case_category"] for case in cases}

    assert REQUIRED_WINDOW_CATEGORIES <= categories
    for case in cases:
        assert case["capability_ids"], case["case_id"]
        assert case["dataset_refs"], case["case_id"]
        assert case["grader_refs"], case["case_id"]
        assert case["expected_trace_refs"], case["case_id"]
        assert case["pass_criteria"], case["case_id"]
        assert case["fail_criteria"], case["case_id"]
        assert case["triage"]["owner"], case["case_id"]
        assert case["triage"]["category"], case["case_id"]
        assert "no_real_provider_quality_certification" in case["non_claims"], case["case_id"]


def test_phase12_l5_runner_passes_blocking_gate_without_provider_dependency() -> None:
    env = _runner_env()
    env["LLM_PROVIDER"] = "fake"
    env.pop("OPENAI_API_KEY", None)

    result = subprocess.run(
        [sys.executable, "scripts/evals/run_l5_eval_suite.py", "--mode", "deterministic"],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["suite_id"] == "phase12_l5"
    assert report["summary"]["blocking_failures"] == 0
    assert set(report["summary"]["case_categories_covered"]) >= REQUIRED_WINDOW_CATEGORIES
    assert report["release_path_policy"]["eval_failure_blocks_l5_release_path"] is True
    assert report["ci"]["default_requires_live_provider_credentials"] is False
    assert report["ci"]["mode_is_ci_safe"] is True
    assert "no_real_provider_quality_certification" in report["non_claims"]


def test_phase12_l5_runner_writes_json_and_markdown_reports(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/evals/run_l5_eval_suite.py",
            "--mode",
            "deterministic",
            "--report-dir",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        env=_runner_env(),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "phase12_l5_eval_report.json").exists()
    markdown = (tmp_path / "P12_L5_EVAL_REPORT.md").read_text(encoding="utf-8")
    assert "P12 L5 Eval Gate Report" in markdown
    assert "Real-provider quality certification remains a separate lane." in markdown


def test_phase12_l5_negative_control_proves_runner_can_block_release_path() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/evals/run_l5_eval_suite.py",
            "--mode",
            "deterministic",
            "--expect-fail-fixture",
        ],
        cwd=REPO_ROOT,
        env=_runner_env(),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["negative_control_result"]["checked"] is True
    assert report["negative_control_result"]["observed_expected_failure"] is True


def test_eval_gate_workflow_runs_phase12_l5_gate() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "eval-gate.yml").read_text(encoding="utf-8")

    assert "Run Phase 12 L5 eval gate" in workflow
    assert "python scripts/evals/run_l5_eval_suite.py --mode deterministic" in workflow
    assert "Run Phase 12 L5 negative-control gate" in workflow
