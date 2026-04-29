from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
from typing import Any

from .document_scan import scan_document
from .diagnostics import Diagnostic, make_diagnostic, make_evidence
from .language_check import check_markdown_language
from .schema import MATURITY_LEVELS, REQUIRED_MODULE_SLOTS, SCHEMA_VERSION, TYPED_BLOCKER_REF_RE
from .validate import validate_state_file


BLOCKED_REASON_CODES = {
    "legacy_locked",
    "missing_required_doc_slot",
    "template_like_required_doc_slot",
    "upstream_module_not_ready",
    "oq_candidate_gate",
    "oq_readiness_gate",
    "implementation_doc_not_active",
    "formal_window_closed",
    "asset_hard_blocker",
    "language_non_compliant",
    "compliance_non_compliant",
    "missing_required_section",
    "missing_relation_ref",
    "document_markers_pending",
    "document_file_missing",
    "document_repo_truth_mismatch",
    "requirement_id_unresolved",
    "maturity_missing",
    "implementation_approval_missing",
    "implementation_scope_unclear",
    "required_tests_missing",
    "acceptance_criteria_missing",
    "path_scope_conflict",
}

REVIEW_REASONS = {
    "downstream_ready_no_hard_blocker",
    "oq_review_only",
    "implementation_doc_activation_recommended",
    "document_ready_for_review",
}

OQ_GATE_LEVELS = ("observe_only", "candidate_gate", "readiness_gate")
OQ_RESOLUTION_POLICIES = (
    "proposed_default_ok",
    "confirmed_only",
    "manual_override_only",
)

MARKDOWN_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*$")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
LIST_PREFIX_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s*")
HEADING_NUMBER_RE = re.compile(r"^\d+(?:\.\d+)*\.?\s*")


def evaluate_state_file(state_path: Path) -> tuple[list[Diagnostic], dict[str, Any]]:
    diagnostics = validate_state_file(state_path)
    if any(item.severity == "error" for item in diagnostics):
        return diagnostics, {}

    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - environment guard
        return (
            diagnostics
            + [
                make_diagnostic(
                    code="SCHEMA_PYYAML_UNAVAILABLE",
                    severity="error",
                    entity_type="system",
                    entity_id="GLOBAL",
                    field_path="python.dependencies.yaml",
                    message="PyYAML is required to parse DOC_STATE YAML.",
                    evidence=[
                        make_evidence(
                            type="dependency",
                            path=state_path.as_posix(),
                            ref="import yaml",
                            value=str(exc),
                        )
                    ],
                )
            ],
            {},
        )

    try:
        state_text = state_path.read_text(encoding="utf-8")
        state = yaml.safe_load(state_text)
    except FileNotFoundError:
        return (
            diagnostics
            + [
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type="system",
                    entity_id="GLOBAL",
                    field_path="input.path",
                    message=f"State file not found: {state_path}",
                    evidence=[
                        make_evidence(
                            type="file_scan",
                            path=state_path.as_posix(),
                            ref="exists",
                            value=False,
                        )
                    ],
                )
            ],
            {},
        )
    except Exception as exc:  # noqa: BLE001
        return (
            diagnostics
            + [
                make_diagnostic(
                    code="SCHEMA_INVALID_FILE_FORMAT",
                    severity="error",
                    entity_type="system",
                    entity_id="GLOBAL",
                    field_path="root",
                    message=f"Failed to parse state yaml: {exc}",
                    evidence=[
                        make_evidence(
                            type="file_scan",
                            path=state_path.as_posix(),
                            ref="yaml.parse",
                            value=str(exc),
                        )
                    ],
                )
            ],
            {},
        )

    if not isinstance(state, dict):
        return (
            diagnostics
            + [
                make_diagnostic(
                    code="SCHEMA_INVALID_FILE_FORMAT",
                    severity="error",
                    entity_type="system",
                    entity_id="GLOBAL",
                    field_path="root",
                    message="State file must contain a top-level mapping.",
                    evidence=[
                        make_evidence(
                            type="file_scan",
                            path=state_path.as_posix(),
                            ref="root.type",
                            value=type(state).__name__,
                        )
                    ],
                )
            ],
            {},
        )

    diagnostics.extend(_validate_oq_persisted_fields(state, state_path))
    if any(item.severity == "error" for item in diagnostics):
        return diagnostics, {}

    evaluated = _evaluate_state_payload(state, state_path=state_path)
    return diagnostics, evaluated


def _validate_oq_persisted_fields(
    state: dict[str, object],
    state_path: Path,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    schema_version = state.get("schema_version")
    if not isinstance(schema_version, int):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="schema_version",
                message=f"schema_version must be {SCHEMA_VERSION}.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref="schema_version",
                        value=schema_version,
                    )
                ],
            )
        )
    elif schema_version != SCHEMA_VERSION:
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_UNKNOWN_ENUM_VALUE",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="schema_version",
                message=f"schema_version must be {SCHEMA_VERSION}.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref="schema_version",
                        value=schema_version,
                    )
                ],
            )
        )

    oqs = state.get("oqs")
    if not isinstance(oqs, dict):
        return diagnostics

    for oq_id, oq in oqs.items():
        if not isinstance(oq, dict):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type="oq",
                    entity_id=str(oq_id),
                    field_path=f"oqs.{oq_id}",
                    message="OQ record must be a mapping.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"oqs.{oq_id}",
                            value=type(oq).__name__,
                        )
                    ],
                )
            )
            continue

        for field_name in ("gate_level", "resolution_policy", "status", "affects"):
            if field_name not in oq:
                diagnostics.append(
                    make_diagnostic(
                        code="SCHEMA_MISSING_REQUIRED_FIELD",
                        severity="error",
                        entity_type="oq",
                        entity_id=str(oq_id),
                        field_path=f"oqs.{oq_id}.{field_name}",
                        message=f"Missing OQ required field: {field_name}",
                        evidence=[
                            make_evidence(
                                type="state_check",
                                path=state_path.as_posix(),
                                ref=f"oqs.{oq_id}.{field_name}",
                                value=None,
                            )
                        ],
                    )
                )

        if oq.get("gate_level") not in OQ_GATE_LEVELS:
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_UNKNOWN_ENUM_VALUE",
                    severity="error",
                    entity_type="oq",
                    entity_id=str(oq_id),
                    field_path=f"oqs.{oq_id}.gate_level",
                    message="Unknown OQ gate_level.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"oqs.{oq_id}.gate_level",
                            value=oq.get("gate_level"),
                        )
                    ],
                )
            )
        if oq.get("resolution_policy") not in OQ_RESOLUTION_POLICIES:
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_UNKNOWN_ENUM_VALUE",
                    severity="error",
                    entity_type="oq",
                    entity_id=str(oq_id),
                    field_path=f"oqs.{oq_id}.resolution_policy",
                    message="Unknown OQ resolution_policy.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"oqs.{oq_id}.resolution_policy",
                            value=oq.get("resolution_policy"),
                        )
                    ],
                )
            )

    return diagnostics


def _evaluate_state_payload(state: dict[str, object], *, state_path: Path) -> dict[str, Any]:
    repo_root = _resolve_repo_root(state_path)
    oqs = state.get("oqs")
    oqs = oqs if isinstance(oqs, dict) else {}
    requirements = state.get("requirements")
    requirements = requirements if isinstance(requirements, dict) else {}
    modules = state.get("modules")
    modules = modules if isinstance(modules, dict) else {}
    subtasks = state.get("subtasks")
    subtasks = subtasks if isinstance(subtasks, dict) else {}
    documents = state.get("documents")
    documents = documents if isinstance(documents, dict) else {}
    governance_rounds = state.get("governance_rounds")
    governance_rounds = governance_rounds if isinstance(governance_rounds, list) else []

    oq_payload = _evaluate_oqs(oqs)
    requirement_derived_map: dict[str, dict[str, Any]] = {}
    known_requirement_ids: set[str] = set()
    requirement_module_links: dict[str, list[str]] = {}
    requirement_task_links: dict[str, list[str]] = {}
    for requirement_id, requirement_obj in requirements.items():
        if not isinstance(requirement_obj, dict):
            continue
        requirement_result = _evaluate_requirement(requirement_id, requirement_obj)
        requirement_derived_map[requirement_id] = requirement_result
        known_requirement_ids.add(str(requirement_id))
        requirement_facts = requirement_obj.get("facts")
        requirement_facts = requirement_facts if isinstance(requirement_facts, dict) else {}
        for module_id in requirement_facts.get("module_ids", []):
            if not isinstance(module_id, str):
                continue
            requirement_module_links.setdefault(str(module_id), []).append(str(requirement_id))
        for task_id in requirement_facts.get("task_ids", []):
            if not isinstance(task_id, str):
                continue
            requirement_task_links.setdefault(str(task_id), []).append(str(requirement_id))

    module_requirement_ids = _prefer_native_requirement_relations(
        fallback_relations=requirement_module_links,
        native_relations=_collect_native_requirement_relations(modules),
    )
    module_requirement_ids = _filter_known_requirement_relations(
        module_requirement_ids,
        known_requirement_ids,
    )
    subtask_requirement_ids = _prefer_native_requirement_relations(
        fallback_relations=requirement_task_links,
        native_relations=_collect_native_requirement_relations(
            subtasks,
            inherited_relations=module_requirement_ids,
            inherit_from_field="module_id",
        ),
    )
    subtask_requirement_ids = _filter_known_requirement_relations(
        subtask_requirement_ids,
        known_requirement_ids,
    )
    requirement_blockers_by_module = _build_requirement_blocker_map(
        module_requirement_ids,
        requirement_derived_map,
    )
    requirement_blockers_by_task = _build_requirement_blocker_map(
        subtask_requirement_ids,
        requirement_derived_map,
    )

    module_derived_map: dict[str, dict[str, Any]] = {}
    for module_id, module_obj in modules.items():
        if isinstance(module_obj, dict):
            module_derived_map[module_id] = _evaluate_module(
                module_id,
                module_obj,
                oq_payload,
                requirement_blockers_by_module.get(str(module_id), []),
                requirement_ids=module_requirement_ids.get(str(module_id), []),
            )

    subtask_derived_map: dict[str, dict[str, Any]] = {}
    for subtask_id, subtask_obj in subtasks.items():
        if isinstance(subtask_obj, dict):
            subtask_derived_map[subtask_id] = _evaluate_subtask(
                subtask_id=subtask_id,
                subtask_obj=subtask_obj,
                oq_payload=oq_payload,
                module_derived_map=module_derived_map,
                direct_requirement_blockers=requirement_blockers_by_task.get(str(subtask_id), []),
                repo_root=repo_root,
                requirement_ids=subtask_requirement_ids.get(str(subtask_id), []),
            )

    requirement_derived_wrapped: dict[str, Any] = {}
    for requirement_id, requirement_result in requirement_derived_map.items():
        requirement_derived_wrapped[requirement_id] = {
            "derived": _finalize_requirement_derived(
                requirement_id=requirement_id,
                requirement_result=requirement_result,
            )
        }

    module_derived_wrapped: dict[str, Any] = {}
    for module_id, module_result in module_derived_map.items():
        module_derived_wrapped[module_id] = {
            "derived": _finalize_module_derived(
                module_id=module_id,
                module_result=module_result,
                module_mode=True,
            )
        }

    subtask_derived_wrapped: dict[str, Any] = {}
    for subtask_id, subtask_result in subtask_derived_map.items():
        subtask_derived_wrapped[subtask_id] = {
            "derived": _finalize_subtask_derived(
                subtask_id=subtask_id,
                subtask_result=subtask_result,
            )
        }

    document_results = _evaluate_documents(
        documents=documents,
        repo_root=repo_root,
    )
    rounds_summary = _summarize_rounds(governance_rounds)

    summary = _build_summary(
        requirement_results=requirement_derived_wrapped,
        module_results=module_derived_wrapped,
        subtask_results=subtask_derived_wrapped,
        document_results=document_results,
        oq_payload=oq_payload,
        oq_source_map=oqs,
        rounds_summary=rounds_summary,
    )

    return {
        "summary": summary,
        "requirements": requirement_derived_wrapped,
        "modules": module_derived_wrapped,
        "subtasks": subtask_derived_wrapped,
        "documents": document_results,
        "oqs": oq_payload,
        "governance_rounds": governance_rounds,
        "rounds_summary": rounds_summary,
    }


def build_delta_summary(
    *,
    current_payload: dict[str, Any],
    baseline_payload: dict[str, Any],
) -> dict[str, Any]:
    current_blockers = _collect_blocker_keys(current_payload)
    baseline_blockers = _collect_blocker_keys(baseline_payload)
    added_blockers = sorted(current_blockers - baseline_blockers)
    closed_blockers = sorted(baseline_blockers - current_blockers)

    current_requirements = _extract_entities(current_payload, key="requirements")
    current_modules = _extract_entities(current_payload, key="modules")
    current_subtasks = _extract_entities(current_payload, key="subtasks")
    baseline_requirements = _extract_entities(baseline_payload, key="requirements")
    baseline_modules = _extract_entities(baseline_payload, key="modules")
    baseline_subtasks = _extract_entities(baseline_payload, key="subtasks")

    return {
        "blocker_changes": {
            "added_count": len(added_blockers),
            "closed_count": len(closed_blockers),
            "added_refs": added_blockers,
            "closed_refs": closed_blockers,
        },
        "review_required_changes": {
            "requirements": _diff_boolean_field(
                current_entities=current_requirements,
                baseline_entities=baseline_requirements,
                field="review_required",
            ),
            "modules": _diff_boolean_field(
                current_entities=current_modules,
                baseline_entities=baseline_modules,
                field="review_required",
            ),
            "subtasks": _diff_boolean_field(
                current_entities=current_subtasks,
                baseline_entities=baseline_subtasks,
                field="review_required",
            ),
        },
        "readiness_changes": {
            "requirements_next_step": _diff_boolean_field(
                current_entities=current_requirements,
                baseline_entities=baseline_requirements,
                field="ready_for_next_step",
            ),
            "modules_downstream": _diff_boolean_field(
                current_entities=current_modules,
                baseline_entities=baseline_modules,
                field="assessed_downstream_ready",
            ),
            "subtasks_downstream": _diff_boolean_field(
                current_entities=current_subtasks,
                baseline_entities=baseline_subtasks,
                field="assessed_downstream_ready",
            ),
            "subtasks_implementation": _diff_boolean_field(
                current_entities=current_subtasks,
                baseline_entities=baseline_subtasks,
                field="assessed_implementation_ready",
            ),
        },
    }


def _evaluate_requirement(
    requirement_id: str,
    requirement: dict[str, object],
) -> dict[str, Any]:
    facts = requirement.get("facts")
    facts = facts if isinstance(facts, dict) else {}
    asset_slots = facts.get("asset_slots")
    asset_slots = asset_slots if isinstance(asset_slots, dict) else {}
    compliance = facts.get("compliance")
    compliance = compliance if isinstance(compliance, dict) else {}
    module_ids = _dedupe_strings(
        [str(module_id) for module_id in _as_list(facts.get("module_ids")) if isinstance(module_id, str)]
    )
    task_ids = _dedupe_strings(
        [str(task_id) for task_id in _as_list(facts.get("task_ids")) if isinstance(task_id, str)]
    )

    gate_blockers: list[dict[str, Any]] = []

    for slot_name, slot_value in asset_slots.items():
        slot_value = slot_value if isinstance(slot_value, dict) else {}
        if not bool(slot_value.get("exists", False)):
            gate_blockers.append(
                _make_blocker(
                    ref=f"policy:asset_missing_{_normalize_policy_token(str(slot_name))}",
                    kind="policy",
                    reason_code="asset_hard_blocker",
                    message=f"requirement {requirement_id} missing asset slot {slot_name}",
                )
            )

    for compliance_key, ref_name in (
        ("naming_ok", "naming_non_compliant"),
        ("path_ok", "path_non_compliant"),
        ("relations_ok", "relations_non_compliant"),
    ):
        if compliance.get(compliance_key) is False:
            gate_blockers.append(
                _make_blocker(
                    ref=f"policy:{ref_name}",
                    kind="policy",
                    reason_code="compliance_non_compliant",
                    message=f"requirement {requirement_id} compliance {compliance_key}=false",
                )
            )

    if compliance.get("language_ok") is False:
        gate_blockers.append(
            _make_blocker(
                ref="policy:language_non_compliant",
                kind="policy",
                reason_code="language_non_compliant",
                message=f"requirement {requirement_id} compliance language_ok=false",
            )
        )

    violations = compliance.get("violations")
    violations = violations if isinstance(violations, list) else []
    for violation in violations:
        if not isinstance(violation, str) or not violation.strip():
            continue
        normalized = _normalize_policy_token(violation)
        if not normalized:
            continue
        if normalized.startswith("language_non_compliant"):
            reason_code = "language_non_compliant"
        else:
            reason_code = "compliance_non_compliant"
        gate_blockers.append(
            _make_blocker(
                ref=f"policy:{normalized}",
                kind="policy",
                reason_code=reason_code,
                message=f"requirement {requirement_id} compliance violation {violation}",
            )
        )

    return {
        "gate_blockers": _dedupe_blockers(gate_blockers),
        "module_ids": module_ids,
        "task_ids": task_ids,
    }


def _evaluate_oqs(oqs: dict[str, object]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for oq_id, oq in oqs.items():
        if not isinstance(oq, dict):
            continue
        gate_level = str(oq.get("gate_level", ""))
        status = str(oq.get("status", ""))
        resolution_policy = str(oq.get("resolution_policy", ""))
        status_class = _oq_status_class(status)
        enforcement = _oq_enforcement(gate_level, resolution_policy, status_class)
        payload[str(oq_id)] = {
            "derived_status_class": status_class,
            "derived_enforcement": enforcement,
            "derived_reason_code": _oq_reason_code(gate_level, enforcement),
        }
    return payload


def _oq_status_class(status: str) -> str:
    if status == "proposed-default":
        return "proposed_default"
    if status in {"resolved", "closed", "accepted", "done", "confirmed"}:
        return "confirmed_clear"
    if status in {"manual_override", "override_approved"}:
        return "manual_override_clear"
    return "unresolved"


def _oq_enforcement(gate_level: str, resolution_policy: str, status_class: str) -> str:
    if gate_level == "observe_only":
        if status_class in {"confirmed_clear", "manual_override_clear"}:
            return "clear"
        return "review_only"

    if gate_level == "candidate_gate":
        if resolution_policy == "confirmed_only":
            return "candidate_blocker" if status_class != "confirmed_clear" else "clear"
        if resolution_policy == "manual_override_only":
            return "candidate_blocker" if status_class != "manual_override_clear" else "clear"
        # proposed_default_ok
        if status_class == "proposed_default":
            return "review_only"
        if status_class in {"confirmed_clear", "manual_override_clear"}:
            return "clear"
        return "candidate_blocker"

    if gate_level == "readiness_gate":
        if resolution_policy == "confirmed_only":
            return "readiness_blocker" if status_class != "confirmed_clear" else "clear"
        if resolution_policy == "manual_override_only":
            return "readiness_blocker" if status_class != "manual_override_clear" else "clear"
        # proposed_default_ok
        if status_class == "proposed_default":
            return "review_only"
        if status_class in {"confirmed_clear", "manual_override_clear"}:
            return "clear"
        return "readiness_blocker"

    return "review_only"


def _oq_reason_code(gate_level: str, enforcement: str) -> str:
    if enforcement == "candidate_blocker":
        return "oq_candidate_gate"
    if enforcement == "readiness_blocker":
        return "oq_readiness_gate"
    return enforcement


def _evaluate_module(
    module_id: str,
    module: dict[str, object],
    oq_payload: dict[str, Any],
    requirement_blockers: list[dict[str, Any]],
    requirement_ids: list[str],
) -> dict[str, Any]:
    facts = module.get("facts")
    facts = facts if isinstance(facts, dict) else {}
    docs = facts.get("docs")
    docs = docs if isinstance(docs, dict) else {}

    related_oq_ids = facts.get("related_oq_ids")
    related_oq_ids = related_oq_ids if isinstance(related_oq_ids, list) else []

    candidate_blockers: list[dict[str, str]] = []
    downstream_blockers: list[dict[str, str]] = []
    oq_review_only_refs: list[str] = []

    downstream_blockers.extend(_clone_blockers(requirement_blockers))

    for oq_id in related_oq_ids:
        oq_info = oq_payload.get(str(oq_id), {})
        enforcement = oq_info.get("derived_enforcement")
        if enforcement == "candidate_blocker":
            candidate_blockers.append(
                _make_blocker(
                    ref=f"oq:{oq_id}",
                    kind="oq",
                    reason_code="oq_candidate_gate",
                    message=f"module {module_id} candidate blocked by OQ {oq_id}",
                )
            )
        elif enforcement == "readiness_blocker":
            downstream_blockers.append(
                _make_blocker(
                    ref=f"oq:{oq_id}",
                    kind="oq",
                    reason_code="oq_readiness_gate",
                    message=f"module {module_id} readiness blocked by OQ {oq_id}",
                )
            )
        elif enforcement == "review_only":
            oq_review_only_refs.append(f"oq:{oq_id}")

    if facts.get("legacy_locked"):
        downstream_blockers.append(
            _make_blocker(
                ref="legacy:locked",
                kind="legacy",
                reason_code="legacy_locked",
                message=f"module {module_id} is legacy locked",
            )
        )

    for slot in REQUIRED_MODULE_SLOTS:
        slot_info = docs.get(slot, {"exists": False, "template_like": False})
        if not isinstance(slot_info, dict):
            slot_info = {"exists": False, "template_like": False}
        if not bool(slot_info.get("exists", False)):
            downstream_blockers.append(
                _make_blocker(
                    ref=f"doc:{slot}",
                    kind="doc",
                    reason_code="missing_required_doc_slot",
                    message=f"module {module_id} required slot {slot} missing",
                )
            )
        elif bool(slot_info.get("template_like", False)):
            downstream_blockers.append(
                _make_blocker(
                    ref=f"doc:{slot}",
                    kind="doc",
                    reason_code="template_like_required_doc_slot",
                    message=f"module {module_id} required slot {slot} template-like",
                )
            )

    downstream_ready = not bool(downstream_blockers)
    return {
        "candidate_blockers": _dedupe_blockers(candidate_blockers),
        "downstream_blockers": _dedupe_blockers(downstream_blockers),
        "gate_blockers": _dedupe_blockers(candidate_blockers + downstream_blockers),
        "oq_review_only_refs": sorted(set(oq_review_only_refs)),
        "assessed_downstream_ready": downstream_ready,
        "requirement_ids": _dedupe_strings(requirement_ids),
    }


def _evaluate_subtask(
    *,
    subtask_id: str,
    subtask_obj: dict[str, object],
    oq_payload: dict[str, Any],
    module_derived_map: dict[str, dict[str, Any]],
    direct_requirement_blockers: list[dict[str, Any]],
    repo_root: Path,
    requirement_ids: list[str],
) -> dict[str, Any]:
    facts = subtask_obj.get("facts")
    facts = facts if isinstance(facts, dict) else {}
    meta = subtask_obj.get("meta")
    meta = meta if isinstance(meta, dict) else {}
    state = subtask_obj.get("state")
    state = state if isinstance(state, dict) else {}
    confirmed = state.get("confirmed")
    confirmed = confirmed if isinstance(confirmed, dict) else {}
    design_doc = facts.get("design_doc")
    impl_doc = facts.get("implementation_doc")

    related_oq_ids = facts.get("related_oq_ids")
    related_oq_ids = related_oq_ids if isinstance(related_oq_ids, list) else []
    upstream_module_ids = facts.get("upstream_module_ids")
    upstream_module_ids = upstream_module_ids if isinstance(upstream_module_ids, list) else []

    candidate_blockers: list[dict[str, str]] = []
    downstream_blockers: list[dict[str, str]] = []
    implementation_blockers: list[dict[str, str]] = []
    oq_review_only_refs: list[str] = []

    downstream_blockers.extend(_clone_blockers(direct_requirement_blockers))

    for oq_id in related_oq_ids:
        oq_info = oq_payload.get(str(oq_id), {})
        enforcement = oq_info.get("derived_enforcement")
        if enforcement == "candidate_blocker":
            candidate_blockers.append(
                _make_blocker(
                    ref=f"oq:{oq_id}",
                    kind="oq",
                    reason_code="oq_candidate_gate",
                    message=f"subtask {subtask_id} candidate blocked by OQ {oq_id}",
                )
            )
        elif enforcement == "readiness_blocker":
            downstream_blockers.append(
                _make_blocker(
                    ref=f"oq:{oq_id}",
                    kind="oq",
                    reason_code="oq_readiness_gate",
                    message=f"subtask {subtask_id} readiness blocked by OQ {oq_id}",
                )
            )
        elif enforcement == "review_only":
            oq_review_only_refs.append(f"oq:{oq_id}")

    if facts.get("legacy_locked"):
        downstream_blockers.append(
            _make_blocker(
                ref="legacy:locked",
                kind="legacy",
                reason_code="legacy_locked",
                message=f"subtask {subtask_id} is legacy locked",
            )
        )

    for upstream_module_id in upstream_module_ids:
        upstream_module = module_derived_map.get(str(upstream_module_id))
        if (
            isinstance(upstream_module, dict)
            and not upstream_module.get("assessed_downstream_ready", True)
        ):
            downstream_blockers.append(
                _make_blocker(
                    ref=f"module:{upstream_module_id}",
                    kind="module",
                    reason_code="upstream_module_not_ready",
                    message=(
                        f"subtask {subtask_id} upstream module {upstream_module_id} is not downstream ready"
                    ),
                )
            )
            downstream_blockers.extend(_clone_blockers(upstream_module.get("gate_blockers", [])))

    for slot_name, slot_doc in (("design_doc", design_doc), ("implementation_doc", impl_doc)):
        if not isinstance(slot_doc, dict):
            slot_doc = {"exists": False, "template_like": False}
        if not bool(slot_doc.get("exists", False)):
            downstream_blockers.append(
                _make_blocker(
                    ref=f"doc:{slot_name}",
                    kind="doc",
                    reason_code="missing_required_doc_slot",
                    message=(
                        f"subtask {subtask_id} required slot {slot_name} is missing"
                    ),
                )
            )
        elif bool(slot_doc.get("template_like", False)):
            downstream_blockers.append(
                _make_blocker(
                    ref=f"doc:{slot_name}",
                    kind="doc",
                    reason_code="template_like_required_doc_slot",
                    message=(
                        f"subtask {subtask_id} required slot {slot_name} is template-like"
                    ),
                )
            )

    if confirmed.get("implementation_doc_state") != "active_working_doc":
        implementation_blockers.append(
            _make_blocker(
                ref="gate:implementation_doc_not_active",
                kind="gate",
                reason_code="implementation_doc_not_active",
                message=(
                    f"subtask {subtask_id} IMPLEMENTATION document exists does not imply "
                    "implementation-ready or packet-ready; implementation_doc_state is not "
                    "active_working_doc"
                ),
            )
        )
    formal_window_open = str(confirmed.get("formal_window_status", "closed")) == "open"
    if not formal_window_open:
        implementation_blockers.append(
            _make_blocker(
                ref="policy:formal_window_closed",
                kind="policy",
                reason_code="formal_window_closed",
                message=(
                    f"scoped formal_window_status is not open; this prevents implementation packet generation "
                    f"and implementation-ready for subtask {subtask_id}"
                ),
            )
        )
    maturity = confirmed.get("maturity")
    if maturity not in MATURITY_LEVELS:
        implementation_blockers.append(
            _make_blocker(
                ref="gate:maturity_missing",
                kind="gate",
                reason_code="maturity_missing",
                message=f"subtask {subtask_id} confirmed maturity is required before implementation-ready",
            )
        )
    implementation_approval_status = str(
        confirmed.get("implementation_approval_status", "none")
    )
    confirmed_readiness = str(confirmed.get("readiness", "blocked"))
    implementation_explicitly_approved = (
        implementation_approval_status == "approved"
        or confirmed_readiness == "implementation_ready"
    )
    if not implementation_explicitly_approved:
        implementation_blockers.append(
            _make_blocker(
                ref="gate:implementation_approval_missing",
                kind="gate",
                reason_code="implementation_approval_missing",
                message=(
                    f"subtask {subtask_id} requires implementation_approval_status=approved "
                    "or confirmed readiness=implementation_ready before implementation-ready"
                ),
            )
        )

    resolved_requirement_id = requirement_ids[0] if len(requirement_ids) == 1 else None
    if resolved_requirement_id is None:
        if requirement_ids:
            implementation_blockers.append(
                _make_blocker(
                    ref="gate:requirement_id_ambiguous",
                    kind="gate",
                    reason_code="requirement_id_unresolved",
                    message=(
                        f"subtask {subtask_id} matches multiple requirement ids: "
                        + ", ".join(sorted(requirement_ids))
                    ),
                )
            )
        else:
            implementation_blockers.append(
                _make_blocker(
                    ref="gate:requirement_id_missing",
                    kind="gate",
                    reason_code="requirement_id_unresolved",
                    message=f"subtask {subtask_id} cannot resolve a unique requirement id",
                )
            )

    packet_inputs = _build_subtask_packet_inputs(
        subtask_id=subtask_id,
        module_id=str(meta.get("module_id", "")),
        subtask_path=str(meta.get("path", "")),
        design_doc=design_doc if isinstance(design_doc, dict) else {},
        implementation_doc=impl_doc if isinstance(impl_doc, dict) else {},
        repo_root=repo_root,
        requirement_id=resolved_requirement_id,
    )
    missing_scope_fields: list[str] = []
    if not packet_inputs.get("goal"):
        missing_scope_fields.append("goal")
    if not packet_inputs.get("allowed_modify_paths"):
        missing_scope_fields.append("allowed_modify_paths")
    if not packet_inputs.get("forbidden_paths"):
        missing_scope_fields.append("forbidden_paths")
    if missing_scope_fields:
        implementation_blockers.append(
            _make_blocker(
                ref="gate:implementation_scope_unclear",
                kind="gate",
                reason_code="implementation_scope_unclear",
                message=(
                    f"subtask {subtask_id} implementation scope is incomplete: "
                    + ", ".join(missing_scope_fields)
                ),
            )
        )
    for conflict in _as_list(packet_inputs.get("path_conflicts")):
        if not isinstance(conflict, dict):
            continue
        implementation_blockers.append(
            _make_blocker(
                ref="gate:path_scope_conflict",
                kind="gate",
                reason_code="path_scope_conflict",
                message=(
                    f"subtask {subtask_id} allowed path {conflict.get('allowed', '')} "
                    f"conflicts with forbidden path {conflict.get('forbidden', '')}"
                ),
            )
        )
    if not packet_inputs.get("required_tests"):
        implementation_blockers.append(
            _make_blocker(
                ref="gate:required_tests_missing",
                kind="gate",
                reason_code="required_tests_missing",
                message=f"subtask {subtask_id} implementation doc is missing required tests",
            )
        )
    if not packet_inputs.get("acceptance_criteria"):
        implementation_blockers.append(
            _make_blocker(
                ref="gate:acceptance_criteria_missing",
                kind="gate",
                reason_code="acceptance_criteria_missing",
                message=(
                    f"subtask {subtask_id} implementation doc is missing acceptance criteria"
                ),
            )
        )
    for violation in _as_list(packet_inputs.get("language_violations")):
        if not isinstance(violation, dict):
            continue
        code = _normalize_policy_token(str(violation.get("code", "language_non_compliant")))
        doc_path = str(violation.get("path", ""))
        message = str(violation.get("message", "language policy violation"))
        implementation_blockers.append(
            _make_blocker(
                ref=f"policy:{code or 'language_non_compliant'}",
                kind="policy",
                reason_code="language_non_compliant",
                message=f"subtask {subtask_id} language violation in {doc_path}: {message}",
            )
        )

    candidate_blockers = _dedupe_blockers(candidate_blockers)
    downstream_blockers = _dedupe_blockers(downstream_blockers)
    implementation_blockers = _dedupe_blockers(implementation_blockers)

    downstream_blocker_refs = sorted(blocker["ref"] for blocker in downstream_blockers)
    design_exists = bool(design_doc and isinstance(design_doc, dict) and design_doc.get("exists"))
    design_template_like = bool(
        design_doc and isinstance(design_doc, dict) and design_doc.get("template_like")
    )
    impl_exists = bool(impl_doc and isinstance(impl_doc, dict) and impl_doc.get("exists"))
    impl_template_like = bool(
        impl_doc and isinstance(impl_doc, dict) and impl_doc.get("template_like")
    )
    impl_state = confirmed.get("implementation_doc_state")

    implementation_doc_activation_recommended = (
        design_exists
        and not design_template_like
        and impl_state != "active_working_doc"
        and (not impl_exists or impl_template_like)
    )
    if implementation_doc_activation_recommended:
        if impl_template_like:
            implementation_doc_activation_reason = "implementation_doc_template_like"
        elif not impl_exists:
            implementation_doc_activation_reason = "implementation_doc_missing"
        else:
            implementation_doc_activation_reason = "implementation_doc_state_inactive"
    else:
        implementation_doc_activation_reason = "implementation_doc_activation_not_applicable"

    return {
        "candidate_blockers": candidate_blockers,
        "downstream_blockers": downstream_blockers,
        "implementation_blockers": implementation_blockers,
        "gate_blockers": _dedupe_blockers(
            candidate_blockers + downstream_blockers + implementation_blockers
        ),
        "oq_review_only_refs": sorted(set(oq_review_only_refs)),
        "implementation_doc_activation_recommended": implementation_doc_activation_recommended,
        "implementation_doc_activation_reason": implementation_doc_activation_reason,
        "implementation_packet_inputs": packet_inputs,
        "requirement_ids": _dedupe_strings(requirement_ids),
        "formal_window_status": "open" if formal_window_open else "closed",
        "implementation_explicitly_approved": implementation_explicitly_approved,
        "formal_window_candidate_recommendation": _build_candidate_recommendation(
            facts=facts,
            confirmed=confirmed,
        ),
        "near_ready_for_formal_window_candidate": _build_near_ready_recommendation(facts),
    }


def _finalize_requirement_derived(
    *,
    requirement_id: str,
    requirement_result: dict[str, Any],
) -> dict[str, Any]:
    gate_blockers = _dedupe_blockers(requirement_result.get("gate_blockers", []))
    blocker_refs = sorted(blocker["ref"] for blocker in gate_blockers)
    ready_for_next_step = not bool(blocker_refs)
    review_reasons = ["downstream_ready_no_hard_blocker"] if ready_for_next_step else []
    module_ids = _dedupe_strings(_as_list(requirement_result.get("module_ids")))
    task_ids = _dedupe_strings(_as_list(requirement_result.get("task_ids")))
    return {
        "current_gate": "module_decomposition_ready",
        "gate_result": "pass" if ready_for_next_step else "blocked",
        "gate_blockers": gate_blockers,
        "blocker_refs": blocker_refs,
        "module_ids": module_ids,
        "task_ids": task_ids,
        "module_count": len(module_ids),
        "task_count": len(task_ids),
        "review_required": ready_for_next_step,
        "review_reasons": review_reasons,
        "ready_for_next_step": ready_for_next_step,
        "implementation_ready": False,
    }


def _evaluate_documents(
    *,
    documents: dict[str, object],
    repo_root: Path,
) -> dict[str, dict[str, Any]]:
    document_registry: dict[str, str] = {}
    for document_id, document_obj in documents.items():
        if isinstance(document_obj, dict):
            meta = document_obj.get("meta")
            if isinstance(meta, dict) and isinstance(meta.get("path"), str):
                document_registry[str(document_id)] = str(meta.get("path"))

    results: dict[str, dict[str, Any]] = {}
    for document_id, document_obj in documents.items():
        if not isinstance(document_obj, dict):
            continue
        meta = document_obj.get("meta")
        meta = meta if isinstance(meta, dict) else {}
        required_sections = meta.get("required_sections")
        required_sections = required_sections if isinstance(required_sections, list) else []
        path = str(meta.get("path", ""))
        facts = scan_document(
            repo_root=repo_root,
            path=path,
            required_sections=required_sections,
            document_registry=document_registry,
        )
        relations = meta.get("relations")
        relations = relations if isinstance(relations, dict) else {}
        derived = _derive_document_status(
            document_id=str(document_id),
            meta=meta,
            facts=facts,
            relations=relations,
        )
        results[str(document_id)] = {
            "facts": facts,
            "derived": derived,
        }
    return results


def _derive_document_status(
    *,
    document_id: str,
    meta: dict[str, Any],
    facts: dict[str, Any],
    relations: dict[str, Any],
) -> dict[str, Any]:
    document_blockers: list[dict[str, Any]] = []
    missing_required_sections = sorted(
        section_id
        for section_id, present in _as_dict(facts.get("section_presence")).items()
        if not bool(present)
    )
    for section_id in missing_required_sections:
        document_blockers.append(
            _make_blocker(
                ref=f"doc:{document_id}#{section_id}",
                kind="document_section",
                reason_code="missing_required_section",
                message=f"document {document_id} missing required section {section_id}",
            )
        )

    if not bool(facts.get("exists")):
        document_blockers.append(
            _make_blocker(
                ref=f"doc:{document_id}#exists",
                kind="document",
                reason_code="document_file_missing",
                message=f"document {document_id} file is missing",
            )
        )

    extracted_refs = _as_dict(facts.get("extracted_refs"))
    missing_relation_refs: list[str] = []
    for document_ref in _as_list(relations.get("document_refs")):
        if document_ref not in _as_list(extracted_refs.get("document_refs")):
            missing_relation_refs.append(f"doc:{document_ref}")
            document_blockers.append(
                _make_blocker(
                    ref=f"doc:{document_ref}",
                    kind="document_relation",
                    reason_code="missing_relation_ref",
                    message=f"document {document_id} missing relation ref {document_ref}",
                )
            )
    for module_ref in _as_list(relations.get("module_refs")):
        if module_ref not in _as_list(extracted_refs.get("module_refs")):
            missing_relation_refs.append(f"module:{module_ref}")
            document_blockers.append(
                _make_blocker(
                    ref=f"module:{module_ref}",
                    kind="module_relation",
                    reason_code="missing_relation_ref",
                    message=f"document {document_id} missing relation ref {module_ref}",
                )
            )
    for oq_ref in _as_list(relations.get("oq_refs")):
        if oq_ref not in _as_list(extracted_refs.get("oq_refs")):
            missing_relation_refs.append(f"oq:{oq_ref}")
            document_blockers.append(
                _make_blocker(
                    ref=f"oq:{oq_ref}",
                    kind="oq_relation",
                    reason_code="missing_relation_ref",
                    message=f"document {document_id} missing relation ref {oq_ref}",
                )
            )

    marker_counts = _as_dict(facts.get("marker_counts"))
    unresolved_markers = sum(
        int(marker_counts.get(key, 0) or 0) for key in ("todo", "tbd", "unresolved")
    )
    if unresolved_markers > 0:
        document_blockers.append(
            _make_blocker(
                ref=f"doc:{document_id}#markers",
                kind="document_marker",
                reason_code="document_markers_pending",
                message=f"document {document_id} still contains unresolved markers",
            )
        )

    repo_truth = _as_dict(facts.get("repo_truth"))
    missing_paths = sorted(
        {
            str(path)
            for path in _as_list(repo_truth.get("missing_paths"))
            if isinstance(path, str) and path.strip()
        }
    )
    direction_drift = _as_dict(facts.get("direction_drift"))
    future_terms = sorted(
        {
            str(term)
            for term in _as_list(direction_drift.get("future_blueprint_terms"))
            if isinstance(term, str) and term.strip()
        }
    )
    doc_type = str(meta.get("doc_type", "")).strip()
    if doc_type in {"design", "plan"} and (len(missing_paths) >= 2 or (missing_paths and future_terms)):
        missing_sample = ", ".join(missing_paths[:5])
        message = f"document {document_id} references repo paths not present in current repo: {missing_sample}"
        if future_terms:
            message += f"; future-target terms: {', '.join(future_terms)}"
        document_blockers.append(
            _make_blocker(
                ref=f"doc:{document_id}#repo_truth",
                kind="document_repo_truth",
                reason_code="document_repo_truth_mismatch",
                message=message,
            )
        )

    review_reasons: list[str] = []
    if not document_blockers:
        review_reasons.append("document_ready_for_review")

    return {
        "required_section_ids": [
            str(section.get("section_id"))
            for section in _as_list(meta.get("required_sections"))
            if isinstance(section, dict)
        ],
        "missing_required_sections": missing_required_sections,
        "missing_relation_refs": sorted(set(missing_relation_refs)),
        "document_blockers": _dedupe_blockers(document_blockers),
        "review_required": bool(review_reasons),
        "review_reasons": sorted(set(review_reasons) & REVIEW_REASONS),
        "assessed_ready": not bool(document_blockers),
    }


def _summarize_rounds(rounds: list[object]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    open_rounds: list[dict[str, Any]] = []
    for item in rounds:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", ""))
        if status:
            counts.update([status])
        if status in {"open", "in_progress", "review"}:
            open_rounds.append(item)
    return {
        "counts": {status: counts.get(status, 0) for status in ("open", "in_progress", "review", "closed")},
        "open_round_count": len(open_rounds),
    }


def _resolve_repo_root(state_path: Path) -> Path:
    normalized = state_path.resolve()
    for candidate in (normalized.parent, *normalized.parents):
        if _looks_like_repo_root(candidate):
            return candidate

    try:
        if normalized.parent.name == "governance" and normalized.parent.parent.name == "docs":
            return normalized.parent.parent.parent
    except IndexError:
        pass
    return normalized.parent


def _looks_like_repo_root(path: Path) -> bool:
    if (path / ".git").exists():
        return True

    has_agents = (path / "AGENTS.md").is_file()
    has_state = (path / "docs" / "governance" / "DOC_STATE.yaml").is_file()
    has_doc_governor = (path / "tools" / "doc_governor").is_dir()
    has_python_project = (path / "pytest.ini").is_file() or (path / "pyproject.toml").is_file()

    return (
        (has_agents and has_doc_governor)
        or (has_agents and has_state)
        or (has_state and has_doc_governor)
        or (has_python_project and has_doc_governor)
    )


def _finalize_module_derived(
    *,
    module_id: str,
    module_result: dict[str, Any],
    module_mode: bool,
) -> dict[str, Any]:
    candidate_blockers = module_result.get("candidate_blockers", [])
    downstream_blockers = module_result.get("downstream_blockers", [])
    gate_blockers = _dedupe_blockers(module_result.get("gate_blockers", []))
    candidate_blocker_refs = sorted(blocker["ref"] for blocker in candidate_blockers)
    downstream_blocker_refs = sorted(blocker["ref"] for blocker in downstream_blockers)
    blocker_refs = sorted(blocker["ref"] for blocker in gate_blockers)
    downstream_ready = not bool(downstream_blocker_refs)
    oq_review_only = bool(module_result.get("oq_review_only_refs"))

    review_reasons: list[str] = []
    if downstream_ready:
        review_reasons.append("downstream_ready_no_hard_blocker")
    if oq_review_only:
        review_reasons.append("oq_review_only")

    review_reasons = sorted(set(review_reasons) & REVIEW_REASONS)
    requirement_ids = _dedupe_strings(_as_list(module_result.get("requirement_ids")))
    return {
        "current_gate": "task_design_ready",
        "gate_result": "pass" if not blocker_refs else "blocked",
        "candidate_blockers": candidate_blockers,
        "candidate_blocker_refs": candidate_blocker_refs,
        "assessed_downstream_ready": downstream_ready,
        "downstream_blockers": downstream_blockers,
        "downstream_blocker_refs": downstream_blocker_refs,
        "gate_blockers": gate_blockers,
        "blocker_refs": blocker_refs,
        "requirement_ids": requirement_ids,
        "review_required": bool(review_reasons),
        "review_reasons": review_reasons,
        "ready_for_next_step": not bool(blocker_refs),
        "implementation_ready": False,
    }


def _finalize_subtask_derived(
    *,
    subtask_id: str,
    subtask_result: dict[str, Any],
) -> dict[str, Any]:
    candidate_blockers = subtask_result.get("candidate_blockers", [])
    downstream_blockers = subtask_result.get("downstream_blockers", [])
    implementation_blockers = subtask_result.get("implementation_blockers", [])
    gate_blockers = _dedupe_blockers(subtask_result.get("gate_blockers", []))

    candidate_blocker_refs = sorted(blocker["ref"] for blocker in candidate_blockers)
    downstream_blocker_refs = sorted(blocker["ref"] for blocker in downstream_blockers)
    implementation_blocker_refs = sorted(blocker["ref"] for blocker in implementation_blockers)
    blocker_refs = sorted(blocker["ref"] for blocker in gate_blockers)
    downstream_ready = not bool(downstream_blocker_refs)
    formal_window_open = (
        str(subtask_result.get("formal_window_status", "closed")) == "open"
    )
    implementation_blockers_without_open_or_approval = [
        ref
        for ref in implementation_blocker_refs
        if ref
        not in {
            "policy:formal_window_closed",
            "gate:implementation_approval_missing",
            "gate:maturity_missing",
        }
    ]
    can_open_formal_window = bool(
        not formal_window_open
        and not candidate_blocker_refs
        and not downstream_blocker_refs
        and not implementation_blockers_without_open_or_approval
    )
    implementation_ready_gate_pass = bool(
        formal_window_open
        and not candidate_blocker_refs
        and not downstream_blocker_refs
        and not implementation_blocker_refs
    )
    assessed_implementation_ready = implementation_ready_gate_pass
    can_generate_implementation_packet = implementation_ready_gate_pass
    can_mark_implementation_ready = implementation_ready_gate_pass
    oq_review_only = bool(subtask_result.get("oq_review_only_refs"))
    impl_activation = bool(subtask_result.get("implementation_doc_activation_recommended"))

    review_reasons: list[str] = []
    if downstream_ready:
        review_reasons.append("downstream_ready_no_hard_blocker")
    if oq_review_only:
        review_reasons.append("oq_review_only")
    if impl_activation:
        review_reasons.append("implementation_doc_activation_recommended")
    review_reasons = sorted(set(review_reasons) & REVIEW_REASONS)
    requirement_ids = _dedupe_strings(_as_list(subtask_result.get("requirement_ids")))

    return {
        "current_gate": "implementation_ready",
        "gate_result": "pass" if not blocker_refs else "blocked",
        "candidate_blockers": candidate_blockers,
        "candidate_blocker_refs": candidate_blocker_refs,
        "downstream_blockers": downstream_blockers,
        "downstream_blocker_refs": downstream_blocker_refs,
        "implementation_blockers": implementation_blockers,
        "implementation_blocker_refs": implementation_blocker_refs,
        "gate_blockers": gate_blockers,
        "blocker_refs": blocker_refs,
        "requirement_ids": requirement_ids,
        "formal_window_status": "open" if formal_window_open else "closed",
        "scoped_formal_window_open": formal_window_open,
        "can_open_formal_window": can_open_formal_window,
        "can_generate_implementation_packet": can_generate_implementation_packet,
        "can_mark_implementation_ready": can_mark_implementation_ready,
        "assessed_downstream_ready": downstream_ready,
        "assessed_implementation_ready": assessed_implementation_ready,
        "implementation_doc_activation_recommended": impl_activation,
        "implementation_doc_activation_reason": str(
            subtask_result.get("implementation_doc_activation_reason", "")
        ),
        "implementation_packet_inputs": _as_dict(
            subtask_result.get("implementation_packet_inputs")
        ),
        "formal_window_candidate_recommendation": _as_dict(
            subtask_result.get("formal_window_candidate_recommendation")
        ),
        "near_ready_for_formal_window_candidate": _as_dict(
            subtask_result.get("near_ready_for_formal_window_candidate")
        ),
        "review_required": bool(review_reasons),
        "review_reasons": review_reasons,
        "ready_for_next_step": not bool(blocker_refs),
        "implementation_ready": assessed_implementation_ready,
    }


def _build_summary(
    *,
    requirement_results: dict[str, dict[str, Any]],
    module_results: dict[str, dict[str, Any]],
    subtask_results: dict[str, dict[str, Any]],
    document_results: dict[str, dict[str, Any]],
    oq_payload: dict[str, Any],
    oq_source_map: dict[str, object],
    rounds_summary: dict[str, Any],
) -> dict[str, Any]:
    reason_counter: Counter[str] = Counter()
    for requirement in requirement_results.values():
        derived = requirement.get("derived", {})
        for blocker in derived.get("gate_blockers", []):
            reason_counter.update([blocker["reason_code"]])
    for module in module_results.values():
        derived = module.get("derived", {})
        for blocker in derived.get("candidate_blockers", []):
            reason_counter.update([blocker["reason_code"]])
        for blocker in derived.get("downstream_blockers", []):
            reason_counter.update([blocker["reason_code"]])
    for subtask in subtask_results.values():
        derived = subtask.get("derived", {})
        for blocker in derived.get("candidate_blockers", []):
            reason_counter.update([blocker["reason_code"]])
        for blocker in derived.get("downstream_blockers", []):
            reason_counter.update([blocker["reason_code"]])
        for blocker in derived.get("implementation_blockers", []):
            reason_counter.update([blocker["reason_code"]])
    for document in document_results.values():
        derived = document.get("derived", {})
        for blocker in derived.get("document_blockers", []):
            reason_counter.update([blocker["reason_code"]])

    summary = {
        "requirements_review_required": sum(
            1 for requirement in requirement_results.values() if requirement["derived"]["review_required"]
        ),
        "modules_review_required": sum(
            1 for module in module_results.values() if module["derived"]["review_required"]
        ),
        "subtasks_review_required": sum(
            1 for subtask in subtask_results.values() if subtask["derived"]["review_required"]
        ),
        "requirements_blocked_count": sum(
            1
            for requirement in requirement_results.values()
            if requirement["derived"]["blocker_refs"]
        ),
        "documents_review_required": sum(
            1 for document in document_results.values() if document["derived"]["review_required"]
        ),
        "modules_blocked_count": sum(
            1
            for module in module_results.values()
            if module["derived"]["candidate_blocker_refs"]
            or module["derived"]["downstream_blocker_refs"]
        ),
        "subtasks_blocked_count": sum(
            1
            for subtask in subtask_results.values()
            if subtask["derived"]["candidate_blocker_refs"]
            or subtask["derived"]["downstream_blocker_refs"]
            or subtask["derived"]["implementation_blocker_refs"]
        ),
        "documents_blocked_count": sum(
            1
            for document in document_results.values()
            if document["derived"]["document_blockers"]
        ),
        "blocked_by_reason_code": {
            reason: count
            for reason, count in sorted(reason_counter.items())
            if reason in BLOCKED_REASON_CODES and count > 0
        },
        "oq_gate_counts": {
            "observe_only.clear": 0,
            "observe_only.review_only": 0,
            "candidate_gate.clear": 0,
            "candidate_gate.review_only": 0,
            "candidate_gate.candidate_blocker": 0,
            "readiness_gate.clear": 0,
            "readiness_gate.review_only": 0,
            "readiness_gate.readiness_blocker": 0,
        },
        "rounds_open_count": int(_as_dict(rounds_summary.get("counts")).get("open", 0)),
        "rounds_in_progress_count": int(_as_dict(rounds_summary.get("counts")).get("in_progress", 0)),
        "rounds_review_count": int(_as_dict(rounds_summary.get("counts")).get("review", 0)),
    }

    for oq_id, oq_info in sorted(oq_payload.items()):
        source = oq_source_map.get(oq_id)
        if not isinstance(source, dict):
            continue
        source_gate_level = source.get("gate_level", "")
        if not source_gate_level:
            continue
        key = f"{source_gate_level}.{oq_info.get('derived_enforcement', '')}"
        if key in summary["oq_gate_counts"]:
            summary["oq_gate_counts"][key] += 1

    return summary


def _make_blocker(*, ref: str, kind: str, reason_code: str, message: str) -> dict[str, Any]:
    if not TYPED_BLOCKER_REF_RE.fullmatch(ref):
        raise ValueError(f"invalid blocker ref: {ref}")
    if reason_code not in BLOCKED_REASON_CODES:
        raise ValueError(f"unsupported blocker reason code: {reason_code}")
    return {
        "ref": ref,
        "kind": kind,
        "reason_code": reason_code,
        "message": message,
    }


def _dedupe_blockers(blockers: list[dict[str, Any]]) -> list[dict[str, str]]:
    ordered = []
    seen = set()
    for blocker in blockers:
        key = (blocker["ref"], blocker["kind"], blocker["reason_code"], blocker["message"])
        if key in seen:
            continue
        seen.add(key)
        ordered.append(blocker)
    ordered.sort(key=lambda item: (item["reason_code"], item["ref"], item["kind"], item["message"]))
    return ordered


def _extract_entities(payload: dict[str, Any], *, key: str) -> dict[str, dict[str, Any]]:
    entities = payload.get(key)
    entities = entities if isinstance(entities, dict) else {}
    extracted: dict[str, dict[str, Any]] = {}
    for entity_id, entity_value in entities.items():
        if not isinstance(entity_value, dict):
            continue
        derived = entity_value.get("derived")
        if isinstance(derived, dict):
            extracted[str(entity_id)] = derived
    return extracted


def _collect_blocker_keys(payload: dict[str, Any]) -> set[str]:
    blockers: set[str] = set()
    entity_maps = {
        "requirement": _extract_entities(payload, key="requirements"),
        "module": _extract_entities(payload, key="modules"),
        "subtask": _extract_entities(payload, key="subtasks"),
        "document": _extract_entities(payload, key="documents"),
    }
    for entity_type, entities in entity_maps.items():
        for entity_id, derived in entities.items():
            if entity_type == "requirement":
                blocker_keys = ("gate_blockers",)
            elif entity_type == "document":
                blocker_keys = ("document_blockers",)
            else:
                blocker_keys = (
                    "candidate_blockers",
                    "downstream_blockers",
                    "implementation_blockers",
                )
            for blocker_key in blocker_keys:
                for blocker in derived.get(blocker_key, []):
                    if not isinstance(blocker, dict):
                        continue
                    ref = str(blocker.get("ref", ""))
                    reason_code = str(blocker.get("reason_code", ""))
                    if not ref:
                        continue
                    blockers.add(f"{entity_type}:{entity_id}:{reason_code}:{ref}")
    return blockers


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _diff_boolean_field(
    *,
    current_entities: dict[str, dict[str, Any]],
    baseline_entities: dict[str, dict[str, Any]],
    field: str,
) -> dict[str, Any]:
    ids = sorted(set(current_entities) | set(baseline_entities))
    to_true: list[str] = []
    to_false: list[str] = []
    unchanged_true = 0
    unchanged_false = 0
    before_true = 0
    after_true = 0

    for entity_id in ids:
        before = bool(baseline_entities.get(entity_id, {}).get(field, False))
        after = bool(current_entities.get(entity_id, {}).get(field, False))
        if before:
            before_true += 1
        if after:
            after_true += 1
        if before and not after:
            to_false.append(entity_id)
        elif not before and after:
            to_true.append(entity_id)
        elif before and after:
            unchanged_true += 1
        else:
            unchanged_false += 1

    return {
        "before_true_count": before_true,
        "after_true_count": after_true,
        "delta_true_count": after_true - before_true,
        "changed_to_true": to_true,
        "changed_to_false": to_false,
        "unchanged_true_count": unchanged_true,
        "unchanged_false_count": unchanged_false,
    }


def _normalize_policy_token(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_")


def _clone_blockers(blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(blocker) for blocker in blockers if isinstance(blocker, dict)]


def _collect_native_requirement_relations(
    entities: dict[str, object],
    *,
    inherited_relations: dict[str, list[str]] | None = None,
    inherit_from_field: str | None = None,
) -> dict[str, list[str]]:
    relation_map: dict[str, list[str]] = {}
    inherited_relations = inherited_relations or {}
    for entity_id, entity_obj in entities.items():
        if not isinstance(entity_obj, dict):
            continue
        meta = entity_obj.get("meta")
        meta = meta if isinstance(meta, dict) else {}
        facts = entity_obj.get("facts")
        facts = facts if isinstance(facts, dict) else {}

        requirement_ids: list[str] = []
        meta_requirement_id = meta.get("requirement_id")
        if isinstance(meta_requirement_id, str) and meta_requirement_id.strip():
            requirement_ids.append(meta_requirement_id.strip())

        fact_requirement_ids = facts.get("requirement_ids")
        if isinstance(fact_requirement_ids, list):
            requirement_ids.extend(
                requirement_id.strip()
                for requirement_id in fact_requirement_ids
                if isinstance(requirement_id, str) and requirement_id.strip()
            )

        if not requirement_ids and inherit_from_field:
            upstream_entity_id = str(meta.get(inherit_from_field) or "").strip()
            if upstream_entity_id:
                requirement_ids.extend(inherited_relations.get(upstream_entity_id, []))

        normalized = _dedupe_strings(requirement_ids)
        if normalized:
            relation_map[str(entity_id)] = normalized
    return relation_map


def _prefer_native_requirement_relations(
    *,
    fallback_relations: dict[str, list[str]],
    native_relations: dict[str, list[str]],
) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = {}
    for entity_id, requirement_ids in fallback_relations.items():
        normalized = _dedupe_strings(
            [
                requirement_id
                for requirement_id in requirement_ids
                if isinstance(requirement_id, str) and requirement_id.strip()
            ]
        )
        if normalized:
            merged[str(entity_id)] = normalized

    for entity_id, requirement_ids in native_relations.items():
        normalized = _dedupe_strings(
            [
                requirement_id
                for requirement_id in requirement_ids
                if isinstance(requirement_id, str) and requirement_id.strip()
            ]
        )
        if normalized:
            merged[str(entity_id)] = normalized
    return merged


def _filter_known_requirement_relations(
    relation_map: dict[str, list[str]],
    known_requirement_ids: set[str],
) -> dict[str, list[str]]:
    filtered: dict[str, list[str]] = {}
    for entity_id, requirement_ids in relation_map.items():
        normalized = [
            requirement_id
            for requirement_id in requirement_ids
            if requirement_id in known_requirement_ids
        ]
        if normalized:
            filtered[str(entity_id)] = normalized
    return filtered


def _build_candidate_recommendation(
    *,
    facts: dict[str, Any],
    confirmed: dict[str, Any],
) -> dict[str, Any]:
    recommended = bool(facts.get("formal_window_candidate_recommended", False))
    candidate_status = str(confirmed.get("candidate_status", "none") or "none")
    state = str(facts.get("formal_window_candidate_state", "") or "").strip()
    if not state:
        state = "document_layer_recommended" if recommended else "none"
    return {
        "recommended": recommended,
        "source": str(facts.get("formal_window_candidate_source", "") or "").strip(),
        "review_status": str(
            facts.get("formal_window_candidate_review_status", "") or ""
        ).strip(),
        "state": state,
        "notes": str(facts.get("formal_window_candidate_notes", "") or "").strip(),
        "candidate_status": candidate_status,
        "tool_effect": "facts_only" if recommended else "state_only",
        "means_formal_window_open": False,
        "means_implementation_ready": False,
        "means_packet_ready": False,
    }


def _build_near_ready_recommendation(facts: dict[str, Any]) -> dict[str, Any]:
    enabled = bool(facts.get("near_ready_for_formal_window_candidate", False))
    state = str(facts.get("near_ready_state", "") or "").strip()
    if not state:
        state = "document_layer_only" if enabled else "none"
    return {
        "enabled": enabled,
        "reason": str(facts.get("near_ready_reason", "") or "").strip(),
        "blockers": _dedupe_strings(
            [str(item) for item in _as_list(facts.get("near_ready_blockers"))]
        ),
        "state": state,
        "tool_effect": "facts_only" if enabled else "none",
        "means_candidate_status_candidate": False,
        "means_downstream_ready": False,
        "means_formal_window_open": False,
        "means_implementation_ready": False,
        "means_packet_ready": False,
    }


def _build_requirement_blocker_map(
    relation_map: dict[str, list[str]],
    requirement_derived_map: dict[str, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    blockers_by_entity: dict[str, list[dict[str, Any]]] = {}
    for entity_id, requirement_ids in relation_map.items():
        blockers: list[dict[str, Any]] = []
        for requirement_id in requirement_ids:
            requirement_result = requirement_derived_map.get(str(requirement_id), {})
            blockers.extend(_clone_blockers(requirement_result.get("gate_blockers", [])))
        if blockers:
            blockers_by_entity[str(entity_id)] = blockers
    return blockers_by_entity


def _build_subtask_packet_inputs(
    *,
    subtask_id: str,
    module_id: str,
    subtask_path: str,
    design_doc: dict[str, object],
    implementation_doc: dict[str, object],
    repo_root: Path,
    requirement_id: str | None,
) -> dict[str, Any]:
    canonical_design_path = _join_relative_path(subtask_path, "SUBTASK_DESIGN.md")
    canonical_implementation_path = _join_relative_path(
        subtask_path,
        "SUBTASK_IMPLEMENTATION.md",
    )
    design_relative_path, design_warnings = _resolve_subtask_doc_relative_path(
        repo_root=repo_root,
        slot_name="design_doc",
        slot_doc=design_doc,
        canonical_relative_path=canonical_design_path,
    )
    (
        implementation_relative_path,
        implementation_warnings,
    ) = _resolve_subtask_doc_relative_path(
        repo_root=repo_root,
        slot_name="implementation_doc",
        slot_doc=implementation_doc,
        canonical_relative_path=canonical_implementation_path,
    )
    design_text = _read_text_if_exists(repo_root / design_relative_path)
    implementation_text = _read_text_if_exists(repo_root / implementation_relative_path)
    design_sections = _parse_markdown_sections(design_text)
    implementation_sections = _parse_markdown_sections(implementation_text)

    goal_items = _extract_section_items(implementation_sections.get("本轮实施目标", []))
    if not goal_items:
        goal_items = _extract_section_items(design_sections.get("子任务目标", []))

    allowed_modify_paths = _extract_section_items(implementation_sections.get("允许修改", []))
    if not allowed_modify_paths:
        allowed_modify_paths = _extract_section_items(implementation_sections.get("允许修改范围", []))
    forbidden_paths = _extract_section_items(implementation_sections.get("禁止修改", []))
    path_conflicts = _detect_path_conflicts(
        allowed_paths=allowed_modify_paths,
        forbidden_paths=forbidden_paths,
    )
    required_tests = _dedupe_strings(
        _extract_section_items(implementation_sections.get("自动化验证", []))
        + _extract_section_items(implementation_sections.get("手动验证", []))
    )
    if not required_tests:
        required_tests = _extract_section_items(implementation_sections.get("测试与验证", []))
    acceptance_criteria = _extract_section_items(implementation_sections.get("完成判定", []))

    language_violations: list[dict[str, str]] = []
    for relative_path, text in (
        (design_relative_path, design_text),
        (implementation_relative_path, implementation_text),
    ):
        if not text.strip():
            continue
        for diagnostic in check_markdown_language(
            path=relative_path,
            text=text,
            entity_type="subtask",
            entity_id=subtask_id,
        ):
            language_violations.append(
                {
                    "code": f"language_non_compliant_{_normalize_policy_token(diagnostic.code)}",
                    "path": relative_path,
                    "message": diagnostic.message,
                }
            )

    return {
        "task_id": subtask_id,
        "module_id": module_id,
        "requirement_id": requirement_id,
        "goal": "\n".join(goal_items).strip(),
        "allowed_modify_paths": allowed_modify_paths,
        "forbidden_paths": forbidden_paths,
        "path_conflicts": path_conflicts,
        "required_tests": required_tests,
        "acceptance_criteria": acceptance_criteria,
        "official_doc_paths": {
            "design_doc": design_relative_path,
            "implementation_doc": implementation_relative_path,
        },
        "doc_path_resolution_warnings": design_warnings + implementation_warnings,
        "language_violations": language_violations,
    }


def _detect_path_conflicts(
    *,
    allowed_paths: list[str],
    forbidden_paths: list[str],
) -> list[dict[str, str]]:
    conflicts: list[dict[str, str]] = []
    for allowed in allowed_paths:
        for forbidden in forbidden_paths:
            if _paths_conflict(allowed, forbidden):
                conflicts.append(
                    {
                        "allowed": allowed,
                        "forbidden": forbidden,
                    }
                )
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in conflicts:
        key = (item["allowed"], item["forbidden"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _paths_conflict(allowed_path: str, forbidden_path: str) -> bool:
    allowed = _normalize_path_pattern(allowed_path)
    forbidden = _normalize_path_pattern(forbidden_path)
    if not allowed or not forbidden:
        return False
    if allowed == forbidden:
        return True
    if forbidden.endswith("/**"):
        prefix = forbidden[:-3].rstrip("/")
        return allowed == prefix or allowed.startswith(prefix + "/")
    if forbidden.endswith("/*"):
        prefix = forbidden[:-2].rstrip("/")
        return allowed.startswith(prefix + "/")
    if allowed.endswith("/**"):
        prefix = allowed[:-3].rstrip("/")
        return forbidden == prefix or forbidden.startswith(prefix + "/")
    return allowed.startswith(forbidden.rstrip("/") + "/") or forbidden.startswith(
        allowed.rstrip("/") + "/"
    )


def _normalize_path_pattern(value: str) -> str:
    text = str(value).strip().strip("`'\"")
    text = text.replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text.rstrip("/")


def _join_relative_path(base_path: str, filename: str) -> str:
    base = Path(base_path)
    return (base / filename).as_posix()


def _registered_doc_path(slot_doc: dict[str, object]) -> str:
    path = slot_doc.get("path", "")
    return str(path).strip() if path is not None else ""


def _resolve_subtask_doc_relative_path(
    *,
    repo_root: Path,
    slot_name: str,
    slot_doc: dict[str, object],
    canonical_relative_path: str,
) -> tuple[str, list[str]]:
    registered_relative_path = _registered_doc_path(slot_doc)
    warnings: list[str] = []
    if registered_relative_path:
        registered_path = Path(registered_relative_path)
        registered_target = (
            registered_path
            if registered_path.is_absolute()
            else repo_root / registered_path
        )
        if registered_target.is_file():
            return registered_path.as_posix(), warnings
        warnings.append(
            (
                f"{slot_name} registered path not found: {registered_relative_path}; "
                f"fallback to canonical path: {canonical_relative_path}"
            )
        )

    canonical_target = repo_root / canonical_relative_path
    if canonical_target.is_file() or not registered_relative_path:
        return canonical_relative_path, warnings
    return Path(registered_relative_path).as_posix(), warnings


def _read_text_if_exists(path: Path) -> str:
    try:
        if path.exists() and path.is_file():
            return path.read_text(encoding="utf-8")
    except OSError:
        return ""
    return ""


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
    normalized = value.strip()
    normalized = HEADING_NUMBER_RE.sub("", normalized)
    return normalized.strip()


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
        value = normalized
        if "：" in value:
            value = value.split("：", 1)[1].strip()
        elif ":" in value:
            value = value.split(":", 1)[1].strip()
        value = value.strip()
        if value:
            items.append(value)
    return _dedupe_strings(items)


def _dedupe_strings(items: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return ordered
