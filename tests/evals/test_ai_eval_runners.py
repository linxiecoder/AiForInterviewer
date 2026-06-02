from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _runner_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = ".:apps/api"
    env.pop("LLM_PROVIDER", None)
    return env


def test_run_question_eval_default_dataset_exits_zero() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "evals.runners.run_question_eval"],
        cwd=REPO_ROOT,
        env=_runner_env(),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    summary = json.loads(result.stdout)
    assert summary["dataset"].endswith("question_generation.jsonl")
    assert summary["failed"] == 0
    assert summary["total"] >= 3


def test_run_feedback_eval_default_datasets_exits_zero() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "evals.runners.run_feedback_eval"],
        cwd=REPO_ROOT,
        env=_runner_env(),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    summary = json.loads(result.stdout)
    assert summary["runner"] == "feedback"
    assert summary["failed"] == 0
    assert summary["total"] >= 5
    assert len(summary["datasets"]) == 3


def test_runner_report_writes_json_summary(tmp_path: Path) -> None:
    report_path = tmp_path / "question_eval_report.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "evals.runners.run_question_eval",
            "--report",
            str(report_path),
        ],
        cwd=REPO_ROOT,
        env=_runner_env(),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["failed"] == 0
    assert report["total"] >= 3


def test_runner_returns_one_for_valid_failing_dataset(tmp_path: Path) -> None:
    dataset = tmp_path / "failing_asset_candidate.jsonl"
    dataset.write_text(
        json.dumps(
            {
                "case_id": "candidate_without_confirmation",
                "task_type": "asset_candidate",
                "input": {},
                "expected": {
                    "project_asset_update_candidates": [
                        {"candidate_id": "asset_candidate_missing_confirmation"}
                    ]
                },
                "must_have": [],
                "must_not_have": [],
                "grader_notes": "Valid JSONL, but domain rules should fail.",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "-m", "evals.runners.run_feedback_eval", "--dataset", str(dataset)],
        cwd=REPO_ROOT,
        env=_runner_env(),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    summary = json.loads(result.stdout)
    assert summary["failed"] == 1


def test_runner_returns_two_for_invalid_jsonl(tmp_path: Path) -> None:
    dataset = tmp_path / "invalid.jsonl"
    dataset.write_text("{not-json}\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "evals.runners.run_question_eval", "--dataset", str(dataset)],
        cwd=REPO_ROOT,
        env=_runner_env(),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "invalid JSONL" in result.stderr


def test_feedback_runner_accepts_multiple_dataset_args() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "evals.runners.run_feedback_eval",
            "--dataset",
            "evals/datasets/feedback_answer_change.jsonl",
            "--dataset",
            "evals/datasets/asset_candidate.jsonl",
        ],
        cwd=REPO_ROOT,
        env=_runner_env(),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    summary = json.loads(result.stdout)
    assert summary["total_datasets"] == 2
    assert summary["failed"] == 0


def test_default_runner_does_not_write_eval_reports_directory() -> None:
    before = sorted(path.name for path in (REPO_ROOT / "evals" / "reports").iterdir())

    result = subprocess.run(
        [sys.executable, "-m", "evals.runners.run_question_eval"],
        cwd=REPO_ROOT,
        env=_runner_env(),
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    after = sorted(path.name for path in (REPO_ROOT / "evals" / "reports").iterdir())
    assert after == before == [".gitkeep"]


def test_runners_do_not_depend_on_llm_provider_or_fake_runtime() -> None:
    env = _runner_env()
    env["LLM_PROVIDER"] = "fake"

    result = subprocess.run(
        [sys.executable, "-m", "evals.runners.run_feedback_eval"],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "LLM_PROVIDER" not in result.stderr
    assert "FakeLlmTransport" not in result.stdout

    runner_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (REPO_ROOT / "evals" / "runners").glob("run_*_eval.py")
    )
    assert "app.infrastructure.llm" not in runner_sources
    assert "tests.fakes" not in runner_sources
