from __future__ import annotations

import argparse
import copy
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from diagnostics import Diagnostic
    from diagnostics import make_diagnostic, make_evidence, result_to_json
    from preflight import preflight_open_window
else:
    from .diagnostics import Diagnostic, make_diagnostic, make_evidence, result_to_json
    from .preflight import preflight_open_window


WINDOW_STATUS_OPEN = "open"
WINDOW_STATUS_CLOSED = "closed"
WINDOW_FIELDS = (
    "window_status",
    "window_opened_at",
    "window_opened_by",
    "window_reason",
)


def _default_window_state() -> dict[str, Any]:
    return {
        "window_status": WINDOW_STATUS_CLOSED,
        "window_opened_at": None,
        "window_opened_by": None,
        "window_reason": None,
    }


def _make_diagnostic(
    *,
    code: str,
    message: str,
    entity_type: str,
    entity_id: str,
    field_path: str,
    value: Any = None,
) -> Diagnostic:
    return make_diagnostic(
        code=code,
        severity="error",
        entity_type=entity_type,
        entity_id=entity_id,
        field_path=field_path,
        message=message,
        evidence=[
            make_evidence(
                type="cli",
                path="open-window",
                ref=field_path,
                value=value,
            )
        ],
    )


def open_window(args: argparse.Namespace) -> int:
    mode = str(args.mode or "").strip().lower()
    entity_type = args.entity_type
    entity_id = args.entity_id
    actor = args.actor
    reason = args.reason
    state_path = Path(args.state).resolve()
    history_path = Path(args.history or "docs/governance/transition_history.jsonl").resolve()

    diagnostics: list[Diagnostic] = []
    if not entity_type:
        diagnostics.append(
            _make_diagnostic(
                code="OPEN_WINDOW_ENTITY_TYPE_MISSING",
                message="entity-type is required",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="--entity-type",
                value=None,
            )
        )
    if not entity_id:
        diagnostics.append(
            _make_diagnostic(
                code="OPEN_WINDOW_ENTITY_ID_MISSING",
                message="entity-id is required",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="--entity-id",
                value=None,
            )
        )
    if mode not in {"dry-run", "apply"}:
        diagnostics.append(
            _make_diagnostic(
                code="OPEN_WINDOW_MODE_INVALID",
                message="mode must be dry-run or apply",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="--mode",
                value=args.mode,
            )
        )
    if mode == "apply" and (not actor or not str(actor).strip()):
        diagnostics.append(
            _make_diagnostic(
                code="OPEN_WINDOW_ACTOR_REQUIRED",
                message="actor is required in apply mode",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="--actor",
                value=actor,
            )
        )
    if mode == "apply" and (not reason or not str(reason).strip()):
        diagnostics.append(
            _make_diagnostic(
                code="OPEN_WINDOW_REASON_REQUIRED",
                message="reason is required in apply mode",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="--reason",
                value=reason,
            )
        )
    if entity_type not in {"module", "subtask"} and entity_type is not None:
        diagnostics.append(
            _make_diagnostic(
                code="OPEN_WINDOW_ENTITY_TYPE_INVALID",
                message="entity_type must be module or subtask",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="--entity-type",
                value=entity_type,
            )
        )
    if diagnostics:
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    payload = preflight_open_window(
        state=str(state_path),
        history=str(history_path),
        entity_type=entity_type,
        entity_id=entity_id,
    )

    if not payload.get("ok", False):
        diagnostics = [
            _make_diagnostic(
                code="OPEN_WINDOW_PREFLIGHT_FAILED",
                message="preflight-open-window must pass before open-window apply",
                entity_type=entity_type or "system",
                entity_id=entity_id or "GLOBAL",
                field_path="preflight",
                value="preflight-open-window ok=false",
            )
        ]
        print(
            result_to_json(
                ok=False,
                diagnostics=diagnostics,
                mode=mode,
                preflight=payload,
            )
        )
        return 1

    target_scope = {
        "entity_type": entity_type,
        "entity_id": entity_id,
    }
    in_eligible = _is_entity_recorded(payload.get("eligible_entities", []), target_scope)
    in_blocked = _is_entity_recorded(payload.get("blocked_entities", []), target_scope)
    in_review_required = _is_entity_recorded(
        payload.get("review_required_before_open", []),
        target_scope,
    )

    if in_review_required:
        diagnostics.append(
            _make_diagnostic(
                code="OPEN_WINDOW_REVIEW_REQUIRED_UNCONFIRMED",
                message="review-required entity cannot apply open-window",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path="review_required_before_open",
                value=True,
            )
        )
    elif in_blocked:
        diagnostics.append(
            _make_diagnostic(
                code="OPEN_WINDOW_ENTITY_BLOCKED",
                message="target entity is blocked by preflight rules",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path="blocked_entities",
                value=True,
            )
        )
    elif not in_eligible:
        diagnostics.append(
            _make_diagnostic(
                code="OPEN_WINDOW_ENTITY_NOT_ELIGIBLE",
                message="target entity is not eligible for open-window",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path="eligible_entities",
                value=False,
            )
        )
    if diagnostics:
        print(
            result_to_json(
                ok=False,
                diagnostics=diagnostics,
                mode=mode,
                preflight=payload,
                would_apply=False,
            )
        )
        return 1

    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        diagnostics = [
            _make_diagnostic(
                code="OPEN_WINDOW_PYYAML_UNAVAILABLE",
                message="PyYAML is required for open-window",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path="dependency",
                value=str(exc),
            )
        ]
        print(
            result_to_json(
                ok=False,
                diagnostics=diagnostics,
                mode=mode,
                preflight=payload,
            )
        )
        return 1

    if not state_path.exists():
        diagnostics = [
            _make_diagnostic(
                code="OPEN_WINDOW_STATE_NOT_FOUND",
                message="official state file not found",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path="state",
                value=state_path.as_posix(),
            )
        ]
        print(
            result_to_json(
                ok=False,
                diagnostics=diagnostics,
                mode=mode,
                preflight=payload,
            )
        )
        return 1
    if not state_path.is_file():
        diagnostics = [
            _make_diagnostic(
                code="OPEN_WINDOW_STATE_NOT_FILE",
                message="state path is not a file",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path="state",
                value=state_path.as_posix(),
            )
        ]
        print(
            result_to_json(
                ok=False,
                diagnostics=diagnostics,
                mode=mode,
                preflight=payload,
            )
        )
        return 1

    state_text = state_path.read_text(encoding="utf-8")
    try:
        state = yaml.safe_load(state_text)
    except Exception as exc:  # noqa: BLE001
        diagnostics = [
            _make_diagnostic(
                code="OPEN_WINDOW_STATE_PARSE_ERROR",
                message=f"failed to parse official state: {exc}",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path="state",
                value=state_path.as_posix(),
            )
        ]
        print(
            result_to_json(
                ok=False,
                diagnostics=diagnostics,
                mode=mode,
                preflight=payload,
            )
        )
        return 1

    if not isinstance(state, dict):
        diagnostics = [
            _make_diagnostic(
                code="OPEN_WINDOW_STATE_FORMAT_ERROR",
                message="state must be a mapping",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path="state",
                value=type(state).__name__,
            )
        ]
        print(
            result_to_json(
                ok=False,
                diagnostics=diagnostics,
                mode=mode,
                preflight=payload,
            )
        )
        return 1

    before_window_state, entity_record = _extract_entity_window_state(
        state=state,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    if entity_record is None:
        diagnostics = [
            _make_diagnostic(
                code="OPEN_WINDOW_ENTITY_NOT_FOUND",
                message="entity not found in official state",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path="state",
                value=f"{entity_type}:{entity_id}",
            )
        ]
        print(
            result_to_json(
                ok=False,
                diagnostics=diagnostics,
                mode=mode,
                preflight=payload,
                would_apply=False,
            )
        )
        return 1

    if _as_str(before_window_state.get("window_status")) == WINDOW_STATUS_OPEN:
        diagnostics = [
            _make_diagnostic(
                code="WINDOW_ALREADY_OPEN",
                message="target entity already has window_status=open",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path="state.confirmed.window_status",
                value=WINDOW_STATUS_OPEN,
            )
        ]
        print(
            result_to_json(
                ok=False,
                diagnostics=diagnostics,
                mode=mode,
                preflight=payload,
                would_apply=False,
            )
        )
        return 1

    after_window_state = _build_window_target_state(actor=actor, reason=reason)
    changed_fields = [
        field
        for field in WINDOW_FIELDS
        if before_window_state.get(field) != after_window_state.get(field)
    ]

    if mode == "dry-run":
        print(
            result_to_json(
                ok=True,
                diagnostics=[],
                mode="dry-run",
                preflight=payload,
                entity_type=entity_type,
                entity_id=entity_id,
                would_apply=True,
                would_change=after_window_state,
                before_state=before_window_state,
                proposed_state=after_window_state,
                changed_fields=changed_fields,
                state_path=state_path.as_posix(),
                history_path=history_path.as_posix(),
            )
        )
        return 0

    transition_id = f"OPEN-WINDOW-{uuid.uuid4().hex}"
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    draft_state = copy.deepcopy(state)
    record = _ensure_entity_record(
        state=draft_state,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    if record is None:
        diagnostics = [
            _make_diagnostic(
                code="OPEN_WINDOW_ENTITY_MUTATION_TARGET_LOST",
                message="target entity unavailable during apply mutation",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path="state",
                value=f"{entity_type}:{entity_id}",
            )
        ]
        print(
            result_to_json(
                ok=False,
                diagnostics=diagnostics,
                mode="apply",
                preflight=payload,
            )
        )
        return 1

    if not isinstance(record.get("state"), dict):
        record["state"] = {}
    if not isinstance(record["state"].get("confirmed"), dict):
        record["state"]["confirmed"] = {}
    record["state"]["confirmed"].update(after_window_state)

    original_state_bytes = state_path.read_bytes()
    try:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = state_path.with_suffix(state_path.suffix + ".tmp")
        tmp_path.write_text(
            yaml.safe_dump(draft_state, allow_unicode=True, sort_keys=False, width=120),
            encoding="utf-8",
        )
        tmp_path.replace(state_path)
    except Exception as exc:  # noqa: BLE001
        diagnostics = [
            _make_diagnostic(
                code="OPEN_WINDOW_STATE_WRITE_FAILED",
                message=f"failed to write official state: {exc}",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=state_path.as_posix(),
                value=str(exc),
            )
        ]
        print(
            result_to_json(
                ok=False,
                diagnostics=diagnostics,
                mode="apply",
                preflight=payload,
                before_state=before_window_state,
                proposed_state=after_window_state,
            )
        )
        return 1

    history_record = {
        "transition_id": transition_id,
        "timestamp": timestamp,
        "actor": actor,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "mode": mode,
        "action": "open-window",
        "source": "preflight",
        "before_state": before_window_state,
        "applied_state": after_window_state,
        "changed_fields": changed_fields,
        "reason": reason,
    }

    history_written = _append_history(history_path, history_record)
    if not history_written:
        try:
            state_path.write_bytes(original_state_bytes)
        except Exception:
            pass
        diagnostics = [
            _make_diagnostic(
                code="OPEN_WINDOW_HISTORY_APPEND_FAILED",
                message="failed to append open-window transition history",
                entity_type=entity_type,
                entity_id=entity_id,
                field_path=history_path.as_posix(),
                value="append",
            )
        ]
        print(
            result_to_json(
                ok=False,
                diagnostics=diagnostics,
                mode="apply",
                preflight=payload,
                before_state=before_window_state,
                proposed_state=after_window_state,
            )
        )
        return 1

    print(
        result_to_json(
            ok=True,
            diagnostics=[],
            mode="apply",
            transition_id=transition_id,
            entity_type=entity_type,
            entity_id=entity_id,
            state_path=state_path.as_posix(),
            history_path=history_path.as_posix(),
            preflight=payload,
            before_state=before_window_state,
            applied_state=after_window_state,
            changed_fields=changed_fields,
        )
    )
    return 0


def _is_entity_recorded(
    entries: list[dict[str, Any]],
    target: dict[str, str | None],
) -> bool:
    for item in entries:
        if not isinstance(item, dict):
            continue
        if (
            _as_str(item.get("entity_type")) == target.get("entity_type")
            and _as_str(item.get("entity_id")) == target.get("entity_id")
        ):
            return True
    return False


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _extract_entity_window_state(
    *,
    state: dict[str, Any],
    entity_type: str,
    entity_id: str,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    entities = state.get("modules") if entity_type == "module" else state.get("subtasks")
    if not isinstance(entities, dict):
        return _default_window_state(), None

    raw_entity = entities.get(entity_id)
    if not isinstance(raw_entity, dict):
        return _default_window_state(), None
    state_obj = raw_entity.get("state")
    if not isinstance(state_obj, dict):
        return _default_window_state(), raw_entity

    confirmed = state_obj.get("confirmed")
    if not isinstance(confirmed, dict):
        return _default_window_state(), raw_entity

    return _coerce_window_state(confirmed), raw_entity


def _ensure_entity_record(
    *,
    state: dict[str, Any],
    entity_type: str,
    entity_id: str,
) -> dict[str, Any] | None:
    entities = state.get("modules") if entity_type == "module" else state.get("subtasks")
    if not isinstance(entities, dict):
        return None
    raw_entity = entities.get(entity_id)
    if not isinstance(raw_entity, dict):
        return None
    return raw_entity


def _coerce_window_state(confirmed: dict[str, Any]) -> dict[str, Any]:
    result = _default_window_state()
    for field in WINDOW_FIELDS:
        value = confirmed.get(field)
        if field == "window_status" and isinstance(value, str):
            result[field] = value
        elif field in {"window_opened_at", "window_opened_by", "window_reason"}:
            result[field] = value if isinstance(value, (str, type(None))) else str(value)
    return result


def _build_window_target_state(
    actor: str | None,
    reason: str | None,
) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "window_status": WINDOW_STATUS_OPEN,
        "window_opened_at": timestamp,
        "window_opened_by": str(actor).strip() if actor else None,
        "window_reason": str(reason).strip() if reason else None,
    }


def _append_history(path: Path, record: dict[str, Any]) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False
