from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
from pathlib import Path
from typing import Any

from .confirm import confirm_transition
from .task_state_writeback import build_task_state_writeback_preview


MAX_TASK_COUNT = 3
IMPLEMENTATION_DOC_STATE_VALUE = "active_working_doc"


def execute_task_state_apply(
    *,
    state_path: str | Path,
    evaluate_payload: dict[str, Any],
    entity_ids: list[str] | tuple[str, ...] | str,
    apply_changes: bool = False,
    actor: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    state_path = Path(state_path).resolve()
    task_ids = _normalize_entity_ids(entity_ids)
    if len(task_ids) > MAX_TASK_COUNT:
        raise ValueError(f"一次最多只允许处理 {MAX_TASK_COUNT} 个 task")

    preview = build_task_state_writeback_preview(
        state_path=state_path,
        evaluate_payload=evaluate_payload,
        entity_ids=task_ids,
    )

    repo_root = _resolve_repo_root_for_confirm(state_path)
    tasks: list[dict[str, Any]] = []
    eligible_count = 0
    applied_count = 0
    blocked_count = 0

    for item in _as_list_of_dicts(preview.get("tasks")):
        task_id = str(item.get("task_id", "")).strip()
        apply_allowed = bool(item.get("eligible_for_writeback"))
        if apply_allowed:
            eligible_count += 1
        else:
            blocked_count += 1

        proposed_changes = _as_dict(item.get("proposed_changes"))
        basis = _build_basis(item)
        task_result = {
            "task_id": task_id,
            "module_id": str(item.get("module_id", "")).strip(),
            "status": str(item.get("status", "")).strip(),
            "apply_allowed": apply_allowed,
            "recommended_value": (
                str(proposed_changes.get("implementation_doc_state", "")).strip() or None
            ),
            "write_target_field": f"subtasks.{task_id}.state.confirmed.implementation_doc_state",
            "write_target_path": state_path.as_posix(),
            "basis": basis,
            "current_blocker_refs": _as_string_list(item.get("current_blocker_refs")),
            "predicted_blocker_refs_after_writeback": _as_string_list(
                item.get("predicted_blocker_refs_after_writeback")
            ),
            "remaining_gap_categories": _as_string_list(item.get("remaining_gap_categories")),
            "suggest_preflight_open_window": bool(item.get("window_only_after_writeback")),
            "confirm_channel": "confirm-transition",
            "suggested_confirm_command": str(item.get("suggested_confirm_command", "")).strip(),
            "dry_run_result": None,
            "apply_result": None,
        }

        if apply_allowed:
            task_result["dry_run_result"] = _invoke_confirm_transition(
                repo_root=repo_root,
                state_path=state_path,
                task_id=task_id,
                proposed_changes=proposed_changes,
                mode="dry-run",
                actor=None,
                reason=str(item.get("suggested_state_transition", {}))
                and "Decision: activate implementation_doc_state after task content gates cleared"
                or "",
            )
        tasks.append(task_result)

    if apply_changes:
        if not (actor and str(actor).strip()):
            raise ValueError("apply 模式必须显式提供 --actor")
        if not (reason and str(reason).strip()):
            raise ValueError("apply 模式必须显式提供 --reason")
        blocked_tasks = [item["task_id"] for item in tasks if not bool(item.get("apply_allowed"))]
        if blocked_tasks:
            raise ValueError(f"存在不允许 apply 的 task: {', '.join(blocked_tasks)}")
        dry_run_failures = [
            item["task_id"]
            for item in tasks
            if not _confirm_ok(_as_dict(item.get("dry_run_result")))
        ]
        if dry_run_failures:
            raise ValueError(
                "底层 confirm-transition dry-run 失败，拒绝执行 apply: "
                + ", ".join(dry_run_failures)
            )
        for item in tasks:
            item["apply_result"] = _invoke_confirm_transition(
                repo_root=repo_root,
                state_path=state_path,
                task_id=str(item.get("task_id", "")).strip(),
                proposed_changes={
                    "implementation_doc_state": IMPLEMENTATION_DOC_STATE_VALUE,
                },
                mode="approve",
                actor=actor,
                reason=reason,
            )
            if _confirm_ok(_as_dict(item.get("apply_result"))):
                applied_count += 1

    summary = {
        "selected_task_count": len(tasks),
        "eligible_task_count": eligible_count,
        "blocked_task_count": blocked_count,
        "applied_task_count": applied_count,
        "suggest_preflight_open_window_count": sum(
            1 for item in tasks if bool(item.get("suggest_preflight_open_window"))
        ),
        "state_write_target_path": state_path.as_posix(),
    }
    reasoning_notes = [
        "本 wrapper 只处理 implementation_doc_state，不写 formal_window_open，不推进 round，不改 task 文档。",
        "默认模式是 dry-run；只有显式 --apply 才会通过 confirm-transition approve 写回 official state。",
        "若内容 blocker 仍未清掉，则 wrapper 会拒绝 apply，避免把未成熟 task 提前推进到状态层。",
    ]
    return {
        "ok": True,
        "mode": "apply" if apply_changes else "dry_run",
        "summary": summary,
        "tasks": tasks,
        "reasoning_notes": reasoning_notes,
    }


def _invoke_confirm_transition(
    *,
    repo_root: Path,
    state_path: Path,
    task_id: str,
    proposed_changes: dict[str, Any],
    mode: str,
    actor: str | None,
    reason: str | None,
) -> dict[str, Any]:
    args = argparse.Namespace(
        input=state_path.as_posix(),
        entity_type="subtask",
        entity_id=task_id,
        proposed_changes=json.dumps(proposed_changes, ensure_ascii=False),
        evidence_ref=[],
        mode=mode,
        actor=actor,
        reason=reason,
        round_id=None,
    )
    stdout = io.StringIO()
    previous = Path.cwd()
    try:
        os.chdir(repo_root)
        with contextlib.redirect_stdout(stdout):
            exit_code = confirm_transition(args)
    finally:
        os.chdir(previous)

    raw_output = stdout.getvalue().strip()
    payload: dict[str, Any]
    if raw_output:
        try:
            parsed = json.loads(raw_output)
            payload = parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            payload = {"ok": False, "raw_output": raw_output}
    else:
        payload = {"ok": exit_code == 0}
    payload["exit_code"] = exit_code
    return payload


def _confirm_ok(payload: dict[str, Any]) -> bool:
    return bool(payload) and int(payload.get("exit_code", 1)) == 0 and bool(payload.get("ok"))


def _build_basis(item: dict[str, Any]) -> list[str]:
    basis = [
        f"preview_status={str(item.get('status', '')).strip()}",
        (
            "current_implementation_doc_state="
            + str(item.get("current_implementation_doc_state", "")).strip()
        ),
    ]
    current_blockers = _as_string_list(item.get("current_blocker_refs"))
    if current_blockers:
        basis.append("current_blocker_refs=" + ", ".join(current_blockers))
    predicted = _as_string_list(item.get("predicted_blocker_refs_after_writeback"))
    if predicted:
        basis.append("predicted_after_writeback=" + ", ".join(predicted))
    else:
        basis.append("predicted_after_writeback=none")
    if bool(item.get("window_only_after_writeback")):
        basis.append("writeback 后只剩 formal_window_closed，可转 preflight-open-window")
    return basis


def _normalize_entity_ids(entity_ids: list[str] | tuple[str, ...] | str) -> list[str]:
    if isinstance(entity_ids, str):
        raw_items = [part.strip() for part in entity_ids.split(",") if part.strip()]
    else:
        raw_items = []
        for item in entity_ids:
            raw_items.extend(part.strip() for part in str(item).split(",") if part.strip())
    task_ids = _dedupe_strings(raw_items)
    if not task_ids:
        raise ValueError("必须显式指定至少一个 --entity-id")
    return task_ids


def _resolve_repo_root_for_confirm(state_path: Path) -> Path:
    normalized = state_path.resolve()
    try:
        if normalized.parent.name == "governance" and normalized.parent.parent.name == "docs":
            return normalized.parent.parent.parent
    except IndexError:
        pass
    raise ValueError("state apply wrapper 仅支持 docs/governance/DOC_STATE.yaml official state 路径")


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
        seen.add(text)
        ordered.append(text)
    return ordered
