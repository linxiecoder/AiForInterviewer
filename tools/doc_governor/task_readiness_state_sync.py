from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
from pathlib import Path
from typing import Any

from .confirm import confirm_transition
from .schema import MATURITY_LEVELS, READINESS_STATUSES
from .task_state_dependency_map import (
    CONTENT_BLOCKERS,
    FORMAL_WINDOW_CLOSED,
    OFFICIAL_READINESS_BLOCKER,
    STATE_GATE_BLOCKERS,
    build_task_state_dependency_map,
)

MAX_TASK_COUNT = 3


def build_task_readiness_state_sync_preview(
    *,
    state_path: str | Path,
    evaluate_payload: dict[str, Any],
    entity_ids: list[str] | tuple[str, ...] | str | None,
) -> dict[str, Any]:
    state_path = Path(state_path).resolve()
    state = _load_state(state_path)
    subtasks = _as_dict(state.get("subtasks"))
    evaluate_subtasks = _as_dict(evaluate_payload.get("subtasks"))
    task_ids = _normalize_entity_ids(entity_ids=entity_ids, state=state)

    dependency_map_payload = build_task_state_dependency_map(
        state_path=state_path,
        evaluate_payload=evaluate_payload,
        entity_ids=task_ids,
    )
    dependency_items = _index_by_task_id(_as_list_of_dicts(dependency_map_payload.get("tasks")))

    tasks: list[dict[str, Any]] = []
    apply_candidate_count = 0
    blocked_task_count = 0
    already_implementation_ready_count = 0

    for task_id in task_ids:
        task_obj = _as_dict(subtasks.get(task_id))
        meta = _as_dict(task_obj.get("meta"))
        state_obj = _as_dict(task_obj.get("state"))
        confirmed = _as_dict(state_obj.get("confirmed"))
        facts = _as_dict(task_obj.get("facts"))

        evaluated = _as_dict(_as_dict(evaluate_subtasks.get(task_id)).get("derived"))
        requirement_ids = _as_string_list(evaluated.get("requirement_ids"))
        blocker_refs = _as_string_list(evaluated.get("blocker_refs"))

        dep_item = _as_dict(dependency_items.get(task_id))
        readiness_gap_blockers = _as_string_list(dep_item.get("readiness_gap_blockers"))
        open_window_gap_blockers = _as_string_list(dep_item.get("open_window_gap_blockers"))
        dependency_stage = str(dep_item.get("dependency_stage", "should_not_enter_open_window")).strip()

        content_blockers, state_blockers, formal_window_blockers = _classify_blockers(
            blockers=open_window_gap_blockers,
        )

        current_readiness = _normalize_readiness(str(confirmed.get("readiness", "")).strip())
        current_readiness = "blocked" if current_readiness not in READINESS_STATUSES else current_readiness
        current_maturity = str(confirmed.get("maturity", "") or "").strip()
        maturity_state_valid = current_maturity in MATURITY_LEVELS
        implementation_doc_state = str(confirmed.get("implementation_doc_state", "")).strip()
        is_active_working_doc = implementation_doc_state == "active_working_doc"
        design_doc_ready = _slot_ready(_as_dict(facts.get("design_doc")))
        implementation_doc_ready = _slot_ready(_as_dict(facts.get("implementation_doc")))

        requirement_relation_unique = len(requirement_ids) == 1
        has_content_blockers = bool(content_blockers)
        state_blockers_without_official = [
            item for item in state_blockers if item != OFFICIAL_READINESS_BLOCKER
        ]

        # 默认：仅在显式条件通过时推进到 downstream_ready，
        # 在当前 readiness 已为 downstream_ready 且可进入 preflight 时再推进到 implementation_ready。
        can_touch_readiness = (
            requirement_relation_unique
            and maturity_state_valid
            and design_doc_ready
            and implementation_doc_ready
            and is_active_working_doc
            and dependency_stage != "stay_in_content_layer"
            and not has_content_blockers
            and not state_blockers_without_official
        )

        target_readiness: str = ""
        status = "blocked_by_readiness_gate"
        summary = "not ready for readiness sync"
        apply_reason = "readiness sync conditions not met"

        if current_readiness == "implementation_ready":
            target_readiness = ""
            status = "already_implementation_ready"
            summary = "readiness already at implementation_ready"
            already_implementation_ready_count += 1
        elif current_readiness in {"blocked", "not_ready", "downstream_ready"}:
            if can_touch_readiness:
                if current_readiness in {"blocked", "not_ready"}:
                    target_readiness = "downstream_ready"
                    status = "can_advance_to_downstream_ready"
                    summary = (
                        "blocked/not_ready task can move to downstream_ready after content/state gates clear"
                    )
                    apply_reason = "Decision: advance task readiness after dependency gate checks"
                elif current_readiness == "downstream_ready" and dependency_stage == "ready_for_preflight_open_window":
                    target_readiness = "implementation_ready"
                    status = "can_advance_to_implementation_ready"
                    summary = "downstream_ready task can move to implementation_ready"
                    apply_reason = "Decision: advance task readiness to implementation_ready before preflight-open-window"
                else:
                    target_readiness = ""
                    summary = "downstream_ready but open-window criteria not ready"
                    status = "blocked_before_preflight_open_window"
                    apply_reason = (
                        "Readiness is downstream_ready but dependency map is not ready_for_preflight_open_window"
                    )
            else:
                if len(requirement_ids) == 0:
                    apply_reason = "requirement relation missing"
                    summary = "cannot sync readiness: requirement relation missing"
                    status = "blocked_by_requirement_relation"
                elif len(requirement_ids) > 1:
                    apply_reason = "requirement relation ambiguous"
                    summary = "cannot sync readiness: requirement relation is not unique"
                    status = "blocked_by_requirement_relation"
                elif not design_doc_ready or not implementation_doc_ready:
                    apply_reason = "content artifacts not yet synced to active working-doc state"
                    summary = "cannot sync readiness: design or implementation doc slot not ready"
                    status = "blocked_by_content_layer"
                elif not maturity_state_valid:
                    apply_reason = "confirmed maturity must already be set before readiness writeback"
                    summary = "cannot sync readiness while confirmed maturity is missing"
                    status = "blocked_by_state_gate"
                elif not is_active_working_doc:
                    apply_reason = "implementation_doc_state not active_working_doc"
                    summary = "cannot sync readiness before implementation_doc_state activation"
                    status = "blocked_by_state_gate"
                elif dependency_stage == "stay_in_content_layer":
                    apply_reason = "dependency map stage is stay_in_content_layer"
                    summary = "cannot sync readiness while still in content layer"
                    status = "stay_in_content_layer"
                elif has_content_blockers:
                    apply_reason = "content blocker remains"
                    summary = "cannot sync readiness while content layer blockers remain"
                    status = "blocked_by_content_blocker"
                elif state_blockers_without_official:
                    apply_reason = "state blocker remains"
                    summary = "cannot sync readiness while state blockers remain"
                    status = "blocked_by_state_blocker"
                elif dependency_stage == "should_not_enter_open_window":
                    apply_reason = "dependency map currently blocks open-window/readiness progression"
                    summary = "dependency map blocks readiness progression"
                    status = "blocked_by_dependency_map"
        else:
            apply_reason = "invalid readiness status"
            summary = "invalid readiness value"
            status = "invalid_readiness"

        target_allowed = bool(target_readiness)
        if target_allowed:
            apply_candidate_count += 1
            planned_paths = [f"subtasks.{task_id}.state.confirmed.readiness"]
            remaining_gap_refs = _derive_remaining_gap_after_target(
                target_readiness=target_readiness,
                readiness_gap_blockers=readiness_gap_blockers,
                open_window_gap_blockers=open_window_gap_blockers,
            )
        else:
            planned_paths = []
            if status != "already_implementation_ready":
                blocked_task_count += 1
            remaining_gap_refs = _dedupe_strings(
                _as_string_list(readiness_gap_blockers) + _as_string_list(open_window_gap_blockers)
            )

        tasks.append(
            {
                "task_id": task_id,
                "module_id": str(meta.get("module_id", "")).strip(),
                "current_maturity": current_maturity or None,
                "maturity_state_valid": maturity_state_valid,
                "current_readiness": current_readiness,
                "target_readiness": target_readiness or None,
                "dependency_stage": dependency_stage,
                "requirement_ids": requirement_ids,
                "requirement_relation_unique": requirement_relation_unique,
                "current_implementation_doc_state": implementation_doc_state,
                "is_active_working_doc": is_active_working_doc,
                "design_doc_ready": design_doc_ready,
                "implementation_doc_ready": implementation_doc_ready,
                "current_blocker_refs": blocker_refs,
                "readiness_gap_blockers": readiness_gap_blockers,
                "open_window_gap_blockers": open_window_gap_blockers,
                "content_layer_blockers": content_blockers,
                "state_layer_blockers": state_blockers,
                "formal_window_blockers": formal_window_blockers,
                "remaining_blockers_after_writeback": remaining_gap_refs,
                "apply_allowed": target_allowed,
                "planned_state_paths": planned_paths,
                "write_target_field": f"subtasks.{task_id}.state.confirmed.readiness",
                "write_target_path": str(state_path.resolve()),
                "status": status,
                "summary": summary,
                "reason": apply_reason,
                "proposed_changes": {"readiness": target_readiness} if target_allowed else {},
                "dry_run_result": None,
                "apply_result": None,
            }
        )

    return {
        "ok": True,
        "mode": "dry_run",
        "state_write_target_path": str(state_path.resolve()),
        "summary": {
            "selected_task_count": len(task_ids),
            "readiness_apply_candidate_count": apply_candidate_count,
            "blocked_task_count": blocked_task_count,
            "already_implementation_ready_count": already_implementation_ready_count,
        },
        "tasks": tasks,
    }


def execute_task_readiness_state_sync(
    *,
    state_path: str | Path,
    evaluate_payload: dict[str, Any],
    entity_ids: list[str] | tuple[str, ...] | str | None,
    apply_changes: bool = False,
    actor: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    state_path = Path(state_path).resolve()
    preview = build_task_readiness_state_sync_preview(
        state_path=state_path,
        evaluate_payload=evaluate_payload,
        entity_ids=entity_ids,
    )

    tasks = _as_list_of_dicts(preview.get("tasks"))
    repo_root = _resolve_repo_root_for_confirm(state_path)

    for item in tasks:
        proposed_changes = _as_dict(item.get("proposed_changes"))
        if not proposed_changes:
            item["dry_run_result"] = {"ok": True, "exit_code": 0, "raw_output": "no change"}
            continue
        item["dry_run_result"] = _invoke_confirm_transition(
            repo_root=repo_root,
            state_path=state_path,
            task_id=str(item.get("task_id", "")).strip(),
            proposed_changes=proposed_changes,
            mode="dry-run",
            actor=None,
            reason=_as_str(item.get("reason")) or "Decision: readiness state sync dry-run",
        )

    if not apply_changes:
        return {**preview, "tasks": tasks}

    eligible_tasks = [item for item in tasks if bool(_as_dict(item.get("proposed_changes")))]
    if not eligible_tasks:
        raise ValueError(
            "apply denied: no selected task is eligible for readiness writeback"
        )

    blocked_tasks = [item for item in tasks if not item.get("apply_allowed")]
    if blocked_tasks:
        blocked_ids = ", ".join(
            str(item.get("task_id", "")).strip() for item in blocked_tasks if item.get("task_id")
        )
        raise ValueError(f"apply denied for blocked task: {blocked_ids}")
    if not (actor and str(actor).strip()):
        raise ValueError("apply requires --actor")
    if not (reason and str(reason).strip()):
        raise ValueError("apply requires --reason")

    failed = [
        item.get("task_id", "")
        for item in tasks
        if item.get("proposed_changes") and not _confirm_ok(_as_dict(item.get("dry_run_result")))
    ]
    if failed:
        raise ValueError("apply blocked by confirm-transition dry-run: " + ", ".join(sorted(set(map(str, failed)))))

    applied_count = 0
    changed_paths: list[str] = []
    for item in tasks:
        proposed_changes = _as_dict(item.get("proposed_changes"))
        if not proposed_changes:
            continue
        apply_task_id = str(item.get("task_id", "")).strip()
        item["apply_result"] = _invoke_confirm_transition(
            repo_root=repo_root,
            state_path=state_path,
            task_id=apply_task_id,
            proposed_changes=proposed_changes,
            mode="approve",
            actor=actor,
            reason=reason,
        )
        if _confirm_ok(_as_dict(item.get("apply_result"))):
            applied_count += 1
            changed_paths.append(f"subtasks.{apply_task_id}.state.confirmed.readiness")

    apply_failed = [
        str(item.get("task_id", "")).strip()
        for item in tasks
        if _as_dict(item.get("proposed_changes")) and not _confirm_ok(_as_dict(item.get("apply_result")))
    ]
    if apply_failed:
        raise ValueError(
            "apply blocked by confirm-transition approve: "
            + ", ".join(sorted(set(filter(None, apply_failed))))
        )

    return {
        "ok": True,
        "mode": "apply",
        "state_write_target_path": str(state_path.resolve()),
        "summary": {
            **_as_dict(preview.get("summary")),
            "applied_task_count": applied_count,
        },
        "tasks": tasks,
        "result_summary": {
            "applied_task_ids": [
                str(item.get("task_id", "")).strip()
                for item in tasks
                if item.get("proposed_changes")
            ],
            "write_target_paths": _dedupe_strings(changed_paths),
        },
    }


def render_task_readiness_state_sync_markdown(payload: dict[str, Any]) -> str:
    summary = _as_dict(payload.get("summary"))
    lines = [
        "# task readiness state sync",
        "",
        "## 概览",
        f"- 已选任务数: {summary.get('selected_task_count', 0)}",
        f"- 可推进任务数: {summary.get('readiness_apply_candidate_count', 0)}",
        f"- 已 implementation_ready: {summary.get('already_implementation_ready_count', 0)}",
        f"- 当前阻塞: {summary.get('blocked_task_count', 0)}",
        "",
        "## 任务明细",
    ]

    for item in _as_list_of_dicts(payload.get("tasks")):
        task_id = str(item.get("task_id", "")).strip()
        module_id = str(item.get("module_id", "")).strip()
        owner = f"{task_id} ({module_id})" if module_id else task_id
        target_readiness = str(item.get("target_readiness", "") or "none").strip()
        remaining_blockers = ", ".join(
            _as_string_list(item.get("remaining_blockers_after_writeback"))
        ) or "none"
        lines.extend(
            [
                f"- {owner}: {item.get('status', '')}",
                (
                    f"  - current={item.get('current_readiness', '')}, "
                    f"target={target_readiness}, stage={item.get('dependency_stage', '')}"
                ),
                f"  - remaining_blockers_after_writeback: {remaining_blockers}",
            ]
        )

    return "\n".join(lines) + "\n"


def write_task_readiness_state_sync_output(
    *,
    payload: dict[str, Any],
    output_path: str | Path,
    output_format: str,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "markdown":
        content = render_task_readiness_state_sync_markdown(payload)
    else:
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    path.write_text(content, encoding="utf-8")
    return path


def _derive_remaining_gap_after_target(
    *,
    target_readiness: str,
    readiness_gap_blockers: list[str],
    open_window_gap_blockers: list[str],
) -> list[str]:
    if target_readiness == "implementation_ready":
        return []
    if target_readiness == "downstream_ready":
        return _dedupe_strings([
            blocker
            for blocker in open_window_gap_blockers
            if blocker != OFFICIAL_READINESS_BLOCKER
        ])
    return _dedupe_strings(readiness_gap_blockers + open_window_gap_blockers)


def _classify_blockers(
    *,
    blockers: list[str],
) -> tuple[list[str], list[str], list[str]]:
    content: list[str] = []
    state: list[str] = []
    formal: list[str] = []
    for blocker in blockers:
        blocker = str(blocker).strip()
        if not blocker:
            continue
        if blocker == FORMAL_WINDOW_CLOSED:
            formal.append(blocker)
            continue
        if blocker in CONTENT_BLOCKERS:
            content.append(blocker)
            continue
        if blocker in STATE_GATE_BLOCKERS or blocker == OFFICIAL_READINESS_BLOCKER:
            state.append(blocker)
            continue
        state.append(blocker)
    return _dedupe_strings(content), _dedupe_strings(state), _dedupe_strings(formal)


def _slot_ready(slot: dict[str, Any]) -> bool:
    return bool(slot.get("exists")) and not bool(slot.get("template_like"))


def _normalize_readiness(value: str) -> str:
    if value in READINESS_STATUSES:
        return value
    return "blocked"


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
    if raw_output:
        try:
            payload = json.loads(raw_output)
        except json.JSONDecodeError:
            payload = {"ok": False, "raw_output": raw_output}
    else:
        payload = {"ok": exit_code == 0}
    payload["exit_code"] = exit_code
    return payload


def _confirm_ok(payload: dict[str, Any]) -> bool:
    return bool(payload) and int(payload.get("exit_code", 1)) == 0 and bool(payload.get("ok"))


def _resolve_repo_root_for_confirm(state_path: Path) -> Path:
    resolved = state_path.resolve()
    if resolved.parent.name == "governance" and resolved.parent.parent.name == "docs":
        return resolved.parent.parent.parent
    raise ValueError("readiness state sync requires docs/governance/DOC_STATE.yaml as official state path")


def _normalize_entity_ids(
    *,
    entity_ids: list[str] | tuple[str, ...] | str | None,
    state: dict[str, Any],
) -> list[str]:
    if isinstance(entity_ids, str):
        raw_items = [part.strip() for part in entity_ids.split(",") if part.strip()]
    else:
        raw_items = []
        for item in entity_ids or []:
            raw_items.extend(part.strip() for part in str(item).split(",") if part.strip())

    task_ids = _dedupe_strings(raw_items)
    if not task_ids:
        raise ValueError("--entity-id is required")
    if len(task_ids) > MAX_TASK_COUNT:
        raise ValueError(f"single run supports up to {MAX_TASK_COUNT} task ids")

    subtasks = _as_dict(state.get("subtasks"))
    missing = [task_id for task_id in task_ids if task_id not in subtasks]
    if missing:
        raise ValueError(f"task not found: {', '.join(missing)}")
    return task_ids


def _index_by_task_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for item in items:
        task_id = str(item.get("task_id", "")).strip()
        if task_id:
            output[task_id] = item
    return output


def _load_state(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("PyYAML is required to read DOC_STATE.yaml") from exc
    if not path.exists():
        raise ValueError(f"state file not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("state must be a mapping")
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


def _as_str(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _dedupe_strings(items: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        output.append(text)
    return output

