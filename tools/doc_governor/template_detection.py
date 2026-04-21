from __future__ import annotations

import re

from .diagnostics import Diagnostic, make_diagnostic, make_evidence


PLACEHOLDER_RE = re.compile(r"\$\([^)]+\)|\$\{[^}]+\}")
EMPTY_FIELD_RE = re.compile(r"^- [^:：]+[：:]\s*$")
EMPTY_BULLET_RE = re.compile(r"^-+\s*$")


def detect_template_signals(
    *,
    path: str,
    text: str,
    doc_kind: str,
) -> tuple[bool, list[dict[str, object]]]:
    diagnostics: list[Diagnostic] = []
    template_like = False

    placeholder_diagnostics = detect_placeholder_residue(path=path, text=text)
    if placeholder_diagnostics:
        template_like = True
        diagnostics.extend(placeholder_diagnostics)

    if doc_kind == "subtask_implementation":
        implementation_like, implementation_diagnostics = detect_implementation_template(
            path=path,
            text=text,
        )
        template_like = template_like or implementation_like
        diagnostics.extend(implementation_diagnostics)

    return template_like, [diagnostic_to_dict(item) for item in diagnostics]


def detect_placeholder_residue(*, path: str, text: str) -> list[Diagnostic]:
    match = PLACEHOLDER_RE.search(text)
    if match is None:
        return []
    return [
        make_diagnostic(
            code="TEMPLATE_PLACEHOLDER_RESIDUE",
            severity="warning",
            entity_type="doc_slot",
            entity_id=path,
            field_path="facts.docs",
            message="文档中存在变量/占位符残留，当前内容不能视为真实成熟输入。",
            evidence=[
                make_evidence(
                    type="file_scan",
                    path=path,
                    ref="placeholder",
                    value=match.group(0),
                    snippet=match.group(0),
                )
            ],
        )
    ]


def detect_implementation_template(*, path: str, text: str) -> tuple[bool, list[Diagnostic]]:
    diagnostics: list[Diagnostic] = []
    empty_field_count = _count_empty_field_lines(text)
    looks_uniform = _looks_like_uniform_implementation_template(text, empty_field_count)
    looks_empty = _looks_like_empty_implementation_template(text, empty_field_count)

    if looks_empty:
        diagnostics.append(
            make_diagnostic(
                code="TEMPLATE_EMPTY_SUBTASK_IMPLEMENTATION",
                severity="warning",
                entity_type="doc_slot",
                entity_id=path,
                field_path="facts.implementation_doc",
                message="子任务实施文档仍是空模板，不能作为 readiness 证据。",
                evidence=[
                    make_evidence(
                        type="file_scan",
                        path=path,
                        ref="empty_field_count",
                        value=empty_field_count,
                    )
                ],
            )
        )

    if looks_uniform:
        diagnostics.append(
            make_diagnostic(
                code="TEMPLATE_UNIFORM_IMPLEMENTATION_TEMPLATE",
                severity="warning",
                entity_type="doc_slot",
                entity_id=path,
                field_path="facts.implementation_doc",
                message="子任务实施文档保留统一模板骨架，当前不应视为已激活工作文档。",
                evidence=[
                    make_evidence(
                        type="file_scan",
                        path=path,
                        ref="uniform_template_markers",
                        value="subtask_implementation_template",
                    )
                ],
            )
        )

    return bool(diagnostics), diagnostics


def _count_empty_field_lines(text: str) -> int:
    count = 0
    for line in text.splitlines():
        stripped = line.strip()
        if EMPTY_FIELD_RE.match(stripped):
            count += 1
        elif EMPTY_BULLET_RE.match(stripped):
            count += 1
    return count


def _looks_like_uniform_implementation_template(text: str, empty_field_count: int) -> bool:
    required_markers = (
        "# 子任务实施文档",
        "## 2. 基本信息",
        "## 9. 实施步骤",
        "## 10. 当前成熟度评估",
    )
    present_markers = sum(marker in text for marker in required_markers)
    has_generic_status_line = "draft / reviewable / implementation-ready / blocked" in text
    return present_markers >= 3 and (has_generic_status_line or empty_field_count >= 12)


def _looks_like_empty_implementation_template(text: str, empty_field_count: int) -> bool:
    required_markers = (
        "# 子任务实施文档",
        "- 子任务 ID：",
        "- 子任务名称：",
        "- 所属模块：",
        "- 当前成熟度：",
        "### Step 1",
    )
    present_markers = sum(marker in text for marker in required_markers)
    return present_markers >= 5 and empty_field_count >= 12


def diagnostic_to_dict(diagnostic: Diagnostic) -> dict[str, object]:
    return {
        "code": diagnostic.code,
        "severity": diagnostic.severity,
        "entity_type": diagnostic.entity_type,
        "entity_id": diagnostic.entity_id,
        "field_path": diagnostic.field_path,
        "message": diagnostic.message,
        "evidence": [
            {
                "type": item.type,
                "path": item.path,
                "ref": item.ref,
                "value": item.value,
                "line": item.line,
                "snippet": item.snippet,
            }
            for item in diagnostic.evidence
        ],
    }
