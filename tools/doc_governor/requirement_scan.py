from __future__ import annotations

import re
from pathlib import Path

from .naming_rules import (
    MODULE_ID_RE,
    REQUIREMENT_ID_RE,
    REQUIREMENT_SCOPE_DIRECTORY,
    REQUIREMENT_SCOPE_ROOT_CLUSTER,
    SUBTASK_ID_RE,
    is_valid_requirement_path,
)
from .schema import make_default_compliance_state


REQUIREMENT_ROOT_ID = "RQ01"
REQUIREMENT_ASSET_SLOTS = {
    "plan_latest": "PLAN_LATEST.md",
    "module_index": "MODULE_INDEX.md",
    "task_index": "TASK_INDEX.md",
}
MARKDOWN_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|(?:\s*:?-+:?\s*\|)+\s*$")
REQUIREMENT_HEADER_TOKENS = ("requirement id", "requirement_id", "requirementid")


def scan_requirements(
    *,
    repo_root: str | Path,
    modules: dict[str, dict[str, object]],
    subtasks: dict[str, dict[str, object]],
) -> dict[str, object]:
    root = Path(repo_root).resolve()
    diagnostics: list[object] = []

    module_ids = sorted(
        module_id for module_id in modules.keys() if MODULE_ID_RE.fullmatch(str(module_id))
    )
    task_ids = sorted(
        task_id for task_id in subtasks.keys() if SUBTASK_ID_RE.fullmatch(str(task_id))
    )

    asset_slots: dict[str, dict[str, object]] = {}
    has_root_assets = False
    for slot_name, relative_path in REQUIREMENT_ASSET_SLOTS.items():
        slot_path = root / relative_path
        exists = slot_path.exists()
        has_root_assets = has_root_assets or exists
        asset_slots[slot_name] = {
            "exists": exists,
            "path": relative_path,
        }

    explicit_requirement_rows, module_requirement_ids, subtask_requirement_ids = (
        _scan_task_index_requirement_relations(
            root / REQUIREMENT_ASSET_SLOTS["task_index"],
            modules=modules,
            subtasks=subtasks,
        )
    )

    explicit_requirement_ids = sorted(
        set(explicit_requirement_rows) | _collect_requirement_ids(module_requirement_ids, subtask_requirement_ids)
    )
    should_emit_fallback_root = has_root_assets or bool(module_ids) or bool(task_ids)

    if explicit_requirement_ids:
        requirements = _build_explicit_requirements(
            explicit_requirement_ids=explicit_requirement_ids,
            explicit_requirement_rows=explicit_requirement_rows,
            asset_slots=asset_slots,
            module_ids=module_ids,
            task_ids=task_ids,
            modules=modules,
            subtasks=subtasks,
            module_requirement_ids=module_requirement_ids,
            subtask_requirement_ids=subtask_requirement_ids,
        )
    elif should_emit_fallback_root:
        requirements = {
            REQUIREMENT_ROOT_ID: _build_requirement_entry(
                requirement_id=REQUIREMENT_ROOT_ID,
                path=".",
                scope_kind=REQUIREMENT_SCOPE_ROOT_CLUSTER,
                module_ids=module_ids,
                task_ids=task_ids,
                asset_slots=asset_slots,
                modules=modules,
                subtasks=subtasks,
            )
        }
        module_requirement_ids = {
            module_id: [REQUIREMENT_ROOT_ID]
            for module_id in module_ids
        }
        subtask_requirement_ids = {
            task_id: [REQUIREMENT_ROOT_ID]
            for task_id in task_ids
        }
    else:
        requirements = {}

    return {
        "requirements": requirements,
        "module_requirement_ids": module_requirement_ids,
        "subtask_requirement_ids": subtask_requirement_ids,
        "diagnostics": diagnostics,
        "counts": {"requirement": len(requirements)},
    }


def _build_explicit_requirements(
    *,
    explicit_requirement_ids: list[str],
    explicit_requirement_rows: dict[str, dict[str, str]],
    asset_slots: dict[str, dict[str, object]],
    module_ids: list[str],
    task_ids: list[str],
    modules: dict[str, dict[str, object]],
    subtasks: dict[str, dict[str, object]],
    module_requirement_ids: dict[str, list[str]],
    subtask_requirement_ids: dict[str, list[str]],
) -> dict[str, dict[str, object]]:
    requirements: dict[str, dict[str, object]] = {}

    for requirement_id in explicit_requirement_ids:
        row = explicit_requirement_rows.get(requirement_id, {})
        path = row.get("path") or f"docs/requirements/{requirement_id}/"
        scope_kind = row.get("scope_kind") or REQUIREMENT_SCOPE_DIRECTORY
        requirement_module_ids = sorted(
            module_id
            for module_id in module_ids
            if requirement_id in module_requirement_ids.get(module_id, [])
        )
        requirement_task_ids = sorted(
            task_id
            for task_id in task_ids
            if requirement_id in subtask_requirement_ids.get(task_id, [])
        )
        requirements[requirement_id] = _build_requirement_entry(
            requirement_id=requirement_id,
            path=path,
            scope_kind=scope_kind,
            module_ids=requirement_module_ids,
            task_ids=requirement_task_ids,
            asset_slots=asset_slots,
            modules=modules,
            subtasks=subtasks,
        )

    return requirements


def _build_requirement_entry(
    *,
    requirement_id: str,
    path: str,
    scope_kind: str,
    module_ids: list[str],
    task_ids: list[str],
    asset_slots: dict[str, dict[str, object]],
    modules: dict[str, dict[str, object]],
    subtasks: dict[str, dict[str, object]],
) -> dict[str, object]:
    compliance = make_default_compliance_state()
    compliance["naming_ok"] = bool(REQUIREMENT_ID_RE.fullmatch(str(requirement_id)))
    compliance["path_ok"] = is_valid_requirement_path(
        requirement_id=requirement_id,
        path=path,
        scope_kind=scope_kind,
    )
    compliance["relations_ok"] = _requirement_relations_ok(
        module_ids=module_ids,
        task_ids=task_ids,
        modules=modules,
        subtasks=subtasks,
    )

    return {
        "meta": {
            "path": path,
            "scope_kind": scope_kind,
        },
        "facts": {
            "module_ids": module_ids,
            "task_ids": task_ids,
            "asset_slots": asset_slots,
            "compliance": compliance,
        },
    }


def _scan_task_index_requirement_relations(
    path: Path,
    *,
    modules: dict[str, dict[str, object]],
    subtasks: dict[str, dict[str, object]],
) -> tuple[dict[str, dict[str, str]], dict[str, list[str]], dict[str, list[str]]]:
    if not path.exists():
        return {}, {}, {}

    requirement_rows: dict[str, dict[str, str]] = {}
    module_requirement_ids: dict[str, list[str]] = {}
    subtask_requirement_ids: dict[str, list[str]] = {}
    subtask_parent_ids: dict[str, str] = {}

    tables = _find_all_markdown_tables(path.read_text(encoding="utf-8"))
    for headers, rows in tables:
        header_index = _build_task_index_header_index(headers)
        if "task_id" not in header_index or "path" not in header_index:
            continue
        requirement_index = header_index.get("requirement_id")
        parent_index = header_index.get("parent")
        for row in rows:
            task_id = _get_cell(row, header_index.get("task_id")).strip()
            path_value = _clean_doc_path(_get_cell(row, header_index.get("path")))
            requirement_ids = _parse_requirement_ids(
                _get_cell(row, requirement_index)
                if requirement_index is not None
                else ""
            )
            if REQUIREMENT_ID_RE.fullmatch(task_id):
                requirement_rows[task_id] = {
                    "path": path_value or f"docs/requirements/{task_id}/",
                    "scope_kind": REQUIREMENT_SCOPE_DIRECTORY,
                }
                continue
            if MODULE_ID_RE.fullmatch(task_id):
                if requirement_ids:
                    module_requirement_ids[task_id] = requirement_ids
                continue
            if SUBTASK_ID_RE.fullmatch(task_id):
                if parent_index is not None:
                    parent_id = _get_cell(row, parent_index).strip()
                    if parent_id:
                        subtask_parent_ids[task_id] = parent_id
                if requirement_ids:
                    subtask_requirement_ids[task_id] = requirement_ids

    for subtask_id, subtask in subtasks.items():
        if subtask_id in subtask_requirement_ids:
            continue
        parent_module_id = subtask_parent_ids.get(str(subtask_id))
        if not parent_module_id:
            meta = subtask.get("meta")
            meta = meta if isinstance(meta, dict) else {}
            parent_module_id = str(meta.get("module_id") or "").strip()
        inherited_ids = module_requirement_ids.get(parent_module_id or "")
        if inherited_ids:
            subtask_requirement_ids[str(subtask_id)] = list(inherited_ids)

    for module_id in list(module_requirement_ids.keys()):
        if str(module_id) not in modules:
            module_requirement_ids.pop(module_id, None)
    for subtask_id in list(subtask_requirement_ids.keys()):
        if str(subtask_id) not in subtasks:
            subtask_requirement_ids.pop(subtask_id, None)

    return requirement_rows, module_requirement_ids, subtask_requirement_ids


def _collect_requirement_ids(
    module_requirement_ids: dict[str, list[str]],
    subtask_requirement_ids: dict[str, list[str]],
) -> set[str]:
    result: set[str] = set()
    for relation_map in (module_requirement_ids, subtask_requirement_ids):
        for requirement_ids in relation_map.values():
            for requirement_id in requirement_ids:
                if REQUIREMENT_ID_RE.fullmatch(str(requirement_id)):
                    result.add(str(requirement_id))
    return result


def _requirement_relations_ok(
    *,
    module_ids: list[str],
    task_ids: list[str],
    modules: dict[str, dict[str, object]],
    subtasks: dict[str, dict[str, object]],
) -> bool:
    allowed_modules = set(module_ids)
    allowed_tasks = set(task_ids)
    for task_id in task_ids:
        if task_id not in allowed_tasks:
            return False
        subtask = subtasks.get(task_id, {})
        if not isinstance(subtask, dict):
            return False
        meta = subtask.get("meta")
        meta = meta if isinstance(meta, dict) else {}
        module_id = str(meta.get("module_id") or "").strip()
        if module_id and module_id not in allowed_modules:
            return False
    for module_id in module_ids:
        if module_id not in modules:
            return False
    return True


def _find_all_markdown_tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    tables: list[tuple[list[str], list[list[str]]]] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines) - 1:
        header_line = lines[index].strip()
        separator_line = lines[index + 1].strip()
        if not (header_line.startswith("|") and MARKDOWN_TABLE_SEPARATOR_RE.fullmatch(separator_line)):
            index += 1
            continue
        headers = _split_markdown_row(header_line)
        rows: list[list[str]] = []
        index += 2
        while index < len(lines):
            row_line = lines[index].strip()
            if not row_line.startswith("|") or MARKDOWN_TABLE_SEPARATOR_RE.fullmatch(row_line):
                break
            rows.append(_split_markdown_row(row_line))
            index += 1
        tables.append((headers, rows))
    return tables


def _split_markdown_row(line: str) -> list[str]:
    parts = [part.strip() for part in line.strip().strip("|").split("|")]
    return [part for part in parts]


def _build_task_index_header_index(headers: list[str]) -> dict[str, int]:
    header_index: dict[str, int] = {}
    for index, raw in enumerate(headers):
        norm = _normalize_header(raw)
        lowered = raw.strip().lower()
        if "taskid" in norm or norm in {"taskid", "task_id", "task"} or "task id" in lowered:
            header_index.setdefault("task_id", index)
        if "parent" in lowered or "上级任务" in raw or "父任务" in raw:
            header_index.setdefault("parent", index)
        if "path" in lowered or "对应文档路径" in raw:
            header_index.setdefault("path", index)
        if any(token in norm for token in REQUIREMENT_HEADER_TOKENS):
            header_index.setdefault("requirement_id", index)

    if "task_id" not in header_index and len(headers) > 0:
        header_index["task_id"] = 0
    if "path" not in header_index and len(headers) > 1:
        header_index["path"] = len(headers) - 1
    if "parent" not in header_index and len(headers) > 2:
        header_index["parent"] = 2
    return header_index


def _normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.strip().lower())


def _get_cell(row: list[str], index: int | None) -> str:
    if index is None or index < 0 or index >= len(row):
        return ""
    return row[index]


def _clean_doc_path(value: str) -> str:
    text = str(value or "").strip()
    if text.startswith("`") and text.endswith("`") and len(text) >= 2:
        text = text[1:-1]
    return text.strip()


def _parse_requirement_ids(value: str) -> list[str]:
    if not isinstance(value, str):
        return []
    normalized = value.strip()
    if normalized in {"", "-"}:
        return []
    normalized = re.sub(r"[，、;/]+", " ", normalized)
    normalized = normalized.replace(",", " ")
    result: list[str] = []
    seen: set[str] = set()
    for token in [item.strip() for item in normalized.split() if item.strip()]:
        if not REQUIREMENT_ID_RE.fullmatch(token) or token in seen:
            continue
        seen.add(token)
        result.append(token)
    return result
