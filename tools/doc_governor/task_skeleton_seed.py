from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import schema

MAX_TASK_COUNT = 10
DESIGN_FILENAME = "SUBTASK_DESIGN.md"
IMPLEMENTATION_FILENAME = "SUBTASK_IMPLEMENTATION.md"
MANUAL_FILL_FIELDS = ["allowed_modify_paths", "required_tests", "acceptance_criteria"]


def build_task_skeleton_seed_plan(
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

        blocked_reason = None
        blocked_decision = None
        if requirement_id is None:
            blocked_decision = str(requirement_resolution["decision"])
            blocked_reason = str(requirement_resolution["reason"])
        elif task_dir is None:
            blocked_decision = "blocked_task_path_missing"
            blocked_reason = "task 缺少可写入的目录 path，当前不能生成双文档骨架。"

        design_plan = _build_doc_plan(
            task_id=task_id,
            task_dir=task_dir,
            doc_kind="design",
            doc_state=_as_dict(facts.get("design_doc")),
        )
        implementation_plan = _build_doc_plan(
            task_id=task_id,
            task_dir=task_dir,
            doc_kind="implementation",
            doc_state=_as_dict(facts.get("implementation_doc")),
        )

        file_plans = [design_plan, implementation_plan]
        blocked_file_plans = [
            item
            for item in file_plans
            if str(item.get("decision", "")).startswith("blocked_")
        ]
        if blocked_file_plans and blocked_decision is None:
            blocked_decision = str(blocked_file_plans[0].get("decision", "blocked_doc_write"))
            blocked_reason = str(blocked_file_plans[0].get("reason", "目标文档不允许自动 seed。"))

        planned_file_count = sum(1 for item in file_plans if bool(item.get("apply_allowed")))
        already_seeded = (
            blocked_decision is None
            and planned_file_count == 0
            and all(str(item.get("decision", "")) == "already_seeded" for item in file_plans)
        )
        apply_allowed = blocked_decision is None and planned_file_count > 0
        decision = (
            blocked_decision
            if blocked_decision is not None
            else ("already_seeded" if already_seeded else "planned")
        )
        reason = (
            blocked_reason
            if blocked_reason is not None
            else (
                "当前 task 的最小双文档骨架已存在，不需要重复 seed。"
                if already_seeded
                else "满足最小安全条件，可生成双文档正式骨架。"
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
                "manual_fill_fields": list(MANUAL_FILL_FIELDS),
                "files": file_plans,
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
        "already_seeded_task_count": sum(
            1 for item in tasks if str(item.get("decision", "")) == "already_seeded"
        ),
        "planned_file_count": sum(
            1
            for task in tasks
            for file_plan in _as_list_of_dicts(task.get("files"))
            if bool(file_plan.get("apply_allowed"))
        ),
        "written_file_count": 0,
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
            "默认模式是 dry-run，只输出 task skeleton seed 计划，不修改任何文档文件。",
            "只有显式选中的 task 才会参与 seed，且默认最多 10 个。",
            "只有 task requirement relation 唯一且明确时才允许 seed；relation 不明确会直接拒绝。",
            "真正 apply 时只写 SUBTASK_DESIGN.md 与 SUBTASK_IMPLEMENTATION.md 的最小中文骨架，不写 DOC_STATE.yaml。",
        ],
    }


def execute_task_skeleton_seed(
    *,
    state_path: str | Path,
    entity_ids: list[str] | tuple[str, ...] | str,
    apply_changes: bool = False,
) -> dict[str, Any]:
    plan = build_task_skeleton_seed_plan(
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

    written_file_count = 0
    updated_tasks: list[dict[str, Any]] = []
    for task in _as_list_of_dicts(plan.get("tasks")):
        updated_task = dict(task)
        updated_files: list[dict[str, Any]] = []
        for file_plan in _as_list_of_dicts(task.get("files")):
            updated_file = dict(file_plan)
            if bool(updated_file.get("apply_allowed")):
                content = _render_doc(
                    doc_kind=str(updated_file.get("doc_kind", "")),
                    task_id=str(task.get("task_id", "")),
                    module_id=str(task.get("module_id", "")),
                    requirement_id=str(task.get("requirement_id", "")),
                )
                path = Path(str(updated_file.get("path", "")))
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                updated_file["status"] = "written"
                updated_file["decision"] = "written"
                written_file_count += 1
            else:
                updated_file["status"] = "unchanged"
            updated_files.append(updated_file)
        updated_task["files"] = updated_files
        updated_tasks.append(updated_task)

    result = dict(plan)
    result["mode"] = "apply"
    result["tasks"] = updated_tasks
    result["summary"] = {
        **_as_dict(plan.get("summary")),
        "written_file_count": written_file_count,
    }
    result["result_summary"] = {
        "written_files": [
            file_plan.get("path", "")
            for task in updated_tasks
            for file_plan in _as_list_of_dicts(task.get("files"))
            if file_plan.get("status") == "written"
        ],
        "manual_fill_fields_remaining": [
            {
                "task_id": task.get("task_id", ""),
                "fields": _as_string_list(task.get("manual_fill_fields")),
            }
            for task in updated_tasks
            if _as_string_list(task.get("manual_fill_fields"))
        ],
    }
    return result


def write_task_skeleton_seed_output(
    *,
    payload: dict[str, Any],
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


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
            "reason": "task requirement relation 不唯一，当前不能自动 seed。",
        }
    if native_ids and container_ids and native_ids != container_ids:
        return {
            "requirement_id": None,
            "relation_source": "conflict",
            "decision": "blocked_requirement_relation_conflict",
            "reason": "task entity side 与 requirement 容器侧 relation 不一致，当前拒绝 seed。",
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
        "reason": "task 当前没有 requirement relation，且 requirement 容器侧也无法唯一推导，不能 seed。",
    }


def _collect_native_requirement_ids(
    *,
    meta_obj: dict[str, Any],
    facts_obj: dict[str, Any],
    known_requirement_ids: set[str],
) -> list[str]:
    requirement_ids: list[str] = []
    meta_requirement_id = _normalize_text(
        meta_obj.get(schema.REQUIREMENT_RELATION_META_FIELD)
    )
    if meta_requirement_id:
        requirement_ids.append(meta_requirement_id)
    requirement_ids.extend(
        _as_string_list(facts_obj.get(schema.REQUIREMENT_RELATION_FACT_FIELD))
    )
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


def _build_doc_plan(
    *,
    task_id: str,
    task_dir: Path | None,
    doc_kind: str,
    doc_state: dict[str, Any],
) -> dict[str, Any]:
    filename = DESIGN_FILENAME if doc_kind == "design" else IMPLEMENTATION_FILENAME
    exists_in_state = bool(doc_state.get("exists"))
    template_like_in_state = bool(doc_state.get("template_like"))
    path = task_dir / filename if task_dir is not None else None
    exists_on_disk = bool(path and path.exists())

    if task_dir is None or path is None:
        return {
            "doc_kind": doc_kind,
            "path": "",
            "exists_in_state": exists_in_state,
            "template_like_in_state": template_like_in_state,
            "exists_on_disk": exists_on_disk,
            "apply_allowed": False,
            "decision": "blocked_doc_path_missing",
            "reason": f"{task_id} 缺少 {filename} 的目标目录，当前不能生成骨架。",
            "write_mode": None,
        }

    if exists_in_state and not template_like_in_state:
        return {
            "doc_kind": doc_kind,
            "path": path.as_posix(),
            "exists_in_state": exists_in_state,
            "template_like_in_state": template_like_in_state,
            "exists_on_disk": exists_on_disk,
            "apply_allowed": False,
            "decision": "already_seeded",
            "reason": f"{filename} 已是正式文档，当前不重复 seed。",
            "write_mode": None,
        }

    if exists_on_disk and not template_like_in_state and not exists_in_state:
        return {
            "doc_kind": doc_kind,
            "path": path.as_posix(),
            "exists_in_state": exists_in_state,
            "template_like_in_state": template_like_in_state,
            "exists_on_disk": exists_on_disk,
            "apply_allowed": False,
            "decision": "blocked_disk_conflict",
            "reason": f"{filename} 在磁盘上已存在，但 state 未声明可替换模板，当前拒绝覆盖。",
            "write_mode": None,
        }

    return {
        "doc_kind": doc_kind,
        "path": path.as_posix(),
        "exists_in_state": exists_in_state,
        "template_like_in_state": template_like_in_state,
        "exists_on_disk": exists_on_disk,
        "apply_allowed": True,
        "decision": "planned",
        "reason": f"{filename} 可生成最小正式骨架。",
        "write_mode": "replace_template" if template_like_in_state or exists_on_disk else "create",
    }


def _render_doc(
    *,
    doc_kind: str,
    task_id: str,
    module_id: str,
    requirement_id: str,
) -> str:
    if doc_kind == "design":
        return _render_design_doc(
            task_id=task_id,
            module_id=module_id,
            requirement_id=requirement_id,
        )
    return _render_implementation_doc(
        task_id=task_id,
        module_id=module_id,
        requirement_id=requirement_id,
    )


def _render_design_doc(
    *,
    task_id: str,
    module_id: str,
    requirement_id: str,
) -> str:
    lines = [
        "# 子任务设计文档",
        "",
        "## 3. 子任务目标",
        f"- 当前子任务：`{task_id}`",
        f"- 当前所属模块：`{module_id}`",
        f"- 当前关联 requirement：`{requirement_id}`",
        "- 待人工填写：子任务目标",
        "",
        "## 5. 技术方案",
        "- 待人工填写：技术方案",
    ]
    return "\n".join(lines) + "\n"


def _render_implementation_doc(
    *,
    task_id: str,
    module_id: str,
    requirement_id: str,
) -> str:
    lines = [
        "# 子任务实施文档",
        "",
        "## 3. 本轮实施目标",
        f"- 当前子任务：`{task_id}`",
        f"- 当前所属模块：`{module_id}`",
        f"- 当前关联 requirement：`{requirement_id}`",
        "- 待人工填写：本轮实施目标",
        "",
        "## 5. 允许修改范围",
        "",
        "### 5.1 允许修改",
        "- 待人工填写：allowed_modify_paths",
        "",
        "### 5.2 禁止修改",
        "- 待人工确认：forbidden_paths（如无额外限制可保留为空）",
        "",
        "## 7. 测试与验证",
        "",
        "### 7.1 自动化验证",
        "- 待人工填写：required_tests",
        "",
        "## 8. 完成判定",
        "- 待人工填写：acceptance_criteria",
    ]
    return "\n".join(lines) + "\n"


def _build_change_summary(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "task_id": task.get("task_id", ""),
            "requirement_id": task.get("requirement_id", ""),
            "decision": task.get("decision", ""),
            "files": [
                {
                    "doc_kind": file_plan.get("doc_kind", ""),
                    "path": file_plan.get("path", ""),
                    "decision": file_plan.get("decision", ""),
                }
                for file_plan in _as_list_of_dicts(task.get("files"))
            ],
        }
        for task in tasks
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
        raise ValueError(f"单次最多只允许处理 {MAX_TASK_COUNT} 个 task")
    missing = [task_id for task_id in task_ids if task_id not in subtasks]
    if missing:
        raise ValueError(f"entity-id not found or not a task: {', '.join(missing)}")
    return task_ids


def _resolve_repo_root(state_path: Path) -> Path:
    normalized = state_path.resolve()
    try:
        if normalized.parent.name == "governance" and normalized.parent.parent.name == "docs":
            return normalized.parent.parent.parent
    except IndexError:
        pass
    return normalized.parent


def _resolve_task_dir(*, repo_root: Path, task_path: str) -> Path | None:
    normalized = task_path.strip().rstrip("/\\")
    if not normalized:
        return None
    return repo_root / Path(normalized)


def _load_state(state_path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to read DOC_STATE.yaml") from exc
    loaded = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _normalize_text(value: Any) -> str | None:
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
