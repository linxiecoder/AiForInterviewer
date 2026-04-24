from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schema import IMPLEMENTATION_DOC_STATES

MAX_TASK_COUNT = 10
STATE_NOT_ACTIVE_GATE = "gate:implementation_doc_not_active"
FORMAL_WINDOW_CLOSED = "policy:formal_window_closed"


def build_task_implementation_state_sync_plan(
    *,
    state_path: str | Path,
    evaluate_payload: dict[str, Any],
    entity_ids: list[str] | tuple[str, ...] | str,
) -> dict[str, Any]:
    state_path = Path(state_path)
    state = _load_state(state_path)
    subtasks = _as_dict(state.get("subtasks"))
    evaluate_subtasks = _as_dict(_as_dict(evaluate_payload).get("subtasks"))
    task_ids = _parse_task_ids(entity_ids=entity_ids, subtasks=subtasks)

    tasks: list[dict[str, Any]] = []
    blocked_tasks: list[dict[str, str]] = []

    for task_id in task_ids:
        task_obj = _as_dict(subtasks.get(task_id))
        meta = _as_dict(task_obj.get("meta"))
        state_obj = _as_dict(task_obj.get("state"))
        confirmed = _as_dict(state_obj.get("confirmed"))
        evaluate_obj = _as_dict(evaluate_subtasks.get(task_id))
        derived = _as_dict(evaluate_obj.get("derived"))

        current_state = str(confirmed.get("implementation_doc_state", "")).strip()
        if current_state not in IMPLEMENTATION_DOC_STATES:
            current_state = "missing"

        requirement_ids = _dedupe_strings(_as_string_list(derived.get("requirement_ids")))
        blocker_refs = _dedupe_strings(_as_string_list(derived.get("implementation_blocker_refs")))

        decision: str
        reason: str
        apply_allowed = False
        planned_state_paths: list[str] = []

        if len(requirement_ids) == 0:
            decision = "blocked_requirement_relation_missing"
            reason = "task requirement relation 缺失，不能进行 implementation_doc_state 写回"
        elif len(requirement_ids) > 1:
            decision = "blocked_requirement_relation_ambiguous"
            reason = "task requirement relation 不唯一（多于 1 条），不能进行 implementation_doc_state 写回"
        elif current_state == "active_working_doc":
            decision = "already_active"
            reason = "implementation_doc_state 已是 active_working_doc，当前样本无须写回"
        elif not _design_docs_ready(blocker_refs):
            decision = "blocked_doc_artifacts_not_ready"
            reason = "design_doc / implementation_doc 仍未完成最小同步，不能推进 implementation_doc_state"
        elif _has_non_state_blockers(blocker_refs):
            decision = "blocked_other_blockers"
            reason = "除 implementation_doc_state 与 formal_window 外仍有可见 blocker，人工确认不足"
        else:
            decision = "planned"
            reason = "满足更高一层前提，可推进 implementation_doc_state"
            apply_allowed = True
            planned_state_paths = [f"subtasks.{task_id}.state.confirmed.implementation_doc_state"]

        predicted_blockers = [
            item for item in blocker_refs if item != STATE_NOT_ACTIVE_GATE
        ]

        task_payload = {
            "task_id": task_id,
            "module_id": str(meta.get("module_id", "")).strip(),
            "requirement_ids": requirement_ids,
            "current_implementation_doc_state": current_state,
            "current_blocker_refs": blocker_refs,
            "predicted_blocker_refs_after_writeback": predicted_blockers,
            "target_state_path": "subtasks.{task_id}.state.confirmed.implementation_doc_state".replace(
                "{task_id}",
                task_id,
            ),
            "planned_state_paths": planned_state_paths,
            "remaining_gap_count": len(predicted_blockers),
            "remaining_gap_refs": predicted_blockers,
            "apply_allowed": apply_allowed,
            "decision": decision,
            "reason": reason,
            "proposed_changes": {
                "implementation_doc_state": "active_working_doc" if apply_allowed else None
            },
        }
        tasks.append(task_payload)
        if str(decision).startswith("blocked_"):
            blocked_tasks.append(
                {
                    "task_id": task_id,
                    "decision": decision,
                    "reason": reason,
                }
            )

    summary = {
        "selected_task_count": len(task_ids),
        "planned_task_count": sum(1 for item in tasks if item.get("apply_allowed")),
        "blocked_task_count": len(blocked_tasks),
        "already_active_count": sum(
            1 for item in tasks if item.get("decision") == "already_active"
        ),
        "written_task_count": 0,
        "written_state_count": 0,
        "state_write_enabled": False,
    }

    return {
        "ok": True,
        "mode": "dry_run",
        "input_state_path": str(state_path.resolve()),
        "entity_ids": task_ids,
        "summary": summary,
        "tasks": tasks,
        "blocked_tasks": blocked_tasks,
        "change_summary": tasks,
        "reasoning_notes": [
            "仅输出 implementation_doc_state 受控变更建议",
            "默认 dry-run；加 --apply 后才执行 state 写回",
            "仅处理 explicit entity-id 指定的任务集合",
            "只改 subtasks.<task>.state.confirmed.implementation_doc_state 字段",
            "不改 readiness / formal_window_open / documents",
        ],
    }


def execute_task_implementation_state_sync(
    *,
    state_path: str | Path,
    evaluate_payload: dict[str, Any],
    entity_ids: list[str] | tuple[str, ...] | str,
    apply_changes: bool = False,
) -> dict[str, Any]:
    plan = build_task_implementation_state_sync_plan(
        state_path=state_path,
        evaluate_payload=evaluate_payload,
        entity_ids=entity_ids,
    )
    if not apply_changes:
        return plan

    blocked_tasks = [
        item
        for item in plan.get("tasks", [])
        if str(item.get("decision", "")).startswith("blocked_")
    ]
    if blocked_tasks:
        labels = ", ".join(
            str(item.get("task_id", "")).strip()
            for item in blocked_tasks
            if item.get("task_id")
        )
        raise ValueError(f"apply 不允许: blocked task: {labels}")

    state = _load_state(Path(state_path))
    state_path = Path(state_path)
    subtasks = _as_dict(state.setdefault("subtasks", {}))

    written_task_count = 0
    written_state_count = 0
    changed_state_paths: list[str] = []

    for item in _as_list_of_dicts(plan.get("tasks")):
        if not item.get("apply_allowed"):
            continue
        task_id = str(item.get("task_id", "")).strip()
        task_obj = _as_dict(subtasks.get(task_id))
        if not task_obj:
            continue
        state_obj = _as_dict(task_obj.setdefault("state", {}))
        confirmed = _as_dict(state_obj.setdefault("confirmed", {}))
        confirmed["implementation_doc_state"] = "active_working_doc"
        state_obj["confirmed"] = confirmed
        task_obj["state"] = state_obj
        subtasks[task_id] = task_obj
        written_task_count += 1
        planned_path = str(item.get("target_state_path", "")).strip()
        if planned_path:
            changed_state_paths.append(planned_path)
        written_state_count += 1

    if written_task_count:
        state["subtasks"] = subtasks
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("PyYAML is required to write DOC_STATE.yaml") from exc
        text = yaml.safe_dump(state, sort_keys=False, allow_unicode=True, width=120)
        _write_text(state_path=state_path, text=text)

    result = dict(plan)
    result["mode"] = "apply"
    result["summary"] = {
        **_as_dict(plan.get("summary")),
        "written_task_count": written_task_count,
        "written_state_count": written_state_count,
        "state_write_enabled": True,
    }
    result["result_summary"] = {
        "written_tasks": [
            item.get("task_id", "")
            for item in _as_list_of_dicts(plan.get("tasks"))
            if item.get("apply_allowed")
        ],
        "written_state_paths": _dedupe_strings(changed_state_paths),
    }
    return result


def write_task_implementation_state_sync_output(
    *,
    payload: dict[str, Any],
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _design_docs_ready(blocker_refs: list[str]) -> bool:
    blocker_set = set(blocker_refs)
    return "doc:design_doc" not in blocker_set and "doc:implementation_doc" not in blocker_set


def _has_non_state_blockers(blocker_refs: list[str]) -> bool:
    for blocker in blocker_refs:
        if blocker == STATE_NOT_ACTIVE_GATE:
            continue
        if blocker == FORMAL_WINDOW_CLOSED:
            continue
        return True
    return False


def _parse_task_ids(
    *,
    entity_ids: list[str] | tuple[str, ...] | str,
    subtasks: dict[str, Any],
) -> list[str]:
    if isinstance(entity_ids, str):
        raw_items = [part.strip() for part in entity_ids.split(",") if part.strip()]
    else:
        raw_items = [str(item).strip() for item in entity_ids if str(item).strip()]
    task_ids = _dedupe_strings(raw_items)
    if not task_ids:
        raise ValueError("--entity-id is required")
    if len(task_ids) > MAX_TASK_COUNT:
        raise ValueError(f"single run supports up to {MAX_TASK_COUNT} task ids")
    missing = [task_id for task_id in task_ids if task_id not in subtasks]
    if missing:
        raise ValueError(f"entity-id not found or not a task: {', '.join(missing)}")
    return task_ids


def _load_state(state_path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("PyYAML is required to read DOC_STATE.yaml") from exc
    raw = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def _write_text(*, state_path: Path, text: str) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if isinstance(item, str) and item.strip()]


def _as_list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


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
