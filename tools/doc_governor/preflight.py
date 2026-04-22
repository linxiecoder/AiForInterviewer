from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any
import json

from .evaluate import _evaluate_state_payload
from .history import DEFAULT_HISTORY_PATH, show_history
from .diagnostics import diagnostics_to_dicts
from .validate import validate_state_file
from .schema import OFFICIAL_STATE_PATH, OQ_POLICY_SOURCE_BOOTSTRAP_DEFAULT


ALLOWED_OPEN_READINESS = {"downstream_ready", "implementation_ready"}
HARD_READINESS_BLOCKERS = {"blocked", "not_ready"}


def preflight_open_window(
    *,
    state: str = OFFICIAL_STATE_PATH,
    evaluate_json: str | None = None,
    history: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> dict[str, Any]:
    state_path = Path(state).resolve()
    history_path = Path(
        DEFAULT_HISTORY_PATH if history is None else history,
    ).resolve()

    parse_errors: list[dict[str, Any]] = []

    official_state, state_errors = _load_official_state(state_path)
    parse_errors.extend(state_errors)
    state_ok = not _has_errors(state_errors)

    # evaluation payload
    evaluate_payload: dict[str, Any]
    evaluation_source = "json" if evaluate_json else "live-evaluate"
    evaluate_errors: list[dict[str, Any]] = []
    if evaluate_json:
        evaluate_payload, evaluate_errors, _ = _load_evaluate_json(
            Path(evaluate_json).resolve(),
        )
    else:
        evaluate_payload, evaluate_errors, evaluate_ok = _load_live_evaluate(state_path)

    parse_errors.extend(evaluate_errors)
    if evaluate_json:
        evaluate_ok = not _has_errors(evaluate_errors)

    if not state_ok:
        return {
            "ok": False,
            "state_path": state_path.as_posix(),
            "history_path": history_path.as_posix(),
            "evaluation_source": evaluation_source,
            "scope": {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "history": history_path.as_posix(),
            },
            "eligible_entities": [],
            "blocked_entities": [],
            "blocker_reasons": [],
            "missing_requirements": [],
            "review_required_before_open": [],
            "summary": {
                "entities_scanned": 0,
                "eligible_count": 0,
                "blocked_count": 0,
                "hard_blocked_count": 0,
                "review_required_unconfirmed_count": 0,
                "history_records": 0,
                "history_parse_error_count": 0,
                "evaluation_source": evaluation_source,
            },
            "parse_errors": parse_errors,
            "history_recent": [],
            "history_signals": {
                "history_recent_parse_error_count": 0,
            },
        }

    entities = _collect_official_entities(
        official_state,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    global_policy = (
        official_state.get("global_policy")
        if isinstance(official_state.get("global_policy"), dict)
        else {}
    )
    formal_window_open = bool(global_policy.get("formal_window_open", True))

    history_records, history_parse_errors = _collect_history_records(
        history_path=history_path,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=200,
    )
    parse_errors.extend(history_parse_errors)

    o = evaluate_payload if isinstance(evaluate_payload, dict) else {}
    oq_payload = o.get("oqs") if isinstance(o, dict) else {}
    if not isinstance(oq_payload, dict):
        oq_payload = {}
    oq_policy_source_map = _collect_oq_policy_sources(
        official_state.get("oqs", {}) if isinstance(official_state.get("oqs"), dict) else {},
    )

    eligible_entities: list[dict[str, Any]] = []
    blocked_entities: list[dict[str, Any]] = []
    blocker_reasons: list[dict[str, Any]] = []
    review_required_before_open: list[dict[str, Any]] = []
    missing_requirements: list[dict[str, Any]] = []

    history_signal_map = _build_history_signal_map(history_records)
    blocked_count = 0
    hard_blocked_count = 0

    for official in entities:
        ent_type = official["entity_type"]
        ent_id = official["entity_id"]
        key = f"{ent_type}::{ent_id}"

        derived = _get_derived(o, ent_type, ent_id)

        official_blockers = _build_official_blockers(
            official,
            entity_type=ent_type,
            entity_id=ent_id,
            formal_window_open=formal_window_open,
        )
        evaluate_blockers = _build_evaluate_blockers(
            ent_type=ent_type,
            ent_id=ent_id,
            derived=derived,
            oq_payload=oq_payload,
            oq_policy_source_map=oq_policy_source_map,
        )

        review_required_info = _build_review_required_info(official, derived)
        blockers = official_blockers + evaluate_blockers

        history = history_signal_map.get(key, {})
        history_count = history.get("history_count", 0)
        if history_count == 0:
            missing_requirements.append(
                {
                    "entity_type": ent_type,
                    "entity_id": ent_id,
                    "code": "history_absent",
                    "sources": ["history"],
                    "message": "no transition_history records for this entity",
                }
            )

        review_required_unconfirmed = review_required_info.get("unconfirmed", False)
        hard_blockers = [item for item in blockers if item.get("level") == "hard"]
        if review_required_unconfirmed:
            reason = review_required_info["reason"]
            reason["proximity"] = "near-open" if not hard_blockers else "blocked"
            review_required_before_open.append(
                {
                    "entity_type": ent_type,
                    "entity_id": ent_id,
                    "reason": reason,
                }
            )
            blockers.append(reason)

        hard_blockers = [item for item in blockers if item.get("level") == "hard"]
        all_sources = sorted(
            {
                src
                for item in blockers
                for src in item.get("sources", [])
            }
        )

        proximity = "openable" if not hard_blockers and not review_required_unconfirmed else (
            "near-open" if review_required_unconfirmed else "blocked"
        )

        blockers_simple = [_simplify_blocker(item) for item in blockers]

        history_recent_records = history.get("recent_records", [])
        history_reasons = _build_history_warning_reasons(
            ent_type=ent_type,
            ent_id=ent_id,
            recent_records=history_recent_records,
        )
        blockers_simple.extend(history_reasons)

        record: dict[str, Any] = {
            "entity_type": ent_type,
            "entity_id": ent_id,
            "proximity": proximity,
            "hard_blockers": [item for item in blockers_simple if item.get("level") == "hard"],
            "blockers": blockers_simple,
            "sources": all_sources,
            "history_recent": history_recent_records,
            "history_signals": history.get("signals", {}),
            "missing_requirements": [],
        }
        if history_count == 0:
            record["missing_requirements"] = [
                item for item in missing_requirements if item["entity_type"] == ent_type and item["entity_id"] == ent_id
            ]

        for item in blockers_simple:
            blocker_reasons.append(item)

        if review_required_unconfirmed:
            reason_item = _normalize_blocker_entry(review_required_info["reason"])
            if reason_item not in blocker_reasons:
                blocker_reasons.append(reason_item)

        if hard_blockers or review_required_unconfirmed:
            blocked_count += 1
            if hard_blockers:
                hard_blocked_count += 1
            blocked_entities.append(record)
            continue

        eligible_entities.append(record)

    if history_parse_errors:
        for item in history_parse_errors:
            parse_errors.append(item)

    history_recent = [
        {
            "transition_id": item.get("transition_id"),
            "timestamp": item.get("timestamp"),
            "entity_type": item.get("entity_type"),
            "entity_id": item.get("entity_id"),
            "result": item.get("result"),
            "actor": item.get("actor"),
        }
        for item in history_records[:10]
    ]

    history_signals = {
        "entity_counts": {
            key: value.get("history_count", 0)
            for key, value in history_signal_map.items()
        },
        "entity_last_result": {
            key: value.get("last_result")
            for key, value in history_signal_map.items()
        },
        "recent_reject_count": {
            key: value.get("signals", {}).get("rejected_count", 0)
            for key, value in history_signal_map.items()
        },
        "parse_errors": history_parse_errors,
        "history_absent": [item["entity_id"] for item in missing_requirements],
    }

    return {
        "ok": evaluate_ok,
        "state_path": state_path.as_posix(),
        "history_path": history_path.as_posix(),
        "evaluation_source": evaluation_source,
        "scope": {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "history": history_path.as_posix(),
        },
        "eligible_entities": eligible_entities,
        "blocked_entities": blocked_entities,
        "blocker_reasons": _dedupe_dicts(blocker_reasons),
        "missing_requirements": missing_requirements,
        "review_required_before_open": review_required_before_open,
        "summary": {
            "entities_scanned": len(entities),
            "eligible_count": len(eligible_entities),
            "blocked_count": blocked_count,
            "hard_blocked_count": hard_blocked_count,
            "review_required_unconfirmed_count": len(review_required_before_open),
            "history_records": len(history_records),
            "history_parse_error_count": len(history_parse_errors),
            "evaluation_source": evaluation_source,
        },
        "parse_errors": parse_errors,
        "history_recent": history_recent,
        "history_signals": history_signals,
    }


def _has_errors(raw_errors: list[dict[str, Any]]) -> bool:
    for item in raw_errors:
        if item.get("severity", "error") == "error":
            return True
    return False


def _load_official_state(state_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - dependency check
        return {
            "schema_version": 1,
            "global_policy": {},
            "oqs": {},
            "modules": {},
            "subtasks": {},
        }, [
            {
                "code": "PRE_FLIGHT_PYYAML_UNAVAILABLE",
                "severity": "error",
                "message": f"PyYAML required for preflight: {exc}",
                "path": state_path.as_posix(),
            }
        ]

    if not state_path.exists():
        return {}, [
            {
                "code": "PRE_FLIGHT_STATE_NOT_FOUND",
                "severity": "error",
                "message": f"official state not found: {state_path}",
                "path": state_path.as_posix(),
            }
        ]

    if not state_path.is_file():
        return {}, [
            {
                "code": "PRE_FLIGHT_STATE_NOT_FILE",
                "severity": "error",
                "message": "official state is not a file",
                "path": state_path.as_posix(),
            }
        ]

    try:
        payload = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {}, [
            {
                "code": "PRE_FLIGHT_STATE_PARSE_ERROR",
                "severity": "error",
                "message": f"failed to parse official state yaml: {exc}",
                "path": state_path.as_posix(),
            }
        ]

    if not isinstance(payload, dict):
        return {}, [
            {
                "code": "PRE_FLIGHT_STATE_TYPE_ERROR",
                "severity": "error",
                "message": "official state must be mapping",
                "path": state_path.as_posix(),
            }
        ]

    return payload, []


def _load_live_evaluate(state_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], bool]:
    diagnostics = validate_state_file(state_path)
    parse_errors = diagnostics_to_dicts(diagnostics)
    if not diagnostics:
        parse_errors = []

    for item in parse_errors:
        if item.get("code", "").startswith("RULE_") and item.get("severity") == "error":
            item["severity"] = "warning"

    has_fatal_state_error = any(
        (not str(item.get("code", "")).startswith("RULE_")) and item.get("severity") == "error"
        for item in parse_errors
    )
    if has_fatal_state_error:
        return {}, parse_errors, False

    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - dependency check
        return {}, [
            {
                "code": "PRE_FLIGHT_PYYAML_UNAVAILABLE",
                "severity": "error",
                "message": f"PyYAML required for preflight evaluate: {exc}",
                "path": state_path.as_posix(),
            }
        ], False

    try:
        payload = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {}, [
            {
                "code": "PRE_FLIGHT_STATE_PARSE_ERROR",
                "severity": "error",
                "message": f"failed to parse official state yaml: {exc}",
                "path": state_path.as_posix(),
            }
        ], False

    payload_map = payload if isinstance(payload, dict) else None
    if not isinstance(payload_map, dict):
        return {}, [
            {
                "code": "PRE_FLIGHT_STATE_TYPE_ERROR",
                "severity": "error",
                "message": "official state must be mapping",
                "path": state_path.as_posix(),
            }
        ], False

    return _evaluate_state_payload(payload_map), parse_errors, True


def _load_evaluate_json(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], bool]:
    if not path.exists():
        return {}, [
            {
                "code": "PRE_FLIGHT_EVALUATE_JSON_NOT_FOUND",
                "severity": "error",
                "message": f"evaluate-json not found: {path}",
                "path": path.as_posix(),
            }
        ], False

    if not path.is_file():
        return {}, [
            {
                "code": "PRE_FLIGHT_EVALUATE_JSON_NOT_FILE",
                "severity": "error",
                "message": "evaluate-json is not a file",
                "path": path.as_posix(),
            }
        ], False

    try:
        raw = path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        return {}, [
            {
                "code": "PRE_FLIGHT_EVALUATE_JSON_READ_ERROR",
                "severity": "error",
                "message": str(exc),
                "path": path.as_posix(),
            }
        ], False

    try:
        payload = json.loads(raw)
    except Exception as exc:  # noqa: BLE001
        return {}, [
            {
                "code": "PRE_FLIGHT_EVALUATE_JSON_INVALID",
                "severity": "error",
                "message": f"evaluate-json invalid json: {exc}",
                "path": path.as_posix(),
            }
        ], False

    if not isinstance(payload, dict):
        return {}, [
            {
                "code": "PRE_FLIGHT_EVALUATE_JSON_TYPE_ERROR",
                "severity": "error",
                "message": "evaluate-json must be object mapping",
                "path": path.as_posix(),
            }
        ], False

    return payload, [], True


def _collect_official_entities(
    state: dict[str, Any],
    *,
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> list[dict[str, Any]]:
    modules = state.get("modules", {}) if isinstance(state.get("modules"), dict) else {}
    subtasks = state.get("subtasks", {}) if isinstance(state.get("subtasks"), dict) else {}

    entities: list[dict[str, Any]] = []
    for e_type, records in (("module", modules), ("subtask", subtasks)):
        if entity_type is not None and entity_type != e_type:
            continue
        for id_, record in records.items():
            if not isinstance(record, dict):
                continue
            if entity_id is not None and id_ != entity_id:
                continue
            state_obj = record.get("state", {})
            confirmed = state_obj.get("confirmed", {}) if isinstance(state_obj, dict) else {}
            if not isinstance(confirmed, dict):
                confirmed = {}
            entities.append(
                {
                    "entity_type": e_type,
                    "entity_id": id_,
                    "confirmed": confirmed,
                    "record": record,
                }
            )
    return entities


def _collect_history_records(
    *,
    history_path: Path,
    entity_type: str | None,
    entity_id: str | None,
    limit: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    payload = show_history(
        history=str(history_path),
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
    )
    return payload.get("records", []), payload.get("parse_errors", [])


def _build_history_signal_map(
    records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    if not isinstance(records, list):
        return {}

    counters = Counter()
    rejected_count: Counter[str] = Counter()
    latest: dict[str, dict[str, Any]] = {}

    for record in records:
        ent_type = _as_str(record.get("entity_type"))
        ent_id = _as_str(record.get("entity_id"))
        if not ent_type or not ent_id:
            continue
        key = f"{ent_type}::{ent_id}"
        counters[key] += 1
        if _as_str(record.get("result")) == "rejected":
            rejected_count[key] += 1
        if key not in latest:
            latest[key] = {
                "transition_id": record.get("transition_id"),
                "timestamp": record.get("timestamp"),
                "result": record.get("result"),
                "actor": record.get("actor"),
            }

    signals: dict[str, dict[str, Any]] = {}
    for key, count in counters.items():
        ent_type, ent_id = key.split("::", 1)
        signals[key] = {
            "history_count": count,
            "recent_records": [
                item
                for item in records
                if f"{_as_str(item.get('entity_type'))}::{_as_str(item.get('entity_id'))}" == key
            ],
            "signals": {
                "rejected_count": rejected_count.get(key, 0),
                "last_result": latest.get(key, {}).get("result"),
            },
            "last_result": latest.get(key, {}).get("result"),
            "last_transition_id": latest.get(key, {}).get("transition_id"),
            "last_actor": latest.get(key, {}).get("actor"),
        }

    return signals


def _get_derived(
    payload: dict[str, Any],
    entity_type: str,
    entity_id: str,
) -> dict[str, Any]:
    container = payload.get("modules") if entity_type == "module" else payload.get("subtasks")
    if not isinstance(container, dict):
        return {}
    raw = container.get(entity_id)
    if not isinstance(raw, dict):
        return {}
    derived = raw.get("derived", {})
    return derived if isinstance(derived, dict) else {}


def _build_official_blockers(
    official: dict[str, Any],
    entity_type: str,
    entity_id: str,
    formal_window_open: bool,
) -> list[dict[str, Any]]:
    confirmed = official.get("confirmed", {}) if isinstance(official.get("confirmed"), dict) else {}
    readiness = _as_str(confirmed.get("readiness"))

    blockers: list[dict[str, Any]] = []
    if entity_type == "subtask" and not formal_window_open:
        blockers.append(
            _make_reason(
                code="formal_window_closed",
                reference=f"{entity_type}:{entity_id}.global_policy",
                level="hard",
                sources=["official_state", "rules"],
                message="formal window is closed and subtask cannot open",
            )
        )

    if readiness not in ALLOWED_OPEN_READINESS and readiness not in HARD_READINESS_BLOCKERS:
        blockers.append(
            _make_reason(
                code="official_readiness_unknown",
                reference=f"{entity_type}:{entity_id}.state.confirmed.readiness",
                level="hard",
                sources=["official_state", "rules"],
                message="official readiness is missing or unknown",
            )
        )
        return blockers

    if readiness in HARD_READINESS_BLOCKERS:
        blockers.append(
            _make_reason(
                code="official_readiness_blocked",
                reference=f"{entity_type}:{entity_id}.state.confirmed.readiness",
                level="hard",
                sources=["official_state", "rules"],
                message=f"official readiness blocks open-window: {readiness}",
            )
        )
    return blockers


def _build_evaluate_blockers(
    *,
    ent_type: str,
    ent_id: str,
    derived: dict[str, Any],
    oq_payload: dict[str, Any],
    oq_policy_source_map: dict[str, str],
) -> list[dict[str, Any]]:
    reasons: list[dict[str, Any]] = []
    candidate_refs = _coerce_str_list(derived.get("candidate_blocker_refs"))
    downstream_refs = _coerce_str_list(derived.get("downstream_blocker_refs"))
    impl_refs = _coerce_str_list(derived.get("implementation_blocker_refs"))
    oq_review_only_refs = _coerce_str_list(derived.get("oq_review_only_refs"))

    for ref in candidate_refs + downstream_refs + impl_refs:
        reason = _reason_from_blocker_ref(
            ref=ref,
            oq_payload=oq_payload,
            oq_policy_source_map=oq_policy_source_map,
        )
        if reason is not None:
            reasons.append(reason)

    for ref in oq_review_only_refs:
        reason = _reason_from_review_only_ref(
            ref=ref,
            oq_policy_source_map=oq_policy_source_map,
        )
        if reason is not None:
            reasons.append(reason)

    return reasons


def _build_review_required_info(
    official: dict[str, Any],
    derived: dict[str, Any],
) -> dict[str, Any]:
    confirmed = official.get("confirmed", {}) if isinstance(official.get("confirmed"), dict) else {}
    review_reasons = set(_coerce_str_list(derived.get("review_reasons")))
    oq_review_only_refs = _coerce_str_list(derived.get("oq_review_only_refs"))
    impl_activation = bool(derived.get("implementation_doc_activation_recommended"))
    review_required = bool(
        oq_review_only_refs
        or impl_activation
        or "oq_review_only" in review_reasons
        or "implementation_doc_activation_recommended" in review_reasons
    )
    review_status = _as_str(confirmed.get("review_status"))
    review_confirmed = review_status == "approved"

    reason: dict[str, Any] | None = None
    if review_required and not review_confirmed:
        ent_type = official["entity_type"]
        ent_id = official["entity_id"]
        reason = _make_reason(
            code="review_required_unconfirmed",
            reference=f"{ent_type}:{ent_id}.state.confirmed.review_status",
            level="soft",
            sources=["evaluate", "official_state", "rules"],
            message="review-required entity is not confirmed",
        )
        reason["review_status"] = review_status or "unreviewed"

    return {
        "required": review_required,
        "confirmed": review_confirmed,
        "unconfirmed": review_required and not review_confirmed,
        "reason": reason,
    }


def _has_hard_blocker(blockers: list[dict[str, Any]]) -> bool:
    return any(item.get("level") == "hard" for item in blockers)


def _reason_from_blocker_ref(
    ref: str,
    oq_payload: dict[str, Any],
    oq_policy_source_map: dict[str, str],
) -> dict[str, Any] | None:
    if not ref:
        return None

    if ref.startswith("oq:"):
        oq_id = ref.split(":", 1)[1]
        oq_info = oq_payload.get(oq_id, {}) if isinstance(oq_payload, dict) else {}
        reason_code = _as_str(oq_info.get("derived_reason_code"))
        if not reason_code:
            reason_code = "oq_blocker"

        source_is_bootstrap_default = (
            oq_policy_source_map.get(oq_id) == OQ_POLICY_SOURCE_BOOTSTRAP_DEFAULT
        )
        sources = ["evaluate", "oq"]
        if source_is_bootstrap_default:
            sources.append("bootstrap_default_oq_policy")

        return _make_reason(
            code=(
                "bootstrap_default_oq_policy_requires_confirmation"
                if source_is_bootstrap_default
                else reason_code
            ),
            reference=ref,
            level="hard",
            sources=sources,
            message=(
                f"bootstrap-default OQ {oq_id} requires explicit confirmation"
                if source_is_bootstrap_default
                else f"OQ blocker: {reason_code} from {oq_id}"
            ),
            extra={
                "oq_id": oq_id,
                "oq_reason_code": reason_code,
            },
        )

    if ref == "policy:formal_window_closed":
        return _make_reason(
            code="formal_window_closed",
            reference=ref,
            level="hard",
            sources=["evaluate", "rules"],
            message="formal_window_closed blocks candidate/open-window",
        )

    if ref.startswith("module:"):
        return _make_reason(
            code="upstream_module_not_ready",
            reference=ref,
            level="hard",
            sources=["evaluate", "rules"],
            message=f"upstream module not ready: {ref}",
        )

    if ref.startswith("gate:"):
        return _make_reason(
            code="implementation_doc_not_active" if "implementation_doc_not_active" in ref else "gate_policy_block",
            reference=ref,
            level="hard",
            sources=["evaluate", "rules"],
            message=f"gate blocker: {ref}",
        )

    if ref.startswith("doc:"):
        return _make_reason(
            code="missing_required_doc_slot",
            reference=ref,
            level="hard",
            sources=["evaluate", "rules"],
            message=f"doc blocker: {ref}",
        )

    if ref.startswith("legacy:"):
        return _make_reason(
            code="legacy_locked",
            reference=ref,
            level="hard",
            sources=["evaluate", "rules"],
            message="legacy lock blocks open-window",
        )

    return _make_reason(
        code="unknown_blocker",
        reference=ref,
        level="hard",
        sources=["evaluate", "rules"],
        message=f"unknown blocker reference: {ref}",
    )


def _reason_from_review_only_ref(
    *,
    ref: str,
    oq_policy_source_map: dict[str, str],
) -> dict[str, Any] | None:
    if not ref.startswith("oq:"):
        return None

    oq_id = ref.split(":", 1)[1]
    if not oq_id:
        return None

    if oq_policy_source_map.get(oq_id) != OQ_POLICY_SOURCE_BOOTSTRAP_DEFAULT:
        return None

    return _make_reason(
        code="bootstrap_default_oq_policy_requires_confirmation",
        reference=ref,
        level="hard",
        sources=["evaluate", "oq", "bootstrap_default_oq_policy", "rules"],
        message=(
            f"bootstrap-default OQ {oq_id} requires explicit confirmation and cannot directly open-window"
        ),
        extra={"oq_id": oq_id},
    )


def _build_history_warning_reasons(
    *,
    ent_type: str,
    ent_id: str,
    recent_records: list[Any],
) -> list[dict[str, Any]]:
    has_recent_reject = False
    has_recent_failed = False

    for item in recent_records[:10]:
        result = _as_str(item.get("result")) if isinstance(item, dict) else ""
        if result == "rejected":
            has_recent_reject = True
        elif result == "failed":
            has_recent_failed = True

    reasons: list[dict[str, Any]] = []
    if has_recent_reject:
        reasons.append(
            {
                "code": "history_recent_reject",
                "reference": f"{ent_type}:{ent_id}",
                "level": "soft",
                "severity": "soft",
                "sources": ["history"],
                "message": "Recent transition history contains a rejected attempt.",
                "extra": {"entity_type": ent_type, "entity_id": ent_id},
            }
        )

    if has_recent_failed:
        reasons.append(
            {
                "code": "history_recent_failed",
                "reference": f"{ent_type}:{ent_id}",
                "level": "soft",
                "severity": "soft",
                "sources": ["history"],
                "message": "Recent transition history contains a failed attempt.",
                "extra": {"entity_type": ent_type, "entity_id": ent_id},
            }
        )

    return reasons


def _collect_oq_policy_sources(raw_oq_state: dict[str, Any]) -> dict[str, str]:
    source_map: dict[str, str] = {}
    for oq_id, oq_info in raw_oq_state.items():
        if not isinstance(oq_info, dict):
            continue
        source = _as_str(oq_info.get("gate_policy_source"))
        if source:
            source_map[str(oq_id)] = source
    return source_map


def _make_reason(
    *,
    code: str,
    reference: str,
    level: str,
    sources: list[str],
    message: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "code": code,
        "reference": reference,
        "level": level,
        "sources": sorted(set(sources)),
        "message": message,
    }
    if extra:
        payload["extra"] = extra
    return payload


def _simplify_blocker(item: dict[str, Any] | None) -> dict[str, Any]:
    if item is None:
        return {}
    return {
        "code": item.get("code"),
        "reference": item.get("reference"),
        "level": item.get("level", "hard"),
        "severity": item.get("severity", item.get("level", "soft")),
        "sources": item.get("sources", []),
        "message": item.get("message", ""),
        "extra": item.get("extra"),
        "proximity": item.get("proximity"),
    }


def _normalize_blocker_entry(item: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {}
    return _simplify_blocker(item)


def _dedupe_dicts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in items:
        tuple_key = json.dumps(item, sort_keys=True, ensure_ascii=False, default=str)
        if tuple_key in seen:
            continue
        seen.add(tuple_key)
        deduped.append(item)

    return deduped


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _coerce_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        if isinstance(item, str):
            result.append(item)
    return result


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    return default
