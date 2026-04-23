from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .requirement_link_suggestions import build_requirement_link_suggestions


MAX_TASK_COUNT = 3
TASK_IDS_FIELD_RE = re.compile(r"^(\s*)task_ids:\s*(.*)$")


def build_requirement_seed_apply_plan(
    *,
    state_path: str | Path,
    entity_ids: list[str] | tuple[str, ...] | str,
    allow_manual_confirmation: bool = False,
) -> dict[str, Any]:
    state_path = Path(state_path)
    state = _load_state(state_path)
    task_ids = _normalize_task_ids(entity_ids=entity_ids, state=state)
    requirements = _as_dict(state.get("requirements"))
    subtasks = _as_dict(state.get("subtasks"))

    tasks: list[dict[str, Any]] = []
    for task_id in task_ids:
        suggestion_payload = build_requirement_link_suggestions(
            state_path=state_path,
            entity_id=task_id,
        )
        suggestion = _extract_task_suggestion(suggestion_payload=suggestion_payload, task_id=task_id)
        task_state = _as_dict(subtasks.get(task_id))
        module_id = str(_as_dict(task_state.get("meta")).get("module_id", "")).strip()

        selected_requirement_id = str(suggestion.get("selected_requirement_id") or "").strip() or None
        candidate_requirement_ids = _as_string_list(suggestion.get("candidate_requirement_ids"))
        needs_manual_confirmation = bool(suggestion.get("needs_manual_confirmation"))
        suggestion_status = str(suggestion.get("status", "")).strip() or "unresolved"
        confidence = _as_dict(suggestion.get("confidence"))
        requirement_exists_in_state = bool(
            selected_requirement_id and selected_requirement_id in requirements
        )
        current_task_ids = (
            _as_string_list(
                _as_dict(_as_dict(requirements.get(selected_requirement_id)).get("facts")).get("task_ids")
            )
            if requirement_exists_in_state and selected_requirement_id
            else []
        )
        already_linked = task_id in current_task_ids
        unique_candidate = bool(
            selected_requirement_id
            and len(candidate_requirement_ids) == 1
            and candidate_requirement_ids[0] == selected_requirement_id
        )
        target_path = (
            f"requirements.{selected_requirement_id}.facts.task_ids"
            if selected_requirement_id
            else None
        )

        decision, reason, apply_allowed = _decide_apply_status(
            suggestion_status=suggestion_status,
            selected_requirement_id=selected_requirement_id,
            candidate_requirement_ids=candidate_requirement_ids,
            requirement_exists_in_state=requirement_exists_in_state,
            needs_manual_confirmation=needs_manual_confirmation,
            allow_manual_confirmation=allow_manual_confirmation,
            already_linked=already_linked,
        )

        change_preview = None
        if selected_requirement_id and requirement_exists_in_state:
            after_task_ids = list(current_task_ids)
            if task_id not in after_task_ids:
                after_task_ids.append(task_id)
            change_preview = {
                "op": "append_if_missing",
                "path": target_path,
                "before_task_ids": current_task_ids,
                "after_task_ids": after_task_ids,
            }

        tasks.append(
            {
                "task_id": task_id,
                "module_id": module_id,
                "suggestion_status": suggestion_status,
                "selected_requirement_id": selected_requirement_id,
                "candidate_requirement_ids": candidate_requirement_ids,
                "confidence": confidence,
                "needs_manual_confirmation": needs_manual_confirmation,
                "manual_confirmation_override_used": bool(
                    allow_manual_confirmation and needs_manual_confirmation
                ),
                "requirement_exists_in_state": requirement_exists_in_state,
                "unique_candidate": unique_candidate,
                "already_linked": already_linked,
                "apply_allowed": apply_allowed,
                "decision": decision,
                "reason": reason or str(suggestion.get("reason", "")).strip(),
                "target_path": target_path,
                "change_preview": change_preview,
            }
        )

    rejected_tasks = [
        {
            "task_id": item.get("task_id", ""),
            "decision": item.get("decision", ""),
            "reason": item.get("reason", ""),
        }
        for item in tasks
        if str(item.get("decision", "")).startswith("blocked_")
    ]
    summary = {
        "selected_task_count": len(task_ids),
        "applyable_task_count": sum(1 for item in tasks if bool(item.get("apply_allowed"))),
        "blocked_task_count": len(rejected_tasks),
        "already_linked_count": sum(1 for item in tasks if bool(item.get("already_linked"))),
        "planned_write_count": sum(
            1
            for item in tasks
            if bool(item.get("apply_allowed")) and not bool(item.get("already_linked"))
        ),
        "applied_write_count": 0,
        "state_write_enabled": False,
        "manual_confirmation_override": bool(allow_manual_confirmation),
    }

    return {
        "ok": True,
        "mode": "dry_run",
        "input_state_path": str(state_path.resolve()),
        "entity_ids": task_ids,
        "summary": summary,
        "tasks": tasks,
        "rejected_tasks": rejected_tasks,
        "change_summary": _build_change_summary(tasks),
        "reasoning_notes": [
            "默认模式是 dry-run，只输出 requirement seed 写回计划，不修改 DOC_STATE.yaml。",
            "只允许处理显式选中的 task，且单次最多 3 个。",
            "默认保留人工确认门槛；如 suggestion 标记 needs_manual_confirmation，必须显式传入二次确认开关才可写入。",
            "真正写入时只会最小化追加 requirements.<requirement_id>.facts.task_ids，不会顺手改其他状态字段。",
        ],
    }


def execute_requirement_seed_apply(
    *,
    state_path: str | Path,
    entity_ids: list[str] | tuple[str, ...] | str,
    apply_changes: bool = False,
    allow_manual_confirmation: bool = False,
) -> dict[str, Any]:
    plan = build_requirement_seed_apply_plan(
        state_path=state_path,
        entity_ids=entity_ids,
        allow_manual_confirmation=allow_manual_confirmation,
    )
    if not apply_changes:
        return plan

    blocked_tasks = [
        item
        for item in _as_list_of_dicts(plan.get("tasks"))
        if str(item.get("decision", "")).startswith("blocked_")
    ]
    if blocked_tasks:
        task_ids = ", ".join(
            str(item.get("task_id", "")).strip()
            for item in blocked_tasks
            if item.get("task_id")
        )
        raise ValueError(f"存在不允许 apply 的 task: {task_ids}")

    state_path = Path(state_path)
    state = _load_state(state_path)
    requirements = _as_dict(state.get("requirements"))
    updated_task_ids_by_requirement: dict[str, list[str]] = {
        requirement_id: _as_string_list(
            _as_dict(_as_dict(requirement_obj).get("facts")).get("task_ids")
        )
        for requirement_id, requirement_obj in requirements.items()
    }
    changed_paths: list[str] = []
    written_links: list[dict[str, Any]] = []
    updated_tasks: list[dict[str, Any]] = []

    for task in _as_list_of_dicts(plan.get("tasks")):
        task_record = dict(task)
        selected_requirement_id = str(task_record.get("selected_requirement_id") or "").strip()
        if not selected_requirement_id:
            updated_tasks.append(task_record)
            continue

        if bool(task_record.get("already_linked")):
            task_record["decision"] = "already_linked"
            task_record["write_status"] = "unchanged"
            updated_tasks.append(task_record)
            continue

        current_task_ids = list(updated_task_ids_by_requirement.get(selected_requirement_id, []))
        task_id = str(task_record.get("task_id", "")).strip()
        if task_id not in current_task_ids:
            before_task_ids = list(current_task_ids)
            current_task_ids.append(task_id)
            updated_task_ids_by_requirement[selected_requirement_id] = current_task_ids
            changed_paths.append(str(task_record.get("target_path", "")).strip())
            written_links.append(
                {
                    "task_id": task_id,
                    "requirement_id": selected_requirement_id,
                    "target_path": task_record.get("target_path"),
                    "before_task_ids": before_task_ids,
                    "task_ids_after": list(current_task_ids),
                }
            )
            task_record["decision"] = "written"
            task_record["write_status"] = "written"
        else:
            task_record["decision"] = "already_linked"
            task_record["write_status"] = "unchanged"
        updated_tasks.append(task_record)

    if written_links:
        updated_text = _read_text(state_path)
        for requirement_id in _dedupe_strings(
            [str(item.get("requirement_id", "")).strip() for item in written_links]
        ):
            updated_text = _replace_requirement_task_ids_block(
                original_text=updated_text,
                requirement_id=requirement_id,
                task_ids=updated_task_ids_by_requirement.get(requirement_id, []),
            )
        _write_text(state_path=state_path, text=updated_text)

    result = dict(plan)
    result["mode"] = "apply"
    result["tasks"] = updated_tasks
    affected_tasks = _dedupe_strings(
        [str(item.get("task_id", "")).strip() for item in updated_tasks if item.get("task_id")]
    )
    result["summary"] = {
        **_as_dict(plan.get("summary")),
        "state_write_enabled": True,
        "applied_write_count": len(written_links),
    }
    result["affected_tasks"] = affected_tasks
    result["result_summary"] = {
        "written_requirement_links": written_links,
        "changed_state_paths": _dedupe_strings(changed_paths),
        "affected_tasks": affected_tasks,
        "unchanged_tasks": [
            item.get("task_id", "")
            for item in updated_tasks
            if item.get("write_status") == "unchanged"
        ],
    }
    return result


def write_requirement_seed_apply_output(
    *,
    payload: dict[str, Any],
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _decide_apply_status(
    *,
    suggestion_status: str,
    selected_requirement_id: str | None,
    candidate_requirement_ids: list[str],
    requirement_exists_in_state: bool,
    needs_manual_confirmation: bool,
    allow_manual_confirmation: bool,
    already_linked: bool,
) -> tuple[str, str, bool]:
    if suggestion_status == "ambiguous" or len(candidate_requirement_ids) > 1:
        return (
            "blocked_ambiguous",
            "候选 requirement 不唯一，当前必须拒绝 apply。",
            False,
        )
    if not selected_requirement_id:
        return (
            "blocked_insufficient_evidence",
            "当前没有唯一且可写入的 requirement 候选，不能写回 official state。",
            False,
        )
    if not requirement_exists_in_state:
        return (
            "blocked_requirement_not_in_state",
            "suggested requirement 尚未存在于 official state，当前范围内不能补建 requirement 容器。",
            False,
        )
    if already_linked:
        return (
            "already_linked",
            "当前 requirement 关系已经存在，不需要重复写入。",
            False,
        )
    if needs_manual_confirmation and not allow_manual_confirmation:
        return (
            "blocked_manual_confirmation",
            "该建议仍带 needs_manual_confirmation，默认拒绝 apply；如确认无误，需显式开启二次确认参数。",
            False,
        )
    return (
        "planned",
        "满足当前最小安全条件，可对 requirement 关系执行最小写回。",
        True,
    )


def _build_change_summary(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for task in tasks:
        items.append(
            {
                "task_id": task.get("task_id", ""),
                "decision": task.get("decision", ""),
                "target_path": task.get("target_path"),
                "reason": task.get("reason", ""),
            }
        )
    return items


def _extract_task_suggestion(
    *,
    suggestion_payload: dict[str, Any],
    task_id: str,
) -> dict[str, Any]:
    for collection_name, status in (
        ("resolved_candidates", "resolved"),
        ("ambiguous_candidates", "ambiguous"),
        ("unresolved_tasks", "unresolved"),
    ):
        for item in _as_list_of_dicts(suggestion_payload.get(collection_name)):
            if str(item.get("task_id", "")).strip() != task_id:
                continue
            return {
                "status": status,
                "selected_requirement_id": item.get("selected_requirement_id"),
                "candidate_requirement_ids": _as_string_list(item.get("candidate_requirement_ids")),
                "confidence": _as_dict(item.get("confidence")),
                "needs_manual_confirmation": bool(item.get("needs_manual_confirmation")),
                "reason": str(item.get("reason", "")).strip(),
            }
    return {
        "status": "unresolved",
        "selected_requirement_id": None,
        "candidate_requirement_ids": [],
        "confidence": {"level": "low", "score": 0.0},
        "needs_manual_confirmation": True,
        "reason": "当前没有可用 suggestion 结果。",
    }


def _normalize_task_ids(
    *,
    entity_ids: list[str] | tuple[str, ...] | str,
    state: dict[str, Any],
) -> list[str]:
    raw_values: list[str]
    if isinstance(entity_ids, str):
        raw_values = [item.strip() for item in entity_ids.split(",")]
    else:
        raw_values = [str(item).strip() for item in entity_ids]

    subtasks = _as_dict(state.get("subtasks"))
    task_ids = _dedupe_strings([item for item in raw_values if item])
    if not task_ids:
        raise ValueError("至少需要一个 --entity-id")
    if len(task_ids) > MAX_TASK_COUNT:
        raise ValueError(f"单次最多只允许处理 {MAX_TASK_COUNT} 个 task")
    missing = [task_id for task_id in task_ids if task_id not in subtasks]
    if missing:
        raise ValueError(f"entity-id not found or not a task: {', '.join(missing)}")
    return task_ids


def _load_state(state_path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to read DOC_STATE.yaml") from exc
    loaded = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _replace_requirement_task_ids_block(
    *,
    original_text: str,
    requirement_id: str,
    task_ids: list[str],
) -> str:
    lines = original_text.splitlines(keepends=True)
    requirements_index = _find_top_level_key(lines, "requirements")
    if requirements_index is None:
        raise ValueError("state 文件中缺少 requirements 顶层区块")

    requirement_index = _find_requirement_index(
        lines=lines,
        requirement_id=requirement_id,
        start=requirements_index + 1,
    )
    if requirement_index is None:
        raise ValueError(f"未找到 requirement 容器: {requirement_id}")
    requirement_end = _find_block_end(lines=lines, start=requirement_index + 1, indent=2)

    facts_index = _find_named_block_index(
        lines=lines,
        name="facts",
        start=requirement_index + 1,
        end=requirement_end,
        indent=4,
    )
    if facts_index is None:
        raise ValueError(f"requirement {requirement_id} 缺少 facts 区块")
    facts_end = _find_block_end(lines=lines, start=facts_index + 1, indent=4)

    task_ids_index = _find_task_ids_index(
        lines=lines,
        start=facts_index + 1,
        end=facts_end,
    )
    if task_ids_index is None:
        raise ValueError(f"requirement {requirement_id} 缺少 facts.task_ids")

    task_ids_end = _find_task_ids_block_end(
        lines=lines,
        start=task_ids_index + 1,
        end=facts_end,
        indent=_leading_spaces(lines[task_ids_index]),
    )
    replacement = _render_task_ids_block(
        indent=_leading_spaces(lines[task_ids_index]),
        task_ids=task_ids,
    )
    lines[task_ids_index:task_ids_end] = replacement
    return "".join(lines)


def _find_top_level_key(lines: list[str], key: str) -> int | None:
    target = f"{key}:"
    for index, line in enumerate(lines):
        if line.rstrip("\r\n") == target:
            return index
    return None


def _find_requirement_index(
    *,
    lines: list[str],
    requirement_id: str,
    start: int,
) -> int | None:
    target = f"  {requirement_id}:"
    for index in range(start, len(lines)):
        stripped = lines[index].strip()
        if not stripped:
            continue
        if _leading_spaces(lines[index]) == 0:
            return None
        if lines[index].rstrip("\r\n") == target:
            return index
    return None


def _find_named_block_index(
    *,
    lines: list[str],
    name: str,
    start: int,
    end: int,
    indent: int,
) -> int | None:
    target = f"{' ' * indent}{name}:"
    for index in range(start, end):
        if lines[index].rstrip("\r\n") == target:
            return index
    return None


def _find_task_ids_index(
    *,
    lines: list[str],
    start: int,
    end: int,
) -> int | None:
    for index in range(start, end):
        if TASK_IDS_FIELD_RE.match(lines[index].rstrip("\r\n")):
            return index
    return None


def _find_block_end(
    *,
    lines: list[str],
    start: int,
    indent: int,
) -> int:
    for index in range(start, len(lines)):
        stripped = lines[index].strip()
        if not stripped:
            continue
        if _leading_spaces(lines[index]) <= indent:
            return index
    return len(lines)


def _find_task_ids_block_end(
    *,
    lines: list[str],
    start: int,
    end: int,
    indent: int,
) -> int:
    for index in range(start, end):
        stripped = lines[index].strip()
        if not stripped:
            continue
        line_indent = _leading_spaces(lines[index])
        if stripped.startswith("- "):
            if line_indent >= indent:
                continue
        if line_indent <= indent:
            return index
    return end


def _render_task_ids_block(*, indent: int, task_ids: list[str]) -> list[str]:
    prefix = " " * indent
    if not task_ids:
        return [f"{prefix}task_ids: []\n"]
    lines = [f"{prefix}task_ids:\n"]
    lines.extend(f"{prefix}- {task_id}\n" for task_id in task_ids)
    return lines


def _leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _read_text(state_path: Path) -> str:
    return state_path.read_text(encoding="utf-8")


def _write_text(*, state_path: Path, text: str) -> None:
    with state_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    output: list[str] = []
    for item in value:
        if isinstance(item, str):
            text = item.strip()
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
