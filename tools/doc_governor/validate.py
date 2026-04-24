from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from .diagnostics import Diagnostic, make_diagnostic, make_evidence
from .naming_rules import (
    MODULE_ID_RE,
    REQUIREMENT_ID_RE,
    REQUIREMENT_SCOPE_KINDS,
    SUBTASK_ID_RE,
    extract_module_id_from_path,
    extract_subtask_id_from_path,
    is_valid_requirement_path,
)
from .rules import evaluate_rules
from .schema import (
    CANDIDATE_STATUSES,
    DOCUMENT_STATUSES,
    DOCUMENT_TYPES,
    GOVERNANCE_ROUND_REQUIRED_FIELDS,
    GOVERNANCE_ROUND_STATUSES,
    IMPLEMENTATION_DOC_STATES,
    MATURITY_LEVELS,
    MODULE_DOC_SLOTS,
    READINESS_STATUSES,
    REQUIREMENT_RELATION_ENTITY_TYPES,
    REQUIREMENT_RELATION_FACT_FIELD,
    REQUIREMENT_RELATION_META_FIELD,
    REVIEW_STATUSES,
    SCHEMA_VERSION,
    SUBTASK_DOC_SLOTS,
    TYPED_BLOCKER_REF_RE,
)


REQUIRED_TOP_LEVEL_FIELDS = (
    "schema_version",
    "global_policy",
    "oqs",
    "modules",
    "subtasks",
)

REQUIRED_GLOBAL_POLICY_FIELDS = (
    "auto_open_enabled",
    "require_confirmation_for_state_writeback",
    "strict_template_gate",
    "formal_window_open",
    "paths",
)

REQUIRED_GLOBAL_POLICY_PATH_FIELDS = ("modules_root", "open_questions_doc", "task_index_doc")

REQUIRED_MODULE_FACT_FIELDS = (
    "upstream_module_ids",
    "related_oq_ids",
    "legacy_locked",
    "declared_blocker_refs",
    "docs",
)

REQUIRED_SUBTASK_FACT_FIELDS = (
    "upstream_module_ids",
    "related_oq_ids",
    "legacy_locked",
    "declared_blocker_refs",
    "design_doc",
    "implementation_doc",
)

REQUIRED_CONFIRMED_FIELDS = (
    "maturity",
    "candidate_status",
    "review_status",
    "readiness",
    "blocker_refs",
    "last_transition_id",
    "last_confirmed_at",
    "last_confirmed_by",
)

SUBTASK_CONFIRMED_REQUIRED_FIELDS = ("implementation_doc_state",) + REQUIRED_CONFIRMED_FIELDS
DOCUMENT_CONFIRMED_REQUIRED_FIELDS = (
    "maturity",
    "status",
    "review_status",
    "blocker_refs",
    "active_round_id",
    "last_round_id",
    "last_transition_id",
    "last_confirmed_at",
    "last_confirmed_by",
)

DOCUMENT_ID_RE = re.compile(r"^DOC-[A-Z0-9-]+$")

def validate_state_file(state_path: Path) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []

    try:
        import yaml
    except ImportError as exc:
        return [
            make_diagnostic(
                code="SCHEMA_PYYAML_UNAVAILABLE",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="python.dependencies.yaml",
                message="PyYAML is required to validate DOC_STATE file.",
                evidence=[
                    make_evidence(
                        type="dependency",
                        path=state_path.as_posix(),
                        ref="import yaml",
                        value=str(exc),
                    )
                ],
            )
        ]

    try:
        state_text = state_path.read_text(encoding="utf-8")
        data = yaml.safe_load(state_text)
    except FileNotFoundError as exc:
        return [
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="input.path",
                message=f"state file not found: {state_path}",
                evidence=[
                    make_evidence(
                        type="file_scan",
                        path=state_path.as_posix(),
                        ref="exists",
                        value=False,
                    )
                ],
            )
        ]
    except Exception as exc:  # noqa: BLE001
        return [
            make_diagnostic(
                code="SCHEMA_INVALID_FILE_FORMAT",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="input.path",
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
        ]

    if not isinstance(data, dict):
        return [
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
                        ref="yaml.root_type",
                        value=type(data).__name__,
                    )
                ],
            )
        ]

    state: dict[str, object] = data

    diagnostics.extend(_validate_top_level(state, state_path))
    diagnostics.extend(_validate_governance_rounds(state.get("governance_rounds"), state_path))
    requirements_obj = state.get("requirements")
    modules_obj = state.get("modules")
    subtasks_obj = state.get("subtasks")

    diagnostics.extend(_validate_requirements(requirements_obj, state_path))
    known_requirement_ids = _collect_known_requirement_ids(requirements_obj)
    diagnostics.extend(
        _validate_modules(
            modules_obj,
            state_path,
            known_requirement_ids=known_requirement_ids,
        )
    )
    diagnostics.extend(
        _validate_subtasks(
            subtasks_obj,
            state_path,
            known_requirement_ids=known_requirement_ids,
        )
    )
    diagnostics.extend(
        _validate_requirement_relation_consistency(
            requirements_obj=requirements_obj,
            modules_obj=modules_obj,
            subtasks_obj=subtasks_obj,
            state_path=state_path,
            known_requirement_ids=known_requirement_ids,
            requirement_mode=_extract_requirement_mode(state.get("global_policy")),
        )
    )
    diagnostics.extend(_validate_documents(state.get("documents"), state_path))

    # Schema validation and rule validation are independent by design.
    diagnostics.extend(evaluate_rules(state))

    return diagnostics


def _collect_known_requirement_ids(requirements_obj: object) -> set[str]:
    if not isinstance(requirements_obj, dict):
        return set()
    return {
        str(requirement_id)
        for requirement_id in requirements_obj.keys()
        if REQUIREMENT_ID_RE.fullmatch(str(requirement_id))
    }


def _extract_requirement_mode(global_policy_obj: object) -> str:
    if not isinstance(global_policy_obj, dict):
        return ""
    asset_policy = global_policy_obj.get("asset_policy")
    if not isinstance(asset_policy, dict):
        return ""
    requirement_mode = asset_policy.get("requirement_mode")
    if not isinstance(requirement_mode, str):
        return ""
    return requirement_mode.strip()


def _validate_top_level(state: dict[str, object], state_path: Path) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for key in REQUIRED_TOP_LEVEL_FIELDS:
        if key not in state:
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type="system",
                    entity_id="GLOBAL",
                    field_path=key,
                    message=f"Missing required top-level field: {key}",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=key,
                            value=None,
                        )
                    ],
                )
            )

    if "schema_version" in state and state.get("schema_version") != SCHEMA_VERSION:
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
                        value=state.get("schema_version"),
                    )
                ],
            )
        )

    global_policy = state.get("global_policy")
    if not isinstance(global_policy, dict):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type="global_policy",
                entity_id="GLOBAL",
                field_path="global_policy",
                message="global_policy must be an object.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref="global_policy",
                        value=type(global_policy).__name__,
                    )
                ],
            )
        )
        return diagnostics

    for key in REQUIRED_GLOBAL_POLICY_FIELDS:
        if key not in global_policy:
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type="global_policy",
                    entity_id="GLOBAL",
                    field_path=f"global_policy.{key}",
                    message=f"Missing required global policy field: {key}",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"global_policy.{key}",
                            value=None,
                        )
                    ],
                )
            )

    paths = global_policy.get("paths")
    if isinstance(paths, dict):
        for key in REQUIRED_GLOBAL_POLICY_PATH_FIELDS:
            if key not in paths:
                diagnostics.append(
                    make_diagnostic(
                        code="SCHEMA_MISSING_REQUIRED_FIELD",
                        severity="error",
                        entity_type="global_policy",
                        entity_id="GLOBAL",
                        field_path=f"global_policy.paths.{key}",
                        message=f"Missing required path field: {key}",
                        evidence=[
                            make_evidence(
                                type="state_check",
                                path=state_path.as_posix(),
                                ref=f"global_policy.paths.{key}",
                                value=None,
                            )
                        ],
                    )
                )
    else:
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type="global_policy",
                entity_id="GLOBAL",
                field_path="global_policy.paths",
                message="global_policy.paths must be an object.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref="global_policy.paths",
                        value=type(paths).__name__,
                    )
                ],
            )
        )

    asset_policy = global_policy.get("asset_policy")
    if asset_policy is not None:
        if not isinstance(asset_policy, dict):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type="global_policy",
                    entity_id="GLOBAL",
                    field_path="global_policy.asset_policy",
                    message="global_policy.asset_policy must be an object.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref="global_policy.asset_policy",
                            value=type(asset_policy).__name__,
                        )
                    ],
                )
            )
        else:
            requirement_mode = asset_policy.get("requirement_mode")
            if requirement_mode is not None and (
                not isinstance(requirement_mode, str)
                or requirement_mode not in REQUIREMENT_SCOPE_KINDS
            ):
                diagnostics.append(
                    make_diagnostic(
                        code="SCHEMA_UNKNOWN_ENUM_VALUE",
                        severity="error",
                        entity_type="global_policy",
                        entity_id="GLOBAL",
                        field_path="global_policy.asset_policy.requirement_mode",
                        message="Unknown requirement_mode value.",
                        evidence=[
                            make_evidence(
                                type="state_check",
                                path=state_path.as_posix(),
                                ref="global_policy.asset_policy.requirement_mode",
                                value=requirement_mode,
                            )
                        ],
                    )
                )

    return diagnostics


def _validate_governance_rounds(rounds_obj: object, state_path: Path) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if rounds_obj is None:
        return diagnostics
    if not isinstance(rounds_obj, list):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_INVALID_GOVERNANCE_ROUND_SHAPE",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="governance_rounds",
                message="governance_rounds must be a list.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref="governance_rounds",
                        value=type(rounds_obj).__name__,
                    )
                ],
            )
        )
        return diagnostics

    for index, item in enumerate(rounds_obj):
        field_root = f"governance_rounds[{index}]"
        if not isinstance(item, dict):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_INVALID_GOVERNANCE_ROUND_SHAPE",
                    severity="error",
                    entity_type="system",
                    entity_id="GLOBAL",
                    field_path=field_root,
                    message="governance_rounds entry must be an object.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=field_root,
                            value=type(item).__name__,
                        )
                    ],
                )
            )
            continue

        for key in GOVERNANCE_ROUND_REQUIRED_FIELDS:
            if key not in item:
                diagnostics.append(
                    make_diagnostic(
                        code="SCHEMA_MISSING_GOVERNANCE_ROUND_FIELD",
                        severity="error",
                        entity_type="system",
                        entity_id="GLOBAL",
                        field_path=f"{field_root}.{key}",
                        message=f"Missing governance round field: {key}",
                        evidence=[
                            make_evidence(
                                type="state_check",
                                path=state_path.as_posix(),
                                ref=f"{field_root}.{key}",
                                value=None,
                            )
                        ],
                    )
                )

        for key in ("round_id", "workflow", "topic", "scope", "opened_by"):
            value = item.get(key)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                diagnostics.append(
                    make_diagnostic(
                        code="SCHEMA_INVALID_GOVERNANCE_ROUND_SHAPE",
                        severity="error",
                        entity_type="system",
                        entity_id="GLOBAL",
                        field_path=f"{field_root}.{key}",
                        message=f"{key} must be a non-empty string.",
                        evidence=[
                            make_evidence(
                                type="state_check",
                                path=state_path.as_posix(),
                                ref=f"{field_root}.{key}",
                                value=value,
                            )
                        ],
                    )
                )

        status = item.get("status")
        if status is not None and status not in GOVERNANCE_ROUND_STATUSES:
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_INVALID_GOVERNANCE_ROUND_ENUM",
                    severity="error",
                    entity_type="system",
                    entity_id="GLOBAL",
                    field_path=f"{field_root}.status",
                    message="governance round status must be one of open|in_progress|review|closed.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"{field_root}.status",
                            value=status,
                        )
                    ],
                )
            )

        opened_at = item.get("opened_at")
        if opened_at is not None and not _is_iso_datetime(opened_at):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_INVALID_GOVERNANCE_ROUND_TIME",
                    severity="error",
                    entity_type="system",
                    entity_id="GLOBAL",
                    field_path=f"{field_root}.opened_at",
                    message="opened_at must be ISO-8601 datetime string.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"{field_root}.opened_at",
                            value=opened_at,
                        )
                    ],
                )
            )

        for key in ("started_at", "review_at", "closed_at"):
            value = item.get(key)
            if value is not None and not _is_iso_datetime(value):
                diagnostics.append(
                    make_diagnostic(
                        code="SCHEMA_INVALID_GOVERNANCE_ROUND_TIME",
                        severity="error",
                        entity_type="system",
                        entity_id="GLOBAL",
                        field_path=f"{field_root}.{key}",
                        message=f"{key} must be ISO-8601 datetime string.",
                        evidence=[
                            make_evidence(
                                type="state_check",
                                path=state_path.as_posix(),
                                ref=f"{field_root}.{key}",
                                value=value,
                            )
                        ],
                    )
                )

        decision_refs = item.get("decision_refs")
        if decision_refs is not None:
            if not isinstance(decision_refs, list):
                diagnostics.append(
                    make_diagnostic(
                        code="SCHEMA_INVALID_GOVERNANCE_ROUND_SHAPE",
                        severity="error",
                        entity_type="system",
                        entity_id="GLOBAL",
                        field_path=f"{field_root}.decision_refs",
                        message="decision_refs must be a list.",
                        evidence=[
                            make_evidence(
                                type="state_check",
                                path=state_path.as_posix(),
                                ref=f"{field_root}.decision_refs",
                                value=type(decision_refs).__name__,
                            )
                        ],
                    )
                )
            else:
                for ref_index, ref in enumerate(decision_refs):
                    if not isinstance(ref, str) or not ref.strip():
                        diagnostics.append(
                            make_diagnostic(
                                code="SCHEMA_INVALID_GOVERNANCE_ROUND_SHAPE",
                                severity="error",
                                entity_type="system",
                                entity_id="GLOBAL",
                                field_path=f"{field_root}.decision_refs[{ref_index}]",
                                message="decision_refs entries must be non-empty strings.",
                                evidence=[
                                    make_evidence(
                                        type="state_check",
                                        path=state_path.as_posix(),
                                        ref=f"{field_root}.decision_refs[{ref_index}]",
                                        value=ref,
                                    )
                                ],
                            )
                        )

        target_documents = item.get("target_documents")
        if not isinstance(target_documents, list):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_INVALID_GOVERNANCE_ROUND_SHAPE",
                    severity="error",
                    entity_type="system",
                    entity_id="GLOBAL",
                    field_path=f"{field_root}.target_documents",
                    message="target_documents must be a list.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"{field_root}.target_documents",
                            value=type(target_documents).__name__,
                        )
                    ],
                )
            )
        else:
            for target_index, target in enumerate(target_documents):
                target_root = f"{field_root}.target_documents[{target_index}]"
                if not isinstance(target, dict):
                    diagnostics.append(
                        make_diagnostic(
                            code="SCHEMA_INVALID_GOVERNANCE_ROUND_SHAPE",
                            severity="error",
                            entity_type="system",
                            entity_id="GLOBAL",
                            field_path=target_root,
                            message="target_documents entry must be an object.",
                            evidence=[
                                make_evidence(
                                    type="state_check",
                                    path=state_path.as_posix(),
                                    ref=target_root,
                                    value=type(target).__name__,
                                )
                            ],
                        )
                    )
                    continue
                document_id = target.get("document_id")
                if not isinstance(document_id, str) or not document_id.strip():
                    diagnostics.append(
                        make_diagnostic(
                            code="SCHEMA_INVALID_GOVERNANCE_ROUND_SHAPE",
                            severity="error",
                            entity_type="system",
                            entity_id="GLOBAL",
                            field_path=f"{target_root}.document_id",
                            message="document_id must be a non-empty string.",
                            evidence=[
                                make_evidence(
                                    type="state_check",
                                    path=state_path.as_posix(),
                                    ref=f"{target_root}.document_id",
                                    value=document_id,
                                )
                            ],
                        )
                    )
                target_sections = target.get("target_sections")
                if not isinstance(target_sections, list) or any(
                    not isinstance(section, str) or not section.strip() for section in target_sections
                ):
                    diagnostics.append(
                        make_diagnostic(
                            code="SCHEMA_INVALID_GOVERNANCE_ROUND_SHAPE",
                            severity="error",
                            entity_type="system",
                            entity_id="GLOBAL",
                            field_path=f"{target_root}.target_sections",
                            message="target_sections must be a list of non-empty strings.",
                            evidence=[
                                make_evidence(
                                    type="state_check",
                                    path=state_path.as_posix(),
                                    ref=f"{target_root}.target_sections",
                                    value=target_sections,
                                )
                            ],
                        )
                    )

        for list_field in ("required_evidence_refs", "exit_criteria", "writeback_items"):
            value = item.get(list_field)
            if not isinstance(value, list) or any(
                not isinstance(entry, str) or not entry.strip() for entry in value
            ):
                diagnostics.append(
                    make_diagnostic(
                        code="SCHEMA_INVALID_GOVERNANCE_ROUND_SHAPE",
                        severity="error",
                        entity_type="system",
                        entity_id="GLOBAL",
                        field_path=f"{field_root}.{list_field}",
                        message=f"{list_field} must be a list of non-empty strings.",
                        evidence=[
                            make_evidence(
                                type="state_check",
                                path=state_path.as_posix(),
                                ref=f"{field_root}.{list_field}",
                                value=value,
                            )
                        ],
                    )
                )

    return diagnostics


def _is_iso_datetime(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    normalized = value.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(normalized)
        return True
    except ValueError:
        return False


def _validate_requirements(requirements_obj: object, state_path: Path) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if requirements_obj is None:
        return diagnostics
    if not isinstance(requirements_obj, dict):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="requirements",
                message="requirements must be a mapping.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref="requirements",
                        value=type(requirements_obj).__name__,
                    )
                ],
            )
        )
        return diagnostics

    requirements: dict[str, object] = requirements_obj
    for requirement_id, requirement_obj in requirements.items():
        if not REQUIREMENT_ID_RE.fullmatch(str(requirement_id)):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_UNKNOWN_ENUM_VALUE",
                    severity="error",
                    entity_type="system",
                    entity_id=str(requirement_id),
                    field_path=f"requirements.{requirement_id}",
                    message="Invalid requirement id format.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref="requirement_id",
                            value=requirement_id,
                        )
                    ],
                )
            )
            continue

        if not isinstance(requirement_obj, dict):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type="requirement",
                    entity_id=requirement_id,
                    field_path=f"requirements.{requirement_id}",
                    message="requirement entry must be an object.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"requirements.{requirement_id}",
                            value=type(requirement_obj).__name__,
                        )
                    ],
                )
            )
            continue

        requirement: dict[str, object] = requirement_obj
        path = _validate_meta_path(
            entity_type="requirement",
            entity_id=requirement_id,
            obj=requirement.get("meta"),
            diagnostics=diagnostics,
            state_path=state_path,
        )
        scope_kind = _validate_requirement_scope_kind(
            requirement_id=requirement_id,
            obj=requirement.get("meta"),
            diagnostics=diagnostics,
            state_path=state_path,
        )
        diagnostics.extend(
            _validate_requirement_facts(
                requirement_id=requirement_id,
                obj=requirement.get("facts"),
                state_path=state_path,
            )
        )
        diagnostics.extend(
            _validate_confirmed_state(
                entity_type="requirement",
                entity_id=requirement_id,
                state_obj=requirement.get("state"),
                required_fields=REQUIRED_CONFIRMED_FIELDS,
                state_path=state_path,
            )
        )
        diagnostics.extend(
            _validate_tracking_state(
                entity_type="requirement",
                entity_id=requirement_id,
                state_obj=requirement.get("state"),
                state_path=state_path,
                required=True,
            )
        )

        if path is not None and scope_kind is not None and not is_valid_requirement_path(
            requirement_id=requirement_id,
            path=path,
            scope_kind=scope_kind,
        ):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_PATH_ID_MISMATCH",
                    severity="error",
                    entity_type="requirement",
                    entity_id=requirement_id,
                    field_path=f"requirements.{requirement_id}.meta.path",
                    message="requirement_id and path/scope_kind mismatch.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref="meta.path",
                            value=path,
                        )
                    ],
                )
            )

    return diagnostics
def _validate_modules(
    modules_obj: object,
    state_path: Path,
    *,
    known_requirement_ids: set[str],
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not isinstance(modules_obj, dict):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="modules",
                message="modules must be a mapping.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref="modules",
                        value=type(modules_obj).__name__,
                    )
                ],
            )
        )
        return diagnostics

    modules: dict[str, object] = modules_obj
    for module_id, module_obj in modules.items():
        if not MODULE_ID_RE.fullmatch(str(module_id)):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_UNKNOWN_ENUM_VALUE",
                    severity="error",
                    entity_type="system",
                    entity_id=str(module_id),
                    field_path=f"modules.{module_id}",
                    message="Invalid module id format.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref="module_id",
                            value=module_id,
                        )
                    ],
                )
            )
            continue

        if not isinstance(module_obj, dict):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type="module",
                    entity_id=module_id,
                    field_path=f"modules.{module_id}",
                    message="module entry must be an object.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"modules.{module_id}",
                            value=type(module_obj).__name__,
                        )
                    ],
                )
            )
            continue

        module: dict[str, object] = module_obj
        path = _validate_meta_path(
            entity_type="module",
            entity_id=module_id,
            obj=module.get("meta"),
            diagnostics=diagnostics,
            state_path=state_path,
        )
        diagnostics.extend(
            _validate_facts(
                entity_type="module",
                entity_id=module_id,
                obj=module.get("facts"),
                required_doc_slots=set(MODULE_DOC_SLOTS),
                required_fields=REQUIRED_MODULE_FACT_FIELDS,
                state_path=state_path,
            )
        )
        diagnostics.extend(
            _validate_compliance(
                entity_type="module",
                entity_id=module_id,
                facts_obj=module.get("facts"),
                state_path=state_path,
                required=False,
            )
        )
        diagnostics.extend(
            _validate_confirmed_state(
                entity_type="module",
                entity_id=module_id,
                state_obj=module.get("state"),
                required_fields=REQUIRED_CONFIRMED_FIELDS,
                state_path=state_path,
            )
        )
        diagnostics.extend(
            _validate_tracking_state(
                entity_type="module",
                entity_id=module_id,
                state_obj=module.get("state"),
                state_path=state_path,
                required=False,
            )
        )
        diagnostics.extend(
            _validate_requirement_relation_fields(
                entity_type="module",
                entity_id=module_id,
                meta_obj=module.get("meta"),
                facts_obj=module.get("facts"),
                state_path=state_path,
                known_requirement_ids=known_requirement_ids,
            )
        )

        if extract_module_id_from_path(path) is not None:
            expected_id = extract_module_id_from_path(path)
            if expected_id != module_id:
                diagnostics.append(
                    make_diagnostic(
                        code="SCHEMA_PATH_ID_MISMATCH",
                        severity="error",
                        entity_type="module",
                        entity_id=module_id,
                        field_path=f"modules.{module_id}.meta.path",
                        message="module_id and path prefix mismatch.",
                        evidence=[
                            make_evidence(
                                type="state_check",
                                path=state_path.as_posix(),
                                ref="meta.path",
                                value=path,
                            )
                        ],
                    )
                )

    return diagnostics


def _validate_subtasks(
    subtasks_obj: object,
    state_path: Path,
    *,
    known_requirement_ids: set[str],
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not isinstance(subtasks_obj, dict):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="subtasks",
                message="subtasks must be a mapping.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref="subtasks",
                        value=type(subtasks_obj).__name__,
                    )
                ],
            )
        )
        return diagnostics

    subtasks: dict[str, object] = subtasks_obj
    for subtask_id, subtask_obj in subtasks.items():
        if not SUBTASK_ID_RE.fullmatch(str(subtask_id)):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_UNKNOWN_ENUM_VALUE",
                    severity="error",
                    entity_type="system",
                    entity_id=str(subtask_id),
                    field_path=f"subtasks.{subtask_id}",
                    message="Invalid subtask id format.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref="subtask_id",
                            value=subtask_id,
                        )
                    ],
                )
            )
            continue

        if not isinstance(subtask_obj, dict):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type="subtask",
                    entity_id=subtask_id,
                    field_path=f"subtasks.{subtask_id}",
                    message="subtask entry must be an object.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"subtasks.{subtask_id}",
                            value=type(subtask_obj).__name__,
                        )
                    ],
                )
            )
            continue

        subtask: dict[str, object] = subtask_obj
        path = _validate_meta_path(
            entity_type="subtask",
            entity_id=subtask_id,
            obj=subtask.get("meta"),
            diagnostics=diagnostics,
            state_path=state_path,
        )
        diagnostics.extend(
            _validate_facts(
                entity_type="subtask",
                entity_id=subtask_id,
                obj=subtask.get("facts"),
                required_doc_slots=set(SUBTASK_DOC_SLOTS),
                required_fields=REQUIRED_SUBTASK_FACT_FIELDS,
                state_path=state_path,
            )
        )
        diagnostics.extend(
            _validate_compliance(
                entity_type="subtask",
                entity_id=subtask_id,
                facts_obj=subtask.get("facts"),
                state_path=state_path,
                required=False,
            )
        )
        diagnostics.extend(
            _validate_confirmed_state(
                entity_type="subtask",
                entity_id=subtask_id,
                state_obj=subtask.get("state"),
                required_fields=SUBTASK_CONFIRMED_REQUIRED_FIELDS,
                state_path=state_path,
            )
        )
        diagnostics.extend(
            _validate_tracking_state(
                entity_type="subtask",
                entity_id=subtask_id,
                state_obj=subtask.get("state"),
                state_path=state_path,
                required=False,
            )
        )
        diagnostics.extend(
            _validate_requirement_relation_fields(
                entity_type="subtask",
                entity_id=subtask_id,
                meta_obj=subtask.get("meta"),
                facts_obj=subtask.get("facts"),
                state_path=state_path,
                known_requirement_ids=known_requirement_ids,
            )
        )

        if extract_subtask_id_from_path(path) is not None:
            expected_id = extract_subtask_id_from_path(path)
            if expected_id != subtask_id:
                diagnostics.append(
                    make_diagnostic(
                        code="SCHEMA_PATH_ID_MISMATCH",
                        severity="error",
                        entity_type="subtask",
                        entity_id=subtask_id,
                        field_path=f"subtasks.{subtask_id}.meta.path",
                        message="subtask_id and path prefix mismatch.",
                        evidence=[
                            make_evidence(
                                type="state_check",
                                path=state_path.as_posix(),
                                ref="meta.path",
                                value=path,
                            )
                        ],
                    )
                )

    return diagnostics


def _validate_documents(documents_obj: object, state_path: Path) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if documents_obj is None:
        return diagnostics
    if not isinstance(documents_obj, dict):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="documents",
                message="documents must be a mapping.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref="documents",
                        value=type(documents_obj).__name__,
                    )
                ],
            )
        )
        return diagnostics

    for document_id, document_obj in documents_obj.items():
        if not DOCUMENT_ID_RE.fullmatch(str(document_id)):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_UNKNOWN_ENUM_VALUE",
                    severity="error",
                    entity_type="system",
                    entity_id=str(document_id),
                    field_path=f"documents.{document_id}",
                    message="Invalid document id format.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref="document_id",
                            value=document_id,
                        )
                    ],
                )
            )
            continue
        if not isinstance(document_obj, dict):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type="document",
                    entity_id=str(document_id),
                    field_path=f"documents.{document_id}",
                    message="document entry must be an object.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"documents.{document_id}",
                            value=type(document_obj).__name__,
                        )
                    ],
                )
            )
            continue

        document = document_obj
        diagnostics.extend(
            _validate_document_meta(
                document_id=str(document_id),
                meta_obj=document.get("meta"),
                state_path=state_path,
            )
        )
        diagnostics.extend(
            _validate_document_facts(
                document_id=str(document_id),
                facts_obj=document.get("facts"),
                state_path=state_path,
            )
        )
        diagnostics.extend(
            _validate_confirmed_state(
                entity_type="document",
                entity_id=str(document_id),
                state_obj=document.get("state"),
                required_fields=DOCUMENT_CONFIRMED_REQUIRED_FIELDS,
                state_path=state_path,
            )
        )

    return diagnostics


def _validate_document_meta(
    *,
    document_id: str,
    meta_obj: object,
    state_path: Path,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not isinstance(meta_obj, dict):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type="document",
                entity_id=document_id,
                field_path=f"documents.{document_id}.meta",
                message="meta must be an object.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"documents.{document_id}.meta",
                        value=type(meta_obj).__name__,
                    )
                ],
            )
        )
        return diagnostics

    doc_type = meta_obj.get("doc_type")
    if doc_type not in DOCUMENT_TYPES:
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_UNKNOWN_ENUM_VALUE",
                severity="error",
                entity_type="document",
                entity_id=document_id,
                field_path=f"documents.{document_id}.meta.doc_type",
                message="Unknown document doc_type.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"documents.{document_id}.meta.doc_type",
                        value=doc_type,
                    )
                ],
            )
        )

    title = meta_obj.get("title")
    if title is not None and (not isinstance(title, str) or not title.strip()):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type="document",
                entity_id=document_id,
                field_path=f"documents.{document_id}.meta.title",
                message="meta.title must be a non-empty string when present.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"documents.{document_id}.meta.title",
                        value=title,
                    )
                ],
            )
        )

    path = meta_obj.get("path")
    if not isinstance(path, str) or not path.strip():
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type="document",
                entity_id=document_id,
                field_path=f"documents.{document_id}.meta.path",
                message="meta.path must be a non-empty string.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"documents.{document_id}.meta.path",
                        value=path,
                    )
                ],
            )
        )

    required_sections = meta_obj.get("required_sections")
    if not isinstance(required_sections, list) or not required_sections:
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type="document",
                entity_id=document_id,
                field_path=f"documents.{document_id}.meta.required_sections",
                message="required_sections must be a non-empty list.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"documents.{document_id}.meta.required_sections",
                        value=required_sections,
                    )
                ],
            )
        )
    else:
        for index, section in enumerate(required_sections):
            if not isinstance(section, dict):
                diagnostics.append(
                    make_diagnostic(
                        code="SCHEMA_MISSING_REQUIRED_FIELD",
                        severity="error",
                        entity_type="document",
                        entity_id=document_id,
                        field_path=f"documents.{document_id}.meta.required_sections[{index}]",
                        message="required_sections entry must be an object.",
                        evidence=[
                            make_evidence(
                                type="state_check",
                                path=state_path.as_posix(),
                                ref=f"documents.{document_id}.meta.required_sections[{index}]",
                                value=type(section).__name__,
                            )
                        ],
                    )
                )
                continue
            for key in ("section_id", "heading"):
                value = section.get(key)
                if not isinstance(value, str) or not value.strip():
                    diagnostics.append(
                        make_diagnostic(
                            code="SCHEMA_MISSING_REQUIRED_FIELD",
                            severity="error",
                            entity_type="document",
                            entity_id=document_id,
                            field_path=f"documents.{document_id}.meta.required_sections[{index}].{key}",
                            message=f"{key} must be a non-empty string.",
                            evidence=[
                                make_evidence(
                                    type="state_check",
                                    path=state_path.as_posix(),
                                    ref=f"documents.{document_id}.meta.required_sections[{index}].{key}",
                                    value=value,
                                )
                            ],
                        )
                    )

    relations = meta_obj.get("relations")
    if not isinstance(relations, dict):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type="document",
                entity_id=document_id,
                field_path=f"documents.{document_id}.meta.relations",
                message="relations must be an object.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"documents.{document_id}.meta.relations",
                        value=type(relations).__name__,
                    )
                ],
            )
        )
    else:
        for list_field in ("document_refs", "module_refs", "oq_refs"):
            value = relations.get(list_field)
            if not isinstance(value, list) or any(
                not isinstance(entry, str) or not entry.strip() for entry in value
            ):
                diagnostics.append(
                    make_diagnostic(
                        code="SCHEMA_MISSING_REQUIRED_FIELD",
                        severity="error",
                        entity_type="document",
                        entity_id=document_id,
                        field_path=f"documents.{document_id}.meta.relations.{list_field}",
                        message=f"{list_field} must be a list of non-empty strings.",
                        evidence=[
                            make_evidence(
                                type="state_check",
                                path=state_path.as_posix(),
                                ref=f"documents.{document_id}.meta.relations.{list_field}",
                                value=value,
                            )
                        ],
                    )
                )

    return diagnostics


def _validate_document_facts(
    *,
    document_id: str,
    facts_obj: object,
    state_path: Path,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not isinstance(facts_obj, dict):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type="document",
                entity_id=document_id,
                field_path=f"documents.{document_id}.facts",
                message="facts must be an object.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"documents.{document_id}.facts",
                        value=type(facts_obj).__name__,
                    )
                ],
            )
        )
        return diagnostics

    exists = facts_obj.get("exists")
    if not isinstance(exists, bool):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type="document",
                entity_id=document_id,
                field_path=f"documents.{document_id}.facts.exists",
                message="exists must be a boolean.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"documents.{document_id}.facts.exists",
                        value=exists,
                    )
                ],
            )
        )

    for list_field in ("headings",):
        value = facts_obj.get(list_field)
        if not isinstance(value, list) or any(not isinstance(entry, str) for entry in value):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type="document",
                    entity_id=document_id,
                    field_path=f"documents.{document_id}.facts.{list_field}",
                    message=f"{list_field} must be a list of strings.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"documents.{document_id}.facts.{list_field}",
                            value=value,
                        )
                    ],
                )
            )

    for dict_field in ("section_presence",):
        value = facts_obj.get(dict_field)
        if not isinstance(value, dict):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type="document",
                    entity_id=document_id,
                    field_path=f"documents.{document_id}.facts.{dict_field}",
                    message=f"{dict_field} must be an object.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"documents.{document_id}.facts.{dict_field}",
                            value=type(value).__name__,
                        )
                    ],
                )
            )

    extracted_refs = facts_obj.get("extracted_refs")
    if not isinstance(extracted_refs, dict):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type="document",
                entity_id=document_id,
                field_path=f"documents.{document_id}.facts.extracted_refs",
                message="extracted_refs must be an object.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"documents.{document_id}.facts.extracted_refs",
                        value=type(extracted_refs).__name__,
                    )
                ],
            )
        )
    else:
        for list_field in ("document_refs", "module_refs", "oq_refs"):
            value = extracted_refs.get(list_field)
            if not isinstance(value, list) or any(not isinstance(entry, str) for entry in value):
                diagnostics.append(
                    make_diagnostic(
                        code="SCHEMA_MISSING_REQUIRED_FIELD",
                        severity="error",
                        entity_type="document",
                        entity_id=document_id,
                        field_path=f"documents.{document_id}.facts.extracted_refs.{list_field}",
                        message=f"{list_field} must be a list of strings.",
                        evidence=[
                            make_evidence(
                                type="state_check",
                                path=state_path.as_posix(),
                                ref=f"documents.{document_id}.facts.extracted_refs.{list_field}",
                                value=value,
                            )
                        ],
                    )
                )

    marker_counts = facts_obj.get("marker_counts")
    if not isinstance(marker_counts, dict):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type="document",
                entity_id=document_id,
                field_path=f"documents.{document_id}.facts.marker_counts",
                message="marker_counts must be an object.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"documents.{document_id}.facts.marker_counts",
                        value=type(marker_counts).__name__,
                    )
                ],
            )
        )
    else:
        for key in ("todo", "tbd", "unresolved"):
            value = marker_counts.get(key)
            if not isinstance(value, int):
                diagnostics.append(
                    make_diagnostic(
                        code="SCHEMA_MISSING_REQUIRED_FIELD",
                        severity="error",
                        entity_type="document",
                        entity_id=document_id,
                        field_path=f"documents.{document_id}.facts.marker_counts.{key}",
                        message=f"{key} must be an integer.",
                        evidence=[
                            make_evidence(
                                type="state_check",
                                path=state_path.as_posix(),
                                ref=f"documents.{document_id}.facts.marker_counts.{key}",
                                value=value,
                            )
                        ],
                    )
                )

    last_scanned_at = facts_obj.get("last_scanned_at")
    if last_scanned_at is not None and not _is_iso_datetime(last_scanned_at):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_INVALID_GOVERNANCE_ROUND_TIME",
                severity="error",
                entity_type="document",
                entity_id=document_id,
                field_path=f"documents.{document_id}.facts.last_scanned_at",
                message="last_scanned_at must be ISO-8601 datetime string when present.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"documents.{document_id}.facts.last_scanned_at",
                        value=last_scanned_at,
                    )
                ],
            )
        )

    return diagnostics


def _validate_meta_path(
    *,
    entity_type: str,
    entity_id: str,
    obj: object,
    diagnostics: list[Diagnostic],
    state_path: Path,
) -> str | None:
    if not isinstance(obj, dict):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}.meta",
                message="meta must be an object.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"{entity_type}s.{entity_id}.meta",
                        value=type(obj).__name__,
                    )
                ],
            )
        )
        return None

    path = obj.get("path")
    if not isinstance(path, str):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}.meta.path",
                message="meta.path must be a string.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"{entity_type}s.{entity_id}.meta.path",
                        value=type(path).__name__,
                    )
                ],
            )
        )
        return None

    if not path.strip():
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}.meta.path",
                message="meta.path cannot be empty.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"{entity_type}s.{entity_id}.meta.path",
                        value=path,
                    )
                ],
            )
        )
        return None

    return path


def _validate_requirement_scope_kind(
    *,
    requirement_id: str,
    obj: object,
    diagnostics: list[Diagnostic],
    state_path: Path,
) -> str | None:
    if not isinstance(obj, dict):
        return None

    scope_kind = obj.get("scope_kind")
    if not isinstance(scope_kind, str):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type="requirement",
                entity_id=requirement_id,
                field_path=f"requirements.{requirement_id}.meta.scope_kind",
                message="meta.scope_kind must be a string.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"requirements.{requirement_id}.meta.scope_kind",
                        value=type(scope_kind).__name__,
                    )
                ],
            )
        )
        return None

    if scope_kind not in REQUIREMENT_SCOPE_KINDS:
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_UNKNOWN_ENUM_VALUE",
                severity="error",
                entity_type="requirement",
                entity_id=requirement_id,
                field_path=f"requirements.{requirement_id}.meta.scope_kind",
                message="Unknown requirement scope_kind value.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"requirements.{requirement_id}.meta.scope_kind",
                        value=scope_kind,
                    )
                ],
            )
        )
        return None

    return scope_kind


def _validate_requirement_facts(
    *,
    requirement_id: str,
    obj: object,
    state_path: Path,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not isinstance(obj, dict):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type="requirement",
                entity_id=requirement_id,
                field_path=f"requirements.{requirement_id}.facts",
                message="facts must be an object.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"requirements.{requirement_id}.facts",
                        value=type(obj).__name__,
                    )
                ],
            )
        )
        return diagnostics

    facts: dict[str, object] = obj
    for field in ("module_ids", "task_ids", "asset_slots", "compliance"):
        if field not in facts:
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type="requirement",
                    entity_id=requirement_id,
                    field_path=f"requirements.{requirement_id}.facts.{field}",
                    message=f"Missing required facts field: {field}",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"requirements.{requirement_id}.facts.{field}",
                            value=None,
                        )
                    ],
                )
            )

    diagnostics.extend(
        _validate_id_list(
            entity_type="requirement",
            entity_id=requirement_id,
            field_name="module_ids",
            values=facts.get("module_ids"),
            state_path=state_path,
            regex=MODULE_ID_RE,
        )
    )
    diagnostics.extend(
        _validate_id_list(
            entity_type="requirement",
            entity_id=requirement_id,
            field_name="task_ids",
            values=facts.get("task_ids"),
            state_path=state_path,
            regex=SUBTASK_ID_RE,
        )
    )
    diagnostics.extend(
        _validate_requirement_asset_slots(
            requirement_id=requirement_id,
            asset_slots_obj=facts.get("asset_slots"),
            state_path=state_path,
        )
    )
    diagnostics.extend(
        _validate_compliance(
            entity_type="requirement",
            entity_id=requirement_id,
            facts_obj=facts,
            state_path=state_path,
            required=True,
        )
    )
    return diagnostics


def _validate_facts(
    *,
    entity_type: str,
    entity_id: str,
    obj: object,
    required_doc_slots: set[str],
    required_fields: tuple[str, ...],
    state_path: Path,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not isinstance(obj, dict):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}.facts",
                message="facts must be an object.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"{entity_type}s.{entity_id}.facts",
                        value=type(obj).__name__,
                    )
                ],
            )
        )
        return diagnostics

    facts: dict[str, object] = obj
    for field in required_fields:
        if field not in facts:
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"{entity_type}s.{entity_id}.facts.{field}",
                    message=f"Missing required facts field: {field}",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"{entity_type}s.{entity_id}.facts.{field}",
                            value=None,
                        )
                    ],
                )
            )

    for field in ("declared_blocker_refs", "related_oq_ids", "upstream_module_ids"):
        if isinstance(facts.get(field), list):
            for value in facts.get(field, []):
                if not isinstance(value, str):
                    diagnostics.append(
                        make_diagnostic(
                            code="SCHEMA_MISSING_REQUIRED_FIELD",
                            severity="error",
                            entity_type=entity_type,
                            entity_id=entity_id,
                            field_path=f"{entity_type}s.{entity_id}.facts.{field}",
                            message=f"{field} entries must be strings.",
                            evidence=[
                                make_evidence(
                                    type="state_check",
                                    path=state_path.as_posix(),
                                    ref=f"{entity_type}s.{entity_id}.facts.{field}",
                                    value=value,
                                )
                            ],
                        )
                    )

    docs_value = facts.get("docs")
    if docs_value is not None:
        if not isinstance(docs_value, dict):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"{entity_type}s.{entity_id}.facts.docs",
                    message="facts.docs must be an object.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"{entity_type}s.{entity_id}.facts.docs",
                            value=type(docs_value).__name__,
                        )
                    ],
                )
            )
        else:
            docs: dict[str, object] = docs_value
            for doc_name in docs.keys():
                if doc_name not in required_doc_slots:
                    diagnostics.append(
                        make_diagnostic(
                            code="SCHEMA_UNKNOWN_DOC_SLOT",
                            severity="error",
                            entity_type=entity_type,
                            entity_id=entity_id,
                            field_path=f"{entity_type}s.{entity_id}.facts.docs.{doc_name}",
                            message=f"Unknown doc slot: {doc_name}",
                            evidence=[
                                make_evidence(
                                    type="state_check",
                                    path=state_path.as_posix(),
                                    ref=f"{entity_type}s.{entity_id}.facts.docs",
                                    value=doc_name,
                                )
                            ],
                        )
                    )
            for required_slot in required_doc_slots:
                if required_slot not in docs:
                    diagnostics.append(
                        make_diagnostic(
                            code="SCHEMA_MISSING_REQUIRED_FIELD",
                            severity="error",
                            entity_type=entity_type,
                            entity_id=entity_id,
                            field_path=f"{entity_type}s.{entity_id}.facts.docs.{required_slot}",
                            message=f"Missing doc slot fact for {required_slot}",
                            evidence=[
                                make_evidence(
                                    type="state_check",
                                    path=state_path.as_posix(),
                                    ref=f"{entity_type}s.{entity_id}.facts.docs.{required_slot}",
                                    value=None,
                                )
                            ],
                        )
                    )
                else:
                    slot_info = docs.get(required_slot)
                    if isinstance(slot_info, dict):
                        for key in ("exists", "template_like"):
                            if not isinstance(slot_info.get(key), bool):
                                diagnostics.append(
                                    make_diagnostic(
                                        code="SCHEMA_MISSING_REQUIRED_FIELD",
                                        severity="error",
                                        entity_type=entity_type,
                                        entity_id=entity_id,
                                        field_path=(
                                            f"{entity_type}s.{entity_id}.facts.docs."
                                            f"{required_slot}.{key}"
                                        ),
                                        message=(
                                            f"facts.docs.{required_slot}.{key} must be boolean."
                                        ),
                                        evidence=[
                                            make_evidence(
                                                type="state_check",
                                                path=state_path.as_posix(),
                                                ref=(
                                                    f"{entity_type}s.{entity_id}.facts.docs."
                                                    f"{required_slot}.{key}"
                                                ),
                                                value=slot_info.get(key),
                                            )
                                        ],
                                    )
                                )
                    else:
                        diagnostics.append(
                            make_diagnostic(
                                code="SCHEMA_MISSING_REQUIRED_FIELD",
                                severity="error",
                                entity_type=entity_type,
                                entity_id=entity_id,
                                field_path=f"{entity_type}s.{entity_id}.facts.docs.{required_slot}",
                                message=f"facts.docs.{required_slot} must be an object.",
                                evidence=[
                                    make_evidence(
                                        type="state_check",
                                        path=state_path.as_posix(),
                                        ref=f"{entity_type}s.{entity_id}.facts.docs.{required_slot}",
                                        value=type(slot_info).__name__,
                                    )
                                ],
                            )
                        )

    if isinstance(facts.get("design_doc"), dict):
        _validate_doc_flags(
            entity_type=entity_type,
            entity_id=entity_id,
            slot_name="design_doc",
            slot_value=facts["design_doc"],
            state_path=state_path,
            diagnostics=diagnostics,
            field_root=f"{entity_type}s.{entity_id}.facts",
        )

    if isinstance(facts.get("implementation_doc"), dict):
        _validate_doc_flags(
            entity_type=entity_type,
            entity_id=entity_id,
            slot_name="implementation_doc",
            slot_value=facts["implementation_doc"],
            state_path=state_path,
            diagnostics=diagnostics,
            field_root=f"{entity_type}s.{entity_id}.facts",
        )

    declared_blocker_refs = facts.get("declared_blocker_refs")
    if isinstance(declared_blocker_refs, list):
        for index, ref in enumerate(declared_blocker_refs):
            if not isinstance(ref, str):
                continue
            if not TYPED_BLOCKER_REF_RE.fullmatch(ref):
                diagnostics.append(
                    make_diagnostic(
                        code="SCHEMA_INVALID_TYPED_REF",
                        severity="error",
                        entity_type=entity_type,
                        entity_id=entity_id,
                        field_path=f"{entity_type}s.{entity_id}.facts.declared_blocker_refs[{index}]",
                        message=f"Invalid typed blocker ref: {ref}",
                        evidence=[
                            make_evidence(
                                type="state_check",
                                path=state_path.as_posix(),
                                ref="facts.declared_blocker_refs",
                                value=ref,
                            )
                        ],
                    )
                )

    return diagnostics


def _validate_requirement_relation_fields(
    *,
    entity_type: str,
    entity_id: str,
    meta_obj: object,
    facts_obj: object,
    state_path: Path,
    known_requirement_ids: set[str],
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if entity_type not in REQUIREMENT_RELATION_ENTITY_TYPES:
        return diagnostics

    meta_requirement_id: str | None = None
    facts_requirement_ids: list[str] | None = None

    if isinstance(meta_obj, dict) and REQUIREMENT_RELATION_META_FIELD in meta_obj:
        raw_meta_requirement_id = meta_obj.get(REQUIREMENT_RELATION_META_FIELD)
        if not isinstance(raw_meta_requirement_id, str) or not REQUIREMENT_ID_RE.fullmatch(
            raw_meta_requirement_id.strip()
        ):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_INVALID_REQUIREMENT_RELATION_ID",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"{entity_type}s.{entity_id}.meta.{REQUIREMENT_RELATION_META_FIELD}",
                    message=f"meta.{REQUIREMENT_RELATION_META_FIELD} must be a valid requirement id.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"{entity_type}s.{entity_id}.meta.{REQUIREMENT_RELATION_META_FIELD}",
                            value=raw_meta_requirement_id,
                        )
                    ],
                )
            )
        else:
            meta_requirement_id = raw_meta_requirement_id.strip()
            if meta_requirement_id not in known_requirement_ids:
                diagnostics.append(
                    make_diagnostic(
                        code="SCHEMA_UNKNOWN_REQUIREMENT_RELATION_ID",
                        severity="error",
                        entity_type=entity_type,
                        entity_id=entity_id,
                        field_path=f"{entity_type}s.{entity_id}.meta.{REQUIREMENT_RELATION_META_FIELD}",
                        message=f"Unknown requirement relation id: {meta_requirement_id}",
                        evidence=[
                            make_evidence(
                                type="state_check",
                                path=state_path.as_posix(),
                                ref=f"{entity_type}s.{entity_id}.meta.{REQUIREMENT_RELATION_META_FIELD}",
                                value=meta_requirement_id,
                            )
                        ],
                    )
                )

    if isinstance(facts_obj, dict) and REQUIREMENT_RELATION_FACT_FIELD in facts_obj:
        raw_requirement_ids = facts_obj.get(REQUIREMENT_RELATION_FACT_FIELD)
        if not isinstance(raw_requirement_ids, list):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"{entity_type}s.{entity_id}.facts.{REQUIREMENT_RELATION_FACT_FIELD}",
                    message=f"{REQUIREMENT_RELATION_FACT_FIELD} must be a list when present.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"{entity_type}s.{entity_id}.facts.{REQUIREMENT_RELATION_FACT_FIELD}",
                            value=type(raw_requirement_ids).__name__,
                        )
                    ],
                )
            )
        else:
            facts_requirement_ids = []
            for index, value in enumerate(raw_requirement_ids):
                if not isinstance(value, str) or not REQUIREMENT_ID_RE.fullmatch(value.strip()):
                    diagnostics.append(
                        make_diagnostic(
                            code="SCHEMA_INVALID_REQUIREMENT_RELATION_ID",
                            severity="error",
                            entity_type=entity_type,
                            entity_id=entity_id,
                            field_path=(
                                f"{entity_type}s.{entity_id}.facts."
                                f"{REQUIREMENT_RELATION_FACT_FIELD}[{index}]"
                            ),
                            message=f"Invalid requirement relation id: {value}",
                            evidence=[
                                make_evidence(
                                    type="state_check",
                                    path=state_path.as_posix(),
                                    ref=f"{entity_type}s.{entity_id}.facts.{REQUIREMENT_RELATION_FACT_FIELD}",
                                    value=value,
                                )
                            ],
                        )
                    )
                    continue
                normalized_value = value.strip()
                facts_requirement_ids.append(normalized_value)
                if normalized_value not in known_requirement_ids:
                    diagnostics.append(
                        make_diagnostic(
                            code="SCHEMA_UNKNOWN_REQUIREMENT_RELATION_ID",
                            severity="error",
                            entity_type=entity_type,
                            entity_id=entity_id,
                            field_path=(
                                f"{entity_type}s.{entity_id}.facts."
                                f"{REQUIREMENT_RELATION_FACT_FIELD}[{index}]"
                            ),
                            message=f"Unknown requirement relation id: {normalized_value}",
                            evidence=[
                                make_evidence(
                                    type="state_check",
                                    path=state_path.as_posix(),
                                    ref=f"{entity_type}s.{entity_id}.facts.{REQUIREMENT_RELATION_FACT_FIELD}",
                                    value=normalized_value,
                                )
                            ],
                        )
                    )

            if facts_requirement_ids is not None:
                facts_requirement_ids = list(dict.fromkeys(facts_requirement_ids))
                if len(facts_requirement_ids) > 1:
                    diagnostics.append(
                        make_diagnostic(
                            code="SCHEMA_REQUIREMENT_RELATION_AMBIGUOUS",
                            severity="warning",
                            entity_type=entity_type,
                            entity_id=entity_id,
                            field_path=f"{entity_type}s.{entity_id}.facts.{REQUIREMENT_RELATION_FACT_FIELD}",
                            message=(
                                f"{REQUIREMENT_RELATION_FACT_FIELD} contains multiple requirement ids: "
                                + ", ".join(facts_requirement_ids)
                            ),
                            evidence=[
                                make_evidence(
                                    type="state_check",
                                    path=state_path.as_posix(),
                                    ref=f"{entity_type}s.{entity_id}.facts.{REQUIREMENT_RELATION_FACT_FIELD}",
                                    value=facts_requirement_ids,
                                )
                            ],
                        )
                    )

    if (
        meta_requirement_id is not None
        and facts_requirement_ids is not None
        and meta_requirement_id not in facts_requirement_ids
    ):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_REQUIREMENT_RELATION_CONFLICT",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}",
                message=(
                    f"meta.{REQUIREMENT_RELATION_META_FIELD} is not compatible with "
                    f"facts.{REQUIREMENT_RELATION_FACT_FIELD}."
                ),
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"{entity_type}s.{entity_id}.meta.{REQUIREMENT_RELATION_META_FIELD}",
                        value=meta_requirement_id,
                    ),
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"{entity_type}s.{entity_id}.facts.{REQUIREMENT_RELATION_FACT_FIELD}",
                        value=facts_requirement_ids,
                    ),
                ],
            )
        )

    return diagnostics


def _validate_requirement_relation_consistency(
    *,
    requirements_obj: object,
    modules_obj: object,
    subtasks_obj: object,
    state_path: Path,
    known_requirement_ids: set[str],
    requirement_mode: str,
) -> list[Diagnostic]:
    if not isinstance(requirements_obj, dict):
        return []

    diagnostics: list[Diagnostic] = []
    diagnostics.extend(
        _validate_entity_requirement_relation_consistency(
            entity_type="module",
            entities_obj=modules_obj,
            container_relations=_collect_requirement_container_relations(
                requirements_obj=requirements_obj,
                relation_field="module_ids",
                known_requirement_ids=known_requirement_ids,
            ),
            state_path=state_path,
            known_requirement_ids=known_requirement_ids,
            requirement_mode=requirement_mode,
        )
    )
    diagnostics.extend(
        _validate_entity_requirement_relation_consistency(
            entity_type="subtask",
            entities_obj=subtasks_obj,
            container_relations=_collect_requirement_container_relations(
                requirements_obj=requirements_obj,
                relation_field="task_ids",
                known_requirement_ids=known_requirement_ids,
            ),
            state_path=state_path,
            known_requirement_ids=known_requirement_ids,
            requirement_mode=requirement_mode,
        )
    )
    return diagnostics


def _collect_requirement_container_relations(
    *,
    requirements_obj: dict[str, object],
    relation_field: str,
    known_requirement_ids: set[str],
) -> dict[str, list[str]]:
    relation_map: dict[str, list[str]] = {}
    for requirement_id, requirement_obj in requirements_obj.items():
        normalized_requirement_id = str(requirement_id).strip()
        if normalized_requirement_id not in known_requirement_ids:
            continue
        if not isinstance(requirement_obj, dict):
            continue
        facts = requirement_obj.get("facts")
        if not isinstance(facts, dict):
            continue
        raw_values = facts.get(relation_field)
        if not isinstance(raw_values, list):
            continue
        for raw_value in raw_values:
            if not isinstance(raw_value, str) or not raw_value.strip():
                continue
            entity_id = raw_value.strip()
            relation_map.setdefault(entity_id, [])
            if normalized_requirement_id not in relation_map[entity_id]:
                relation_map[entity_id].append(normalized_requirement_id)
    return relation_map


def _validate_entity_requirement_relation_consistency(
    *,
    entity_type: str,
    entities_obj: object,
    container_relations: dict[str, list[str]],
    state_path: Path,
    known_requirement_ids: set[str],
    requirement_mode: str,
) -> list[Diagnostic]:
    if not isinstance(entities_obj, dict):
        return []

    relation_field = "module_ids" if entity_type == "module" else "task_ids"
    diagnostics: list[Diagnostic] = []
    for entity_id, entity_obj in entities_obj.items():
        if not isinstance(entity_obj, dict):
            continue
        meta = entity_obj.get("meta")
        facts = entity_obj.get("facts")
        entity_requirement_ids = _collect_entity_requirement_relation_ids(
            meta_obj=meta,
            facts_obj=facts,
            known_requirement_ids=known_requirement_ids,
        )
        container_requirement_ids = list(container_relations.get(str(entity_id), []))
        container_requirement_ids = list(dict.fromkeys(container_requirement_ids))

        if len(container_requirement_ids) > 1:
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_REQUIREMENT_RELATION_AMBIGUOUS",
                    severity="warning",
                    entity_type=entity_type,
                    entity_id=str(entity_id),
                    field_path=f"{entity_type}s.{entity_id}",
                    message=(
                        "requirement container side contains multiple requirement ids: "
                        + ", ".join(container_requirement_ids)
                    ),
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"requirements.{requirement_id}.facts.{relation_field}",
                            value=[str(entity_id)],
                        )
                        for requirement_id in container_requirement_ids
                    ],
                )
            )

        if not entity_requirement_ids and container_requirement_ids:
            if _allow_legacy_root_requirement_container_only_relation(
                requirement_mode=requirement_mode,
                known_requirement_ids=known_requirement_ids,
                container_requirement_ids=container_requirement_ids,
            ):
                continue
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_REQUIREMENT_RELATION_ENTITY_MISSING",
                    severity="warning",
                    entity_type=entity_type,
                    entity_id=str(entity_id),
                    field_path=f"{entity_type}s.{entity_id}",
                    message=(
                        "entity side is missing requirement relation while requirement container declares "
                        + ", ".join(container_requirement_ids)
                    ),
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"requirements.{requirement_id}.facts.{relation_field}",
                            value=[str(entity_id)],
                        )
                        for requirement_id in container_requirement_ids
                    ],
                )
            )
            continue

        if entity_requirement_ids and not container_requirement_ids:
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_REQUIREMENT_RELATION_CONTAINER_MISSING",
                    severity="warning",
                    entity_type=entity_type,
                    entity_id=str(entity_id),
                    field_path=f"{entity_type}s.{entity_id}",
                    message=(
                        "requirement container side is missing declared relation for "
                        + ", ".join(entity_requirement_ids)
                    ),
                    evidence=_build_entity_requirement_relation_evidence(
                        entity_type=entity_type,
                        entity_id=str(entity_id),
                        entity_requirement_ids=entity_requirement_ids,
                        state_path=state_path,
                    ),
                )
            )
            continue

        if not entity_requirement_ids or not container_requirement_ids:
            continue

        entity_set = set(entity_requirement_ids)
        container_set = set(container_requirement_ids)
        if entity_set.isdisjoint(container_set):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_REQUIREMENT_RELATION_CONTAINER_CONFLICT",
                    severity="warning",
                    entity_type=entity_type,
                    entity_id=str(entity_id),
                    field_path=f"{entity_type}s.{entity_id}",
                    message="entity-side and requirement-container relations disagree.",
                    evidence=_build_requirement_relation_consistency_evidence(
                        entity_type=entity_type,
                        entity_id=str(entity_id),
                        entity_requirement_ids=entity_requirement_ids,
                        container_requirement_ids=container_requirement_ids,
                        state_path=state_path,
                        relation_field=relation_field,
                    ),
                )
            )
            continue

        if entity_set != container_set:
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_REQUIREMENT_RELATION_DRIFT",
                    severity="warning",
                    entity_type=entity_type,
                    entity_id=str(entity_id),
                    field_path=f"{entity_type}s.{entity_id}",
                    message="entity-side and requirement-container relations only partially overlap.",
                    evidence=_build_requirement_relation_consistency_evidence(
                        entity_type=entity_type,
                        entity_id=str(entity_id),
                        entity_requirement_ids=entity_requirement_ids,
                        container_requirement_ids=container_requirement_ids,
                        state_path=state_path,
                        relation_field=relation_field,
                    ),
                )
            )

    return diagnostics


def _collect_entity_requirement_relation_ids(
    *,
    meta_obj: object,
    facts_obj: object,
    known_requirement_ids: set[str],
) -> list[str]:
    requirement_ids: list[str] = []
    if isinstance(meta_obj, dict):
        meta_requirement_id = meta_obj.get(REQUIREMENT_RELATION_META_FIELD)
        if isinstance(meta_requirement_id, str):
            normalized_value = meta_requirement_id.strip()
            if REQUIREMENT_ID_RE.fullmatch(normalized_value) and normalized_value in known_requirement_ids:
                requirement_ids.append(normalized_value)

    if isinstance(facts_obj, dict):
        raw_requirement_ids = facts_obj.get(REQUIREMENT_RELATION_FACT_FIELD)
        if isinstance(raw_requirement_ids, list):
            for raw_value in raw_requirement_ids:
                if not isinstance(raw_value, str):
                    continue
                normalized_value = raw_value.strip()
                if REQUIREMENT_ID_RE.fullmatch(normalized_value) and normalized_value in known_requirement_ids:
                    requirement_ids.append(normalized_value)

    return list(dict.fromkeys(requirement_ids))


def _allow_legacy_root_requirement_container_only_relation(
    *,
    requirement_mode: str,
    known_requirement_ids: set[str],
    container_requirement_ids: list[str],
) -> bool:
    return (
        requirement_mode == "root_requirement_cluster"
        and known_requirement_ids == {"RQ01"}
        and container_requirement_ids == ["RQ01"]
    )


def _build_entity_requirement_relation_evidence(
    *,
    entity_type: str,
    entity_id: str,
    entity_requirement_ids: list[str],
    state_path: Path,
) -> list[dict[str, object]]:
    evidence = [
        make_evidence(
            type="state_check",
            path=state_path.as_posix(),
            ref=f"{entity_type}s.{entity_id}.meta.{REQUIREMENT_RELATION_META_FIELD}",
            value=entity_requirement_ids[0],
        )
    ]
    evidence.append(
        make_evidence(
            type="state_check",
            path=state_path.as_posix(),
            ref=f"{entity_type}s.{entity_id}.facts.{REQUIREMENT_RELATION_FACT_FIELD}",
            value=entity_requirement_ids,
        )
    )
    return evidence


def _build_requirement_relation_consistency_evidence(
    *,
    entity_type: str,
    entity_id: str,
    entity_requirement_ids: list[str],
    container_requirement_ids: list[str],
    state_path: Path,
    relation_field: str,
) -> list[dict[str, object]]:
    evidence = _build_entity_requirement_relation_evidence(
        entity_type=entity_type,
        entity_id=entity_id,
        entity_requirement_ids=entity_requirement_ids,
        state_path=state_path,
    )
    evidence.extend(
        make_evidence(
            type="state_check",
            path=state_path.as_posix(),
            ref=f"requirements.{requirement_id}.facts.{relation_field}",
            value=[entity_id],
        )
        for requirement_id in container_requirement_ids
    )
    return evidence


def _validate_id_list(
    *,
    entity_type: str,
    entity_id: str,
    field_name: str,
    values: object,
    state_path: Path,
    regex: re.Pattern[str],
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not isinstance(values, list):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}.facts.{field_name}",
                message=f"{field_name} must be a list.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"{entity_type}s.{entity_id}.facts.{field_name}",
                        value=type(values).__name__,
                    )
                ],
            )
        )
        return diagnostics

    for index, value in enumerate(values):
        if not isinstance(value, str) or not regex.fullmatch(value):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_UNKNOWN_ENUM_VALUE",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"{entity_type}s.{entity_id}.facts.{field_name}[{index}]",
                    message=f"Invalid id in {field_name}: {value}",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"{entity_type}s.{entity_id}.facts.{field_name}",
                            value=value,
                        )
                    ],
                )
            )
    return diagnostics


def _validate_requirement_asset_slots(
    *,
    requirement_id: str,
    asset_slots_obj: object,
    state_path: Path,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not isinstance(asset_slots_obj, dict):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type="requirement",
                entity_id=requirement_id,
                field_path=f"requirements.{requirement_id}.facts.asset_slots",
                message="asset_slots must be an object.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"requirements.{requirement_id}.facts.asset_slots",
                        value=type(asset_slots_obj).__name__,
                    )
                ],
            )
        )
        return diagnostics

    for slot_name in ("plan_latest", "module_index", "task_index"):
        slot_value = asset_slots_obj.get(slot_name)
        if not isinstance(slot_value, dict):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type="requirement",
                    entity_id=requirement_id,
                    field_path=f"requirements.{requirement_id}.facts.asset_slots.{slot_name}",
                    message=f"Missing asset slot fact for {slot_name}",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"requirements.{requirement_id}.facts.asset_slots.{slot_name}",
                            value=type(slot_value).__name__,
                        )
                    ],
                )
            )
            continue

        if not isinstance(slot_value.get("exists"), bool):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type="requirement",
                    entity_id=requirement_id,
                    field_path=(
                        f"requirements.{requirement_id}.facts.asset_slots.{slot_name}.exists"
                    ),
                    message=f"asset_slots.{slot_name}.exists must be boolean.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=(
                                f"requirements.{requirement_id}.facts.asset_slots.{slot_name}.exists"
                            ),
                            value=slot_value.get("exists"),
                        )
                    ],
                )
            )
        if not isinstance(slot_value.get("path"), str) or not str(slot_value.get("path")).strip():
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type="requirement",
                    entity_id=requirement_id,
                    field_path=f"requirements.{requirement_id}.facts.asset_slots.{slot_name}.path",
                    message=f"asset_slots.{slot_name}.path must be a non-empty string.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=(
                                f"requirements.{requirement_id}.facts.asset_slots.{slot_name}.path"
                            ),
                            value=slot_value.get("path"),
                        )
                    ],
                )
            )

    return diagnostics


def _validate_tracking_state(
    *,
    entity_type: str,
    entity_id: str,
    state_obj: object,
    state_path: Path,
    required: bool,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not isinstance(state_obj, dict):
        return diagnostics

    tracking = state_obj.get("tracking")
    if tracking is None:
        if required:
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"{entity_type}s.{entity_id}.state.tracking",
                    message="state.tracking must be an object.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"{entity_type}s.{entity_id}.state.tracking",
                            value=None,
                        )
                    ],
                )
            )
        return diagnostics

    if not isinstance(tracking, dict):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_INVALID_TRACKING_FIELD",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}.state.tracking",
                message="state.tracking must be an object.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"{entity_type}s.{entity_id}.state.tracking",
                        value=type(tracking).__name__,
                    )
                ],
            )
        )
        return diagnostics

    for key in ("active_round_id", "last_round_id"):
        value = tracking.get(key)
        if key not in tracking and required:
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_INVALID_TRACKING_FIELD",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"{entity_type}s.{entity_id}.state.tracking.{key}",
                    message=f"tracking.{key} is required.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"{entity_type}s.{entity_id}.state.tracking.{key}",
                            value=None,
                        )
                    ],
                )
            )
            continue
        if value is not None and (not isinstance(value, str) or not value.strip()):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_INVALID_TRACKING_FIELD",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"{entity_type}s.{entity_id}.state.tracking.{key}",
                    message=f"tracking.{key} must be null or non-empty string.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"{entity_type}s.{entity_id}.state.tracking.{key}",
                            value=value,
                        )
                    ],
                )
            )
    return diagnostics


def _validate_compliance(
    *,
    entity_type: str,
    entity_id: str,
    facts_obj: object,
    state_path: Path,
    required: bool,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not isinstance(facts_obj, dict):
        return diagnostics

    compliance = facts_obj.get("compliance")
    if compliance is None:
        if required:
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"{entity_type}s.{entity_id}.facts.compliance",
                    message="facts.compliance must be an object.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"{entity_type}s.{entity_id}.facts.compliance",
                            value=None,
                        )
                    ],
                )
            )
        return diagnostics

    if not isinstance(compliance, dict):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_INVALID_COMPLIANCE_FIELD",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}.facts.compliance",
                message="facts.compliance must be an object.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"{entity_type}s.{entity_id}.facts.compliance",
                        value=type(compliance).__name__,
                    )
                ],
            )
        )
        return diagnostics

    for key in ("naming_ok", "path_ok", "relations_ok", "language_ok"):
        value = compliance.get(key)
        if key not in compliance and required:
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_INVALID_COMPLIANCE_FIELD",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"{entity_type}s.{entity_id}.facts.compliance.{key}",
                    message=f"compliance.{key} is required.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"{entity_type}s.{entity_id}.facts.compliance.{key}",
                            value=None,
                        )
                    ],
                )
            )
            continue
        if value is not None and not isinstance(value, bool):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_INVALID_COMPLIANCE_FIELD",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"{entity_type}s.{entity_id}.facts.compliance.{key}",
                    message=f"compliance.{key} must be null or boolean.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"{entity_type}s.{entity_id}.facts.compliance.{key}",
                            value=value,
                        )
                    ],
                )
            )

    violations = compliance.get("violations")
    if not isinstance(violations, list):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_INVALID_COMPLIANCE_FIELD",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}.facts.compliance.violations",
                message="compliance.violations must be a list.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"{entity_type}s.{entity_id}.facts.compliance.violations",
                        value=type(violations).__name__,
                    )
                ],
            )
        )
    elif any(not isinstance(item, str) for item in violations):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_INVALID_COMPLIANCE_FIELD",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}.facts.compliance.violations",
                message="compliance.violations entries must be strings.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"{entity_type}s.{entity_id}.facts.compliance.violations",
                        value=violations,
                    )
                ],
            )
        )
    return diagnostics


def _validate_doc_flags(
    *,
    entity_type: str,
    entity_id: str,
    slot_name: str,
    slot_value: dict[str, object],
    state_path: Path,
    diagnostics: list[Diagnostic],
    field_root: str,
) -> None:
    for key in ("exists", "template_like"):
        if not isinstance(slot_value.get(key), bool):
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"{field_root}.{slot_name}.{key}",
                    message=f"facts.{slot_name}.{key} must be boolean.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"{field_root}.{slot_name}.{key}",
                            value=slot_value.get(key),
                        )
                    ],
                )
            )


def _validate_confirmed_state(
    *,
    entity_type: str,
    entity_id: str,
    state_obj: object,
    required_fields: tuple[str, ...],
    state_path: Path,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not isinstance(state_obj, dict):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}.state",
                message="state must be an object.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"{entity_type}s.{entity_id}.state",
                        value=type(state_obj).__name__,
                    )
                ],
            )
        )
        return diagnostics

    confirmed = state_obj.get("confirmed")
    if not isinstance(confirmed, dict):
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_MISSING_REQUIRED_FIELD",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}.state.confirmed",
                message="state.confirmed must be an object.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"{entity_type}s.{entity_id}.state.confirmed",
                        value=type(confirmed).__name__,
                    )
                ],
            )
        )
        return diagnostics

    for field in required_fields:
        if field not in confirmed:
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_MISSING_REQUIRED_FIELD",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"{entity_type}s.{entity_id}.state.confirmed.{field}",
                    message=f"Missing required confirmed field: {field}",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"{entity_type}s.{entity_id}.state.confirmed.{field}",
                            value=None,
                        )
                    ],
                )
            )

    if entity_type == "document":
        status = confirmed.get("status")
        if status not in DOCUMENT_STATUSES:
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_UNKNOWN_ENUM_VALUE",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"{entity_type}s.{entity_id}.state.confirmed.status",
                    message="Unknown document status value.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"{entity_type}s.{entity_id}.state.confirmed.status",
                            value=status,
                        )
                    ],
                )
            )

        review_status = str(confirmed.get("review_status"))
        if review_status not in REVIEW_STATUSES:
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_UNKNOWN_ENUM_VALUE",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"{entity_type}s.{entity_id}.state.confirmed.review_status",
                    message="Unknown review_status value.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"{entity_type}s.{entity_id}.state.confirmed.review_status",
                            value=confirmed.get("review_status"),
                        )
                    ],
                )
            )

        maturity = confirmed.get("maturity")
        if maturity is not None and maturity not in MATURITY_LEVELS:
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_UNKNOWN_ENUM_VALUE",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"{entity_type}s.{entity_id}.state.confirmed.maturity",
                    message="Unknown maturity value.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"{entity_type}s.{entity_id}.state.confirmed.maturity",
                            value=maturity,
                        )
                    ],
                )
            )

        for field_name in ("active_round_id", "last_round_id", "last_transition_id", "last_confirmed_at", "last_confirmed_by"):
            value = confirmed.get(field_name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                diagnostics.append(
                    make_diagnostic(
                        code="SCHEMA_MISSING_REQUIRED_FIELD",
                        severity="error",
                        entity_type=entity_type,
                        entity_id=entity_id,
                        field_path=f"{entity_type}s.{entity_id}.state.confirmed.{field_name}",
                        message=f"{field_name} must be a non-empty string when present.",
                        evidence=[
                            make_evidence(
                                type="state_check",
                                path=state_path.as_posix(),
                                ref=f"{entity_type}s.{entity_id}.state.confirmed.{field_name}",
                                value=value,
                            )
                        ],
                    )
                )

        blocker_refs = confirmed.get("blocker_refs")
        if isinstance(blocker_refs, list):
            for index, ref in enumerate(blocker_refs):
                if isinstance(ref, str) and not TYPED_BLOCKER_REF_RE.fullmatch(ref):
                    diagnostics.append(
                        make_diagnostic(
                            code="SCHEMA_INVALID_TYPED_REF",
                            severity="error",
                            entity_type=entity_type,
                            entity_id=entity_id,
                            field_path=f"{entity_type}s.{entity_id}.state.confirmed.blocker_refs[{index}]",
                            message=f"Invalid typed blocker ref: {ref}",
                            evidence=[
                                make_evidence(
                                    type="state_check",
                                    path=state_path.as_posix(),
                                    ref="state.confirmed.blocker_refs",
                                    value=ref,
                                )
                            ],
                        )
                    )
        return diagnostics

    candidate_status = str(confirmed.get("candidate_status"))
    if candidate_status not in CANDIDATE_STATUSES:
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_UNKNOWN_ENUM_VALUE",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}.state.confirmed.candidate_status",
                message="Unknown candidate_status value.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"{entity_type}s.{entity_id}.state.confirmed.candidate_status",
                        value=confirmed.get("candidate_status"),
                    )
                ],
            )
        )

    review_status = str(confirmed.get("review_status"))
    if review_status not in REVIEW_STATUSES:
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_UNKNOWN_ENUM_VALUE",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}.state.confirmed.review_status",
                message="Unknown review_status value.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"{entity_type}s.{entity_id}.state.confirmed.review_status",
                        value=confirmed.get("review_status"),
                    )
                ],
            )
        )

    readiness = str(confirmed.get("readiness"))
    if readiness not in READINESS_STATUSES:
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_UNKNOWN_ENUM_VALUE",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}.state.confirmed.readiness",
                message="Unknown readiness value.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"{entity_type}s.{entity_id}.state.confirmed.readiness",
                        value=confirmed.get("readiness"),
                    )
                ],
            )
        )

    maturity = confirmed.get("maturity")
    if maturity is not None and maturity not in MATURITY_LEVELS:
        diagnostics.append(
            make_diagnostic(
                code="SCHEMA_UNKNOWN_ENUM_VALUE",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}.state.confirmed.maturity",
                message="Unknown maturity value.",
                evidence=[
                    make_evidence(
                        type="state_check",
                        path=state_path.as_posix(),
                        ref=f"{entity_type}s.{entity_id}.state.confirmed.maturity",
                        value=maturity,
                    )
                ],
            )
        )

    if str(confirmed.get("implementation_doc_state", "")) and entity_type == "subtask":
        implementation_doc_state = str(confirmed.get("implementation_doc_state"))
        if implementation_doc_state not in IMPLEMENTATION_DOC_STATES:
            diagnostics.append(
                make_diagnostic(
                    code="SCHEMA_UNKNOWN_ENUM_VALUE",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"{entity_type}s.{entity_id}.state.confirmed.implementation_doc_state",
                    message="Unknown implementation_doc_state value.",
                    evidence=[
                        make_evidence(
                            type="state_check",
                            path=state_path.as_posix(),
                            ref=f"{entity_type}s.{entity_id}.state.confirmed.implementation_doc_state",
                            value=confirmed.get("implementation_doc_state"),
                        )
                    ],
                )
            )

    blocker_refs = confirmed.get("blocker_refs")
    if isinstance(blocker_refs, list):
        for index, ref in enumerate(blocker_refs):
            if isinstance(ref, str) and not TYPED_BLOCKER_REF_RE.fullmatch(ref):
                diagnostics.append(
                    make_diagnostic(
                        code="SCHEMA_INVALID_TYPED_REF",
                        severity="error",
                        entity_type=entity_type,
                        entity_id=entity_id,
                        field_path=(
                            f"{entity_type}s.{entity_id}.state.confirmed.blocker_refs[{index}]"
                        ),
                        message=f"Invalid typed blocker ref: {ref}",
                        evidence=[
                            make_evidence(
                                type="state_check",
                                path=state_path.as_posix(),
                                ref="state.confirmed.blocker_refs",
                                value=ref,
                            )
                        ],
                    )
                )

    return diagnostics
