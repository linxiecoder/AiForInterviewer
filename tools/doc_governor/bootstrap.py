from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .diagnostics import Diagnostic, make_diagnostic, make_evidence
from .schema import (
    BOOTSTRAP_REPORT_PATH,
    BOOTSTRAP_STATE_PATH,
    OQ_DEFAULT_POLICY_SOURCE,
    OQ_DEFAULT_GATE_LEVEL,
    OQ_DEFAULT_RESOLUTION_POLICY,
    OQ_POLICY_SOURCE_BOOTSTRAP_DEFAULT,
    OQ_POLICY_SOURCE_EXPLICIT,
    GLOBAL_POLICY_DEFAULTS,
    OFFICIAL_STATE_PATH,
    SCHEMA_VERSION,
    make_default_compliance_state,
    make_default_confirmed_state,
    make_default_tracking_state,
)


def build_bootstrap_state(scan_result: dict[str, object]) -> tuple[dict[str, object], list[Diagnostic]]:
    diagnostics = list(scan_result["diagnostics"])
    oqs, oq_default_diagnostics = _normalize_oq_policy_fields(scan_result["oqs"])
    diagnostics.extend(oq_default_diagnostics)
    module_requirement_ids = _resolve_requirement_relations(
        scan_result=scan_result,
        relation_key="module_requirement_ids",
        fact_field="module_ids",
    )
    subtask_requirement_ids = _resolve_requirement_relations(
        scan_result=scan_result,
        relation_key="subtask_requirement_ids",
        fact_field="task_ids",
    )

    state: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "global_policy": copy.deepcopy(GLOBAL_POLICY_DEFAULTS),
        "oqs": oqs,
        "requirements": {},
        "modules": {},
        "subtasks": {},
    }

    for requirement_id, requirement in scan_result.get("requirements", {}).items():
        requirement_meta = requirement.get("meta", {})
        requirement_facts = dict(requirement.get("facts", {}))
        requirement_facts.setdefault("compliance", make_default_compliance_state())
        state["requirements"][requirement_id] = {
            "meta": dict(requirement_meta),
            "facts": requirement_facts,
            "state": {
                "confirmed": make_default_confirmed_state("requirement"),
                "tracking": make_default_tracking_state(),
            },
        }

    for module_id, module in scan_result["modules"].items():
        module_facts = dict(module["facts"])
        module_facts.setdefault("compliance", make_default_compliance_state())
        requirement_ids = list(module_requirement_ids.get(str(module_id), []))
        if requirement_ids:
            module_facts["requirement_ids"] = requirement_ids
        module_meta = {"path": module["meta"]["path"]}
        if len(requirement_ids) == 1:
            module_meta["requirement_id"] = requirement_ids[0]
        state["modules"][module_id] = {
            "meta": module_meta,
            "facts": module_facts,
            "state": {
                "confirmed": make_default_confirmed_state("module"),
                "tracking": make_default_tracking_state(),
            },
        }

    ambiguous_subtasks: list[str] = []
    for subtask_id, subtask in scan_result["subtasks"].items():
        confirmed_state = make_default_confirmed_state("subtask")
        subtask_facts = dict(subtask["facts"])
        subtask_facts.setdefault("compliance", make_default_compliance_state())
        requirement_ids = list(subtask_requirement_ids.get(str(subtask_id), []))
        if requirement_ids:
            subtask_facts["requirement_ids"] = requirement_ids
        implementation_doc = subtask_facts["implementation_doc"]
        subtask_meta = dict(subtask["meta"])
        if len(requirement_ids) == 1:
            subtask_meta["requirement_id"] = requirement_ids[0]
        if implementation_doc["exists"] and implementation_doc["template_like"]:
            confirmed_state["implementation_doc_state"] = "inactive_template"
        state["subtasks"][subtask_id] = {
            "meta": subtask_meta,
            "facts": subtask_facts,
            "state": {
                "confirmed": confirmed_state,
                "tracking": make_default_tracking_state(),
            },
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

    diagnostics = _reorder_diagnostics(diagnostics)
    return state, diagnostics


def _normalize_oq_policy_fields(oqs: object) -> tuple[dict[str, dict[str, object]], list[Diagnostic]]:
    if not isinstance(oqs, dict):
        return {}, []

    normalized: dict[str, dict[str, object]] = {}
    missing_gate_ids: list[str] = []
    missing_resolution_ids: list[str] = []
    missing_any_ids: list[str] = []

    for oq_id, oq in oqs.items():
        if not isinstance(oq_id, str):
            continue
        if not isinstance(oq, dict):
            continue
        normalized[oq_id] = dict(oq)

        raw_gate_level = oq.get("gate_level")
        has_gate_level = isinstance(raw_gate_level, str) and raw_gate_level.strip()
        has_resolution_policy = (
            isinstance(oq.get("resolution_policy"), str)
            and str(oq.get("resolution_policy")).strip()
        )
        if not isinstance(raw_gate_level, str) or not raw_gate_level.strip():
            normalized[oq_id]["gate_level"] = OQ_DEFAULT_GATE_LEVEL
            missing_gate_ids.append(oq_id)
            normalized[oq_id]["gate_policy_source"] = OQ_POLICY_SOURCE_BOOTSTRAP_DEFAULT
        else:
            normalized[oq_id]["gate_policy_source"] = OQ_POLICY_SOURCE_EXPLICIT

        if not has_resolution_policy:
            normalized[oq_id]["resolution_policy"] = OQ_DEFAULT_RESOLUTION_POLICY
            missing_resolution_ids.append(oq_id)
            if OQ_DEFAULT_POLICY_SOURCE == OQ_POLICY_SOURCE_BOOTSTRAP_DEFAULT:
                normalized[oq_id]["gate_policy_source"] = OQ_POLICY_SOURCE_BOOTSTRAP_DEFAULT

        if oq_id in missing_gate_ids or oq_id in missing_resolution_ids:
            if oq_id not in missing_any_ids:
                missing_any_ids.append(oq_id)
        if "gate_policy_source" not in normalized[oq_id]:
            normalized[oq_id]["gate_policy_source"] = OQ_POLICY_SOURCE_EXPLICIT

    if not missing_any_ids:
        return normalized, []

    missing_any_ids = sorted(missing_any_ids)
    applied_count = len(missing_any_ids)
    diagnostics = [
        make_diagnostic(
            code="BOOTSTRAP_OQ_POLICY_DEFAULT_APPLIED",
            severity="warning",
            entity_type="system",
            entity_id="GLOBAL",
            field_path="oqs[*]",
            message=(
                f"Applied default OQ policy fields to {applied_count} OQ(s): "
                f"gate_level={OQ_DEFAULT_GATE_LEVEL}, resolution_policy={OQ_DEFAULT_RESOLUTION_POLICY}"
            ),
            evidence=[
                make_evidence(
                    type="oq_policy_default",
                    path="OPEN_QUESTIONS.md",
                    ref="defaulted_oqs",
                    value={
                        "count": applied_count,
                        "missing_gate_level_count": len(missing_gate_ids),
                        "missing_resolution_policy_count": len(missing_resolution_ids),
                        "defaults": {
                            "gate_level": OQ_DEFAULT_GATE_LEVEL,
                            "resolution_policy": OQ_DEFAULT_RESOLUTION_POLICY,
                        },
                        "oq_ids": missing_any_ids[:10],
                    },
                )
            ],
        )
    ]
    return normalized, diagnostics


def _resolve_requirement_relations(
    *,
    scan_result: dict[str, object],
    relation_key: str,
    fact_field: str,
) -> dict[str, list[str]]:
    raw_relation_map = scan_result.get(relation_key)
    relation_map: dict[str, list[str]] = {}
    if isinstance(raw_relation_map, dict):
        for entity_id, requirement_ids in raw_relation_map.items():
            if not isinstance(requirement_ids, list):
                continue
            normalized = [
                str(requirement_id)
                for requirement_id in requirement_ids
                if isinstance(requirement_id, str) and str(requirement_id).strip()
            ]
            if normalized:
                relation_map[str(entity_id)] = sorted(dict.fromkeys(normalized))

    if relation_map:
        return relation_map

    requirements = scan_result.get("requirements")
    requirements = requirements if isinstance(requirements, dict) else {}
    for requirement_id, requirement in requirements.items():
        if not isinstance(requirement, dict):
            continue
        facts = requirement.get("facts")
        facts = facts if isinstance(facts, dict) else {}
        for entity_id in facts.get(fact_field, []):
            if not isinstance(entity_id, str):
                continue
            relation_map.setdefault(entity_id, []).append(str(requirement_id))

    for entity_id, requirement_ids in list(relation_map.items()):
        relation_map[entity_id] = sorted(dict.fromkeys(requirement_ids))
    return relation_map


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
    oq_policy_diag = [item for item in diagnostics if item.code == "BOOTSTRAP_OQ_POLICY_DEFAULT_APPLIED"]
    if oq_policy_diag:
        for item in oq_policy_diag:
            evidence = item.evidence[0].value or {}
            count = evidence.get("count", "n/a")
            defaults = evidence.get("defaults", {})
            oq_ids = evidence.get("oq_ids", [])
            missing_gate = evidence.get("missing_gate_level_count", "n/a")
            missing_policy = evidence.get("missing_resolution_policy_count", "n/a")
            lines.append(
                "- OQ policy defaults applied:"
                f" count={count}"
                f", defaults={defaults}"
                f", missing_gate_level={missing_gate}"
                f", missing_resolution_policy={missing_policy}"
                f", sample_oq_ids={oq_ids}"
            )
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


def _reorder_diagnostics(diagnostics: list[Diagnostic]) -> list[Diagnostic]:
    severity_rank = {"error": 0, "warning": 1}
    return sorted(
        diagnostics,
        key=lambda item: (
            severity_rank.get(item.severity, 9),
            0 if item.code == "BOOTSTRAP_IMPL_DOC_STATE_AMBIGUOUS" else 1,
            item.code,
            item.entity_type,
            item.entity_id,
        ),
    )


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
