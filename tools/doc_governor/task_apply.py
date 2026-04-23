from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .task_patch_preview import build_task_patch_preview


MAX_TASK_COUNT = 3
ALLOWED_DOC_FILENAMES = {"SUBTASK_DESIGN.md", "SUBTASK_IMPLEMENTATION.md"}
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+")


def build_task_readiness_fix_plan(
    *,
    state_path: str | Path,
    evaluate_payload: dict[str, Any],
    entity_id: str,
) -> dict[str, Any]:
    state_path = Path(state_path)
    state = _load_state(state_path)
    repo_root = _resolve_repo_root(state_path)
    requested_task_ids = _parse_task_ids(entity_id=entity_id, state=state)

    tasks: list[dict[str, Any]] = []
    requirement_seed_actions: list[dict[str, Any]] = []

    for task_id in requested_task_ids:
        preview = build_task_patch_preview(
            state_path=state_path,
            evaluate_payload=evaluate_payload,
            entity_id=task_id,
        )
        task_preview_map = {
            str(item.get("task_id", "")).strip(): item
            for item in _as_list_of_dicts(preview.get("task_document_patch_previews"))
            if item.get("task_id")
        }
        deferred_map = {
            str(item.get("task_id", "")).strip(): item
            for item in _as_list_of_dicts(_as_dict(preview.get("batch_preview")).get("deferred_tasks"))
            if item.get("task_id")
        }
        requirement_seed_map = {
            str(item.get("task_id", "")).strip(): item
            for item in _as_list_of_dicts(preview.get("requirement_seed_patch_preview"))
            if item.get("task_id")
        }

        requirement_action = _build_requirement_seed_action(requirement_seed_map.get(task_id))
        if requirement_action:
            requirement_seed_actions.append(requirement_action)

        if task_id in deferred_map:
            deferred_item = deferred_map[task_id]
            tasks.append(
                {
                    "task_id": task_id,
                    "module_id": str(deferred_item.get("module_id", "")).strip(),
                    "apply_allowed": False,
                    "reason": str(deferred_item.get("reason", "")).strip() or "当前 task 被 deferred，不能直接 apply。",
                    "apply_blockers": _as_string_list(deferred_item.get("module_inherited_blockers")) or [
                        "deferred_task"
                    ],
                    "files": [],
                    "manual_fill_fields": [],
                    "requirement_seed_action": requirement_action,
                }
            )
            continue

        task_preview = _as_dict(task_preview_map.get(task_id))
        if not task_preview:
            tasks.append(
                {
                    "task_id": task_id,
                    "module_id": "",
                    "apply_allowed": False,
                    "reason": "当前 task 没有可执行的 patch preview，不能直接 apply。",
                    "apply_blockers": ["missing_patch_preview"],
                    "files": [],
                    "manual_fill_fields": [],
                    "requirement_seed_action": requirement_action,
                }
            )
            continue

        file_plans = _build_file_plans(
            repo_root=repo_root,
            task_preview=task_preview,
        )
        module_level_blockers = _as_string_list(task_preview.get("module_level_blockers"))
        apply_allowed = not module_level_blockers and bool(file_plans)
        apply_blockers = list(module_level_blockers)
        if not file_plans:
            apply_blockers.append("no_file_changes_planned")

        tasks.append(
            {
                "task_id": task_id,
                "module_id": str(task_preview.get("module_id", "")).strip(),
                "apply_allowed": apply_allowed,
                "reason": str(task_preview.get("reason", "")).strip(),
                "apply_blockers": _dedupe_strings(apply_blockers),
                "files": file_plans,
                "manual_fill_fields": _as_string_list(task_preview.get("manual_fill_fields")),
                "requirement_seed_action": requirement_action,
            }
        )

    blocked_tasks = [item for item in tasks if not bool(item.get("apply_allowed"))]
    planned_file_count = sum(len(_as_list_of_dicts(item.get("files"))) for item in tasks)
    return {
        "ok": True,
        "mode": "dry_run",
        "input_state_path": str(state_path.resolve()),
        "entity_ids": requested_task_ids,
        "summary": {
            "selected_task_count": len(requested_task_ids),
            "applyable_task_count": len(tasks) - len(blocked_tasks),
            "blocked_task_count": len(blocked_tasks),
            "planned_file_count": planned_file_count,
            "written_file_count": 0,
            "requirement_seed_action_count": len(requirement_seed_actions),
            "state_write_enabled": False,
        },
        "requirement_seed_actions": requirement_seed_actions,
        "tasks": tasks,
        "change_summary": _build_change_summary(tasks=tasks, requirement_seed_actions=requirement_seed_actions),
        "reasoning_notes": [
            "默认模式是 dry-run，只输出执行计划，不写任何文件。",
            "本批次不会写 DOC_STATE.yaml；requirement seed 仍停留在预览/阻断层。",
            "真正允许 apply 的内容只限 task 文档中文章节骨架、标题替换、旧状态语义清理与空白占位段落。",
        ],
    }


def execute_task_readiness_fix(
    *,
    state_path: str | Path,
    evaluate_payload: dict[str, Any],
    entity_id: str,
    apply_changes: bool = False,
) -> dict[str, Any]:
    plan = build_task_readiness_fix_plan(
        state_path=state_path,
        evaluate_payload=evaluate_payload,
        entity_id=entity_id,
    )
    if not apply_changes:
        return plan

    blocked_tasks = [item for item in _as_list_of_dicts(plan.get("tasks")) if not bool(item.get("apply_allowed"))]
    if blocked_tasks:
        task_ids = ", ".join(str(item.get("task_id", "")).strip() for item in blocked_tasks if item.get("task_id"))
        raise ValueError(f"存在不允许 apply 的 task: {task_ids}")

    repo_root = _resolve_repo_root(Path(state_path))
    written_file_count = 0
    updated_tasks: list[dict[str, Any]] = []
    for task in _as_list_of_dicts(plan.get("tasks")):
        updated_files: list[dict[str, Any]] = []
        for file_plan in _as_list_of_dicts(task.get("files")):
            updated_files.append(_apply_file_plan(repo_root=repo_root, file_plan=file_plan))
            if updated_files[-1]["status"] == "written":
                written_file_count += 1
        updated_task = dict(task)
        updated_task["files"] = updated_files
        updated_tasks.append(updated_task)

    result = dict(plan)
    result["mode"] = "apply"
    result["tasks"] = updated_tasks
    summary = _as_dict(result.get("summary"))
    summary["written_file_count"] = written_file_count
    result["summary"] = summary
    result["result_summary"] = {
        "written_files": [
            file_plan.get("path", "")
            for task in updated_tasks
            for file_plan in _as_list_of_dicts(task.get("files"))
            if file_plan.get("status") == "written"
        ],
        "manual_fill_fields_remaining": [
            {
                "task_id": task.get("task_id", ""),
                "fields": _as_string_list(task.get("manual_fill_fields")),
            }
            for task in updated_tasks
            if _as_string_list(task.get("manual_fill_fields"))
        ],
    }
    return result


def render_task_readiness_fix_plan_markdown(payload: dict[str, Any]) -> str:
    summary = _as_dict(payload.get("summary"))
    lines = [
        "# 任务 readiness 修复执行计划",
        "",
        "## 摘要",
        f"- 模式: {payload.get('mode', '')}",
        f"- 目标 task: {', '.join(_as_string_list(payload.get('entity_ids'))) or '无'}",
        f"- 计划文件数: {summary.get('planned_file_count', 0)}",
        f"- 实际写入文件数: {summary.get('written_file_count', 0)}",
        f"- 被阻断 task 数量: {summary.get('blocked_task_count', 0)}",
        "",
        "## requirement seed 动作",
    ]
    for item in _as_list_of_dicts(payload.get("requirement_seed_actions")):
        lines.append(
            f"- {item.get('task_id', '')}: {item.get('status', '')} | "
            f"{item.get('target_path', '无目标路径')} | {item.get('reason', '')}"
        )

    lines.extend(["", "## task 执行计划"])
    for task in _as_list_of_dicts(payload.get("tasks")):
        lines.append(
            f"- {task.get('task_id', '')}: apply_allowed={bool(task.get('apply_allowed'))} | {task.get('reason', '')}"
        )
        for file_plan in _as_list_of_dicts(task.get("files")):
            lines.append(
                f"  - {file_plan.get('path', '')}: {file_plan.get('status', '')} | "
                f"预填={', '.join(_as_string_list(file_plan.get('prefill_fields'))) or '无'} | "
                f"人工填写={', '.join(_as_string_list(file_plan.get('manual_fill_fields'))) or '无'}"
            )

    notes = payload.get("reasoning_notes")
    if isinstance(notes, list) and notes:
        lines.extend(["", "## 说明"])
        for note in notes:
            text = str(note).strip()
            if text:
                lines.append(f"- {text}")
    return "\n".join(lines) + "\n"


def write_task_readiness_fix_plan_output(
    *,
    payload: dict[str, Any],
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".md":
        path.write_text(render_task_readiness_fix_plan_markdown(payload), encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _build_requirement_seed_action(item: dict[str, Any] | None) -> dict[str, Any] | None:
    if not item:
        return None
    suggested_requirement_id = str(item.get("suggested_requirement_id") or "").strip() or None
    if bool(item.get("needs_manual_confirmation")):
        status = "blocked_manual_confirmation"
        reason = "requirement seed 仍需人工确认，本批次不会自动写回 state。"
    elif not suggested_requirement_id:
        status = "blocked_insufficient_evidence"
        reason = "当前没有足够 requirement 证据，不应生成自动写回。"
    else:
        status = "blocked_state_write_disabled"
        reason = "本批次明确禁止写 DOC_STATE.yaml，requirement seed 只保留为执行前预览。"
    return {
        "task_id": str(item.get("task_id", "")).strip(),
        "suggested_requirement_id": suggested_requirement_id,
        "target_path": item.get("target_path"),
        "status": status,
        "reason": reason,
        "apply_allowed": False,
        "needs_manual_confirmation": bool(item.get("needs_manual_confirmation")),
        "confidence": _as_dict(item.get("confidence")),
    }


def _build_file_plans(
    *,
    repo_root: Path,
    task_preview: dict[str, Any],
) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    implementation_preview = _as_dict(task_preview.get("implementation_doc_patch_preview"))
    if bool(implementation_preview.get("enabled")):
        outputs.append(
            _make_file_plan(
                repo_root=repo_root,
                task_preview=task_preview,
                doc_kind="implementation",
                patch_preview=implementation_preview,
            )
        )
    design_preview = _as_dict(task_preview.get("design_doc_patch_preview"))
    if bool(design_preview.get("enabled")):
        outputs.append(
            _make_file_plan(
                repo_root=repo_root,
                task_preview=task_preview,
                doc_kind="design",
                patch_preview=design_preview,
            )
        )
    return outputs


def _make_file_plan(
    *,
    repo_root: Path,
    task_preview: dict[str, Any],
    doc_kind: str,
    patch_preview: dict[str, Any],
) -> dict[str, Any]:
    relative_path = str(patch_preview.get("target_relative_path", "")).strip()
    path = (repo_root / relative_path).resolve()
    if path.name not in ALLOWED_DOC_FILENAMES:
        raise ValueError(f"file plan points to non-target file: {relative_path}")

    prefill_fields = _pick_doc_fields(
        fields=_as_string_list(task_preview.get("carry_over_fields")),
        doc_kind=doc_kind,
    )
    manual_fill_fields = _pick_doc_fields(
        fields=_as_string_list(task_preview.get("manual_fill_fields")),
        doc_kind=doc_kind,
    )
    return {
        "doc_kind": doc_kind,
        "path": relative_path,
        "status": "planned",
        "write_allowed": True,
        "cleanup_old_status_semantics": bool(patch_preview.get("cleanup_old_status_semantics")),
        "section_changes": _as_list_of_dicts(patch_preview.get("section_patch_preview")),
        "prefill_fields": prefill_fields,
        "manual_fill_fields": manual_fill_fields,
        "original_exists": path.exists(),
    }


def _apply_file_plan(
    *,
    repo_root: Path,
    file_plan: dict[str, Any],
) -> dict[str, Any]:
    relative_path = str(file_plan.get("path", "")).strip()
    target = (repo_root / relative_path).resolve()
    if target.name not in ALLOWED_DOC_FILENAMES:
        raise ValueError(f"refuse to write non-target file: {relative_path}")

    original_text = _read_text_if_exists(target)
    new_text = _render_target_markdown(
        doc_kind=str(file_plan.get("doc_kind", "")).strip(),
        original_text=original_text,
        prefill_fields=_as_string_list(file_plan.get("prefill_fields")),
        manual_fill_fields=_as_string_list(file_plan.get("manual_fill_fields")),
    )
    updated = dict(file_plan)
    if new_text == original_text:
        updated["status"] = "unchanged"
        return updated

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(new_text, encoding="utf-8")
    disk_text = target.read_text(encoding="utf-8")
    if disk_text != new_text:
        raise ValueError(f"写入后回读校验失败: {relative_path}")
    updated["status"] = "written"
    return updated


def _render_target_markdown(
    *,
    doc_kind: str,
    original_text: str,
    prefill_fields: list[str],
    manual_fill_fields: list[str],
) -> str:
    if doc_kind == "implementation":
        goal_lines = _extract_goal_lines(original_text) if "goal" in prefill_fields else []
        return _render_implementation_doc(goal_lines=goal_lines, manual_fill_fields=manual_fill_fields)
    if doc_kind == "design":
        goal_lines = _extract_goal_lines(original_text)
        tech_lines = _extract_section_lines(
            original_text,
            ["## 5. 技术方案", "## 5. Technical Approach", "## Technical Approach", "## 5. Solution"],
        )
        return _render_design_doc(goal_lines=goal_lines, tech_lines=tech_lines, manual_fill_fields=manual_fill_fields)
    raise ValueError(f"unsupported doc kind: {doc_kind}")


def _render_implementation_doc(
    *,
    goal_lines: list[str],
    manual_fill_fields: list[str],
) -> str:
    lines = [
        "# 子任务实施文档",
        "",
        "## 3. 本轮实施目标",
    ]
    lines.extend(goal_lines or ["- 待人工确认：本轮实施目标"])
    lines.extend(
        [
            "",
            "## 5. 允许修改范围",
            "",
            "### 5.1 允许修改",
            "- 待人工填写：allowed_modify_paths",
            "",
            "### 5.2 禁止修改",
            "- 待人工确认：forbidden_paths（如无额外限制可保留为空）",
            "",
            "## 7. 测试与验证",
            "",
            "### 7.1 自动化验证",
            "- 待人工填写：required_tests",
            "",
            "## 8. 完成判定",
            "- 待人工填写：acceptance_criteria",
        ]
    )
    if manual_fill_fields:
        lines.extend(
            [
                "",
                "## 9. 人工补充提醒",
                f"- 本轮仍需人工填写：{', '.join(_dedupe_strings(manual_fill_fields))}",
            ]
        )
    return "\n".join(lines) + "\n"


def _render_design_doc(
    *,
    goal_lines: list[str],
    tech_lines: list[str],
    manual_fill_fields: list[str],
) -> str:
    lines = [
        "# 子任务设计文档",
        "",
        "## 3. 子任务目标",
    ]
    lines.extend(goal_lines or ["- 待人工填写：子任务目标"])
    lines.extend(["", "## 5. 技术方案"])
    lines.extend(tech_lines or ["- 待人工填写：技术方案"])
    if manual_fill_fields:
        lines.extend(
            [
                "",
                "## 6. 人工补充提醒",
                "- 本文档目前只补最小章节骨架，详细设计仍需人工继续完善。",
            ]
        )
    return "\n".join(lines) + "\n"


def _extract_goal_lines(text: str) -> list[str]:
    for heading in (
        "## 3. 本轮实施目标",
        "## 3. 子任务目标",
        "## 3. Goal",
        "## Goal",
        "## 3. Goals",
    ):
        lines = _extract_section_lines(text, [heading])
        if lines:
            return lines
    return []


def _extract_section_lines(text: str, headings: list[str]) -> list[str]:
    if not text:
        return []
    lines = text.splitlines()
    start_index: int | None = None
    for index, line in enumerate(lines):
        if line.strip() in headings:
            start_index = index + 1
            break
    if start_index is None:
        return []

    collected: list[str] = []
    for line in lines[start_index:]:
        if HEADING_RE.match(line):
            break
        stripped = line.rstrip()
        if not stripped and not collected:
            continue
        collected.append(stripped)
    result = [line for line in collected if line.strip()]
    return result


def _build_change_summary(
    *,
    tasks: list[dict[str, Any]],
    requirement_seed_actions: list[dict[str, Any]],
) -> list[str]:
    notes: list[str] = []
    if requirement_seed_actions:
        notes.append("requirement seed 继续停留在计划/阻断层，本轮不会写回 state。")
    for task in tasks:
        task_id = str(task.get("task_id", "")).strip()
        if bool(task.get("apply_allowed")):
            file_count = len(_as_list_of_dicts(task.get("files")))
            notes.append(f"{task_id} 可进入半自动 apply，计划落地 {file_count} 个 markdown 骨架文件。")
        else:
            blockers = ", ".join(_as_string_list(task.get("apply_blockers"))) or "未知阻断"
            notes.append(f"{task_id} 当前不能直接 apply：{blockers}")
    return notes


def _parse_task_ids(
    *,
    entity_id: str,
    state: dict[str, Any],
) -> list[str]:
    raw_ids = [item.strip() for item in str(entity_id).split(",") if item.strip()]
    task_ids = _dedupe_strings(raw_ids)
    if not task_ids:
        raise ValueError("必须提供至少一个 task entity-id")
    if len(task_ids) > MAX_TASK_COUNT:
        raise ValueError(f"一次最多只允许处理 {MAX_TASK_COUNT} 个 task")
    subtasks = _as_dict(state.get("subtasks"))
    missing = [task_id for task_id in task_ids if task_id not in subtasks]
    if missing:
        raise ValueError(f"entity-id 不是有效 task: {', '.join(missing)}")
    return task_ids


def _pick_doc_fields(*, fields: list[str], doc_kind: str) -> list[str]:
    if doc_kind == "implementation":
        allowed = {"goal", "allowed_modify_paths", "forbidden_paths", "required_tests", "acceptance_criteria"}
    else:
        allowed = {"goal", "design_key_sections"}
    return [field for field in fields if field in allowed]


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
