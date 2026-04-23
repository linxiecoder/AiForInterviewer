from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .task_readiness_preview import (
    DESIGN_CHINESE_HEADINGS,
    IMPLEMENTATION_CHINESE_HEADINGS,
    build_task_readiness_preview,
)


IMPLEMENTATION_SCOPE_HEADINGS = ["## 5. 允许修改范围", "### 5.1 允许修改", "### 5.2 禁止修改"]
IMPLEMENTATION_TEST_HEADINGS = ["## 7. 测试与验证", "### 7.1 自动化验证"]
IMPLEMENTATION_ACCEPTANCE_HEADINGS = ["## 8. 完成判定"]
DESIGN_MINIMAL_HEADINGS = ["## 3. 子任务目标", "## 5. 技术方案"]


def build_task_patch_preview(
    *,
    state_path: str | Path,
    evaluate_payload: dict[str, Any],
    entity_id: str | None = None,
) -> dict[str, Any]:
    state_path = Path(state_path)
    state = _load_state(state_path)
    preview = build_task_readiness_preview(
        state_path=state_path,
        evaluate_payload=evaluate_payload,
        entity_id=entity_id,
    )

    subtasks = _as_dict(state.get("subtasks"))
    requirements = _as_dict(state.get("requirements"))

    requirement_seed_patch_preview = _build_requirement_seed_patch_preview(
        preview=preview,
        requirements=requirements,
    )
    task_document_patch_previews = _build_task_document_patch_previews(
        preview=preview,
        subtasks=subtasks,
    )
    manual_confirmation_points = _build_manual_confirmation_points(
        preview=preview,
        requirement_seed_patch_preview=requirement_seed_patch_preview,
        task_document_patch_previews=task_document_patch_previews,
    )
    carry_over_candidates = _build_carry_over_candidates(task_document_patch_previews)
    manual_fill_required = _build_manual_fill_required(task_document_patch_previews)
    batch_preview = _build_batch_preview(
        preview=preview,
        task_document_patch_previews=task_document_patch_previews,
    )

    source_summary = _as_dict(preview.get("summary"))
    return {
        "summary": {
            "selected_entity_id": source_summary.get("selected_entity_id", entity_id or "ALL"),
            "selected_scope": source_summary.get("selected_scope", ""),
            "selected_task_count": int(source_summary.get("selected_task_count", 0)),
            "requirement_seed_patch_count": len(requirement_seed_patch_preview),
            "task_document_patch_count": len(task_document_patch_previews),
            "manual_confirmation_count": len(manual_confirmation_points),
            "deferred_task_count": len(_as_list_of_dicts(batch_preview.get("deferred_tasks"))),
        },
        "requirement_seed_patch_preview": requirement_seed_patch_preview,
        "task_document_patch_previews": task_document_patch_previews,
        "manual_confirmation_points": manual_confirmation_points,
        "carry_over_candidates": carry_over_candidates,
        "manual_fill_required": manual_fill_required,
        "batch_preview": batch_preview,
        "confidence": _as_dict(preview.get("confidence")),
        "reasoning_notes": _build_reasoning_notes(
            preview=preview,
            requirement_seed_patch_preview=requirement_seed_patch_preview,
            task_document_patch_previews=task_document_patch_previews,
            batch_preview=batch_preview,
        ),
    }


def render_task_patch_preview_markdown(payload: dict[str, Any]) -> str:
    summary = _as_dict(payload.get("summary"))
    lines = [
        "# 任务 patch 预览",
        "",
        "## 摘要",
        f"- 选择范围: {summary.get('selected_scope', '')}",
        f"- 目标实体: {summary.get('selected_entity_id', '')}",
        f"- 纳入分析 task 数量: {summary.get('selected_task_count', 0)}",
        f"- requirement seed patch 数量: {summary.get('requirement_seed_patch_count', 0)}",
        f"- task 文档 patch 数量: {summary.get('task_document_patch_count', 0)}",
        f"- 需要人工确认数量: {summary.get('manual_confirmation_count', 0)}",
        f"- 暂缓 task 数量: {summary.get('deferred_task_count', 0)}",
        "",
        "## requirement seed patch 预览",
    ]
    for item in _as_list_of_dicts(payload.get("requirement_seed_patch_preview")):
        lines.append(
            f"- {item.get('task_id', '')}: {item.get('target_path', '无目标路径')} | "
            f"建议 requirement={item.get('suggested_requirement_id', '') or '待确认'} | "
            f"需人工确认={bool(item.get('needs_manual_confirmation'))}"
        )

    lines.extend(["", "## task 文档 patch 预览"])
    for item in _as_list_of_dicts(payload.get("task_document_patch_previews")):
        lines.append(f"- {item.get('task_id', '')}: {item.get('reason', '')}")
        lines.append(f"  - 可迁移: {', '.join(_as_string_list(item.get('carry_over_fields'))) or '无'}")
        lines.append(f"  - 人工填写: {', '.join(_as_string_list(item.get('manual_fill_fields'))) or '无'}")

    lines.extend(["", "## 批次说明"])
    batch = _as_dict(payload.get("batch_preview"))
    lines.append(f"- 首批 task: {', '.join(_as_string_list(batch.get('task_ids'))) or '无'}")
    for reason in _as_string_list(batch.get("rationale")):
        lines.append(f"- {reason}")

    deferred_tasks = _as_list_of_dicts(batch.get("deferred_tasks"))
    if deferred_tasks:
        lines.extend(["", "## 暂缓对象"])
        for item in deferred_tasks:
            lines.append(f"- {item.get('task_id', '')}: {item.get('reason', '')}")

    manual_points = _as_list_of_dicts(payload.get("manual_confirmation_points"))
    if manual_points:
        lines.extend(["", "## 需要人工确认"])
        for item in manual_points:
            lines.append(f"- {item.get('title', '')}: {item.get('reason', '')}")

    notes = payload.get("reasoning_notes")
    if isinstance(notes, list) and notes:
        lines.extend(["", "## 说明"])
        for note in notes:
            text = str(note).strip()
            if text:
                lines.append(f"- {text}")
    return "\n".join(lines) + "\n"


def write_task_patch_preview_output(
    *,
    payload: dict[str, Any],
    output_path: str | Path,
    output_format: str,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "markdown":
        path.write_text(render_task_patch_preview_markdown(payload), encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _build_requirement_seed_patch_preview(
    *,
    preview: dict[str, Any],
    requirements: dict[str, Any],
) -> list[dict[str, Any]]:
    patches: list[dict[str, Any]] = []
    for item in _as_list_of_dicts(preview.get("requirement_seed_preview")):
        task_id = str(item.get("task_id", "")).strip()
        suggested_requirement_id = str(item.get("suggested_requirement_id") or "").strip()
        target_path = ""
        patch_preview: dict[str, Any] | None = None
        if suggested_requirement_id:
            target_path = f"requirements.{suggested_requirement_id}.facts.task_ids"
            patch_preview = {
                "op": "append_if_missing",
                "path": target_path,
                "value_preview": [task_id],
                "requirement_exists_in_state": suggested_requirement_id in requirements,
            }
        patches.append(
            {
                "task_id": task_id,
                "module_id": str(item.get("module_id", "")).strip(),
                "suggested_requirement_id": suggested_requirement_id or None,
                "candidate_requirement_ids": _as_string_list(item.get("candidate_requirement_ids")),
                "target_path": target_path or None,
                "patch_preview": patch_preview,
                "confidence": _as_dict(item.get("confidence")),
                "needs_manual_confirmation": bool(item.get("needs_manual_confirmation")),
                "reason": str(item.get("reason", "")).strip(),
            }
        )
    return patches


def _build_task_document_patch_previews(
    *,
    preview: dict[str, Any],
    subtasks: dict[str, Any],
) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    for item in _as_list_of_dicts(preview.get("candidate_task_previews")):
        task_id = str(item.get("task_id", "")).strip()
        state_task = _as_dict(subtasks.get(task_id))
        meta = _as_dict(state_task.get("meta"))
        task_root = str(meta.get("path", "")).strip()
        carry_over_fields = _as_string_list(item.get("carry_over_fields"))
        manual_fill_fields = _as_string_list(item.get("manual_fill_fields"))
        outputs.append(
            {
                "task_id": task_id,
                "module_id": str(item.get("module_id", "")).strip(),
                "reason": str(item.get("reason", "")).strip(),
                "suggested_requirement_id": item.get("suggested_requirement_id"),
                "cleanup_old_status_semantics": bool(item.get("cleanup_old_status_semantics")),
                "carry_over_fields": carry_over_fields,
                "carry_over_notes": _as_string_list(item.get("carry_over_notes")),
                "manual_fill_fields": manual_fill_fields,
                "module_level_blockers": _as_string_list(item.get("module_level_blockers")),
                "implementation_doc_patch_preview": _build_implementation_doc_patch_preview(
                    task_root=task_root,
                    carry_over_fields=carry_over_fields,
                    manual_fill_fields=manual_fill_fields,
                    cleanup_old_status_semantics=bool(item.get("cleanup_old_status_semantics")),
                    heading_replacements=_as_string_list(
                        _as_dict(item.get("heading_replacements")).get("implementation_doc")
                    ),
                ),
                "design_doc_patch_preview": _build_design_doc_patch_preview(
                    task_root=task_root,
                    manual_fill_fields=manual_fill_fields,
                    cleanup_old_status_semantics=bool(item.get("cleanup_old_status_semantics")),
                    heading_replacements=_as_string_list(
                        _as_dict(item.get("heading_replacements")).get("design_doc")
                    ),
                ),
                "minimal_change_skeleton": _as_list_of_dicts(item.get("minimal_change_skeleton")),
            }
        )
    return outputs


def _build_implementation_doc_patch_preview(
    *,
    task_root: str,
    carry_over_fields: list[str],
    manual_fill_fields: list[str],
    cleanup_old_status_semantics: bool,
    heading_replacements: list[str],
) -> dict[str, Any]:
    return {
        "enabled": True,
        "target_relative_path": _join_relative_path(task_root, "SUBTASK_IMPLEMENTATION.md"),
        "section_patch_preview": [
            {
                "section_key": "title",
                "action": "replace_heading" if heading_replacements else "keep_heading_if_already_compliant",
                "proposed_heading": IMPLEMENTATION_CHINESE_HEADINGS[0],
                "carry_over_fields": [],
                "manual_fill_fields": [],
                "notes": ["若当前仍是英文标题或旧模板标题，应切换到中文主标题。"],
            },
            {
                "section_key": "goal",
                "action": "ensure_section",
                "proposed_heading": IMPLEMENTATION_CHINESE_HEADINGS[1],
                "carry_over_fields": _filter_fields(carry_over_fields, {"goal"}),
                "manual_fill_fields": _filter_fields(manual_fill_fields, {"goal"}),
                "notes": ["可复用旧文档中已有的实施目标表述。"],
            },
            {
                "section_key": "scope",
                "action": "ensure_section",
                "proposed_heading": IMPLEMENTATION_SCOPE_HEADINGS[0],
                "subheadings": IMPLEMENTATION_SCOPE_HEADINGS[1:],
                "carry_over_fields": _filter_fields(carry_over_fields, {"allowed_modify_paths", "forbidden_paths"}),
                "manual_fill_fields": _filter_fields(manual_fill_fields, {"allowed_modify_paths"}),
                "notes": ["allowed_modify_paths 应放在 5.1，禁止修改范围应放在 5.2。"],
            },
            {
                "section_key": "tests",
                "action": "ensure_section",
                "proposed_heading": IMPLEMENTATION_TEST_HEADINGS[0],
                "subheadings": IMPLEMENTATION_TEST_HEADINGS[1:],
                "carry_over_fields": _filter_fields(carry_over_fields, {"required_tests"}),
                "manual_fill_fields": _filter_fields(manual_fill_fields, {"required_tests"}),
                "notes": ["required_tests 应落在自动化验证小节；若仅有占位语句，仍需人工补具体命令或验证方式。"],
            },
            {
                "section_key": "acceptance",
                "action": "ensure_section",
                "proposed_heading": IMPLEMENTATION_ACCEPTANCE_HEADINGS[0],
                "carry_over_fields": _filter_fields(carry_over_fields, {"acceptance_criteria"}),
                "manual_fill_fields": _filter_fields(manual_fill_fields, {"acceptance_criteria"}),
                "notes": ["acceptance_criteria 应单独落在完成判定章节。"],
            },
        ],
        "cleanup_old_status_semantics": cleanup_old_status_semantics,
    }


def _build_design_doc_patch_preview(
    *,
    task_root: str,
    manual_fill_fields: list[str],
    cleanup_old_status_semantics: bool,
    heading_replacements: list[str],
) -> dict[str, Any]:
    enabled = bool(heading_replacements) or "design_key_sections" in manual_fill_fields
    section_patch_preview: list[dict[str, Any]] = []
    if enabled:
        section_patch_preview.append(
            {
                "section_key": "title",
                "action": "replace_heading" if heading_replacements else "ensure_heading",
                "proposed_heading": DESIGN_CHINESE_HEADINGS[0],
                "manual_fill_fields": [],
                "notes": ["若 design doc 仍是旧模板或英文标题，应切换到中文主标题。"],
            }
        )
        for heading in DESIGN_MINIMAL_HEADINGS:
            section_patch_preview.append(
                {
                    "section_key": heading,
                    "action": "ensure_section",
                    "proposed_heading": heading,
                    "manual_fill_fields": ["design_key_sections"] if "design_key_sections" in manual_fill_fields else [],
                    "notes": ["至少补齐目标与技术方案两段，避免 design doc 继续停留在骨架态。"],
                }
            )
    return {
        "enabled": enabled,
        "target_relative_path": _join_relative_path(task_root, "SUBTASK_DESIGN.md"),
        "section_patch_preview": section_patch_preview,
        "cleanup_old_status_semantics": cleanup_old_status_semantics,
    }


def _build_manual_confirmation_points(
    *,
    preview: dict[str, Any],
    requirement_seed_patch_preview: list[dict[str, Any]],
    task_document_patch_previews: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    points = [
        {"title": item.get("title", ""), "reason": item.get("reason", "")}
        for item in _as_list_of_dicts(preview.get("manual_confirmation_points"))
        if item.get("title")
    ]
    for item in requirement_seed_patch_preview:
        if bool(item.get("needs_manual_confirmation")):
            points.append(
                {
                    "title": f"{item.get('task_id', '')} 的 requirement seed patch 仍需人工确认",
                    "reason": "当前只预览补关系的位置与内容，不会在 preview 层直接写回 requirement 真值。",
                }
            )
    for item in task_document_patch_previews:
        if _as_string_list(item.get("manual_fill_fields")):
            points.append(
                {
                    "title": f"{item.get('task_id', '')} 的 patch 仍有人工填写点",
                    "reason": "allowed_modify_paths / required_tests / acceptance_criteria 等内容仍需结合真实任务补正文。",
                }
            )
    return _dedupe_dict_items(points)


def _build_carry_over_candidates(task_document_patch_previews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "task_id": item.get("task_id", ""),
            "fields": _as_string_list(item.get("carry_over_fields")),
            "notes": _as_string_list(item.get("carry_over_notes")),
        }
        for item in task_document_patch_previews
        if _as_string_list(item.get("carry_over_fields"))
    ]


def _build_manual_fill_required(task_document_patch_previews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "task_id": item.get("task_id", ""),
            "fields": _as_string_list(item.get("manual_fill_fields")),
            "module_level_blockers": _as_string_list(item.get("module_level_blockers")),
        }
        for item in task_document_patch_previews
        if _as_string_list(item.get("manual_fill_fields"))
    ]


def _build_batch_preview(
    *,
    preview: dict[str, Any],
    task_document_patch_previews: list[dict[str, Any]],
) -> dict[str, Any]:
    batch = _as_dict(preview.get("batch_rationale"))
    summaries = []
    preview_map = {
        str(item.get("task_id", "")).strip(): item
        for item in task_document_patch_previews
        if item.get("task_id")
    }
    for task_id in _as_string_list(batch.get("task_ids")):
        item = _as_dict(preview_map.get(task_id))
        if not item:
            continue
        summaries.append(
            {
                "task_id": task_id,
                "reason": item.get("reason", ""),
                "manual_fill_fields": _as_string_list(item.get("manual_fill_fields")),
                "carry_over_fields": _as_string_list(item.get("carry_over_fields")),
            }
        )
    return {
        "task_ids": _as_string_list(batch.get("task_ids")),
        "rationale": _as_string_list(batch.get("reasons")),
        "why_this_batch": str(batch.get("why_this_batch", "")).strip(),
        "task_patch_summaries": summaries,
        "deferred_tasks": _as_list_of_dicts(preview.get("deferred_tasks")),
    }


def _build_reasoning_notes(
    *,
    preview: dict[str, Any],
    requirement_seed_patch_preview: list[dict[str, Any]],
    task_document_patch_previews: list[dict[str, Any]],
    batch_preview: dict[str, Any],
) -> list[str]:
    notes = [
        "本能力是 patch preview 层，只把现有 preview 结果整理成可审阅的变更草案，不写回 state，也不修改文档。",
        "requirement seed patch preview 仍然只是建议，不会把 suggested requirement 直接提升为正式真值。",
    ]
    if task_document_patch_previews:
        notes.append("task 文档 patch preview 只给出章节级骨架、可迁移内容和人工填写点，不会生成自动 patch。")
    if _as_list_of_dicts(batch_preview.get("deferred_tasks")):
        notes.append("deferred task 会继续保留在批次外，避免把模块层 blocker 错误地下沉到 task 文档局部修复。")
    notes.extend(
        str(item).strip()
        for item in preview.get("reasoning_notes", [])
        if str(item).strip()
    )
    if any(bool(item.get("needs_manual_confirmation")) for item in requirement_seed_patch_preview):
        notes.append("当前 requirement 映射仍带 needs_manual_confirmation，下一步若进入执行也应先做人审。")
    return _dedupe_strings(notes)


def _filter_fields(fields: list[str], allowed: set[str]) -> list[str]:
    return [field for field in fields if field in allowed]


def _join_relative_path(base_path: str, filename: str) -> str:
    return (Path(base_path) / filename).as_posix()


def _load_state(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - environment guard
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


def _as_list_of_dicts(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return _dedupe_strings([str(item).strip() for item in value if str(item).strip()])


def _dedupe_strings(items: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        ordered.append(text)
        seen.add(text)
    return ordered


def _dedupe_dict_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        title = str(item.get("title", "")).strip()
        reason = str(item.get("reason", "")).strip()
        key = (title, reason)
        if not title or key in seen:
            continue
        ordered.append({"title": title, "reason": reason})
        seen.add(key)
    return ordered
