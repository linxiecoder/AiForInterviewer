from __future__ import annotations

from pathlib import Path

from .naming_rules import (
    MODULE_ID_RE,
    REQUIREMENT_SCOPE_ROOT_CLUSTER,
    SUBTASK_ID_RE,
)
from .schema import make_default_compliance_state


REQUIREMENT_ROOT_ID = "RQ01"
REQUIREMENT_ASSET_SLOTS = {
    "plan_latest": "PLAN_LATEST.md",
    "module_index": "MODULE_INDEX.md",
    "task_index": "TASK_INDEX.md",
}


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

    should_emit = has_root_assets or bool(module_ids) or bool(task_ids)
    if not should_emit:
        return {
            "requirements": {},
            "diagnostics": diagnostics,
            "counts": {"requirement": 0},
        }

    compliance = make_default_compliance_state()
    compliance["naming_ok"] = True
    compliance["path_ok"] = True
    compliance["relations_ok"] = all(
        isinstance(subtask.get("meta"), dict)
        and str(subtask["meta"].get("module_id") or "").strip() in module_ids
        for subtask in subtasks.values()
    )

    requirements = {
        REQUIREMENT_ROOT_ID: {
            "meta": {
                "path": ".",
                "scope_kind": REQUIREMENT_SCOPE_ROOT_CLUSTER,
            },
            "facts": {
                "module_ids": module_ids,
                "task_ids": task_ids,
                "asset_slots": asset_slots,
                "compliance": compliance,
            },
        }
    }

    return {
        "requirements": requirements,
        "diagnostics": diagnostics,
        "counts": {"requirement": len(requirements)},
    }
