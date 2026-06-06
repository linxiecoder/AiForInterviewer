#!/usr/bin/env python3
"""Run deterministic Phase 9 eval suites and write machine/docs reports."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evals.graders.code_rules import find_forbidden_data, grade_case, load_jsonl


RUNNER_VERSION = "phase9.eval_gate.v1"
REPORT_SCHEMA_VERSION = "phase9.eval_report.v1"
SUPPORTED_MODES = {"replay", "fixture"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic Phase 9 eval gate.")
    parser.add_argument("--suite", default="phase9", help="Suite ID registered under evals/suites/<suite>.json.")
    parser.add_argument("--mode", default="replay", help="Default CI-safe mode: replay or fixture.")
    parser.add_argument("--report-dir", type=Path, help="Report directory for the human report.")
    parser.add_argument(
        "--expect-fail-fixture",
        action="store_true",
        help="Pass only if the registered negative-control fixture creates a blocking failure.",
    )
    args = parser.parse_args(argv)

    if args.mode not in SUPPORTED_MODES:
        print(
            json.dumps(
                {"runner": RUNNER_VERSION, "error": f"unsupported mode: {args.mode}", "supported_modes": sorted(SUPPORTED_MODES)},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 3

    try:
        manifest = _load_manifest(args.suite)
        if args.expect_fail_fixture:
            report = _run_negative_control(manifest=manifest, mode=args.mode)
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 0 if report["negative_control_result"]["observed_expected_failure"] else 1

        report = _run_suite(manifest=manifest, mode=args.mode)
        markdown = _render_markdown_report(report)
        _scan_report_or_raise(report, markdown)
        if args.report_dir is not None:
            _write_reports(report=report, markdown=markdown, report_dir=args.report_dir)
    except Exception as exc:
        print(json.dumps({"runner": RUNNER_VERSION, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["summary"]["blocking_failures"] == 0 else 1


def _load_manifest(suite_id: str) -> dict[str, Any]:
    path = REPO_ROOT / "evals" / "suites" / f"{suite_id}.json"
    with path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    if manifest.get("suite_id") != suite_id:
        raise ValueError(f"{path}: suite_id mismatch")
    required_fields = {
        "manifest_version",
        "suite_id",
        "mode",
        "ci_blocking",
        "minimum_pass_criteria",
        "datasets",
        "negative_control_refs",
        "report_safety_scanners",
        "non_claims",
    }
    missing = sorted(field for field in required_fields if field not in manifest)
    if missing:
        raise ValueError(f"{path}: missing manifest fields: {', '.join(missing)}")
    scan = find_forbidden_data(manifest)
    if scan["forbidden_key_paths"] or scan["forbidden_value_paths"]:
        raise ValueError(f"{path}: manifest contains forbidden data paths: {scan}")
    return manifest


def _run_suite(*, manifest: dict[str, Any], mode: str) -> dict[str, Any]:
    started_at = _utc_now()
    dataset_results: list[dict[str, Any]] = []
    capability_results: dict[str, dict[str, Any]] = {}
    blocking_failures: list[dict[str, Any]] = []
    deferred_cases: list[dict[str, Any]] = []
    skipped_cases: list[dict[str, Any]] = []
    dataset_digests: dict[str, str] = {}
    grader_versions: set[str] = set()
    total_cases = 0
    passed = 0
    failed = 0

    for dataset_config in manifest["datasets"]:
        dataset_id = _require_text(dataset_config, "dataset_id")
        dataset_path = REPO_ROOT / _require_text(dataset_config, "path")
        capability_ids = list(dataset_config.get("capability_ids") or [])
        blocking_dataset = bool(dataset_config.get("blocking", True))
        grader_version = _require_text(dataset_config, "grader_version")
        grader_versions.add(grader_version)
        dataset_digests[dataset_id] = _sha256_digest(dataset_path)

        cases = []
        for case in load_jsonl(dataset_path):
            case_result = grade_case(case)
            case_blocking = bool(case.get("blocking", blocking_dataset))
            case_summary = {
                "case_id": case_result["case_id"],
                "task_type": case_result["task_type"],
                "passed": case_result["passed"],
                "failures": case_result["failures"],
                "warnings": case_result["warnings"],
                "checked_rules": case_result["checked_rules"],
                "blocking": case_blocking,
                "capability_ids": capability_ids,
            }
            cases.append(case_summary)
            total_cases += 1
            if case_result["passed"]:
                passed += 1
            else:
                failed += 1
                if case_blocking:
                    blocking_failures.append(
                        {
                            "dataset_id": dataset_id,
                            "case_id": case_result["case_id"],
                            "task_type": case_result["task_type"],
                            "failures": case_result["failures"],
                            "capability_ids": capability_ids,
                        }
                    )

            if _is_deferred_case(case):
                deferred_cases.append(
                    {
                        "dataset_id": dataset_id,
                        "case_id": case_result["case_id"],
                        "category": "deferred",
                        "reason": case.get("expected", {}).get("reason", "deferred_with_reason"),
                        "owner_phase": case.get("expected", {}).get("owner_phase", "UNKNOWN"),
                        "capability_ids": capability_ids,
                    }
                )

            for capability_id in capability_ids:
                capability = capability_results.setdefault(
                    capability_id,
                    {"capability_id": capability_id, "case_ids": [], "blocking_failures": [], "deferred_cases": []},
                )
                capability["case_ids"].append(case_result["case_id"])
                if not case_result["passed"] and case_blocking:
                    capability["blocking_failures"].append(case_result["case_id"])
                if _is_deferred_case(case):
                    capability["deferred_cases"].append(case_result["case_id"])

        dataset_results.append(
            {
                "dataset_id": dataset_id,
                "path": dataset_config["path"],
                "capability_ids": capability_ids,
                "grader": dataset_config.get("grader", "code_rules"),
                "grader_version": grader_version,
                "blocking": blocking_dataset,
                "total_cases": len(cases),
                "passed": sum(1 for case in cases if case["passed"]),
                "failed": sum(1 for case in cases if not case["passed"]),
                "cases": cases,
            }
        )

    capability_rows = []
    for capability in sorted(capability_results.values(), key=lambda item: item["capability_id"]):
        if capability["blocking_failures"]:
            status = "failed"
        elif capability["deferred_cases"] and not any(
            case_id not in capability["deferred_cases"] for case_id in capability["case_ids"]
        ):
            status = "deferred_with_reason"
        else:
            status = "passed"
        capability_rows.append({**capability, "status": status})

    finished_at = _utc_now()
    report = {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "suite_id": manifest["suite_id"],
        "manifest_version": manifest["manifest_version"],
        "mode": mode,
        "provider_evidence_type": mode,
        "generated_at_utc": finished_at,
        "started_at_utc": started_at,
        "finished_at_utc": finished_at,
        "commit_sha": _commit_sha(),
        "runner_version": RUNNER_VERSION,
        "grader_versions": sorted(grader_versions),
        "dataset_digests": dataset_digests,
        "summary": {
            "total_cases": total_cases,
            "passed": passed,
            "failed": failed,
            "skipped": len(skipped_cases),
            "deferred": len(deferred_cases),
            "blocking_failures": len(blocking_failures),
        },
        "capability_results": capability_rows,
        "dataset_results": dataset_results,
        "blocking_failures": blocking_failures,
        "skips": skipped_cases,
        "deferred_cases": deferred_cases,
        "negative_control_result": {
            "checked": False,
            "observed_expected_failure": None,
            "reason": "Run --expect-fail-fixture for negative-control proof.",
        },
        "non_claims": manifest["non_claims"],
        "security_scan": {
            "forbidden_report_keys_found": [],
            "forbidden_report_values_found": [],
            "raw_payload_stored": False,
        },
        "ci": {
            "default_requires_live_provider_credentials": False,
            "llm_provider_env_used": bool(os.environ.get("LLM_PROVIDER")),
            "mode_is_ci_safe": mode in {"replay", "fixture"},
        },
    }
    return report


def _run_negative_control(*, manifest: dict[str, Any], mode: str) -> dict[str, Any]:
    expected_failures: list[dict[str, Any]] = []
    for control in manifest.get("negative_control_refs", []):
        dataset_path = REPO_ROOT / _require_text(control, "path")
        expected = _require_text(control, "expected_failure_contains")
        for case in load_jsonl(dataset_path):
            result = grade_case(case)
            failures = result["failures"]
            observed = any(expected in failure for failure in failures)
            expected_failures.append(
                {
                    "dataset_id": control["dataset_id"],
                    "case_id": result["case_id"],
                    "expected_failure_contains": expected,
                    "observed_expected_failure": observed,
                    "failures": failures,
                }
            )

    observed_all = bool(expected_failures) and all(item["observed_expected_failure"] for item in expected_failures)
    return {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "suite_id": manifest["suite_id"],
        "mode": mode,
        "runner_version": RUNNER_VERSION,
        "generated_at_utc": _utc_now(),
        "negative_control_result": {
            "checked": True,
            "observed_expected_failure": observed_all,
            "cases": expected_failures,
        },
        "non_claims": manifest["non_claims"],
    }


def _render_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "---",
        "title: P9_EVAL_REPORT",
        "type: goal-evidence",
        "status: eval_gate_passed" if report["summary"]["blocking_failures"] == 0 else "status: eval_gate_failed",
        "permalink: ai-for-interviewer/docs/goals/2026-06-06/p9-eval-report",
        "---",
        "",
        "# P9 Eval Gate Report",
        "",
        "## Run Metadata",
        "",
        f"- Suite: `{report['suite_id']}`",
        f"- Mode: `{report['mode']}`",
        f"- Commit SHA: `{report['commit_sha']}`",
        f"- Runner version: `{report['runner_version']}`",
        f"- Grader versions: `{', '.join(report['grader_versions'])}`",
        f"- Generated at UTC: `{report['generated_at_utc']}`",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|---|---:|",
    ]
    for key, value in report["summary"].items():
        lines.append(f"| `{key}` | {value} |")

    lines.extend(
        [
            "",
            "## Dataset Digests",
            "",
            "| Dataset | Digest |",
            "|---|---|",
        ]
    )
    for dataset_id, digest in sorted(report["dataset_digests"].items()):
        lines.append(f"| `{dataset_id}` | `{digest}` |")

    lines.extend(["", "## Capability Coverage", "", "| Capability | Status | Cases | Blocking Failures |", "|---|---|---|---|"])
    for capability in report["capability_results"]:
        lines.append(
            "| `{capability_id}` | `{status}` | {cases} | {failures} |".format(
                capability_id=capability["capability_id"],
                status=capability["status"],
                cases=", ".join(f"`{case_id}`" for case_id in capability["case_ids"]),
                failures=", ".join(f"`{case_id}`" for case_id in capability["blocking_failures"]) or "-",
            )
        )

    lines.extend(["", "## Blocking Failures", ""])
    if report["blocking_failures"]:
        lines.extend(["| Dataset | Case | Failures |", "|---|---|---|"])
        for failure in report["blocking_failures"]:
            lines.append(
                f"| `{failure['dataset_id']}` | `{failure['case_id']}` | `{', '.join(failure['failures'])}` |"
            )
    else:
        lines.append("No blocking failures.")

    lines.extend(["", "## Deferred Cases", ""])
    if report["deferred_cases"]:
        lines.extend(["| Dataset | Case | Owner Phase | Reason |", "|---|---|---|---|"])
        for item in report["deferred_cases"]:
            lines.append(f"| `{item['dataset_id']}` | `{item['case_id']}` | `{item['owner_phase']}` | {item['reason']} |")
    else:
        lines.append("No deferred cases.")

    lines.extend(
        [
            "",
            "## Security Scan",
            "",
            "- JSON and Markdown reports were scanned before write.",
            "- Forbidden report key findings: none.",
            "- Forbidden report value findings: none.",
            "- Raw payload stored: false.",
            "",
            "## CI Gate",
            "",
            "- Default mode is replay / fixture and does not require live provider credentials.",
            f"- `LLM_PROVIDER` visible to this run: `{report['ci']['llm_provider_env_used']}`",
            "",
            "## Non-Claims",
            "",
        ]
    )
    for non_claim in report["non_claims"]:
        lines.append(f"- `{non_claim}`")
    return "\n".join(lines) + "\n"


def _scan_report_or_raise(report: dict[str, Any], markdown: str) -> None:
    report_scan = find_forbidden_data(report)
    markdown_scan = find_forbidden_data({"markdown_report": markdown})
    forbidden_key_paths = report_scan["forbidden_key_paths"] + markdown_scan["forbidden_key_paths"]
    forbidden_value_paths = report_scan["forbidden_value_paths"] + markdown_scan["forbidden_value_paths"]
    if forbidden_key_paths or forbidden_value_paths:
        raise ValueError(
            "report security scan failed: "
            f"forbidden_key_paths={forbidden_key_paths}, forbidden_value_paths={forbidden_value_paths}"
        )


def _write_reports(*, report: dict[str, Any], markdown: str, report_dir: Path) -> None:
    report_dir = (REPO_ROOT / report_dir).resolve() if not report_dir.is_absolute() else report_dir
    report_dir.mkdir(parents=True, exist_ok=True)

    markdown_path = report_dir / "P9_EVAL_REPORT.md"
    json_dir = REPO_ROOT / "evals" / "reports" if _is_docs_goals_path(report_dir) else report_dir
    json_dir.mkdir(parents=True, exist_ok=True)
    json_path = json_dir / "phase9_eval_report.json"

    markdown_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _is_docs_goals_path(path: Path) -> bool:
    try:
        path.relative_to(REPO_ROOT / "docs" / "goals")
    except ValueError:
        return False
    return True


def _is_deferred_case(case: dict[str, Any]) -> bool:
    expected = case.get("expected")
    return isinstance(expected, dict) and expected.get("status") == "deferred_with_reason"


def _sha256_digest(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def _commit_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return "UNKNOWN"
    return result.stdout.strip() or "UNKNOWN"


def _utc_now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _require_text(mapping: dict[str, Any], field: str) -> str:
    value = mapping.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"missing required text field: {field}")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
