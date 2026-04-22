from __future__ import annotations

import re
from pathlib import Path

from .diagnostics import Diagnostic, make_diagnostic, make_evidence
from .naming_rules import MODULE_DIR_RE, SUBTASK_DIR_RE
from .requirement_scan import scan_requirements
from .schema import MODULE_DOC_SLOTS, SUBTASK_DOC_SLOTS
from .template_detection import detect_template_signals

MARKDOWN_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|(?:\s*:?-+:?\s*\|)+\s*$")


OPEN_QUESTIONS_HEADERS = (
    "OQ ID",
    "问题",
    "状态",
    "关联模块",
)

TASK_INDEX_HEADERS = (
    "Task ID",
    "对应文档路径",
)

OPEN_QUESTION_REQUIRED_HEADERS = ("oq_id", "title", "status", "affects")
OPEN_QUESTION_OPTIONAL_HEADERS = ("gate_level", "resolution_policy")

DOC_KIND_KEY_FIELDS = {
    "module_design": ("目标", "范围", "约束"),
    "module_doc": ("输入", "输出", "风险"),
    "subtask_design": ("目标", "方案", "验收"),
    "subtask_implementation": ("步骤", "验证", "回滚"),
}

DOC_KIND_TEMPLATE_HEADINGS = {
    "module_design": {"背景", "目标", "范围", "约束", "风险"},
    "module_doc": {"背景", "输入", "输出", "依赖", "风险"},
    "subtask_design": {"目标", "方案", "边界", "验收"},
    "subtask_implementation": {"步骤", "验证", "回滚"},
}


def scan_repo(repo_root: str | Path) -> dict[str, object]:
    root = Path(repo_root).resolve()
    filesystem = scan_filesystem(root)
    oq_scan = scan_open_questions_table(root / "OPEN_QUESTIONS.md")
    task_scan = scan_task_index_table(root / "TASK_INDEX.md")

    diagnostics = [
        *filesystem["diagnostics"],
        *oq_scan["diagnostics"],
        *task_scan["diagnostics"],
    ]

    oqs = oq_scan["oqs"]
    modules = _merge_modules(
        repo_root=root,
        filesystem_modules=filesystem["modules"],
        table_modules=task_scan["modules"],
        oqs=oqs,
    )
    subtasks = _merge_subtasks(
        repo_root=root,
        filesystem_subtasks=filesystem["subtasks"],
        table_subtasks=task_scan["subtasks"],
        oqs=oqs,
    )
    requirement_scan = scan_requirements(
        repo_root=root,
        modules=modules,
        subtasks=subtasks,
    )
    diagnostics.extend(requirement_scan["diagnostics"])

    template_like_doc_count = 0
    for module in modules.values():
        template_like_doc_count += sum(
            1 for item in module["facts"]["docs"].values() if item["template_like"]
        )
    for subtask in subtasks.values():
        template_like_doc_count += sum(
            1
            for item in (
                subtask["facts"]["design_doc"],
                subtask["facts"]["implementation_doc"],
            )
            if item["template_like"]
        )

    return {
        "repo_root": root,
        "diagnostics": diagnostics,
        "oqs": oqs,
        "requirements": requirement_scan["requirements"],
        "modules": modules,
        "subtasks": subtasks,
        "counts": {
            "requirement": requirement_scan["counts"]["requirement"],
            "module": len(modules),
            "subtask": len(subtasks),
            "oq": len(oqs),
            "template_like_doc": template_like_doc_count,
        },
    }


def scan_filesystem(repo_root: Path) -> dict[str, object]:
    modules_root = repo_root / "docs" / "modules"
    diagnostics: list[Diagnostic] = []
    modules: dict[str, dict[str, object]] = {}
    subtasks: dict[str, dict[str, object]] = {}

    if not modules_root.exists():
        return {"modules": modules, "subtasks": subtasks, "diagnostics": diagnostics}

    for module_dir in sorted(path for path in modules_root.iterdir() if path.is_dir()):
        module_match = MODULE_DIR_RE.match(module_dir.name)
        if module_match is None:
            continue
        module_id = module_match.group(1)
        module_docs, module_diagnostics = _scan_doc_slots(
            repo_root=repo_root,
            base_dir=module_dir,
            slots=MODULE_DOC_SLOTS,
            entity_type="module",
            entity_id=module_id,
        )
        diagnostics.extend(module_diagnostics)
        modules[module_id] = {
            "module_id": module_id,
            "path": module_dir.relative_to(repo_root).as_posix(),
            "docs": module_docs,
        }

        sub_modules_dir = module_dir / "sub_modules"
        if not sub_modules_dir.exists():
            continue

        for subtask_dir in sorted(
            path for path in sub_modules_dir.iterdir() if path.is_dir()
        ):
            subtask_match = SUBTASK_DIR_RE.match(subtask_dir.name)
            if subtask_match is None:
                continue
            subtask_id = subtask_match.group(1)
            subtask_docs, subtask_diagnostics = _scan_doc_slots(
                repo_root=repo_root,
                base_dir=subtask_dir,
                slots=SUBTASK_DOC_SLOTS,
                entity_type="subtask",
                entity_id=subtask_id,
            )
            diagnostics.extend(subtask_diagnostics)
            subtasks[subtask_id] = {
                "subtask_id": subtask_id,
                "module_id": module_id,
                "path": subtask_dir.relative_to(repo_root).as_posix(),
                "docs": subtask_docs,
            }

    return {"modules": modules, "subtasks": subtasks, "diagnostics": diagnostics}


def scan_open_questions_table(path: Path) -> dict[str, object]:
    diagnostics: list[Diagnostic] = []
    oqs: dict[str, dict[str, object]] = {}
    if not path.exists():
        diagnostics.append(
            make_diagnostic(
                code="SCAN_OPEN_QUESTIONS_TABLE_NOT_FOUND",
                severity="warning",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="OPEN_QUESTIONS.md",
                message="OPEN_QUESTIONS.md structured table not found.",
                evidence=[
                    make_evidence(
                        type="file_scan",
                        path=str(path),
                        ref="exists",
                        value=False,
                    )
                ],
            )
        )
        return {"oqs": oqs, "diagnostics": diagnostics}

    table = _find_markdown_table(path.read_text(encoding="utf-8"), OPEN_QUESTIONS_HEADERS)
    if table is None:
        diagnostics.append(
            make_diagnostic(
                code="SCAN_OPEN_QUESTIONS_TABLE_NOT_FOUND",
                severity="warning",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="OPEN_QUESTIONS.md",
                message="OPEN_QUESTIONS.md structured table not found.",
                evidence=[make_evidence(type="file_scan", path=str(path), ref="table_headers")],
            )
        )
        return {"oqs": oqs, "diagnostics": diagnostics}

    headers, rows = table
    header_index = _build_oq_header_index(headers)

    for row_index, row in enumerate(rows, start=1):
        try:
            oq_id = _get_cell(header_index, row, "oq_id").strip()
            if not oq_id:
                raise ValueError("Missing OQ ID")
            affects = _parse_affected_entities(_get_cell(header_index, row, "affects"))
            if not isinstance(affects, dict):
                affects = {"modules": [], "subtasks": []}

            oq_entry: dict[str, object] = {
                "title": _get_cell(header_index, row, "title").strip(),
                "status": _get_cell(header_index, row, "status").strip() or "open",
                "affects": affects,
                "declared_blocker_refs": [],
            }

            gate_level = _get_cell(header_index, row, "gate_level").strip()
            if gate_level:
                oq_entry["gate_level"] = gate_level

            resolution_policy = _get_cell(header_index, row, "resolution_policy").strip()
            if resolution_policy:
                oq_entry["resolution_policy"] = resolution_policy

            oqs[oq_id] = oq_entry
        except Exception as exc:  # noqa: BLE001
            diagnostics.append(
                make_diagnostic(
                    code="SCAN_OPEN_QUESTIONS_ROW_PARSE_FAILED",
                    severity="warning",
                    entity_type="oq",
                    entity_id=f"ROW-{row_index}",
                    field_path=f"OPEN_QUESTIONS.md.row[{row_index}]",
                    message=f"OPEN_QUESTIONS.md row {row_index} parse failed: {exc}",
                    evidence=[
                        make_evidence(
                            type="table_row",
                            path=str(path),
                            ref=f"row[{row_index}]",
                            value=" | ".join(row),
                        )
                    ],
                )
            )

    return {"oqs": oqs, "diagnostics": diagnostics}


def scan_task_index_table(path: Path) -> dict[str, object]:
    diagnostics: list[Diagnostic] = []
    modules: dict[str, dict[str, object]] = {}
    subtasks: dict[str, dict[str, object]] = {}

    if not path.exists():
        diagnostics.append(
            make_diagnostic(
                code="SCAN_TASK_INDEX_TABLE_NOT_FOUND",
                severity="warning",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="TASK_INDEX.md",
                message="TASK_INDEX.md structured table not found.",
                evidence=[
                    make_evidence(
                        type="file_scan",
                        path=str(path),
                        ref="exists",
                        value=False,
                    )
                ],
            )
        )
        return {"modules": modules, "subtasks": subtasks, "diagnostics": diagnostics}

    tables = _find_all_markdown_tables(path.read_text(encoding="utf-8"), TASK_INDEX_HEADERS)
    if not tables:
        diagnostics.append(
            make_diagnostic(
                code="SCAN_TASK_INDEX_TABLE_NOT_FOUND",
                severity="warning",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="TASK_INDEX.md",
                message="TASK_INDEX.md structured table not found.",
                evidence=[make_evidence(type="file_scan", path=str(path), ref="table_headers")],
            )
        )
        return {"modules": modules, "subtasks": subtasks, "diagnostics": diagnostics}

    row_counter = 0
    for headers, rows in tables:
        header_index = _build_task_index_header_index(headers)
        if not header_index:
            diagnostics.append(
                make_diagnostic(
                    code="SCAN_TASK_INDEX_TABLE_NOT_FOUND",
                    severity="warning",
                    entity_type="system",
                    entity_id="GLOBAL",
                    field_path="TASK_INDEX.md",
                    message="TASK_INDEX table headers are not parsable.",
                    evidence=[make_evidence(type="file_scan", path=str(path), ref="table_headers")],
                )
            )
            continue

        for row in rows:
            row_counter += 1
            try:
                task_id = _get_cell(header_index, row, "task_id").strip()
                path_value = _clean_doc_path(_get_cell(header_index, row, "path"))
                if not task_id or not path_value:
                    raise ValueError("Task ID or path missing")

                upstream = _parse_module_dependencies(_get_cell(header_index, row, "upstream"))
                legacy_locked = _is_legacy_locked_row(_row_as_dict(header_index, row))
                if task_id.startswith("M"):
                    modules[task_id] = {
                        "path": path_value,
                        "upstream_module_ids": upstream,
                        "legacy_locked": legacy_locked,
                    }
                elif task_id.startswith("ST"):
                    subtasks[task_id] = {
                        "path": path_value,
                        "module_id": _get_cell(header_index, row, "parent").strip(),
                        "upstream_module_ids": upstream,
                        "legacy_locked": legacy_locked,
                    }
            except Exception as exc:  # noqa: BLE001
                diagnostics.append(
                    make_diagnostic(
                        code="SCAN_TASK_INDEX_ROW_PARSE_FAILED",
                        severity="warning",
                        entity_type="system",
                        entity_id=f"ROW-{row_counter}",
                        field_path=f"TASK_INDEX.md.row[{row_counter}]",
                        message=f"TASK_INDEX.md row {row_counter} parse failed: {exc}",
                        evidence=[
                            make_evidence(
                                type="table_row",
                                path=str(path),
                                ref=f"row[{row_counter}]",
                                value=" | ".join(row),
                            )
                        ],
                    )
                )

    return {"modules": modules, "subtasks": subtasks, "diagnostics": diagnostics}


def _scan_doc_slots(
    *,
    repo_root: Path,
    base_dir: Path,
    slots: dict[str, str],
    entity_type: str,
    entity_id: str,
) -> tuple[dict[str, dict[str, object]], list[Diagnostic]]:
    docs: dict[str, dict[str, object]] = {}
    diagnostics: list[Diagnostic] = []
    for slot_name, filename in slots.items():
        doc_path = base_dir / filename
        relative_path = doc_path.relative_to(repo_root).as_posix()
        if doc_path.exists():
            text = doc_path.read_text(encoding="utf-8")
            doc_kind = _resolve_doc_kind(entity_type=entity_type, slot_name=slot_name)
            template_like, template_diagnostics = detect_template_signals(
                path=relative_path,
                text=text,
                doc_kind=doc_kind,
            )
            docs[slot_name] = {"exists": True, "template_like": template_like}
            for item in template_diagnostics:
                diagnostics.append(
                    make_diagnostic(
                        code=str(item["code"]),
                        severity=str(item["severity"]),
                        entity_type="doc_slot",
                        entity_id=relative_path,
                        field_path=f"facts.{slot_name}",
                        message=str(item["message"]),
                        evidence=[
                            make_evidence(
                                type=str(evidence["type"]),
                                path=str(evidence["path"]),
                                ref=str(evidence["ref"]),
                                value=evidence.get("value"),
                                line=evidence.get("line"),
                                snippet=evidence.get("snippet"),
                            )
                            for evidence in item["evidence"]
                        ],
                    )
                )
            weak_signals = _collect_doc_weak_signals(text=text, doc_kind=doc_kind)
            diagnostics.append(
                make_diagnostic(
                    code="SCAN_DOC_WEAK_SIGNALS",
                    severity="warning",
                    entity_type="doc_slot",
                    entity_id=relative_path,
                    field_path=f"facts.{slot_name}.weak_signals",
                    message=(
                        "文档弱信号仅用于诊断讨论，不会直接回写 confirmed state。"
                    ),
                    evidence=[
                        make_evidence(
                            type="doc_signal",
                            path=relative_path,
                            ref="weak_signals",
                            value=weak_signals,
                        )
                    ],
                )
            )
        else:
            docs[slot_name] = {"exists": False, "template_like": False}
    return docs, diagnostics


def _merge_modules(
    *,
    repo_root: Path,
    filesystem_modules: dict[str, dict[str, object]],
    table_modules: dict[str, dict[str, object]],
    oqs: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    modules: dict[str, dict[str, object]] = {}
    for module_id in sorted(set(filesystem_modules) | set(table_modules)):
        fs_entry = filesystem_modules.get(module_id, {})
        table_entry = table_modules.get(module_id, {})
        path_value = table_entry.get("path") or fs_entry.get("path") or _default_module_path(module_id)
        modules[module_id] = {
            "meta": {"path": path_value},
            "facts": {
                "upstream_module_ids": list(table_entry.get("upstream_module_ids", [])),
                "related_oq_ids": sorted(
                    oq_id
                    for oq_id, oq in oqs.items()
                    if module_id in oq.get("affects", {}).get("modules", [])
                ),
                "legacy_locked": bool(table_entry.get("legacy_locked", False)),
                "declared_blocker_refs": [],
                "docs": fs_entry.get(
                    "docs",
                    {slot: {"exists": False, "template_like": False} for slot in MODULE_DOC_SLOTS},
                ),
            },
        }
    return modules


def _merge_subtasks(
    *,
    repo_root: Path,
    filesystem_subtasks: dict[str, dict[str, object]],
    table_subtasks: dict[str, dict[str, object]],
    oqs: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    subtasks: dict[str, dict[str, object]] = {}
    for subtask_id in sorted(set(filesystem_subtasks) | set(table_subtasks)):
        fs_entry = filesystem_subtasks.get(subtask_id, {})
        table_entry = table_subtasks.get(subtask_id, {})
        path_value = table_entry.get("path") or fs_entry.get("path") or ""
        docs = fs_entry.get(
            "docs",
            {
                slot: {"exists": False, "template_like": False}
                for slot in SUBTASK_DOC_SLOTS
            },
        )
        subtasks[subtask_id] = {
            "meta": {
                "module_id": table_entry.get("module_id") or fs_entry.get("module_id"),
                "path": path_value,
            },
            "facts": {
                "upstream_module_ids": list(table_entry.get("upstream_module_ids", [])),
                "related_oq_ids": sorted(
                    oq_id
                    for oq_id, oq in oqs.items()
                    if subtask_id in oq.get("affects", {}).get("subtasks", [])
                ),
                "legacy_locked": bool(table_entry.get("legacy_locked", False)),
                "declared_blocker_refs": [],
                "design_doc": docs["design_doc"],
                "implementation_doc": docs["implementation_doc"],
            },
        }
    return subtasks


def _find_markdown_table(
    text: str, required_headers: tuple[str, ...]
) -> tuple[list[str], list[list[str]]] | None:
    tables = _find_all_markdown_tables(text, required_headers)
    return tables[0] if tables else None


def _find_all_markdown_tables(
    text: str,
    required_headers: tuple[str, ...],
) -> list[tuple[list[str], list[list[str]]]]:
    tables: list[tuple[list[str], list[list[str]]]] = []
    normalized_required = {_normalize_header(h) for h in required_headers}
    for block in _extract_table_blocks(text):
        headers = _split_markdown_row(block[0])
        normalized = {_normalize_header(cell) for cell in headers}
        if not normalized_required.issubset(normalized):
            continue
        rows = [_split_markdown_row(line) for line in block[2:]]
        tables.append((headers, rows))
    return tables


def _extract_table_blocks(text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            current.append(line)
            continue
        if current:
            if len(current) >= 2 and MARKDOWN_TABLE_SEPARATOR_RE.match(current[1]):
                blocks.append(current)
            current = []
    if current and len(current) >= 2 and MARKDOWN_TABLE_SEPARATOR_RE.match(current[1]):
        blocks.append(current)
    return blocks


def _split_markdown_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _normalize_header(value: str) -> str:
    normalized = (
        value.strip()
        .lower()
        .replace("（", "(")
        .replace("）", ")")
        .replace("：", ":")
        .replace("；", ";")
        .replace(",", ",")
        .replace("`", "")
    )
    return re.sub(r"[\s_-]+", "", normalized)


def _build_oq_header_index(headers: list[str]) -> dict[str, int]:
    header_index: dict[str, int] = {}
    for index, raw_header in enumerate(headers):
        normalized = _normalize_header(raw_header)
        lowered = raw_header.strip().lower()
        if normalized in {"oqid", "oq_id", "oqid"}:
            header_index.setdefault("oq_id", index)
        if normalized in {"qid", "issueid", "issue_id", "issueid", "title", "问题", "标题"} or "issue" in lowered or "title" in lowered:
            header_index.setdefault("title", index)
        if normalized in {"status", "state", "状态"} or "status" in lowered or "state" in lowered:
            header_index.setdefault("status", index)
        if normalized in {"affects", "related", "关联", "关联模块", "影响", "影响范围"} or "affect" in lowered or "关联" in lowered or "相关" in lowered:
            header_index.setdefault("affects", index)
        if normalized in {"gatelevel", "gate_level", "gatelevel", "gatelvl", "candidate_gate", "readiness_gate", "observe_only", "gatelvl", "gatel"} or "gate" in lowered:
            header_index.setdefault("gate_level", index)
        if "resolutionpolicy" in normalized or "resolution_policy" in normalized or "resolution policy" in lowered or "resolutionpolicy" in lowered:
            header_index.setdefault("resolution_policy", index)

    # Fallback by stable column order for tables that we don't recognize well.
    fallback_order = ["oq_id", "title", "status", "affects"]
    for fallback_index, field in enumerate(fallback_order):
        if field not in header_index:
            if fallback_index < len(headers):
                header_index[field] = fallback_index

    return header_index


def _build_task_index_header_index(headers: list[str]) -> dict[str, int]:
    normalized_to_index = {_normalize_header(value): index for index, value in enumerate(headers)}
    header_index: dict[str, int] = {}

    for raw in headers:
        norm = _normalize_header(raw)
        lowered = raw.strip().lower()
        if "taskid" in norm or norm in {"taskid", "task_id", "task"} or "task id" in lowered:
            header_index.setdefault("task_id", headers.index(raw))
        if "parent" in lowered or "父任务" in raw:
            header_index.setdefault("parent", headers.index(raw))
        if "upstream" in lowered or "依赖" in raw:
            header_index.setdefault("upstream", headers.index(raw))
        if "path" in lowered or "文档路径" in raw:
            header_index.setdefault("path", headers.index(raw))

    # fallback to canonical positions in known layout:
    # [Task ID, 名称, 父任务, 前置依赖, ..., ..., ..., 对应文档路径]
    if "task_id" not in header_index and len(headers) > 0:
        header_index["task_id"] = 0
    if "path" not in header_index and len(headers) > 2:
        header_index["path"] = len(headers) - 1
    if "parent" not in header_index and len(headers) > 2:
        header_index["parent"] = 2
    if "upstream" not in header_index and len(headers) > 3:
        header_index["upstream"] = 3

    return header_index if header_index else {}


def _resolve_doc_kind(*, entity_type: str, slot_name: str) -> str:
    if entity_type == "subtask" and slot_name == "implementation_doc":
        return "subtask_implementation"
    if entity_type == "subtask" and slot_name == "design_doc":
        return "subtask_design"
    if entity_type == "module" and slot_name == "design":
        return "module_design"
    return "module_doc"


def _get_cell(header_index: dict[str, int], row: list[str], key: str) -> str:
    index = header_index.get(key, -1)
    if index < 0 or index >= len(row):
        return ""
    return row[index]


def _parse_affected_entities(value: str) -> dict[str, list[str]]:
    modules: set[str] = set()
    subtasks: set[str] = set()
    if not isinstance(value, str):
        return {"modules": [], "subtasks": []}
    normalized = re.sub(r"[、,，;；/|]\s*", " ", value.strip())
    for token in [item.strip() for item in normalized.split() if item.strip()]:
        if re.fullmatch(r"M\d{2}-M\d{2}", token):
            start = int(token[1:3])
            end = int(token[5:7])
            for number in range(start, end + 1):
                modules.add(f"M{number:02d}")
        elif re.fullmatch(r"M\d{2}", token):
            modules.add(token)
        elif re.fullmatch(r"ST\d{2}_\d{2}", token):
            subtasks.add(token)
    return {"modules": sorted(modules), "subtasks": sorted(subtasks)}


def _parse_module_dependencies(value: str) -> list[str]:
    if not isinstance(value, str):
        return []
    normalized = value.strip()
    if normalized in {"", "-"}:
        return []
    normalized = re.sub(r"[、,，;；/|]\s*", " ", normalized)
    result: list[str] = []
    for token in [item.strip() for item in normalized.split() if item.strip()]:
        if re.fullmatch(r"M\d{2}", token):
            result.append(token)
    return result


def _clean_doc_path(value: str) -> str:
    return value.strip().strip("`").strip()


def _is_legacy_locked_row(row_map: dict[str, str]) -> bool:
    combined = " ".join(
        [
            row_map.get("Task ID", ""),
            row_map.get("实现", ""),
            row_map.get("名称", ""),
            row_map.get("状态", ""),
            row_map.get("是否具备实施条件", ""),
        ]
    ).lower()
    return "legacy" in combined or "锁定" in combined


def _row_as_dict(header_index: dict[str, int], row: list[str]) -> dict[str, str]:
    return {
        "Task ID": _get_cell(header_index, row, "task_id"),
        "名称": _get_cell(header_index, row, "name"),
        "父任务": _get_cell(header_index, row, "parent"),
        "前置依赖": _get_cell(header_index, row, "upstream"),
        "状态": _get_cell(header_index, row, "status"),
        "文档成熟度": _get_cell(header_index, row, "maturity"),
        "是否具备实施条件": _get_cell(header_index, row, "implementation_ready"),
        "对应文档路径": _get_cell(header_index, row, "path"),
    }


def _default_module_path(module_id: str) -> str:
    return f"docs/modules/{module_id}"


def _collect_doc_weak_signals(*, text: str, doc_kind: str) -> dict[str, object]:
    heading_titles = _collect_headings(text)
    sections_added = _count_added_sections(heading_titles, doc_kind)
    paragraph_ratio = _calculate_non_template_paragraph_ratio(text)
    key_fields = DOC_KIND_KEY_FIELDS.get(doc_kind, ())
    field_hits = sum(1 for field in key_fields if field in text)
    completeness = field_hits / len(key_fields) if key_fields else 0.0
    return {
        "added_section_count": sections_added,
        "non_template_paragraph_ratio": round(paragraph_ratio, 4),
        "key_fields_completeness": round(completeness, 4),
        "key_fields_hit_count": field_hits,
        "key_fields_total": len(key_fields),
    }


def _collect_headings(text: str) -> list[str]:
    headings: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        title = stripped.lstrip("#").strip()
        if title:
            headings.append(title)
    return headings


def _count_added_sections(heading_titles: list[str], doc_kind: str) -> int:
    baseline = {re.sub(r"\s+", "", item) for item in DOC_KIND_TEMPLATE_HEADINGS.get(doc_kind, set())}
    if not heading_titles:
        return 0
    count = 0
    for title in heading_titles:
        normalized = re.sub(r"\s+", "", title)
        if normalized and normalized not in baseline:
            count += 1
    return count


def _calculate_non_template_paragraph_ratio(text: str) -> float:
    paragraphs = _extract_plain_paragraphs(text)
    if not paragraphs:
        return 0.0
    non_template_count = sum(1 for paragraph in paragraphs if not _is_template_paragraph(paragraph))
    return non_template_count / len(paragraphs)


def _extract_plain_paragraphs(text: str) -> list[str]:
    chunks = re.split(r"\n\s*\n", text)
    results: list[str] = []
    for chunk in chunks:
        lines = [line.strip() for line in chunk.splitlines() if line.strip()]
        if not lines:
            continue
        if any(
            line.startswith(("#", "-", "*", "|", "```", ">"))
            or re.match(r"^\d+\.", line)
            for line in lines
        ):
            continue
        merged = " ".join(lines)
        if merged:
            results.append(merged)
    return results


def _is_template_paragraph(paragraph: str) -> bool:
    tokens = (
        "todo",
        "tbd",
        "placeholder",
        "待补充",
        "待完善",
        "示例",
        "模板",
        "xxx",
    )
    lower = paragraph.lower()
    return any(token in lower for token in tokens)
