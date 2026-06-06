"""Deterministic code-rule graders for offline AI eval datasets."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


FORBIDDEN_KEYS = {
    "raw_prompt",
    "system_prompt",
    "developer_prompt",
    "raw_completion",
    "provider_payload",
    "raw_provider_payload",
    "full_resume",
    "full_jd",
    "full_answer",
    "full_asset_body",
    "token",
    "secret",
    "cookie",
    "api_key",
}

SECRET_VALUE_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{8,}"),
    re.compile(r"\bbearer\s+[A-Za-z0-9._-]+", re.IGNORECASE),
    re.compile(r"\bapi[_-]?key\s*=", re.IGNORECASE),
    re.compile(r"\btoken\s*=", re.IGNORECASE),
    re.compile(r"\bsecret\s*=", re.IGNORECASE),
    re.compile(r"\bcookie\s*=", re.IGNORECASE),
)

SUPPORTED_TASK_TYPES = {
    "question_generation",
    "feedback_asset_consistency",
    "feedback_answer_change",
    "feedback_answer_coverage",
    "asset_candidate",
    "provider_boundary",
    "fake_gate",
    "agent_handoff_trace",
    "runtime_foundation_gap",
    "source_support_contract",
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


def find_forbidden_data(value: Any) -> dict[str, list[str]]:
    return {
        "forbidden_key_paths": _forbidden_key_paths(value),
        "forbidden_value_paths": _forbidden_value_paths(value),
    }


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
    elif task_type == "feedback_answer_coverage":
        _merge_domain_result(result, grade_feedback_answer_coverage_case(case))
    elif task_type == "asset_candidate":
        _merge_domain_result(result, grade_asset_candidate_case(case))
    elif task_type == "provider_boundary":
        _merge_domain_result(result, grade_provider_boundary_case(case))
    elif task_type == "fake_gate":
        _merge_domain_result(result, grade_fake_gate_case(case))
    elif task_type == "agent_handoff_trace":
        _merge_domain_result(result, grade_agent_handoff_trace_case(case))
    elif task_type == "runtime_foundation_gap":
        _merge_domain_result(result, grade_runtime_foundation_gap_case(case))
    elif task_type == "source_support_contract":
        _merge_domain_result(result, grade_source_support_contract_case(case))

    _finalize(result)
    return result


def grade_question_generation_case(case: dict[str, Any]) -> dict[str, Any]:
    result = _domain_result()
    input_data = _dict(case.get("input"))
    expected = _dict(case.get("expected"))
    payload = _candidate_payload(case)
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

    if expected.get("output_kind") == "question_candidate":
        if payload.get("candidate_type") != "question_candidate":
            result["failures"].append("question_output_must_be_question_candidate")
        _require_refs(payload, ("trace_refs", "validation_refs"), result)
        result["checked_rules"].append("question_candidate_refs_required")

    if expected.get("grounding_status") == "grounding_blocked":
        if _status_is_success(payload.get("status")):
            result["failures"].append("grounding_blocked_must_not_be_success")
        if _has_non_empty_formal_refs(payload):
            result["failures"].append("grounding_blocked_must_not_have_formal_refs")
        result["checked_rules"].append("grounding_blocked_no_formal_question")

    if expected.get("generation_path") == "deterministic_fallback":
        if _status_is_success(payload.get("status")):
            result["failures"].append("deterministic_fallback_must_not_be_generated_success")
        result["checked_rules"].append("deterministic_fallback_not_success")

    completed_focus_refs = input_data.get("completed_focus_refs")
    focus_key = payload.get("focus_key") or expected.get("focus_key")
    if isinstance(completed_focus_refs, list) and focus_key:
        if _text(focus_key) in {_text(item) for item in completed_focus_refs}:
            result["failures"].append("follow_up_focus_repeated")
        result["checked_rules"].append("follow_up_anti_repetition")

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


def grade_feedback_answer_coverage_case(case: dict[str, Any]) -> dict[str, Any]:
    result = _domain_result()
    expected = _dict(case.get("expected"))
    coverage = _dict(expected.get("answer_coverage"))
    missing_points = coverage.get("missing_points")
    weak_points = coverage.get("weak_points")
    contradicted_points = coverage.get("contradicted_points")

    if not any(isinstance(points, list) and points for points in (missing_points, weak_points, contradicted_points)):
        result["failures"].append("answer_coverage_requires_gap_points")
    if coverage.get("status") not in {"needs_improvement", "partial", "blocked"}:
        result["failures"].append("answer_coverage_status_invalid")
    result["checked_rules"].append("answer_coverage_gap_detected")
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


def grade_provider_boundary_case(case: dict[str, Any]) -> dict[str, Any]:
    result = _domain_result()
    expected = _dict(case.get("expected"))
    payload = _candidate_payload(case)

    if expected.get("provider_request_status") in {"validation_failed", "provider_unavailable", "rejected"}:
        if _status_is_success(payload.get("status") or expected.get("status")):
            result["failures"].append("provider_failure_must_not_be_success")
        result["checked_rules"].append("provider_failure_not_success")

    if expected.get("no_full_prompt_asset_fallback") is True:
        if payload.get("full_prompt_asset_fallback") is True or expected.get("full_prompt_asset_fallback") is True:
            result["failures"].append("full_prompt_asset_fallback_forbidden")
        result["checked_rules"].append("no_full_prompt_asset_fallback")

    if expected.get("fail_closed") is True:
        reason_codes = payload.get("reason_codes") or expected.get("reason_codes")
        if not isinstance(reason_codes, list) or not reason_codes:
            result["failures"].append("fail_closed_requires_reason_codes")
        result["checked_rules"].append("provider_fail_closed_reason_codes")

    return result


def grade_fake_gate_case(case: dict[str, Any]) -> dict[str, Any]:
    result = _domain_result()
    expected = _dict(case.get("expected"))
    payload = _candidate_payload(case)

    provider_evidence_type = _text(payload.get("provider_evidence_type") or expected.get("provider_evidence_type"))
    non_claims = payload.get("non_claims") or expected.get("non_claims")
    if provider_evidence_type in {"fake", "replay", "fixture"}:
        if not isinstance(non_claims, list) or "not_real_provider_quality_evidence" not in {
            _text(item) for item in non_claims
        }:
            result["failures"].append("fake_or_replay_requires_real_provider_non_claim")
        result["checked_rules"].append("fake_replay_non_claim_visible")

    if payload.get("runtime_fake_provider_allowed") is True or expected.get("runtime_fake_provider_allowed") is True:
        result["failures"].append("runtime_fake_provider_must_remain_rejected")

    if payload.get("fake_provider_used") is True and _status_is_success(payload.get("status")):
        result["failures"].append("fake_provider_must_not_be_generated_success")

    if payload.get("fallback_reported_as_generated_success") is True:
        result["failures"].append("fallback_must_not_be_generated_success")

    return result


def grade_agent_handoff_trace_case(case: dict[str, Any]) -> dict[str, Any]:
    result = _domain_result()
    payload = _candidate_payload(case)
    expected = _dict(case.get("expected"))
    candidate_type = _text(payload.get("candidate_type") or expected.get("candidate_type"))

    if candidate_type not in {"question_candidate", "feedback_candidate", "asset_update_candidate"}:
        result["failures"].append(f"unsupported_candidate_type:{candidate_type or 'missing'}")
    _require_refs(payload or expected, ("trace_refs", "validation_refs"), result)
    if expected.get("handoff_refs_required") is True:
        _require_refs(payload or expected, ("handoff_refs",), result)
    if candidate_type == "asset_update_candidate":
        if payload.get("user_confirmation_required") is not True and expected.get("user_confirmation_required") is not True:
            result["failures"].append("asset_update_candidate_user_confirmation_required")
    if _has_non_empty_formal_refs(payload) or _has_non_empty_formal_refs(expected):
        result["failures"].append("candidate_handoff_must_not_have_formal_refs")
    result["checked_rules"].append("candidate_handoff_refs_only")
    return result


def grade_runtime_foundation_gap_case(case: dict[str, Any]) -> dict[str, Any]:
    result = _domain_result()
    expected = _dict(case.get("expected"))
    status = _text(expected.get("status"))
    if status != "deferred_with_reason":
        result["failures"].append("runtime_gap_must_be_deferred_with_reason")
    for field in ("reason", "owner_phase", "non_claim"):
        if not _text(expected.get(field)):
            result["failures"].append(f"runtime_gap_missing_{field}")
    result["checked_rules"].append("runtime_gap_remains_deferred")
    return result


def grade_source_support_contract_case(case: dict[str, Any]) -> dict[str, Any]:
    result = _domain_result()
    expected = _dict(case.get("expected"))
    summary = _dict(expected.get("source_support_summary"))
    support_level = _text(summary.get("source_support_level"))

    if support_level in {"direct_project_evidence", "adjacent_project_evidence", "job_gap_only"}:
        if not isinstance(summary.get("reason_codes"), list) or not summary["reason_codes"]:
            result["failures"].append("source_support_summary_requires_reason_codes")
        if not isinstance(summary.get("evidence_refs"), list):
            result["failures"].append("source_support_summary_requires_evidence_refs")
        result["checked_rules"].append("source_support_summary_refs_visible")
    elif support_level == "insufficient_context":
        if expected.get("status") != "deferred_with_reason":
            result["failures"].append("insufficient_context_requires_deferred_record")
        result["checked_rules"].append("insufficient_context_deferred")
    else:
        result["failures"].append(f"unsupported_source_support_level:{support_level or 'missing'}")

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
    for path in _forbidden_value_paths(case):
        result["failures"].append(f"forbidden_value:{path}")


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
            if _normalize_key(key_text) in FORBIDDEN_KEYS:
                paths.append(path)
            paths.extend(_forbidden_key_paths(child, prefix=path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(_forbidden_key_paths(child, prefix=f"{prefix}[{index}]"))
    return paths


def _forbidden_value_paths(value: Any, *, prefix: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            paths.extend(_forbidden_value_paths(child, prefix=path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(_forbidden_value_paths(child, prefix=f"{prefix}[{index}]"))
    elif isinstance(value, str) and _looks_like_secret_value(value):
        paths.append(prefix or "<root>")
    return paths


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")


def _looks_like_secret_value(value: str) -> bool:
    return any(pattern.search(value) for pattern in SECRET_VALUE_PATTERNS)


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


def _require_refs(payload: dict[str, Any], fields: tuple[str, ...], result: dict[str, list[str]]) -> None:
    for field in fields:
        refs = payload.get(field)
        if not isinstance(refs, list) or not refs:
            result["failures"].append(f"{field}_required")


def _status_is_success(value: Any) -> bool:
    return _text(value) in {"success", "generated", "generated_success", "accepted", "succeeded"}


def _has_non_empty_formal_refs(payload: dict[str, Any]) -> bool:
    formal_refs = payload.get("formal_refs")
    formal_write_refs = payload.get("formal_write_refs")
    return bool(formal_refs) or bool(formal_write_refs)


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
