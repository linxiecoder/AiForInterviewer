from __future__ import annotations

from typing import Any

from .diagnostics import Diagnostic, make_diagnostic, make_evidence

RENDER_OUTPUT_DIR_NAME = "DOC_GOVERNOR_REPORT.md"

GATE_COUNT_KEYS = [
    "observe_only.clear",
    "observe_only.review_only",
    "candidate_gate.clear",
    "candidate_gate.review_only",
    "candidate_gate.candidate_blocker",
    "readiness_gate.clear",
    "readiness_gate.review_only",
    "readiness_gate.readiness_blocker",
]

REQUIREMENT_RELATION_CONSISTENCY_CODES = {
    "SCHEMA_REQUIREMENT_RELATION_ENTITY_MISSING": "entity_missing",
    "SCHEMA_REQUIREMENT_RELATION_CONTAINER_MISSING": "container_missing",
    "SCHEMA_REQUIREMENT_RELATION_CONTAINER_CONFLICT": "container_conflict",
    "SCHEMA_REQUIREMENT_RELATION_DRIFT": "drift",
    "SCHEMA_REQUIREMENT_RELATION_AMBIGUOUS": "ambiguous",
}


def render_from_payload(
    payload: dict[str, Any],
    *,
    render_input_invalid: bool,
    input_incomplete: bool,
    agenda_limit: int = 10,
) -> str:
    summary = _as_dict(payload.get("summary"))
    requirements = _as_dict(payload.get("requirements"))
    modules = _as_dict(payload.get("modules"))
    subtasks = _as_dict(payload.get("subtasks"))
    documents = _as_dict(payload.get("documents"))
    oqs = _as_dict(payload.get("oqs"))
    governance_rounds = _as_list(payload.get("governance_rounds"))
    delta_summary = _as_dict(payload.get("delta_summary"))
    diagnostics = _as_list(payload.get("diagnostics"))

    if not isinstance(payload.get("summary"), dict):
        input_incomplete = True
    if not isinstance(payload.get("modules"), dict):
        input_incomplete = True
    if not isinstance(payload.get("subtasks"), dict):
        input_incomplete = True
    if "documents" in payload and not isinstance(payload.get("documents"), dict):
        input_incomplete = True
    if not isinstance(payload.get("oqs"), dict):
        input_incomplete = True

    notes = _build_notes(
        render_input_invalid=render_input_invalid,
        input_incomplete=input_incomplete,
    )
    lines: list[str] = ["# Doc Governor 解释性治理报告", ""]
    lines.extend(_render_summary(summary))
    lines.extend(
        _render_requirement_mainflow(
            summary=summary,
            requirements=requirements,
            modules=modules,
            subtasks=subtasks,
            diagnostics=diagnostics,
        )
    )
    lines.extend(_render_review_section(modules, section_type="modules"))
    lines.extend(_render_review_section(subtasks, section_type="subtasks"))
    lines.extend(_render_review_section(documents, section_type="documents"))
    lines.extend(_render_blocker_sections(modules=modules, subtasks=subtasks))
    lines.extend(_render_document_blockers(documents=documents))
    lines.extend(_render_oq_summary(summary=summary, oqs=oqs))
    lines.extend(_render_open_rounds(governance_rounds))
    lines.extend(_render_round_delta(delta_summary))
    lines.extend(
        _render_next_round_agenda(
            modules=modules,
            subtasks=subtasks,
            documents=documents,
            oqs=oqs,
            governance_rounds=governance_rounds,
            agenda_limit=max(0, agenda_limit),
        )
    )
    lines.append("## 说明与解释边界")
    lines.extend(f"- {line}" for line in notes)
    return "\n".join(lines).rstrip() + "\n"


def _build_notes(*, render_input_invalid: bool, input_incomplete: bool) -> list[str]:
    notes: list[str] = [
        "这是仅供报告使用的派生输出，不代表已确认的治理状态。",
        "本报告是只读的解释性快照，不是 DOC_STATE 文件的真值来源。",
        "本报告不能直接作为 readiness 判断或自动 open-window 的信号。",
        "不要使用该文件执行状态回写，也不要把它当作 confirm-transition 的触发依据。",
    ]
    if render_input_invalid:
        notes.append("render_input_invalid=1: 输入诊断中存在 error。")
    if input_incomplete:
        notes.append(
            "render_input_incomplete=1: 必需区块 summary/modules/subtasks/oqs 缺失，已按空内容渲染。"
        )
    return notes


def _render_summary(summary: dict[str, Any]) -> list[str]:
    lines = [
        "## 摘要",
        "",
        f"- requirements_review_required: {summary.get('requirements_review_required', 0)}",
        f"- modules_review_required: {summary.get('modules_review_required', 0)}",
        f"- subtasks_review_required: {summary.get('subtasks_review_required', 0)}",
        f"- documents_review_required: {summary.get('documents_review_required', 0)}",
        f"- requirements_blocked_count: {summary.get('requirements_blocked_count', 0)}",
        f"- modules_blocked_count: {summary.get('modules_blocked_count', 0)}",
        f"- subtasks_blocked_count: {summary.get('subtasks_blocked_count', 0)}",
        f"- documents_blocked_count: {summary.get('documents_blocked_count', 0)}",
        f"- rounds_open_count: {summary.get('rounds_open_count', 0)}",
        f"- rounds_in_progress_count: {summary.get('rounds_in_progress_count', 0)}",
        f"- rounds_review_count: {summary.get('rounds_review_count', 0)}",
    ]

    blocked_by_reason_code = summary.get("blocked_by_reason_code")
    if isinstance(blocked_by_reason_code, dict) and blocked_by_reason_code:
        lines.append("- blocked_by_reason_code:")
        for reason, count in sorted(blocked_by_reason_code.items()):
            lines.append(f"  - {reason}: {count}")
    else:
        lines.append("- blocked_by_reason_code: {}")

    lines.append("- oq_gate_counts:")
    oq_gate_counts = _as_dict(summary.get("oq_gate_counts"))
    for key in GATE_COUNT_KEYS:
        lines.append(f"  - {key}: {oq_gate_counts.get(key, 0)}")
    return lines + [""]


def _render_requirement_mainflow(
    *,
    summary: dict[str, Any],
    requirements: dict[str, Any],
    modules: dict[str, Any],
    subtasks: dict[str, Any],
    diagnostics: list[Any],
) -> list[str]:
    relation_counts = _summarize_requirement_relation_status(modules=modules, subtasks=subtasks)
    consistency_counts = _summarize_requirement_relation_consistency(diagnostics)
    lines = [
        "## 需求主链",
        "",
        "### 计数",
        f"- requirement_entries: {len(requirements)}",
        f"- requirements_review_required: {summary.get('requirements_review_required', 0)}",
        f"- requirements_blocked_count: {summary.get('requirements_blocked_count', 0)}",
        f"- modules_missing_requirement_relation: {relation_counts['modules_missing_requirement_relation']}",
        f"- modules_ambiguous_requirement_relation: {relation_counts['modules_ambiguous_requirement_relation']}",
        f"- subtasks_missing_requirement_relation: {relation_counts['subtasks_missing_requirement_relation']}",
        f"- subtasks_ambiguous_requirement_relation: {relation_counts['subtasks_ambiguous_requirement_relation']}",
        f"- modules_relation_consistency_errors: {consistency_counts['modules_relation_consistency_errors']}",
        f"- modules_relation_consistency_warnings: {consistency_counts['modules_relation_consistency_warnings']}",
        f"- subtasks_relation_consistency_errors: {consistency_counts['subtasks_relation_consistency_errors']}",
        f"- subtasks_relation_consistency_warnings: {consistency_counts['subtasks_relation_consistency_warnings']}",
        "",
        "### 关联总览",
    ]

    if requirements:
        lines.append("")
        for requirement_id in sorted(requirements):
            derived = _as_dict(_as_dict(requirements.get(requirement_id)).get("derived"))
            module_ids = _normalize_string_list(derived.get("module_ids"))
            task_ids = _normalize_string_list(derived.get("task_ids"))
            blocker_refs = _normalize_string_list(derived.get("blocker_refs"))
            gate_result = str(derived.get("gate_result", "unknown"))
            review_required = "true" if bool(derived.get("review_required")) else "false"
            lines.append(
                f"- `{requirement_id}`: gate={gate_result} review_required={review_required} "
                f"modules={_format_inline_list(module_ids)} tasks={_format_inline_list(task_ids)} "
                f"blockers={_format_inline_list(blocker_refs)}"
            )
    else:
        lines.extend(["", "- 无"])

    lines.extend(["", "### 关联告警", ""])
    alerts = _collect_requirement_relation_alerts(modules=modules, subtasks=subtasks)
    alerts.extend(_collect_requirement_relation_consistency_alerts(diagnostics))
    lines.extend(alerts if alerts else ["- 无"])
    return lines + [""]


def _summarize_requirement_relation_status(
    *,
    modules: dict[str, Any],
    subtasks: dict[str, Any],
) -> dict[str, int]:
    counts = {
        "modules_missing_requirement_relation": 0,
        "modules_ambiguous_requirement_relation": 0,
        "subtasks_missing_requirement_relation": 0,
        "subtasks_ambiguous_requirement_relation": 0,
    }
    for entity_type, entities in (("modules", modules), ("subtasks", subtasks)):
        for entity in entities.values():
            derived = _as_dict(_as_dict(entity).get("derived"))
            requirement_ids = _normalize_string_list(derived.get("requirement_ids"))
            if not requirement_ids:
                counts[f"{entity_type}_missing_requirement_relation"] += 1
            elif len(requirement_ids) > 1:
                counts[f"{entity_type}_ambiguous_requirement_relation"] += 1
    return counts


def _collect_requirement_relation_alerts(
    *,
    modules: dict[str, Any],
    subtasks: dict[str, Any],
) -> list[str]:
    rows: list[str] = []
    for entity_type, entities in (("module", modules), ("subtask", subtasks)):
        for entity_id in sorted(entities):
            derived = _as_dict(_as_dict(entities.get(entity_id)).get("derived"))
            requirement_ids = _normalize_string_list(derived.get("requirement_ids"))
            if not requirement_ids:
                rows.append(f"- `{entity_type}:{entity_id}`: requirement_relation=missing")
                continue
            if len(requirement_ids) > 1:
                blocker_refs = _collect_relation_alert_blocker_refs(derived)
                suffix = (
                    f" blockers={_format_inline_list(blocker_refs)}"
                    if blocker_refs
                    else ""
                )
                rows.append(
                    f"- `{entity_type}:{entity_id}`: requirement_relation=ambiguous "
                    f"ids={_format_inline_list(requirement_ids)}{suffix}"
                )
    return rows


def _summarize_requirement_relation_consistency(diagnostics: list[Any]) -> dict[str, int]:
    counts = {
        "modules_relation_consistency_errors": 0,
        "modules_relation_consistency_warnings": 0,
        "subtasks_relation_consistency_errors": 0,
        "subtasks_relation_consistency_warnings": 0,
    }
    for diagnostic in diagnostics:
        diag = _as_dict(diagnostic)
        code = str(diag.get("code", ""))
        if code not in REQUIREMENT_RELATION_CONSISTENCY_CODES:
            continue
        entity_type = str(diag.get("entity_type", ""))
        severity = str(diag.get("severity", "warning"))
        if entity_type == "module":
            key = "modules_relation_consistency_errors" if severity == "error" else "modules_relation_consistency_warnings"
            counts[key] += 1
        elif entity_type == "subtask":
            key = "subtasks_relation_consistency_errors" if severity == "error" else "subtasks_relation_consistency_warnings"
            counts[key] += 1
    return counts


def _collect_requirement_relation_consistency_alerts(diagnostics: list[Any]) -> list[str]:
    sortable_rows: list[tuple[str, str, str, str]] = []
    for diagnostic in diagnostics:
        diag = _as_dict(diagnostic)
        code = str(diag.get("code", ""))
        if code not in REQUIREMENT_RELATION_CONSISTENCY_CODES:
            continue
        entity_type = str(diag.get("entity_type", "")).strip()
        entity_id = str(diag.get("entity_id", "")).strip()
        severity = str(diag.get("severity", "warning")).strip() or "warning"
        if entity_type not in {"module", "subtask"} or not entity_id:
            continue
        sortable_rows.append((entity_type, entity_id, severity, code))

    rows: list[str] = []
    for entity_type, entity_id, severity, code in sorted(sortable_rows):
        rows.append(
            f"- `{entity_type}:{entity_id}`: relation_consistency="
            f"{REQUIREMENT_RELATION_CONSISTENCY_CODES[code]} "
            f"severity={severity} code={code}"
        )
    return rows


def _collect_relation_alert_blocker_refs(derived: dict[str, Any]) -> list[str]:
    blocker_refs = _normalize_string_list(derived.get("blocker_refs"))
    if blocker_refs:
        return blocker_refs

    collected: list[str] = []
    for blocker_key in (
        "candidate_blockers",
        "downstream_blockers",
        "implementation_blockers",
    ):
        for blocker in _as_list(derived.get(blocker_key)):
            if not isinstance(blocker, dict):
                continue
            ref = str(blocker.get("ref", "")).strip()
            if ref:
                collected.append(ref)
    return _normalize_string_list(collected)


def _normalize_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _format_inline_list(values: list[str]) -> str:
    return "[" + ", ".join(values) + "]"


def _render_review_section(entities: dict[str, Any], section_type: str) -> list[str]:
    title_map = {
        "modules": "需评审模块",
        "subtasks": "需评审子任务",
        "documents": "需评审文档",
    }
    title = title_map[section_type]
    lines = [f"## {title}", ""]
    rows: list[str] = []
    for entity_id in sorted(entities):
        entity = _as_dict(entities.get(entity_id, {}))
        derived = _as_dict(entity.get("derived"))
        if not derived.get("review_required"):
            continue
        reasons = ", ".join(str(item) for item in _as_list(derived.get("review_reasons")))
        rows.append(f"- `{entity_id}`: review_required=true reason=[{reasons}]")
    lines.extend(rows if rows else ["- 无"])
    return lines + [""]


def _render_blocker_sections(
    *,
    modules: dict[str, Any],
    subtasks: dict[str, Any],
) -> list[str]:
    module_candidate = _get_blockers(
        entities=modules,
        entity_type="module",
        blocker_key="candidate_blockers",
    )
    subtask_candidate = _get_blockers(
        entities=subtasks,
        entity_type="subtask",
        blocker_key="candidate_blockers",
    )

    module_downstream = _get_blockers(
        entities=modules,
        entity_type="module",
        blocker_key="downstream_blockers",
    )
    subtask_downstream = _get_blockers(
        entities=subtasks,
        entity_type="subtask",
        blocker_key="downstream_blockers",
    )
    subtask_impl = _get_blockers(
        entities=subtasks,
        entity_type="subtask",
        blocker_key="implementation_blockers",
    )

    lines: list[str] = ["## 按层级汇总的 candidate blockers", ""]
    lines.extend(["### 模块", ""])
    _append_blocker_lines(lines, module_candidate)
    lines.extend(["### 子任务", ""])
    _append_blocker_lines(lines, subtask_candidate)

    lines.extend(["", "## 按层级汇总的 downstream blockers", ""])
    lines.extend(["### 模块", ""])
    _append_blocker_lines(lines, module_downstream)
    lines.extend(["### 子任务", ""])
    _append_blocker_lines(lines, subtask_downstream)

    lines.extend(["", "## 按层级汇总的 implementation blockers", ""])
    lines.extend(["### 子任务", ""])
    _append_blocker_lines(lines, subtask_impl)
    return lines + [""]


def _render_document_blockers(*, documents: dict[str, Any]) -> list[str]:
    blockers = _get_blockers(
        entities=documents,
        entity_type="document",
        blocker_key="document_blockers",
    )
    lines = ["## 文档阻塞项", "", "### 文档", ""]
    _append_blocker_lines(lines, blockers)
    return lines + [""]


def _get_blockers(
    *,
    entities: dict[str, Any],
    entity_type: str,
    blocker_key: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entity_id in sorted(entities):
        entity = _as_dict(entities.get(entity_id, {}))
        derived = _as_dict(entity.get("derived"))
        for blocker in _as_list(derived.get(blocker_key)):
            if not isinstance(blocker, dict):
                continue
            rows.append(
                {
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "ref": str(blocker.get("ref", "")),
                    "kind": str(blocker.get("kind", "")),
                    "reason_code": str(blocker.get("reason_code", "")),
                    "message": str(blocker.get("message", "")),
                }
            )
    return sorted(
        rows,
        key=lambda item: (item["reason_code"], item["ref"], item["entity_type"], item["entity_id"]),
    )


def _append_blocker_lines(lines: list[str], blockers: list[dict[str, Any]]) -> None:
    if not blockers:
        lines.append("- 无")
        return
    for blocker in blockers:
        lines.append(
            f"- [{blocker['entity_type']}:{blocker['entity_id']}] "
            f"reason_code={blocker['reason_code']} ref={blocker['ref']} "
            f"kind={blocker['kind']} message={blocker['message']}"
        )


def _render_oq_summary(*, summary: dict[str, Any], oqs: dict[str, Any]) -> list[str]:
    lines = ["## OQ 门控摘要", "", "### 计数"]
    oq_gate_counts = _as_dict(summary.get("oq_gate_counts"))

    if not oq_gate_counts and not oqs:
        lines.append("- 无")
        lines.append("")
        return lines

    for key in GATE_COUNT_KEYS:
        lines.append(f"- {key}: {oq_gate_counts.get(key, 0)}")
    return lines + [""]


def _render_open_rounds(governance_rounds: list[Any]) -> list[str]:
    lines = ["## 未关闭轮次", ""]
    rows: list[str] = []
    for item in governance_rounds:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", ""))
        if status not in {"open", "in_progress", "review"}:
            continue
        targets = []
        for target in _as_list(item.get("target_documents")):
            if not isinstance(target, dict):
                continue
            document_id = str(target.get("document_id", ""))
            sections = ",".join(
                section
                for section in _as_list(target.get("target_sections"))
                if isinstance(section, str) and section
            )
            targets.append(f"{document_id}:{sections}" if sections else document_id)
        rows.append(
            f"- `{item.get('round_id', '')}`: status={status} topic={item.get('topic', '')} "
            f"targets=[{'; '.join(targets)}]"
        )
    lines.extend(rows if rows else ["- 无"])
    return lines + [""]


def _render_round_delta(delta_summary: dict[str, Any]) -> list[str]:
    lines = ["## 轮次变化摘要", ""]
    if not delta_summary:
        lines.append("- 无")
        return lines + [""]

    blocker_changes = _as_dict(delta_summary.get("blocker_changes"))
    lines.extend(["### 阻塞项变化"])
    lines.append(f"- added_count: {blocker_changes.get('added_count', 0)}")
    lines.append(f"- closed_count: {blocker_changes.get('closed_count', 0)}")

    review_required_changes = _as_dict(delta_summary.get("review_required_changes"))
    lines.extend(["", "### 需评审变化"])
    for key in ("modules", "subtasks"):
        delta = _as_dict(review_required_changes.get(key))
        lines.append(
            f"- {key}: before={delta.get('before_true_count', 0)} after={delta.get('after_true_count', 0)} "
            f"delta={delta.get('delta_true_count', 0)}"
        )

    readiness_changes = _as_dict(delta_summary.get("readiness_changes"))
    lines.extend(["", "### 就绪度变化"])
    for key in ("modules_downstream", "subtasks_downstream", "subtasks_implementation"):
        delta = _as_dict(readiness_changes.get(key))
        lines.append(
            f"- {key}: before={delta.get('before_true_count', 0)} after={delta.get('after_true_count', 0)} "
            f"delta={delta.get('delta_true_count', 0)}"
        )

    return lines + [""]


def _render_next_round_agenda(
    *,
    modules: dict[str, Any],
    subtasks: dict[str, Any],
    documents: dict[str, Any],
    oqs: dict[str, Any],
    governance_rounds: list[Any],
    agenda_limit: int,
) -> list[str]:
    lines = ["## 下一轮议程", ""]
    agenda_items = _build_next_round_agenda(
        modules=modules,
        subtasks=subtasks,
        documents=documents,
        oqs=oqs,
        governance_rounds=governance_rounds,
        agenda_limit=agenda_limit,
    )
    if not agenda_items:
        lines.append("- 无")
        return lines + [""]

    for idx, item in enumerate(agenda_items, start=1):
        lines.append(f"### 议程 {idx}: {item['category']}")
        lines.append(f"- entity: {item['entity']}")
        lines.append(f"- current_state: {item['current_state']}")
        lines.append(
            "- blocking_reason_codes: "
            + (", ".join(item["blocking_reason_codes"]) if item["blocking_reason_codes"] else "无")
        )
        lines.append(
            "- required_evidence: "
            + (", ".join(item["required_evidence"]) if item["required_evidence"] else "无")
        )
        lines.append(f"- suggested_owner: {item['suggested_owner']}")
        lines.append("")
    return lines


def _build_next_round_agenda(
    *,
    modules: dict[str, Any],
    subtasks: dict[str, Any],
    documents: dict[str, Any],
    oqs: dict[str, Any],
    governance_rounds: list[Any],
    agenda_limit: int,
) -> list[dict[str, Any]]:
    agenda: list[dict[str, Any]] = []

    for oq_id in sorted(oqs):
        oq = _as_dict(oqs.get(oq_id))
        enforcement = str(oq.get("derived_enforcement", ""))
        reason_code = str(oq.get("derived_reason_code", ""))
        if enforcement not in {"candidate_blocker", "readiness_blocker"} and reason_code not in {
            "oq_candidate_gate",
            "oq_readiness_gate",
        }:
            continue
        agenda.append(
            {
                "category": "必须先决策的 OQ（candidate/readiness gate）",
                "entity": f"oq:{oq_id}",
                "current_state": (
                    f"status_class={str(oq.get('derived_status_class', 'unknown'))}, "
                    f"enforcement={enforcement or 'unknown'}"
                ),
                "blocking_reason_codes": [reason_code] if reason_code else [],
                "required_evidence": ["已确认的 OQ 决策证据（confirmed/manual override）"],
                "suggested_owner": "governance-owner",
                "_sort_group": 0,
                "_sort_key": f"oq:{oq_id}",
            }
        )

    for document_id in sorted(documents):
        derived = _as_dict(_as_dict(documents.get(document_id)).get("derived"))
        blocker_codes = _collect_blocker_reason_codes(derived)
        if blocker_codes:
            agenda.append(
                {
                    "category": "文档缺口待补齐",
                    "entity": f"document:{document_id}",
                    "current_state": (
                        f"review_required={str(bool(derived.get('review_required'))).lower()}, "
                        f"hard_blocker_count={len(blocker_codes)}"
                    ),
                    "blocking_reason_codes": blocker_codes,
                    "required_evidence": ["文档章节补齐证据"],
                    "suggested_owner": "document-owner",
                    "_sort_group": 1,
                    "_sort_key": f"document:{document_id}",
                }
            )
        elif derived.get("review_required"):
            agenda.append(
                {
                    "category": "文档待评审",
                    "entity": f"document:{document_id}",
                    "current_state": "review_required=true, hard_blocker_count=0",
                    "blocking_reason_codes": [],
                    "required_evidence": ["文档评审确认依据"],
                    "suggested_owner": "document-owner",
                    "_sort_group": 2,
                    "_sort_key": f"document:{document_id}",
                }
            )

    near_open_entities = _collect_entity_agenda(modules=modules, subtasks=subtasks, near_open_only=True)
    for index, item in enumerate(near_open_entities):
        item["category"] = "review_required 的 near-open 实体"
        item["_sort_group"] = 3
        item["_sort_key"] = f"{index:04d}"
        agenda.append(item)

    blocker_light_entities = _collect_entity_agenda(modules=modules, subtasks=subtasks, near_open_only=False)
    for index, item in enumerate(blocker_light_entities):
        if item.get("_hard_blocker_count", 0) <= 0:
            continue
        item["category"] = "hard blocker 最少、最接近可推进的实体"
        item["_sort_group"] = 4
        item["_sort_key"] = f"{index:04d}"
        agenda.append(item)

    for item in governance_rounds:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", ""))
        if status not in {"open", "in_progress", "review"}:
            continue
        agenda.append(
            {
                "category": "未关闭 round 的收口项",
                "entity": f"round:{item.get('round_id', '')}",
                "current_state": f"status={status}",
                "blocking_reason_codes": [],
                "required_evidence": [
                    str(entry)
                    for entry in _as_list(item.get("writeback_items"))
                    if isinstance(entry, str) and entry
                ],
                "suggested_owner": "governance-owner",
                "_sort_group": 5,
                "_sort_key": str(item.get("round_id", "")),
            }
        )

    if agenda_limit <= 0:
        return []
    for item in agenda:
        item.setdefault("_sort_group", 99)
        item.setdefault("_sort_key", item["entity"])
    agenda.sort(key=lambda item: (item["_sort_group"], item["_sort_key"]))
    return [
        {
            key: value
            for key, value in item.items()
            if not key.startswith("_")
        }
        for item in agenda[:agenda_limit]
    ]


def _collect_entity_agenda(
    *,
    modules: dict[str, Any],
    subtasks: dict[str, Any],
    near_open_only: bool,
) -> list[dict[str, Any]]:
    entities: list[dict[str, Any]] = []
    for entity_type, source in (("module", modules), ("subtask", subtasks)):
        for entity_id in sorted(source):
            entity = _as_dict(source.get(entity_id))
            derived = _as_dict(entity.get("derived"))
            review_required = bool(derived.get("review_required"))
            blocker_codes = _collect_blocker_reason_codes(derived)
            hard_blocker_count = len(blocker_codes)
            if near_open_only and (not review_required or hard_blocker_count != 0):
                continue
            entities.append(
                {
                    "entity": f"{entity_type}:{entity_id}",
                    "current_state": (
                        f"review_required={str(review_required).lower()}, "
                        f"hard_blocker_count={hard_blocker_count}"
                    ),
                    "blocking_reason_codes": blocker_codes,
                    "required_evidence": (
                        ["评审确认依据"]
                        if review_required
                        else ["阻塞项消解证据", "评审确认依据"]
                    ),
                    "suggested_owner": f"{entity_type}-owner",
                    "_hard_blocker_count": hard_blocker_count,
                    "_review_required": review_required,
                }
            )

    entities.sort(
        key=lambda item: (
            item["_hard_blocker_count"],
            0 if item["_review_required"] else 1,
            0 if str(item["entity"]).startswith("subtask:") else 1,
            item["entity"],
        )
    )
    return entities


def _collect_blocker_reason_codes(derived: dict[str, Any]) -> list[str]:
    reason_codes: list[str] = []
    for blocker_key in (
        "candidate_blockers",
        "downstream_blockers",
        "implementation_blockers",
        "document_blockers",
    ):
        for blocker in _as_list(derived.get(blocker_key)):
            if not isinstance(blocker, dict):
                continue
            reason = str(blocker.get("reason_code", "")).strip()
            if reason:
                reason_codes.append(reason)
    return sorted(set(reason_codes))


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def build_render_diagnostics(
    path: Any,
    code: str,
    message: str,
    severity: str = "error",
) -> list[Diagnostic]:
    return [
        make_diagnostic(
            code=code,
            severity=severity,
            entity_type="render",
            entity_id="GLOBAL",
            field_path="render",
            message=message,
            evidence=[
                make_evidence(
                    type="file_scan",
                    path=path.as_posix(),
                    ref="render",
                    value=path.as_posix(),
                )
            ],
        )
    ]
