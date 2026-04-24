from __future__ import annotations

import argparse
import copy
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .diagnostics import Diagnostic, make_diagnostic, make_evidence, result_to_json
from .evaluate import OQ_GATE_LEVELS, OQ_RESOLUTION_POLICIES, evaluate_state_file
from .rules import evaluate_rules
from .round_template import load_round_decision_anchor
from .schema import (
    CANDIDATE_STATUSES,
    DOCUMENT_STATUSES,
    IMPLEMENTATION_DOC_STATES,
    MATURITY_LEVELS,
    OQ_POLICY_SOURCE_BOOTSTRAP_DEFAULT,
    OFFICIAL_STATE_PATH,
    READINESS_STATUSES,
    REVIEW_STATUSES,
    SCHEMA_VERSION,
    TYPED_BLOCKER_REF_RE,
)
from .validate import validate_state_file


CONFIRM_ALLOWED_FIELDS_BY_ENTITY = {
    "module": frozenset(
        {
            "maturity",
            "candidate_status",
            "review_status",
            "readiness",
            "blocker_refs",
        }
    ),
    "subtask": frozenset(
        {
            "maturity",
            "candidate_status",
            "review_status",
            "readiness",
            "blocker_refs",
            "implementation_doc_state",
        }
    ),
    "document": frozenset(
        {
            "maturity",
            "status",
            "review_status",
            "blocker_refs",
            "active_round_id",
        }
    ),
    "policy": frozenset(
        {
            "formal_window_open",
        }
    ),
}
CONFIRM_FORBIDDEN_FIELDS = frozenset(
    {
        "last_transition_id",
        "last_confirmed_at",
        "last_confirmed_by",
    }
)
CONFIRM_TRANSITION_HISTORY = "transition_history.jsonl"
STATE_INPUT_PATH = OFFICIAL_STATE_PATH

READINESS_RANK = {
    "blocked": 0,
    "not_ready": 1,
    "downstream_ready": 2,
    "implementation_ready": 3,
}
CANDIDATE_RANK = {
    "none": 0,
    "observe": 1,
    "candidate": 2,
}
HARD_GATE_BLOCKER_PREFIXES = ("policy:asset_", "policy:language_non_compliant")


def confirm_transition(args: argparse.Namespace) -> int:
    state_path = Path(args.input or STATE_INPUT_PATH).resolve()
    official_state_path = Path(STATE_INPUT_PATH).resolve()
    evidence_refs = list(args.evidence_ref or [])

    diagnostics = _validate_input_paths(state_path, official_state_path)
    if args.entity_type not in {"module", "subtask", "document", "policy"}:
        diagnostics.append(
            make_diagnostic(
                code="CONFIRM_ENTITY_TYPE_INVALID",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="entity_type",
                message="entity_type must be module, subtask, document, or policy",
                evidence=[
                    make_evidence(
                        type="cli",
                        path="--entity-type",
                        ref="value",
                        value=args.entity_type,
                    )
                ],
            )
        )
    if not args.entity_id:
        diagnostics.append(
            make_diagnostic(
                code="CONFIRM_ENTITY_ID_MISSING",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="entity_id",
                message="entity-id is required",
                evidence=[
                    make_evidence(
                        type="cli",
                        path="--entity-id",
                        ref="value",
                        value="",
                    )
                ],
            )
        )
    if args.mode in {"approve", "reject"}:
        if not (args.actor and str(args.actor).strip()):
            diagnostics.append(
                make_diagnostic(
                    code="CONFIRM_ACTOR_REQUIRED",
                    severity="error",
                    entity_type="system",
                    entity_id="GLOBAL",
                    field_path="--actor",
                    message="actor is required for approve or reject",
                    evidence=[
                        make_evidence(
                            type="cli",
                            path="--actor",
                            ref="value",
                            value=args.actor,
                        )
                    ],
                )
            )
        if not (args.reason and str(args.reason).strip()):
            diagnostics.append(
                make_diagnostic(
                    code="CONFIRM_REASON_REQUIRED",
                    severity="error",
                    entity_type="system",
                    entity_id="GLOBAL",
                    field_path="--reason",
                    message="reason is required for approve or reject",
                    evidence=[
                        make_evidence(
                            type="cli",
                            path="--reason",
                            ref="value",
                            value=args.reason,
                        )
                    ],
                )
            )

    round_id = (getattr(args, "round_id", None) or "").strip()
    if round_id:
        anchor = load_round_decision_anchor(round_id=round_id)
        if anchor is None:
            diagnostics.append(
                make_diagnostic(
                    code="CONFIRM_ROUND_TEMPLATE_NOT_FOUND",
                    severity="error",
                    entity_type="system",
                    entity_id="GLOBAL",
                    field_path="--round-id",
                    message="round template not found under docs/governance/rounds",
                    evidence=[
                        make_evidence(
                            type="file_check",
                            path=f"docs/governance/rounds/{round_id}.md",
                            ref="exists",
                            value=False,
                        )
                    ],
                )
            )
        elif anchor not in str(args.reason or ""):
            diagnostics.append(
                make_diagnostic(
                    code="CONFIRM_REASON_MISSING_DECISION_ANCHOR",
                    severity="error",
                    entity_type="system",
                    entity_id="GLOBAL",
                    field_path="--reason",
                    message=f"reason must include decision anchor: {anchor}",
                    evidence=[
                        make_evidence(
                            type="cli",
                            path="--reason",
                            ref="contains",
                            value=anchor,
                        )
                    ],
                )
            )

    if args.mode not in {"dry-run", "approve", "reject"}:
        diagnostics.append(
            make_diagnostic(
                code="CONFIRM_MODE_INVALID",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="--mode",
                message="mode must be dry-run, approve, or reject",
                evidence=[
                    make_evidence(
                        type="cli",
                        path="--mode",
                        ref="value",
                        value=args.mode,
                    )
                ],
            )
        )
    if any(item.severity == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    validation_diagnostics = validate_state_file(state_path)
    diagnostics.extend(validation_diagnostics)
    if any(item.severity == "error" for item in validation_diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    state = _load_state(state_path)
    if not isinstance(state, dict):
        diagnostics.append(
            make_diagnostic(
                code="CONFIRM_STATE_LOAD_FAILED",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="state",
                message="state file must be a mapping",
                evidence=[
                    make_evidence(
                        type="file_parse",
                        path=state_path.as_posix(),
                        ref="mapping",
                        value=type(state).__name__,
                    )
                ],
            )
        )
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    proposed = _parse_proposed_changes(args.proposed_changes)
    if proposed is None:
        diagnostics.append(
            make_diagnostic(
                code="CONFIRM_PROPOSED_CHANGES_PARSE_ERROR",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="--proposed-changes",
                message="failed to parse proposed changes",
                evidence=[
                    make_evidence(
                        type="cli",
                        path="--proposed-changes",
                        ref="value",
                        value=args.proposed_changes,
                    )
                ],
            )
        )
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    entity_type = args.entity_type
    entity_id = args.entity_id
    entity = _extract_entity(state=state, entity_type=entity_type, entity_id=entity_id)
    if entity is None:
        diagnostics.append(
            make_diagnostic(
                code="CONFIRM_ENTITY_NOT_FOUND",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}",
                message="entity not found in official state",
                evidence=[
                    make_evidence(
                        type="state_lookup",
                        path=state_path.as_posix(),
                        ref="entity_id",
                        value=entity_id,
                    )
                ],
            )
        )
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    before_state = _extract_confirmed_state(entity)
    if not before_state:
        diagnostics.append(
            make_diagnostic(
                code="CONFIRM_STATE_SECTION_MISSING",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}.state.confirmed",
                message="confirmed state is required",
                evidence=[
                    make_evidence(
                        type="state_section",
                        path=state_path.as_posix(),
                        ref="state.confirmed",
                        value=None,
                    )
                ],
            )
        )
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    validation_state_changes = _validate_state_change_inputs(
        entity_type=entity_type,
        entity_id=entity_id,
        before_state=before_state,
        proposed_changes=proposed,
        evidence_refs=evidence_refs,
    )
    diagnostics.extend(validation_state_changes)
    if any(item.severity == "error" for item in validation_state_changes):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    after_state = copy.deepcopy(before_state)
    for field, value in proposed.items():
        after_state[field] = value

    changed_fields = _collect_changed_fields(before_state, after_state)

    candidate_promotion = entity_type in {"module", "subtask"} and _is_candidate_status_promotion(before_state, after_state)
    readiness_promotion = entity_type in {"module", "subtask"} and _is_readiness_promotion(before_state, after_state)
    if candidate_promotion and not evidence_refs:
        diagnostics.append(
            make_diagnostic(
                code="CONFIRM_EVIDENCE_REQUIRED",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}.state.confirmed.candidate_status",
                message="candidate_status promotion requires at least one evidence-ref",
                evidence=[
                    make_evidence(
                        type="cli",
                        path="--evidence-ref",
                        ref="required",
                        value=None,
                    )
                ],
            )
        )

    if (candidate_promotion or readiness_promotion) and _is_blocked_by_bootstrap_default(
        entity_type=entity_type,
        entity_id=entity_id,
        state=state,
        before_state=before_state,
        after_state=after_state,
        candidate_promotion=candidate_promotion,
        readiness_promotion=readiness_promotion,
    ):
        blocked = _check_bootstrap_default_oq_blockers(
            entity_type=entity_type,
            entity_id=entity_id,
            state=state,
            before_state=before_state,
            after_state=after_state,
            candidate_promotion=candidate_promotion,
            readiness_promotion=readiness_promotion,
        )
        diagnostics.extend(blocked)

    if any(item.severity == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    if args.mode == "approve":
        approve_gate_diagnostics = _validate_approve_gate_blockers(
            state_path=state_path,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        diagnostics.extend(approve_gate_diagnostics)
        if any(item.severity == "error" for item in approve_gate_diagnostics):
            print(result_to_json(ok=False, diagnostics=diagnostics))
            return 1

    draft = copy.deepcopy(state)
    _write_entity_confirmed_state(
        draft=draft,
        entity_type=entity_type,
        entity_id=entity_id,
        confirmed_state=after_state,
    )
    rule_diagnostics = evaluate_rules(draft)
    diagnostics.extend(rule_diagnostics)
    if any(item.severity == "error" for item in rule_diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    transition_id = uuid.uuid4().hex
    timestamp = datetime.now(timezone.utc).isoformat()
    if args.mode == "dry-run":
        print(
            result_to_json(
                ok=True,
                diagnostics=[],
                entity_type=entity_type,
                entity_id=entity_id,
                mode="dry-run",
                dry_run=True,
                transition_id=transition_id,
                changed_fields=sorted(changed_fields),
            )
        )
        return 0

    actor = args.actor or "system"
    reason = args.reason or ""
    if args.mode == "approve":
        applied_state = copy.deepcopy(after_state)
        if entity_type != "policy":
            applied_state["last_transition_id"] = transition_id
            applied_state["last_confirmed_at"] = timestamp
            applied_state["last_confirmed_by"] = actor
        _write_entity_confirmed_state(
            draft=draft,
            entity_type=entity_type,
            entity_id=entity_id,
            confirmed_state=applied_state,
        )
        if not _write_state_file(draft, state_path, diagnostics):
            print(result_to_json(ok=False, diagnostics=diagnostics))
            return 1
    else:
        # reject keeps official state unchanged
        applied_state = before_state

    if not _append_transition_history(
        history_path=state_path.parent / CONFIRM_TRANSITION_HISTORY,
        transition_id=transition_id,
        timestamp=timestamp,
        actor=actor,
        round_id=(str(args.round_id).strip() or None) if args.round_id is not None else None,
        entity_type=entity_type,
        entity_id=entity_id,
        dry_run=False,
        before_confirmed_state=before_state,
        proposed_state=after_state,
        applied_state=applied_state,
        changed_fields=changed_fields,
        evidence_refs=evidence_refs,
        reason=reason,
        schema_version=state.get("schema_version", SCHEMA_VERSION),
    ):
        diagnostics.append(
            make_diagnostic(
                code="CONFIRM_HISTORY_WRITE_FAILED",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="transition_history.jsonl",
                message="failed to append transition history",
                evidence=[
                    make_evidence(
                        type="file_write",
                        path=str(state_path.parent / CONFIRM_TRANSITION_HISTORY),
                        ref="append",
                        value=True,
                    )
                ],
            )
        )
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    print(
        result_to_json(
            ok=True,
            diagnostics=[],
            entity_type=entity_type,
            entity_id=entity_id,
            mode=args.mode,
            dry_run=False,
            transition_id=transition_id,
            changed_fields=sorted(changed_fields),
        )
    )
    return 0


def _validate_input_paths(state_path: Path, official_state_path: Path) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if state_path != official_state_path:
        diagnostics.append(
            make_diagnostic(
                code="CONFIRM_STATE_PATH_FORBIDDEN",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="input",
                message="confirm-transition only accepts official DOC_STATE.yaml",
                evidence=[
                    make_evidence(
                        type="file_check",
                        path=state_path.as_posix(),
                        ref="official_path",
                        value=official_state_path.as_posix(),
                    )
                ],
            )
        )
    return diagnostics


def _load_state(path: Path) -> dict[str, object] | list[Any] | None:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(f"PyYAML unavailable: {exc}") from exc

    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        return data
    return None


def _parse_proposed_changes(raw: str | None) -> dict[str, object] | None:
    if not raw:
        return None
    try:
        obj = json.loads(raw)
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    return obj


def _extract_entity(
    *,
    state: dict[str, object],
    entity_type: str,
    entity_id: str,
) -> dict[str, object] | None:
    if entity_type == "policy":
        if entity_id != "global_policy":
            return None
        policy = state.get("global_policy")
        if not isinstance(policy, dict):
            return None
        return {"state": {"confirmed": copy.deepcopy(policy)}}
    entities = state.get(f"{entity_type}s")
    if not isinstance(entities, dict):
        return None
    entity = entities.get(entity_id)
    if not isinstance(entity, dict):
        return None
    return entity


def _extract_confirmed_state(entity: dict[str, object]) -> dict[str, object]:
    state_obj = entity.get("state")
    if not isinstance(state_obj, dict):
        return {}
    confirmed = state_obj.get("confirmed")
    if isinstance(confirmed, dict):
        return copy.deepcopy(confirmed)
    return {}


def _extract_facts(entity: dict[str, object]) -> dict[str, object]:
    facts = entity.get("facts")
    if isinstance(facts, dict):
        return facts
    return {}


def _validate_state_change_inputs(
    *,
    entity_type: str,
    entity_id: str,
    before_state: dict[str, object],
    proposed_changes: dict[str, Any],
    evidence_refs: list[str],
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    allowed_fields = CONFIRM_ALLOWED_FIELDS_BY_ENTITY.get(entity_type, frozenset())
    for field in proposed_changes:
        if field in CONFIRM_FORBIDDEN_FIELDS:
            diagnostics.append(
                make_diagnostic(
                    code="CONFIRM_FORBIDDEN_PROPOSED_CHANGE",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"{field}",
                    message=f"proposed field '{field}' is system-managed",
                    evidence=[
                        make_evidence(
                            type="cli",
                            path="--proposed-changes",
                            ref=field,
                            value=proposed_changes.get(field),
                        )
                    ],
                )
            )
            continue
        if field not in allowed_fields:
            diagnostics.append(
                make_diagnostic(
                    code="CONFIRM_FORBIDDEN_PROPOSED_CHANGE",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"{field}",
                    message=f"unsupported proposed field '{field}'",
                    evidence=[
                        make_evidence(
                            type="cli",
                            path="--proposed-changes",
                            ref=field,
                            value=proposed_changes.get(field),
                        )
                    ],
                )
            )
            continue

        if field == "implementation_doc_state" and entity_type != "subtask":
            diagnostics.append(
                make_diagnostic(
                    code="CONFIRM_FIELD_SCOPE_VIOLATION",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"state.confirmed.{field}",
                    message="implementation_doc_state is valid only for subtask",
                    evidence=[
                        make_evidence(
                            type="cli",
                            path="--proposed-changes",
                            ref=field,
                            value=proposed_changes.get(field),
                        )
                    ],
                )
            )
            continue

        if field == "formal_window_open":
            if entity_type != "policy":
                diagnostics.append(
                    make_diagnostic(
                        code="CONFIRM_FIELD_SCOPE_VIOLATION",
                        severity="error",
                        entity_type=entity_type,
                        entity_id=entity_id,
                        field_path=f"state.confirmed.{field}",
                        message="formal_window_open is valid only for policy",
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="--proposed-changes",
                                ref=field,
                                value=proposed_changes.get(field),
                            )
                        ],
                    )
                )
                continue
            if not isinstance(proposed_changes.get(field), bool):
                diagnostics.append(
                    make_diagnostic(
                        code="CONFIRM_UNKNOWN_ENUM",
                        severity="error",
                        entity_type=entity_type,
                        entity_id=entity_id,
                        field_path=f"state.confirmed.{field}",
                        message="formal_window_open must be boolean",
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="--proposed-changes",
                                ref=field,
                                value=proposed_changes.get(field),
                            )
                        ],
                    )
                )
            continue

        if field == "maturity" and proposed_changes.get(field) not in MATURITY_LEVELS + (None,):
            diagnostics.append(
                make_diagnostic(
                    code="CONFIRM_UNKNOWN_ENUM",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"state.confirmed.{field}",
                    message="Unknown maturity value",
                    evidence=[
                        make_evidence(
                            type="cli",
                            path="--proposed-changes",
                            ref=field,
                            value=proposed_changes.get(field),
                        )
                    ],
                )
            )
        if field == "candidate_status" and proposed_changes.get(field) not in CANDIDATE_STATUSES:
            diagnostics.append(
                make_diagnostic(
                    code="CONFIRM_UNKNOWN_ENUM",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"state.confirmed.{field}",
                    message="Unknown candidate_status value",
                    evidence=[
                        make_evidence(
                            type="cli",
                            path="--proposed-changes",
                            ref=field,
                            value=proposed_changes.get(field),
                        )
                    ],
                )
            )
        if field == "review_status" and proposed_changes.get(field) not in REVIEW_STATUSES:
            diagnostics.append(
                make_diagnostic(
                    code="CONFIRM_UNKNOWN_ENUM",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"state.confirmed.{field}",
                    message="Unknown review_status value",
                    evidence=[
                        make_evidence(
                            type="cli",
                            path="--proposed-changes",
                            ref=field,
                            value=proposed_changes.get(field),
                        )
                    ],
                )
            )
        if field == "status" and proposed_changes.get(field) not in DOCUMENT_STATUSES:
            diagnostics.append(
                make_diagnostic(
                    code="CONFIRM_UNKNOWN_ENUM",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"state.confirmed.{field}",
                    message="Unknown document status value",
                    evidence=[
                        make_evidence(
                            type="cli",
                            path="--proposed-changes",
                            ref=field,
                            value=proposed_changes.get(field),
                        )
                    ],
                )
            )
        if field == "readiness" and proposed_changes.get(field) not in READINESS_STATUSES:
            diagnostics.append(
                make_diagnostic(
                    code="CONFIRM_UNKNOWN_ENUM",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"state.confirmed.{field}",
                    message="Unknown readiness value",
                    evidence=[
                        make_evidence(
                            type="cli",
                            path="--proposed-changes",
                            ref=field,
                            value=proposed_changes.get(field),
                        )
                    ],
                )
            )
        if field == "implementation_doc_state" and proposed_changes.get(field) not in IMPLEMENTATION_DOC_STATES:
            diagnostics.append(
                make_diagnostic(
                    code="CONFIRM_UNKNOWN_ENUM",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"state.confirmed.{field}",
                    message="Unknown implementation_doc_state value",
                    evidence=[
                        make_evidence(
                            type="cli",
                            path="--proposed-changes",
                            ref=field,
                            value=proposed_changes.get(field),
                        )
                    ],
                )
            )
        if field == "blocker_refs":
            blocker_refs = proposed_changes.get(field)
            if not isinstance(blocker_refs, list):
                diagnostics.append(
                    make_diagnostic(
                        code="CONFIRM_INVALID_BLOCKER_REFS",
                        severity="error",
                        entity_type=entity_type,
                        entity_id=entity_id,
                        field_path="state.confirmed.blocker_refs",
                        message="blocker_refs must be a list",
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="--proposed-changes",
                                ref=field,
                                value=blocker_refs,
                            )
                        ],
                    )
                )
            else:
                for index, ref in enumerate(blocker_refs):
                    if not isinstance(ref, str):
                        diagnostics.append(
                            make_diagnostic(
                                code="CONFIRM_INVALID_TYPED_REF",
                                severity="error",
                                entity_type=entity_type,
                                entity_id=entity_id,
                                field_path=f"state.confirmed.blocker_refs[{index}]",
                                message="blocker ref must be string",
                                evidence=[
                                    make_evidence(
                                        type="cli",
                                        path="--proposed-changes",
                                        ref=field,
                                        value=ref,
                                    )
                                ],
                            )
                        )
                    elif not TYPED_BLOCKER_REF_RE.fullmatch(ref):
                        diagnostics.append(
                            make_diagnostic(
                                code="CONFIRM_INVALID_TYPED_REF",
                                severity="error",
                                entity_type=entity_type,
                                entity_id=entity_id,
                                field_path=f"state.confirmed.blocker_refs[{index}]",
                                message="invalid blocker ref",
                                evidence=[
                                    make_evidence(
                                        type="cli",
                                        path="--proposed-changes",
                                        ref=field,
                                        value=ref,
                                    )
                                ],
                            )
                        )
        if field == "active_round_id":
            active_round_id = proposed_changes.get(field)
            if active_round_id is not None and (not isinstance(active_round_id, str) or not active_round_id.strip()):
                diagnostics.append(
                    make_diagnostic(
                        code="CONFIRM_UNKNOWN_ENUM",
                        severity="error",
                        entity_type=entity_type,
                        entity_id=entity_id,
                        field_path="state.confirmed.active_round_id",
                        message="active_round_id must be a non-empty string when present",
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="--proposed-changes",
                                ref=field,
                                value=active_round_id,
                            )
                        ],
                    )
                )

    for ref in evidence_refs:
        if not TYPED_BLOCKER_REF_RE.fullmatch(ref):
            diagnostics.append(
                make_diagnostic(
                    code="CONFIRM_INVALID_TYPED_REF",
                    severity="error",
                    entity_type="system",
                    entity_id="GLOBAL",
                    field_path="--evidence-ref",
                    message="invalid evidence ref",
                    evidence=[
                        make_evidence(
                            type="cli",
                            path="--evidence-ref",
                            ref="value",
                            value=ref,
                        )
                    ],
                )
            )

    after_state = copy.deepcopy(before_state)
    after_state.update(proposed_changes)
    if entity_type in {"document", "policy"}:
        return diagnostics
    candidate_status = str(after_state.get("candidate_status"))
    review_status = str(after_state.get("review_status"))
    readiness = str(after_state.get("readiness"))

    if candidate_status == "candidate" and review_status != "pending_confirmation":
        diagnostics.append(
            make_diagnostic(
                code="RULE_ILLEGAL_STATE_COMBINATION",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}.state.confirmed.review_status",
                message="candidate requires pending_confirmation review_status",
                evidence=[
                    make_evidence(
                        type="state_transition",
                        path=f"{entity_type}:{entity_id}",
                        ref="candidate_status/review_status",
                        value={"candidate_status": candidate_status, "review_status": review_status},
                    )
                ],
            )
        )

    if candidate_status in {"none", "observe"} and review_status == "approved":
        diagnostics.append(
            make_diagnostic(
                code="RULE_ILLEGAL_STATE_COMBINATION",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}.state.confirmed.review_status",
                message="approved review requires candidate status",
                evidence=[
                    make_evidence(
                        type="state_transition",
                        path=f"{entity_type}:{entity_id}",
                        ref="candidate_status/review_status",
                        value={"candidate_status": candidate_status, "review_status": review_status},
                    )
                ],
            )
        )

    if readiness == "implementation_ready" and entity_type != "subtask":
        if after_state.get("readiness") != before_state.get("readiness"):
            diagnostics.append(
                make_diagnostic(
                    code="CONFIRM_FIELD_SCOPE_VIOLATION",
                    severity="error",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_path=f"{entity_type}s.{entity_id}.state.confirmed.readiness",
                    message="module readiness cannot be set to implementation_ready",
                    evidence=[
                        make_evidence(
                            type="state_transition",
                            path=f"{entity_type}:{entity_id}",
                            ref="readiness",
                            value=readiness,
                        )
                    ],
                )
            )

    return diagnostics


def _collect_changed_fields(before: dict[str, object], after: dict[str, object]) -> list[str]:
    keys = set(before) | set(after)
    changed = []
    for key in keys:
        if before.get(key) != after.get(key):
            changed.append(key)
    return sorted(changed)


def _is_candidate_status_promotion(before: dict[str, object], after: dict[str, object]) -> bool:
    before_status = str(before.get("candidate_status"))
    after_status = str(after.get("candidate_status"))
    return (
        CANDIDATE_RANK.get(before_status, -1) < CANDIDATE_RANK.get(after_status, -1)
        and after_status == "candidate"
    )


def _is_readiness_promotion(before: dict[str, object], after: dict[str, object]) -> bool:
    before_status = str(before.get("readiness"))
    after_status = str(after.get("readiness"))
    return READINESS_RANK.get(after_status, -1) > READINESS_RANK.get(before_status, -1)


def _is_blocked_by_bootstrap_default(
    *,
    entity_type: str,
    entity_id: str,
    state: dict[str, object],
    before_state: dict[str, object],
    after_state: dict[str, object],
    candidate_promotion: bool,
    readiness_promotion: bool,
) -> bool:
    facts = _extract_facts(_extract_entity(state=state, entity_type=entity_type, entity_id=entity_id) or {})
    related_oq_ids = facts.get("related_oq_ids")
    if not isinstance(related_oq_ids, list):
        return False

    oqs = state.get("oqs")
    if not isinstance(oqs, dict):
        return False

    if not (candidate_promotion or readiness_promotion):
        return False

    for oq_id in related_oq_ids:
        if not isinstance(oq_id, str):
            continue
        oq = oqs.get(oq_id)
        if not isinstance(oq, dict):
            continue
        if oq.get("gate_policy_source") != OQ_POLICY_SOURCE_BOOTSTRAP_DEFAULT:
            continue

        gate_level = str(oq.get("gate_level", ""))
        resolution_policy = str(oq.get("resolution_policy", ""))
        status = str(oq.get("status", ""))
        if gate_level not in OQ_GATE_LEVELS or resolution_policy not in OQ_RESOLUTION_POLICIES:
            continue

        enforcement = _oq_enforcement(
            gate_level=gate_level,
            resolution_policy=resolution_policy,
            status_class=_oq_status_class(status),
        )

        if candidate_promotion and gate_level == "candidate_gate" and enforcement != "clear":
            return True
        if readiness_promotion and gate_level == "readiness_gate" and enforcement != "clear":
            return True

    return False


def _check_bootstrap_default_oq_blockers(
    *,
    entity_type: str,
    entity_id: str,
    state: dict[str, object],
    before_state: dict[str, object],
    after_state: dict[str, object],
    candidate_promotion: bool,
    readiness_promotion: bool,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if not (candidate_promotion or readiness_promotion):
        return diagnostics

    blocked_oqs: list[str] = []
    facts = _extract_facts(_extract_entity(state=state, entity_type=entity_type, entity_id=entity_id) or {})
    related_oq_ids = facts.get("related_oq_ids")
    if not isinstance(related_oq_ids, list):
        return diagnostics

    oqs = state.get("oqs")
    if not isinstance(oqs, dict):
        return diagnostics

    for oq_id in related_oq_ids:
        if not isinstance(oq_id, str):
            continue
        oq = oqs.get(oq_id)
        if not isinstance(oq, dict):
            continue
        if oq.get("gate_policy_source") != OQ_POLICY_SOURCE_BOOTSTRAP_DEFAULT:
            continue

        gate_level = str(oq.get("gate_level", ""))
        resolution_policy = str(oq.get("resolution_policy", ""))
        status = str(oq.get("status", ""))
        if gate_level not in OQ_GATE_LEVELS or resolution_policy not in OQ_RESOLUTION_POLICIES:
            continue

        enforcement = _oq_enforcement(
            gate_level=gate_level,
            resolution_policy=resolution_policy,
            status_class=_oq_status_class(status),
        )
        if candidate_promotion and gate_level == "candidate_gate" and enforcement != "clear":
            blocked_oqs.append(oq_id)
        if readiness_promotion and gate_level == "readiness_gate" and enforcement != "clear":
            blocked_oqs.append(oq_id)

    if blocked_oqs:
        diagnostics.append(
            make_diagnostic(
                code="CONFIRM_BOOTSTRAP_DEFAULT_OQ_POLICY_BLOCKS_APPROVE",
                severity="error",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=f"{entity_type}s.{entity_id}",
                message=(
                    "bootstrap default OQ policy cannot alone support candidate/readiness promotion"
                ),
                evidence=[
                    make_evidence(
                        type="oq_policy_source",
                        path="DOC_STATE.yaml",
                        ref="blocked_oq_ids",
                        value=sorted(set(blocked_oqs)),
                    )
                ],
            )
        )

    return diagnostics


def _validate_approve_gate_blockers(
    *,
    state_path: Path,
    entity_type: str,
    entity_id: str,
) -> list[Diagnostic]:
    if entity_type == "policy":
        return []
    diagnostics, payload = evaluate_state_file(state_path)
    evaluation_errors = [item for item in diagnostics if item.severity == "error"]
    if evaluation_errors:
        return evaluation_errors

    entity_key = "subtasks" if entity_type == "subtask" else f"{entity_type}s"
    entity_payload = payload.get(entity_key)
    entity_payload = entity_payload if isinstance(entity_payload, dict) else {}
    derived = entity_payload.get(entity_id)
    derived = derived if isinstance(derived, dict) else {}
    derived_state = derived.get("derived")
    derived_state = derived_state if isinstance(derived_state, dict) else {}
    blocker_refs = derived_state.get("blocker_refs")
    blocker_refs = blocker_refs if isinstance(blocker_refs, list) else []

    hard_blockers = sorted(
        ref for ref in blocker_refs if isinstance(ref, str) and _is_hard_gate_blocker(ref)
    )
    if not hard_blockers:
        return []

    return [
        make_diagnostic(
            code="CONFIRM_HARD_GATE_BLOCKERS_PRESENT",
            severity="error",
            entity_type=entity_type,
            entity_id=entity_id,
            field_path=f"{entity_type}s.{entity_id}.state.confirmed",
            message=(
                "approve blocked by unresolved hard gate blockers: "
                + ", ".join(hard_blockers)
            ),
            evidence=[
                make_evidence(
                    type="gate_evaluation",
                    path=state_path.as_posix(),
                    ref="blocker_refs",
                    value=hard_blockers,
                )
            ],
        )
    ]


def _write_entity_confirmed_state(
    *,
    draft: dict[str, object],
    entity_type: str,
    entity_id: str,
    confirmed_state: dict[str, object],
) -> None:
    if entity_type == "policy":
        draft["global_policy"] = copy.deepcopy(confirmed_state)
        return
    draft[entity_type + "s"][entity_id]["state"]["confirmed"] = confirmed_state


def _is_hard_gate_blocker(ref: str) -> bool:
    return any(ref.startswith(prefix) for prefix in HARD_GATE_BLOCKER_PREFIXES)


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
        return "clear" if status_class in {"confirmed_clear", "manual_override_clear"} else "review_only"

    if gate_level == "candidate_gate":
        if resolution_policy == "confirmed_only":
            return "candidate_blocker" if status_class != "confirmed_clear" else "clear"
        if resolution_policy == "manual_override_only":
            return "candidate_blocker" if status_class != "manual_override_clear" else "clear"
        if status_class == "proposed_default":
            return "review_only"
        return "candidate_blocker" if status_class == "unresolved" else "clear"

    if gate_level == "readiness_gate":
        if resolution_policy == "confirmed_only":
            return "readiness_blocker" if status_class != "confirmed_clear" else "clear"
        if resolution_policy == "manual_override_only":
            return "readiness_blocker" if status_class != "manual_override_clear" else "clear"
        if status_class == "proposed_default":
            return "review_only"
        return "readiness_blocker" if status_class == "unresolved" else "clear"

    return "review_only"


def _write_state_file(state: dict[str, object], state_path: Path, diagnostics: list[Diagnostic]) -> bool:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        diagnostics.append(
            make_diagnostic(
                code="CONFIRM_PYYAML_UNAVAILABLE",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="python.dependencies.yaml",
                message="PyYAML is required by confirm-transition",
                evidence=[
                    make_evidence(
                        type="dependency",
                        path=state_path.as_posix(),
                        ref="import yaml",
                        value=str(exc),
                    )
                ],
            )
        )
        return False
    try:
        state_path.write_text(
            yaml.safe_dump(state, allow_unicode=True, sort_keys=False, width=120),
            encoding="utf-8",
        )
        return True
    except Exception as exc:  # noqa: BLE001
        diagnostics.append(
            make_diagnostic(
                code="CONFIRM_STATE_WRITE_FAILED",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path=state_path.as_posix(),
                message=f"failed to write official state: {exc}",
                evidence=[
                    make_evidence(
                        type="file_write",
                        path=state_path.as_posix(),
                        ref="write",
                        value=str(exc),
                    )
                ],
            )
        )
        return False


def _append_transition_history(
    *,
    history_path: Path,
    transition_id: str,
    timestamp: str,
    actor: str,
    round_id: str | None,
    entity_type: str,
    entity_id: str,
    dry_run: bool,
    before_confirmed_state: dict[str, object],
    proposed_state: dict[str, object],
    applied_state: dict[str, object],
    changed_fields: list[str],
    evidence_refs: list[str],
    reason: str,
    schema_version: int,
) -> bool:
    record = {
        "transition_id": transition_id,
        "timestamp": timestamp,
        "actor": actor,
        "round_id": round_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "dry_run": dry_run,
        "before_confirmed_state": {
            "schema_version": schema_version,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "confirmed": before_confirmed_state,
        },
        "proposed_state": proposed_state,
        "applied_state": applied_state,
        "changed_fields": changed_fields,
        "evidence_refs": evidence_refs,
        "reason": reason,
        "schema_version": schema_version,
    }
    try:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False
