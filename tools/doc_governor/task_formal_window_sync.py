from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
from pathlib import Path
from typing import Any

from .confirm import confirm_transition
from .task_readiness_state_sync import (
    MAX_TASK_COUNT,
    _as_dict,
    _as_list_of_dicts,
    _as_str,
    _as_string_list,
    _classify_blockers,
    _confirm_ok,
    _dedupe_strings,
    _load_state,
    _normalize_entity_ids,
    _normalize_readiness,
    _resolve_repo_root_for_confirm,
    _slot_ready,
)
from .task_state_dependency_map import (
    ALLOWED_OPEN_READINESS,
    FORMAL_WINDOW_BLOCKER,
    build_task_state_dependency_map,
)
from .task_window_bridge import build_task_window_bridge

POLICY_ENTITY_TYPE = "policy"
POLICY_ENTITY_ID = "global_policy"
FORMAL_WINDOW_TARGET_VALUE = True


def build_task_formal_window_sync_preview(
    *,
    state_path: str | Path,
    evaluate_payload: dict[str, Any],
    entity_ids: list[str] | tuple[str, ...] | str | None,
) -> dict[str, Any]:
    state_path = Path(state_path).resolve()
    state = _load_state(state_path)
    global_policy = _as_dict(state.get("global_policy"))
    subtasks = _as_dict(state.get("subtasks"))
    evaluate_subtasks = _as_dict(evaluate_payload.get("subtasks"))
    task_ids = _normalize_entity_ids(entity_ids=entity_ids, state=state)

    dependency_map_payload = build_task_state_dependency_map(
        state_path=state_path,
        evaluate_payload=evaluate_payload,
        entity_ids=task_ids,
    )
    dependency_items = _index_by_task_id(_as_list_of_dicts(dependency_map_payload.get("tasks")))

    bridge_payload = build_task_window_bridge(
        state_path=state_path,
        evaluate_payload=evaluate_payload,
        entity_ids=task_ids,
    )
    prerequisite_items = _index_by_task_id(_as_list_of_dicts(bridge_payload.get("prerequisites")))
    example_items = _index_by_task_id(_as_list_of_dicts(bridge_payload.get("task_examples")))

    current_formal_window_open = bool(global_policy.get("formal_window_open", False))
    tasks: list[dict[str, Any]] = []
    apply_candidate_count = 0
    blocked_task_count = 0
    already_formal_window_open_count = 0

    for task_id in task_ids:
        task_obj = _as_dict(subtasks.get(task_id))
        meta = _as_dict(task_obj.get("meta"))
        facts = _as_dict(task_obj.get("facts"))
        confirmed = _as_dict(_as_dict(task_obj.get("state")).get("confirmed"))

        evaluated = _as_dict(_as_dict(evaluate_subtasks.get(task_id)).get("derived"))
        requirement_ids = _as_string_list(evaluated.get("requirement_ids"))
        blocker_refs = _as_string_list(evaluated.get("blocker_refs"))

        dependency_item = _as_dict(dependency_items.get(task_id))
        prerequisite_item = _as_dict(prerequisite_items.get(task_id))
        example_item = _as_dict(example_items.get(task_id))

        current_readiness = _normalize_readiness(_as_str(confirmed.get("readiness")))
        readiness_allowed = current_readiness in ALLOWED_OPEN_READINESS
        implementation_doc_state = _as_str(confirmed.get("implementation_doc_state"))
        is_active_working_doc = implementation_doc_state == "active_working_doc"
        design_doc_ready = _slot_ready(_as_dict(facts.get("design_doc")))
        implementation_doc_ready = _slot_ready(_as_dict(facts.get("implementation_doc")))
        requirement_relation_unique = len(requirement_ids) == 1

        dependency_stage = _as_str(dependency_item.get("dependency_stage")) or "should_not_enter_open_window"
        open_window_gap_blockers = _as_string_list(dependency_item.get("open_window_gap_blockers"))
        content_blockers, state_blockers, formal_window_blockers = _classify_blockers(
            blockers=open_window_gap_blockers,
        )

        bridge_classification = _as_str(example_item.get("classification"))
        remaining_manual_fill_fields = _as_string_list(
            prerequisite_item.get("remaining_manual_fill_fields")
        )
        non_formal_blockers = [
            blocker for blocker in open_window_gap_blockers if blocker != FORMAL_WINDOW_BLOCKER
        ]
        only_formal_window_gap = (
            dependency_stage == "can_consider_readiness_but_not_formal"
            and bridge_classification == "already_window_only"
            and not content_blockers
            and not state_blockers
            and not remaining_manual_fill_fields
            and _dedupe_strings(open_window_gap_blockers) == [FORMAL_WINDOW_BLOCKER]
        )

        status = "blocked_by_formal_window_gate"
        summary = "formal window sync conditions not met"
        reason = "formal window sync conditions not met"
        apply_allowed = False

        if current_formal_window_open:
            status = "already_formal_window_open"
            summary = "formal_window_open already true"
            reason = "formal_window_open already enabled"
            already_formal_window_open_count += 1
        elif not requirement_ids:
            status = "blocked_by_requirement_relation"
            summary = "cannot sync formal window: requirement relation missing"
            reason = "requirement relation missing"
        elif not requirement_relation_unique:
            status = "blocked_by_requirement_relation"
            summary = "cannot sync formal window: requirement relation is not unique"
            reason = "requirement relation ambiguous"
        elif not design_doc_ready or not implementation_doc_ready:
            status = "blocked_by_content_layer"
            summary = "cannot sync formal window: design or implementation doc slot not ready"
            reason = "content artifacts not yet synced"
        elif not is_active_working_doc:
            status = "blocked_by_state_gate"
            summary = "cannot sync formal window before implementation_doc_state activation"
            reason = "implementation_doc_state not active_working_doc"
        elif not readiness_allowed:
            status = "blocked_by_readiness_gate"
            summary = "cannot sync formal window before readiness reaches allowed state"
            reason = "readiness not in allowed open-window state"
        elif dependency_stage == "stay_in_content_layer":
            status = "stay_in_content_layer"
            summary = "cannot sync formal window while task remains in content layer"
            reason = "dependency map stage is stay_in_content_layer"
        elif content_blockers or remaining_manual_fill_fields:
            status = "blocked_by_content_blocker"
            summary = "cannot sync formal window while content blockers remain"
            reason = "content blocker or manual fill field remains"
        elif state_blockers:
            status = "blocked_by_state_blocker"
            summary = "cannot sync formal window while state blockers remain"
            reason = "state blocker remains"
        elif dependency_stage == "should_not_enter_open_window":
            status = "blocked_by_dependency_map"
            summary = "dependency map still blocks formal window progression"
            reason = "dependency map currently blocks open-window progression"
        elif bridge_classification != "already_window_only":
            status = "blocked_by_bridge"
            summary = "task window bridge does not classify the task as window-only"
            reason = "bridge classification is not already_window_only"
        elif not only_formal_window_gap or non_formal_blockers:
            status = "blocked_by_formal_window_scope"
            summary = "formal window is not the only remaining blocker"
            reason = "non-formal blockers still remain after bridge/dependency checks"
        else:
            status = "can_open_formal_window"
            summary = "task is now blocked only by formal_window_closed"
            reason = "selected task only lacks formal window gate"
            apply_allowed = True
            apply_candidate_count += 1

        if not apply_allowed and status != "already_formal_window_open":
            blocked_task_count += 1

        tasks.append(
            {
                "task_id": task_id,
                "module_id": _as_str(meta.get("module_id")),
                "current_formal_window_open": current_formal_window_open,
                "target_formal_window_open": FORMAL_WINDOW_TARGET_VALUE if apply_allowed else None,
                "requirement_ids": requirement_ids,
                "requirement_relation_unique": requirement_relation_unique,
                "current_readiness": current_readiness,
                "readiness_allowed": readiness_allowed,
                "current_implementation_doc_state": implementation_doc_state,
                "is_active_working_doc": is_active_working_doc,
                "design_doc_ready": design_doc_ready,
                "implementation_doc_ready": implementation_doc_ready,
                "dependency_stage": dependency_stage,
                "bridge_classification": bridge_classification,
                "current_blocker_refs": blocker_refs,
                "open_window_gap_blockers": open_window_gap_blockers,
                "content_layer_blockers": content_blockers,
                "state_layer_blockers": state_blockers,
                "formal_window_blockers": formal_window_blockers,
                "remaining_manual_fill_fields": remaining_manual_fill_fields,
                "remaining_blockers_after_writeback": [] if apply_allowed else open_window_gap_blockers,
                "apply_allowed": apply_allowed,
                "planned_state_paths": ["global_policy.formal_window_open"] if apply_allowed else [],
                "write_target_field": "global_policy.formal_window_open",
                "write_target_path": str(state_path),
                "status": status,
                "summary": summary,
                "reason": reason,
                "proposed_changes": (
                    {"formal_window_open": FORMAL_WINDOW_TARGET_VALUE} if apply_allowed else {}
                ),
            }
        )

    return {
        "ok": True,
        "mode": "dry_run",
        "state_write_target_path": str(state_path),
        "write_target_field": "global_policy.formal_window_open",
        "current_formal_window_open": current_formal_window_open,
        "summary": {
            "selected_task_count": len(task_ids),
            "formal_window_apply_candidate_count": apply_candidate_count,
            "blocked_task_count": blocked_task_count,
            "already_formal_window_open_count": already_formal_window_open_count,
        },
        "tasks": tasks,
        "reasoning_notes": [
            "本 wrapper 只处理 global_policy.formal_window_open，不接 round/open-window 主链。",
            "默认模式是 dry-run；只有显式 --apply 才会通过 confirm-transition approve 写回 official state。",
            "若任务仍停留在内容层或状态层 blocker，则 formal window 不允许提前推进。",
        ],
    }


def execute_task_formal_window_sync(
    *,
    state_path: str | Path,
    evaluate_payload: dict[str, Any],
    entity_ids: list[str] | tuple[str, ...] | str | None,
    apply_changes: bool = False,
    actor: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    state_path = Path(state_path).resolve()
    preview = build_task_formal_window_sync_preview(
        state_path=state_path,
        evaluate_payload=evaluate_payload,
        entity_ids=entity_ids,
    )

    repo_root = _resolve_repo_root_for_confirm(state_path)
    tasks = _as_list_of_dicts(preview.get("tasks"))
    proposed_changes = {"formal_window_open": FORMAL_WINDOW_TARGET_VALUE}
    eligible_tasks = [item for item in tasks if bool(item.get("apply_allowed"))]

    if eligible_tasks and not bool(preview.get("current_formal_window_open")):
        policy_dry_run_result = _invoke_policy_confirm_transition(
            repo_root=repo_root,
            state_path=state_path,
            proposed_changes=proposed_changes,
            mode="dry-run",
            actor=None,
            reason="Decision: open formal window after task-level gate checks",
        )
    else:
        policy_dry_run_result = {"ok": True, "exit_code": 0, "raw_output": "no change"}

    if not apply_changes:
        return {
            **preview,
            "policy_dry_run_result": policy_dry_run_result,
        }

    if not eligible_tasks:
        raise ValueError("apply denied: no selected task is eligible for formal_window_open writeback")
    blocked_tasks = [
        str(item.get("task_id", "")).strip() for item in tasks if not bool(item.get("apply_allowed"))
    ]
    if blocked_tasks:
        raise ValueError(f"apply denied for blocked task: {', '.join(sorted(set(filter(None, blocked_tasks))))}")
    if not (actor and str(actor).strip()):
        raise ValueError("apply requires --actor")
    if not (reason and str(reason).strip()):
        raise ValueError("apply requires --reason")
    if not _confirm_ok(_as_dict(policy_dry_run_result)):
        raise ValueError("apply blocked by confirm-transition dry-run: global_policy")

    policy_apply_result = _invoke_policy_confirm_transition(
        repo_root=repo_root,
        state_path=state_path,
        proposed_changes=proposed_changes,
        mode="approve",
        actor=actor,
        reason=reason,
    )
    if not _confirm_ok(_as_dict(policy_apply_result)):
        raise ValueError("apply blocked by confirm-transition approve: global_policy")

    return {
        "ok": True,
        "mode": "apply",
        "state_write_target_path": str(state_path),
        "write_target_field": "global_policy.formal_window_open",
        "current_formal_window_open": bool(preview.get("current_formal_window_open")),
        "summary": {
            **_as_dict(preview.get("summary")),
            "applied_policy_count": 1,
            "affected_task_count": len(eligible_tasks),
        },
        "tasks": tasks,
        "policy_dry_run_result": policy_dry_run_result,
        "policy_apply_result": policy_apply_result,
        "result_summary": {
            "applied_task_ids": [
                str(item.get("task_id", "")).strip() for item in eligible_tasks if item.get("task_id")
            ],
            "write_target_paths": ["global_policy.formal_window_open"],
        },
    }


def render_task_formal_window_sync_markdown(payload: dict[str, Any]) -> str:
    summary = _as_dict(payload.get("summary"))
    lines = [
        "# task formal window sync",
        "",
        "## 概览",
        f"- 已选任务数: {summary.get('selected_task_count', 0)}",
        f"- 可推进任务数: {summary.get('formal_window_apply_candidate_count', 0)}",
        f"- 当前已打开 formal window: {summary.get('already_formal_window_open_count', 0)}",
        f"- 当前阻塞任务数: {summary.get('blocked_task_count', 0)}",
        f"- 当前 formal_window_open: {bool(payload.get('current_formal_window_open'))}",
        "",
        "## 任务明细",
    ]

    for item in _as_list_of_dicts(payload.get("tasks")):
        task_id = _as_str(item.get("task_id"))
        module_id = _as_str(item.get("module_id"))
        owner = f"{task_id} ({module_id})" if module_id else task_id
        remaining_blockers = ", ".join(_as_string_list(item.get("remaining_blockers_after_writeback"))) or "none"
        lines.extend(
            [
                f"- {owner}: {item.get('status', '')}",
                (
                    f"  - readiness={item.get('current_readiness', '')}, "
                    f"implementation_doc_state={item.get('current_implementation_doc_state', '')}, "
                    f"bridge={item.get('bridge_classification', '')}"
                ),
                f"  - remaining_blockers_after_writeback: {remaining_blockers}",
            ]
        )

    return "\n".join(lines) + "\n"


def write_task_formal_window_sync_output(
    *,
    payload: dict[str, Any],
    output_path: str | Path,
    output_format: str,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "markdown":
        content = render_task_formal_window_sync_markdown(payload)
    else:
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    path.write_text(content, encoding="utf-8")
    return path


def _invoke_policy_confirm_transition(
    *,
    repo_root: Path,
    state_path: Path,
    proposed_changes: dict[str, Any],
    mode: str,
    actor: str | None,
    reason: str | None,
) -> dict[str, Any]:
    args = argparse.Namespace(
        input=state_path.as_posix(),
        entity_type=POLICY_ENTITY_TYPE,
        entity_id=POLICY_ENTITY_ID,
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
    if raw_output:
        try:
            payload = json.loads(raw_output)
        except json.JSONDecodeError:
            payload = {"ok": False, "raw_output": raw_output}
    else:
        payload = {"ok": exit_code == 0}
    payload["exit_code"] = exit_code
    return payload


def _index_by_task_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for item in items:
        task_id = _as_str(item.get("task_id"))
        if task_id:
            indexed[task_id] = item
    return indexed
