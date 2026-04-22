from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.doc_governor.preflight import preflight_open_window  # type: ignore[import-not-found]
    from tools.doc_governor.schema import OFFICIAL_STATE_PATH
else:
    from .preflight import preflight_open_window
    from .schema import OFFICIAL_STATE_PATH


def plan_open_window(
    *,
    state: str = OFFICIAL_STATE_PATH,
    history: str = "docs/governance/transition_history.jsonl",
    evaluate_json: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    preflight_payload = preflight_open_window(
        state=state,
        evaluate_json=evaluate_json,
        history=history,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    if not isinstance(preflight_payload, dict):
        preflight_payload = {}

    parse_errors = _as_list(preflight_payload.get("parse_errors"))
    preflight_summary = _as_dict(preflight_payload.get("summary"))
    preflight_eligible = _dedupe_by_key(_as_list(preflight_payload.get("eligible_entities")))
    preflight_blocked = _dedupe_by_key(_as_list(preflight_payload.get("blocked_entities")))
    preflight_review_required = _dedupe_by_key(
        _as_list(preflight_payload.get("review_required_before_open")),
    )
    preflight_blocker_reasons = _dedupe_by_key(_as_list(preflight_payload.get("blocker_reasons")))
    preflight_missing_requirements = _as_list(preflight_payload.get("missing_requirements"))
    preflight_history_signals = _as_dict(preflight_payload.get("history_signals"))

    preflight_ok = bool(preflight_payload.get("ok", False))

    hard_blocked: list[dict[str, Any]] = []
    near_open_but_blocked: list[dict[str, Any]] = []

    review_required_keys = {_entity_key(item) for item in preflight_review_required}

    for item in preflight_blocked:
        if _is_hard_blocker(item):
            hard_blocked.append(item)
            continue
        if _entity_key(item) in review_required_keys or item.get("proximity") == "near-open":
            near_open_but_blocked.append(item)

    # Keep three buckets mutually exclusive.
    hard_keys = {_entity_key(item) for item in hard_blocked}
    near_open_but_blocked = [
        item for item in near_open_but_blocked if _entity_key(item) not in hard_keys
    ]

    eligible_to_apply = preflight_eligible
    eligible_keys = {_entity_key(item) for item in eligible_to_apply}
    hard_blocked = [item for item in hard_blocked if _entity_key(item) not in eligible_keys]
    near_open_but_blocked = [
        item for item in near_open_but_blocked if _entity_key(item) not in eligible_keys
    ]

    if limit is not None:
        eligible_to_apply = _apply_limit(eligible_to_apply, limit)
        near_open_but_blocked = _apply_limit(near_open_but_blocked, limit)
        hard_blocked = _apply_limit(hard_blocked, limit)

    would_change_by_entity = [
        {
            "entity_type": item.get("entity_type"),
            "entity_id": item.get("entity_id"),
            "window_status": "open",
            "window_opened_at": _now_utc_iso(),
            "window_opened_by": None,
            "window_reason": None,
        }
        for item in eligible_to_apply
    ]

    if limit is not None:
        would_change_by_entity = _apply_limit(would_change_by_entity, limit)

    return {
        "ok": preflight_ok,
        "state_path": _as_str(preflight_payload.get("state_path"), default=str(Path(state).resolve())),
        "history_path": _as_str(
            preflight_payload.get("history_path"),
            default=str(Path(history).resolve()),
        ),
        "evaluation_source": _as_str(preflight_payload.get("evaluation_source"), default="live-evaluate"),
        "scope": _as_dict(preflight_payload.get("scope")),
        "eligible_to_apply": eligible_to_apply,
        "near_open_but_blocked": near_open_but_blocked,
        "hard_blocked": hard_blocked,
        "blocker_reasons": preflight_blocker_reasons,
        "would_change_by_entity": would_change_by_entity,
        "summary": {
            "entities_scanned": preflight_summary.get("entities_scanned", len(eligible_to_apply) + len(near_open_but_blocked) + len(hard_blocked)),
            "eligible_to_apply_count": len(eligible_to_apply),
            "near_open_but_blocked_count": len(near_open_but_blocked),
            "hard_blocked_count": len(hard_blocked),
            "preflight_eligible_count": preflight_summary.get("eligible_count", 0),
            "preflight_blocked_count": preflight_summary.get("blocked_count", 0),
            "evaluation_source": _as_str(preflight_payload.get("evaluation_source"), default="live-evaluate"),
        },
        "missing_requirements": preflight_missing_requirements,
        "history_signals": preflight_history_signals,
        "parse_errors": parse_errors,
    }


def _entity_key(item: dict[str, Any]) -> str:
    return f"{item.get('entity_type')}::{item.get('entity_id')}"


def _is_hard_blocker(item: dict[str, Any]) -> bool:
    hard_blockers = item.get("hard_blockers", [])
    for blocker in _as_list(hard_blockers):
        if _as_str(blocker.get("level")).lower() == "hard":
            return True
    for blocker in _as_list(item.get("blockers")):
        if _as_str(blocker.get("level")).lower() == "hard":
            return True
    return False


def _dedupe_by_key(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        key = _entity_key(item)
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def _apply_limit(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if limit < 0:
        return items
    return items[:limit]


def _as_str(value: Any, *, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value
    return str(value)


def _as_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            result.append(item)
    return result


def _as_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return value


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
