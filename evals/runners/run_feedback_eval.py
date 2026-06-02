from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from evals.graders.code_rules import grade_dataset


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASETS = (
    REPO_ROOT / "evals" / "datasets" / "feedback_asset_consistency.jsonl",
    REPO_ROOT / "evals" / "datasets" / "feedback_answer_change.jsonl",
    REPO_ROOT / "evals" / "datasets" / "asset_candidate.jsonl",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic feedback evals.")
    parser.add_argument("--dataset", type=Path, action="append")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)

    dataset_paths = tuple(args.dataset) if args.dataset else DEFAULT_DATASETS
    try:
        summaries = [grade_dataset(path) for path in dataset_paths]
    except Exception as exc:
        error = {"runner": "feedback", "error": str(exc)}
        print(json.dumps(error, ensure_ascii=False), file=sys.stderr)
        return 2

    summary = _combine_summaries(summaries)
    _write_report(args.report, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["failed"] == 0 else 1


def _combine_summaries(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    total = sum(int(summary["total"]) for summary in summaries)
    failed = sum(int(summary["failed"]) for summary in summaries)
    passed = sum(int(summary["passed"]) for summary in summaries)
    return {
        "runner": "feedback",
        "total_datasets": len(summaries),
        "total": total,
        "passed": passed,
        "failed": failed,
        "score": 1 if total > 0 and failed == 0 else 0,
        "datasets": summaries,
    }


def _write_report(path: Path | None, summary: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
