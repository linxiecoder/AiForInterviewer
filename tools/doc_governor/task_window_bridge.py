from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .task_apply_summary import build_task_apply_summary
from .task_state_writeback import (
    FORMAL_WINDOW_CLOSED,
    IMPLEMENTATION_DOC_NOT_ACTIVE,
    build_task_state_writeback_preview,
)


REQUIREMENT_PREFIX = "gate:requirement_id_"
MODULE_BLOCKERS = {"doc:api", "doc:open_questions"}
MANUAL_FIELDS = {
    "allowed_modify_paths",
    "required_tests",
    "acceptance_criteria",
    "design_key_sections",
}


def build_task_window_bridge(
    *,
    state_path: str | Path,
    evaluate_payload: dict[str, Any],
    entity_ids: list[str] | tuple[str, ...] | str | None = None,
) -> dict[str, Any]:
    state_path = Path(state_path)
    state = _load_state(state_path)
    task_ids = _normalize_entity_ids(entity_ids=entity_ids, state=state)

    writeback_preview = build_task_state_writeback_preview(
        state_path=state_path,
        evaluate_payload=evaluate_payload,
        entity_ids=task_ids,
    )
    apply_summary = build_task_apply_summary(
        state_path=state_path,
        after_evaluate_payload=evaluate_payload,
        entity_ids=task_ids,
        before_payload=None,
    )

    subtasks = _as_dict(state.get("subtasks"))
    writeback_map = {
        str(item.get("task_id", "")).strip(): item
        for item in _as_list_of_dicts(writeback_preview.get("tasks"))
        if item.get("task_id")
    }
    resolved_map = _group_blockers_by_task(apply_summary.get("resolved_blockers"))
    manual_map = _group_manual_fill_by_task(apply_summary.get("manual_fill_remaining"))
    status_map = {
        str(item.get("task_id", "")).strip(): item
        for item in _as_list_of_dicts(apply_summary.get("task_status_after_apply"))
        if item.get("task_id")
    }

    candidate_tasks_after_state_activation: list[dict[str, Any]] = []
    blocked_before_open_window: list[dict[str, Any]] = []
    state_activation_prerequisites: list[dict[str, Any]] = []
    predicted_post_activation_blockers: list[dict[str, Any]] = []
    recommended_next_step: list[dict[str, Any]] = []
    task_examples: list[dict[str, Any]] = []

    classification_counts = {
        "content_blocked": 0,
        "state_activation_candidate": 0,
        "window_only_after_state_activation": 0,
        "post_activation_still_blocked": 0,
        "already_window_only": 0,
        "module_level_blocked": 0,
        "requirement_relation_blocked": 0,
    }

    for task_id in task_ids:
        task_state = _as_dict(subtasks.get(task_id))
        meta = _as_dict(task_state.get("meta"))
        module_id = str(meta.get("module_id", "")).strip()

        writeback_item = _as_dict(writeback_map.get(task_id))
        status_item = _as_dict(status_map.get(task_id))
        resolved_in_content = resolved_map.get(task_id, set())
        manual_fill_fields = manual_map.get(task_id, [])

        current_blockers = _as_string_list(writeback_item.get("current_blocker_refs"))
        predicted_blockers = _as_string_list(
            writeback_item.get("predicted_blocker_refs_after_writeback")
        )
        effective_current_blockers = [
            blocker for blocker in current_blockers if blocker not in resolved_in_content
        ]
        effective_predicted_blockers = [
            blocker for blocker in predicted_blockers if blocker not in resolved_in_content
        ]

        categorized = _categorize_blockers(effective_current_blockers)
        activation_needed = (
            str(writeback_item.get("current_implementation_doc_state", "")).strip()
            != "active_working_doc"
        )
        content_prerequisites_satisfied = (
            not categorized["content"]
            and not categorized["other"]
            and not any(field in MANUAL_FIELDS for field in manual_fill_fields)
        )
        requirement_prerequisites_satisfied = not categorized["requirement"]
        module_prerequisites_satisfied = not categorized["module"]
        eligible_for_state_activation = (
            activation_needed
            and content_prerequisites_satisfied
            and requirement_prerequisites_satisfied
            and module_prerequisites_satisfied
        )
        only_formal_window_after_activation = (
            effective_predicted_blockers == [FORMAL_WINDOW_CLOSED]
        )
        post_activation_still_blocked = bool(
            [
                blocker
                for blocker in effective_predicted_blockers
                if blocker != FORMAL_WINDOW_CLOSED
            ]
        )

        classification = _classify_task(
            activation_needed=activation_needed,
            eligible_for_state_activation=eligible_for_state_activation,
            only_formal_window_after_activation=only_formal_window_after_activation,
            post_activation_still_blocked=post_activation_still_blocked,
            categorized=categorized,
            manual_fill_fields=manual_fill_fields,
        )
        classification_counts[classification] = (
            classification_counts.get(classification, 0) + 1
        )

        prerequisite_item = _build_prerequisite_item(
            task_id=task_id,
            module_id=module_id,
            activation_needed=activation_needed,
            eligible_for_state_activation=eligible_for_state_activation,
            categorized=categorized,
            manual_fill_fields=manual_fill_fields,
        )
        state_activation_prerequisites.append(prerequisite_item)

        predicted_item = {
            "task_id": task_id,
            "module_id": module_id,
            "activation_needed": activation_needed,
            "current_effective_blockers": effective_current_blockers,
            "predicted_post_activation_blockers": effective_predicted_blockers,
            "only_formal_window_after_activation": only_formal_window_after_activation,
            "post_activation_still_blocked": post_activation_still_blocked,
        }
        predicted_post_activation_blockers.append(predicted_item)

        reason = _build_reason(
            classification=classification,
            categorized=categorized,
            manual_fill_fields=manual_fill_fields,
            effective_predicted_blockers=effective_predicted_blockers,
        )
        record = {
            "task_id": task_id,
            "module_id": module_id,
            "classification": classification,
            "activation_needed": activation_needed,
            "eligible_for_state_activation": eligible_for_state_activation,
            "current_effective_blockers": effective_current_blockers,
            "predicted_post_activation_blockers": effective_predicted_blockers,
            "manual_fill_fields": manual_fill_fields,
            "resolved_in_content": sorted(resolved_in_content),
            "remaining_gap_categories": _as_string_list(
                _as_dict(status_item).get("remaining_gap_categories")
            ),
            "reason": reason,
        }
        if classification in {
            "window_only_after_state_activation",
            "already_window_only",
            "state_activation_candidate",
        }:
            candidate_tasks_after_state_activation.append(record)
        else:
            blocked_before_open_window.append(record)

        task_examples.append(
            _build_task_example(
                task_id=task_id,
                module_id=module_id,
                classification=classification,
                reason=reason,
                categorized=categorized,
                manual_fill_fields=manual_fill_fields,
                effective_predicted_blockers=effective_predicted_blockers,
            )
        )
        recommended_next_step.extend(
            _build_task_actions(
                task_id=task_id,
                module_id=module_id,
                classification=classification,
                categorized=categorized,
                manual_fill_fields=manual_fill_fields,
            )
        )

    recommended_next_step = _prepend_batch_actions(
        next_actions=_dedupe_actions(recommended_next_step),
        classification_counts=classification_counts,
        candidate_tasks=candidate_tasks_after_state_activation,
        blocked_tasks=blocked_before_open_window,
    )

    confidence = _build_confidence(
        writeback_preview=writeback_preview,
        blocked_tasks=blocked_before_open_window,
    )
    reasoning_notes = _build_reasoning_notes(
        writeback_preview=writeback_preview,
        classification_counts=classification_counts,
    )

    return {
        "summary": {
            "selected_task_count": len(task_ids),
            "candidate_after_state_activation_count": len(
                candidate_tasks_after_state_activation
            ),
            "blocked_before_open_window_count": len(blocked_before_open_window),
            "content_blocked_count": classification_counts["content_blocked"],
            "state_activation_candidate_count": classification_counts[
                "state_activation_candidate"
            ],
            "window_only_after_state_activation_count": classification_counts[
                "window_only_after_state_activation"
            ],
            "post_activation_still_blocked_count": classification_counts[
                "post_activation_still_blocked"
            ],
            "module_level_blocked_count": classification_counts[
                "module_level_blocked"
            ],
            "requirement_relation_blocked_count": classification_counts[
                "requirement_relation_blocked"
            ],
        },
        "candidate_tasks_after_state_activation": candidate_tasks_after_state_activation,
        "blocked_before_open_window": blocked_before_open_window,
        "state_activation_prerequisites": state_activation_prerequisites,
        "predicted_post_activation_blockers": predicted_post_activation_blockers,
        "recommended_next_step": recommended_next_step,
        "confidence": confidence,
        "reasoning_notes": reasoning_notes,
        "task_examples": task_examples,
    }


def _build_prerequisite_item(
    *,
    task_id: str,
    module_id: str,
    activation_needed: bool,
    eligible_for_state_activation: bool,
    categorized: dict[str, list[str]],
    manual_fill_fields: list[str],
) -> dict[str, Any]:
    prerequisites = [
        {
            "code": "content_blockers_cleared",
            "satisfied": not categorized["content"] and not categorized["other"],
            "details": categorized["content"] + categorized["other"],
        },
        {
            "code": "manual_fields_filled",
            "satisfied": not manual_fill_fields,
            "details": manual_fill_fields,
        },
        {
            "code": "requirement_relation_resolved",
            "satisfied": not categorized["requirement"],
            "details": categorized["requirement"],
        },
        {
            "code": "module_level_blockers_cleared",
            "satisfied": not categorized["module"],
            "details": categorized["module"],
        },
    ]
    return {
        "task_id": task_id,
        "module_id": module_id,
        "activation_needed": activation_needed,
        "eligible_for_state_activation": eligible_for_state_activation,
        "prerequisites": prerequisites,
    }


def _build_reason(
    *,
    classification: str,
    categorized: dict[str, list[str]],
    manual_fill_fields: list[str],
    effective_predicted_blockers: list[str],
) -> str:
    if classification == "window_only_after_state_activation":
        return "内容 blocker 已基本收敛；若推进 implementation_doc_state，预计只剩 formal_window_closed。"
    if classification == "already_window_only":
        return "implementation_doc_state 已处于激活态，当前主要只剩 formal_window_closed。"
    if classification == "state_activation_candidate":
        return "内容 blocker 已收敛到可考虑推进 implementation_doc_state，但激活后仍有其他非 window blocker。"
    if classification == "module_level_blocked":
        blockers = ", ".join(categorized["module"]) or "module blocker"
        return f"当前仍受模块继承 blocker 影响，应先回到模块层处理：{blockers}。"
    if classification == "requirement_relation_blocked":
        blockers = ", ".join(categorized["requirement"]) or "requirement relation"
        return f"requirement 关系仍未闭合；即使推进 implementation_doc_state 也不适合直接进入 open-window：{blockers}。"
    if classification == "content_blocked":
        parts: list[str] = []
        if categorized["content"] or categorized["other"]:
            parts.append("仍有内容层 blocker")
        if manual_fill_fields:
            parts.append(f"仍需人工填写字段：{', '.join(manual_fill_fields)}")
        return "；".join(parts) or "当前仍有内容 blocker，不适合考虑 open-window。"
    remaining = ", ".join(effective_predicted_blockers) or "其他 blocker"
    return f"即使推进 implementation_doc_state，预计仍会保留非 window blocker：{remaining}。"


def _build_task_example(
    *,
    task_id: str,
    module_id: str,
    classification: str,
    reason: str,
    categorized: dict[str, list[str]],
    manual_fill_fields: list[str],
    effective_predicted_blockers: list[str],
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "module_id": module_id,
        "classification": classification,
        "why_close_to_open_window": classification in {
            "window_only_after_state_activation",
            "already_window_only",
        },
        "why_deferred": classification not in {
            "window_only_after_state_activation",
            "already_window_only",
        },
        "reason": reason,
        "module_level_blockers": categorized["module"],
        "manual_fill_fields": manual_fill_fields,
        "predicted_post_activation_blockers": effective_predicted_blockers,
    }


def _build_task_actions(
    *,
    task_id: str,
    module_id: str,
    classification: str,
    categorized: dict[str, list[str]],
    manual_fill_fields: list[str],
) -> list[dict[str, Any]]:
    if classification == "window_only_after_state_activation":
        return [
            {
                "scope": "task",
                "task_id": task_id,
                "module_id": module_id,
                "title": "先做 implementation_doc_state dry-run",
                "reason": "内容 blocker 已基本收敛；推进状态位后可直接衔接 preflight-open-window。",
            }
        ]
    if classification == "already_window_only":
        return [
            {
                "scope": "task",
                "task_id": task_id,
                "module_id": module_id,
                "title": "保留为 preflight-open-window 候选",
                "reason": "当前主要只剩 formal window 问题，不需要继续在 task 文档层修补结构。",
            }
        ]
    if classification == "module_level_blocked":
        return [
            {
                "scope": "module",
                "task_id": task_id,
                "module_id": module_id,
                "title": "先解决模块继承 blocker",
                "reason": "这类问题不应通过继续修 task 文档绕过。",
            }
        ]
    if classification == "requirement_relation_blocked":
        return [
            {
                "scope": "task",
                "task_id": task_id,
                "module_id": module_id,
                "title": "先确认 requirement 关系",
                "reason": "requirement 关系未闭合时，不宜提前推进 implementation_doc_state 或 open-window。",
            }
        ]
    if classification == "content_blocked":
        reason = (
            f"先补人工字段：{', '.join(manual_fill_fields)}"
            if manual_fill_fields
            else "先清理剩余内容 blocker"
        )
        return [
            {
                "scope": "task",
                "task_id": task_id,
                "module_id": module_id,
                "title": "先继续处理内容层缺口",
                "reason": reason,
            }
        ]
    return [
        {
            "scope": "task",
            "task_id": task_id,
            "module_id": module_id,
            "title": "推进前重新评估激活后 blocker",
            "reason": "implementation_doc_state 激活后仍有非 window blocker，需要先确认是否值得推进。",
        }
    ]


def _prepend_batch_actions(
    *,
    next_actions: list[dict[str, Any]],
    classification_counts: dict[str, int],
    candidate_tasks: list[dict[str, Any]],
    blocked_tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    batch_actions: list[dict[str, Any]] = []
    if classification_counts.get("content_blocked", 0):
        batch_actions.append(
            {
                "scope": "batch",
                "task_id": "",
                "module_id": "",
                "title": "先消内容 blocker，再谈 state activation",
                "reason": "仍有 task 停留在人工字段或文档内容层，过早推进 implementation_doc_state 只会制造假候选。",
            }
        )
    if candidate_tasks:
        task_ids = ", ".join(
            item.get("task_id", "") for item in candidate_tasks if item.get("task_id")
        )
        batch_actions.append(
            {
                "scope": "batch",
                "task_id": "",
                "module_id": "",
                "title": "把 state activation dry-run 聚焦到首批候选",
                "reason": f"当前更适合先看这些 task：{task_ids}。",
            }
        )
    if classification_counts.get("module_level_blocked", 0):
        batch_actions.append(
            {
                "scope": "batch",
                "task_id": "",
                "module_id": "",
                "title": "模块继承 blocker 继续留在模块层处理",
                "reason": "这类 task 不应进入首批 open-window 候选。",
            }
        )
    if blocked_tasks and not candidate_tasks:
        batch_actions.append(
            {
                "scope": "batch",
                "task_id": "",
                "module_id": "",
                "title": "当前没有可直接桥接到 preflight-open-window 的 task",
                "reason": "需要先处理 requirement、内容或模块层前置问题。",
            }
        )
    return _dedupe_actions(batch_actions + next_actions)


def _build_confidence(
    *,
    writeback_preview: dict[str, Any],
    blocked_tasks: list[dict[str, Any]],
) -> dict[str, Any]:
    score = 0.86
    if any(
        item.get("status") == "evaluate_payload_out_of_sync"
        for item in _as_list_of_dicts(writeback_preview.get("tasks"))
    ):
        score -= 0.12
    if any(item.get("classification") == "post_activation_still_blocked" for item in blocked_tasks):
        score -= 0.04
    if any(item.get("classification") == "content_blocked" for item in blocked_tasks):
        score -= 0.04
    level = "high" if score >= 0.85 else "medium" if score >= 0.7 else "low"
    return {
        "level": level,
        "score": round(max(0.0, min(1.0, score)), 2),
    }


def _build_reasoning_notes(
    *,
    writeback_preview: dict[str, Any],
    classification_counts: dict[str, int],
) -> list[str]:
    notes = [
        "本模块只做桥接分析，不写 state，也不修改 preflight-open-window 或 open-window 主链。",
        "判断是否接近 open-window 时，会同时参考 state 激活预测和当前文档内容检查，避免把已清掉的结构问题误当成仍需继续修文档。",
        "formal_window_closed 仍然是独立 gate；即使内容层和 implementation_doc_state 已经到位，也不等于窗口已经可以直接打开。",
    ]
    if classification_counts.get("module_level_blocked", 0):
        notes.append("存在模块继承 blocker 的 task 会继续留在模块层，不会被桥接层误推到 open-window 候选。")
    if any(
        item.get("status") == "evaluate_payload_out_of_sync"
        for item in _as_list_of_dicts(writeback_preview.get("tasks"))
    ):
        notes.append("部分 task 的 evaluate payload 与当前 state 可能不同步；这类结果应先重新 evaluate-state 再决定是否推进。")
    return notes


def _classify_task(
    *,
    activation_needed: bool,
    eligible_for_state_activation: bool,
    only_formal_window_after_activation: bool,
    post_activation_still_blocked: bool,
    categorized: dict[str, list[str]],
    manual_fill_fields: list[str],
) -> str:
    if categorized["module"]:
        return "module_level_blocked"
    if categorized["requirement"]:
        return "requirement_relation_blocked"
    if categorized["content"] or categorized["other"] or manual_fill_fields:
        return "content_blocked"
    if not activation_needed and categorized["state"] == [FORMAL_WINDOW_CLOSED]:
        return "already_window_only"
    if eligible_for_state_activation and only_formal_window_after_activation:
        return "window_only_after_state_activation"
    if eligible_for_state_activation and not post_activation_still_blocked:
        return "state_activation_candidate"
    if activation_needed:
        return "post_activation_still_blocked"
    return "content_blocked"


def _categorize_blockers(blockers: list[str]) -> dict[str, list[str]]:
    buckets = {
        "requirement": [],
        "module": [],
        "content": [],
        "state": [],
        "other": [],
    }
    for blocker in blockers:
        if blocker.startswith(REQUIREMENT_PREFIX):
            buckets["requirement"].append(blocker)
        elif blocker.startswith("module:") or blocker in MODULE_BLOCKERS:
            buckets["module"].append(blocker)
        elif blocker in {IMPLEMENTATION_DOC_NOT_ACTIVE, FORMAL_WINDOW_CLOSED}:
            buckets["state"].append(blocker)
        elif blocker in {
            "doc:implementation_doc",
            "doc:design_doc",
            "gate:implementation_scope_unclear",
            "gate:required_tests_missing",
            "gate:acceptance_criteria_missing",
        } or blocker.startswith("policy:language_non_compliant"):
            buckets["content"].append(blocker)
        else:
            buckets["other"].append(blocker)
    return {key: _dedupe_strings(value) for key, value in buckets.items()}


def _group_blockers_by_task(items: Any) -> dict[str, set[str]]:
    output: dict[str, set[str]] = {}
    for item in _as_list_of_dicts(items):
        task_id = str(item.get("task_id", "")).strip()
        blocker = str(item.get("blocker", "")).strip()
        if not task_id or not blocker:
            continue
        output.setdefault(task_id, set()).add(blocker)
    return output


def _group_manual_fill_by_task(items: Any) -> dict[str, list[str]]:
    output: dict[str, list[str]] = {}
    for item in _as_list_of_dicts(items):
        task_id = str(item.get("task_id", "")).strip()
        if not task_id:
            continue
        output[task_id] = _dedupe_strings(_as_string_list(item.get("fields")))
    return output


def _normalize_entity_ids(
    *,
    entity_ids: list[str] | tuple[str, ...] | str | None,
    state: dict[str, Any],
) -> list[str]:
    subtasks = _as_dict(state.get("subtasks"))
    if entity_ids is None:
        return sorted(subtasks.keys())
    if isinstance(entity_ids, str):
        raw = [part.strip() for part in entity_ids.split(",") if part.strip()]
    else:
        raw = []
        for item in entity_ids:
            raw.extend(part.strip() for part in str(item).split(",") if part.strip())
    task_ids = _dedupe_strings(raw)
    missing = [task_id for task_id in task_ids if task_id not in subtasks]
    if missing:
        raise ValueError(f"entity-id 不是有效 task: {', '.join(missing)}")
    return task_ids


def _load_state(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("state 文件不是有效对象")
    return data


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


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _as_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        output: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                output.append(text)
        return output
    return []


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
