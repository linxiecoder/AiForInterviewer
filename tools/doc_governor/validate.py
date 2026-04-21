from __future__ import annotations

import re
from pathlib import Path

from .diagnostics import Diagnostic, make_diagnostic, make_evidence
from .rules import evaluate_rules
from .schema import (
    CANDIDATE_STATUSES,
    IMPLEMENTATION_DOC_STATES,
    MATURITY_LEVELS,
    MODULE_DOC_SLOTS,
    READINESS_STATUSES,
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

MODULE_ID_RE = re.compile(r"^M\d{2}$")
SUBTASK_ID_RE = re.compile(r"^ST\d{2}_\d{2}$")
PATH_MODULE_TOKEN_RE = re.compile(r"^(M\d{2})(?:-|$|/)")
PATH_SUBTASK_TOKEN_RE = re.compile(r"^(ST\d{2}_\d{2})(?:-|$|/)")


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
    diagnostics.extend(_validate_modules(state.get("modules"), state_path))
    diagnostics.extend(_validate_subtasks(state.get("subtasks"), state_path))

    # Schema validation and rule validation are independent by design.
    diagnostics.extend(evaluate_rules(state))

    return diagnostics


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

    return diagnostics


def _validate_modules(modules_obj: object, state_path: Path) -> list[Diagnostic]:
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
            _validate_confirmed_state(
                entity_type="module",
                entity_id=module_id,
                state_obj=module.get("state"),
                required_fields=REQUIRED_CONFIRMED_FIELDS,
                state_path=state_path,
            )
        )

        if _extract_id_from_module_path(path) is not None:
            expected_id = _extract_id_from_module_path(path)
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


def _validate_subtasks(subtasks_obj: object, state_path: Path) -> list[Diagnostic]:
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
            _validate_confirmed_state(
                entity_type="subtask",
                entity_id=subtask_id,
                state_obj=subtask.get("state"),
                required_fields=SUBTASK_CONFIRMED_REQUIRED_FIELDS,
                state_path=state_path,
            )
        )

        if _extract_id_from_subtask_path(path) is not None:
            expected_id = _extract_id_from_subtask_path(path)
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


def _extract_id_from_module_path(path: str | None) -> str | None:
    if path is None:
        return None
    normalized = path.strip().strip("/").replace("\\", "/")
    for part in normalized.split("/"):
        match = PATH_MODULE_TOKEN_RE.match(part)
        if match:
            return match.group(1)
    return None


def _extract_id_from_subtask_path(path: str | None) -> str | None:
    if path is None:
        return None
    normalized = path.strip().strip("/").replace("\\", "/")
    for part in normalized.split("/"):
        match = PATH_SUBTASK_TOKEN_RE.match(part)
        if match:
            return match.group(1)
    return None
