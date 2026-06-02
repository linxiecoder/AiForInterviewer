"""Deterministic code-rule graders for offline AI eval datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


FORBIDDEN_KEYS = {
    "raw_prompt",
    "system_prompt",
    "developer_prompt",
    "raw_completion",
    "provider_payload",
    "full_resume",
    "full_jd",
    "token",
    "secret",
    "cookie",
    "api_key",
}

SUPPORTED_TASK_TYPES = {
    "question_generation",
    "feedback_asset_consistency",
    "feedback_answer_change",
    "asset_candidate",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
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
    return cases


def grade_dataset(path: Path) -> dict[str, Any]:
    cases = [grade_case(case) for case in load_jsonl(path)]
    total = len(cases)
    failed = sum(1 for case in cases if not case["passed"])
    passed = total - failed
    return {
        "dataset": path.as_posix(),
        "total": total,
        "passed": passed,
        "failed": failed,
        "score": 1 if total > 0 and failed == 0 else 0,
        "cases": cases,
    }


def grade_case(case: dict[str, Any]) -> dict[str, Any]:
    case_id = str(case.get("case_id") or "")
    task_type = str(case.get("task_type") or "")
    result = _base_result(case_id=case_id, task_type=task_type)

    _check_required_fields(case, result)
    _check_forbidden_keys(case, result)
    _check_must_have_must_not_have(case, result)

    if task_type not in SUPPORTED_TASK_TYPES:
        result["failures"].append(f"unsupported_task_type:{task_type}")
    elif task_type == "question_generation":
        _merge_domain_result(result, grade_question_generation_case(case))
    elif task_type == "feedback_asset_consistency":
        _merge_domain_result(result, grade_feedback_asset_consistency_case(case))
    elif task_type == "feedback_answer_change":
        _merge_domain_result(result, grade_feedback_answer_change_case(case))
    elif task_type == "asset_candidate":
        _merge_domain_result(result, grade_asset_candidate_case(case))

    _finalize(result)
    return result


def grade_question_generation_case(case: dict[str, Any]) -> dict[str, Any]:
    result = _domain_result()
    input_data = _dict(case.get("input"))
    expected = _dict(case.get("expected"))
    support_level = _text(input_data.get("source_support_level") or expected.get("source_support_level"))
    question_mode = _text(expected.get("question_mode"))

    if support_level == "direct_project_evidence":
        _require_expected_list_items(
            expected,
            "required_question_focus",
            ["真实实现链路", "职责边界", "关键取舍", "验证方式"],
            result,
        )
        result["checked_rules"].append("direct_project_evidence_grounded_deep_dive")
    elif support_level == "job_gap_only":
        if "能力补偿" not in question_mode and "假设" not in question_mode:
            result["failures"].append("job_gap_only_requires_compensation_or_hypothetical_question")
        result["checked_rules"].append("job_gap_only_no_completed_fact_claim")
    elif support_level == "adjacent_project_evidence":
        required_language = expected.get("required_hypothetical_language")
        if not isinstance(required_language, list) or not {"如果", "假设", "你会如何"}.intersection(
            {_text(item) for item in required_language}
        ):
            result["failures"].append("adjacent_project_evidence_requires_hypothetical_language")
        if "hypothetical" not in question_mode and "假设" not in question_mode:
            result["failures"].append("adjacent_project_evidence_requires_hypothetical_mode")
        result["checked_rules"].append("adjacent_project_evidence_no_unsupported_claim_as_fact")
    else:
        result["warnings"].append(f"unknown_source_support_level:{support_level or 'missing'}")

    return result


def grade_feedback_asset_consistency_case(case: dict[str, Any]) -> dict[str, Any]:
    result = _domain_result()
    expected = _dict(case.get("expected"))
    asset_check = _dict(expected.get("asset_consistency_check"))
    status = _text(asset_check.get("status"))

    if status == "conflict":
        if not asset_check.get("conflicts") and not asset_check.get("unsupported_claims"):
            result["failures"].append("asset_consistency_conflict_requires_conflict_or_unsupported_claim")
        cards = expected.get("feedback_cards")
        if not isinstance(cards, list) or not cards or _dict(cards[0]).get("key") != "asset_consistency":
            result["failures"].append("asset_consistency_conflict_requires_first_card")
        result["checked_rules"].append("confirmed_asset_conflict_detected")

    if expected.get("archived_policy") == "historical_reference_only":
        if status not in {"insufficient_asset_context", "not_applicable"}:
            result["failures"].append("archived_asset_must_not_create_current_conflict")
        if asset_check.get("checked_asset_refs"):
            result["failures"].append("archived_asset_checked_as_current_source")
        result["checked_rules"].append("archived_asset_historical_reference_only")

    return result


def grade_feedback_answer_change_case(case: dict[str, Any]) -> dict[str, Any]:
    result = _domain_result()
    expected = _dict(case.get("expected"))
    change = _dict(expected.get("answer_change_analysis"))
    regressed_points = change.get("regressed_points")
    fixed_loss_points = change.get("fixed_loss_points")

    if regressed_points:
        if change.get("trend") == "improved":
            result["failures"].append("regressed_points_must_not_be_improved_trend")
        result["checked_rules"].append("same_question_regression_detected")
    if fixed_loss_points:
        if change.get("trend") not in {"improved", "mixed"}:
            result["failures"].append("fixed_loss_points_requires_improved_or_mixed_trend")
        result["checked_rules"].append("fixed_loss_points_detected")
    if not regressed_points and not fixed_loss_points:
        result["warnings"].append("answer_change_analysis_without_regression_or_fixed_loss")

    return result


def grade_asset_candidate_case(case: dict[str, Any]) -> dict[str, Any]:
    result = _domain_result()
    payload = _candidate_payload(case)
    candidates = _asset_candidates(payload)
    if not candidates:
        result["failures"].append("asset_candidate_missing")
        return result

    for candidate in candidates:
        if candidate.get("user_confirmation_required") is not True:
            result["failures"].append("asset_candidate_user_confirmation_required")
        if candidate.get("status") in {"asset_confirmed", "asset_archived"}:
            result["failures"].append("asset_candidate_must_not_write_formal_asset_status")
    result["checked_rules"].append("asset_candidate_requires_user_confirmation")
    return result


def _base_result(*, case_id: str, task_type: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "task_type": task_type,
        "passed": False,
        "score": 0,
        "failures": [],
        "warnings": [],
        "checked_rules": [],
    }


def _domain_result() -> dict[str, list[str]]:
    return {"failures": [], "warnings": [], "checked_rules": []}


def _merge_domain_result(result: dict[str, Any], domain_result: dict[str, list[str]]) -> None:
    for key in ("failures", "warnings", "checked_rules"):
        result[key].extend(domain_result.get(key, []))


def _finalize(result: dict[str, Any]) -> None:
    result["checked_rules"] = sorted(set(result["checked_rules"]))
    result["warnings"] = sorted(set(result["warnings"]))
    result["failures"] = sorted(set(result["failures"]))
    result["passed"] = not result["failures"]
    result["score"] = 1 if result["passed"] else 0


def _check_required_fields(case: dict[str, Any], result: dict[str, Any]) -> None:
    for field in ("case_id", "task_type", "input", "expected", "must_have", "must_not_have", "grader_notes"):
        if field not in case:
            result["failures"].append(f"missing_required_field:{field}")
    if not isinstance(case.get("input"), dict):
        result["failures"].append("input_must_be_object")
    if not isinstance(case.get("expected"), dict):
        result["failures"].append("expected_must_be_object")
    if not isinstance(case.get("must_have"), list):
        result["failures"].append("must_have_must_be_array")
    if not isinstance(case.get("must_not_have"), list):
        result["failures"].append("must_not_have_must_be_array")


def _check_forbidden_keys(case: dict[str, Any], result: dict[str, Any]) -> None:
    for path in _forbidden_key_paths(case):
        result["failures"].append(f"forbidden_key:{path}")


def _check_must_have_must_not_have(case: dict[str, Any], result: dict[str, Any]) -> None:
    if not isinstance(case.get("must_have"), list) or not isinstance(case.get("must_not_have"), list):
        return
    target = case.get("candidate_output")
    if target is None:
        target = {"input": case.get("input"), "expected": case.get("expected")}
    haystack = _json_text(target)

    for needle in case["must_have"]:
        text = _text(needle)
        if text and text not in haystack:
            result["failures"].append(f"must_have_missing:{text}")
    for needle in case["must_not_have"]:
        text = _text(needle)
        if text and text in haystack:
            result["failures"].append(f"must_not_have_present:{text}")
    result["checked_rules"].append("must_have_must_not_have")


def _forbidden_key_paths(value: Any, *, prefix: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            if key_text.casefold() in FORBIDDEN_KEYS:
                paths.append(path)
            paths.extend(_forbidden_key_paths(child, prefix=path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(_forbidden_key_paths(child, prefix=f"{prefix}[{index}]"))
    return paths


def _require_expected_list_items(
    expected: dict[str, Any],
    field: str,
    required_items: list[str],
    result: dict[str, list[str]],
) -> None:
    value = expected.get(field)
    items = {_text(item) for item in value} if isinstance(value, list) else set()
    for item in required_items:
        if item not in items:
            result["failures"].append(f"{field}_missing:{item}")


def _candidate_payload(case: dict[str, Any]) -> dict[str, Any]:
    candidate_output = case.get("candidate_output")
    if isinstance(candidate_output, dict):
        return candidate_output
    return _dict(case.get("expected"))


def _asset_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for key in ("project_asset_update_candidates", "asset_candidates"):
        value = payload.get(key)
        if isinstance(value, list):
            candidates.extend(_dict(item) for item in value if isinstance(item, dict))
    return candidates


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
