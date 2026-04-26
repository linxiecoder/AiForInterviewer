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
from .task_state_dependency_map import build_task_state_dependency_map
from .task_window_bridge import build_task_window_bridge


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

    bridge_payload: dict[str, Any] = {
        "summary": {"selected_task_count": 0, "candidate_task_count": 0, "deferred_task_count": 0},
        "candidate_tasks_after_state_activation": [],
        "blocked_before_open_window": [],
        "task_examples": [],
        "prerequisites": [],
    }
    dependency_map_payload: dict[str, Any] = {
        "summary": {"selected_task_count": 0},
        "tasks": [],
    }
    bridge_by_task: dict[str, dict[str, Any]] = {}
    dependency_by_task: dict[str, dict[str, Any]] = {}
    if entity_type in {None, "subtask"}:
        subtask_ids = [
            str(item.get("entity_id", "")).strip()
            for item in entities
            if item.get("entity_type") == "subtask" and item.get("entity_id")
        ]
        if subtask_ids:
            bridge_payload = build_task_window_bridge(
                state_path=state_path,
                evaluate_payload=o,
                entity_ids=subtask_ids,
            )
            dependency_map_payload = build_task_state_dependency_map(
                state_path=state_path,
                evaluate_payload=o,
                entity_ids=subtask_ids,
            )
            bridge_by_task = _index_task_bridge_payload(bridge_payload)
            dependency_by_task = _index_by_task_id(
                dependency_map_payload.get("tasks", []),
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

        task_bridge_info: dict[str, Any] | None = None
        if ent_type == "subtask":
            bridge_item = bridge_by_task.get(ent_id, {})
            dependency_item = dependency_by_task.get(ent_id, {})
            task_bridge_info = {
                "classification": _as_str(bridge_item.get("classification")),
                "reason": _as_str(bridge_item.get("reason")),
                "dependency_stage": _as_str(dependency_item.get("dependency_stage")),
                "current_effective_blockers": _coerce_str_list(
                    bridge_item.get("current_effective_blockers")
                ),
                "predicted_post_activation_blockers": _coerce_str_list(
                    bridge_item.get("predicted_post_activation_blockers")
                ),
                "content_blockers": _coerce_str_list(bridge_item.get("content_blockers")),
                "module_level_blockers": _coerce_str_list(
                    bridge_item.get("module_level_blockers")
                ),
                "manual_fill_fields": _coerce_str_list(bridge_item.get("manual_fill_fields")),
            }
            bridge_reason = _build_task_bridge_reason(
                entity_id=ent_id,
                formal_window_open=formal_window_open,
                bridge_item=bridge_item,
                dependency_item=dependency_item,
            )
            if bridge_reason is not None:
                blockers.append(bridge_reason)

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
        if task_bridge_info is not None:
            record["task_candidate_bridge"] = task_bridge_info
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

    payload = {
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
        "task_candidate_bridge": {
            "summary": bridge_payload.get("summary", {}),
            "candidate_tasks": bridge_payload.get("candidate_tasks_after_state_activation", []),
            "deferred_tasks": bridge_payload.get("blocked_before_open_window", []),
            "dependency_summary": dependency_map_payload.get("summary", {}),
        },
        "parse_errors": parse_errors,
        "history_recent": history_recent,
        "history_signals": history_signals,
    }
    if entity_type == "subtask" and entity_id:
        payload.update(
            _build_subtask_gate_summary(
                subtask_id=entity_id,
                official_state=official_state,
                evaluate_payload=o,
                formal_window_open=formal_window_open,
                eligible_entities=eligible_entities,
                blocked_entities=blocked_entities,
            )
        )
    return payload


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

    return _evaluate_state_payload(payload_map, state_path=state_path), parse_errors, True


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


def _build_subtask_gate_summary(
    *,
    subtask_id: str,
    official_state: dict[str, Any],
    evaluate_payload: dict[str, Any],
    formal_window_open: bool,
    eligible_entities: list[dict[str, Any]],
    blocked_entities: list[dict[str, Any]],
) -> dict[str, Any]:
    subtasks = _coerce_dict(official_state.get("subtasks"))
    subtask = _coerce_dict(subtasks.get(subtask_id))
    facts = _coerce_dict(subtask.get("facts"))
    state_obj = _coerce_dict(subtask.get("state"))
    confirmed = _coerce_dict(state_obj.get("confirmed"))
    derived = _get_derived(evaluate_payload, "subtask", subtask_id)
    packet_inputs = _coerce_dict(derived.get("implementation_packet_inputs"))

    target_record = _find_entity_record(
        entity_id=subtask_id,
        eligible_entities=eligible_entities,
        blocked_entities=blocked_entities,
    )
    blockers = list(target_record.get("blockers", [])) if target_record else []
    hard_blockers = [item for item in blockers if item.get("level") == "hard"]

    design_doc = _doc_slot_gate_summary("design_doc", facts.get("design_doc"))
    implementation_doc = _doc_slot_gate_summary(
        "implementation_doc",
        facts.get("implementation_doc"),
    )
    implementation_doc["state"] = _as_str(confirmed.get("implementation_doc_state"))

    acceptance_criteria = _coerce_str_list(packet_inputs.get("acceptance_criteria"))
    required_tests = _coerce_str_list(packet_inputs.get("required_tests"))
    goal = _as_str(packet_inputs.get("goal"))
    allowed_modify_paths = _coerce_str_list(packet_inputs.get("allowed_modify_paths"))
    forbidden_paths = _coerce_str_list(packet_inputs.get("forbidden_paths"))

    implementation_scope = {
        "clear": bool(goal and allowed_modify_paths and forbidden_paths),
        "goal_present": bool(goal),
        "allowed_modify_paths_present": bool(allowed_modify_paths),
        "forbidden_paths_present": bool(forbidden_paths),
        "goal": goal,
        "allowed_modify_paths": allowed_modify_paths,
        "forbidden_paths": forbidden_paths,
    }
    required_doc_slots = {
        "all_present": bool(design_doc["exists"] and implementation_doc["exists"]),
        "all_non_template": bool(
            design_doc["exists"]
            and implementation_doc["exists"]
            and not design_doc["template_like"]
            and not implementation_doc["template_like"]
        ),
        "necessary_not_sufficient": True,
        "slots": {
            "design_doc": design_doc,
            "implementation_doc": implementation_doc,
        },
        "message": (
            "required doc slot present is necessary but not sufficient for formal window "
            "or implementation-ready"
        ),
    }

    no_hard_blockers = not hard_blockers
    packet_inputs_complete = bool(
        required_doc_slots["all_non_template"]
        and implementation_doc["state"] == "active_working_doc"
        and implementation_scope["clear"]
        and acceptance_criteria
        and required_tests
    )
    can_generate_packet = bool(formal_window_open and no_hard_blockers and packet_inputs_complete)
    can_mark_ready = can_generate_packet
    can_open_formal_window = bool(no_hard_blockers)

    candidate = {
        "candidate_status": _as_str(confirmed.get("candidate_status")) or "none",
        "review_status": _as_str(confirmed.get("review_status")),
        "formal_window_candidate_recommended": bool(
            facts.get("formal_window_candidate_recommended", False)
        ),
        "source": _as_str(facts.get("formal_window_candidate_source")),
        "review_status_from_facts": _as_str(
            facts.get("formal_window_candidate_review_status")
        ),
        "state": _as_str(facts.get("formal_window_candidate_state"))
        or (
            "document_layer_recommended"
            if facts.get("formal_window_candidate_recommended")
            else "none"
        ),
        "notes": _as_str(facts.get("formal_window_candidate_notes")),
        "formal_window_candidate_is_open": False,
        "implementation_ready": False,
        "packet_ready": False,
    }

    near_ready = {
        "enabled": bool(facts.get("near_ready_for_formal_window_candidate", False)),
        "reason": _as_str(facts.get("near_ready_reason")),
        "blockers": _coerce_str_list(facts.get("near_ready_blockers")),
        "state": _as_str(facts.get("near_ready_state"))
        or (
            "document_layer_only"
            if facts.get("near_ready_for_formal_window_candidate")
            else "none"
        ),
        "candidate_status_candidate": False,
        "downstream_ready": False,
    }

    return {
        "subtask_id": subtask_id,
        "gate_result": "pass" if can_open_formal_window else "blocked",
        "can_open_formal_window": can_open_formal_window,
        "can_generate_implementation_packet": can_generate_packet,
        "can_mark_implementation_ready": can_mark_ready,
        "required_doc_slots": required_doc_slots,
        "design_doc": design_doc,
        "implementation_doc": implementation_doc,
        "acceptance_criteria": {
            "present": bool(acceptance_criteria),
            "count": len(acceptance_criteria),
            "items": acceptance_criteria,
        },
        "required_tests": {
            "present": bool(required_tests),
            "count": len(required_tests),
            "items": required_tests,
        },
        "implementation_scope": implementation_scope,
        "formal_window_open": formal_window_open,
        "candidate": candidate,
        "near_ready": near_ready,
        "blockers": blockers,
        "next_required_actions": _build_next_required_actions(
            blockers=blockers,
            formal_window_open=formal_window_open,
            implementation_doc=implementation_doc,
            acceptance_criteria=acceptance_criteria,
            required_tests=required_tests,
            implementation_scope=implementation_scope,
        ),
    }


def _find_entity_record(
    *,
    entity_id: str,
    eligible_entities: list[dict[str, Any]],
    blocked_entities: list[dict[str, Any]],
) -> dict[str, Any] | None:
    for record in blocked_entities + eligible_entities:
        if record.get("entity_type") == "subtask" and record.get("entity_id") == entity_id:
            return record
    return None


def _doc_slot_gate_summary(slot_name: str, raw_slot: object) -> dict[str, Any]:
    slot = _coerce_dict(raw_slot)
    return {
        "slot": slot_name,
        "exists": bool(slot.get("exists", False)),
        "template_like": bool(slot.get("template_like", False)),
        "present_non_template": bool(
            slot.get("exists", False) and not slot.get("template_like", False)
        ),
        "necessary_not_sufficient": True,
        "message": (
            f"{slot_name} exists=true is necessary but not sufficient for formal window "
            "or implementation-ready"
        ),
    }


def _build_next_required_actions(
    *,
    blockers: list[dict[str, Any]],
    formal_window_open: bool,
    implementation_doc: dict[str, Any],
    acceptance_criteria: list[str],
    required_tests: list[str],
    implementation_scope: dict[str, Any],
) -> list[str]:
    actions: list[str] = []
    blocker_codes = {str(item.get("code", "")) for item in blockers}
    if not formal_window_open or "formal_window_closed" in blocker_codes:
        actions.append("confirm and open the formal window before any implementation packet")
    if not implementation_doc.get("exists") or implementation_doc.get("template_like"):
        actions.append("create a non-template implementation_doc slot")
    if implementation_doc.get("state") != "active_working_doc":
        actions.append("activate implementation_doc_state only after review confirmation")
    if not acceptance_criteria:
        actions.append("add acceptance criteria before marking implementation-ready")
    if not required_tests:
        actions.append("add required tests before marking implementation-ready")
    if not implementation_scope.get("clear"):
        actions.append("clarify goal, allowed_modify_paths, and forbidden_paths")
    if not actions:
        actions.append("preflight is clear; use the formal confirmation workflow for any state change")
    return actions


def _coerce_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


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
            message=(
                "formal_window_open=false prevents implementation packet generation, "
                "implementation-ready, and formal-window progression"
            ),
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
        gate_code = ref.split(":", 1)[1]
        messages = {
            "implementation_doc_not_active": (
                "IMPLEMENTATION document exists does not imply implementation-ready or "
                "packet-ready; implementation_doc_state must be active_working_doc"
            ),
            "acceptance_criteria_missing": (
                "acceptance criteria missing prevents implementation-ready and packet generation"
            ),
            "required_tests_missing": (
                "required tests missing prevents implementation-ready and packet generation"
            ),
            "implementation_scope_unclear": (
                "implementation scope is unclear; goal, allowed paths, and forbidden paths "
                "must be explicit before implementation-ready"
            ),
            "requirement_id_unresolved": "unique requirement_id is required before packet generation",
        }
        return _make_reason(
            code=gate_code or "gate_policy_block",
            reference=ref,
            level="hard",
            sources=["evaluate", "rules"],
            message=messages.get(gate_code, f"gate blocker: {ref}"),
        )

    if ref.startswith("doc:"):
        return _make_reason(
            code="missing_required_doc_slot",
            reference=ref,
            level="hard",
            sources=["evaluate", "rules"],
            message=(
                f"required doc slot present is necessary but not sufficient; doc blocker: {ref}"
            ),
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


def _index_by_task_id(items: Any) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    if not isinstance(items, list):
        return indexed
    for item in items:
        if not isinstance(item, dict):
            continue
        task_id = _as_str(item.get("task_id")).strip()
        if task_id:
            indexed[task_id] = item
    return indexed


def _index_task_bridge_payload(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    indexed = _index_by_task_id(payload.get("task_examples", []))
    candidate_items = _index_by_task_id(payload.get("candidate_tasks_after_state_activation", []))
    deferred_items = _index_by_task_id(payload.get("blocked_before_open_window", []))
    prerequisite_items = _index_by_task_id(payload.get("prerequisites", []))
    for task_id, item in candidate_items.items():
        indexed.setdefault(task_id, {}).update(item)
    for task_id, item in deferred_items.items():
        indexed.setdefault(task_id, {}).update(item)
    for task_id, item in prerequisite_items.items():
        indexed.setdefault(task_id, {}).update(item)
    return indexed


def _build_task_bridge_reason(
    *,
    entity_id: str,
    formal_window_open: bool,
    bridge_item: dict[str, Any],
    dependency_item: dict[str, Any],
) -> dict[str, Any] | None:
    if not formal_window_open:
        return None

    classification = _as_str(bridge_item.get("classification"))
    dependency_stage = _as_str(dependency_item.get("dependency_stage"))
    if (
        classification == "ready_for_preflight_open_window"
        and dependency_stage == "ready_for_preflight_open_window"
    ):
        return None

    reason = _as_str(bridge_item.get("reason")) or "task bridge still does not place this task in preflight candidate pool"
    return _make_reason(
        code="task_not_in_open_window_candidate_pool",
        reference=f"subtask:{entity_id}.task_window_bridge",
        level="hard",
        sources=["task_window_bridge", "task_state_dependency_map"],
        message=reason,
        extra={
            "classification": classification or "unknown",
            "dependency_stage": dependency_stage or "unknown",
        },
    )


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
