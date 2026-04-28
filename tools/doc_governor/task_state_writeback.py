from __future__ import annotations

import json
from pathlib import Path
from typing import Any


IMPLEMENTATION_DOC_NOT_ACTIVE = "gate:implementation_doc_not_active"
FORMAL_WINDOW_CLOSED = "policy:formal_window_closed"
IMPLEMENTATION_READY_ONLY_BLOCKERS = {
    "gate:maturity_missing",
    "gate:implementation_approval_missing",
}


def build_task_state_writeback_preview(
    *,
    state_path: str | Path,
    evaluate_payload: dict[str, Any],
    entity_ids: list[str] | tuple[str, ...] | str | None,
) -> dict[str, Any]:
    state_path = Path(state_path)
    state = _load_state(state_path)
    task_ids = _normalize_entity_ids(entity_ids=entity_ids, state=state)

    subtasks = _as_dict(state.get("subtasks"))
    evaluate_subtasks = _as_dict(evaluate_payload.get("subtasks"))

    tasks: list[dict[str, Any]] = []
    batch_actions: list[dict[str, str]] = []

    for task_id in task_ids:
        task_state = _as_dict(subtasks.get(task_id))
        meta = _as_dict(task_state.get("meta"))
        confirmed = _as_dict(_as_dict(task_state.get("state")).get("confirmed"))
        derived = _as_dict(_as_dict(evaluate_subtasks.get(task_id)).get("derived"))

        blockers = _dedupe_strings(_as_string_list(derived.get("blocker_refs")))
        implementation_doc_state = str(confirmed.get("implementation_doc_state", "")).strip()
        needs_activation = implementation_doc_state != "active_working_doc"
        predicted_blockers = [
            blocker
            for blocker in blockers
            if not (needs_activation and blocker == IMPLEMENTATION_DOC_NOT_ACTIVE)
            and blocker not in IMPLEMENTATION_READY_ONLY_BLOCKERS
        ]
        remaining_categories = _dedupe_strings(
            [_categorize_blocker(blocker) for blocker in predicted_blockers]
        )
        non_state_blockers = [
            blocker
            for blocker in blockers
            if blocker not in {IMPLEMENTATION_DOC_NOT_ACTIVE, FORMAL_WINDOW_CLOSED}
            and blocker not in IMPLEMENTATION_READY_ONLY_BLOCKERS
        ]

        eligible_for_writeback = (
            needs_activation
            and IMPLEMENTATION_DOC_NOT_ACTIVE in blockers
            and not non_state_blockers
        )
        window_only_after_writeback = predicted_blockers == [FORMAL_WINDOW_CLOSED]
        implementation_ready_after_writeback = not predicted_blockers

        if eligible_for_writeback:
            status = "eligible_activation"
        elif not needs_activation:
            status = "already_active"
        elif blockers and IMPLEMENTATION_DOC_NOT_ACTIVE not in blockers:
            status = "evaluate_payload_out_of_sync"
        else:
            status = "blocked_other_blockers"

        proposed_changes = (
            {"implementation_doc_state": "active_working_doc"}
            if eligible_for_writeback
            else {}
        )
        transition = _build_transition_suggestion(
            task_id=task_id,
            proposed_changes=proposed_changes,
        )

        tasks.append(
            {
                "task_id": task_id,
                "module_id": str(meta.get("module_id", "")).strip(),
                "current_implementation_doc_state": implementation_doc_state,
                "current_blocker_refs": blockers,
                "predicted_blocker_refs_after_writeback": predicted_blockers,
                "remaining_gap_categories": remaining_categories,
                "eligible_for_writeback": eligible_for_writeback,
                "window_only_after_writeback": window_only_after_writeback,
                "implementation_ready_after_writeback": implementation_ready_after_writeback,
                "status": status,
                "proposed_changes": proposed_changes,
                "suggested_state_transition": transition,
                "suggested_confirm_command": _build_confirm_command(transition),
                "summary": _build_summary_sentence(
                    status=status,
                    blockers=blockers,
                    predicted_blockers=predicted_blockers,
                ),
            }
        )

    if any(bool(item.get("eligible_for_writeback")) for item in tasks):
        batch_actions.append(
            {
                "title": "先做 implementation_doc_state dry-run",
                "reason": "这一步只推进 task 的 implementation_doc_state，不直接放行 readiness，也不直接写 formal window。",
            }
        )
    if any(bool(item.get("window_only_after_writeback")) for item in tasks):
        batch_actions.append(
            {
                "title": "激活后再接 preflight-open-window",
                "reason": "若写回后只剩 formal_window_closed，下一步应进入 open-window 预检，而不是继续修 task 文本。",
            }
        )
    if any("manual_fill" in _as_string_list(item.get("remaining_gap_categories")) for item in tasks):
        batch_actions.append(
            {
                "title": "仍需先补人工字段",
                "reason": "存在 allowed_modify_paths / required_tests / acceptance_criteria 之类缺口时，不应提前写 implementation_doc_state。",
            }
        )

    summary = {
        "selected_task_count": len(task_ids),
        "activation_candidate_count": sum(1 for item in tasks if bool(item.get("eligible_for_writeback"))),
        "already_active_count": sum(1 for item in tasks if item.get("status") == "already_active"),
        "blocked_task_count": sum(1 for item in tasks if item.get("status") == "blocked_other_blockers"),
        "window_only_after_writeback_count": sum(1 for item in tasks if bool(item.get("window_only_after_writeback"))),
        "implementation_ready_after_writeback_count": sum(
            1 for item in tasks if bool(item.get("implementation_ready_after_writeback"))
        ),
    }

    reasoning_notes = [
        "本能力只做 state 写回预览，不会写 DOC_STATE.yaml，也不会替代 confirm-transition。",
        "implementation_doc_state 只在当前 blocker 已收敛到状态位层时才建议推进，避免把内容未完成的 task 提前激活。",
        "formal_window_closed 仍然属于独立 gate；即使 implementation_doc_state 可推进，也不等于已经可以直接开始代码实现。",
    ]

    return {
        "summary": summary,
        "tasks": tasks,
        "batch_actions": batch_actions,
        "reasoning_notes": reasoning_notes,
    }


def render_task_state_writeback_markdown(payload: dict[str, Any]) -> str:
    summary = _as_dict(payload.get("summary"))
    lines = [
        "# 任务 state 写回预览",
        "",
        "## 摘要",
        f"- 目标 task 数量: {summary.get('selected_task_count', 0)}",
        f"- 可推进 implementation_doc_state 的 task 数量: {summary.get('activation_candidate_count', 0)}",
        f"- 已经 active_working_doc 的 task 数量: {summary.get('already_active_count', 0)}",
        f"- 仍被其他 blocker 阻断的 task 数量: {summary.get('blocked_task_count', 0)}",
        f"- 写回后只剩 formal window 的 task 数量: {summary.get('window_only_after_writeback_count', 0)}",
        f"- 写回后可直达 implementation_ready 的 task 数量: {summary.get('implementation_ready_after_writeback_count', 0)}",
        "",
        "## task 判断",
    ]
    for item in _as_list_of_dicts(payload.get("tasks")):
        lines.append(
            f"- {item.get('task_id', '')}: {item.get('status', '')} | {item.get('summary', '')}"
        )
        predicted = ", ".join(_as_string_list(item.get("predicted_blocker_refs_after_writeback"))) or "无"
        lines.append(f"  - 写回后预计 blocker: {predicted}")
        command = str(item.get("suggested_confirm_command", "")).strip()
        if command:
            lines.append(f"  - confirm-transition 建议: `{command}`")

    actions = _as_list_of_dicts(payload.get("batch_actions"))
    if actions:
        lines.extend(["", "## 批次建议"])
        for item in actions:
            lines.append(f"- {item.get('title', '')}: {item.get('reason', '')}")

    notes = _as_string_list(payload.get("reasoning_notes"))
    if notes:
        lines.extend(["", "## 说明"])
        lines.extend(f"- {note}" for note in notes)
    return "\n".join(lines) + "\n"


def write_task_state_writeback_output(
    *,
    payload: dict[str, Any],
    output_path: str | Path,
    output_format: str,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "markdown":
        path.write_text(render_task_state_writeback_markdown(payload), encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _build_transition_suggestion(
    *,
    task_id: str,
    proposed_changes: dict[str, Any],
) -> dict[str, Any]:
    if not proposed_changes:
        return {}
    return {
        "entity_type": "subtask",
        "entity_id": task_id,
        "mode": "dry-run",
        "proposed_changes": proposed_changes,
        "reason_template": "Decision: activate implementation_doc_state after task content gates cleared",
        "requires_evidence_refs": False,
    }


def _build_confirm_command(transition: dict[str, Any]) -> str:
    if not transition:
        return ""
    proposed_changes = json.dumps(
        _as_dict(transition.get("proposed_changes")),
        ensure_ascii=False,
    )
    reason = str(transition.get("reason_template", "")).strip()
    task_id = str(transition.get("entity_id", "")).strip()
    return (
        "python -m tools.doc_governor.cli confirm-transition "
        f"--entity-type subtask --entity-id {task_id} "
        f"--proposed-changes '{proposed_changes}' "
        "--mode dry-run "
        f"--reason '{reason}'"
    )


def _build_summary_sentence(
    *,
    status: str,
    blockers: list[str],
    predicted_blockers: list[str],
) -> str:
    if status == "eligible_activation":
        if predicted_blockers == [FORMAL_WINDOW_CLOSED]:
            return "内容层 blocker 已基本清掉，写回 implementation_doc_state 后将只剩 formal window。"
        if not predicted_blockers:
            return "写回 implementation_doc_state 后预计可直接达到 implementation_ready。"
        return "当前可推进 implementation_doc_state，但写回后仍有其他 blocker。"
    if status == "already_active":
        if predicted_blockers == [FORMAL_WINDOW_CLOSED]:
            return "implementation_doc_state 已激活，当前主要剩 formal window blocker。"
        if not predicted_blockers:
            return "implementation_doc_state 已激活，当前没有剩余 blocker。"
        return "implementation_doc_state 已激活，但仍有其他 blocker。"
    if status == "evaluate_payload_out_of_sync":
        return "当前 state 与 evaluate payload 看起来不同步，建议先重新 evaluate-state。"
    if IMPLEMENTATION_DOC_NOT_ACTIVE in blockers:
        return "除了 implementation_doc_state 之外仍有其他 blocker，暂不建议写回状态位。"
    return "当前没有可推进的 implementation_doc_state 写回动作。"


def _normalize_entity_ids(
    *,
    entity_ids: list[str] | tuple[str, ...] | str | None,
    state: dict[str, Any],
) -> list[str]:
    if entity_ids is None:
        return sorted(str(task_id) for task_id in _as_dict(state.get("subtasks")).keys())
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
    if blocker in {IMPLEMENTATION_DOC_NOT_ACTIVE, FORMAL_WINDOW_CLOSED} or blocker in IMPLEMENTATION_READY_ONLY_BLOCKERS:
        return "state_window"
    return "other"


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
