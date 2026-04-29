from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .task_apply import build_task_readiness_fix_plan


IMPLEMENTATION_REQUIRED_HEADINGS = [
    "# 子任务实施文档",
    "## 3. 本轮实施目标",
    "## 5. 允许修改范围",
    "## 7. 测试与验证",
    "## 8. 完成判定",
]
DESIGN_REQUIRED_HEADINGS = [
    "# 子任务设计文档",
    "## 3. 子任务目标",
    "## 5. 技术方案",
]
OLD_STATUS_RE = re.compile(
    r"(draft\s*/\s*reviewable\s*/\s*(?:downstream-ready|implementation-ready)\s*/\s*blocked)"
    r"|(?:当前状态\s*[:：].*(?:draft|reviewable|downstream-ready|implementation-ready|blocked))",
    re.IGNORECASE,
)
PLACEHOLDER_FIELD_RE = re.compile(r"待人工填写：([A-Za-z_]+)")
PACKET_INPUT_FIELD_KEYS = {
    "goal": "goal",
    "allowed_modify_paths": "allowed_modify_paths",
    "forbidden_paths": "forbidden_paths",
    "required_tests": "required_tests",
    "acceptance_criteria": "acceptance_criteria",
}


def build_task_apply_summary(
    *,
    state_path: str | Path,
    after_evaluate_payload: dict[str, Any],
    entity_ids: list[str] | tuple[str, ...] | str,
    before_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state_path = Path(state_path)
    state = _load_state(state_path)
    repo_root = _resolve_repo_root(state_path)
    task_ids = _normalize_entity_ids(entity_ids=entity_ids, state=state)
    plan = build_task_readiness_fix_plan(
        state_path=state_path,
        evaluate_payload=after_evaluate_payload,
        entity_id=",".join(task_ids),
    )

    after_subtasks = _as_dict(after_evaluate_payload.get("subtasks"))
    before_map = _build_before_blocker_map(before_payload)

    applied_tasks: list[dict[str, Any]] = []
    resolved_blockers: list[dict[str, Any]] = []
    remaining_blockers: list[dict[str, Any]] = []
    newly_exposed_gaps: list[dict[str, Any]] = []
    manual_fill_remaining: list[dict[str, Any]] = []
    task_status_after_apply: list[dict[str, Any]] = []
    next_actions: list[dict[str, Any]] = []

    plan_tasks = {
        str(item.get("task_id", "")).strip(): item
        for item in _as_list_of_dicts(plan.get("tasks"))
        if item.get("task_id")
    }
    requirement_actions = {
        str(item.get("task_id", "")).strip(): item
        for item in _as_list_of_dicts(plan.get("requirement_seed_actions"))
        if item.get("task_id")
    }

    for task_id in task_ids:
        task_state = _as_dict(_as_dict(state.get("subtasks")).get(task_id))
        task_plan = _as_dict(plan_tasks.get(task_id))
        requirement_action = _as_dict(requirement_actions.get(task_id))
        derived = _as_dict(_as_dict(after_subtasks.get(task_id)).get("derived"))
        after_blockers = _as_string_list(derived.get("blocker_refs"))
        packet_inputs = _as_dict(derived.get("implementation_packet_inputs"))
        inspection = _inspect_task_docs(
            repo_root=repo_root,
            task_state=task_state,
        )
        manual_fields = _filter_manual_fields_with_packet_inputs(
            _dedupe_strings(
                _as_string_list(task_plan.get("manual_fill_fields"))
                + _as_string_list(_as_dict(inspection.get("implementation")).get("placeholder_fields"))
                + _as_string_list(_as_dict(inspection.get("design")).get("placeholder_fields"))
            ),
            packet_inputs=packet_inputs,
        )

        resolved_items = _build_resolved_blockers(
            task_id=task_id,
            inspection=inspection,
            after_blockers=after_blockers,
            before_blockers=before_map.get(task_id, []),
        )
        remaining_items = _build_remaining_blockers(
            task_id=task_id,
            after_blockers=after_blockers,
        )
        gap_item = _build_newly_exposed_gap(
            task_id=task_id,
            inspection=inspection,
            manual_fields=manual_fields,
        )
        manual_item = {
            "task_id": task_id,
            "fields": manual_fields,
            "reason": "结构骨架已落地后，当前仍需人工补齐这些字段。",
        }

        status_item = _build_task_status_after_apply(
            task_id=task_id,
            task_plan=task_plan,
            requirement_action=requirement_action,
            inspection=inspection,
            remaining_items=remaining_items,
            manual_fields=manual_fields,
        )
        action_items = _build_next_actions_for_task(
            task_id=task_id,
            requirement_action=requirement_action,
            task_plan=task_plan,
            manual_fields=manual_fields,
            remaining_items=remaining_items,
        )

        applied_tasks.append(
            {
                "task_id": task_id,
                "module_id": str(task_plan.get("module_id", "")).strip(),
                "inspected_files": inspection["inspected_files"],
                "requirement_seed_status": str(requirement_action.get("status", "")).strip(),
                "closer_to_implementation_ready": bool(status_item.get("closer_to_implementation_ready")),
                "summary": str(status_item.get("summary", "")).strip(),
            }
        )
        resolved_blockers.extend(resolved_items)
        remaining_blockers.extend(remaining_items)
        if gap_item:
            newly_exposed_gaps.append(gap_item)
        if manual_fields:
            manual_fill_remaining.append(manual_item)
        task_status_after_apply.append(status_item)
        next_actions.extend(action_items)

    next_actions = _dedupe_action_items(next_actions)
    next_actions = _prepend_batch_actions(
        next_actions=next_actions,
        task_status_after_apply=task_status_after_apply,
    )

    summary = {
        "selected_task_count": len(task_ids),
        "resolved_blocker_count": len(resolved_blockers),
        "remaining_blocker_count": len(remaining_blockers),
        "newly_exposed_gap_count": len(newly_exposed_gaps),
        "manual_fill_task_count": len(manual_fill_remaining),
        "closer_to_ready_count": sum(1 for item in task_status_after_apply if bool(item.get("closer_to_implementation_ready"))),
    }
    confidence = _build_confidence(
        task_status_after_apply=task_status_after_apply,
        before_payload=before_payload,
    )
    reasoning_notes = _build_reasoning_notes(
        before_payload=before_payload,
        remaining_blockers=remaining_blockers,
        task_status_after_apply=task_status_after_apply,
    )

    return {
        "summary": summary,
        "applied_tasks": applied_tasks,
        "resolved_blockers": resolved_blockers,
        "remaining_blockers": remaining_blockers,
        "newly_exposed_gaps": newly_exposed_gaps,
        "manual_fill_remaining": manual_fill_remaining,
        "task_status_after_apply": task_status_after_apply,
        "next_actions": next_actions,
        "confidence": confidence,
        "reasoning_notes": reasoning_notes,
    }


def render_task_apply_summary_markdown(payload: dict[str, Any]) -> str:
    summary = _as_dict(payload.get("summary"))
    lines = [
        "# 任务 apply 结果总结",
        "",
        "## 摘要",
        f"- 目标 task 数量: {summary.get('selected_task_count', 0)}",
        f"- 已清掉 blocker 数量: {summary.get('resolved_blocker_count', 0)}",
        f"- 仍保留 blocker 数量: {summary.get('remaining_blocker_count', 0)}",
        f"- 新暴露缺口数量: {summary.get('newly_exposed_gap_count', 0)}",
        f"- 仍需人工填写 task 数量: {summary.get('manual_fill_task_count', 0)}",
        f"- 更接近 implementation_ready 的 task 数量: {summary.get('closer_to_ready_count', 0)}",
        "",
        "## 当前 task 状态",
    ]
    for item in _as_list_of_dicts(payload.get("task_status_after_apply")):
        lines.append(
            f"- {item.get('task_id', '')}: closer={bool(item.get('closer_to_implementation_ready'))} | {item.get('summary', '')}"
        )

    lines.extend(["", "## 已清掉的问题"])
    for item in _as_list_of_dicts(payload.get("resolved_blockers")):
        lines.append(f"- {item.get('task_id', '')}: {item.get('blocker', '')} | {item.get('note', '')}")

    lines.extend(["", "## 仍保留的问题"])
    for item in _as_list_of_dicts(payload.get("remaining_blockers")):
        lines.append(f"- {item.get('task_id', '')}: {item.get('blocker', '')} | {item.get('category', '')}")

    gaps = _as_list_of_dicts(payload.get("newly_exposed_gaps"))
    if gaps:
        lines.extend(["", "## 新暴露缺口"])
        for item in gaps:
            lines.append(f"- {item.get('task_id', '')}: {', '.join(_as_string_list(item.get('fields'))) or '无'} | {item.get('reason', '')}")

    manual_items = _as_list_of_dicts(payload.get("manual_fill_remaining"))
    if manual_items:
        lines.extend(["", "## 人工填写残留"])
        for item in manual_items:
            lines.append(f"- {item.get('task_id', '')}: {', '.join(_as_string_list(item.get('fields'))) or '无'}")

    lines.extend(["", "## 下一步建议"])
    for item in _as_list_of_dicts(payload.get("next_actions")):
        scope = str(item.get("scope", "")).strip()
        prefix = f"[{scope}] " if scope else ""
        lines.append(f"- {prefix}{item.get('title', '')}: {item.get('reason', '')}")

    notes = payload.get("reasoning_notes")
    if isinstance(notes, list) and notes:
        lines.extend(["", "## 说明"])
        for note in notes:
            text = str(note).strip()
            if text:
                lines.append(f"- {text}")
    return "\n".join(lines) + "\n"


def write_task_apply_summary_output(
    *,
    payload: dict[str, Any],
    output_path: str | Path,
    output_format: str,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "markdown":
        path.write_text(render_task_apply_summary_markdown(payload), encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _inspect_task_docs(
    *,
    repo_root: Path,
    task_state: dict[str, Any],
) -> dict[str, Any]:
    meta = _as_dict(task_state.get("meta"))
    facts = _as_dict(task_state.get("facts"))
    task_root = str(meta.get("path", "")).strip()
    canonical_design_path = _join_relative_path(task_root, "SUBTASK_DESIGN.md")
    canonical_implementation_path = _join_relative_path(
        task_root,
        "SUBTASK_IMPLEMENTATION.md",
    )
    design_path = _resolve_subtask_doc_relative_path(
        repo_root=repo_root,
        slot_doc=_as_dict(facts.get("design_doc")),
        canonical_relative_path=canonical_design_path,
    )
    implementation_path = _resolve_subtask_doc_relative_path(
        repo_root=repo_root,
        slot_doc=_as_dict(facts.get("implementation_doc")),
        canonical_relative_path=canonical_implementation_path,
    )
    design_text = _read_text_if_exists(repo_root / design_path)
    implementation_text = _read_text_if_exists(repo_root / implementation_path)
    return {
        "inspected_files": [design_path, implementation_path],
        "design": {
            "path": design_path,
            "headings_ok": _has_required_headings(design_text, DESIGN_REQUIRED_HEADINGS),
            "old_status_cleared": not bool(OLD_STATUS_RE.search(design_text)),
            "placeholder_fields": _extract_placeholder_fields(design_text),
            "text": design_text,
        },
        "implementation": {
            "path": implementation_path,
            "headings_ok": _has_required_headings(implementation_text, IMPLEMENTATION_REQUIRED_HEADINGS),
            "old_status_cleared": not bool(OLD_STATUS_RE.search(implementation_text)),
            "placeholder_fields": _extract_placeholder_fields(implementation_text),
            "text": implementation_text,
        },
    }


def _build_before_blocker_map(before_payload: dict[str, Any] | None) -> dict[str, list[str]]:
    if not isinstance(before_payload, dict):
        return {}
    subtasks = _as_dict(before_payload.get("subtasks"))
    output: dict[str, list[str]] = {}
    for task_id, item in subtasks.items():
        blocker_refs = _as_string_list(_as_dict(_as_dict(item).get("derived")).get("blocker_refs"))
        if blocker_refs:
            output[str(task_id)] = blocker_refs
    return output


def _build_resolved_blockers(
    *,
    task_id: str,
    inspection: dict[str, Any],
    after_blockers: list[str],
    before_blockers: list[str],
) -> list[dict[str, Any]]:
    resolved: list[dict[str, Any]] = []
    implementation = _as_dict(inspection.get("implementation"))
    design = _as_dict(inspection.get("design"))

    inferred_targets: list[tuple[str, bool, str]] = [
        (
            "doc:implementation_doc",
            bool(implementation.get("headings_ok")),
            "implementation 文档已具备中文章节骨架。",
        ),
        (
            "doc:design_doc",
            bool(design.get("headings_ok")),
            "design 文档已具备最小中文章节骨架。",
        ),
        (
            "policy:language_non_compliant_lang_heading_not_chinese_by_default",
            bool(implementation.get("headings_ok")) and bool(design.get("headings_ok") or design.get("text")),
            "英文标题/章节骨架问题已被清理为中文主结构。",
        ),
        (
            "legacy:old_status_semantics",
            bool(implementation.get("old_status_cleared")) and bool(design.get("old_status_cleared")),
            "旧状态语义已从当前文档正文中清理。",
        ),
    ]

    for blocker, condition, note in inferred_targets:
        if not condition:
            continue
        resolved.append(
            {
                "task_id": task_id,
                "blocker": blocker,
                "resolved_in_content": True,
                "still_reported_by_formal_gate": blocker in after_blockers,
                "was_present_in_before_snapshot": blocker in before_blockers if before_blockers else None,
                "note": note if blocker not in after_blockers else note + " 但 formal gate 仍可能因为 state 未写回而保留旧 blocker。",
            }
        )
    return _dedupe_blocker_items(resolved)


def _build_remaining_blockers(
    *,
    task_id: str,
    after_blockers: list[str],
) -> list[dict[str, Any]]:
    return [
        {
            "task_id": task_id,
            "blocker": blocker,
            "category": _categorize_blocker(blocker),
        }
        for blocker in after_blockers
    ]


def _build_newly_exposed_gap(
    *,
    task_id: str,
    inspection: dict[str, Any],
    manual_fields: list[str],
) -> dict[str, Any] | None:
    implementation = _as_dict(inspection.get("implementation"))
    if not bool(implementation.get("headings_ok")) or not manual_fields:
        return None
    return {
        "task_id": task_id,
        "fields": manual_fields,
        "reason": "结构性问题已初步清掉，当前主要缺口转为人工填写字段。",
    }


def _build_task_status_after_apply(
    *,
    task_id: str,
    task_plan: dict[str, Any],
    requirement_action: dict[str, Any],
    inspection: dict[str, Any],
    remaining_items: list[dict[str, Any]],
    manual_fields: list[str],
) -> dict[str, Any]:
    remaining_categories = _dedupe_strings([str(item.get("category", "")).strip() for item in remaining_items if item.get("category")])
    closer = bool(_as_dict(inspection.get("implementation")).get("headings_ok")) or bool(_as_dict(inspection.get("design")).get("headings_ok"))
    if manual_fields and "manual_fill" not in remaining_categories:
        remaining_categories.append("manual_fill")
    if bool(requirement_action):
        status = str(requirement_action.get("status", "")).strip()
        if status.startswith("blocked_") and "requirement_relation" not in remaining_categories:
            remaining_categories.append("requirement_relation")

    return {
        "task_id": task_id,
        "module_id": str(task_plan.get("module_id", "")).strip(),
        "closer_to_implementation_ready": closer,
        "remaining_gap_categories": remaining_categories,
        "requirement_seed_status": str(requirement_action.get("status", "")).strip(),
        "summary": _build_task_summary_sentence(
            requirement_action=requirement_action,
            inspection=inspection,
            manual_fields=manual_fields,
            remaining_categories=remaining_categories,
        ),
    }


def _build_task_summary_sentence(
    *,
    requirement_action: dict[str, Any],
    inspection: dict[str, Any],
    manual_fields: list[str],
    remaining_categories: list[str],
) -> str:
    parts: list[str] = []
    if bool(_as_dict(inspection.get("implementation")).get("headings_ok")):
        parts.append("实施文档骨架已落地")
    if bool(_as_dict(inspection.get("design")).get("headings_ok")):
        parts.append("设计文档最小结构已就位")
    if manual_fields:
        parts.append("仍需人工补字段")
    status = str(requirement_action.get("status", "")).strip()
    if status:
        parts.append(f"requirement seed 仍为 {status}")
    if remaining_categories:
        parts.append("未达到 fully ready")
    return "，".join(parts) or "当前无显著变化。"


def _build_next_actions_for_task(
    *,
    task_id: str,
    requirement_action: dict[str, Any],
    task_plan: dict[str, Any],
    manual_fields: list[str],
    remaining_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    requirement_status = str(requirement_action.get("status", "")).strip()
    if requirement_status == "blocked_manual_confirmation":
        actions.append(
            {
                "scope": "task",
                "task_id": task_id,
                "title": "先确认 requirement seed",
                "reason": "当前 requirement 关系仍只是建议态，不能直接视为正式真值。",
            }
        )
    blocker_categories = _dedupe_strings([str(item.get("category", "")).strip() for item in remaining_items if item.get("category")])
    if "module_inherited" in blocker_categories:
        actions.append(
            {
                "scope": "task",
                "task_id": task_id,
                "title": "先解决模块继承 blocker",
                "reason": "这类问题不应继续在 task 文档里局部修补，应先回到模块层处理。",
            }
        )
    for field in manual_fields:
        title = {
            "allowed_modify_paths": "继续补 allowed_modify_paths",
            "required_tests": "继续补 required_tests",
            "acceptance_criteria": "继续补 acceptance_criteria",
            "design_key_sections": "继续补 design 文档关键段落",
        }.get(field, f"继续补 {field}")
        actions.append(
            {
                "scope": "task",
                "task_id": task_id,
                "title": title,
                "reason": "apply 只落了结构骨架，这部分仍需人工填写具体内容。",
            }
        )
    if "state_window" in blocker_categories:
        actions.append(
            {
                "scope": "task",
                "task_id": task_id,
                "title": "最后再处理状态位与开窗问题",
                "reason": "当前仍有 formal window / implementation_doc_state 类阻断，不宜在内容尚未补齐前优先推进。",
            }
        )
    return actions


def _prepend_batch_actions(
    *,
    next_actions: list[dict[str, Any]],
    task_status_after_apply: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    batch_actions: list[dict[str, Any]] = []
    if any("requirement_relation" in _as_string_list(item.get("remaining_gap_categories")) for item in task_status_after_apply):
        batch_actions.append(
            {
                "scope": "batch",
                "task_id": "",
                "title": "先统一确认 requirement seed",
                "reason": "若 requirement 关系仍停留在建议态，后续 readiness 推进都会继续受限。",
            }
        )
    if any("manual_fill" in _as_string_list(item.get("remaining_gap_categories")) for item in task_status_after_apply):
        batch_actions.append(
            {
                "scope": "batch",
                "task_id": "",
                "title": "优先补人工字段",
                "reason": "结构问题已初步清理后，当前主要收益来自补 allowed_modify_paths / required_tests / acceptance_criteria。",
            }
        )
    return _dedupe_action_items(batch_actions + next_actions)


def _build_confidence(
    *,
    task_status_after_apply: list[dict[str, Any]],
    before_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    score = 0.7
    if before_payload:
        score += 0.1
    if any(bool(item.get("closer_to_implementation_ready")) for item in task_status_after_apply):
        score += 0.08
    score = min(score, 0.92)
    level = "high" if score >= 0.85 else "medium"
    return {"level": level, "score": round(score, 2)}


def _build_reasoning_notes(
    *,
    before_payload: dict[str, Any] | None,
    remaining_blockers: list[dict[str, Any]],
    task_status_after_apply: list[dict[str, Any]],
) -> list[str]:
    notes = [
        "本能力是 apply 后总结层，只做对比总结和下一步建议，不写回 state，也不修改文档。",
        "它会同时参考 formal evaluate blocker 与当前 markdown 内容结构，因此不会只复读 blocker 列表。",
    ]
    if not before_payload:
        notes.append("当前未提供 before snapshot；resolved_blockers 主要依据当前文件结构与 apply 合同做推断，而不是严格历史快照 diff。")
    if any(item.get("blocker") == "gate:requirement_id_missing" for item in remaining_blockers):
        notes.append("requirement seed 仍然只是建议态；在未写 state 的前提下，这一层不会把它提升成正式 requirement 真值。")
    if any(bool(item.get("closer_to_implementation_ready")) for item in task_status_after_apply):
        notes.append("当前 task 已比 apply 前更接近 implementation_ready，但这不等于已经 fully ready。")
    return _dedupe_strings(notes)


def _normalize_entity_ids(
    *,
    entity_ids: list[str] | tuple[str, ...] | str,
    state: dict[str, Any],
) -> list[str]:
    if isinstance(entity_ids, str):
        raw_items = [part.strip() for part in entity_ids.split(",") if part.strip()]
    else:
        raw_items = []
        for item in entity_ids:
            raw_items.extend(part.strip() for part in str(item).split(",") if part.strip())
    task_ids = _dedupe_strings(raw_items)
    if not task_ids:
        raise ValueError("至少需要一个 task entity-id")
    subtasks = _as_dict(state.get("subtasks"))
    missing = [task_id for task_id in task_ids if task_id not in subtasks]
    if missing:
        raise ValueError(f"entity-id 不是有效 task: {', '.join(missing)}")
    return task_ids


def _categorize_blocker(blocker: str) -> str:
    if blocker.startswith("gate:requirement_id_"):
        return "requirement_relation"
    if blocker in {"doc:implementation_doc", "doc:design_doc"} or blocker.startswith("policy:language_non_compliant"):
        return "doc_structure"
    if blocker in {
        "gate:implementation_scope_unclear",
        "gate:required_tests_missing",
        "gate:acceptance_criteria_missing",
        "gate:path_scope_conflict",
    }:
        return "manual_fill"
    if blocker.startswith("module:") or blocker in {"doc:api", "doc:open_questions"}:
        return "module_inherited"
    if blocker in {
        "gate:implementation_doc_not_active",
        "policy:formal_window_closed",
        "gate:maturity_missing",
        "gate:implementation_approval_missing",
    }:
        return "state_window"
    return "other"


def _has_required_headings(text: str, headings: list[str]) -> bool:
    if not text:
        return False
    return all(heading in text for heading in headings)


def _extract_placeholder_fields(text: str) -> list[str]:
    if not text:
        return []
    fields = _dedupe_strings(PLACEHOLDER_FIELD_RE.findall(text))
    if "技术方案" in text and "design_key_sections" not in fields and "待人工填写：技术方案" in text:
        fields.append("design_key_sections")
    if "子任务目标" in text and "design_key_sections" not in fields and "待人工填写：子任务目标" in text:
        fields.append("design_key_sections")
    return _dedupe_strings(fields)


def _filter_manual_fields_with_packet_inputs(
    fields: list[str],
    *,
    packet_inputs: dict[str, Any],
) -> list[str]:
    filtered: list[str] = []
    for field in fields:
        packet_key = PACKET_INPUT_FIELD_KEYS.get(field)
        if packet_key and _packet_input_field_present(packet_inputs.get(packet_key)):
            continue
        filtered.append(field)
    return _dedupe_strings(filtered)


def _packet_input_field_present(value: object) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(_as_string_list(value))
    return bool(value)


def _resolve_subtask_doc_relative_path(
    *,
    repo_root: Path,
    slot_doc: dict[str, Any],
    canonical_relative_path: str,
) -> str:
    registered_relative_path = str(slot_doc.get("path", "")).strip()
    if registered_relative_path:
        registered_path = Path(registered_relative_path)
        registered_target = (
            registered_path
            if registered_path.is_absolute()
            else repo_root / registered_path
        )
        if registered_target.is_file():
            return registered_path.as_posix()

    canonical_target = repo_root / canonical_relative_path
    if canonical_target.is_file() or not registered_relative_path:
        return canonical_relative_path
    return Path(registered_relative_path).as_posix()


def _join_relative_path(base_path: str, filename: str) -> str:
    return (Path(base_path) / filename).as_posix()


def _read_text_if_exists(path: Path) -> str:
    try:
        if path.exists() and path.is_file():
            return path.read_text(encoding="utf-8")
    except OSError:
        return ""
    return ""


def _resolve_repo_root(state_path: Path) -> Path:
    normalized = state_path.resolve()
    try:
        if normalized.parent.name == "governance" and normalized.parent.parent.name == "docs":
            return normalized.parent.parent.parent
    except IndexError:
        pass
    return normalized.parent


def _load_state(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise ValueError(f"加载 state 文件需要 PyYAML: {exc}") from exc
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"未找到 state 文件: {path}") from exc
    if not isinstance(raw, dict):
        raise ValueError("state 文件内容必须是映射结构")
    return raw


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


def _dedupe_blocker_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = (str(item.get("task_id", "")).strip(), str(item.get("blocker", "")).strip())
        if not key[0] or not key[1] or key in seen:
            continue
        ordered.append(item)
        seen.add(key)
    return ordered


def _dedupe_action_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        key = (
            str(item.get("scope", "")).strip(),
            str(item.get("task_id", "")).strip(),
            str(item.get("title", "")).strip(),
        )
        if not key[2] or key in seen:
            continue
        ordered.append(item)
        seen.add(key)
    return ordered
