from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .language_check import check_markdown_language
from .template_detection import detect_template_signals


MARKDOWN_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*$")
HEADING_NUMBER_RE = re.compile(r"^\d+(?:\.\d+)*\s*[\.\u3001]?\s*")
LIST_PREFIX_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
OLD_STATUS_RE = re.compile(
    r"(draft\s*/\s*reviewable\s*/\s*(?:downstream-ready|implementation-ready)\s*/\s*blocked)"
    r"|(?:当前状态\s*[:：].*(?:draft|reviewable|downstream-ready|implementation-ready|blocked))",
    re.IGNORECASE,
)
STEP_HEADING_RE = re.compile(r"^\s{0,3}#{2,6}\s+step\s+\d+\b", re.IGNORECASE | re.MULTILINE)

IMPLEMENTATION_DOC_REFS = {
    "doc:implementation_doc",
    "gate:implementation_scope_unclear",
    "gate:required_tests_missing",
    "gate:acceptance_criteria_missing",
}
DESIGN_DOC_REFS = {"doc:design_doc"}
LANGUAGE_REF_PREFIX = "policy:language_non_compliant"


def build_task_remediation_plan(
    *,
    state_path: str | Path,
    evaluate_payload: dict[str, Any],
    entity_id: str | None = None,
) -> dict[str, Any]:
    state_path = Path(state_path)
    state = _load_state(state_path)
    repo_root = _resolve_repo_root(state_path)

    subtasks = _as_dict(state.get("subtasks"))
    evaluate_subtasks = _as_dict(evaluate_payload.get("subtasks"))
    evaluate_modules = _as_dict(evaluate_payload.get("modules"))

    selected_task_ids, selected_scope = _select_task_ids(state=state, entity_id=entity_id)
    if not selected_task_ids:
        raise ValueError("no subtasks available for remediation planning")

    module_blockers_by_module: dict[str, list[str]] = {}
    for module_id, module_entry in evaluate_modules.items():
        derived = _as_dict(_as_dict(module_entry).get("derived"))
        module_blockers_by_module[str(module_id)] = _as_string_list(derived.get("blocker_refs"))

    task_records: list[dict[str, Any]] = []
    for task_id in selected_task_ids:
        state_task = _as_dict(subtasks.get(task_id))
        task_records.append(
            _build_task_record(
                task_id=task_id,
                state_task=state_task,
                evaluate_task=_as_dict(evaluate_subtasks.get(task_id)),
                module_blockers_by_module=module_blockers_by_module,
                repo_root=repo_root,
            )
        )

    document_findings = [
        {
            "task_id": record["task_id"],
            "module_id": record["module_id"],
            "design_doc": record["design_doc"],
            "implementation_doc": record["implementation_doc"],
        }
        for record in task_records
    ]
    migration_actions = [
        {
            "task_id": record["task_id"],
            "module_id": record["module_id"],
            "ordered_actions": record["migration_actions"],
        }
        for record in task_records
    ]
    carry_over_candidates = [
        {
            "task_id": record["task_id"],
            "module_id": record["module_id"],
            "fields": record["carry_over_fields"],
            "field_sources": record["carry_over_sources"],
            "notes": record["carry_over_notes"],
        }
        for record in task_records
        if record["carry_over_fields"]
    ]
    manual_fill_required = [
        {
            "task_id": record["task_id"],
            "module_id": record["module_id"],
            "fields": record["manual_fill_fields"],
            "reason": record["manual_fill_reason"],
        }
        for record in task_records
        if record["manual_fill_fields"]
    ]
    blocking_issues = [
        {
            "task_id": record["task_id"],
            "module_id": record["module_id"],
            "task_doc_blockers": record["task_doc_blockers"],
            "module_inherited_blockers": record["module_inherited_blockers"],
            "other_blockers": record["other_blockers"],
            "needs_manual_confirmation": bool(
                record["module_inherited_blockers"] or record["other_blockers"]
            ),
        }
        for record in task_records
    ]

    sample_tasks = _build_sample_tasks(task_records)
    recommended_order = _build_recommended_order(task_records)
    confidence = _build_confidence(task_records)
    needs_manual_confirmation = _build_manual_confirmation_items(task_records)
    reasoning_notes = _build_reasoning_notes(task_records)

    return {
        "summary": _build_summary(
            task_records=task_records,
            selected_scope=selected_scope,
            entity_id=entity_id,
        ),
        "document_findings": document_findings,
        "migration_actions": migration_actions,
        "manual_fill_required": manual_fill_required,
        "carry_over_candidates": carry_over_candidates,
        "blocking_issues": blocking_issues,
        "sample_tasks": sample_tasks,
        "recommended_order": recommended_order,
        "confidence": confidence,
        "needs_manual_confirmation": needs_manual_confirmation,
        "reasoning_notes": reasoning_notes,
    }


def render_task_remediation_markdown(payload: dict[str, Any]) -> str:
    summary = _as_dict(payload.get("summary"))
    lines = [
        "# 任务文档整改规划",
        "",
        "## 摘要",
        f"- 选择范围: {summary.get('selected_scope', '')}",
        f"- 目标实体: {summary.get('selected_entity_id', '')}",
        f"- 纳入分析 task 数量: {summary.get('selected_task_count', 0)}",
        f"- implementation 文档待迁移数量: {summary.get('implementation_template_task_count', 0)}",
        f"- design 文档待启用数量: {summary.get('design_template_task_count', 0)}",
        f"- 需要人工补字段的 task 数量: {summary.get('manual_fill_task_count', 0)}",
        f"- 含模块继承 blocker 的 task 数量: {summary.get('module_inherited_task_count', 0)}",
        "",
        "## 主建议顺序",
    ]
    for item in _as_list_of_dicts(payload.get("recommended_order")):
        lines.append(f"- {item.get('step', '?')}. {item.get('title', '')}: {item.get('reason', '')}")

    lines.extend(["", "## 推荐样本 task"])
    for item in _as_list_of_dicts(payload.get("sample_tasks")):
        lines.append(
            f"- {item.get('example_kind', '')}: {item.get('task_id', '')} | {item.get('reason', '')}"
        )

    lines.extend(["", "## 需要人工补充的字段"])
    for item in _as_list_of_dicts(payload.get("manual_fill_required")):
        fields = ", ".join(_as_string_list(item.get("fields")))
        lines.append(f"- {item.get('task_id', '')}: {fields} | {item.get('reason', '')}")

    lines.extend(["", "## 可迁移内容"])
    for item in _as_list_of_dicts(payload.get("carry_over_candidates")):
        fields = ", ".join(_as_string_list(item.get("fields")))
        lines.append(f"- {item.get('task_id', '')}: {fields}")

    lines.extend(["", "## 阻断说明"])
    for item in _as_list_of_dicts(payload.get("blocking_issues")):
        blockers = ", ".join(_as_string_list(item.get("task_doc_blockers")))
        inherited = ", ".join(_as_string_list(item.get("module_inherited_blockers")))
        other = ", ".join(_as_string_list(item.get("other_blockers")))
        lines.append(
            f"- {item.get('task_id', '')}: task 文档={blockers or '无'} | "
            f"模块继承={inherited or '无'} | 其他={other or '无'}"
        )

    manual_items = _as_list_of_dicts(payload.get("needs_manual_confirmation"))
    if manual_items:
        lines.extend(["", "## 需要人工确认"])
        for item in manual_items:
            lines.append(f"- {item.get('title', '')}: {item.get('reason', '')}")

    notes = payload.get("reasoning_notes")
    note_items = notes if isinstance(notes, list) else []
    if note_items:
        lines.extend(["", "## 说明"])
        for note in note_items:
            text = str(note).strip()
            if text:
                lines.append(f"- {text}")

    return "\n".join(lines) + "\n"


def write_task_remediation_output(
    *,
    payload: dict[str, Any],
    output_path: str | Path,
    output_format: str,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "markdown":
        path.write_text(render_task_remediation_markdown(payload), encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _build_task_record(
    *,
    task_id: str,
    state_task: dict[str, Any],
    evaluate_task: dict[str, Any],
    module_blockers_by_module: dict[str, list[str]],
    repo_root: Path,
) -> dict[str, Any]:
    meta = _as_dict(state_task.get("meta"))
    facts = _as_dict(state_task.get("facts"))
    module_id = str(meta.get("module_id", "")).strip()
    task_root = str(meta.get("path", "")).strip()
    blocker_refs = _as_string_list(_as_dict(evaluate_task.get("derived")).get("blocker_refs"))
    module_blockers = _as_string_list(module_blockers_by_module.get(module_id))

    design_relative_path = _join_relative_path(task_root, "SUBTASK_DESIGN.md")
    implementation_relative_path = _join_relative_path(task_root, "SUBTASK_IMPLEMENTATION.md")
    design_text = _read_text_if_exists(repo_root / design_relative_path)
    implementation_text = _read_text_if_exists(repo_root / implementation_relative_path)

    design_doc = _inspect_doc(
        relative_path=design_relative_path,
        text=design_text,
        state_doc=_as_dict(facts.get("design_doc")),
        doc_kind="design",
    )
    implementation_doc = _inspect_doc(
        relative_path=implementation_relative_path,
        text=implementation_text,
        state_doc=_as_dict(facts.get("implementation_doc")),
        doc_kind="implementation",
    )

    carry_over_fields: list[str] = []
    carry_over_sources: dict[str, str] = {}
    carry_over_notes: list[str] = []

    implementation_fields = _as_dict(implementation_doc.get("extracted_fields"))
    design_fields = _as_dict(design_doc.get("extracted_fields"))
    for field_name in (
        "goal",
        "allowed_modify_paths",
        "required_tests",
        "acceptance_criteria",
        "forbidden_paths",
    ):
        values = _as_string_list(implementation_fields.get(field_name))
        if values:
            carry_over_fields.append(field_name)
            carry_over_sources[field_name] = "implementation_doc"
            continue
        design_values = _as_string_list(design_fields.get(field_name))
        if design_values:
            carry_over_fields.append(field_name)
            carry_over_sources[field_name] = "design_doc"
    if "goal" in carry_over_sources and carry_over_sources["goal"] == "design_doc":
        carry_over_notes.append("当前 goal 主要来自 design 文档，迁移到 implementation 文档前仍需人工确认")
    if implementation_doc.get("old_status_semantics") or design_doc.get("old_status_semantics"):
        carry_over_notes.append("旧状态语义行不能直接沿用为当前正文真值")

    manual_fill_fields: list[str] = []
    if not _field_present(implementation_fields, "allowed_modify_paths") or (
        "gate:implementation_scope_unclear" in blocker_refs
    ):
        manual_fill_fields.append("allowed_modify_paths")
    if not _field_present(implementation_fields, "required_tests") or (
        "gate:required_tests_missing" in blocker_refs
    ):
        manual_fill_fields.append("required_tests")
    if not _field_present(implementation_fields, "acceptance_criteria") or (
        "gate:acceptance_criteria_missing" in blocker_refs
    ):
        manual_fill_fields.append("acceptance_criteria")
    if design_doc["template_like"] or "doc:design_doc" in blocker_refs:
        manual_fill_fields.append("design_key_sections")
    manual_fill_fields = _dedupe_strings(manual_fill_fields)

    module_inherited_blockers = _dedupe_strings(
        [
            ref
            for ref in blocker_refs
            if ref.startswith("module:") or ref in module_blockers
        ]
    )
    task_doc_blockers = _dedupe_strings(
        [
            ref
            for ref in blocker_refs
            if ref not in module_inherited_blockers
            and (
                ref in IMPLEMENTATION_DOC_REFS
                or ref in DESIGN_DOC_REFS
                or ref.startswith(LANGUAGE_REF_PREFIX)
            )
        ]
    )
    other_blockers = _dedupe_strings(
        [
            ref
            for ref in blocker_refs
            if ref not in module_inherited_blockers and ref not in task_doc_blockers
        ]
    )

    return {
        "task_id": task_id,
        "module_id": module_id,
        "design_doc": design_doc,
        "implementation_doc": implementation_doc,
        "carry_over_fields": _dedupe_strings(carry_over_fields),
        "carry_over_sources": carry_over_sources,
        "carry_over_notes": carry_over_notes,
        "manual_fill_fields": manual_fill_fields,
        "manual_fill_reason": _build_manual_fill_reason(manual_fill_fields),
        "task_doc_blockers": task_doc_blockers,
        "module_inherited_blockers": module_inherited_blockers,
        "other_blockers": other_blockers,
        "migration_actions": _build_task_migration_actions(
            design_doc=design_doc,
            implementation_doc=implementation_doc,
            manual_fill_fields=manual_fill_fields,
            module_inherited_blockers=module_inherited_blockers,
        ),
    }


def _inspect_doc(
    *,
    relative_path: str,
    text: str,
    state_doc: dict[str, Any],
    doc_kind: str,
) -> dict[str, Any]:
    state_template_like = bool(state_doc.get("template_like", False))
    template_like = state_template_like
    template_signals: list[dict[str, Any]] = []
    if text.strip():
        detected_template_like, template_signals = detect_template_signals(
            path=relative_path,
            text=text,
            doc_kind="subtask_implementation" if doc_kind == "implementation" else "subtask_design",
        )
        template_like = template_like or detected_template_like

    language_diagnostics = []
    if text.strip():
        language_diagnostics = [
            _diagnostic_to_dict(item)
            for item in check_markdown_language(path=relative_path, text=text)
        ]

    old_status_semantics = bool(OLD_STATUS_RE.search(text))
    legacy_step_markers = len(STEP_HEADING_RE.findall(text))
    template_like = template_like or old_status_semantics

    sections = _parse_markdown_sections(text)
    extracted_fields: dict[str, list[str]] = {
        "goal": _extract_from_sections(sections, "goal"),
        "allowed_modify_paths": _extract_from_sections(sections, "allowed_modify_paths"),
        "forbidden_paths": _extract_from_sections(sections, "forbidden_paths"),
        "required_tests": _extract_from_sections(sections, "required_tests"),
        "acceptance_criteria": _extract_from_sections(sections, "acceptance_criteria"),
    }

    structure_gaps: list[str] = []
    if doc_kind == "implementation":
        if not extracted_fields["allowed_modify_paths"]:
            structure_gaps.append("missing_allowed_modify_paths")
        if not extracted_fields["required_tests"]:
            structure_gaps.append("missing_required_tests")
        if not extracted_fields["acceptance_criteria"]:
            structure_gaps.append("missing_acceptance_criteria")
    else:
        if not _extract_from_sections(sections, "goal"):
            structure_gaps.append("missing_design_goal")
        if not _extract_from_sections(sections, "technical_solution"):
            structure_gaps.append("missing_technical_solution")

    return {
        "path": relative_path,
        "exists": bool(text.strip()) or bool(state_doc.get("exists", False)),
        "template_like": template_like,
        "template_signal_count": len(template_signals),
        "template_signals": template_signals,
        "language_violation_count": len(language_diagnostics),
        "language_violations": language_diagnostics,
        "old_status_semantics": old_status_semantics,
        "legacy_step_marker_count": legacy_step_markers,
        "extracted_fields": extracted_fields,
        "structure_gaps": structure_gaps,
    }


def _build_task_migration_actions(
    *,
    design_doc: dict[str, Any],
    implementation_doc: dict[str, Any],
    manual_fill_fields: list[str],
    module_inherited_blockers: list[str],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    step = 1

    if (
        implementation_doc["template_like"]
        or design_doc["template_like"]
        or implementation_doc["language_violation_count"] > 0
        or design_doc["language_violation_count"] > 0
    ):
        actions.append(
            {
                "step": step,
                "title": "先修标题、章节结构与中文规则",
                "reason": "当前文档仍带有旧模板痕迹、英文标题或英文正文主导问题",
            }
        )
        step += 1

    if implementation_doc["old_status_semantics"] or design_doc["old_status_semantics"]:
        actions.append(
            {
                "step": step,
                "title": "清理旧状态语义",
                "reason": "draft / reviewable / downstream-ready / implementation-ready 等旧口径不应继续作为正文真值",
            }
        )
        step += 1

    ordered_manual_fields = [
        ("allowed_modify_paths", "补允许修改范围"),
        ("required_tests", "补测试要求"),
        ("acceptance_criteria", "补完成判定"),
        ("design_key_sections", "补设计文档关键段落"),
    ]
    for field_name, title in ordered_manual_fields:
        if field_name in manual_fill_fields:
            actions.append(
                {
                    "step": step,
                    "title": title,
                    "reason": _manual_field_reason(field_name),
                }
            )
            step += 1

    if module_inherited_blockers:
        actions.append(
            {
                "step": step,
                "title": "将模块继承 blocker 保留在模块层处理",
                "reason": "这些问题不是 task 文档局部整改即可消除，不应误归为 task 自身缺陷",
            }
        )

    if not actions:
        actions.append(
            {
                "step": 1,
                "title": "当前文档结构已可读",
                "reason": "本规划未发现需要优先迁移的结构缺口，可转入其他阻断项判断",
            }
        )
    return actions


def _build_summary(
    *,
    task_records: list[dict[str, Any]],
    selected_scope: str,
    entity_id: str | None,
) -> dict[str, Any]:
    return {
        "selected_entity_id": entity_id or "ALL",
        "selected_scope": selected_scope,
        "selected_task_count": len(task_records),
        "implementation_template_task_count": sum(
            1 for item in task_records if bool(item["implementation_doc"]["template_like"])
        ),
        "design_template_task_count": sum(
            1 for item in task_records if bool(item["design_doc"]["template_like"])
        ),
        "language_issue_task_count": sum(
            1
            for item in task_records
            if (
                int(item["design_doc"]["language_violation_count"]) > 0
                or int(item["implementation_doc"]["language_violation_count"]) > 0
            )
        ),
        "manual_fill_task_count": sum(1 for item in task_records if item["manual_fill_fields"]),
        "module_inherited_task_count": sum(
            1 for item in task_records if item["module_inherited_blockers"]
        ),
    }


def _build_recommended_order(task_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = {
        "structure": 0,
        "old_status": 0,
        "allowed_modify_paths": 0,
        "required_tests": 0,
        "acceptance_criteria": 0,
        "design_key_sections": 0,
        "module_inherited": 0,
    }
    for item in task_records:
        if (
            item["implementation_doc"]["template_like"]
            or item["design_doc"]["template_like"]
            or item["implementation_doc"]["language_violation_count"] > 0
            or item["design_doc"]["language_violation_count"] > 0
        ):
            counts["structure"] += 1
        if item["implementation_doc"]["old_status_semantics"] or item["design_doc"]["old_status_semantics"]:
            counts["old_status"] += 1
        for field_name in item["manual_fill_fields"]:
            if field_name in counts:
                counts[field_name] += 1
        if item["module_inherited_blockers"]:
            counts["module_inherited"] += 1

    order_specs = [
        ("structure", "先修标题/章节结构与中文规则", "旧模板和英文标题问题会放大后续字段缺口"),
        ("old_status", "再清理旧状态语义", "避免正文继续用旧状态口径冒充当前 gate 真值"),
        ("allowed_modify_paths", "补允许修改范围", "这是 implementation scope 最小必需字段"),
        ("required_tests", "补测试要求", "这是进入 implementation_ready 的硬门槛之一"),
        ("acceptance_criteria", "补完成判定", "没有 acceptance criteria 就无法形成收口标准"),
        ("design_key_sections", "必要时再补设计文档关键段落", "design 文档只在仍为模板或缺关键段落时补"),
        ("module_inherited", "把模块继承 blocker 留在模块层处理", "不要把模块级缺口误记为 task 文档局部问题"),
    ]
    recommended_order: list[dict[str, Any]] = []
    step = 1
    for key, title, reason in order_specs:
        if counts[key] <= 0:
            continue
        recommended_order.append(
            {
                "step": step,
                "title": title,
                "reason": f"{reason}，当前影响 {counts[key]} 个 task",
            }
        )
        step += 1
    if not recommended_order:
        recommended_order.append(
            {
                "step": 1,
                "title": "当前无需新增整改顺序",
                "reason": "所选 task 没有暴露出明显的 task 文档结构缺口",
            }
        )
    return recommended_order


def _build_sample_tasks(task_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []

    old_template_candidates = sorted(
        task_records,
        key=lambda item: (
            not item["implementation_doc"]["old_status_semantics"],
            not item["implementation_doc"]["template_like"],
            item["implementation_doc"]["language_violation_count"]
            + item["design_doc"]["language_violation_count"],
            item["task_id"],
        ),
    )
    if old_template_candidates:
        item = old_template_candidates[0]
        samples.append(
            _make_sample_task(
                example_kind="old_template_case",
                task=item,
                reason="implementation 文档仍带旧状态语义、旧模板结构或英文标题问题，适合作为迁移基线样本",
            )
        )

    pilot_candidates = [
        item
        for item in task_records
        if not item["module_inherited_blockers"]
    ]
    if pilot_candidates:
        pilot_candidates = sorted(
            pilot_candidates,
            key=lambda item: (
                item["design_doc"]["template_like"],
                item["implementation_doc"]["template_like"],
                len(item["manual_fill_fields"]),
                -len(item["carry_over_fields"]),
                len(item["task_doc_blockers"]),
                item["task_id"],
            ),
        )
        item = pilot_candidates[0]
        samples.append(
            _make_sample_task(
                example_kind="pilot_candidate",
                task=item,
                reason="自身文档缺口相对更少，且没有额外模块继承 blocker，更适合作为首批打样对象",
            )
        )

    module_candidates = [item for item in task_records if item["module_inherited_blockers"]]
    if module_candidates:
        module_candidates = sorted(
            module_candidates,
            key=lambda item: (
                -len(item["module_inherited_blockers"]),
                len(item["task_doc_blockers"]),
                item["task_id"],
            ),
        )
        item = module_candidates[0]
        samples.append(
            _make_sample_task(
                example_kind="module_inherited_case",
                task=item,
                reason="它的部分问题来自模块继承 blocker，不应把所有缺口都归结为 task 文档本身",
            )
        )

    return samples


def _make_sample_task(*, example_kind: str, task: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "example_kind": example_kind,
        "task_id": task["task_id"],
        "module_id": task["module_id"],
        "reason": reason,
        "local_doc_issues": task["task_doc_blockers"],
        "module_inherited_blockers": task["module_inherited_blockers"],
    }


def _build_confidence(task_records: list[dict[str, Any]]) -> dict[str, Any]:
    if not task_records:
        return {"level": "low", "score": 0.1}
    readable_count = sum(
        1
        for item in task_records
        if item["design_doc"]["exists"] or item["implementation_doc"]["exists"]
    )
    score = 0.4 + 0.4 * (readable_count / len(task_records))
    if any(item["module_inherited_blockers"] for item in task_records):
        score -= 0.06
    if any(item["manual_fill_fields"] for item in task_records):
        score -= 0.04
    score = max(0.2, min(0.92, round(score, 2)))
    if score >= 0.8:
        level = "high"
    elif score >= 0.55:
        level = "medium"
    else:
        level = "low"
    return {"level": level, "score": score}


def _build_manual_confirmation_items(task_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    field_to_title = {
        "allowed_modify_paths": "允许修改范围仍需人工补充",
        "required_tests": "测试要求仍需人工补充",
        "acceptance_criteria": "完成判定仍需人工补充",
        "design_key_sections": "部分 design 文档仍需人工补关键段落",
    }
    for field_name, title in field_to_title.items():
        affected = [item["task_id"] for item in task_records if field_name in item["manual_fill_fields"]]
        if affected:
            items.append(
                {
                    "title": title,
                    "reason": f"{', '.join(affected[:8])} 当前缺少该字段，无法仅靠旧文档直接迁移",
                }
            )

    inherited = [item["task_id"] for item in task_records if item["module_inherited_blockers"]]
    if inherited:
        items.append(
            {
                "title": "模块继承 blocker 需保留在模块层确认",
                "reason": f"{', '.join(inherited[:8])} 仍受模块级文档或契约缺口影响，task 文档整改不能单独消除这些 blocker",
            }
        )

    english_carry = [
        item["task_id"]
        for item in task_records
        if (
            int(item["design_doc"]["language_violation_count"]) > 0
            or int(item["implementation_doc"]["language_violation_count"]) > 0
        )
        and item["carry_over_fields"]
    ]
    if english_carry:
        items.append(
            {
                "title": "旧英文内容可迁移但仍需人工确认",
                "reason": f"{', '.join(english_carry[:8])} 存在可迁移内容，但标题和术语仍应先回到中文主结构",
            }
        )
    return items


def _build_reasoning_notes(task_records: list[dict[str, Any]]) -> list[str]:
    notes = [
        "本规划器是只读解释器，只输出整改顺序与证据，不修改真实文档，也不写回 state。",
        "允许修改范围、测试要求、完成判定目前都按最小非空结构判断，不做更强的语义理解。",
    ]
    if any(item["module_inherited_blockers"] for item in task_records):
        notes.append("若某 task 同时含有模块继承 blocker，应把模块问题和 task 文档问题拆开解释。")
    if any(item["implementation_doc"]["old_status_semantics"] for item in task_records):
        notes.append("旧状态语义只能视为待清理文本噪音，不能继续当作当前 readiness 真值。")
    return notes


def _build_manual_fill_reason(fields: list[str]) -> str:
    if not fields:
        return "当前未发现必须人工补充的 task 文档字段"
    field_labels = {
        "allowed_modify_paths": "允许修改范围",
        "required_tests": "测试要求",
        "acceptance_criteria": "完成判定",
        "design_key_sections": "design 文档关键段落",
    }
    labels = [field_labels.get(item, item) for item in fields]
    return "、".join(labels) + " 目前仍需人工补充，不能仅靠旧文档自动迁移"


def _manual_field_reason(field_name: str) -> str:
    mapping = {
        "allowed_modify_paths": "当前 implementation 文档无法明确允许修改范围",
        "required_tests": "当前 implementation 文档没有给出可执行测试要求",
        "acceptance_criteria": "当前 implementation 文档没有给出最小完成判定",
        "design_key_sections": "当前 design 文档仍是模板或缺关键段落",
    }
    return mapping.get(field_name, "当前字段仍需人工补充")


def _field_present(fields: dict[str, Any], field_name: str) -> bool:
    return bool(_as_string_list(fields.get(field_name)))


def _extract_from_sections(sections: dict[str, list[str]], field_name: str) -> list[str]:
    aliases = {
        "goal": ("本轮实施目标", "子任务目标", "goal", "task goal"),
        "allowed_modify_paths": ("允许修改", "允许修改范围", "allowed changes", "allowed change", "allowed paths", "allowed modify paths"),
        "forbidden_paths": ("禁止修改", "forbidden paths", "forbidden changes"),
        "required_tests": (
            "自动化验证",
            "手动验证",
            "测试与验证",
            "tests",
            "test plan",
            "automated tests",
            "manual tests",
        ),
        "acceptance_criteria": ("完成判定", "acceptance", "acceptance criteria", "done criteria"),
        "technical_solution": ("技术方案", "实现方案", "方案", "solution", "technical approach"),
    }.get(field_name, ())
    collected: list[str] = []
    for alias in aliases:
        collected.extend(_extract_section_items(sections.get(_normalize_heading_key(alias), [])))
    return _dedupe_strings(collected)


def _parse_markdown_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current_key: str | None = None
    for line in text.splitlines():
        match = MARKDOWN_HEADING_RE.match(line)
        if match:
            current_key = _normalize_heading_key(match.group(1))
            sections.setdefault(current_key, [])
            continue
        if current_key is not None:
            sections[current_key].append(line)
    return sections


def _normalize_heading_key(value: str) -> str:
    normalized = HEADING_NUMBER_RE.sub("", value.strip())
    return normalized.strip().strip(":：").casefold()


def _extract_section_items(lines: list[str]) -> list[str]:
    items: list[str] = []
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("|"):
            continue
        normalized = LIST_PREFIX_RE.sub("", stripped).strip()
        if not normalized:
            continue
        code_spans = [item.strip() for item in INLINE_CODE_RE.findall(normalized) if item.strip()]
        if code_spans:
            items.extend(code_spans)
            continue
        if "：" in normalized:
            normalized = normalized.split("：", 1)[1].strip()
        elif ":" in normalized:
            normalized = normalized.split(":", 1)[1].strip()
        if normalized:
            items.append(normalized)
    return _dedupe_strings(items)


def _resolve_repo_root(state_path: Path) -> Path:
    normalized = state_path.resolve()
    try:
        if normalized.parent.name == "governance" and normalized.parent.parent.name == "docs":
            return normalized.parent.parent.parent
    except IndexError:
        pass
    return normalized.parent


def _select_task_ids(
    *,
    state: dict[str, Any],
    entity_id: str | None,
) -> tuple[list[str], str]:
    subtasks = _as_dict(state.get("subtasks"))
    modules = _as_dict(state.get("modules"))
    requirements = _as_dict(state.get("requirements"))

    if not entity_id:
        return sorted(subtasks.keys()), "all_tasks"

    if entity_id in subtasks:
        return [entity_id], "task"

    if entity_id in modules:
        task_ids = []
        for task_id, subtask in subtasks.items():
            meta = _as_dict(_as_dict(subtask).get("meta"))
            if str(meta.get("module_id", "")).strip() == entity_id:
                task_ids.append(task_id)
        if not task_ids:
            raise ValueError(f"module has no subtasks for remediation planning: {entity_id}")
        return sorted(task_ids), "module"

    if entity_id in requirements:
        requirement = _as_dict(requirements.get(entity_id))
        facts = _as_dict(requirement.get("facts"))
        task_ids = [task_id for task_id in _as_string_list(facts.get("task_ids")) if task_id in subtasks]
        if not task_ids:
            raise ValueError(f"requirement has no subtasks for remediation planning: {entity_id}")
        return sorted(task_ids), "requirement"

    raise ValueError(f"entity-id not found: {entity_id}")


def _join_relative_path(base_path: str, filename: str) -> str:
    return (Path(base_path) / filename).as_posix()


def _read_text_if_exists(path: Path) -> str:
    try:
        if path.exists() and path.is_file():
            return path.read_text(encoding="utf-8")
    except OSError:
        return ""
    return ""


def _load_state(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - environment guard
        raise ValueError(f"PyYAML is required to load state file: {exc}") from exc

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"state file not found: {path}") from exc
    if not isinstance(raw, dict):
        raise ValueError("state file must contain a mapping")
    return raw


def _diagnostic_to_dict(diagnostic: Any) -> dict[str, Any]:
    evidence = getattr(diagnostic, "evidence", [])
    return {
        "code": getattr(diagnostic, "code", ""),
        "severity": getattr(diagnostic, "severity", ""),
        "entity_type": getattr(diagnostic, "entity_type", ""),
        "entity_id": getattr(diagnostic, "entity_id", ""),
        "field_path": getattr(diagnostic, "field_path", ""),
        "message": getattr(diagnostic, "message", ""),
        "evidence": [
            {
                "type": getattr(item, "type", ""),
                "path": getattr(item, "path", ""),
                "ref": getattr(item, "ref", ""),
                "value": getattr(item, "value", None),
                "line": getattr(item, "line", None),
                "snippet": getattr(item, "snippet", None),
            }
            for item in evidence
        ],
    }


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
