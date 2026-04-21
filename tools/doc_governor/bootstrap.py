from __future__ import annotations

from pathlib import Path
from typing import Any

from .diagnostics import Diagnostic, make_diagnostic, make_evidence
from .schema import (
    BOOTSTRAP_REPORT_PATH,
    BOOTSTRAP_STATE_PATH,
    GLOBAL_POLICY_DEFAULTS,
    OFFICIAL_STATE_PATH,
    SCHEMA_VERSION,
    make_default_confirmed_state,
)


def build_bootstrap_state(scan_result: dict[str, object]) -> tuple[dict[str, object], list[Diagnostic]]:
    diagnostics = list(scan_result["diagnostics"])
    state: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "global_policy": GLOBAL_POLICY_DEFAULTS,
        "oqs": scan_result["oqs"],
        "modules": {},
        "subtasks": {},
    }

    for module_id, module in scan_result["modules"].items():
        state["modules"][module_id] = {
            "meta": {"path": module["meta"]["path"]},
            "facts": module["facts"],
            "state": {"confirmed": make_default_confirmed_state("module")},
        }

    ambiguous_subtasks: list[str] = []
    for subtask_id, subtask in scan_result["subtasks"].items():
        confirmed_state = make_default_confirmed_state("subtask")
        implementation_doc = subtask["facts"]["implementation_doc"]
        if implementation_doc["exists"] and implementation_doc["template_like"]:
            confirmed_state["implementation_doc_state"] = "inactive_template"
        state["subtasks"][subtask_id] = {
            "meta": subtask["meta"],
            "facts": subtask["facts"],
            "state": {"confirmed": confirmed_state},
        }
        if implementation_doc["exists"] and not implementation_doc["template_like"]:
            ambiguous_subtasks.append(subtask_id)
            diagnostics.append(
                make_diagnostic(
                    code="BOOTSTRAP_IMPL_DOC_STATE_AMBIGUOUS",
                    severity="error",
                    entity_type="subtask",
                    entity_id=subtask_id,
                    field_path=f"subtasks.{subtask_id}.facts.implementation_doc",
                    message="检测到存在但非模板化的实施文档；Phase 1A 不允许自动将其导入为真值。",
                    evidence=[
                        make_evidence(
                            type="file_scan",
                            path=subtask["meta"]["path"],
                            ref="implementation_doc.exists/template_like",
                            value="exists=true, template_like=false",
                        )
                    ],
                )
            )

    return state, diagnostics


def render_bootstrap_report(
    *,
    scan_result: dict[str, object],
    diagnostics: list[Diagnostic],
    output_path: Path,
    report_path: Path,
) -> str:
    template_docs = _collect_template_like_docs(scan_result)
    ambiguous_impl_docs = _collect_ambiguous_implementation_docs(scan_result)
    counts = scan_result["counts"]
    lines = [
        "# Bootstrap Report",
        "",
        "## Summary",
        "",
        f"- repo_root: `{Path(scan_result['repo_root']).as_posix()}`",
        f"- output_path: `{output_path.as_posix()}`",
        f"- report_path: `{report_path.as_posix()}`",
        f"- diagnostics: error={sum(1 for item in diagnostics if item.severity == 'error')}, warning={sum(1 for item in diagnostics if item.severity == 'warning')}",
        "",
        "## Scan counts",
        "",
        f"- modules: {counts['module']}",
        f"- subtasks: {counts['subtask']}",
        f"- oqs: {counts['oq']}",
        f"- template_like_docs: {counts['template_like_doc']}",
        "",
        "## Detected template-like docs",
        "",
    ]
    if template_docs:
        lines.extend(f"- `{item}`" for item in template_docs)
    else:
        lines.append("- none")

    lines.extend(["", "## Ambiguous implementation docs", ""])
    if ambiguous_impl_docs:
        lines.extend(f"- `{item}`" for item in ambiguous_impl_docs)
    else:
        lines.append("- none")

    lines.extend(["", "## Diagnostics snapshot", ""])
    if diagnostics:
        for diagnostic in diagnostics[:10]:
            lines.append(
                f"- `{diagnostic.code}` [{diagnostic.severity}] {diagnostic.entity_type}:{diagnostic.entity_id} -> {diagnostic.message}"
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def write_bootstrap_outputs(
    *,
    state: dict[str, object],
    diagnostics: list[Diagnostic],
    scan_result: dict[str, object],
    output_path: Path,
    report_path: Path,
    yaml_module: Any,
    overwrite: bool,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_text = render_bootstrap_report(
        scan_result=scan_result,
        diagnostics=diagnostics,
        output_path=output_path,
        report_path=report_path,
    )
    yaml_text = yaml_module.safe_dump(
        state,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )
    output_path.write_text(yaml_text, encoding="utf-8")
    report_path.write_text(report_text, encoding="utf-8")


def resolve_output_paths(
    *,
    repo_root: Path,
    output: str | None = None,
    report: str | None = None,
) -> tuple[Path, Path]:
    output_path = (repo_root / (output or BOOTSTRAP_STATE_PATH)).resolve()
    report_path = (repo_root / (report or BOOTSTRAP_REPORT_PATH)).resolve()
    return output_path, report_path


def ensure_writable_bootstrap_targets(
    *,
    repo_root: Path,
    output_path: Path,
    report_path: Path,
    overwrite: bool,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    official_state = (repo_root / OFFICIAL_STATE_PATH).resolve()
    if output_path == official_state or report_path == official_state:
        diagnostics.append(
            make_diagnostic(
                code="BOOTSTRAP_OFFICIAL_STATE_WRITE_FORBIDDEN",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="docs/governance/DOC_STATE.yaml",
                message="Phase 1A bootstrap 不允许写入或覆盖正式 DOC_STATE.yaml。",
                evidence=[
                    make_evidence(
                        type="derived_check",
                        path=official_state.as_posix(),
                        ref="official_state_path",
                        value=output_path.as_posix(),
                    )
                ],
            )
        )
        return diagnostics

    existing_targets = [target for target in (output_path, report_path) if target.exists()]
    if existing_targets and not overwrite:
        diagnostics.append(
            make_diagnostic(
                code="BOOTSTRAP_OUTPUT_EXISTS",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="bootstrap.outputs",
                message="bootstrap 输出文件已存在；如需覆盖，必须显式传入 --overwrite。",
                evidence=[
                    make_evidence(
                        type="file_scan",
                        path=target.as_posix(),
                        ref="exists",
                        value=True,
                    )
                    for target in existing_targets
                ],
            )
        )
    return diagnostics


def _collect_template_like_docs(scan_result: dict[str, object]) -> list[str]:
    docs: list[str] = []
    for module_id, module in scan_result["modules"].items():
        for slot_name, slot in module["facts"]["docs"].items():
            if slot["template_like"]:
                docs.append(f"{module['meta']['path']}#{slot_name}")
    for subtask_id, subtask in scan_result["subtasks"].items():
        if subtask["facts"]["design_doc"]["template_like"]:
            docs.append(f"{subtask['meta']['path']}#design_doc")
        if subtask["facts"]["implementation_doc"]["template_like"]:
            docs.append(f"{subtask['meta']['path']}#implementation_doc")
    return sorted(docs)


def _collect_ambiguous_implementation_docs(scan_result: dict[str, object]) -> list[str]:
    docs: list[str] = []
    for subtask in scan_result["subtasks"].values():
        implementation_doc = subtask["facts"]["implementation_doc"]
        if implementation_doc["exists"] and not implementation_doc["template_like"]:
            docs.append(f"{subtask['meta']['path']}#implementation_doc")
    return sorted(docs)
