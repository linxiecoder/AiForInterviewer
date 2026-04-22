from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .document_scan import scan_document
from .diagnostics import Diagnostic, make_diagnostic, make_evidence
from .schema import REQUIRED_MODULE_SLOTS, SCHEMA_VERSION, TYPED_BLOCKER_REF_RE
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
    "missing_required_section",
    "missing_relation_ref",
    "document_markers_pending",
    "document_file_missing",
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
    oqs = state.get("oqs")
    oqs = oqs if isinstance(oqs, dict) else {}
    modules = state.get("modules")
    modules = modules if isinstance(modules, dict) else {}
    subtasks = state.get("subtasks")
    subtasks = subtasks if isinstance(subtasks, dict) else {}
    documents = state.get("documents")
    documents = documents if isinstance(documents, dict) else {}
    governance_rounds = state.get("governance_rounds")
    governance_rounds = governance_rounds if isinstance(governance_rounds, list) else []

    global_policy = state.get("global_policy")
    global_policy = global_policy if isinstance(global_policy, dict) else {}
    formal_window_open = bool(global_policy.get("formal_window_open", True))

    oq_payload = _evaluate_oqs(oqs)
    module_derived_map: dict[str, dict[str, Any]] = {}
    for module_id, module_obj in modules.items():
        if isinstance(module_obj, dict):
            module_derived_map[module_id] = _evaluate_module(module_id, module_obj, oq_payload)

    subtask_derived_map: dict[str, dict[str, Any]] = {}
    for subtask_id, subtask_obj in subtasks.items():
        if isinstance(subtask_obj, dict):
            subtask_derived_map[subtask_id] = _evaluate_subtask(
                subtask_id=subtask_id,
                subtask_obj=subtask_obj,
                oq_payload=oq_payload,
                module_derived_map=module_derived_map,
                formal_window_open=formal_window_open,
            )

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
        repo_root=_resolve_repo_root(state_path),
    )
    rounds_summary = _summarize_rounds(governance_rounds)

    summary = _build_summary(
        module_results=module_derived_wrapped,
        subtask_results=subtask_derived_wrapped,
        document_results=document_results,
        oq_payload=oq_payload,
        oq_source_map=oqs,
        rounds_summary=rounds_summary,
    )

    return {
        "summary": summary,
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

    current_modules = _extract_entities(current_payload, key="modules")
    current_subtasks = _extract_entities(current_payload, key="subtasks")
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
        "oq_review_only_refs": sorted(set(oq_review_only_refs)),
        "assessed_downstream_ready": downstream_ready,
    }


def _evaluate_subtask(
    *,
    subtask_id: str,
    subtask_obj: dict[str, object],
    oq_payload: dict[str, Any],
    module_derived_map: dict[str, dict[str, Any]],
    formal_window_open: bool,
) -> dict[str, Any]:
    facts = subtask_obj.get("facts")
    facts = facts if isinstance(facts, dict) else {}
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
                message=f"subtask {subtask_id} implementation_doc_state is not active_working_doc",
            )
        )
    if not formal_window_open:
        implementation_blockers.append(
            _make_blocker(
                ref="policy:formal_window_closed",
                kind="policy",
                reason_code="formal_window_closed",
                message=f"formal window is closed for subtask {subtask_id}",
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
        "oq_review_only_refs": sorted(set(oq_review_only_refs)),
        "implementation_doc_activation_recommended": implementation_doc_activation_recommended,
        "implementation_doc_activation_reason": implementation_doc_activation_reason,
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
    try:
        if normalized.parent.name == "governance" and normalized.parent.parent.name == "docs":
            return normalized.parent.parent.parent
    except IndexError:
        pass
    return normalized.parent


def _finalize_module_derived(
    *,
    module_id: str,
    module_result: dict[str, Any],
    module_mode: bool,
) -> dict[str, Any]:
    candidate_blockers = module_result.get("candidate_blockers", [])
    downstream_blockers = module_result.get("downstream_blockers", [])
    candidate_blocker_refs = sorted(blocker["ref"] for blocker in candidate_blockers)
    downstream_blocker_refs = sorted(blocker["ref"] for blocker in downstream_blockers)
    downstream_ready = not bool(downstream_blocker_refs)
    oq_review_only = bool(module_result.get("oq_review_only_refs"))

    review_reasons: list[str] = []
    if downstream_ready:
        review_reasons.append("downstream_ready_no_hard_blocker")
    if oq_review_only:
        review_reasons.append("oq_review_only")

    review_reasons = sorted(set(review_reasons) & REVIEW_REASONS)
    return {
        "candidate_blockers": candidate_blockers,
        "candidate_blocker_refs": candidate_blocker_refs,
        "assessed_downstream_ready": downstream_ready,
        "downstream_blockers": downstream_blockers,
        "downstream_blocker_refs": downstream_blocker_refs,
        "review_required": bool(review_reasons),
        "review_reasons": review_reasons,
    }


def _finalize_subtask_derived(
    *,
    subtask_id: str,
    subtask_result: dict[str, Any],
) -> dict[str, Any]:
    candidate_blockers = subtask_result.get("candidate_blockers", [])
    downstream_blockers = subtask_result.get("downstream_blockers", [])
    implementation_blockers = subtask_result.get("implementation_blockers", [])

    candidate_blocker_refs = sorted(blocker["ref"] for blocker in candidate_blockers)
    downstream_blocker_refs = sorted(blocker["ref"] for blocker in downstream_blockers)
    implementation_blocker_refs = sorted(blocker["ref"] for blocker in implementation_blockers)
    downstream_ready = not bool(downstream_blocker_refs)
    assessed_implementation_ready = not bool(implementation_blocker_refs)
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

    return {
        "candidate_blockers": candidate_blockers,
        "candidate_blocker_refs": candidate_blocker_refs,
        "downstream_blockers": downstream_blockers,
        "downstream_blocker_refs": downstream_blocker_refs,
        "implementation_blockers": implementation_blockers,
        "implementation_blocker_refs": implementation_blocker_refs,
        "assessed_downstream_ready": downstream_ready,
        "assessed_implementation_ready": assessed_implementation_ready,
        "implementation_doc_activation_recommended": impl_activation,
        "implementation_doc_activation_reason": str(
            subtask_result.get("implementation_doc_activation_reason", "")
        ),
        "review_required": bool(review_reasons),
        "review_reasons": review_reasons,
    }


def _build_summary(
    *,
    module_results: dict[str, dict[str, Any]],
    subtask_results: dict[str, dict[str, Any]],
    document_results: dict[str, dict[str, Any]],
    oq_payload: dict[str, Any],
    oq_source_map: dict[str, object],
    rounds_summary: dict[str, Any],
) -> dict[str, Any]:
    reason_counter: Counter[str] = Counter()
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
        "modules_review_required": sum(
            1 for module in module_results.values() if module["derived"]["review_required"]
        ),
        "subtasks_review_required": sum(
            1 for subtask in subtask_results.values() if subtask["derived"]["review_required"]
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
        "module": _extract_entities(payload, key="modules"),
        "subtask": _extract_entities(payload, key="subtasks"),
        "document": _extract_entities(payload, key="documents"),
    }
    for entity_type, entities in entity_maps.items():
        for entity_id, derived in entities.items():
            for blocker_key in (
                "candidate_blockers",
                "downstream_blockers",
                "implementation_blockers",
                "document_blockers",
            ):
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
