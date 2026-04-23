from __future__ import annotations

import json
from pathlib import Path
from typing import Any


GLOBAL_RELATION_REFS = {
    "gate:requirement_id_missing",
    "gate:requirement_id_ambiguous",
}
GLOBAL_STATE_REFS = {
    "gate:implementation_doc_not_active",
    "policy:formal_window_closed",
}
TEMPLATE_STRUCTURE_REFS = {
    "doc:implementation_doc",
    "doc:design_doc",
    "gate:implementation_scope_unclear",
    "gate:required_tests_missing",
    "gate:acceptance_criteria_missing",
}


def build_task_adaptation_plan(
    *,
    state_path: str | Path,
    evaluate_payload: dict[str, Any],
    entity_id: str | None = None,
) -> dict[str, Any]:
    state = _load_state(Path(state_path))
    state_subtasks = _as_dict(state.get("subtasks"))
    evaluate_subtasks = _as_dict(evaluate_payload.get("subtasks"))
    evaluate_modules = _as_dict(evaluate_payload.get("modules"))

    selected_task_ids, selected_scope = _select_task_ids(
        state=state,
        entity_id=entity_id,
        evaluate_subtasks=evaluate_subtasks,
    )
    if not selected_task_ids:
        raise ValueError("no subtasks available for adaptation planning")

    module_blockers_by_module: dict[str, list[str]] = {}
    for module_id, module_entry in evaluate_modules.items():
        derived = _as_dict(_as_dict(module_entry).get("derived"))
        module_blockers_by_module[str(module_id)] = _as_string_list(derived.get("blocker_refs"))

    task_infos: list[dict[str, Any]] = []
    for task_id in selected_task_ids:
        state_task = _as_dict(state_subtasks.get(task_id))
        meta = _as_dict(state_task.get("meta"))
        facts = _as_dict(state_task.get("facts"))
        evaluate_task = _as_dict(evaluate_subtasks.get(task_id))
        derived = _as_dict(evaluate_task.get("derived"))
        module_id = str(meta.get("module_id", "")).strip()
        blocker_refs = _as_string_list(derived.get("blocker_refs"))
        task_infos.append(
            {
                "task_id": task_id,
                "module_id": module_id,
                "blocker_refs": blocker_refs,
                "design_doc_template_like": bool(
                    _as_dict(facts.get("design_doc")).get("template_like", False)
                ),
                "implementation_doc_template_like": bool(
                    _as_dict(facts.get("implementation_doc")).get("template_like", False)
                ),
                "module_blocker_refs": module_blockers_by_module.get(module_id, []),
            }
        )

    blocker_groups = _build_blocker_groups(
        task_infos=task_infos,
        module_blockers_by_module=module_blockers_by_module,
    )
    global_findings = [
        _group_to_finding(group)
        for group in blocker_groups
        if group.get("category") == "global"
    ]
    module_level_findings = _build_module_level_findings(
        task_infos=task_infos,
        module_blockers_by_module=module_blockers_by_module,
    )
    task_specific_groups = [
        group for group in blocker_groups if group.get("category") == "task_specific"
    ]

    candidate_tasks, ambiguous_candidates = _rank_candidate_tasks(task_infos)
    task_examples = _build_task_examples(
        task_infos=task_infos,
        candidate_tasks=candidate_tasks,
    )

    recommended_order = _build_recommended_order(
        blocker_groups=blocker_groups,
        module_level_findings=module_level_findings,
        task_specific_groups=task_specific_groups,
    )
    alternative_orders = _build_alternative_orders(
        blocker_groups=blocker_groups,
        module_level_findings=module_level_findings,
    )
    needs_manual_confirmation = _build_manual_confirmation_items(
        state=state,
        task_infos=task_infos,
        blocker_groups=blocker_groups,
        candidate_tasks=candidate_tasks,
        ambiguous_candidates=ambiguous_candidates,
    )
    confidence = _build_overall_confidence(
        blocker_groups=blocker_groups,
        selected_task_count=len(task_infos),
        ambiguous_candidates=ambiguous_candidates,
    )
    next_actions = _build_next_actions(
        recommended_order=recommended_order,
        candidate_tasks=candidate_tasks,
        needs_manual_confirmation=needs_manual_confirmation,
    )
    reasoning_notes = _build_reasoning_notes(
        blocker_groups=blocker_groups,
        task_infos=task_infos,
        entity_id=entity_id,
        selected_scope=selected_scope,
    )

    return {
        "summary": {
            "selected_entity_id": entity_id or "ALL",
            "selected_scope": selected_scope,
            "selected_task_count": len(task_infos),
            "state_task_count": len(state_subtasks),
            "evaluate_task_count": len(evaluate_subtasks),
            "global_problem_count": len(global_findings),
            "module_problem_count": len(module_level_findings),
            "candidate_task_count": len(candidate_tasks),
        },
        "global_findings": global_findings,
        "blocker_groups": blocker_groups,
        "recommended_order": recommended_order,
        "candidate_tasks": candidate_tasks,
        "module_level_findings": module_level_findings,
        "task_examples": task_examples,
        "next_actions": next_actions,
        "confidence": confidence,
        "ambiguous_candidates": ambiguous_candidates,
        "needs_manual_confirmation": needs_manual_confirmation,
        "alternative_orders": alternative_orders,
        "reasoning_notes": reasoning_notes,
    }


def render_task_adaptation_markdown(plan: dict[str, Any]) -> str:
    summary = _as_dict(plan.get("summary"))
    lines = [
        "# 任务适配规划",
        "",
        "## 摘要",
        f"- 选择范围: {summary.get('selected_scope', '')}",
        f"- 目标实体: {summary.get('selected_entity_id', '')}",
        f"- 纳入分析 task 数量: {summary.get('selected_task_count', 0)}",
        f"- 全局问题数量: {summary.get('global_problem_count', 0)}",
        f"- 模块级问题数量: {summary.get('module_problem_count', 0)}",
        "",
        "## 主建议顺序",
    ]
    for item in _as_list_of_dicts(plan.get("recommended_order")):
        lines.append(
            f"- {item.get('step', '?')}. {item.get('title', '')}: {item.get('reason', '')}"
        )

    lines.extend(["", "## 推荐打样对象"])
    for item in _as_list_of_dicts(plan.get("candidate_tasks")):
        reason_text = str(item.get("reason", "")).strip()
        lines.append(f"- {item.get('task_id', '')}: {reason_text}")

    lines.extend(["", "## 模块级发现"])
    for item in _as_list_of_dicts(plan.get("module_level_findings")):
        blockers = ", ".join(_as_string_list(item.get("blocker_refs")))
        lines.append(
            f"- {item.get('module_id', '')}: {blockers} | {item.get('reason', '')}"
        )

    lines.extend(["", "## 代表样本"])
    for item in _as_list_of_dicts(plan.get("task_examples")):
        lines.append(
            f"- {item.get('example_kind', '')}: {item.get('task_id', '')} | {item.get('reason', '')}"
        )

    lines.extend(["", "## 下一步最小动作"])
    for item in _as_list_of_dicts(plan.get("next_actions")):
        lines.append(f"- {item.get('title', '')}: {item.get('detail', '')}")

    manual_items = _as_list_of_dicts(plan.get("needs_manual_confirmation"))
    if manual_items:
        lines.extend(["", "## 需要人工确认"])
        for item in manual_items:
            lines.append(f"- {item.get('title', '')}: {item.get('reason', '')}")

    return "\n".join(lines) + "\n"


def write_task_adaptation_output(
    *,
    plan: dict[str, Any],
    output_path: str | Path,
    output_format: str,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "markdown":
        path.write_text(render_task_adaptation_markdown(plan), encoding="utf-8")
    else:
        path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _load_state(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - environment guard
        raise ValueError(f"PyYAML is required to load state file: {exc}") from exc

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"state file not found: {path}") from exc
    if not isinstance(raw, dict):
        raise ValueError("state file must contain a mapping")
    return raw


def _select_task_ids(
    *,
    state: dict[str, Any],
    entity_id: str | None,
    evaluate_subtasks: dict[str, Any],
) -> tuple[list[str], str]:
    state_subtasks = _as_dict(state.get("subtasks"))
    if not entity_id:
        task_ids = sorted(task_id for task_id in state_subtasks if task_id in evaluate_subtasks)
        return task_ids, "all_tasks"

    if entity_id in state_subtasks:
        if entity_id not in evaluate_subtasks:
            raise ValueError(f"entity-id not found in evaluate subtasks: {entity_id}")
        return [entity_id], "task"

    if entity_id in _as_dict(state.get("modules")):
        task_ids = []
        for task_id, subtask in state_subtasks.items():
            meta = _as_dict(_as_dict(subtask).get("meta"))
            if str(meta.get("module_id", "")).strip() == entity_id and task_id in evaluate_subtasks:
                task_ids.append(task_id)
        if not task_ids:
            raise ValueError(f"module has no subtasks in evaluate payload: {entity_id}")
        return sorted(task_ids), "module"

    if entity_id in _as_dict(state.get("requirements")):
        requirement = _as_dict(_as_dict(state.get("requirements")).get(entity_id))
        facts = _as_dict(requirement.get("facts"))
        task_ids = [
            task_id
            for task_id in _as_string_list(facts.get("task_ids"))
            if task_id in state_subtasks and task_id in evaluate_subtasks
        ]
        if not task_ids:
            raise ValueError(f"requirement has no subtasks in evaluate payload: {entity_id}")
        return sorted(task_ids), "requirement"

    raise ValueError(f"entity-id not found: {entity_id}")


def _build_blocker_groups(
    *,
    task_infos: list[dict[str, Any]],
    module_blockers_by_module: dict[str, list[str]],
) -> list[dict[str, Any]]:
    selected_task_ids = [item["task_id"] for item in task_infos]
    all_task_count = len(selected_task_ids)
    groups: list[dict[str, Any]] = []

    relation_refs = _collect_matching_refs(task_infos, lambda ref: ref in GLOBAL_RELATION_REFS)
    if relation_refs:
        groups.append(
            _make_group(
                group_id="global:requirement_relation",
                category="global",
                focus="requirement_relation",
                title="先补 requirement-task 关系",
                blocker_refs=relation_refs,
                task_infos=task_infos,
                reason="当前 requirement 关系无法唯一解析，会让所有 implementation 规划都停在入口处。",
                confidence=_confidence("high", 0.94),
                needs_manual_confirmation=True,
            )
        )

    activation_refs = _collect_matching_refs(task_infos, lambda ref: ref in GLOBAL_STATE_REFS)
    if activation_refs:
        groups.append(
            _make_group(
                group_id="global:activation_and_window_state",
                category="global",
                focus="activation_window_state",
                title="最后再处理状态放行",
                blocker_refs=activation_refs,
                task_infos=task_infos,
                reason="formal window 和 implementation_doc_state 是放行位，不适合先于内容适配处理。",
                confidence=_confidence("high", 0.9),
                needs_manual_confirmation=False,
            )
        )

    implementation_migration_refs = _collect_matching_refs(
        task_infos,
        lambda ref: ref == "doc:implementation_doc"
        or ref == "gate:implementation_scope_unclear"
        or ref == "gate:required_tests_missing"
        or ref == "gate:acceptance_criteria_missing"
        or ref.startswith("policy:language_non_compliant"),
    )
    if implementation_migration_refs:
        groups.append(
            _make_group(
                group_id="template:implementation_doc_migration",
                category="template_structure",
                focus="implementation_doc_migration",
                title="统一迁移实施文档结构",
                blocker_refs=implementation_migration_refs,
                task_infos=task_infos,
                reason="这些 blocker 更像旧模板/旧结构问题，适合批量迁移而不是逐 task 人工重写。",
                confidence=_confidence("high", 0.9),
                needs_manual_confirmation=False,
            )
        )

    design_refs = _collect_matching_refs(task_infos, lambda ref: ref == "doc:design_doc")
    if design_refs:
        groups.append(
            _make_group(
                group_id="template:design_doc_enablement",
                category="template_structure",
                focus="design_doc_enablement",
                title="补齐设计文档最小有效内容",
                blocker_refs=design_refs,
                task_infos=task_infos,
                reason="设计文档仍是模板态的 task 不适合直接进入 implementation-ready 适配。",
                confidence=_confidence("medium", 0.78),
                needs_manual_confirmation=False,
            )
        )

    for module_id, module_blockers in sorted(module_blockers_by_module.items()):
        if not module_blockers:
            continue
        affected_task_infos = [
            item
            for item in task_infos
            if item["module_id"] == module_id
            and any(
                blocker in item["blocker_refs"] or f"module:{module_id}" in item["blocker_refs"]
                for blocker in module_blockers
            )
        ]
        if not affected_task_infos:
            continue
        blocker_refs = _dedupe_strings([f"module:{module_id}"] + module_blockers)
        groups.append(
            _make_group(
                group_id=f"module:{module_id}",
                category="module_inherited",
                focus="module_blocker_cleanup",
                title=f"先处理 {module_id} 模块级 blocker",
                blocker_refs=blocker_refs,
                task_infos=affected_task_infos,
                reason="这些问题已经在模块层出现，应视为模块继承问题，而不是 task 个别问题。",
                confidence=_confidence("high", 0.88),
                needs_manual_confirmation=False,
            )
        )

    covered_refs = {
        ref
        for group in groups
        for ref in _as_string_list(group.get("blocker_refs"))
    }
    for task_info in task_infos:
        leftover_refs = [
            ref for ref in task_info["blocker_refs"] if ref not in covered_refs
        ]
        if not leftover_refs:
            continue
        groups.append(
            _make_group(
                group_id=f"task:{task_info['task_id']}",
                category="task_specific",
                focus="task_specific_cleanup",
                title=f"{task_info['task_id']} 个别补齐",
                blocker_refs=leftover_refs,
                task_infos=[task_info],
                reason="这些 blocker 没有形成稳定的全局、模板或模块继承模式，应保留为 task 个别处理项。",
                confidence=_confidence("medium", 0.68),
                needs_manual_confirmation=False,
            )
        )

    order = {
        "global": 0,
        "template_structure": 1,
        "module_inherited": 2,
        "task_specific": 3,
    }
    return sorted(
        groups,
        key=lambda item: (
            order.get(str(item.get("category", "")), 99),
            -int(item.get("affected_task_count", 0)),
            str(item.get("group_id", "")),
        ),
    )


def _build_module_level_findings(
    *,
    task_infos: list[dict[str, Any]],
    module_blockers_by_module: dict[str, list[str]],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for module_id, blocker_refs in sorted(module_blockers_by_module.items()):
        if not blocker_refs:
            continue
        affected_task_ids = sorted(
            item["task_id"]
            for item in task_infos
            if item["module_id"] == module_id
            and (
                f"module:{module_id}" in item["blocker_refs"]
                or any(ref in item["blocker_refs"] for ref in blocker_refs)
            )
        )
        if not affected_task_ids:
            continue
        findings.append(
            {
                "module_id": module_id,
                "blocker_refs": _dedupe_strings(blocker_refs),
                "affected_task_ids": affected_task_ids,
                "affected_task_count": len(affected_task_ids),
                "reason": "这些 blocker 已经在模块层成立，应优先在模块层解释和收口。",
                "confidence": _confidence("high", 0.88),
            }
        )
    return findings


def _rank_candidate_tasks(
    task_infos: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not task_infos:
        return [], []

    min_blocker_count = min(len(item["blocker_refs"]) for item in task_infos)
    ranked: list[dict[str, Any]] = []
    for item in task_infos:
        blockers = item["blocker_refs"]
        has_module_inherited = any(
            ref.startswith("module:") or ref in item["module_blocker_refs"] for ref in blockers
        )
        reason_keys: list[str] = []
        score = 100 - (len(blockers) * 8)
        if len(blockers) <= min_blocker_count + 1:
            score += 5
            reason_keys.append("low_blocker_count")
        if not has_module_inherited:
            score += 4
            reason_keys.append("no_module_inherited_blockers")
        else:
            score -= 15
            reason_keys.append("module_inherited_blockers")
        if not item["design_doc_template_like"]:
            score += 6
            reason_keys.append("design_doc_not_template")
        else:
            score -= 8
            reason_keys.append("design_doc_template_like")
        if item["implementation_doc_template_like"]:
            score -= 2
            reason_keys.append("implementation_doc_template_like")

        if not reason_keys:
            reason_keys.append("neutral_signal")
        ranked.append(
            {
                "task_id": item["task_id"],
                "module_id": item["module_id"],
                "score": score,
                "blocker_count": len(blockers),
                "reason_keys": _dedupe_strings(reason_keys),
                "reason": _candidate_reason_text(reason_keys),
                "confidence": _confidence("medium" if has_module_inherited else "high", 0.82 if not has_module_inherited else 0.66),
            }
        )

    ranked.sort(key=lambda item: (-int(item["score"]), int(item["blocker_count"]), str(item["task_id"])))
    candidate_tasks = ranked[: min(3, len(ranked))]

    ambiguous_candidates: list[dict[str, Any]] = []
    if len(ranked) > 1:
        boundary = ranked[1]
        boundary_key = (int(boundary["score"]), int(boundary["blocker_count"]))
        cluster = [
            item
            for item in ranked
            if (int(item["score"]), int(item["blocker_count"])) == boundary_key
        ]
        for item in cluster[:6]:
            ambiguous_candidates.append(
                {
                    "task_id": item["task_id"],
                    "module_id": item["module_id"],
                    "reason": "当前排序信号不足以进一步区分这组候选 task。",
                    "confidence": _confidence("medium", 0.62),
                }
            )
    return candidate_tasks, ambiguous_candidates


def _build_task_examples(
    *,
    task_infos: list[dict[str, Any]],
    candidate_tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    candidate_ids = {item["task_id"] for item in candidate_tasks}
    task_map = {item["task_id"]: item for item in task_infos}

    if candidate_tasks:
        top = candidate_tasks[0]
        top_task = task_map.get(top["task_id"], {})
        top_has_module_inherited = any(
            ref.startswith("module:") or ref in _as_string_list(top_task.get("module_blocker_refs"))
            for ref in _as_string_list(top_task.get("blocker_refs"))
        )
        examples.append(
            {
                "example_kind": "pilot_candidate",
                "task_id": top["task_id"],
                "module_id": top["module_id"],
                "reason": (
                    "这个 task 在当前选择范围内是代表样本，但仍受模块继承 blocker 影响，不宜直接外推为全仓首批对象。"
                    if top_has_module_inherited
                    else "这个 task 的 blocker 更少，且没有明显模块继承问题，适合作为第一批打样对象。"
                ),
                "confidence": top["confidence"],
            }
        )

    old_template_case = next(
        (
            item
            for item in task_infos
            if item["design_doc_template_like"] and item["implementation_doc_template_like"]
        ),
        None,
    )
    if old_template_case is not None:
        examples.append(
            {
                "example_kind": "old_template_case",
                "task_id": old_template_case["task_id"],
                "module_id": old_template_case["module_id"],
                "reason": "这是典型旧模板 task，问题集中在设计/实施文档结构和语言规则迁移。",
                "confidence": _confidence("high", 0.9),
            }
        )

    module_case = next(
        iter(
            sorted(
                (
                    item
                    for item in task_infos
                    if any(
                        ref.startswith("module:") or ref in item["module_blocker_refs"]
                        for ref in item["blocker_refs"]
                    )
                ),
                key=lambda item: (
                    item["design_doc_template_like"],
                    len(item["blocker_refs"]),
                    item["task_id"],
                ),
            )
        ),
        None,
    )
    if module_case is not None:
        examples.append(
            {
                "example_kind": "module_inherited_case",
                "task_id": module_case["task_id"],
                "module_id": module_case["module_id"],
                "reason": "这个 task 自身并非唯一问题源，当前更像被模块级 blocker 一并拖住。",
                "confidence": _confidence("high", 0.86),
            }
        )

    for item in task_infos:
        if item["task_id"] in candidate_ids:
            continue
        if not any(example["task_id"] == item["task_id"] for example in examples):
            examples.append(
                {
                    "example_kind": "non_pilot_reference",
                    "task_id": item["task_id"],
                    "module_id": item["module_id"],
                    "reason": "这个 task 可以作为对照样本，但不建议作为第一批优先对象。",
                    "confidence": _confidence("medium", 0.64),
                }
            )
            break
    return examples


def _build_recommended_order(
    *,
    blocker_groups: list[dict[str, Any]],
    module_level_findings: list[dict[str, Any]],
    task_specific_groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    order: list[dict[str, Any]] = []
    focus_map = {group["focus"]: group for group in blocker_groups}

    def _append_step(focus: str, title: str) -> None:
        group = focus_map.get(focus)
        if not isinstance(group, dict):
            return
        order.append(
            {
                "step": len(order) + 1,
                "focus": focus,
                "title": title,
                "blocker_refs": _as_string_list(group.get("blocker_refs")),
                "reason": str(group.get("reason", "")),
                "confidence": group.get("confidence", _confidence("medium", 0.7)),
            }
        )

    _append_step("requirement_relation", "先补关系映射")
    _append_step("implementation_doc_migration", "再做实施文档批量迁移")
    _append_step("design_doc_enablement", "然后补设计文档最小有效内容")
    if module_level_findings:
        _append_step("module_blocker_cleanup", "随后处理模块继承 blocker")
    _append_step("activation_window_state", "最后再处理状态放行")
    if task_specific_groups:
        _append_step("task_specific_cleanup", "剩余 task 个别补齐")
    return order


def _build_alternative_orders(
    *,
    blocker_groups: list[dict[str, Any]],
    module_level_findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    focus_ids = {group["focus"] for group in blocker_groups}
    alternatives: list[dict[str, Any]] = []
    if {"requirement_relation", "implementation_doc_migration"} & focus_ids:
        alternatives.append(
            {
                "order_id": "template_first",
                "title": "如果你想先统一文档结构",
                "steps": [
                    "implementation_doc_migration",
                    "design_doc_enablement",
                    "requirement_relation",
                    "activation_window_state",
                ],
                "reason": "适合先减少旧模板噪声，再回头收 requirement 关系。",
            }
        )
        alternatives.append(
            {
                "order_id": "relation_first",
                "title": "如果你想先补关系真值",
                "steps": [
                    "requirement_relation",
                    "implementation_doc_migration",
                    "design_doc_enablement",
                    "activation_window_state",
                ],
                "reason": "适合先把 requirement-task 主链补齐，再批量迁移 task 文档。",
            }
        )
    if module_level_findings:
        alternatives.append(
            {
                "order_id": "module_first",
                "title": "如果你当前只想解一个模块",
                "steps": [
                    "module_blocker_cleanup",
                    "implementation_doc_migration",
                    "requirement_relation",
                    "activation_window_state",
                ],
                "reason": "适合聚焦单模块，但不适合作为全仓默认顺序。",
            }
        )
    return alternatives


def _build_manual_confirmation_items(
    *,
    state: dict[str, Any],
    task_infos: list[dict[str, Any]],
    blocker_groups: list[dict[str, Any]],
    candidate_tasks: list[dict[str, Any]],
    ambiguous_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not _as_dict(state.get("requirements")):
        items.append(
            {
                "title": "requirement 真值映射仍需人工确认",
                "reason": "当前 official state 没有 requirement 条目，planner 只能先把它识别成全局前置问题。",
                "confidence": _confidence("high", 0.94),
            }
        )
    if ambiguous_candidates:
        items.append(
            {
                "title": "第二梯队候选存在并列",
                "reason": "当前排序足以给出主建议，但不足以稳定区分并列候选的先后顺序。",
                "confidence": _confidence("medium", 0.64),
            }
        )
    if len(task_infos) == 1 and candidate_tasks:
        items.append(
            {
                "title": "当前仅分析单一范围",
                "reason": "单 task / 单 module 视角适合局部规划，但不应替代全仓优先级结论。",
                "confidence": _confidence("medium", 0.7),
            }
        )
    if any(group.get("category") == "module_inherited" for group in blocker_groups):
        items.append(
            {
                "title": "模块级 blocker 需保持模块层解释",
                "reason": "这些问题不应被 planner 误判成 task 个别修复项，必要时应回到模块层确认。",
                "confidence": _confidence("high", 0.86),
            }
        )
    return items


def _build_overall_confidence(
    *,
    blocker_groups: list[dict[str, Any]],
    selected_task_count: int,
    ambiguous_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    score = 0.84
    if selected_task_count <= 1:
        score -= 0.12
    if ambiguous_candidates:
        score -= 0.08
    if any(group.get("needs_manual_confirmation") for group in blocker_groups):
        score -= 0.04
    if score >= 0.85:
        level = "high"
    elif score >= 0.7:
        level = "medium"
    else:
        level = "low"
    return _confidence(level, round(score, 2))


def _build_next_actions(
    *,
    recommended_order: list[dict[str, Any]],
    candidate_tasks: list[dict[str, Any]],
    needs_manual_confirmation: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if recommended_order:
        first = recommended_order[0]
        actions.append(
            {
                "title": "按主顺序启动第一步",
                "detail": f"先处理 {first.get('focus', '')}，因为它对后续 implementation-ready 入口影响最大。",
            }
        )
    if candidate_tasks:
        first_candidate = candidate_tasks[0]
        actions.append(
            {
                "title": "选一个代表 task 做打样验证",
                "detail": f"优先用 {first_candidate.get('task_id', '')} 验证适配路径，但本轮目标仍是验证工具解释能力。",
            }
        )
    if needs_manual_confirmation:
        actions.append(
            {
                "title": "保留人工确认点",
                "detail": "planner 已给出主建议，但 requirement 关系和并列候选仍应保留人工确认。",
            }
        )
    return actions


def _build_reasoning_notes(
    *,
    blocker_groups: list[dict[str, Any]],
    task_infos: list[dict[str, Any]],
    entity_id: str | None,
    selected_scope: str,
) -> list[str]:
    notes = [
        "该 planner 是只读规划器，不写回 state，也不自动修文档。",
        "规则主要用于分组、排序和推荐样本，不用于给每个 task 生成唯一修复答案。",
    ]
    if entity_id:
        notes.append(
            f"当前结果已被限制在 {selected_scope} 范围，适合局部判断，不应直接替代全仓规划。"
        )
    if any(group.get("category") == "module_inherited" for group in blocker_groups):
        notes.append("模块继承 blocker 会优先保留为模块层问题，而不是压成 task 个别问题。")
    if any(item["design_doc_template_like"] for item in task_infos):
        notes.append("部分 task 仍处于设计文档模板态，这会降低 planner 对个别 task 排序的确定性。")
    return notes


def _group_to_finding(group: dict[str, Any]) -> dict[str, Any]:
    return {
        "finding_id": str(group.get("group_id", "")),
        "title": str(group.get("title", "")),
        "blocker_refs": _as_string_list(group.get("blocker_refs")),
        "affected_task_ids": _as_string_list(group.get("affected_task_ids")),
        "affected_task_count": int(group.get("affected_task_count", 0)),
        "reason": str(group.get("reason", "")),
        "confidence": group.get("confidence", _confidence("medium", 0.7)),
    }


def _make_group(
    *,
    group_id: str,
    category: str,
    focus: str,
    title: str,
    blocker_refs: list[str],
    task_infos: list[dict[str, Any]],
    reason: str,
    confidence: dict[str, Any],
    needs_manual_confirmation: bool,
) -> dict[str, Any]:
    affected_task_ids = sorted(item["task_id"] for item in task_infos)
    modules = sorted({item["module_id"] for item in task_infos if item["module_id"]})
    return {
        "group_id": group_id,
        "category": category,
        "focus": focus,
        "title": title,
        "blocker_refs": _dedupe_strings(blocker_refs),
        "affected_task_ids": affected_task_ids,
        "affected_task_count": len(affected_task_ids),
        "modules": modules,
        "representative_tasks": affected_task_ids[:3],
        "reason": reason,
        "confidence": confidence,
        "needs_manual_confirmation": needs_manual_confirmation,
    }


def _collect_matching_refs(
    task_infos: list[dict[str, Any]],
    predicate: Any,
) -> list[str]:
    refs: list[str] = []
    for item in task_infos:
        for ref in item["blocker_refs"]:
            if predicate(ref):
                refs.append(ref)
    return _dedupe_strings(refs)


def _candidate_reason_text(reason_keys: list[str]) -> str:
    pieces = {
        "low_blocker_count": "blocker 数量相对更低",
        "no_module_inherited_blockers": "没有明显模块继承 blocker",
        "module_inherited_blockers": "仍受模块继承 blocker 影响",
        "design_doc_not_template": "设计文档已不是纯模板态",
        "design_doc_template_like": "设计文档仍偏模板态",
        "implementation_doc_template_like": "实施文档仍需迁移到当前有效结构",
        "neutral_signal": "当前没有额外强信号",
    }
    return "；".join(pieces.get(key, key) for key in reason_keys)


def _confidence(level: str, score: float) -> dict[str, Any]:
    return {"level": level, "score": score}


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return _dedupe_strings([str(item).strip() for item in value if str(item).strip()])


def _as_list_of_dicts(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _dedupe_strings(items: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return ordered
