from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schema import OFFICIAL_STATE_PATH
from .task_state_writeback import (
    FORMAL_WINDOW_CLOSED,
    IMPLEMENTATION_DOC_NOT_ACTIVE,
    build_task_state_writeback_preview,
)

DEPENDENCY_MAP_CONTRACT_VERSION = 1

ALLOWED_OPEN_READINESS = {"downstream_ready", "implementation_ready"}
FORMAL_WINDOW_BLOCKER = FORMAL_WINDOW_CLOSED
IMPLEMENTATION_READY_ONLY_BLOCKERS = {
    "gate:maturity_missing",
    "gate:implementation_approval_missing",
}
STATE_GATE_BLOCKERS = {IMPLEMENTATION_DOC_NOT_ACTIVE}
CONTENT_BLOCKERS = {
    "doc:implementation_doc",
    "doc:design_doc",
    "gate:implementation_scope_unclear",
    "gate:required_tests_missing",
    "gate:acceptance_criteria_missing",
    "gate:path_scope_conflict",
}
OFFICIAL_READINESS_BLOCKER = "state:official_readiness_not_ready"


def build_task_state_dependency_map(
    *,
    state_path: str | Path = OFFICIAL_STATE_PATH,
    evaluate_payload: dict[str, Any],
    entity_ids: list[str] | tuple[str, ...] | str | None,
) -> dict[str, Any]:
    writeback_preview = build_task_state_writeback_preview(
        state_path=state_path,
        evaluate_payload=evaluate_payload,
        entity_ids=entity_ids,
    )
    state = _load_state(Path(state_path))

    tasks_payload = _as_list_of_dicts(writeback_preview.get("tasks"))
    map_items: list[dict[str, Any]] = []
    for item in tasks_payload:
        task_id = str(item.get("task_id", "")).strip()
        if not task_id:
            continue

        module_id = str(item.get("module_id", "")).strip()
        current_readiness = _as_str(
            _as_dict(_as_dict(_as_dict(state.get("subtasks", {})).get(task_id)).get("state"))
            .get("confirmed", {})
            .get("readiness"),
        )
        confirmed = _as_dict(
            _as_dict(_as_dict(_as_dict(state.get("subtasks", {})).get(task_id)).get("state"))
            .get("confirmed", {})
        )
        formal_window_open = _as_str(confirmed.get("formal_window_status")) == "open"
        derived = _as_dict(
            _as_dict(_as_dict(evaluate_payload.get("subtasks")).get(task_id)).get("derived")
        )
        is_active_working_doc = bool(
            str(item.get("current_implementation_doc_state", "")).strip()
            == "active_working_doc"
        )

        current_blockers = _as_string_list(item.get("current_blocker_refs"))
        predicted_blockers = _as_string_list(item.get("predicted_blocker_refs_after_writeback"))

        readiness_gap = _derive_readiness_gap(
            current_readiness=current_readiness,
            predicted_blockers=predicted_blockers,
        )
        open_window_gap = _derive_open_window_gap(
            readiness_gap=readiness_gap,
            predicted_blockers=predicted_blockers,
            formal_window_open=formal_window_open,
        )

        readiness_content, readiness_state, readiness_formal = _split_blockers_by_layer(
            blockers=readiness_gap,
            include_formal_layer=True,
        )
        open_window_content, open_window_state, open_window_formal = _split_blockers_by_layer(
            blockers=open_window_gap,
            include_formal_layer=True,
        )

        dependency_stage = _classify_stage(
            readiness_gap=readiness_gap,
            open_window_gap=open_window_gap,
            readiness_content=readiness_content,
        )
        recommended = _build_recommended_step(
            task_id=task_id,
            module_id=module_id,
            dependency_stage=dependency_stage,
        )
        can_open_formal_window = dependency_stage in {
            "can_consider_readiness_but_not_formal",
            "ready_for_preflight_open_window",
        }
        can_generate_implementation_packet = bool(
            formal_window_open and bool(derived.get("can_generate_implementation_packet"))
        )
        can_mark_implementation_ready = bool(
            formal_window_open and bool(derived.get("can_mark_implementation_ready"))
        )

        map_items.append(
            {
                "task_id": task_id,
                "module_id": module_id,
                "gate_result": "pass" if can_open_formal_window else "blocked",
                "can_open_formal_window": can_open_formal_window,
                "can_generate_implementation_packet": can_generate_implementation_packet,
                "can_mark_implementation_ready": can_mark_implementation_ready,
                "scoped_formal_window_open": formal_window_open,
                "is_active_working_doc": is_active_working_doc,
                "current_readiness": current_readiness or "blocked",
                "current_blocker_refs": current_blockers,
                "predicted_blocker_refs_after_writeback": predicted_blockers,
                "readiness_gap_blockers": readiness_gap,
                "open_window_gap_blockers": open_window_gap,
                "content_layer_blockers": open_window_content,
                "state_layer_blockers": open_window_state,
                "formal_window_blockers": open_window_formal,
                "dependency_stage": dependency_stage,
                "recommended_next_step": recommended,
                "can_continue_readiness": not readiness_gap,
                "can_enter_preflight_open_window": dependency_stage == "ready_for_preflight_open_window",
                "must_stay_content_layer": dependency_stage == "stay_in_content_layer",
                "cannot_enter_open_window_yet": dependency_stage == "should_not_enter_open_window",
            }
        )

    summary = {
        "selected_task_count": len(map_items),
        "active_working_doc_count": sum(
            1 for item in map_items if bool(item.get("is_active_working_doc"))
        ),
        "stay_in_content_layer_count": sum(
            1 for item in map_items if item.get("dependency_stage") == "stay_in_content_layer"
        ),
        "can_consider_readiness_only_count": sum(
            1
            for item in map_items
            if item.get("dependency_stage") == "can_consider_readiness_but_not_formal"
        ),
        "ready_for_preflight_open_window_count": sum(
            1 for item in map_items if item.get("dependency_stage") == "ready_for_preflight_open_window"
        ),
        "should_not_enter_open_window_count": sum(
            1 for item in map_items if item.get("dependency_stage") == "should_not_enter_open_window"
        ),
    }

    return {
        "contract_version": DEPENDENCY_MAP_CONTRACT_VERSION,
        "summary": summary,
        "tasks": map_items,
        "reasoning_notes": [
            "本能力仅做依赖映射与只读可视化，不写入 readiness / formal_window_status。",
            "依赖评估以 implementation_doc_state 激活后的 predicted blocker 为主线，但不进行任何状态写回。",
            "formal_window_closed 属于独立正式窗口层；即使 readiness 达标，亦不表示可直接打开正式 open-window。",
        ],
    }


def render_task_state_dependency_map_markdown(payload: dict[str, Any]) -> str:
    summary = _as_dict(payload.get("summary"))
    tasks = _as_list_of_dicts(payload.get("tasks"))
    lines = [
        "# 任务 state 依赖映射预览",
        "",
        "## 摘要",
        f"- 目标 task 数：{summary.get('selected_task_count', 0)}",
        f"- 已处于 active_working_doc：{summary.get('active_working_doc_count', 0)}",
        f"- 仍需内容层修补：{summary.get('stay_in_content_layer_count', 0)}",
        f"- 可继续 readiness 但未放行 formal window：{summary.get('can_consider_readiness_only_count', 0)}",
        f"- 可转向 preflight-open-window：{summary.get('ready_for_preflight_open_window_count', 0)}",
        f"- 仍不应进入 open-window：{summary.get('should_not_enter_open_window_count', 0)}",
        "",
        "## 任务映射",
    ]

    if not tasks:
        lines.append("- 无结果")
        return "\n".join(lines) + "\n"

    for item in tasks:
        task_id = str(item.get("task_id", "")).strip()
        module_id = str(item.get("module_id", "")).strip()
        owner = task_id or "UNKNOWN"
        if module_id:
            owner = f"{owner} ({module_id})"
        lines.extend(
            [
                f"- {owner}：{item.get('dependency_stage', '').replace('_', ' ')}",
                f"  - active_working_doc: {item.get('is_active_working_doc', False)}",
                f"  - 当前 readiness: {item.get('current_readiness', 'blocked')}",
                (
                    f"  - gate_result: {item.get('gate_result', 'blocked')}; "
                    f"can_open_formal_window={_format_bool(item.get('can_open_formal_window'))}; "
                    f"can_generate_implementation_packet={_format_bool(item.get('can_generate_implementation_packet'))}; "
                    f"can_mark_implementation_ready={_format_bool(item.get('can_mark_implementation_ready'))}"
                ),
                (
                    "  - 离 readiness 差距："
                    f"{', '.join(_as_string_list(item.get('readiness_gap_blockers'))) or '无'}"
                ),
                (
                    "  - 离 open-window/preflight 差距："
                    f"{', '.join(_as_string_list(item.get('open_window_gap_blockers'))) or '无'}"
                ),
                (
                    "  - 阻塞分层："
                    f"内容层={', '.join(_as_string_list(item.get('content_layer_blockers')) ) or '无'}；"
                    f"状态层={', '.join(_as_string_list(item.get('state_layer_blockers')) ) or '无'}；"
                    f"formal层={', '.join(_as_string_list(item.get('formal_window_blockers')) ) or '无'}"
                ),
                f"  - 下一步建议：{item.get('recommended_next_step', {}).get('reason', '')}",
            ]
        )

    notes = _as_string_list(payload.get("reasoning_notes"))
    if notes:
        lines.extend(["", "## 说明", *[f"- {note}" for note in notes]])
    return "\n".join(lines) + "\n"


def write_task_state_dependency_map_output(
    *,
    payload: dict[str, Any],
    output_path: str | Path,
    output_format: str,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "markdown":
        path.write_text(
            render_task_state_dependency_map_markdown(payload),
            encoding="utf-8",
        )
    else:
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return path


def _classify_stage(
    *,
    readiness_gap: list[str],
    open_window_gap: list[str],
    readiness_content: list[str],
) -> str:
    if readiness_content:
        return "stay_in_content_layer"
    if open_window_gap == [FORMAL_WINDOW_BLOCKER]:
        return "can_consider_readiness_but_not_formal"
    if not readiness_gap:
        if not open_window_gap:
            return "ready_for_preflight_open_window"
    return "should_not_enter_open_window"


def _derive_readiness_gap(
    *,
    current_readiness: str,
    predicted_blockers: list[str],
) -> list[str]:
    blockers = [blocker for blocker in predicted_blockers if blocker]
    blockers = _dedupe_strings(blockers)
    readiness_gap = [b for b in blockers if b != FORMAL_WINDOW_BLOCKER]
    if current_readiness not in ALLOWED_OPEN_READINESS:
        readiness_gap.append(OFFICIAL_READINESS_BLOCKER)
    return _dedupe_strings(readiness_gap)


def _derive_open_window_gap(
    *,
    readiness_gap: list[str],
    predicted_blockers: list[str],
    formal_window_open: bool,
) -> list[str]:
    blockers: list[str] = [
        blocker for blocker in readiness_gap if blocker and blocker != OFFICIAL_READINESS_BLOCKER
    ]
    for blocker in predicted_blockers:
        if blocker in IMPLEMENTATION_READY_ONLY_BLOCKERS:
            continue
        if blocker and blocker not in blockers:
            blockers.append(blocker)
    if not formal_window_open and FORMAL_WINDOW_BLOCKER not in blockers:
        blockers.append(FORMAL_WINDOW_BLOCKER)
    return _dedupe_strings(blockers)


def _split_blockers_by_layer(
    *,
    blockers: list[str],
    include_formal_layer: bool,
) -> tuple[list[str], list[str], list[str]]:
    content: list[str] = []
    state: list[str] = []
    formal: list[str] = []
    for blocker in blockers:
        if not blocker:
            continue
        if include_formal_layer and blocker == FORMAL_WINDOW_BLOCKER:
            formal.append(blocker)
        elif blocker in CONTENT_BLOCKERS or blocker in STATE_GATE_BLOCKERS:
            state.append(blocker) if blocker in STATE_GATE_BLOCKERS else content.append(blocker)
        elif blocker == OFFICIAL_READINESS_BLOCKER:
            state.append(blocker)
        else:
            state.append(blocker)
    return _dedupe_strings(content), _dedupe_strings(state), _dedupe_strings(formal)


def _build_recommended_step(
    *,
    task_id: str,
    module_id: str,
    dependency_stage: str,
) -> dict[str, Any]:
    owner = task_id or "UNKNOWN"
    if module_id:
        owner = f"{owner} ({module_id})"
    if dependency_stage == "stay_in_content_layer":
        return {
            "task_id": task_id,
            "module_id": module_id,
            "scope": "content",
            "reason": f"{owner} 当前仍有内容层 blocker，先补齐文档/字段再进入 state 继续链路。",
            "action": "continue_content_layer",
        }
    if dependency_stage == "can_consider_readiness_but_not_formal":
        return {
            "task_id": task_id,
            "module_id": module_id,
            "scope": "readiness",
            "reason": f"{owner} readiness 已可接近，但受 formal_window_closed 约束，不建议直接入窗口。",
            "action": "consider_readiness_then_wait_formal_window",
        }
    if dependency_stage == "ready_for_preflight_open_window":
        return {
            "task_id": task_id,
            "module_id": module_id,
            "scope": "preflight",
            "reason": f"{owner} 已满足 readiness 关键条件，可转向 preflight-open-window。",
            "action": "advance_to_preflight_open_window",
        }
    return {
        "task_id": task_id,
        "module_id": module_id,
        "scope": "blocked",
        "reason": f"{owner} 仍存在状态层/其他阻塞，不应进入 open-window。",
        "action": "stay_blocked_until_unblocked",
    }


def _load_state(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise ValueError(f"加载 state 文件需要 PyYAML: {exc}") from exc
    if not path.exists():
        raise ValueError(f"state file not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("state must be mapping")
    return raw


def _dedupe_strings(items: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = str(item).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


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
    if isinstance(value, str):
        return value
    return str(value)


def _format_bool(value: object) -> str:
    return "true" if bool(value) else "false"
