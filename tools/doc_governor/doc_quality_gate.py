from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .diagnostics import Diagnostic, make_diagnostic, make_evidence

DOC_QUALITY_GATE_REPORT_PATH = "docs/governance/DOC_QUALITY_GATE_REPORT.md"
REQUIRED_FIELDS = ("Owner", "Last Updated", "Scope", "Depends On", "Supersedes")
ALLOWED_STAGE_TAGS = {"R0", "R1", "R2"}


def run_doc_quality_gate(repo_root: Path) -> dict[str, Any]:
    governance_dir = repo_root / "docs" / "governance"
    diagnostics: list[Diagnostic] = []
    docs = [
        path
        for path in governance_dir.glob("*.md")
        if path.name not in {"DOC_QUALITY_GATE_REPORT.md"}
    ]

    current_entrypoints: dict[str, list[str]] = {}
    for path in docs:
        text = path.read_text(encoding="utf-8")
        diagnostics.extend(_check_required_fields(path, text))
        diagnostics.extend(_check_links(repo_root, path, text))
        diagnostics.extend(_check_stage_tags(path, text))
        _collect_entrypoint_topics(path, text, current_entrypoints)

    for topic, holders in current_entrypoints.items():
        if len(holders) > 1:
            diagnostics.append(
                make_diagnostic(
                    code="DOC_GATE_DUPLICATE_CURRENT_ENTRY",
                    severity="error",
                    entity_type="document",
                    entity_id=topic,
                    field_path="entrypoint.current",
                    message=f"同一主题存在多个当前入口: {topic}",
                    evidence=[
                        make_evidence(
                            type="file_scan",
                            path="docs/governance",
                            ref="duplicate_current_entry",
                            value=holders,
                        )
                    ],
                )
            )

    has_error = any(item.severity == "error" for item in diagnostics)
    report_path = repo_root / DOC_QUALITY_GATE_REPORT_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_report(diagnostics, docs), encoding="utf-8")
    return {
        "ok": not has_error,
        "report_path": report_path.as_posix(),
        "diagnostics": diagnostics,
    }


def _check_required_fields(path: Path, text: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for field in REQUIRED_FIELDS:
        if re.search(rf"^\s*-?\s*{re.escape(field)}\s*:", text, re.MULTILINE) is None:
            diagnostics.append(
                make_diagnostic(
                    code="DOC_GATE_REQUIRED_FIELD_MISSING",
                    severity="error",
                    entity_type="document",
                    entity_id=path.name,
                    field_path=f"metadata.{field}",
                    message=f"缺少必填字段: {field}",
                    evidence=[make_evidence(type="file_scan", path=path.as_posix(), ref=field, value=None)],
                )
            )
    return diagnostics


def _check_links(repo_root: Path, path: Path, text: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        if link.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = (path.parent / link).resolve()
        if not target.exists():
            diagnostics.append(make_diagnostic(code="DOC_GATE_BROKEN_LINK", severity="error", entity_type="document", entity_id=path.name, field_path="links", message=f"失效链接: {link}", evidence=[make_evidence(type="file_scan", path=path.as_posix(), ref="link", value=link)]))
            continue
        if ".." in Path(link).parts:
            diagnostics.append(make_diagnostic(code="DOC_GATE_CROSS_LEVEL_REFERENCE", severity="error", entity_type="document", entity_id=path.name, field_path="links", message=f"检测到跨层误引用: {link}", evidence=[make_evidence(type="file_scan", path=path.as_posix(), ref="link", value=link)]))
    return diagnostics


def _check_stage_tags(path: Path, text: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    found = set(re.findall(r"\bR[0-9]+\b", text))
    invalid = sorted(tag for tag in found if tag not in ALLOWED_STAGE_TAGS)
    for tag in invalid:
        diagnostics.append(make_diagnostic(code="DOC_GATE_STAGE_TAG_INVALID", severity="error", entity_type="document", entity_id=path.name, field_path="stage_tag", message=f"阶段标签不在统一模型中: {tag}", evidence=[make_evidence(type="file_scan", path=path.as_posix(), ref="stage_tag", value=tag)]))
    return diagnostics


def _collect_entrypoint_topics(path: Path, text: str, mapping: dict[str, list[str]]) -> None:
    for topic in re.findall(r"当前入口\s*[:：]\s*([^\n]+)", text):
        mapping.setdefault(topic.strip(), []).append(path.name)


def _render_report(diagnostics: list[Diagnostic], docs: list[Path]) -> str:
    lines = ["# 文档质量门禁报告", "", f"- 扫描文档数: {len(docs)}", f"- 诊断数: {len(diagnostics)}", ""]
    if not diagnostics:
        lines.append("门禁通过：未发现错误。")
    else:
        lines.append("门禁未通过：存在以下问题。")
        lines.append("")
        for item in diagnostics:
            lines.append(f"- [{item.severity}] {item.code} | {item.entity_id} | {item.message}")
    lines.append("")
    lines.append("规则：门禁未通过时，不得进入下一窗口。")
    return "\n".join(lines) + "\n"
