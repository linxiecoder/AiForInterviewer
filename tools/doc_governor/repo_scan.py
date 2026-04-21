from __future__ import annotations

from pathlib import Path
import re

from .diagnostics import Diagnostic, make_diagnostic, make_evidence
from .schema import MODULE_DOC_SLOTS, SUBTASK_DOC_SLOTS
from .template_detection import detect_template_signals


MODULE_DIR_RE = re.compile(r"^(M\d{2})-")
SUBTASK_DIR_RE = re.compile(r"^(ST\d{2}_\d{2})-")
MARKDOWN_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|(?:\s*:?-+:?\s*\|)+\s*$")

OPEN_QUESTIONS_HEADERS = (
    "OQ ID",
    "问题",
    "状态",
    "关联模块",
    "当前建议",
    "需回写文档",
)
TASK_INDEX_HEADERS = (
    "Task ID",
    "名称",
    "父任务",
    "前置依赖",
    "状态",
    "文档成熟度",
    "是否具备实施条件",
    "对应文档路径",
)


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
        "modules": modules,
        "subtasks": subtasks,
        "counts": {
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

        for subtask_dir in sorted(path for path in sub_modules_dir.iterdir() if path.is_dir()):
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
                message="未找到 OPEN_QUESTIONS.md 结构化表，当前仅保留文件系统扫描结果。",
                evidence=[make_evidence(type="file_scan", path=str(path), ref="exists", value=False)],
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
                message="未找到 OPEN_QUESTIONS.md 结构化表，当前仅保留文件系统扫描结果。",
                evidence=[make_evidence(type="file_scan", path=str(path), ref="table_headers")],
            )
        )
        return {"oqs": oqs, "diagnostics": diagnostics}

    headers, rows = table
    for row_index, row in enumerate(rows, start=1):
        try:
            row_map = dict(zip(headers, row, strict=True))
            oq_id = row_map["OQ ID"].strip()
            if not oq_id:
                raise ValueError("Missing OQ ID")
            affects = _parse_affected_entities(row_map["关联模块"])
            oqs[oq_id] = {
                "title": row_map["问题"].strip(),
                "status": row_map["状态"].strip(),
                "affects": affects,
                "declared_blocker_refs": [],
            }
        except Exception as exc:  # noqa: BLE001
            diagnostics.append(
                make_diagnostic(
                    code="SCAN_OPEN_QUESTIONS_ROW_PARSE_FAILED",
                    severity="warning",
                    entity_type="oq",
                    entity_id=f"ROW-{row_index}",
                    field_path=f"OPEN_QUESTIONS.md.row[{row_index}]",
                    message=f"OPEN_QUESTIONS.md 第 {row_index} 行解析失败：{exc}",
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
                message="未找到 TASK_INDEX.md 结构化表，当前仅保留文件系统扫描结果。",
                evidence=[make_evidence(type="file_scan", path=str(path), ref="exists", value=False)],
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
                message="未找到 TASK_INDEX.md 结构化表，当前仅保留文件系统扫描结果。",
                evidence=[make_evidence(type="file_scan", path=str(path), ref="table_headers")],
            )
        )
        return {"modules": modules, "subtasks": subtasks, "diagnostics": diagnostics}

    row_counter = 0
    for headers, rows in tables:
        for row in rows:
            row_counter += 1
            try:
                row_map = dict(zip(headers, row, strict=True))
                task_id = row_map["Task ID"].strip()
                path_value = _clean_doc_path(row_map["对应文档路径"])
                if not task_id or not path_value:
                    raise ValueError("Task ID or path missing")
                if task_id.startswith("M"):
                    modules[task_id] = {
                        "path": path_value,
                        "upstream_module_ids": _parse_module_dependencies(row_map["前置依赖"]),
                        "legacy_locked": False,
                    }
                elif task_id.startswith("ST"):
                    subtasks[task_id] = {
                        "path": path_value,
                        "module_id": row_map["父任务"].strip(),
                        "upstream_module_ids": _parse_module_dependencies(row_map["前置依赖"]),
                        "legacy_locked": _is_legacy_locked_row(row_map),
                    }
            except Exception as exc:  # noqa: BLE001
                diagnostics.append(
                    make_diagnostic(
                        code="SCAN_TASK_INDEX_ROW_PARSE_FAILED",
                        severity="warning",
                        entity_type="system",
                        entity_id=f"ROW-{row_counter}",
                        field_path=f"TASK_INDEX.md.row[{row_counter}]",
                        message=f"TASK_INDEX.md 第 {row_counter} 行解析失败：{exc}",
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
            diagnostics.extend(_diagnostic_dicts_to_objects(template_diagnostics))
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
                    if module_id in oq["affects"]["modules"]
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
                    if subtask_id in oq["affects"]["subtasks"]
                ),
                "legacy_locked": bool(table_entry.get("legacy_locked", False)),
                "declared_blocker_refs": [],
                "design_doc": docs["design_doc"],
                "implementation_doc": docs["implementation_doc"],
            },
        }
    return subtasks


def _diagnostic_dicts_to_objects(items: list[dict[str, object]]) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for item in items:
        diagnostics.append(
            make_diagnostic(
                code=str(item["code"]),
                severity=str(item["severity"]),
                entity_type=str(item["entity_type"]),
                entity_id=str(item["entity_id"]),
                field_path=str(item["field_path"]),
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
    return diagnostics


def _resolve_doc_kind(*, entity_type: str, slot_name: str) -> str:
    if entity_type == "subtask" and slot_name == "implementation_doc":
        return "subtask_implementation"
    if entity_type == "subtask" and slot_name == "design_doc":
        return "subtask_design"
    if entity_type == "module" and slot_name == "design":
        return "module_design"
    return "module_doc"


def _find_markdown_table(text: str, required_headers: tuple[str, ...]) -> tuple[list[str], list[list[str]]] | None:
    tables = _find_all_markdown_tables(text, required_headers)
    return tables[0] if tables else None


def _find_all_markdown_tables(
    text: str,
    required_headers: tuple[str, ...],
) -> list[tuple[list[str], list[list[str]]]]:
    tables: list[tuple[list[str], list[list[str]]]] = []
    for block in _extract_table_blocks(text):
        headers = _split_markdown_row(block[0])
        if tuple(headers) != required_headers:
            continue
        rows: list[list[str]] = []
        for line in block[2:]:
            rows.append(_split_markdown_row(line))
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


def _parse_affected_entities(value: str) -> dict[str, list[str]]:
    modules: set[str] = set()
    subtasks: set[str] = set()
    normalized = value.replace("，", "、").replace(",", "、").replace("/", "、")
    for token in [item.strip() for item in normalized.split("、") if item.strip()]:
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
    if value.strip() in {"", "-"}:
        return []
    normalized = value.replace("，", "、").replace(",", "、")
    result: list[str] = []
    for token in [item.strip() for item in normalized.split("、") if item.strip()]:
        if re.fullmatch(r"M\d{2}", token):
            result.append(token)
    return result


def _clean_doc_path(value: str) -> str:
    return value.strip().strip("`").strip()


def _is_legacy_locked_row(row_map: dict[str, str]) -> bool:
    combined = " ".join(
        [
            row_map.get("名称", ""),
            row_map.get("文档成熟度", ""),
            row_map.get("状态", ""),
        ]
    )
    return "历史容器" in combined or "禁止直开" in combined


def _default_module_path(module_id: str) -> str:
    return f"docs/modules/{module_id}"
