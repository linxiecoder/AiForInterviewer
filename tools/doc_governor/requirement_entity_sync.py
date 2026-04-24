from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import schema


def build_requirement_entity_sync_plan(
    *,
    state_path: str | Path,
    entity_ids: list[str] | tuple[str, ...] | str | None = None,
) -> dict[str, Any]:
    state_path = Path(state_path)
    state = _load_state(state_path)
    requirements = _as_dict(state.get("requirements"))
    modules = _as_dict(state.get("modules"))
    subtasks = _as_dict(state.get("subtasks"))
    selected_requirement_ids = _normalize_requirement_ids(
        entity_ids=entity_ids,
        requirements=requirements,
    )
    known_requirement_ids = set(requirements.keys())
    module_container_relations = _collect_container_relations(
        requirements=requirements,
        relation_field="module_ids",
        known_requirement_ids=known_requirement_ids,
    )
    task_container_relations = _collect_container_relations(
        requirements=requirements,
        relation_field="task_ids",
        known_requirement_ids=known_requirement_ids,
    )

    selected_module_ids: list[str] = []
    selected_task_ids: list[str] = []
    entity_relations: list[dict[str, Any]] = []
    requirement_summaries: list[dict[str, Any]] = []

    for requirement_id in selected_requirement_ids:
        requirement = _as_dict(requirements.get(requirement_id))
        facts = _as_dict(requirement.get("facts"))
        module_ids = _as_string_list(facts.get("module_ids"))
        task_ids = _as_string_list(facts.get("task_ids"))
        selected_module_ids.extend(module_ids)
        selected_task_ids.extend(task_ids)
        requirement_summaries.append(
            {
                "requirement_id": requirement_id,
                "module_ids": module_ids,
                "task_ids": task_ids,
                "entity_relation_count": len(module_ids) + len(task_ids),
            }
        )
        for module_id in module_ids:
            entity_relations.append(
                _build_entity_relation_plan_item(
                    entity_type="module",
                    entity_id=module_id,
                    requirement_id=requirement_id,
                    entities=modules,
                    known_requirement_ids=known_requirement_ids,
                    container_relations=module_container_relations,
                )
            )
        for task_id in task_ids:
            entity_relations.append(
                _build_entity_relation_plan_item(
                    entity_type="subtask",
                    entity_id=task_id,
                    requirement_id=requirement_id,
                    entities=subtasks,
                    known_requirement_ids=known_requirement_ids,
                    container_relations=task_container_relations,
                )
            )

    blocked_relations = [
        {
            "entity_type": item.get("entity_type", ""),
            "entity_id": item.get("entity_id", ""),
            "requirement_id": item.get("requirement_id", ""),
            "decision": item.get("decision", ""),
            "reason": item.get("reason", ""),
        }
        for item in entity_relations
        if str(item.get("decision", "")).startswith("blocked_")
    ]
    summary = {
        "selected_requirement_count": len(selected_requirement_ids),
        "selected_module_count": len(_dedupe_strings(selected_module_ids)),
        "selected_task_count": len(_dedupe_strings(selected_task_ids)),
        "selected_relation_count": len(entity_relations),
        "planned_write_count": sum(
            1
            for item in entity_relations
            if bool(item.get("apply_allowed")) and not bool(item.get("already_synced"))
        ),
        "already_synced_count": sum(
            1 for item in entity_relations if bool(item.get("already_synced"))
        ),
        "blocked_relation_count": len(blocked_relations),
        "state_write_enabled": False,
        "applied_write_count": 0,
    }

    return {
        "ok": True,
        "mode": "dry_run",
        "input_state_path": str(state_path.resolve()),
        "entity_ids": selected_requirement_ids,
        "summary": summary,
        "requirements": requirement_summaries,
        "entity_relations": entity_relations,
        "blocked_relations": blocked_relations,
        "change_summary": _build_change_summary(entity_relations),
        "reasoning_notes": [
            "默认模式是 dry-run，只输出 requirement relation entity-side 同步计划，不修改 DOC_STATE.yaml。",
            "写回只处理 requirement 容器已经正式声明的 module_ids / task_ids，不推断新的 requirement 候选。",
            "真正 apply 时只会最小化同步 meta.requirement_id 与 facts.requirement_ids，不会顺手修改其他状态字段。",
            "若 entity side 已存在冲突 relation 或 container 自身不唯一，当前批次会拒绝 apply，保留人工处理门槛。",
        ],
    }


def execute_requirement_entity_sync(
    *,
    state_path: str | Path,
    entity_ids: list[str] | tuple[str, ...] | str | None = None,
    apply_changes: bool = False,
) -> dict[str, Any]:
    plan = build_requirement_entity_sync_plan(
        state_path=state_path,
        entity_ids=entity_ids,
    )
    if not apply_changes:
        return plan

    blocked_relations = [
        item
        for item in _as_list_of_dicts(plan.get("entity_relations"))
        if str(item.get("decision", "")).startswith("blocked_")
    ]
    if blocked_relations:
        labels = ", ".join(
            f"{item.get('entity_type', '')}:{item.get('entity_id', '')}"
            for item in blocked_relations
        )
        raise ValueError(f"存在不允许 apply 的 relation: {labels}")

    state_path = Path(state_path)
    state = _load_state(state_path)
    updated_text = _read_text(state_path)
    written_relations: list[dict[str, Any]] = []
    changed_paths: list[str] = []
    updated_relations: list[dict[str, Any]] = []

    for relation in _as_list_of_dicts(plan.get("entity_relations")):
        relation_record = dict(relation)
        if bool(relation_record.get("already_synced")):
            relation_record["decision"] = "already_synced"
            relation_record["write_status"] = "unchanged"
            updated_relations.append(relation_record)
            continue

        entity_type = str(relation_record.get("entity_type", "")).strip()
        entity_id = str(relation_record.get("entity_id", "")).strip()
        requirement_id = str(relation_record.get("requirement_id", "")).strip()
        state_collection_key = "modules" if entity_type == "module" else "subtasks"
        entity_obj = _as_dict(_as_dict(state.get(state_collection_key)).get(entity_id))
        updated_entity_obj = _apply_requirement_relation(
            entity_obj=entity_obj,
            requirement_id=requirement_id,
        )
        updated_text = _replace_entity_block(
            original_text=updated_text,
            section_name=state_collection_key,
            entity_id=entity_id,
            updated_entity_obj=updated_entity_obj,
        )
        written_relations.append(
            {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "requirement_id": requirement_id,
                "target_paths": _as_string_list(relation_record.get("target_paths")),
            }
        )
        changed_paths.extend(_as_string_list(relation_record.get("target_paths")))
        relation_record["decision"] = "written"
        relation_record["write_status"] = "written"
        updated_relations.append(relation_record)

    if written_relations:
        _write_text(state_path=state_path, text=updated_text)

    affected_entities = [
        f"{item.get('entity_type', '')}:{item.get('entity_id', '')}"
        for item in updated_relations
        if item.get("entity_id")
    ]
    result = dict(plan)
    result["mode"] = "apply"
    result["entity_relations"] = updated_relations
    result["summary"] = {
        **_as_dict(plan.get("summary")),
        "state_write_enabled": True,
        "applied_write_count": len(written_relations),
    }
    result["result_summary"] = {
        "written_relations": written_relations,
        "changed_state_paths": _dedupe_strings(changed_paths),
        "affected_entities": _dedupe_strings(affected_entities),
        "unchanged_entities": [
            f"{item.get('entity_type', '')}:{item.get('entity_id', '')}"
            for item in updated_relations
            if item.get("write_status") == "unchanged"
        ],
    }
    return result


def write_requirement_entity_sync_output(
    *,
    payload: dict[str, Any],
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _build_entity_relation_plan_item(
    *,
    entity_type: str,
    entity_id: str,
    requirement_id: str,
    entities: dict[str, Any],
    known_requirement_ids: set[str],
    container_relations: dict[str, list[str]],
) -> dict[str, Any]:
    target_paths = [
        f"{entity_type}s.{entity_id}.meta.{schema.REQUIREMENT_RELATION_META_FIELD}",
        f"{entity_type}s.{entity_id}.facts.{schema.REQUIREMENT_RELATION_FACT_FIELD}",
    ]
    entity_obj = _as_dict(entities.get(entity_id))
    if not entity_obj:
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "requirement_id": requirement_id,
            "container_requirement_ids": _dedupe_strings(container_relations.get(entity_id, [])),
            "existing_meta_requirement_id": None,
            "existing_requirement_ids": [],
            "target_paths": target_paths,
            "already_synced": False,
            "apply_allowed": False,
            "decision": "blocked_entity_not_found",
            "reason": "requirement 容器声明了 relation，但目标 entity 在 official state 中不存在。",
            "change_preview": None,
        }

    meta = _as_dict(entity_obj.get("meta"))
    facts = _as_dict(entity_obj.get("facts"))
    existing_requirement_ids = _collect_entity_requirement_ids(
        meta_obj=meta,
        facts_obj=facts,
        known_requirement_ids=known_requirement_ids,
    )
    existing_meta_requirement_id = _normalize_requirement_text(
        meta.get(schema.REQUIREMENT_RELATION_META_FIELD)
    )
    container_requirement_ids = _dedupe_strings(container_relations.get(entity_id, []))

    if len(container_requirement_ids) > 1:
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "requirement_id": requirement_id,
            "container_requirement_ids": container_requirement_ids,
            "existing_meta_requirement_id": existing_meta_requirement_id,
            "existing_requirement_ids": existing_requirement_ids,
            "target_paths": target_paths,
            "already_synced": False,
            "apply_allowed": False,
            "decision": "blocked_container_ambiguous",
            "reason": "同一 entity 在 requirement 容器侧对应多个 requirement，当前不能自动同步。",
            "change_preview": None,
        }

    expected_requirement_ids = [requirement_id]
    if existing_requirement_ids and set(existing_requirement_ids) != {requirement_id}:
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "requirement_id": requirement_id,
            "container_requirement_ids": container_requirement_ids,
            "existing_meta_requirement_id": existing_meta_requirement_id,
            "existing_requirement_ids": existing_requirement_ids,
            "target_paths": target_paths,
            "already_synced": False,
            "apply_allowed": False,
            "decision": "blocked_entity_conflict",
            "reason": "entity side 已存在与 requirement 容器不一致的 relation，当前拒绝自动覆盖。",
            "change_preview": {
                "before_meta_requirement_id": existing_meta_requirement_id,
                "before_requirement_ids": existing_requirement_ids,
                "after_meta_requirement_id": requirement_id,
                "after_requirement_ids": expected_requirement_ids,
            },
        }

    already_synced = (
        existing_meta_requirement_id == requirement_id
        and existing_requirement_ids == expected_requirement_ids
    )
    decision = "already_synced" if already_synced else "planned"
    reason = (
        "entity side requirement relation 已与容器声明一致，不需要重复写入。"
        if already_synced
        else "满足最小安全条件，可将 requirement 容器声明同步到 entity side。"
    )
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "requirement_id": requirement_id,
        "container_requirement_ids": container_requirement_ids,
        "existing_meta_requirement_id": existing_meta_requirement_id,
        "existing_requirement_ids": existing_requirement_ids,
        "target_paths": target_paths,
        "already_synced": already_synced,
        "apply_allowed": not already_synced,
        "decision": decision,
        "reason": reason,
        "change_preview": {
            "before_meta_requirement_id": existing_meta_requirement_id,
            "before_requirement_ids": existing_requirement_ids,
            "after_meta_requirement_id": requirement_id,
            "after_requirement_ids": expected_requirement_ids,
        },
    }


def _apply_requirement_relation(
    *,
    entity_obj: dict[str, Any],
    requirement_id: str,
) -> dict[str, Any]:
    updated_entity = dict(entity_obj)
    updated_entity["meta"] = _build_meta_with_requirement(
        meta_obj=_as_dict(entity_obj.get("meta")),
        requirement_id=requirement_id,
    )
    updated_entity["facts"] = _build_facts_with_requirement(
        facts_obj=_as_dict(entity_obj.get("facts")),
        requirement_id=requirement_id,
    )
    return updated_entity


def _build_meta_with_requirement(
    *,
    meta_obj: dict[str, Any],
    requirement_id: str,
) -> dict[str, Any]:
    updated: dict[str, Any] = {}
    if "path" in meta_obj:
        updated["path"] = meta_obj.get("path")
    updated[schema.REQUIREMENT_RELATION_META_FIELD] = requirement_id
    for key, value in meta_obj.items():
        if key in {"path", schema.REQUIREMENT_RELATION_META_FIELD}:
            continue
        updated[key] = value
    return updated


def _build_facts_with_requirement(
    *,
    facts_obj: dict[str, Any],
    requirement_id: str,
) -> dict[str, Any]:
    updated: dict[str, Any] = {}
    inserted = False
    if "upstream_module_ids" not in facts_obj:
        updated[schema.REQUIREMENT_RELATION_FACT_FIELD] = [requirement_id]
        inserted = True
    for key, value in facts_obj.items():
        if key == schema.REQUIREMENT_RELATION_FACT_FIELD:
            continue
        updated[key] = value
        if key == "upstream_module_ids":
            updated[schema.REQUIREMENT_RELATION_FACT_FIELD] = [requirement_id]
            inserted = True
    if not inserted:
        updated[schema.REQUIREMENT_RELATION_FACT_FIELD] = [requirement_id]
    return updated


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
        raise ValueError(f"未找到 {section_name[:-1]} 实体: {entity_id}")
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


def _normalize_requirement_ids(
    *,
    entity_ids: list[str] | tuple[str, ...] | str | None,
    requirements: dict[str, Any],
) -> list[str]:
    if entity_ids is None:
        raw_values = []
    elif isinstance(entity_ids, str):
        raw_values = [item.strip() for item in entity_ids.split(",")]
    else:
        raw_values = [str(item).strip() for item in entity_ids]

    requirement_ids = _dedupe_strings([item for item in raw_values if item])
    if not requirement_ids:
        requirement_ids = [str(item).strip() for item in requirements.keys() if str(item).strip()]
    if not requirement_ids:
        raise ValueError("official state 中没有可同步的 requirement 容器")
    missing = [item for item in requirement_ids if item not in requirements]
    if missing:
        raise ValueError(f"entity-id not found or not a requirement: {', '.join(missing)}")
    return requirement_ids


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


def _collect_entity_requirement_ids(
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


def _normalize_requirement_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _build_change_summary(entity_relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "entity_type": item.get("entity_type", ""),
            "entity_id": item.get("entity_id", ""),
            "requirement_id": item.get("requirement_id", ""),
            "decision": item.get("decision", ""),
            "target_paths": item.get("target_paths", []),
            "reason": item.get("reason", ""),
        }
        for item in entity_relations
    ]


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
