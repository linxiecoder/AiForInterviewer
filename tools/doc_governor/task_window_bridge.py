from __future__ import annotations

from pathlib import Path
from typing import Any

from .task_apply_summary import build_task_apply_summary
from .task_state_writeback import (
    FORMAL_WINDOW_CLOSED,
    IMPLEMENTATION_DOC_NOT_ACTIVE,
    build_task_state_writeback_preview,
)


MODULE_LEVEL_BLOCKERS = {"doc:api", "doc:open_questions"}
CONTENT_BLOCKERS = {
    "doc:implementation_doc",
    "doc:design_doc",
    "gate:implementation_scope_unclear",
    "gate:required_tests_missing",
    "gate:acceptance_criteria_missing",
}


def build_task_window_bridge(
    *,
    state_path: str | Path,
    evaluate_payload: dict[str, Any],
    entity_ids: list[str] | tuple[str, ...] | str | None = None,
) -> dict[str, Any]:
    writeback_preview = build_task_state_writeback_preview(
        state_path=state_path,
        evaluate_payload=evaluate_payload,
        entity_ids=entity_ids,
    )
    task_ids = [
        str(item.get("task_id", "")).strip()
        for item in _as_list_of_dicts(writeback_preview.get("tasks"))
        if item.get("task_id")
    ]
    apply_summary = build_task_apply_summary(
        state_path=state_path,
        after_evaluate_payload=evaluate_payload,
        entity_ids=task_ids,
        before_payload=None,
    )

    resolved_map = _group_blockers_by_task(apply_summary.get("resolved_blockers"))
    manual_fill_map = _group_fields_by_task(apply_summary.get("manual_fill_remaining"))

    candidate_tasks_after_state_activation: list[dict[str, Any]] = []
    blocked_before_open_window: list[dict[str, Any]] = []
    state_activation_prerequisites: list[dict[str, Any]] = []
    predicted_post_activation_blockers: list[dict[str, Any]] = []
    task_examples: list[dict[str, Any]] = []
    recommended_next_step: list[dict[str, Any]] = []

    summary_counters = {
        "content_blocked_count": 0,
        "window_only_after_state_activation_count": 0,
        "post_activation_still_blocked_count": 0,
        "already_window_only_count": 0,
        "module_level_blocked_count": 0,
        "requirement_relation_blocked_count": 0,
    }

    for item in _as_list_of_dicts(writeback_preview.get("tasks")):
        task_id = str(item.get("task_id", "")).strip()
        if not task_id:
            continue
        module_id = str(item.get("module_id", "")).strip()
        resolved_in_content = resolved_map.get(task_id, set())
        manual_fill_fields = manual_fill_map.get(task_id, [])

        current_blockers = _as_string_list(item.get("current_blocker_refs"))
        predicted_blockers = _as_string_list(
            item.get("predicted_blocker_refs_after_writeback")
        )
        effective_current_blockers = [
            blocker for blocker in current_blockers if blocker not in resolved_in_content
        ]
        effective_predicted_blockers = [
            blocker for blocker in predicted_blockers if blocker not in resolved_in_content
        ]
        categories = _categorize_blockers(effective_current_blockers)
        activation_needed = (
            str(item.get("current_implementation_doc_state", "")).strip()
            != "active_working_doc"
        )

        classification = _classify_task(
            activation_needed=activation_needed,
            categories=categories,
            manual_fill_fields=manual_fill_fields,
            effective_predicted_blockers=effective_predicted_blockers,
        )
        summary_counters[f"{classification}_count"] = (
            summary_counters.get(f"{classification}_count", 0) + 1
        )

        record = {
            "task_id": task_id,
            "module_id": module_id,
            "classification": classification,
            "current_effective_blockers": effective_current_blockers,
            "predicted_post_activation_blockers": effective_predicted_blockers,
            "manual_fill_fields": manual_fill_fields,
            "resolved_in_content": sorted(resolved_in_content),
            "reason": _build_reason(
                classification=classification,
                manual_fill_fields=manual_fill_fields,
                categories=categories,
                effective_predicted_blockers=effective_predicted_blockers,
            ),
        }

        state_activation_prerequisites.append(
            {
                "task_id": task_id,
                "module_id": module_id,
                "activation_needed": activation_needed,
                "content_blockers_cleared": not categories["content"]
                and not manual_fill_fields
                and not categories["other"],
                "requirement_relation_resolved": not categories["requirement"],
                "module_level_blockers_cleared": not categories["module"],
                "remaining_manual_fill_fields": manual_fill_fields,
            }
        )
        predicted_post_activation_blockers.append(
            {
                "task_id": task_id,
                "module_id": module_id,
                "activation_needed": activation_needed,
                "predicted_post_activation_blockers": effective_predicted_blockers,
                "window_only_after_state_activation": (
                    effective_predicted_blockers == [FORMAL_WINDOW_CLOSED]
                ),
            }
        )
        task_examples.append(
            {
                "task_id": task_id,
                "module_id": module_id,
                "classification": classification,
                "reason": record["reason"],
                "why_close_to_open_window": classification
                in {
                    "window_only_after_state_activation",
                    "already_window_only",
                },
                "why_not_open_window_yet": classification
                not in {
                    "window_only_after_state_activation",
                    "already_window_only",
                },
                "module_level_blockers": categories["module"],
            }
        )
        recommended_next_step.extend(
            _build_next_actions(
                task_id=task_id,
                module_id=module_id,
                classification=classification,
                categories=categories,
                manual_fill_fields=manual_fill_fields,
            )
        )

        if classification in {
            "window_only_after_state_activation",
            "already_window_only",
        }:
            candidate_tasks_after_state_activation.append(record)
        else:
            blocked_before_open_window.append(record)

    recommended_next_step = _prepend_batch_actions(
        next_actions=_dedupe_actions(recommended_next_step),
        candidate_tasks=candidate_tasks_after_state_activation,
        blocked_tasks=blocked_before_open_window,
    )

    return {
        "summary": {
            "selected_task_count": len(task_ids),
            "candidate_tasks_after_state_activation_count": len(
                candidate_tasks_after_state_activation
            ),
            "blocked_before_open_window_count": len(blocked_before_open_window),
            "content_blocked_count": summary_counters["content_blocked_count"],
            "window_only_after_state_activation_count": summary_counters[
                "window_only_after_state_activation_count"
            ],
            "post_activation_still_blocked_count": summary_counters[
                "post_activation_still_blocked_count"
            ],
            "already_window_only_count": summary_counters[
                "already_window_only_count"
            ],
            "module_level_blocked_count": summary_counters[
                "module_level_blocked_count"
            ],
            "requirement_relation_blocked_count": summary_counters[
                "requirement_relation_blocked_count"
            ],
        },
        "candidate_tasks_after_state_activation": candidate_tasks_after_state_activation,
        "blocked_before_open_window": blocked_before_open_window,
        "state_activation_prerequisites": state_activation_prerequisites,
        "predicted_post_activation_blockers": predicted_post_activation_blockers,
        "recommended_next_step": recommended_next_step,
        "confidence": _build_confidence(
            candidate_tasks=candidate_tasks_after_state_activation,
            blocked_tasks=blocked_before_open_window,
        ),
        "reasoning_notes": [
            "本桥接层只做分析，不写 state，不修改 preflight-open-window 行为。",
            "判断是否接近 open-window 时，会剔除当前文档内容里已清掉但 formal gate 仍可能保留的旧 blocker 表象。",
            "formal_window_closed 仍是独立 gate；即使内容 blocker 已收敛，也不等于窗口已经可直接打开。",
        ],
        "task_examples": task_examples,
    }


def _classify_task(
    *,
    activation_needed: bool,
    categories: dict[str, list[str]],
    manual_fill_fields: list[str],
    effective_predicted_blockers: list[str],
) -> str:
    if categories["module"]:
        return "module_level_blocked"
    if categories["requirement"]:
        return "requirement_relation_blocked"
    if categories["content"] or categories["other"] or manual_fill_fields:
        return "content_blocked"
    if not activation_needed and effective_predicted_blockers == [FORMAL_WINDOW_CLOSED]:
        return "already_window_only"
    if activation_needed and effective_predicted_blockers == [FORMAL_WINDOW_CLOSED]:
        return "window_only_after_state_activation"
    return "post_activation_still_blocked"


def _build_reason(
    *,
    classification: str,
    manual_fill_fields: list[str],
    categories: dict[str, list[str]],
    effective_predicted_blockers: list[str],
) -> str:
    if classification == "window_only_after_state_activation":
        return "内容 blocker 已基本收敛；若推进 implementation_doc_state，预计只剩 formal_window_closed。"
    if classification == "already_window_only":
        return "当前 implementation_doc_state 已激活，主要只剩 formal_window_closed。"
    if classification == "content_blocked":
        if manual_fill_fields:
            return f"当前仍需先补人工字段：{', '.join(manual_fill_fields)}。"
        blockers = ", ".join(categories["content"] + categories["other"]) or "内容 blocker"
        return f"当前仍被内容 blocker 阻断：{blockers}。"
    if classification == "module_level_blocked":
        blockers = ", ".join(categories["module"]) or "module blocker"
        return f"当前仍应留在模块层处理：{blockers}。"
    if classification == "requirement_relation_blocked":
        blockers = ", ".join(categories["requirement"]) or "requirement relation"
        return f"requirement 关系仍未闭合：{blockers}。"
    blockers = ", ".join(effective_predicted_blockers) or "剩余 blocker"
    return f"即使推进 implementation_doc_state，预计仍不适合进入 open-window：{blockers}。"


def _build_next_actions(
    *,
    task_id: str,
    module_id: str,
    classification: str,
    categories: dict[str, list[str]],
    manual_fill_fields: list[str],
) -> list[dict[str, Any]]:
    if classification == "window_only_after_state_activation":
        return [
            {
                "scope": "task",
                "task_id": task_id,
                "module_id": module_id,
                "title": "先推进 implementation_doc_state dry-run",
                "reason": "激活后预计只剩 formal window，可以进入 preflight-open-window 视角。",
            }
        ]
    if classification == "already_window_only":
        return [
            {
                "scope": "task",
                "task_id": task_id,
                "module_id": module_id,
                "title": "保留为 open-window 候选",
                "reason": "当前主要问题已收敛到 formal window 层。",
            }
        ]
    if classification == "module_level_blocked":
        return [
            {
                "scope": "module",
                "task_id": task_id,
                "module_id": module_id,
                "title": "先解决模块继承 blocker",
                "reason": "不应继续在 task 文档层局部修补来绕过模块问题。",
            }
        ]
    if classification == "requirement_relation_blocked":
        return [
            {
                "scope": "task",
                "task_id": task_id,
                "module_id": module_id,
                "title": "先确认 requirement 关系",
                "reason": "requirement 关系未闭合时，不适合提前推进 open-window 视角。",
            }
        ]
    if classification == "content_blocked":
        detail = (
            f"先补人工字段：{', '.join(manual_fill_fields)}"
            if manual_fill_fields
            else "先继续清理内容 blocker"
        )
        return [
            {
                "scope": "task",
                "task_id": task_id,
                "module_id": module_id,
                "title": "先继续处理内容层缺口",
                "reason": detail,
            }
        ]
    return [
        {
            "scope": "task",
            "task_id": task_id,
            "module_id": module_id,
            "title": "推进前重新评估激活后 blocker",
            "reason": "state 激活后仍会保留非 window blocker，当前不应直接转入 preflight-open-window。",
        }
    ]


def _prepend_batch_actions(
    *,
    next_actions: list[dict[str, Any]],
    candidate_tasks: list[dict[str, Any]],
    blocked_tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    batch_actions: list[dict[str, Any]] = []
    if candidate_tasks:
        task_ids = ", ".join(
            item.get("task_id", "") for item in candidate_tasks if item.get("task_id")
        )
        batch_actions.append(
            {
                "scope": "batch",
                "task_id": "",
                "module_id": "",
                "title": "优先看首批 state activation 候选",
                "reason": f"当前最接近 open-window 的 task 是：{task_ids}。",
            }
        )
    if any(item.get("classification") == "content_blocked" for item in blocked_tasks):
        batch_actions.append(
            {
                "scope": "batch",
                "task_id": "",
                "module_id": "",
                "title": "先消内容 blocker，再谈 open-window",
                "reason": "仍有 task 停留在人工字段或内容层，不宜提前推进 formal window 视角。",
            }
        )
    if any(item.get("classification") == "module_level_blocked" for item in blocked_tasks):
        batch_actions.append(
            {
                "scope": "batch",
                "task_id": "",
                "module_id": "",
                "title": "模块 blocker 继续留在模块层",
                "reason": "模块继承问题不应通过 task 层桥接分析被误推成 open-window 候选。",
            }
        )
    return _dedupe_actions(batch_actions + next_actions)


def _build_confidence(
    *,
    candidate_tasks: list[dict[str, Any]],
    blocked_tasks: list[dict[str, Any]],
) -> dict[str, Any]:
    score = 0.82
    if candidate_tasks:
        score += 0.06
    if any(item.get("classification") == "module_level_blocked" for item in blocked_tasks):
        score -= 0.03
    if any(item.get("classification") == "content_blocked" for item in blocked_tasks):
        score -= 0.03
    score = round(max(0.0, min(1.0, score)), 2)
    level = "high" if score >= 0.85 else "medium" if score >= 0.7 else "low"
    return {"level": level, "score": score}


def _group_blockers_by_task(items: Any) -> dict[str, set[str]]:
    output: dict[str, set[str]] = {}
    for item in _as_list_of_dicts(items):
        task_id = str(item.get("task_id", "")).strip()
        blocker = str(item.get("blocker", "")).strip()
        if not task_id or not blocker:
            continue
        output.setdefault(task_id, set()).add(blocker)
    return output


def _group_fields_by_task(items: Any) -> dict[str, list[str]]:
    output: dict[str, list[str]] = {}
    for item in _as_list_of_dicts(items):
        task_id = str(item.get("task_id", "")).strip()
        if not task_id:
            continue
        output[task_id] = _dedupe_strings(_as_string_list(item.get("fields")))
    return output


def _categorize_blockers(blockers: list[str]) -> dict[str, list[str]]:
    buckets = {
        "requirement": [],
        "module": [],
        "content": [],
        "state": [],
        "other": [],
    }
    for blocker in blockers:
        if blocker.startswith("gate:requirement_id_"):
            buckets["requirement"].append(blocker)
        elif blocker.startswith("module:") or blocker in MODULE_LEVEL_BLOCKERS:
            buckets["module"].append(blocker)
        elif blocker in {IMPLEMENTATION_DOC_NOT_ACTIVE, FORMAL_WINDOW_CLOSED}:
            buckets["state"].append(blocker)
        elif blocker in CONTENT_BLOCKERS or blocker.startswith(
            "policy:language_non_compliant"
        ):
            buckets["content"].append(blocker)
        else:
            buckets["other"].append(blocker)
    return {key: _dedupe_strings(value) for key, value in buckets.items()}


def _dedupe_actions(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str, str]] = set()
    output: list[dict[str, Any]] = []
    for item in items:
        key = (
            str(item.get("scope", "")).strip(),
            str(item.get("task_id", "")).strip(),
            str(item.get("module_id", "")).strip(),
            str(item.get("title", "")).strip(),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def _as_list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    output: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            output.append(text)
    return output


def _dedupe_strings(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        output.append(text)
    return output
