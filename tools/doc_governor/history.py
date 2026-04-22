from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json


DEFAULT_HISTORY_PATH = "docs/governance/transition_history.jsonl"

RESULT_CANONICAL_ALIASES = {
    "approved": "approved",
    "approve": "approved",
    "rejected": "rejected",
    "reject": "rejected",
    "blocked": "blocked",
    "failed": "failed",
    "dry-run": "blocked",
    "dryrun": "blocked",
}
KNOWN_RESULTS = frozenset({"approved", "rejected", "blocked", "failed"})


def resolve_history_counts() -> dict[str, int]:
    return {"approved": 0, "rejected": 0, "blocked": 0, "failed": 0}


def canonicalize_result(raw: str | None) -> str | None:
    if not isinstance(raw, str):
        return None
    return RESULT_CANONICAL_ALIASES.get(raw.strip().lower())


def parse_history_timestamp(raw: str | None) -> datetime | None:
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    cleaned = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(cleaned)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid timestamp: {raw}") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_history_timestamp_str(raw: str | None) -> datetime | None:
    if raw is None:
        return None
    return parse_history_timestamp(raw)


def as_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _parse_line(
    line: str,
    line_no: int,
    parse_errors: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not line.strip():
        return None
    try:
        parsed = json.loads(line)
    except json.JSONDecodeError as exc:
        parse_errors.append(
            {
                "line": line_no,
                "code": "HISTORY_RECORD_PARSE_ERROR",
                "message": f"invalid JSON line: {exc}",
                "value": line[:200],
            }
        )
        return None

    if not isinstance(parsed, dict):
        parse_errors.append(
            {
                "line": line_no,
                "code": "HISTORY_RECORD_INVALID",
                "message": "history record must be an object",
                "value": type(parsed).__name__,
            }
        )
        return None

    record = dict(parsed)
    timestamp_raw = as_str(record.get("timestamp"))
    if timestamp_raw is None:
        record["_parsed_timestamp"] = None
    else:
        try:
            record["_parsed_timestamp"] = parse_history_timestamp(timestamp_raw)
        except ValueError as exc:
            parse_errors.append(
                {
                    "line": line_no,
                    "code": "HISTORY_TIMESTAMP_INVALID",
                    "message": str(exc),
                    "value": timestamp_raw,
                }
            )
            record["_parsed_timestamp"] = None

    explicit = canonicalize_result(as_str(record.get("result")))
    if explicit is not None:
        record["result"] = explicit
        return record

    dry_run_value = record.get("dry_run")
    if isinstance(dry_run_value, bool) and dry_run_value:
        record["result"] = "blocked"
        return record

    changed_fields = record.get("changed_fields")
    if isinstance(changed_fields, list):
        record["result"] = "approved" if changed_fields else "rejected"
        return record

    parse_errors.append(
        {
            "line": line_no,
            "code": "HISTORY_RESULT_DERIVATION_FAILED",
            "message": "result cannot be derived",
            "value": "failed",
        }
    )
    record["result"] = "failed"
    return record


def _in_time_window(
    record: dict[str, Any],
    *,
    since: datetime | None,
    until: datetime | None,
    line_no: int,
    parse_errors: list[dict[str, Any]],
) -> bool:
    parsed_ts = record.get("_parsed_timestamp")
    if (since is not None or until is not None) and parsed_ts is None:
        parse_errors.append(
            {
                "line": line_no,
                "code": "HISTORY_RECORD_OUT_OF_WINDOW",
                "message": "timestamp missing or invalid for time-window filtering",
                "value": as_str(record.get("timestamp")),
            }
        )
        return False

    if since is not None and parsed_ts is not None and parsed_ts < since:
        return False
    if until is not None and parsed_ts is not None and parsed_ts >= until:
        return False
    return True


def _matches_filters(
    record: dict[str, Any],
    *,
    entity_type: str | None,
    entity_id: str | None,
    actor: str | None,
    result: str | None,
    since: datetime | None,
    until: datetime | None,
    line_no: int,
    parse_errors: list[dict[str, Any]],
) -> bool:
    if not _in_time_window(
        record,
        since=since,
        until=until,
        line_no=line_no,
        parse_errors=parse_errors,
    ):
        return False
    if entity_type and as_str(record.get("entity_type")) != entity_type:
        return False
    if entity_id and as_str(record.get("entity_id")) != entity_id:
        return False
    if actor and as_str(record.get("actor")) != actor:
        return False
    if result and as_str(record.get("result")) != result:
        return False
    return True


def _collect_records(
    history: str,
    *,
    entity_type: str | None = None,
    entity_id: str | None = None,
    actor: str | None = None,
    result: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    parse_errors: list[dict[str, Any]] = []
    path = Path(history)

    if not path.exists():
        return [], parse_errors
    if not path.is_file():
        parse_errors.append(
            {
                "line": 0,
                "code": "HISTORY_PATH_NOT_FILE",
                "message": "history path is not a file",
                "value": str(path),
            }
        )
        return [], parse_errors

    raw_records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            parsed = _parse_line(raw.strip(), line_no, parse_errors)
            if parsed is None:
                continue

            if _matches_filters(
                parsed,
                entity_type=entity_type,
                entity_id=entity_id,
                actor=actor,
                result=result,
                since=since,
                until=until,
                line_no=line_no,
                parse_errors=parse_errors,
            ):
                raw_records.append(parsed)

    raw_records.sort(
        key=lambda item: item.get("_parsed_timestamp") or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return raw_records, parse_errors


def _as_payload(record: dict[str, Any]) -> dict[str, Any]:
    payload = dict(record)
    payload.pop("_parsed_timestamp", None)
    return payload


def show_history(
    *,
    history: str = DEFAULT_HISTORY_PATH,
    entity_type: str | None = None,
    entity_id: str | None = None,
    actor: str | None = None,
    result: str | None = None,
    limit: int = 50,
    since: datetime | None = None,
    until: datetime | None = None,
) -> dict[str, Any]:
    normalized_result = canonicalize_result(result)
    path = Path(history).resolve()
    records, parse_errors = _collect_records(
        str(path),
        entity_type=entity_type,
        entity_id=entity_id,
        actor=actor,
        result=normalized_result,
        since=since,
        until=until,
    )

    counts = resolve_history_counts()
    for record in records:
        result_value = canonicalize_result(as_str(record.get("result")))
        if result_value is None:
            continue
        counts[result_value] += 1

    limited = records[:max(0, int(limit))]
    return {
        "ok": True,
        "filters": {
            "history": str(path),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "actor": actor,
            "result": normalized_result,
            "since": since.isoformat() if since else None,
            "until": until.isoformat() if until else None,
        },
        "counts": counts,
        "parse_errors": parse_errors,
        "records": [_as_payload(record) for record in limited],
        "total_matched": len(records),
        "returned": len(limited),
        "limit": max(0, int(limit)),
    }


def summarize_history(
    *,
    history: str = DEFAULT_HISTORY_PATH,
    entity_type: str | None = None,
    entity_id: str | None = None,
    actor: str | None = None,
    result: str | None = None,
    limit: int = 20,
    since: datetime | None = None,
    until: datetime | None = None,
    top_rejected: int = 10,
) -> dict[str, Any]:
    normalized_result = canonicalize_result(result)
    path = Path(history).resolve()
    records, parse_errors = _collect_records(
        str(path),
        entity_type=entity_type,
        entity_id=entity_id,
        actor=actor,
        result=normalized_result,
        since=since,
        until=until,
    )

    counts = resolve_history_counts()
    for record in records:
        result_value = canonicalize_result(as_str(record.get("result")))
        if result_value is None:
            continue
        counts[result_value] += 1

    latest_attempt_by_entity: list[dict[str, Any]] = []
    latest_map: dict[str, dict[str, Any]] = {}
    for record in records:
        key = f"{as_str(record.get('entity_type'))}::{as_str(record.get('entity_id'))}"
        if key not in latest_map:
            latest_map[key] = {
                "entity_type": as_str(record.get("entity_type")),
                "entity_id": as_str(record.get("entity_id")),
                "timestamp": as_str(record.get("timestamp")),
                "result": as_str(record.get("result")),
                "transition_id": as_str(record.get("transition_id")),
                "actor": as_str(record.get("actor")),
                "mode": as_str(record.get("mode")),
                "dry_run": record.get("dry_run"),
            }

    for key in sorted(latest_map):
        latest_attempt_by_entity.append(latest_map[key])

    rejected_count_by_entity: dict[str, int] = {}
    for record in records:
        if as_str(record.get("result")) != "rejected":
            continue
        ent_key = f"{as_str(record.get('entity_type'))}::{as_str(record.get('entity_id'))}"
        rejected_count_by_entity[ent_key] = rejected_count_by_entity.get(ent_key, 0) + 1

    top_rejected_entities = []
    max_rejected = max(0, int(top_rejected))
    for key, count in sorted(
        rejected_count_by_entity.items(),
        key=lambda item: (item[1], item[0]),
        reverse=True,
    )[:max_rejected]:
        ent_type, ent_id = key.split("::", 1)
        top_rejected_entities.append(
            {
                "entity_type": ent_type,
                "entity_id": ent_id,
                "rejected_count": count,
            }
        )

    recent_records = records[: max(0, int(limit))]
    return {
        "ok": True,
        "window": {
            "history": str(path),
            "since": since.isoformat() if since else None,
            "until": until.isoformat() if until else None,
        },
        "scope": {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "actor": actor,
            "result": normalized_result,
        },
        "counts": counts,
        "latest_attempt_by_entity": latest_attempt_by_entity,
        "top_rejected_entities": top_rejected_entities,
        "recent_records": [_as_payload(record) for record in recent_records],
        "parse_errors": parse_errors,
    }
