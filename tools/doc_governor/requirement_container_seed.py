from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

from .requirement_scan import scan_requirements
from .schema import (
    make_default_confirmed_state,
    make_default_tracking_state,
)


MAX_REQUIREMENT_COUNT = 3


def build_requirement_container_seed_plan(
    *,
    state_path: str | Path,
    entity_ids: list[str] | tuple[str, ...] | str | None = None,
    allow_manual_confirmation: bool = False,
) -> dict[str, Any]:
    state_path = Path(state_path)
    state = _load_state(state_path)
    repo_root = _resolve_repo_root(state_path)
    requirements = _as_dict(state.get("requirements"))
    modules = _as_dict(state.get("modules"))
    subtasks = _as_dict(state.get("subtasks"))

    scan_result = scan_requirements(
        repo_root=repo_root,
        modules=modules,
        subtasks=subtasks,
    )
    scanned_requirements = _as_dict(scan_result.get("requirements"))
    selected_requirement_ids = _select_requirement_ids(
        entity_ids=entity_ids,
        scanned_requirements=scanned_requirements,
        existing_requirements=requirements,
    )

    containers: list[dict[str, Any]] = []
    for requirement_id in selected_requirement_ids:
        scanned_requirement = _as_dict(scanned_requirements.get(requirement_id))
        exists_in_state = requirement_id in requirements
        detected = bool(scanned_requirement)
        confidence = _build_confidence(scanned_requirement=scanned_requirement, exists_in_state=exists_in_state)
        needs_manual_confirmation = detected and not exists_in_state
        skeleton_preview = (
            _build_requirement_skeleton(scanned_requirement=scanned_requirement)
            if detected and not exists_in_state
            else None
        )
        decision, reason, apply_allowed = _decide_status(
            requirement_id=requirement_id,
            detected=detected,
            exists_in_state=exists_in_state,
            allow_manual_confirmation=allow_manual_confirmation,
        )

        target_fields = [
            "meta",
            "facts.module_ids",
            "facts.task_ids",
            "facts.asset_slots",
            "facts.compliance",
            "state.confirmed",
            "state.tracking",
        ]
        blocked_reasons: list[str] = []
        if str(decision).startswith("blocked_"):
            blocked_reasons.append(reason)

        containers.append(
            {
                "requirement_id": requirement_id,
                "source": "requirement_scan" if detected else "explicit_request",
                "target_path": f"requirements.{requirement_id}",
                "target_fields": target_fields,
                "confidence": confidence,
                "needs_manual_confirmation": needs_manual_confirmation,
                "manual_confirmation_override_used": bool(
                    allow_manual_confirmation and needs_manual_confirmation
                ),
                "requirement_exists_in_state": exists_in_state,
                "apply_allowed": apply_allowed,
                "decision": decision,
                "reason": reason,
                "blocked_reasons": blocked_reasons,
                "identified_signals": _build_identified_signals(scanned_requirement=scanned_requirement),
                "skeleton_preview": skeleton_preview,
            }
        )

    summary = {
        "selected_requirement_count": len(selected_requirement_ids),
        "scanned_requirement_count": len(scanned_requirements),
        "missing_container_count": sum(
            1 for item in containers if not bool(item.get("requirement_exists_in_state"))
        ),
        "applyable_container_count": sum(1 for item in containers if bool(item.get("apply_allowed"))),
        "blocked_container_count": sum(
            1 for item in containers if str(item.get("decision", "")).startswith("blocked_")
        ),
        "planned_write_count": sum(
            1
            for item in containers
            if bool(item.get("apply_allowed")) and not bool(item.get("requirement_exists_in_state"))
        ),
        "applied_write_count": 0,
        "state_write_enabled": False,
        "manual_confirmation_override": bool(allow_manual_confirmation),
    }

    return {
        "ok": True,
        "mode": "dry_run",
        "input_state_path": str(state_path.resolve()),
        "entity_ids": selected_requirement_ids,
        "summary": summary,
        "containers": containers,
        "rejected_containers": [
            {
                "requirement_id": item.get("requirement_id", ""),
                "decision": item.get("decision", ""),
                "reason": item.get("reason", ""),
            }
            for item in containers
            if str(item.get("decision", "")).startswith("blocked_")
        ],
        "change_summary": [
            {
                "requirement_id": item.get("requirement_id", ""),
                "decision": item.get("decision", ""),
                "target_path": item.get("target_path"),
                "reason": item.get("reason", ""),
            }
            for item in containers
        ],
        "reasoning_notes": [
            "默认模式是 dry-run，只输出 requirement container seed 计划，不修改 DOC_STATE.yaml。",
            "这层只负责引入 requirement 最小容器，不会顺手批量写 task relation。",
            "写入骨架时会保留 facts.task_ids=[]，后续 task-to-requirement 关系仍由 apply-requirement-seed 按 task 逐个追加。",
            "新增 top-level requirement 容器默认要求人工确认；真正写入时仍需显式 --apply，并建议同时带二次确认开关。",
        ],
    }


def execute_requirement_container_seed(
    *,
    state_path: str | Path,
    entity_ids: list[str] | tuple[str, ...] | str | None = None,
    apply_changes: bool = False,
    allow_manual_confirmation: bool = False,
) -> dict[str, Any]:
    plan = build_requirement_container_seed_plan(
        state_path=state_path,
        entity_ids=entity_ids,
        allow_manual_confirmation=allow_manual_confirmation,
    )
    if not apply_changes:
        return plan

    blocked_containers = [
        item
        for item in _as_list_of_dicts(plan.get("containers"))
        if str(item.get("decision", "")).startswith("blocked_")
    ]
    if blocked_containers:
        requirement_ids = ", ".join(
            str(item.get("requirement_id", "")).strip()
            for item in blocked_containers
            if item.get("requirement_id")
        )
        raise ValueError(f"存在不允许 apply 的 requirement container: {requirement_ids}")

    state_path = Path(state_path)
    changed_paths: list[str] = []
    written_containers: list[dict[str, Any]] = []
    updated_containers: list[dict[str, Any]] = []

    for item in _as_list_of_dicts(plan.get("containers")):
        container = dict(item)
        requirement_id = str(container.get("requirement_id", "")).strip()
        if not requirement_id:
            updated_containers.append(container)
            continue
        if bool(container.get("requirement_exists_in_state")):
            container["decision"] = "already_in_state"
            container["write_status"] = "unchanged"
            updated_containers.append(container)
            continue

        skeleton_preview = _as_dict(container.get("skeleton_preview"))
        changed_paths.append(str(container.get("target_path", "")).strip())
        written_containers.append(
            {
                "requirement_id": requirement_id,
                "target_path": container.get("target_path"),
                "written_fields": list(_as_list(container.get("target_fields"))),
            }
        )
        container["decision"] = "written"
        container["write_status"] = "written"
        updated_containers.append(container)

    if written_containers:
        _write_requirement_containers(
            state_path=state_path,
            containers=[
                item
                for item in updated_containers
                if item.get("write_status") == "written"
            ],
        )

    result = dict(plan)
    result["mode"] = "apply"
    result["containers"] = updated_containers
    result["summary"] = {
        **_as_dict(plan.get("summary")),
        "state_write_enabled": True,
        "applied_write_count": len(written_containers),
    }
    result["result_summary"] = {
        "written_requirement_containers": written_containers,
        "changed_state_paths": _dedupe_strings(changed_paths),
        "unchanged_requirement_ids": [
            item.get("requirement_id", "")
            for item in updated_containers
            if item.get("write_status") == "unchanged"
        ],
    }
    return result


def write_requirement_container_seed_output(
    *,
    payload: dict[str, Any],
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _build_requirement_skeleton(*, scanned_requirement: dict[str, Any]) -> dict[str, Any]:
    meta = copy.deepcopy(_as_dict(scanned_requirement.get("meta")))
    facts = copy.deepcopy(_as_dict(scanned_requirement.get("facts")))
    facts["task_ids"] = []
    if "module_ids" not in facts:
        facts["module_ids"] = []
    if "asset_slots" not in facts:
        facts["asset_slots"] = {}
    if "compliance" not in facts:
        facts["compliance"] = {}
    return {
        "meta": meta,
        "facts": facts,
        "state": {
            "confirmed": make_default_confirmed_state("requirement"),
            "tracking": make_default_tracking_state(),
        },
    }


def _decide_status(
    *,
    requirement_id: str,
    detected: bool,
    exists_in_state: bool,
    allow_manual_confirmation: bool,
) -> tuple[str, str, bool]:
    if exists_in_state:
        return (
            "already_in_state",
            f"official state 中已存在 requirement 容器：{requirement_id}",
            False,
        )
    if not detected:
        return (
            "blocked_not_detected",
            f"当前 requirement_scan 未识别出 requirement 容器：{requirement_id}",
            False,
        )
    if not allow_manual_confirmation:
        return (
            "blocked_manual_confirmation",
            "新增 official requirement 容器默认要求人工确认；如确认无误，需显式开启二次确认参数。",
            False,
        )
    return (
        "planned",
        "满足当前最小安全条件，可引入 requirement 最小容器。",
        True,
    )


def _build_confidence(
    *,
    scanned_requirement: dict[str, Any],
    exists_in_state: bool,
) -> dict[str, Any]:
    if exists_in_state:
        return {"level": "high", "score": 0.98}
    if not scanned_requirement:
        return {"level": "low", "score": 0.2}
    facts = _as_dict(scanned_requirement.get("facts"))
    asset_slots = _as_dict(facts.get("asset_slots"))
    present_assets = sum(1 for slot in asset_slots.values() if _as_dict(slot).get("exists") is True)
    module_count = len(_as_string_list(facts.get("module_ids")))
    score = 0.55
    if present_assets:
        score += 0.1
    if module_count:
        score += 0.15
    score = min(0.95, round(score, 2))
    level = "high" if score >= 0.8 else "medium"
    return {"level": level, "score": score}


def _build_identified_signals(*, scanned_requirement: dict[str, Any]) -> list[str]:
    if not scanned_requirement:
        return []
    signals: list[str] = ["requirement_scan_detected"]
    facts = _as_dict(scanned_requirement.get("facts"))
    if _as_string_list(facts.get("module_ids")):
        signals.append("module_ids_available")
    if any(_as_dict(slot).get("exists") is True for slot in _as_dict(facts.get("asset_slots")).values()):
        signals.append("root_assets_present")
    if _as_dict(scanned_requirement.get("meta")).get("scope_kind") == "root_requirement_cluster":
        signals.append("root_requirement_cluster")
    return signals


def _select_requirement_ids(
    *,
    entity_ids: list[str] | tuple[str, ...] | str | None,
    scanned_requirements: dict[str, Any],
    existing_requirements: dict[str, Any],
) -> list[str]:
    if entity_ids is None:
        missing_ids = [
            requirement_id
            for requirement_id in sorted(scanned_requirements.keys())
            if requirement_id not in existing_requirements
        ]
        return missing_ids

    if isinstance(entity_ids, str):
        raw_ids = [item.strip() for item in entity_ids.split(",")]
    else:
        raw_ids = [str(item).strip() for item in entity_ids]

    selected_ids = _dedupe_strings([item for item in raw_ids if item])
    if not selected_ids:
        raise ValueError("至少需要一个 --entity-id")
    if len(selected_ids) > MAX_REQUIREMENT_COUNT:
        raise ValueError(f"单次最多只允许处理 {MAX_REQUIREMENT_COUNT} 个 requirement")
    return selected_ids


def _resolve_repo_root(state_path: Path) -> Path:
    normalized = state_path.resolve()
    try:
        if normalized.parent.name == "governance" and normalized.parent.parent.name == "docs":
            return normalized.parent.parent.parent
    except IndexError:
        pass
    return normalized.parent


def _load_state(state_path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise ValueError(f"加载 state 文件需要 PyYAML: {exc}") from exc

    try:
        raw = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"未找到 state 文件: {state_path}") from exc
    if not isinstance(raw, dict):
        raise ValueError("state 文件内容必须是映射结构")
    return raw


def _write_requirement_containers(
    *,
    state_path: Path,
    containers: list[dict[str, Any]],
) -> None:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise ValueError(f"写入 state 文件需要 PyYAML: {exc}") from exc

    original_text = state_path.read_text(encoding="utf-8")
    blocks: list[str] = []
    for item in containers:
        requirement_id = str(item.get("requirement_id", "")).strip()
        skeleton_preview = _as_dict(item.get("skeleton_preview"))
        if not requirement_id or not skeleton_preview:
            continue
        dumped = yaml.safe_dump(
            {requirement_id: skeleton_preview},
            sort_keys=False,
            allow_unicode=True,
            width=120,
        ).rstrip("\n")
        indented = "\n".join(f"  {line}" if line else line for line in dumped.splitlines())
        blocks.append(indented)
    if not blocks:
        return

    new_text = _insert_requirement_blocks(
        original_text=original_text,
        requirement_blocks=blocks,
    )
    state_path.write_text(new_text, encoding="utf-8")


def _insert_requirement_blocks(
    *,
    original_text: str,
    requirement_blocks: list[str],
) -> str:
    lines = original_text.splitlines(keepends=True)
    block_text = "\n".join(requirement_blocks)
    if block_text and not block_text.endswith("\n"):
        block_text += "\n"

    requirement_index = _find_top_level_key(lines, "requirements")
    if requirement_index is not None:
        insert_at = _find_next_top_level_index(lines, start=requirement_index + 1)
        if insert_at is None:
            insert_at = len(lines)
        lines.insert(insert_at, block_text)
        return "".join(lines)

    insert_at = _find_top_level_key(lines, "modules")
    if insert_at is None:
        insert_at = _find_top_level_key(lines, "subtasks")
    if insert_at is None:
        insert_at = len(lines)
    lines.insert(insert_at, f"requirements:\n{block_text}")
    return "".join(lines)


def _find_top_level_key(lines: list[str], key: str) -> int | None:
    pattern = re.compile(rf"^{re.escape(key)}:\s*$")
    for index, line in enumerate(lines):
        if pattern.match(line.rstrip("\n")):
            return index
    return None


def _find_next_top_level_index(lines: list[str], *, start: int) -> int | None:
    for index in range(start, len(lines)):
        stripped = lines[index].strip()
        if not stripped:
            continue
        if not lines[index].startswith((" ", "\t")):
            return index
    return None


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


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
