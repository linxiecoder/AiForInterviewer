from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import schema
from .template_detection import detect_template_signals

MAX_TASK_COUNT = 10
DESIGN_FILENAME = "SUBTASK_DESIGN.md"
IMPLEMENTATION_FILENAME = "SUBTASK_IMPLEMENTATION.md"

DOC_SLOT_SPECS = {
    "design_doc": {
        "filename": DESIGN_FILENAME,
        "required_headings": (
            "# 子任务设计文档",
            "## 3. 子任务目标",
            "## 5. 技术方案",
        ),
        "doc_kind": "subtask_design",
    },
    "implementation_doc": {
        "filename": IMPLEMENTATION_FILENAME,
        "required_headings": (
            "# 子任务实施文档",
            "## 3. 本轮实施目标",
            "## 5. 允许修改范围",
            "## 7. 测试与验证",
            "## 8. 完成判定",
        ),
        "doc_kind": "subtask_implementation",
    },
}


def build_task_doc_state_sync_plan(
    *,
    state_path: str | Path,
    entity_ids: list[str] | tuple[str, ...] | str,
) -> dict[str, Any]:
    state_path = Path(state_path)
    state = _load_state(state_path)
    repo_root = _resolve_repo_root(state_path)
    requirements = _as_dict(state.get("requirements"))
    subtasks = _as_dict(state.get("subtasks"))
    task_ids = _parse_task_ids(entity_ids=entity_ids, subtasks=subtasks)
    known_requirement_ids = set(requirements.keys())
    container_task_relations = _collect_container_relations(
        requirements=requirements,
        relation_field="task_ids",
        known_requirement_ids=known_requirement_ids,
    )

    tasks: list[dict[str, Any]] = []
    for task_id in task_ids:
        task_obj = _as_dict(subtasks.get(task_id))
        meta = _as_dict(task_obj.get("meta"))
        facts = _as_dict(task_obj.get("facts"))
        module_id = str(meta.get("module_id", "")).strip()
        task_dir = _resolve_task_dir(
            repo_root=repo_root,
            task_path=str(meta.get("path", "")).strip(),
        )

        requirement_resolution = _resolve_requirement_relation(
            task_id=task_id,
            meta_obj=meta,
            facts_obj=facts,
            known_requirement_ids=known_requirement_ids,
            container_relations=container_task_relations,
        )
        requirement_id = requirement_resolution["requirement_id"]
        relation_source = requirement_resolution["relation_source"]

        task_block_decision: str | None = None
        task_block_reason: str | None = None
        if requirement_id is None:
            task_block_decision = str(requirement_resolution["decision"])
            task_block_reason = str(requirement_resolution["reason"])
        elif task_dir is None:
            task_block_decision = "blocked_task_path_missing"
            task_block_reason = "task 缺少可定位的目录 path，当前不能同步文档槽位状态。"

        slot_plans = [
            _build_slot_plan(
                slot_name="design_doc",
                task_id=task_id,
                task_dir=task_dir,
                facts_obj=facts,
                task_block_decision=task_block_decision,
                task_block_reason=task_block_reason,
                repo_root=repo_root,
            ),
            _build_slot_plan(
                slot_name="implementation_doc",
                task_id=task_id,
                task_dir=task_dir,
                facts_obj=facts,
                task_block_decision=task_block_decision,
                task_block_reason=task_block_reason,
                repo_root=repo_root,
            ),
        ]

        planned_state_paths = _dedupe_strings(
            [
                state_path_item
                for slot in slot_plans
                for state_path_item in _as_string_list(slot.get("target_paths"))
                if bool(slot.get("apply_allowed"))
            ]
        )
        blocked_conditions = _dedupe_strings(
            [
                str(slot.get("reason", "")).strip()
                for slot in slot_plans
                if str(slot.get("decision", "")).startswith("blocked_")
                and str(slot.get("reason", "")).strip()
            ]
        )
        planned_slot_count = sum(1 for slot in slot_plans if bool(slot.get("apply_allowed")))
        already_synced = (
            task_block_decision is None
            and planned_slot_count == 0
            and all(str(slot.get("decision", "")) == "already_synced" for slot in slot_plans)
        )
        apply_allowed = task_block_decision is None and planned_slot_count > 0
        decision = (
            task_block_decision
            if task_block_decision is not None
            else ("already_synced" if already_synced else "planned")
        )
        reason = (
            task_block_reason
            if task_block_reason is not None
            else (
                "当前 task 的文档槽位与最小状态已同步，不需要重复写回。"
                if already_synced
                else "满足最小安全条件，可将 task 双文档槽位同步到 DOC_STATE.yaml。"
            )
        )

        tasks.append(
            {
                "task_id": task_id,
                "module_id": module_id,
                "requirement_id": requirement_id,
                "relation_source": relation_source,
                "apply_allowed": apply_allowed,
                "decision": decision,
                "reason": reason,
                "planned_state_paths": planned_state_paths,
                "blocked_conditions": blocked_conditions,
                "slots": slot_plans,
            }
        )

    blocked_tasks = [
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
        "planned_task_count": sum(1 for item in tasks if bool(item.get("apply_allowed"))),
        "blocked_task_count": len(blocked_tasks),
        "already_synced_task_count": sum(
            1 for item in tasks if str(item.get("decision", "")) == "already_synced"
        ),
        "planned_slot_count": sum(
            1
            for task in tasks
            for slot in _as_list_of_dicts(task.get("slots"))
            if bool(slot.get("apply_allowed"))
        ),
        "minimal_ready_slot_count": sum(
            1
            for task in tasks
            for slot in _as_list_of_dicts(task.get("slots"))
            if bool(slot.get("minimal_sync_ready"))
        ),
        "planned_state_path_count": len(
            _dedupe_strings(
                [
                    path
                    for task in tasks
                    for path in _as_string_list(task.get("planned_state_paths"))
                ]
            )
        ),
        "written_task_count": 0,
        "written_slot_count": 0,
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
        "change_summary": _build_change_summary(tasks),
        "reasoning_notes": [
            "默认模式是 dry-run，只输出 task doc artifact/state sync 计划，不修改 DOC_STATE.yaml。",
            "只有显式选中的 task 才会参与同步，且默认最多 10 个。",
            "只同步 design_doc / implementation_doc 的最小 facts 槽位与路径，不推进 implementation_doc_state、readiness、formal_window_open。",
            "若当前 state 已存在正式文档判断，则本轮不会自动降级覆盖，只会在安全场景下补齐缺失的最小 tracking/facts。",
        ],
    }


def execute_task_doc_state_sync(
    *,
    state_path: str | Path,
    entity_ids: list[str] | tuple[str, ...] | str,
    apply_changes: bool = False,
) -> dict[str, Any]:
    plan = build_task_doc_state_sync_plan(
        state_path=state_path,
        entity_ids=entity_ids,
    )
    if not apply_changes:
        return plan

    blocked_tasks = [
        item
        for item in _as_list_of_dicts(plan.get("tasks"))
        if str(item.get("decision", "")).startswith("blocked_")
    ]
    if blocked_tasks:
        labels = ", ".join(
            str(item.get("task_id", "")).strip()
            for item in blocked_tasks
            if item.get("task_id")
        )
        raise ValueError(f"存在不允许 apply 的 task: {labels}")

    state_path = Path(state_path)
    state = _load_state(state_path)
    updated_text = _read_text(state_path)
    updated_tasks: list[dict[str, Any]] = []
    written_task_count = 0
    written_slot_count = 0
    changed_state_paths: list[str] = []

    for task_plan in _as_list_of_dicts(plan.get("tasks")):
        task_id = str(task_plan.get("task_id", "")).strip()
        updated_task = dict(task_plan)
        updated_slots: list[dict[str, Any]] = []
        planned_slots = [
            slot
            for slot in _as_list_of_dicts(task_plan.get("slots"))
            if bool(slot.get("apply_allowed"))
        ]
        if planned_slots:
            task_obj = _as_dict(_as_dict(state.get("subtasks")).get(task_id))
            updated_task_obj = _apply_slot_syncs(
                task_obj=task_obj,
                slot_plans=planned_slots,
            )
            updated_text = _replace_entity_block(
                original_text=updated_text,
                section_name="subtasks",
                entity_id=task_id,
                updated_entity_obj=updated_task_obj,
            )
            _as_dict(state.setdefault("subtasks", {}))[task_id] = updated_task_obj
            written_task_count += 1

        for slot_plan in _as_list_of_dicts(task_plan.get("slots")):
            updated_slot = dict(slot_plan)
            if bool(updated_slot.get("apply_allowed")):
                updated_slot["write_status"] = "written"
                updated_slot["decision"] = "written"
                written_slot_count += 1
                changed_state_paths.extend(_as_string_list(updated_slot.get("target_paths")))
            else:
                updated_slot["write_status"] = "unchanged"
            updated_slots.append(updated_slot)

        updated_task["slots"] = updated_slots
        if planned_slots:
            updated_task["decision"] = "written"
        elif str(updated_task.get("decision", "")) == "already_synced":
            updated_task["decision"] = "already_synced"
        updated_tasks.append(updated_task)

    if written_slot_count:
        _write_text(state_path=state_path, text=updated_text)

    result = dict(plan)
    result["mode"] = "apply"
    result["tasks"] = updated_tasks
    result["summary"] = {
        **_as_dict(plan.get("summary")),
        "written_task_count": written_task_count,
        "written_slot_count": written_slot_count,
        "state_write_enabled": True,
    }
    result["result_summary"] = {
        "written_tasks": [
            item.get("task_id", "")
            for item in updated_tasks
            if str(item.get("decision", "")) == "written"
        ],
        "written_slots": [
            {
                "task_id": task.get("task_id", ""),
                "slot_name": slot.get("slot_name", ""),
                "target_paths": _as_string_list(slot.get("target_paths")),
            }
            for task in updated_tasks
            for slot in _as_list_of_dicts(task.get("slots"))
            if slot.get("write_status") == "written"
        ],
        "changed_state_paths": _dedupe_strings(changed_state_paths),
        "unchanged_tasks": [
            item.get("task_id", "")
            for item in updated_tasks
            if str(item.get("decision", "")) == "already_synced"
        ],
    }
    return result


def write_task_doc_state_sync_output(
    *,
    payload: dict[str, Any],
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _build_slot_plan(
    *,
    slot_name: str,
    task_id: str,
    task_dir: Path | None,
    facts_obj: dict[str, Any],
    task_block_decision: str | None,
    task_block_reason: str | None,
    repo_root: Path,
) -> dict[str, Any]:
    spec = _as_dict(DOC_SLOT_SPECS.get(slot_name))
    filename = str(spec.get("filename", "")).strip()
    relative_path = None
    absolute_path = None
    if task_dir is not None and filename:
        absolute_path = task_dir / filename
        try:
            relative_path = absolute_path.relative_to(repo_root).as_posix()
        except ValueError:
            relative_path = absolute_path.as_posix()

    target_paths = [
        f"subtasks.{task_id}.facts.{slot_name}.exists",
        f"subtasks.{task_id}.facts.{slot_name}.template_like",
        f"subtasks.{task_id}.facts.docs.{slot_name}.exists",
        f"subtasks.{task_id}.facts.docs.{slot_name}.template_like",
        f"subtasks.{task_id}.facts.docs.{slot_name}.path",
    ]
    current_direct = _as_dict(facts_obj.get(slot_name))
    current_docs = _as_dict(facts_obj.get("docs"))
    current_nested = _as_dict(current_docs.get(slot_name))
    current_state = {
        "exists": current_direct.get("exists"),
        "template_like": current_direct.get("template_like"),
        "path": _normalize_path_text(current_nested.get("path")),
    }

    if task_block_decision is not None:
        return {
            "slot_name": slot_name,
            "filename": filename,
            "path": relative_path,
            "current_state": current_state,
            "desired_state": None,
            "target_paths": [],
            "planned_fields": [],
            "file_exists": False,
            "missing_required_headings": [],
            "minimal_sync_ready": False,
            "detected_template_like": None,
            "template_diagnostics": [],
            "already_synced": False,
            "apply_allowed": False,
            "decision": task_block_decision,
            "reason": task_block_reason or "",
        }

    file_exists = bool(absolute_path and absolute_path.exists())
    if not file_exists:
        return {
            "slot_name": slot_name,
            "filename": filename,
            "path": relative_path,
            "current_state": current_state,
            "desired_state": None,
            "target_paths": [],
            "planned_fields": [],
            "file_exists": False,
            "missing_required_headings": list(_as_tuple_of_strings(spec.get("required_headings"))),
            "minimal_sync_ready": False,
            "detected_template_like": None,
            "template_diagnostics": [],
            "already_synced": False,
            "apply_allowed": False,
            "decision": "blocked_doc_file_missing",
            "reason": "目标文档文件不存在，当前不能同步该 doc slot。",
        }

    text = absolute_path.read_text(encoding="utf-8")
    required_headings = _as_tuple_of_strings(spec.get("required_headings"))
    missing_required_headings = [marker for marker in required_headings if marker not in text]
    if missing_required_headings:
        current_is_formal = current_state["exists"] is True and current_state["template_like"] is False
        decision = (
            "blocked_existing_formal_state_conflict"
            if current_is_formal
            else "blocked_minimal_headings_missing"
        )
        reason = (
            "磁盘文档与当前正式判断不一致，本轮不自动覆盖已有正式文档判断。"
            if current_is_formal
            else "目标文档缺少最小骨架章节，当前不能同步该 doc slot。"
        )
        return {
            "slot_name": slot_name,
            "filename": filename,
            "path": relative_path,
            "current_state": current_state,
            "desired_state": None,
            "target_paths": [],
            "planned_fields": [],
            "file_exists": True,
            "missing_required_headings": missing_required_headings,
            "minimal_sync_ready": False,
            "detected_template_like": None,
            "template_diagnostics": [],
            "already_synced": False,
            "apply_allowed": False,
            "decision": decision,
            "reason": reason,
        }

    template_like, template_diagnostics = detect_template_signals(
        path=str(relative_path or absolute_path.as_posix()),
        text=text,
        doc_kind=str(spec.get("doc_kind", "")).strip(),
    )
    desired_exists = True
    desired_template_like = bool(template_like)
    desired_path = relative_path or absolute_path.as_posix()
    current_is_formal = current_state["exists"] is True and current_state["template_like"] is False

    if current_is_formal and desired_template_like:
        return {
            "slot_name": slot_name,
            "filename": filename,
            "path": relative_path,
            "current_state": current_state,
            "desired_state": None,
            "target_paths": [],
            "planned_fields": [],
            "file_exists": True,
            "missing_required_headings": [],
            "minimal_sync_ready": True,
            "detected_template_like": desired_template_like,
            "template_diagnostics": template_diagnostics,
            "already_synced": False,
            "apply_allowed": False,
            "decision": "blocked_existing_formal_state_conflict",
            "reason": "磁盘文档会导致 formal 判断降级，本轮不自动覆盖已有正式文档判断。",
        }

    desired_state = {
        "exists": True,
        "template_like": current_state["template_like"]
        if current_is_formal and current_state["template_like"] is False
        else desired_template_like,
        "path": desired_path,
    }
    current_nested_exists = current_nested.get("exists")
    current_nested_template_like = current_nested.get("template_like")
    current_nested_path = _normalize_path_text(current_nested.get("path"))

    already_synced = (
        current_state["exists"] is desired_state["exists"]
        and current_state["template_like"] is desired_state["template_like"]
        and current_nested_exists is desired_state["exists"]
        and current_nested_template_like is desired_state["template_like"]
        and current_nested_path == desired_state["path"]
    )
    planned_fields = [] if already_synced else list(target_paths)
    reason = (
        "当前 doc slot 最小状态已同步，不需要重复写回。"
        if already_synced
        else "满足最小骨架条件，可同步文档槽位存在性、template_like 与路径。"
    )
    return {
        "slot_name": slot_name,
        "filename": filename,
        "path": relative_path,
        "current_state": current_state,
        "desired_state": desired_state,
        "target_paths": planned_fields,
        "planned_fields": planned_fields,
        "file_exists": True,
        "missing_required_headings": [],
        "minimal_sync_ready": True,
        "detected_template_like": desired_template_like,
        "template_diagnostics": template_diagnostics,
        "already_synced": already_synced,
        "apply_allowed": not already_synced,
        "decision": "already_synced" if already_synced else "planned",
        "reason": reason,
    }


def _apply_slot_syncs(
    *,
    task_obj: dict[str, Any],
    slot_plans: list[dict[str, Any]],
) -> dict[str, Any]:
    updated_task = dict(task_obj)
    facts = _as_dict(task_obj.get("facts"))
    updated_facts = dict(facts)
    docs_map = _as_dict(updated_facts.get("docs"))
    updated_docs = dict(docs_map)

    for slot_plan in slot_plans:
        slot_name = str(slot_plan.get("slot_name", "")).strip()
        desired_state = _as_dict(slot_plan.get("desired_state"))
        if not slot_name or not desired_state:
            continue
        updated_facts[slot_name] = {
            "exists": bool(desired_state.get("exists")),
            "template_like": bool(desired_state.get("template_like")),
        }
        current_nested = _as_dict(updated_docs.get(slot_name))
        updated_nested = dict(current_nested)
        updated_nested["exists"] = bool(desired_state.get("exists"))
        updated_nested["template_like"] = bool(desired_state.get("template_like"))
        updated_nested["path"] = str(desired_state.get("path", "")).strip()
        updated_docs[slot_name] = updated_nested

    updated_facts["docs"] = updated_docs
    updated_task["facts"] = updated_facts
    return updated_task


def _resolve_requirement_relation(
    *,
    task_id: str,
    meta_obj: dict[str, Any],
    facts_obj: dict[str, Any],
    known_requirement_ids: set[str],
    container_relations: dict[str, list[str]],
) -> dict[str, Any]:
    native_ids = _collect_native_requirement_ids(
        meta_obj=meta_obj,
        facts_obj=facts_obj,
        known_requirement_ids=known_requirement_ids,
    )
    container_ids = _dedupe_strings(container_relations.get(task_id, []))

    if len(native_ids) > 1 or len(container_ids) > 1:
        return {
            "requirement_id": None,
            "relation_source": "ambiguous",
            "decision": "blocked_requirement_relation_ambiguous",
            "reason": "task requirement relation 不唯一，当前不能同步文档槽位状态。",
        }
    if native_ids and container_ids and native_ids != container_ids:
        return {
            "requirement_id": None,
            "relation_source": "conflict",
            "decision": "blocked_requirement_relation_conflict",
            "reason": "task entity side 与 requirement 容器侧 relation 不一致，当前拒绝同步。",
        }
    if native_ids:
        return {
            "requirement_id": native_ids[0],
            "relation_source": "entity_native" if not container_ids else "entity_and_container",
            "decision": "resolved",
            "reason": "",
        }
    if container_ids:
        return {
            "requirement_id": container_ids[0],
            "relation_source": "requirement_container",
            "decision": "resolved",
            "reason": "",
        }
    return {
        "requirement_id": None,
        "relation_source": "missing",
        "decision": "blocked_requirement_relation_missing",
        "reason": "task 当前没有 requirement relation，且 requirement 容器侧也无法唯一推导，不能同步。",
    }


def _collect_native_requirement_ids(
    *,
    meta_obj: dict[str, Any],
    facts_obj: dict[str, Any],
    known_requirement_ids: set[str],
) -> list[str]:
    requirement_ids: list[str] = []
    meta_requirement_id = _normalize_requirement_text(
        meta_obj.get(schema.REQUIREMENT_RELATION_META_FIELD)
    )
    if meta_requirement_id:
        requirement_ids.append(meta_requirement_id)
    for requirement_id in _as_string_list(
        facts_obj.get(schema.REQUIREMENT_RELATION_FACT_FIELD)
    ):
        requirement_ids.append(requirement_id)
    return [
        requirement_id
        for requirement_id in _dedupe_strings(requirement_ids)
        if requirement_id in known_requirement_ids
    ]


def _collect_container_relations(
    *,
    requirements: dict[str, Any],
    relation_field: str,
    known_requirement_ids: set[str],
) -> dict[str, list[str]]:
    relation_map: dict[str, list[str]] = {}
    for requirement_id, requirement_obj in requirements.items():
        normalized_requirement_id = str(requirement_id).strip()
        if normalized_requirement_id not in known_requirement_ids:
            continue
        facts = _as_dict(_as_dict(requirement_obj).get("facts"))
        for entity_id in _as_string_list(facts.get(relation_field)):
            relation_map.setdefault(entity_id, [])
            if normalized_requirement_id not in relation_map[entity_id]:
                relation_map[entity_id].append(normalized_requirement_id)
    return relation_map


def _build_change_summary(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "task_id": task.get("task_id", ""),
            "slot_name": slot.get("slot_name", ""),
            "decision": slot.get("decision", ""),
            "target_paths": slot.get("target_paths", []),
            "reason": slot.get("reason", ""),
        }
        for task in tasks
        for slot in _as_list_of_dicts(task.get("slots"))
    ]


def _parse_task_ids(
    *,
    entity_ids: list[str] | tuple[str, ...] | str,
    subtasks: dict[str, Any],
) -> list[str]:
    if isinstance(entity_ids, str):
        raw_values = [item.strip() for item in entity_ids.split(",")]
    else:
        raw_values = [str(item).strip() for item in entity_ids]
    task_ids = _dedupe_strings([item for item in raw_values if item])
    if not task_ids:
        raise ValueError("至少需要一个 --entity-id")
    if len(task_ids) > MAX_TASK_COUNT:
        raise ValueError(f"一次最多只允许处理 {MAX_TASK_COUNT} 个 task")
    missing = [task_id for task_id in task_ids if task_id not in subtasks]
    if missing:
        raise ValueError(f"entity-id not found or not a task: {', '.join(missing)}")
    return task_ids


def _resolve_repo_root(state_path: Path) -> Path:
    resolved = state_path.resolve()
    parts = resolved.parts
    if "docs" in parts:
        docs_index = parts.index("docs")
        return Path(*parts[:docs_index])
    return resolved.parent


def _resolve_task_dir(*, repo_root: Path, task_path: str) -> Path | None:
    normalized = task_path.strip().rstrip("/\\")
    if not normalized:
        return None
    return repo_root / Path(normalized)


def _replace_entity_block(
    *,
    original_text: str,
    section_name: str,
    entity_id: str,
    updated_entity_obj: dict[str, Any],
) -> str:
    lines = original_text.splitlines(keepends=True)
    section_index = _find_top_level_key(lines, section_name)
    if section_index is None:
        raise ValueError(f"state 文件中缺少 {section_name} 顶层区块")
    entity_index = _find_entity_index(
        lines=lines,
        entity_id=entity_id,
        start=section_index + 1,
    )
    if entity_index is None:
        raise ValueError(f"未找到 subtask 实体: {entity_id}")
    entity_end = _find_block_end(lines=lines, start=entity_index + 1, indent=2)
    replacement = _render_entity_block(
        entity_id=entity_id,
        entity_obj=updated_entity_obj,
    )
    lines[entity_index:entity_end] = replacement
    return "".join(lines)


def _render_entity_block(
    *,
    entity_id: str,
    entity_obj: dict[str, Any],
) -> list[str]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to write DOC_STATE.yaml") from exc
    dumped = yaml.safe_dump(
        {entity_id: entity_obj},
        sort_keys=False,
        allow_unicode=True,
        width=120,
    )
    return [f"  {line}" if line else line for line in dumped.splitlines(keepends=True)]


def _find_top_level_key(lines: list[str], key: str) -> int | None:
    target = f"{key}:"
    for index, line in enumerate(lines):
        if line.rstrip("\r\n") == target:
            return index
    return None


def _find_entity_index(
    *,
    lines: list[str],
    entity_id: str,
    start: int,
) -> int | None:
    target = f"  {entity_id}:"
    for index in range(start, len(lines)):
        stripped = lines[index].strip()
        if not stripped:
            continue
        if _leading_spaces(lines[index]) == 0:
            return None
        if lines[index].rstrip("\r\n") == target:
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


def _leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _load_state(state_path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to read DOC_STATE.yaml") from exc
    loaded = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _read_text(state_path: Path) -> str:
    return state_path.read_text(encoding="utf-8")


def _write_text(*, state_path: Path, text: str) -> None:
    with state_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def _normalize_requirement_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _normalize_path_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


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


def _as_tuple_of_strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


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
