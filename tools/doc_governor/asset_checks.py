from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re

from .artifact_policy import ArtifactPolicy, AssetSlot, build_default_artifact_policy
from .diagnostics import Diagnostic, make_diagnostic, make_evidence
from .template_detection import detect_template_signals


MARKDOWN_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|(?:\s*:?-+:?\s*\|)+\s*$")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*$")

_TEMPLATE_CODE_MAP = {
    "TEMPLATE_PLACEHOLDER_RESIDUE": "ASSET_TEMPLATE_PLACEHOLDER_RESIDUE",
    "TEMPLATE_EMPTY_SUBTASK_IMPLEMENTATION": "ASSET_TEMPLATE_EMPTY_IMPLEMENTATION",
    "TEMPLATE_UNIFORM_IMPLEMENTATION_TEMPLATE": "ASSET_TEMPLATE_UNIFORM_IMPLEMENTATION",
}


@dataclass(frozen=True)
class _ModuleRecord:
    module_id: str
    path: Path
    relative_path: str


@dataclass(frozen=True)
class _SubtaskRecord:
    subtask_id: str
    module_id: str
    path: Path
    relative_path: str


def check_repo_assets(
    repo_root: str | Path,
    *,
    policy: ArtifactPolicy | None = None,
) -> list[Diagnostic]:
    root = Path(repo_root).resolve()
    active_policy = policy or build_default_artifact_policy()
    diagnostics: list[Diagnostic] = []

    diagnostics.extend(_check_required_root_docs(root, active_policy))
    modules, subtasks, discovery_diagnostics = _discover_assets(root, active_policy)
    diagnostics.extend(discovery_diagnostics)

    module_index = _parse_index(
        root / active_policy.module_index_file,
        id_headers=active_policy.module_index_id_headers,
        path_headers=active_policy.module_index_path_headers,
    )
    diagnostics.extend(_check_index_entries(root, module_index, index_file=active_policy.module_index_file))
    diagnostics.extend(_check_module_index(root, modules, module_index, active_policy.module_index_file))

    subtasks_by_module: dict[str, dict[str, _SubtaskRecord]] = {}
    for subtask in subtasks.values():
        subtasks_by_module.setdefault(subtask.module_id, {})[subtask.subtask_id] = subtask

    for module_id, module in modules.items():
        subtask_index = _parse_index(
            module.path / active_policy.subtask_index_file,
            id_headers=active_policy.subtask_index_id_headers,
            path_headers=active_policy.subtask_index_path_headers,
            parent_headers=active_policy.subtask_index_parent_headers,
        )
        diagnostics.extend(
            _check_subtask_index(
                root=root,
                module=module,
                indexed_rows=subtask_index,
                actual_rows=subtasks_by_module.get(module_id, {}),
                index_filename=active_policy.subtask_index_file,
            )
        )

    return diagnostics


def _check_required_root_docs(root: Path, policy: ArtifactPolicy) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for relative_path in policy.required_root_docs:
        if _is_ignored(relative_path, policy):
            continue
        path = root / relative_path
        if path.exists():
            continue
        diagnostics.append(
            make_diagnostic(
                code="ASSET_REQUIRED_DOC_MISSING",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path=f"required_root_docs.{relative_path}",
                message=f"缺少必需文档：{relative_path}",
                evidence=[
                    make_evidence(
                        type="file_scan",
                        path=relative_path,
                        ref="exists",
                        value=False,
                    )
                ],
            )
        )
    return diagnostics


def _discover_assets(
    root: Path,
    policy: ArtifactPolicy,
) -> tuple[dict[str, _ModuleRecord], dict[str, _SubtaskRecord], list[Diagnostic]]:
    diagnostics: list[Diagnostic] = []
    modules: dict[str, _ModuleRecord] = {}
    subtasks: dict[str, _SubtaskRecord] = {}
    modules_root = root / policy.modules_root
    if not modules_root.exists():
        return modules, subtasks, diagnostics

    for module_dir in sorted(path for path in modules_root.iterdir() if path.is_dir()):
        module_relative = module_dir.relative_to(root).as_posix()
        if _is_ignored(module_relative, policy):
            continue
        module_match = policy.module_dir_pattern.match(module_dir.name)
        if module_match is None:
            diagnostics.append(
                _path_diagnostic(
                    code="ASSET_INVALID_MODULE_DIR_NAME",
                    severity="warning",
                    entity_type="module",
                    entity_id=module_dir.name,
                    field_path="meta.path",
                    message="模块目录命名不符合 `Mxx-slug` 规则。",
                    relative_path=module_relative,
                )
            )
            continue

        module_id = module_match.group(1)
        modules[module_id] = _ModuleRecord(
            module_id=module_id,
            path=module_dir,
            relative_path=module_relative,
        )
        diagnostics.extend(
            _check_doc_slots(
                root=root,
                base_dir=module_dir,
                entity_type="module",
                entity_id=module_id,
                slots=policy.module_slots,
            )
        )

        sub_modules_dir = module_dir / "sub_modules"
        if not sub_modules_dir.exists():
            continue

        for subtask_dir in sorted(path for path in sub_modules_dir.iterdir() if path.is_dir()):
            subtask_relative = subtask_dir.relative_to(root).as_posix()
            if _is_ignored(subtask_relative, policy):
                continue
            subtask_match = policy.subtask_dir_pattern.match(subtask_dir.name)
            if subtask_match is None:
                diagnostics.append(
                    _path_diagnostic(
                        code="ASSET_INVALID_SUBTASK_DIR_NAME",
                        severity="warning",
                        entity_type="subtask",
                        entity_id=subtask_dir.name,
                        field_path="meta.path",
                        message="子任务目录命名不符合 `STxx_xx-slug` 规则。",
                        relative_path=subtask_relative,
                    )
                )
                continue

            subtask_id = subtask_match.group(1)
            subtasks[subtask_id] = _SubtaskRecord(
                subtask_id=subtask_id,
                module_id=module_id,
                path=subtask_dir,
                relative_path=subtask_relative,
            )
            diagnostics.extend(
                _check_doc_slots(
                    root=root,
                    base_dir=subtask_dir,
                    entity_type="subtask",
                    entity_id=subtask_id,
                    slots=policy.subtask_slots,
                )
            )

    return modules, subtasks, diagnostics


def _check_doc_slots(
    *,
    root: Path,
    base_dir: Path,
    entity_type: str,
    entity_id: str,
    slots: dict[str, AssetSlot],
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for slot_name, slot in slots.items():
        doc_path = base_dir / slot.filename
        relative_path = doc_path.relative_to(root).as_posix()
        field_path = f"assets.{slot_name}"
        if not doc_path.exists():
            diagnostics.append(
                make_diagnostic(
                    code="ASSET_REQUIRED_DOC_MISSING",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=field_path,
                    message=f"缺少必需文档：{slot.filename}",
                    evidence=[
                        make_evidence(
                            type="file_scan",
                            path=relative_path,
                            ref="exists",
                            value=False,
                        )
                    ],
                )
            )
            continue

        text = doc_path.read_text(encoding="utf-8")
        diagnostics.extend(
            _check_required_headings(
                path=relative_path,
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=field_path,
                required_headings=slot.required_headings,
                text=text,
            )
        )
        diagnostics.extend(
            _convert_template_diagnostics(
                path=relative_path,
                field_path=field_path,
                diagnostics_payload=detect_template_signals(
                    path=relative_path,
                    text=text,
                    doc_kind=slot.doc_kind,
                )[1],
            )
        )
    return diagnostics


def _check_required_headings(
    *,
    path: str,
    entity_type: str,
    entity_id: str,
    field_path: str,
    required_headings: tuple[str, ...],
    text: str,
) -> list[Diagnostic]:
    if not required_headings:
        return []

    headings = _extract_heading_texts(text)
    diagnostics: list[Diagnostic] = []
    for heading in required_headings:
        if any(heading in item for item in headings):
            continue
        diagnostics.append(
            make_diagnostic(
                code="ASSET_REQUIRED_HEADING_MISSING",
                severity="warning",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=field_path,
                message=f"文档缺少必需标题：{heading}",
                evidence=[
                    make_evidence(
                        type="heading_scan",
                        path=path,
                        ref="required_heading",
                        value=heading,
                    )
                ],
            )
        )
    return diagnostics


def _extract_heading_texts(text: str) -> list[str]:
    headings: list[str] = []
    in_code_fence = False
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        match = HEADING_RE.match(raw_line)
        if match is None:
            continue
        headings.append(match.group(1).strip())
    return headings


def _convert_template_diagnostics(
    *,
    path: str,
    field_path: str,
    diagnostics_payload: list[dict[str, object]],
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for item in diagnostics_payload:
        evidence = item.get("evidence") or []
        diagnostics.append(
            make_diagnostic(
                code=_TEMPLATE_CODE_MAP.get(str(item["code"]), "ASSET_TEMPLATE_SIGNAL"),
                severity=str(item["severity"]),
                entity_type="doc",
                entity_id=path,
                field_path=field_path,
                message=str(item["message"]),
                evidence=[
                    make_evidence(
                        type=str(entry["type"]),
                        path=str(entry["path"]),
                        ref=str(entry["ref"]),
                        value=entry.get("value"),
                        line=entry.get("line"),
                        snippet=entry.get("snippet"),
                    )
                    for entry in evidence
                ],
            )
        )
    return diagnostics


def _parse_index(
    path: Path,
    *,
    id_headers: tuple[str, ...],
    path_headers: tuple[str, ...],
    parent_headers: tuple[str, ...] = (),
) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}

    table = _find_table(
        path.read_text(encoding="utf-8"),
        required_headers=id_headers + path_headers,
    )
    if table is None:
        return {}

    headers, rows = table
    header_index = _build_header_index(headers, id_headers, path_headers, parent_headers)
    results: dict[str, dict[str, str]] = {}
    for row in rows:
        item_id = _get_cell(header_index, row, "id").strip()
        if not item_id:
            continue
        results[item_id] = {
            "path": _clean_doc_path(_get_cell(header_index, row, "path")),
            "parent": _get_cell(header_index, row, "parent").strip(),
        }
    return results


def _check_index_entries(
    root: Path,
    rows: dict[str, dict[str, str]],
    *,
    index_file: str,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for item_id, entry in rows.items():
        path_value = entry.get("path", "")
        if not path_value:
            continue
        if (root / path_value).exists():
            continue
        diagnostics.append(
            make_diagnostic(
                code="ASSET_INDEX_PATH_MISSING",
                severity="warning",
                entity_type="index",
                entity_id=item_id,
                field_path=f"indexes.{index_file}",
                message=f"索引中的路径不存在：{path_value}",
                evidence=[
                    make_evidence(
                        type="table_row",
                        path=index_file,
                        ref="path",
                        value=path_value,
                    )
                ],
            )
        )
    return diagnostics


def _check_module_index(
    root: Path,
    modules: dict[str, _ModuleRecord],
    indexed_rows: dict[str, dict[str, str]],
    index_file: str,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for module_id, module in modules.items():
        entry = indexed_rows.get(module_id)
        if entry is None:
            diagnostics.append(
                make_diagnostic(
                    code="ASSET_ORPHAN_MODULE_DIR",
                    severity="warning",
                    entity_type="module",
                    entity_id=module_id,
                    field_path=f"indexes.{index_file}",
                    message="模块目录存在，但未被父级模块索引登记。",
                    evidence=[
                        make_evidence(
                            type="file_scan",
                            path=module.relative_path,
                            ref="indexed",
                            value=False,
                        )
                    ],
                )
            )
            continue
        indexed_path = entry.get("path", "")
        if indexed_path and _normalize_path(indexed_path) != module.relative_path:
            diagnostics.append(
                make_diagnostic(
                    code="ASSET_INDEX_PATH_MISMATCH",
                    severity="warning",
                    entity_type="module",
                    entity_id=module_id,
                    field_path=f"indexes.{index_file}",
                    message="模块索引记录的路径与实际目录不一致。",
                    evidence=[
                        make_evidence(
                            type="table_row",
                            path=index_file,
                            ref="path",
                            value={"indexed": indexed_path, "actual": module.relative_path},
                        )
                    ],
                )
            )
    return diagnostics


def _check_subtask_index(
    *,
    root: Path,
    module: _ModuleRecord,
    indexed_rows: dict[str, dict[str, str]],
    actual_rows: dict[str, _SubtaskRecord],
    index_filename: str,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    index_file = f"{module.relative_path}/{index_filename}"

    diagnostics.extend(_check_index_entries(root, indexed_rows, index_file=index_file))

    for subtask_id, subtask in actual_rows.items():
        entry = indexed_rows.get(subtask_id)
        if entry is None:
            diagnostics.append(
                make_diagnostic(
                    code="ASSET_ORPHAN_SUBTASK_DIR",
                    severity="warning",
                    entity_type="subtask",
                    entity_id=subtask_id,
                    field_path=f"indexes.{index_file}",
                    message="子任务目录存在，但未被父级任务索引登记。",
                    evidence=[
                        make_evidence(
                            type="file_scan",
                            path=subtask.relative_path,
                            ref="indexed",
                            value=False,
                        )
                    ],
                )
            )
            continue

        parent_value = entry.get("parent", "")
        if parent_value and parent_value != module.module_id:
            diagnostics.append(
                make_diagnostic(
                    code="ASSET_SUBTASK_PARENT_MISMATCH",
                    severity="error",
                    entity_type="subtask",
                    entity_id=subtask_id,
                    field_path=f"indexes.{index_file}",
                    message="子任务索引中的父模块与目录归属不一致。",
                    evidence=[
                        make_evidence(
                            type="table_row",
                            path=index_file,
                            ref="parent",
                            value={"indexed": parent_value, "actual": module.module_id},
                        )
                    ],
                )
            )

        indexed_path = entry.get("path", "")
        if indexed_path and _normalize_path(indexed_path) != subtask.relative_path:
            diagnostics.append(
                make_diagnostic(
                    code="ASSET_INDEX_PATH_MISMATCH",
                    severity="warning",
                    entity_type="subtask",
                    entity_id=subtask_id,
                    field_path=f"indexes.{index_file}",
                    message="子任务索引记录的路径与实际目录不一致。",
                    evidence=[
                        make_evidence(
                            type="table_row",
                            path=index_file,
                            ref="path",
                            value={"indexed": indexed_path, "actual": subtask.relative_path},
                        )
                    ],
                )
            )

    return diagnostics


def _find_table(
    text: str,
    *,
    required_headers: tuple[str, ...],
) -> tuple[list[str], list[list[str]]] | None:
    normalized_required = {_normalize_header(item) for item in required_headers}
    current: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            current.append(line)
            continue
        if current:
            table = _consume_table_block(current, normalized_required)
            if table is not None:
                return table
            current = []
    if current:
        return _consume_table_block(current, normalized_required)
    return None


def _consume_table_block(
    lines: list[str],
    normalized_required: set[str],
) -> tuple[list[str], list[list[str]]] | None:
    if len(lines) < 2 or not MARKDOWN_TABLE_SEPARATOR_RE.match(lines[1]):
        return None
    headers = _split_markdown_row(lines[0])
    normalized_headers = {_normalize_header(item) for item in headers}
    if not normalized_required.issubset(normalized_headers):
        return None
    rows = [_split_markdown_row(line) for line in lines[2:]]
    return headers, rows


def _build_header_index(
    headers: list[str],
    id_headers: tuple[str, ...],
    path_headers: tuple[str, ...],
    parent_headers: tuple[str, ...],
) -> dict[str, int]:
    normalized = {_normalize_header(value): index for index, value in enumerate(headers)}
    mapping: dict[str, int] = {}
    for alias in id_headers:
        if _normalize_header(alias) in normalized:
            mapping["id"] = normalized[_normalize_header(alias)]
            break
    for alias in path_headers:
        if _normalize_header(alias) in normalized:
            mapping["path"] = normalized[_normalize_header(alias)]
            break
    for alias in parent_headers:
        if _normalize_header(alias) in normalized:
            mapping["parent"] = normalized[_normalize_header(alias)]
            break
    mapping.setdefault("parent", -1)
    return mapping


def _get_cell(header_index: dict[str, int], row: list[str], key: str) -> str:
    index = header_index.get(key, -1)
    if index < 0 or index >= len(row):
        return ""
    return row[index]


def _split_markdown_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _normalize_header(value: str) -> str:
    return value.strip().lower().replace("_", "").replace(" ", "")


def _clean_doc_path(value: str) -> str:
    return value.strip().strip("`").rstrip("/").replace("\\", "/")


def _normalize_path(value: str) -> str:
    return _clean_doc_path(value)


def _path_diagnostic(
    *,
    code: str,
    severity: str,
    entity_type: str,
    entity_id: str,
    field_path: str,
    message: str,
    relative_path: str,
) -> Diagnostic:
    return make_diagnostic(
        code=code,
        severity=severity,
        entity_type=entity_type,
        entity_id=entity_id,
        field_path=field_path,
        message=message,
        evidence=[
            make_evidence(
                type="file_scan",
                path=relative_path,
                ref="path",
                value=relative_path,
            )
        ],
    )


def _is_ignored(relative_path: str, policy: ArtifactPolicy) -> bool:
    pure_path = PurePosixPath(relative_path)
    return any(pure_path.match(pattern) for pattern in policy.ignored_path_globs)
