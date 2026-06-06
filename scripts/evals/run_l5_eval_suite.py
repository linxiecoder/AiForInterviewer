#!/usr/bin/env python3
"""Run the deterministic Phase 12 L5 multi-agent eval gate."""

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
DEFAULT_MANIFEST = REPO_ROOT / "tests" / "evals" / "phase12" / "suite.json"

RUNNER_VERSION = "phase12.l5_eval_gate.v1"
REPORT_SCHEMA_VERSION = "phase12.l5_eval_report.v1"
SUPPORTED_MODES = {"deterministic", "replay"}

REQUIRED_CASE_FIELDS = {
    "case_id",
    "case_category",
    "capability_ids",
    "dataset_refs",
    "grader_refs",
    "input_refs",
    "expected_candidate_refs",
    "expected_handoff_refs",
    "expected_validation_refs",
    "expected_trace_refs",
    "expected_hitl_refs",
    "expected_failure_mode",
    "pass_criteria",
    "fail_criteria",
    "triage",
    "provider_evidence_type",
    "non_claims",
    "blocking",
    "deferred_if_not_executable",
}

REQUIRED_NON_CLAIMS = {
    "no_l5_release",
    "no_real_provider_quality_certification",
    "no_remote_ci_success",
    "no_phase12_release_gate_complete",
}

REF_LIST_FIELDS = {
    "dataset_refs",
    "grader_refs",
    "input_refs",
    "expected_trace_refs",
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Phase 12 L5 deterministic eval gate.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="L5 eval suite manifest path.")
    parser.add_argument("--mode", default="deterministic", help="deterministic or replay.")
    parser.add_argument("--report-dir", type=Path, help="Directory for JSON and Markdown reports.")
    parser.add_argument(
        "--expect-fail-fixture",
        action="store_true",
        help="Pass only if the registered negative-control fixture produces its expected blocking failure.",
    )
    args = parser.parse_args(argv)

    if args.mode not in SUPPORTED_MODES:
        _print_error({"error": f"unsupported mode: {args.mode}", "supported_modes": sorted(SUPPORTED_MODES)})
        return 3

    try:
        manifest_path = _resolve_path(args.manifest)
        manifest = _load_manifest(manifest_path)
        if args.expect_fail_fixture:
            report = _run_negative_control(manifest=manifest, mode=args.mode)
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 0 if report["negative_control_result"]["observed_expected_failure"] else 1

        report = _run_suite(manifest=manifest, manifest_path=manifest_path, mode=args.mode)
        markdown = _render_markdown_report(report)
        _scan_report_or_raise(report, markdown)
        if args.report_dir is not None:
            _write_reports(report=report, markdown=markdown, report_dir=args.report_dir)
    except Exception as exc:
        _print_error({"error": str(exc)})
        return 2

    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["summary"]["blocking_failures"] == 0 else 1


def _load_manifest(path: Path) -> dict[str, Any]:
    manifest = _load_json(path)
    required = {
        "manifest_version",
        "suite_id",
        "ci_blocking",
        "minimum_pass_criteria",
        "datasets",
        "negative_control_refs",
        "quality_lanes",
        "release_path_policy",
        "non_claims",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise ValueError(f"{path}: missing manifest fields: {', '.join(missing)}")
    if manifest["suite_id"] != "phase12_l5":
        raise ValueError(f"{path}: suite_id must be phase12_l5")
    if manifest["ci_blocking"] is not True:
        raise ValueError(f"{path}: ci_blocking must be true")
    if manifest["release_path_policy"].get("eval_failure_blocks_l5_release_path") is not True:
        raise ValueError(f"{path}: eval failure must block L5 release path")
    _raise_forbidden_data(path.as_posix(), manifest)
    return manifest


def _run_suite(*, manifest: dict[str, Any], manifest_path: Path, mode: str) -> dict[str, Any]:
    started_at = _utc_now()
    dataset_results: list[dict[str, Any]] = []
    blocking_failures: list[dict[str, Any]] = []
    capability_results: dict[str, dict[str, Any]] = {}
    category_coverage: set[str] = set()
    dataset_digests: dict[str, str] = {manifest_path.relative_to(REPO_ROOT).as_posix(): _sha256_digest(manifest_path)}
    total_cases = 0
    passed = 0
    failed = 0
    deferred = 0

    for dataset_config in manifest["datasets"]:
        dataset_id = _require_text(dataset_config, "dataset_id")
        dataset_path = _resolve_path(REPO_ROOT / _require_text(dataset_config, "path"))
        dataset_digest_key = dataset_path.relative_to(REPO_ROOT).as_posix()
        dataset_digests[dataset_digest_key] = _sha256_digest(dataset_path)
        dataset_cases: list[dict[str, Any]] = []
        dataset_passed = 0
        dataset_failed = 0

        for case in _load_jsonl(dataset_path):
            case_result = _grade_case(case, dataset_path=dataset_path, dataset_config=dataset_config)
            dataset_cases.append(case_result)
            total_cases += 1
            category_coverage.add(str(case.get("case_category")))
            if case.get("deferred_if_not_executable") is True:
                deferred += 1
            if case_result["passed"]:
                passed += 1
                dataset_passed += 1
            else:
                failed += 1
                dataset_failed += 1
                if case_result["blocking"]:
                    blocking_failures.append(
                        {
                            "dataset_id": dataset_id,
                            "case_id": case_result["case_id"],
                            "case_category": case_result["case_category"],
                            "failures": case_result["failures"],
                            "triage": case_result["triage"],
                        }
                    )

            for capability_id in case_result["capability_ids"]:
                row = capability_results.setdefault(
                    capability_id,
                    {
                        "capability_id": capability_id,
                        "case_ids": [],
                        "blocking_failures": [],
                        "deferred_cases": [],
                        "non_claims": sorted(REQUIRED_NON_CLAIMS),
                    },
                )
                row["case_ids"].append(case_result["case_id"])
                if case_result["blocking"] and not case_result["passed"]:
                    row["blocking_failures"].append(case_result["case_id"])
                if case.get("deferred_if_not_executable") is True:
                    row["deferred_cases"].append(case_result["case_id"])

        dataset_results.append(
            {
                "dataset_id": dataset_id,
                "path": dataset_config["path"],
                "grader": dataset_config["grader"],
                "grader_version": dataset_config["grader_version"],
                "blocking": bool(dataset_config.get("blocking", True)),
                "total_cases": len(dataset_cases),
                "passed": dataset_passed,
                "failed": dataset_failed,
                "cases": dataset_cases,
            }
        )

    missing_categories = sorted(set(manifest["minimum_pass_criteria"]["required_case_categories"]) - category_coverage)
    for category in missing_categories:
        blocking_failures.append(
            {
                "dataset_id": "suite",
                "case_id": f"missing_required_category:{category}",
                "case_category": category,
                "failures": [f"missing_required_case_category:{category}"],
                "triage": {"owner": "qa_eval", "category": "suite_coverage"},
            }
        )
    failed += len(missing_categories)

    capability_rows = []
    for row in sorted(capability_results.values(), key=lambda item: item["capability_id"]):
        status = "failed" if row["blocking_failures"] else "passed"
        capability_rows.append({**row, "status": status})

    report = {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "suite_id": manifest["suite_id"],
        "manifest_version": manifest["manifest_version"],
        "mode": mode,
        "provider_evidence_type": mode,
        "generated_at_utc": _utc_now(),
        "started_at_utc": started_at,
        "finished_at_utc": _utc_now(),
        "commit_sha": _commit_sha(),
        "runner_version": RUNNER_VERSION,
        "dataset_digests": dataset_digests,
        "summary": {
            "total_cases": total_cases,
            "passed": passed,
            "failed": failed,
            "deferred": deferred,
            "blocking_failures": len(blocking_failures),
            "case_categories_covered": sorted(category_coverage),
        },
        "capability_results": capability_rows,
        "dataset_results": dataset_results,
        "blocking_failures": blocking_failures,
        "quality_lanes": manifest["quality_lanes"],
        "release_path_policy": manifest["release_path_policy"],
        "negative_control_result": {
            "checked": False,
            "observed_expected_failure": None,
            "reason": "Run --expect-fail-fixture for negative-control proof.",
        },
        "non_claims": manifest["non_claims"],
        "ci": {
            "ci_blocking": manifest["ci_blocking"],
            "default_requires_live_provider_credentials": False,
            "llm_provider_env_used": bool(os.environ.get("LLM_PROVIDER")),
            "mode_is_ci_safe": mode in {"deterministic", "replay"},
        },
    }
    return report


def _run_negative_control(*, manifest: dict[str, Any], mode: str) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    for control in manifest["negative_control_refs"]:
        dataset_path = _resolve_path(REPO_ROOT / _require_text(control, "path"))
        expected = _require_text(control, "expected_failure_contains")
        dataset_config = {
            "dataset_id": control["dataset_id"],
            "path": control["path"],
            "grader": "phase12_l5_case_rules",
            "grader_version": "phase12_l5_case_rules.v1",
            "blocking": True,
        }
        for case in _load_jsonl(dataset_path):
            result = _grade_case(case, dataset_path=dataset_path, dataset_config=dataset_config)
            observed = any(expected in failure for failure in result["failures"])
            cases.append(
                {
                    "dataset_id": control["dataset_id"],
                    "case_id": result["case_id"],
                    "expected_failure_contains": expected,
                    "observed_expected_failure": observed,
                    "failures": result["failures"],
                }
            )

    observed_all = bool(cases) and all(case["observed_expected_failure"] for case in cases)
    return {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "suite_id": manifest["suite_id"],
        "mode": mode,
        "runner_version": RUNNER_VERSION,
        "generated_at_utc": _utc_now(),
        "negative_control_result": {
            "checked": True,
            "observed_expected_failure": observed_all,
            "cases": cases,
        },
        "non_claims": manifest["non_claims"],
    }


def _grade_case(case: dict[str, Any], *, dataset_path: Path, dataset_config: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    assertions_checked: list[str] = []
    missing = sorted(REQUIRED_CASE_FIELDS - set(case))
    failures.extend(f"missing_required_field:{field}" for field in missing)
    assertions_checked.append("required_fields_present")

    _raise_forbidden_data(str(case.get("case_id", dataset_path)), case)
    dataset_ref = f"{dataset_path.relative_to(REPO_ROOT).as_posix()}#{case.get('case_id', '')}"

    for field in REF_LIST_FIELDS:
        if not _non_empty_str_list(case.get(field)):
            failures.append(f"missing_{field.removeprefix('expected_')}")
    assertions_checked.append("required_refs_present")

    if dataset_ref not in set(case.get("dataset_refs") or []):
        failures.append("dataset_ref_must_point_to_case")

    if not _non_empty_str_list(case.get("capability_ids")):
        failures.append("capability_ids_required")
    if not set(case.get("capability_ids") or []) <= set(dataset_config.get("capability_ids") or []):
        failures.append("case_capability_ids_must_be_declared_by_dataset")

    if not _non_empty_str_list(case.get("pass_criteria")):
        failures.append("pass_criteria_required")
    if not _non_empty_str_list(case.get("fail_criteria")):
        failures.append("fail_criteria_required")
    assertions_checked.append("pass_fail_criteria_present")

    triage = case.get("triage")
    if not isinstance(triage, dict) or not _text(triage.get("owner")) or not _text(triage.get("category")):
        failures.append("triage_owner_and_category_required")
        triage = {"owner": "UNKNOWN", "category": "UNKNOWN"}
    assertions_checked.append("triage_present")

    non_claims = set(case.get("non_claims") or [])
    missing_non_claims = sorted(REQUIRED_NON_CLAIMS - non_claims)
    failures.extend(f"missing_non_claim:{item}" for item in missing_non_claims)
    assertions_checked.append("fake_or_replay_non_claim_visible")

    provider_evidence_type = _text(case.get("provider_evidence_type"))
    if provider_evidence_type in {"fake", "fixture", "replay", "deterministic_regression"}:
        if "no_real_provider_quality_certification" not in non_claims:
            failures.append("fake_or_replay_requires_real_provider_non_claim")
    if provider_evidence_type == "real_provider":
        warnings.append("real_provider_evidence_is_non_ci_quality_lane")

    category = _text(case.get("case_category"))
    failure_mode = _text(case.get("expected_failure_mode"))
    if category == "happy_path" and failure_mode != "none":
        failures.append("happy_path_expected_failure_mode_must_be_none")
    if category not in {"happy_path", "replay"} and failure_mode in {"", "none"}:
        failures.append("negative_case_expected_failure_mode_required")
    if category in {"asset_conflict", "hitl", "provider_failure", "validation_failure"}:
        if not _non_empty_str_list(case.get("expected_hitl_refs")):
            failures.append("hitl_refs_required_for_blocked_or_reviewed_case")
    if category == "cross_agent_handoff_failure" and not _non_empty_str_list(case.get("expected_handoff_refs")):
        failures.append("handoff_refs_required")
    if category == "replay":
        criteria_text = " ".join(case.get("pass_criteria") or [])
        if "read_only" not in criteria_text or "side_effect_counters_zero" not in criteria_text:
            failures.append("replay_case_requires_read_only_side_effect_criteria")
    assertions_checked.append("category_specific_contract")

    return {
        "case_id": _text(case.get("case_id")) or "<missing>",
        "dataset_id": dataset_config["dataset_id"],
        "case_category": category,
        "capability_ids": list(case.get("capability_ids") or []),
        "passed": not failures,
        "blocking": bool(case.get("blocking", dataset_config.get("blocking", True))),
        "deferred_if_not_executable": bool(case.get("deferred_if_not_executable")),
        "failures": sorted(set(failures)),
        "warnings": sorted(set(warnings)),
        "assertions_checked": sorted(set(assertions_checked)),
        "expected_failure_mode": failure_mode,
        "expected_non_claims": sorted(non_claims),
        "triage": triage,
    }


def _render_markdown_report(report: dict[str, Any]) -> str:
    status = "eval_gate_passed" if report["summary"]["blocking_failures"] == 0 else "eval_gate_failed"
    lines = [
        "---",
        "title: P12_L5_EVAL_REPORT",
        "type: goal-evidence",
        f"status: {status}",
        "permalink: ai-for-interviewer/docs/goals/2026-06-07/p12-l5-eval-report",
        "---",
        "",
        "# P12 L5 Eval Gate Report",
        "",
        "## Run Metadata",
        "",
        f"- Suite: `{report['suite_id']}`",
        f"- Mode: `{report['mode']}`",
        f"- Commit SHA: `{report['commit_sha']}`",
        f"- Runner version: `{report['runner_version']}`",
        f"- Generated at UTC: `{report['generated_at_utc']}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    for key, value in report["summary"].items():
        lines.append(f"| `{key}` | `{value}` |")

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

    lines.extend(["", "## Release Path Policy", ""])
    lines.append("- Eval failure blocks the L5 release path: `true`.")
    lines.append("- Passing this deterministic/replay gate is not an L5 release claim.")
    lines.append("- Real-provider quality certification remains a separate lane.")

    lines.extend(["", "## Blocking Failures", ""])
    if report["blocking_failures"]:
        lines.extend(["| Dataset | Case | Triage | Failures |", "|---|---|---|---|"])
        for failure in report["blocking_failures"]:
            triage = failure["triage"]
            lines.append(
                f"| `{failure['dataset_id']}` | `{failure['case_id']}` | `{triage['owner']}:{triage['category']}` | `{', '.join(failure['failures'])}` |"
            )
    else:
        lines.append("No blocking failures.")

    lines.extend(["", "## Non-Claims", ""])
    for non_claim in report["non_claims"]:
        lines.append(f"- `{non_claim}`")
    return "\n".join(lines) + "\n"


def _scan_report_or_raise(report: dict[str, Any], markdown: str) -> None:
    _raise_forbidden_data("phase12_l5_report", report)
    _raise_forbidden_data("phase12_l5_markdown", {"markdown_report": markdown})


def _write_reports(*, report: dict[str, Any], markdown: str, report_dir: Path) -> None:
    report_dir = _resolve_path(report_dir if report_dir.is_absolute() else REPO_ROOT / report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "P12_L5_EVAL_REPORT.md").write_text(markdown, encoding="utf-8")
    (report_dir / "phase12_l5_eval_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: JSON root must be object")
    return payload


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSONL: {exc.msg}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_number}: JSONL case must be an object")
            cases.append(payload)
    if not cases:
        raise ValueError(f"{path}: dataset must not be empty")
    return cases


def _raise_forbidden_data(label: str, value: Any) -> None:
    paths = _forbidden_key_paths(value)
    if paths:
        raise ValueError(f"{label}: forbidden payload keys present: {', '.join(paths)}")


def _forbidden_key_paths(value: Any, *, prefix: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            if _normalize_key(key_text) in FORBIDDEN_PAYLOAD_KEYS:
                paths.append(path)
            paths.extend(_forbidden_key_paths(item, prefix=path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_forbidden_key_paths(item, prefix=f"{prefix}[{index}]"))
    return paths


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _non_empty_str_list(value: Any) -> bool:
    return isinstance(value, list) and any(isinstance(item, str) and item for item in value)


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _resolve_path(path: Path) -> Path:
    return path.expanduser().resolve()


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


def _print_error(payload: dict[str, Any]) -> None:
    print(json.dumps({"runner": RUNNER_VERSION, **payload}, ensure_ascii=False), file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
