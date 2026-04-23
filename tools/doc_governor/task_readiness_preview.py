from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .requirement_link_suggestions import build_requirement_link_suggestions
from .task_readiness_plan import build_task_readiness_plan
from .task_remediation import build_task_remediation_plan


IMPLEMENTATION_CHINESE_HEADINGS = [
    "# 子任务实施文档",
    "## 3. 本轮实施目标",
    "## 5. 允许修改范围",
    "## 7. 测试与验证",
    "## 8. 完成判定",
]
DESIGN_CHINESE_HEADINGS = [
    "# 子任务设计文档",
    "## 3. 子任务目标",
    "## 5. 技术方案",
]


def build_task_readiness_preview(
    *,
    state_path: str | Path,
    evaluate_payload: dict[str, Any],
    entity_id: str | None = None,
) -> dict[str, Any]:
    readiness_plan = build_task_readiness_plan(
        state_path=state_path,
        evaluate_payload=evaluate_payload,
        entity_id=entity_id,
    )
    remediation_plan = build_task_remediation_plan(
        state_path=state_path,
        evaluate_payload=evaluate_payload,
        entity_id=entity_id,
    )
    requirement_suggestions = build_requirement_link_suggestions(
        state_path=state_path,
        entity_id=entity_id,
    )

    remediation_findings = {
        item["task_id"]: item
        for item in _as_list_of_dicts(remediation_plan.get("document_findings"))
        if item.get("task_id")
    }
    remediation_carry = {
        item["task_id"]: item
        for item in _as_list_of_dicts(remediation_plan.get("carry_over_candidates"))
        if item.get("task_id")
    }
    remediation_manual = {
        item["task_id"]: item
        for item in _as_list_of_dicts(remediation_plan.get("manual_fill_required"))
        if item.get("task_id")
    }
    remediation_blocking = {
        item["task_id"]: item
        for item in _as_list_of_dicts(remediation_plan.get("blocking_issues"))
        if item.get("task_id")
    }
    action_sequences = {
        item["task_id"]: item
        for item in _as_list_of_dicts(readiness_plan.get("task_action_sequences"))
        if item.get("task_id")
    }
    requirement_map = _build_requirement_preview_map(requirement_suggestions)

    selected_task_count = int(_as_dict(readiness_plan.get("summary")).get("selected_task_count", 0))
    requirement_seed_preview = _build_requirement_seed_preview(
        requirement_map=requirement_map,
        readiness_plan=readiness_plan,
    )
    candidate_task_previews = _build_candidate_task_previews(
        readiness_plan=readiness_plan,
        remediation_findings=remediation_findings,
        remediation_carry=remediation_carry,
        remediation_manual=remediation_manual,
        remediation_blocking=remediation_blocking,
        action_sequences=action_sequences,
        requirement_map=requirement_map,
    )
    deferred_tasks = _build_deferred_previews(
        readiness_plan=readiness_plan,
        remediation_blocking=remediation_blocking,
    )
    manual_confirmation_points = _build_manual_confirmation_points(
        readiness_plan=readiness_plan,
        requirement_seed_preview=requirement_seed_preview,
        candidate_task_previews=candidate_task_previews,
    )
    batch_rationale = _build_batch_rationale(
        readiness_plan=readiness_plan,
        candidate_task_previews=candidate_task_previews,
        deferred_tasks=deferred_tasks,
    )
    preview_actions = _build_preview_actions(
        requirement_seed_preview=requirement_seed_preview,
        candidate_task_previews=candidate_task_previews,
        deferred_tasks=deferred_tasks,
    )

    return {
        "summary": {
            "selected_entity_id": entity_id or "ALL",
            "selected_scope": str(_as_dict(readiness_plan.get("summary")).get("selected_scope", "")),
            "selected_task_count": selected_task_count,
            "requirement_seed_count": len(requirement_seed_preview),
            "candidate_task_preview_count": len(candidate_task_previews),
            "deferred_task_count": len(deferred_tasks),
            "manual_confirmation_count": len(manual_confirmation_points),
        },
        "requirement_seed_preview": requirement_seed_preview,
        "candidate_task_previews": candidate_task_previews,
        "manual_confirmation_points": manual_confirmation_points,
        "deferred_tasks": deferred_tasks,
        "batch_rationale": batch_rationale,
        "preview_actions": preview_actions,
        "confidence": _as_dict(readiness_plan.get("confidence")),
        "reasoning_notes": _build_reasoning_notes(
            readiness_plan=readiness_plan,
            remediation_plan=remediation_plan,
            requirement_seed_preview=requirement_seed_preview,
            candidate_task_previews=candidate_task_previews,
            deferred_tasks=deferred_tasks,
        ),
    }


def render_task_readiness_preview_markdown(payload: dict[str, Any]) -> str:
    summary = _as_dict(payload.get("summary"))
    lines = [
        "# 任务 readiness 修复预览",
        "",
        "## 摘要",
        f"- 选择范围: {summary.get('selected_scope', '')}",
        f"- 目标实体: {summary.get('selected_entity_id', '')}",
        f"- 纳入分析 task 数量: {summary.get('selected_task_count', 0)}",
        f"- requirement seed 预览数量: {summary.get('requirement_seed_count', 0)}",
        f"- 候选 task 预览数量: {summary.get('candidate_task_preview_count', 0)}",
        f"- 暂缓 task 数量: {summary.get('deferred_task_count', 0)}",
        "",
        "## requirement seed 预览",
    ]
    for item in _as_list_of_dicts(payload.get("requirement_seed_preview")):
        lines.append(
            f"- {item.get('task_id', '')}: {item.get('suggested_requirement_id', '')} | "
            f"需人工确认={bool(item.get('needs_manual_confirmation'))} | {item.get('reason', '')}"
        )

    lines.extend(["", "## 候选 task 预览"])
    for item in _as_list_of_dicts(payload.get("candidate_task_previews")):
        lines.append(f"- {item.get('task_id', '')}: {item.get('reason', '')}")
        carry = ", ".join(_as_string_list(item.get("carry_over_fields")))
        manual = ", ".join(_as_string_list(item.get("manual_fill_fields")))
        lines.append(f"  - 可迁移: {carry or '无'}")
        lines.append(f"  - 人工补充: {manual or '无'}")

    lines.extend(["", "## 暂缓对象"])
    for item in _as_list_of_dicts(payload.get("deferred_tasks")):
        lines.append(f"- {item.get('task_id', '')}: {item.get('reason', '')}")

    lines.extend(["", "## 批次说明"])
    batch = _as_dict(payload.get("batch_rationale"))
    lines.append(f"- 批次 task: {', '.join(_as_string_list(batch.get('task_ids'))) or '无'}")
    for reason in _as_string_list(batch.get("reasons")):
        lines.append(f"- {reason}")

    lines.extend(["", "## preview 动作"])
    for item in _as_list_of_dicts(payload.get("preview_actions")):
        lines.append(f"- {item.get('title', '')}: {item.get('detail', '')}")

    manual_items = _as_list_of_dicts(payload.get("manual_confirmation_points"))
    if manual_items:
        lines.extend(["", "## 需要人工确认"])
        for item in manual_items:
            lines.append(f"- {item.get('title', '')}: {item.get('reason', '')}")

    notes = payload.get("reasoning_notes")
    if isinstance(notes, list) and notes:
        lines.extend(["", "## 说明"])
        for note in notes:
            text = str(note).strip()
            if text:
                lines.append(f"- {text}")

    return "\n".join(lines) + "\n"


def write_task_readiness_preview_output(
    *,
    payload: dict[str, Any],
    output_path: str | Path,
    output_format: str,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "markdown":
        path.write_text(render_task_readiness_preview_markdown(payload), encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _build_requirement_preview_map(requirement_suggestions: dict[str, Any]) -> dict[str, dict[str, Any]]:
    preview_map: dict[str, dict[str, Any]] = {}
    for collection_name, status in (
        ("resolved_candidates", "resolved"),
        ("ambiguous_candidates", "ambiguous"),
        ("unresolved_tasks", "unresolved"),
    ):
        for item in _as_list_of_dicts(requirement_suggestions.get(collection_name)):
            task_id = str(item.get("task_id", "")).strip()
            if not task_id:
                continue
            preview_map[task_id] = {
                "status": status,
                "suggested_requirement_id": item.get("selected_requirement_id"),
                "candidate_requirement_ids": _as_string_list(item.get("candidate_requirement_ids")),
                "confidence": _as_dict(item.get("confidence")),
                "needs_manual_confirmation": bool(item.get("needs_manual_confirmation")),
                "reason": str(item.get("reason", "")).strip(),
            }
    return preview_map


def _build_requirement_seed_preview(
    *,
    requirement_map: dict[str, dict[str, Any]],
    readiness_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    previews: list[dict[str, Any]] = []
    module_by_task: dict[str, str] = {}
    for item in _as_list_of_dicts(readiness_plan.get("candidate_tasks")) + _as_list_of_dicts(readiness_plan.get("deferred_tasks")):
        task_id = str(item.get("task_id", "")).strip()
        module_id = str(item.get("module_id", "")).strip()
        if task_id:
            module_by_task[task_id] = module_id

    for task_id in sorted(requirement_map.keys()):
        item = requirement_map[task_id]
        if item.get("status") == "resolved" and not bool(item.get("needs_manual_confirmation")):
            continue
        suggested_requirement_id = str(item.get("suggested_requirement_id") or "").strip() or None
        seed_preview = None
        if suggested_requirement_id:
            seed_preview = {
                "requirement_id": suggested_requirement_id,
                "task_ids_append": [task_id],
                "module_ids_context": [module_by_task.get(task_id)] if module_by_task.get(task_id) else [],
            }
        previews.append(
            {
                "task_id": task_id,
                "module_id": module_by_task.get(task_id, ""),
                "suggested_requirement_id": suggested_requirement_id,
                "candidate_requirement_ids": _as_string_list(item.get("candidate_requirement_ids")),
                "confidence": _as_dict(item.get("confidence")),
                "needs_manual_confirmation": bool(item.get("needs_manual_confirmation")),
                "seed_entry_preview": seed_preview,
                "reason": str(item.get("reason", "")).strip(),
            }
        )
    return previews


def _build_candidate_task_previews(
    *,
    readiness_plan: dict[str, Any],
    remediation_findings: dict[str, dict[str, Any]],
    remediation_carry: dict[str, dict[str, Any]],
    remediation_manual: dict[str, dict[str, Any]],
    remediation_blocking: dict[str, dict[str, Any]],
    action_sequences: dict[str, dict[str, Any]],
    requirement_map: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    previews: list[dict[str, Any]] = []
    for item in _as_list_of_dicts(readiness_plan.get("candidate_tasks")):
        task_id = str(item.get("task_id", "")).strip()
        if not task_id:
            continue
        finding = _as_dict(remediation_findings.get(task_id))
        design_doc = _as_dict(finding.get("design_doc"))
        implementation_doc = _as_dict(finding.get("implementation_doc"))
        carry = _as_dict(remediation_carry.get(task_id))
        manual = _as_dict(remediation_manual.get(task_id))
        blocking = _as_dict(remediation_blocking.get(task_id))
        requirement_info = _as_dict(requirement_map.get(task_id))
        previews.append(
            {
                "task_id": task_id,
                "module_id": str(item.get("module_id", "")).strip(),
                "suggested_requirement_id": requirement_info.get("suggested_requirement_id"),
                "reason": str(item.get("reason", "")).strip(),
                "heading_replacements": {
                    "design_doc": DESIGN_CHINESE_HEADINGS if _needs_design_replacement(design_doc) else [],
                    "implementation_doc": IMPLEMENTATION_CHINESE_HEADINGS if _needs_implementation_replacement(implementation_doc) else [],
                },
                "cleanup_old_status_semantics": bool(
                    design_doc.get("old_status_semantics") or implementation_doc.get("old_status_semantics")
                ),
                "carry_over_fields": _as_string_list(carry.get("fields")),
                "carry_over_notes": _as_string_list(carry.get("notes")),
                "manual_fill_fields": _as_string_list(manual.get("fields")),
                "module_level_blockers": _as_string_list(blocking.get("module_inherited_blockers")),
                "minimal_change_skeleton": _as_list_of_dicts(_as_dict(action_sequences.get(task_id)).get("actions")),
            }
        )
    return previews


def _build_deferred_previews(
    *,
    readiness_plan: dict[str, Any],
    remediation_blocking: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    previews: list[dict[str, Any]] = []
    for item in _as_list_of_dicts(readiness_plan.get("deferred_tasks")):
        task_id = str(item.get("task_id", "")).strip()
        if not task_id:
            continue
        blocking = _as_dict(remediation_blocking.get(task_id))
        previews.append(
            {
                "task_id": task_id,
                "module_id": str(item.get("module_id", "")).strip(),
                "reason": str(item.get("reason", "")).strip(),
                "module_inherited_blockers": _as_string_list(blocking.get("module_inherited_blockers")),
            }
        )
    return previews


def _build_manual_confirmation_points(
    *,
    readiness_plan: dict[str, Any],
    requirement_seed_preview: list[dict[str, Any]],
    candidate_task_previews: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    points = [
        {"title": item.get("title", ""), "reason": item.get("reason", "")}
        for item in _as_list_of_dicts(readiness_plan.get("needs_manual_confirmation"))
        if item.get("title")
    ]
    for item in requirement_seed_preview:
        if bool(item.get("needs_manual_confirmation")):
            points.append(
                {
                    "title": f"{item.get('task_id', '')} 的 requirement seed 仍需人工确认",
                    "reason": "当前 preview 只输出建议 seed，不会直接写回 requirement 关系。",
                }
            )
    for item in candidate_task_previews:
        manual_fields = _as_string_list(item.get("manual_fill_fields"))
        if manual_fields:
            points.append(
                {
                    "title": f"{item.get('task_id', '')} 仍需人工补字段",
                    "reason": "、".join(manual_fields) + " 目前只能给出预览骨架，不能自动补正文。",
                }
            )
    return _dedupe_dict_items(points)


def _build_batch_rationale(
    *,
    readiness_plan: dict[str, Any],
    candidate_task_previews: list[dict[str, Any]],
    deferred_tasks: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_ids = [item["task_id"] for item in candidate_task_previews]
    reasons = [
        "这一批 task 具有更低的模块继承 blocker 成本，更适合先验证 readiness 修复闭环。",
        "这一批同时覆盖了 pilot candidate 与旧模板样本，便于对照不同整改路径。",
    ]
    if deferred_tasks:
        reasons.append("存在模块继承 blocker 的 task 暂不纳入首批，避免把模块级问题误收敛成 task 局部问题。")
    return {
        "task_ids": candidate_ids,
        "reasons": reasons,
        "why_this_batch": "先用首批最低成本样本验证 requirement seed + remediation preview 的执行闭环。",
        "deferred_highlights": [
            {"task_id": item["task_id"], "reason": item["reason"]}
            for item in deferred_tasks[:5]
        ],
    }


def _build_preview_actions(
    *,
    requirement_seed_preview: list[dict[str, Any]],
    candidate_task_previews: list[dict[str, Any]],
    deferred_tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if requirement_seed_preview:
        actions.append(
            {
                "title": "预览 requirement seed",
                "detail": ", ".join(item["task_id"] for item in requirement_seed_preview[:8]),
            }
        )
    if candidate_task_previews:
        actions.append(
            {
                "title": "预览首批候选 task 骨架",
                "detail": ", ".join(item["task_id"] for item in candidate_task_previews[:8]),
            }
        )
    if deferred_tasks:
        actions.append(
            {
                "title": "保留 deferred task 在模块层或后续批次",
                "detail": ", ".join(item["task_id"] for item in deferred_tasks[:8]),
            }
        )
    return actions


def _build_reasoning_notes(
    *,
    readiness_plan: dict[str, Any],
    remediation_plan: dict[str, Any],
    requirement_seed_preview: list[dict[str, Any]],
    candidate_task_previews: list[dict[str, Any]],
    deferred_tasks: list[dict[str, Any]],
) -> list[str]:
    notes = [
        "本能力是 preview 层，只把规划结果转成可执行预览，不自动修文档，也不写回 state。",
        "requirement seed preview 仍然只是建议，不会在 preview 阶段直接变成正式 requirement 关系。",
    ]
    notes.extend(
        str(item).strip()
        for item in readiness_plan.get("reasoning_notes", [])
        if str(item).strip()
    )
    notes.extend(
        str(item).strip()
        for item in remediation_plan.get("reasoning_notes", [])
        if str(item).strip()
    )
    if candidate_task_previews:
        notes.append("候选 task 的最小变更骨架适合直接作为下一步 Codex 执行输入，但仍需人工选择是否实际写入。")
    if deferred_tasks:
        notes.append("deferred task 不是永久跳过，而是当前不纳入首批修复样本。")
    if any(bool(item.get("needs_manual_confirmation")) for item in requirement_seed_preview):
        notes.append("当前 requirement 映射仍保留 needs_manual_confirmation，不会被 preview 层强行拍板。")
    return _dedupe_strings(notes)


def _needs_design_replacement(design_doc: dict[str, Any]) -> bool:
    return bool(design_doc.get("template_like")) or int(design_doc.get("language_violation_count", 0)) > 0


def _needs_implementation_replacement(implementation_doc: dict[str, Any]) -> bool:
    return bool(implementation_doc.get("template_like")) or int(
        implementation_doc.get("language_violation_count", 0)
    ) > 0


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list_of_dicts(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return _dedupe_strings([str(item).strip() for item in value if str(item).strip()])


def _dedupe_strings(items: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        ordered.append(text)
        seen.add(text)
    return ordered


def _dedupe_dict_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        title = str(item.get("title", "")).strip()
        reason = str(item.get("reason", "")).strip()
        key = (title, reason)
        if not title or key in seen:
            continue
        ordered.append({"title": title, "reason": reason})
        seen.add(key)
    return ordered
