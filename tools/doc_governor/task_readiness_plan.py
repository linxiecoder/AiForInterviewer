from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .requirement_link_suggestions import build_requirement_link_suggestions
from .task_adaptation import build_task_adaptation_plan
from .task_remediation import build_task_remediation_plan


def build_task_readiness_plan(
    *,
    state_path: str | Path,
    evaluate_payload: dict[str, Any],
    entity_id: str | None = None,
) -> dict[str, Any]:
    adaptation_plan = build_task_adaptation_plan(
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

    remediation_findings = _as_list_of_dicts(remediation_plan.get("document_findings"))
    selected_task_ids = [item["task_id"] for item in remediation_findings if item.get("task_id")]
    remediation_blocking_map = {
        item["task_id"]: item
        for item in _as_list_of_dicts(remediation_plan.get("blocking_issues"))
        if item.get("task_id")
    }
    remediation_manual_map = {
        item["task_id"]: item
        for item in _as_list_of_dicts(remediation_plan.get("manual_fill_required"))
        if item.get("task_id")
    }
    remediation_carry_map = {
        item["task_id"]: item
        for item in _as_list_of_dicts(remediation_plan.get("carry_over_candidates"))
        if item.get("task_id")
    }
    remediation_finding_map = {
        item["task_id"]: item
        for item in remediation_findings
        if item.get("task_id")
    }
    remediation_sample_map = {
        item["task_id"]: item
        for item in _as_list_of_dicts(remediation_plan.get("sample_tasks"))
        if item.get("task_id")
    }
    adaptation_candidate_map = {
        item["task_id"]: item
        for item in _as_list_of_dicts(adaptation_plan.get("candidate_tasks"))
        if item.get("task_id")
    }
    requirement_map = _build_requirement_status_map(requirement_suggestions)
    evaluate_subtasks = _as_dict(evaluate_payload.get("subtasks"))

    global_prerequisites = _build_global_prerequisites(
        selected_task_ids=selected_task_ids,
        requirement_suggestions=requirement_suggestions,
        adaptation_plan=adaptation_plan,
        evaluate_subtasks=evaluate_subtasks,
    )
    module_level_actions = _build_module_level_actions(
        adaptation_plan=adaptation_plan,
        remediation_blocking_map=remediation_blocking_map,
    )
    task_action_sequences = _build_task_action_sequences(
        selected_task_ids=selected_task_ids,
        requirement_map=requirement_map,
        remediation_blocking_map=remediation_blocking_map,
        remediation_manual_map=remediation_manual_map,
        remediation_finding_map=remediation_finding_map,
    )
    candidate_tasks, deferred_tasks = _rank_tasks(
        selected_task_ids=selected_task_ids,
        requirement_map=requirement_map,
        remediation_blocking_map=remediation_blocking_map,
        remediation_manual_map=remediation_manual_map,
        remediation_carry_map=remediation_carry_map,
        remediation_finding_map=remediation_finding_map,
        remediation_sample_map=remediation_sample_map,
        adaptation_candidate_map=adaptation_candidate_map,
        task_action_sequences=task_action_sequences,
    )
    recommended_order = _build_recommended_order(
        global_prerequisites=global_prerequisites,
        module_level_actions=module_level_actions,
        remediation_plan=remediation_plan,
    )
    confidence = _build_overall_confidence(
        adaptation_plan=adaptation_plan,
        remediation_plan=remediation_plan,
        requirement_suggestions=requirement_suggestions,
    )
    needs_manual_confirmation = _build_manual_confirmation_items(
        global_prerequisites=global_prerequisites,
        module_level_actions=module_level_actions,
        candidate_tasks=candidate_tasks,
        deferred_tasks=deferred_tasks,
        requirement_suggestions=requirement_suggestions,
        remediation_plan=remediation_plan,
    )
    reasoning_notes = _build_reasoning_notes(
        adaptation_plan=adaptation_plan,
        remediation_plan=remediation_plan,
        requirement_suggestions=requirement_suggestions,
        candidate_tasks=candidate_tasks,
        deferred_tasks=deferred_tasks,
    )

    return {
        "summary": {
            "selected_entity_id": entity_id or "ALL",
            "selected_scope": str(remediation_plan.get("summary", {}).get("selected_scope", "")),
            "selected_task_count": len(selected_task_ids),
            "global_prerequisite_count": len(global_prerequisites),
            "module_action_count": len(module_level_actions),
            "candidate_task_count": len(candidate_tasks),
            "deferred_task_count": len(deferred_tasks),
        },
        "global_prerequisites": global_prerequisites,
        "module_level_actions": module_level_actions,
        "candidate_tasks": candidate_tasks,
        "deferred_tasks": deferred_tasks,
        "recommended_order": recommended_order,
        "task_action_sequences": task_action_sequences,
        "confidence": confidence,
        "needs_manual_confirmation": needs_manual_confirmation,
        "reasoning_notes": reasoning_notes,
    }


def render_task_readiness_markdown(payload: dict[str, Any]) -> str:
    summary = _as_dict(payload.get("summary"))
    lines = [
        "# 任务 readiness 规划",
        "",
        "## 摘要",
        f"- 选择范围: {summary.get('selected_scope', '')}",
        f"- 目标实体: {summary.get('selected_entity_id', '')}",
        f"- 纳入分析 task 数量: {summary.get('selected_task_count', 0)}",
        f"- 全局前置数量: {summary.get('global_prerequisite_count', 0)}",
        f"- 模块层动作数量: {summary.get('module_action_count', 0)}",
        f"- 首批候选 task 数量: {summary.get('candidate_task_count', 0)}",
        f"- 暂缓 task 数量: {summary.get('deferred_task_count', 0)}",
        "",
        "## 主建议顺序",
    ]
    for item in _as_list_of_dicts(payload.get("recommended_order")):
        lines.append(f"- {item.get('step', '?')}. {item.get('title', '')}: {item.get('reason', '')}")

    lines.extend(["", "## 全局前置"])
    for item in _as_list_of_dicts(payload.get("global_prerequisites")):
        lines.append(f"- {item.get('title', '')}: {item.get('reason', '')}")

    lines.extend(["", "## 模块层动作"])
    for item in _as_list_of_dicts(payload.get("module_level_actions")):
        blockers = ", ".join(_as_string_list(item.get("blocker_refs")))
        lines.append(f"- {item.get('module_id', '')}: {blockers} | {item.get('reason', '')}")

    lines.extend(["", "## 首批候选 task"])
    for item in _as_list_of_dicts(payload.get("candidate_tasks")):
        lines.append(f"- {item.get('task_id', '')}: {item.get('reason', '')}")

    lines.extend(["", "## 暂缓对象"])
    for item in _as_list_of_dicts(payload.get("deferred_tasks")):
        lines.append(f"- {item.get('task_id', '')}: {item.get('reason', '')}")

    lines.extend(["", "## task 动作序列"])
    for item in _as_list_of_dicts(payload.get("task_action_sequences")):
        lines.append(f"- {item.get('task_id', '')}:")
        for action in _as_list_of_dicts(item.get("actions")):
            lines.append(f"  - {action.get('step', '?')}. {action.get('title', '')}: {action.get('reason', '')}")

    manual_items = _as_list_of_dicts(payload.get("needs_manual_confirmation"))
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


def write_task_readiness_output(
    *,
    payload: dict[str, Any],
    output_path: str | Path,
    output_format: str,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "markdown":
        path.write_text(render_task_readiness_markdown(payload), encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _build_requirement_status_map(requirement_suggestions: dict[str, Any]) -> dict[str, dict[str, Any]]:
    task_map: dict[str, dict[str, Any]] = {}
    for item in _as_list_of_dicts(requirement_suggestions.get("resolved_candidates")):
        task_id = str(item.get("task_id", "")).strip()
        if not task_id:
            continue
        task_map[task_id] = {
            "status": "manual_confirmation" if bool(item.get("needs_manual_confirmation")) else "resolved",
            "selected_requirement_id": item.get("selected_requirement_id"),
            "candidate_requirement_ids": _as_string_list(item.get("candidate_requirement_ids")),
            "reason": str(item.get("reason", "")).strip(),
            "confidence": _as_dict(item.get("confidence")),
        }
    for item in _as_list_of_dicts(requirement_suggestions.get("ambiguous_candidates")):
        task_id = str(item.get("task_id", "")).strip()
        if not task_id:
            continue
        task_map[task_id] = {
            "status": "ambiguous",
            "selected_requirement_id": None,
            "candidate_requirement_ids": _as_string_list(item.get("candidate_requirement_ids")),
            "reason": str(item.get("reason", "")).strip(),
            "confidence": _as_dict(item.get("confidence")),
        }
    for item in _as_list_of_dicts(requirement_suggestions.get("unresolved_tasks")):
        task_id = str(item.get("task_id", "")).strip()
        if not task_id:
            continue
        task_map[task_id] = {
            "status": "unresolved",
            "selected_requirement_id": None,
            "candidate_requirement_ids": _as_string_list(item.get("candidate_requirement_ids")),
            "reason": str(item.get("reason", "")).strip(),
            "confidence": _as_dict(item.get("confidence")),
        }
    return task_map


def _build_global_prerequisites(
    *,
    selected_task_ids: list[str],
    requirement_suggestions: dict[str, Any],
    adaptation_plan: dict[str, Any],
    evaluate_subtasks: dict[str, Any],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    unresolved_ids = [
        item["task_id"]
        for item in _as_list_of_dicts(requirement_suggestions.get("unresolved_tasks"))
        if item.get("task_id")
    ]
    manual_ids = [
        item["task_id"]
        for item in _as_list_of_dicts(requirement_suggestions.get("resolved_candidates"))
        if item.get("task_id") and bool(item.get("needs_manual_confirmation"))
    ] + [
        item["task_id"]
        for item in _as_list_of_dicts(requirement_suggestions.get("ambiguous_candidates"))
        if item.get("task_id")
    ]
    requirement_affected = _dedupe_strings(unresolved_ids + manual_ids)
    if requirement_affected:
        items.append(
            {
                "prerequisite_id": "requirement_relation",
                "title": "先确认 requirement 映射",
                "reason": f"{len(requirement_affected)} 个 task 的 requirement 关系仍需人工确认或证据不足，不能跳过这一步直接推进 implementation readiness。",
                "affected_task_ids": requirement_affected,
                "confidence": _as_dict(requirement_suggestions.get("confidence")),
                "needs_manual_confirmation": True,
            }
        )

    activation_affected: list[str] = []
    for task_id in selected_task_ids:
        blocker_refs = _as_string_list(_as_dict(_as_dict(evaluate_subtasks.get(task_id)).get("derived")).get("blocker_refs"))
        if "gate:implementation_doc_not_active" in blocker_refs or "policy:formal_window_closed" in blocker_refs:
            activation_affected.append(task_id)
    activation_affected = _dedupe_strings(activation_affected)
    if activation_affected:
        items.append(
            {
                "prerequisite_id": "activation_window_state",
                "title": "最后再处理状态位和开窗",
                "reason": f"{len(activation_affected)} 个 task 当前仍受 implementation_doc_state 或 formal_window_open 影响，但这类状态位应放在内容整改之后处理。",
                "affected_task_ids": activation_affected,
                "confidence": {"level": "high", "score": 0.9},
                "needs_manual_confirmation": False,
            }
        )

    if not items and _as_list_of_dicts(adaptation_plan.get("global_findings")):
        for item in _as_list_of_dicts(adaptation_plan.get("global_findings"))[:2]:
            items.append(
                {
                    "prerequisite_id": str(item.get("focus", "")).strip() or "global_precondition",
                    "title": str(item.get("title", "")).strip() or "保留全局前置解释",
                    "reason": str(item.get("reason", "")).strip(),
                    "affected_task_ids": _as_string_list(item.get("affected_task_ids")),
                    "confidence": _as_dict(item.get("confidence")),
                    "needs_manual_confirmation": bool(item.get("needs_manual_confirmation")),
                }
            )
    return items


def _build_module_level_actions(
    *,
    adaptation_plan: dict[str, Any],
    remediation_blocking_map: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    findings = _as_list_of_dicts(adaptation_plan.get("module_level_findings"))
    actions: list[dict[str, Any]] = []
    for item in findings:
        module_id = str(item.get("module_id", "")).strip()
        affected_task_ids = _as_string_list(item.get("affected_task_ids"))
        if not affected_task_ids:
            affected_task_ids = sorted(
                task_id
                for task_id, blocking in remediation_blocking_map.items()
                if module_id and f"module:{module_id}" in _as_string_list(blocking.get("module_inherited_blockers"))
            )
        actions.append(
            {
                "module_id": module_id,
                "blocker_refs": _as_string_list(item.get("blocker_refs")),
                "affected_task_ids": affected_task_ids,
                "reason": f"这些 blocker 已经在模块层成立，先收口模块文档或共享契约，再回到 task 级整改更稳。",
                "recommended_action": "先在模块层解释和收口 blocker，再推进受影响 task。",
                "confidence": _as_dict(item.get("confidence")),
            }
        )
    return actions


def _build_task_action_sequences(
    *,
    selected_task_ids: list[str],
    requirement_map: dict[str, dict[str, Any]],
    remediation_blocking_map: dict[str, dict[str, Any]],
    remediation_manual_map: dict[str, dict[str, Any]],
    remediation_finding_map: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    sequences: list[dict[str, Any]] = []
    for task_id in selected_task_ids:
        requirement_info = requirement_map.get(task_id, {})
        blocking = remediation_blocking_map.get(task_id, {})
        manual_fill = _as_string_list(_as_dict(remediation_manual_map.get(task_id)).get("fields"))
        findings = remediation_finding_map.get(task_id, {})
        implementation_doc = _as_dict(findings.get("implementation_doc"))
        design_doc = _as_dict(findings.get("design_doc"))
        actions: list[dict[str, Any]] = []
        step = 1

        if requirement_info.get("status") in {"manual_confirmation", "ambiguous", "unresolved"}:
            actions.append(
                {
                    "step": step,
                    "title": "先确认 requirement 映射",
                    "reason": str(requirement_info.get("reason", "")).strip() or "当前 requirement 关系仍未稳定，先确认再做 task 级整改更稳。",
                }
            )
            step += 1

        structure_needed = bool(
            implementation_doc.get("template_like")
            or design_doc.get("template_like")
            or int(implementation_doc.get("language_violation_count", 0)) > 0
            or int(design_doc.get("language_violation_count", 0)) > 0
        )
        if structure_needed:
            actions.append(
                {
                    "step": step,
                    "title": "先修标题/章节结构与中文规则",
                    "reason": "旧模板和英文标题问题会放大后续字段缺口，应先迁到当前有效结构。",
                }
            )
            step += 1

        if bool(implementation_doc.get("old_status_semantics")) or bool(design_doc.get("old_status_semantics")):
            actions.append(
                {
                    "step": step,
                    "title": "清理旧状态语义",
                    "reason": "旧状态口径不能继续充当当前 readiness 真值。",
                }
            )
            step += 1

        for field_name, title, reason in (
            ("allowed_modify_paths", "补允许修改范围", "这是 implementation scope 的最小必需字段。"),
            ("required_tests", "补测试要求", "这是进入 implementation_ready 的硬门槛之一。"),
            ("acceptance_criteria", "补完成判定", "没有 acceptance criteria 就没有收口标准。"),
            ("design_key_sections", "必要时补 design 文档关键段落", "design 文档仍为模板或缺关键段落时再补。"),
        ):
            if field_name in manual_fill:
                actions.append({"step": step, "title": title, "reason": reason})
                step += 1

        if _as_string_list(blocking.get("module_inherited_blockers")):
            actions.append(
                {
                    "step": step,
                    "title": "将模块 blocker 保留在模块层处理",
                    "reason": "这类问题不能靠单个 task 文档整改独立消除。",
                }
            )
            step += 1

        other_blockers = _as_string_list(blocking.get("other_blockers"))
        if "gate:implementation_doc_not_active" in other_blockers or "policy:formal_window_closed" in other_blockers:
            actions.append(
                {
                    "step": step,
                    "title": "最后再动状态位和开窗",
                    "reason": "状态位和 formal window 应放在内容已满足最小条件之后处理。",
                }
            )
            step += 1

        if not actions:
            actions.append(
                {
                    "step": 1,
                    "title": "当前 task 已接近 readiness",
                    "reason": "当前未发现新的 task 级整改动作，可转向正式状态或其他外部阻断判断。",
                }
            )

        sequences.append({"task_id": task_id, "actions": actions})
    return sequences


def _rank_tasks(
    *,
    selected_task_ids: list[str],
    requirement_map: dict[str, dict[str, Any]],
    remediation_blocking_map: dict[str, dict[str, Any]],
    remediation_manual_map: dict[str, dict[str, Any]],
    remediation_carry_map: dict[str, dict[str, Any]],
    remediation_finding_map: dict[str, dict[str, Any]],
    remediation_sample_map: dict[str, dict[str, Any]],
    adaptation_candidate_map: dict[str, dict[str, Any]],
    task_action_sequences: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sequence_map = {item["task_id"]: item for item in task_action_sequences if item.get("task_id")}
    ranked: list[dict[str, Any]] = []

    for task_id in selected_task_ids:
        blocking = remediation_blocking_map.get(task_id, {})
        manual_fields = _as_string_list(_as_dict(remediation_manual_map.get(task_id)).get("fields"))
        carry_fields = _as_string_list(_as_dict(remediation_carry_map.get(task_id)).get("fields"))
        findings = remediation_finding_map.get(task_id, {})
        sample_info = remediation_sample_map.get(task_id, {})
        adaptation_info = adaptation_candidate_map.get(task_id, {})
        requirement_info = requirement_map.get(task_id, {})

        module_inherited = _as_string_list(blocking.get("module_inherited_blockers"))
        score = 100
        reason_bits: list[str] = []
        defer_reason = ""

        if requirement_info.get("status") == "unresolved":
            score -= 40
            defer_reason = "当前 requirement 证据不足，不适合列入首批打样。"
        elif requirement_info.get("status") in {"manual_confirmation", "ambiguous"}:
            score -= 8
            reason_bits.append("requirement 关系已有倾向性候选，可先带着人工确认推进")
        else:
            reason_bits.append("requirement 关系相对更稳定")

        if module_inherited:
            score -= 35
            defer_reason = "当前仍受模块继承 blocker 拖累，不值得作为首批 task 样本。"
            reason_bits.append("存在模块继承 blocker")
        else:
            score += 8
            reason_bits.append("没有额外模块继承 blocker")

        design_doc = _as_dict(findings.get("design_doc"))
        implementation_doc = _as_dict(findings.get("implementation_doc"))
        if not bool(design_doc.get("template_like")):
            score += 8
            reason_bits.append("design 文档较完整")
        else:
            score -= 10
            reason_bits.append("design 文档仍偏模板")

        if bool(implementation_doc.get("template_like")):
            score -= 6
            reason_bits.append("implementation 文档仍需迁移")

        score -= len(manual_fields) * 6
        score += len(carry_fields) * 3
        if sample_info.get("example_kind") == "pilot_candidate":
            score += 10
        elif sample_info.get("example_kind") == "old_template_case":
            score += 1
        if adaptation_info:
            score += int(adaptation_info.get("score", 0)) // 10

        ranked.append(
            {
                "task_id": task_id,
                "module_id": str(findings.get("module_id", "")).strip(),
                "score": score,
                "reason_bits": _dedupe_strings(reason_bits),
                "defer_reason": defer_reason,
                "requirement_info": requirement_info,
                "action_sequence": _as_dict(sequence_map.get(task_id)),
            }
        )

    ranked.sort(key=lambda item: (-int(item["score"]), str(item["task_id"])))
    candidate_tasks: list[dict[str, Any]] = []
    deferred_tasks: list[dict[str, Any]] = []

    for item in ranked:
        task_id = item["task_id"]
        requirement_info = _as_dict(item.get("requirement_info"))
        candidate_entry = {
            "task_id": task_id,
            "module_id": item["module_id"],
            "selected_requirement_id": requirement_info.get("selected_requirement_id"),
            "requirement_status": requirement_info.get("status", "unknown"),
            "reason": _candidate_reason_text(task_id=task_id, item=item),
            "confidence": _candidate_confidence(item),
            "minimal_action_count": len(_as_list_of_dicts(_as_dict(item.get("action_sequence")).get("actions"))),
        }
        if item["defer_reason"]:
            deferred_tasks.append(
                {
                    "task_id": task_id,
                    "module_id": item["module_id"],
                    "reason": item["defer_reason"],
                    "confidence": _candidate_confidence(item),
                }
            )
            continue
        if len(candidate_tasks) < 3:
            candidate_tasks.append(candidate_entry)
        else:
            deferred_tasks.append(
                {
                    "task_id": task_id,
                    "module_id": item["module_id"],
                    "reason": "当前不属于首批最低成本样本，可在前一批打样结果稳定后再推进。",
                    "confidence": _candidate_confidence(item),
                }
            )
    return candidate_tasks, deferred_tasks


def _candidate_reason_text(*, task_id: str, item: dict[str, Any]) -> str:
    reason_bits = _as_string_list(item.get("reason_bits"))
    if item.get("defer_reason"):
        return str(item.get("defer_reason"))
    if task_id.endswith("09_03") or task_id == "ST09_03":
        return "自身文档缺口更少，且没有额外模块继承 blocker，更适合先打样。"
    if task_id == "ST01_01":
        return "虽然仍是旧模板样本，但它能代表最典型的 implementation 迁移路径，适合作为首批对照样本。"
    if reason_bits:
        return "；".join(reason_bits[:3]) + "。"
    return "当前属于相对更适合进入首批 readiness 打样的 task。"


def _candidate_confidence(item: dict[str, Any]) -> dict[str, Any]:
    score = float(item.get("score", 0))
    normalized = max(0.2, min(0.92, round(score / 100, 2)))
    if normalized >= 0.8:
        level = "high"
    elif normalized >= 0.55:
        level = "medium"
    else:
        level = "low"
    return {"level": level, "score": normalized}


def _build_recommended_order(
    *,
    global_prerequisites: list[dict[str, Any]],
    module_level_actions: list[dict[str, Any]],
    remediation_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    summary = _as_dict(remediation_plan.get("summary"))
    order: list[dict[str, Any]] = []
    step = 1

    if any(item.get("prerequisite_id") == "requirement_relation" for item in global_prerequisites):
        order.append(
            {
                "step": step,
                "title": "先确认 requirement 映射",
                "reason": "先把 task 归属 requirement 的问题确认下来，后续 task 级整改才有稳定上下文。",
            }
        )
        step += 1

    if int(summary.get("implementation_template_task_count", 0)) > 0 or int(summary.get("language_issue_task_count", 0)) > 0:
        order.append(
            {
                "step": step,
                "title": "再迁移 implementation 文档结构与中文规则",
                "reason": "这是当前最主要的共性 blocker，先处理它能同时降低 template、language 和结构类缺口。",
            }
        )
        step += 1

    if int(summary.get("manual_fill_task_count", 0)) > 0:
        order.append(
            {
                "step": step,
                "title": "再补 scope / tests / acceptance",
                "reason": "这些字段直接决定 implementation_ready 是否能通过，不适合继续后置。",
            }
        )
        step += 1

    if int(summary.get("design_template_task_count", 0)) > 0:
        order.append(
            {
                "step": step,
                "title": "必要时补 design 文档关键段落",
                "reason": "只在 design 文档仍为模板或缺关键段落时补，不做无差别回写。",
            }
        )
        step += 1

    if module_level_actions:
        order.append(
            {
                "step": step,
                "title": "处理模块 blocker",
                "reason": "受模块继承 blocker 影响的 task 不值得直接进入首批打样，应先收口模块层问题。",
            }
        )
        step += 1

    if any(item.get("prerequisite_id") == "activation_window_state" for item in global_prerequisites):
        order.append(
            {
                "step": step,
                "title": "最后再动状态位和开窗",
                "reason": "implementation_doc_state 与 formal window 应放在内容和关系问题处理完之后。",
            }
        )

    if not order:
        order.append(
            {
                "step": 1,
                "title": "当前范围内未发现新的 readiness 规划动作",
                "reason": "所选 task 已经没有明显的全局、模块或 task 级规划缺口。",
            }
        )
    return order


def _build_overall_confidence(
    *,
    adaptation_plan: dict[str, Any],
    remediation_plan: dict[str, Any],
    requirement_suggestions: dict[str, Any],
) -> dict[str, Any]:
    scores = []
    for payload in (adaptation_plan, remediation_plan, requirement_suggestions):
        confidence = _as_dict(payload.get("confidence"))
        if "score" in confidence:
            scores.append(float(confidence.get("score", 0.0)))
    if not scores:
        return {"level": "low", "score": 0.2}
    score = round(sum(scores) / len(scores), 2)
    if score >= 0.8:
        level = "high"
    elif score >= 0.55:
        level = "medium"
    else:
        level = "low"
    return {"level": level, "score": score}


def _build_manual_confirmation_items(
    *,
    global_prerequisites: list[dict[str, Any]],
    module_level_actions: list[dict[str, Any]],
    candidate_tasks: list[dict[str, Any]],
    deferred_tasks: list[dict[str, Any]],
    requirement_suggestions: dict[str, Any],
    remediation_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for prereq in global_prerequisites:
        if bool(prereq.get("needs_manual_confirmation")):
            items.append({"title": prereq.get("title", ""), "reason": prereq.get("reason", "")})
    for item in module_level_actions:
        items.append(
            {
                "title": f"模块 {item.get('module_id', '')} blocker 需模块层确认",
                "reason": f"{', '.join(_as_string_list(item.get('affected_task_ids'))[:8])} 不应仅靠 task 文档调整来消除模块级缺口。",
            }
        )
    for item in _as_list_of_dicts(remediation_plan.get("needs_manual_confirmation")):
        items.append({"title": item.get("title", ""), "reason": item.get("reason", "")})
    for item in candidate_tasks + deferred_tasks:
        if item.get("requirement_status") in {"manual_confirmation", "ambiguous"}:
            items.append(
                {
                    "title": f"{item.get('task_id', '')} 的 requirement 候选仍需人工确认",
                    "reason": "当前已有倾向性候选，但还不能直接视为正式真值。",
                }
            )
    if not items and int(_as_dict(requirement_suggestions.get("summary")).get("manual_confirmation_count", 0)) > 0:
        items.append(
            {
                "title": "部分 requirement 建议仍需人工确认",
                "reason": "当前 planner 只读输出保留了不确定性，没有自动把建议写回 state。",
            }
        )
    return _dedupe_dict_items(items)


def _build_reasoning_notes(
    *,
    adaptation_plan: dict[str, Any],
    remediation_plan: dict[str, Any],
    requirement_suggestions: dict[str, Any],
    candidate_tasks: list[dict[str, Any]],
    deferred_tasks: list[dict[str, Any]],
) -> list[str]:
    notes = [
        "本聚合器是只读 readiness planner，只汇总现有 gate 和 planner 输出，不改文档、不写回 state。",
        "候选 task 的动作序列是最小推进顺序，不等于自动修复脚本。",
    ]
    notes.extend(
        str(item).strip()
        for item in remediation_plan.get("reasoning_notes", [])
        if str(item).strip()
    )
    notes.extend(
        str(item).strip()
        for item in adaptation_plan.get("reasoning_notes", [])
        if str(item).strip()
    )
    if int(_as_dict(requirement_suggestions.get("summary")).get("manual_confirmation_count", 0)) > 0:
        notes.append("requirement 链接建议仍可能保留 needs_manual_confirmation，不会在聚合层被强行拍板。")
    if deferred_tasks:
        notes.append("被暂缓的 task 不代表永远不做，只代表当前不属于首批最低成本样本。")
    if candidate_tasks:
        notes.append("首批候选 task 优先考虑更少的模块继承 blocker、更低的人工补字段成本和更高的可迁移内容比例。")
    return _dedupe_strings(notes)


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
