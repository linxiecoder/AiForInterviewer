from __future__ import annotations

from typing import Any

from .diagnostics import Diagnostic, make_diagnostic, make_evidence

RENDER_OUTPUT_DIR_NAME = "DOC_GOVERNOR_REPORT.md"

GATE_COUNT_KEYS = [
    "observe_only.clear",
    "observe_only.review_only",
    "candidate_gate.clear",
    "candidate_gate.review_only",
    "candidate_gate.candidate_blocker",
    "readiness_gate.clear",
    "readiness_gate.review_only",
    "readiness_gate.readiness_blocker",
]


def render_from_payload(
    payload: dict[str, Any],
    *,
    render_input_invalid: bool,
    input_incomplete: bool,
    agenda_limit: int = 10,
) -> str:
    summary = _as_dict(payload.get("summary"))
    modules = _as_dict(payload.get("modules"))
    subtasks = _as_dict(payload.get("subtasks"))
    oqs = _as_dict(payload.get("oqs"))
    delta_summary = _as_dict(payload.get("delta_summary"))

    if not isinstance(payload.get("summary"), dict):
        input_incomplete = True
    if not isinstance(payload.get("modules"), dict):
        input_incomplete = True
    if not isinstance(payload.get("subtasks"), dict):
        input_incomplete = True
    if not isinstance(payload.get("oqs"), dict):
        input_incomplete = True

    notes = _build_notes(
        render_input_invalid=render_input_invalid,
        input_incomplete=input_incomplete,
    )
    lines: list[str] = ["# DOC_GOVERNOR_REPORT", ""]
    lines.extend(_render_summary(summary))
    lines.extend(_render_review_section(modules, section_type="modules"))
    lines.extend(_render_review_section(subtasks, section_type="subtasks"))
    lines.extend(_render_blocker_sections(modules=modules, subtasks=subtasks))
    lines.extend(_render_oq_summary(summary=summary, oqs=oqs))
    lines.extend(
        _render_next_round_agenda(
            modules=modules,
            subtasks=subtasks,
            oqs=oqs,
            agenda_limit=max(0, agenda_limit),
        )
    )
    lines.append("## Notes / interpretation boundary")
    lines.extend(f"- {line}" for line in notes)
    return "\n".join(lines).rstrip() + "\n"


def _build_notes(*, render_input_invalid: bool, input_incomplete: bool) -> list[str]:
    notes: list[str] = [
        "This is report-only derived output and does not represent confirmed governance state.",
        "This report is a read-only interpretation snapshot and is not the source of truth for DOC_STATE files.",
        "The report cannot be used as a direct readiness or auto-open-window signal.",
        "Do not use this file for state write-back and do not treat it as an execution trigger for confirm-transition.",
    ]
    if render_input_invalid:
        notes.append("render_input_invalid=1: input diagnostics contains error.")
    if input_incomplete:
        notes.append(
            "render_input_incomplete=1: required blocks summary/modules/subtasks/oqs were missing and rendered as empty."
        )
    return notes


def _render_summary(summary: dict[str, Any]) -> list[str]:
    lines = [
        "## Summary",
        "",
        f"- modules_review_required: {summary.get('modules_review_required', 0)}",
        f"- subtasks_review_required: {summary.get('subtasks_review_required', 0)}",
        f"- modules_blocked_count: {summary.get('modules_blocked_count', 0)}",
        f"- subtasks_blocked_count: {summary.get('subtasks_blocked_count', 0)}",
    ]

    blocked_by_reason_code = summary.get("blocked_by_reason_code")
    if isinstance(blocked_by_reason_code, dict) and blocked_by_reason_code:
        lines.append("- blocked_by_reason_code:")
        for reason, count in sorted(blocked_by_reason_code.items()):
            lines.append(f"  - {reason}: {count}")
    else:
        lines.append("- blocked_by_reason_code: {}")

    lines.append("- oq_gate_counts:")
    oq_gate_counts = _as_dict(summary.get("oq_gate_counts"))
    for key in GATE_COUNT_KEYS:
        lines.append(f"  - {key}: {oq_gate_counts.get(key, 0)}")
    return lines + [""]


def _render_review_section(entities: dict[str, Any], section_type: str) -> list[str]:
    title = (
        "Modules Requiring Review" if section_type == "modules" else "Subtasks Requiring Review"
    )
    lines = [f"## {title}", ""]
    rows: list[str] = []
    for entity_id in sorted(entities):
        entity = _as_dict(entities.get(entity_id, {}))
        derived = _as_dict(entity.get("derived"))
        if not derived.get("review_required"):
            continue
        reasons = ", ".join(str(item) for item in _as_list(derived.get("review_reasons")))
        rows.append(f"- `{entity_id}`: review_required=true reason=[{reasons}]")
    lines.extend(rows if rows else ["- none"])
    return lines + [""]


def _render_blocker_sections(
    *, modules: dict[str, Any], subtasks: dict[str, Any]
) -> list[str]:
    module_candidate = _get_blockers(
        entities=modules,
        entity_type="module",
        blocker_key="candidate_blockers",
    )
    subtask_candidate = _get_blockers(
        entities=subtasks,
        entity_type="subtask",
        blocker_key="candidate_blockers",
    )

    module_downstream = _get_blockers(
        entities=modules,
        entity_type="module",
        blocker_key="downstream_blockers",
    )
    subtask_downstream = _get_blockers(
        entities=subtasks,
        entity_type="subtask",
        blocker_key="downstream_blockers",
    )
    subtask_impl = _get_blockers(
        entities=subtasks,
        entity_type="subtask",
        blocker_key="implementation_blockers",
    )

    lines: list[str] = ["## Candidate blockers by layer", ""]
    lines.extend(["### Modules", ""])
    _append_blocker_lines(lines, module_candidate)
    lines.extend(["### Subtasks", ""])
    _append_blocker_lines(lines, subtask_candidate)

    lines.extend(["", "## Downstream blockers by layer", ""])
    lines.extend(["### Modules", ""])
    _append_blocker_lines(lines, module_downstream)
    lines.extend(["### Subtasks", ""])
    _append_blocker_lines(lines, subtask_downstream)

    lines.extend(["", "## Implementation blockers by layer", ""])
    lines.extend(["### Subtasks", ""])
    _append_blocker_lines(lines, subtask_impl)
    return lines + [""]


def _get_blockers(
    *,
    entities: dict[str, Any],
    entity_type: str,
    blocker_key: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entity_id in sorted(entities):
        entity = _as_dict(entities.get(entity_id, {}))
        derived = _as_dict(entity.get("derived"))
        for blocker in _as_list(derived.get(blocker_key)):
            if not isinstance(blocker, dict):
                continue
            rows.append(
                {
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "ref": str(blocker.get("ref", "")),
                    "kind": str(blocker.get("kind", "")),
                    "reason_code": str(blocker.get("reason_code", "")),
                    "message": str(blocker.get("message", "")),
                }
            )
    return sorted(
        rows,
        key=lambda item: (item["reason_code"], item["ref"], item["entity_type"], item["entity_id"]),
    )


def _append_blocker_lines(lines: list[str], blockers: list[dict[str, Any]]) -> None:
    if not blockers:
        lines.append("- none")
        return
    for blocker in blockers:
        lines.append(
            f"- [{blocker['entity_type']}:{blocker['entity_id']}] "
            f"reason_code={blocker['reason_code']} ref={blocker['ref']} "
            f"kind={blocker['kind']} message={blocker['message']}"
        )


def _render_oq_summary(*, summary: dict[str, Any], oqs: dict[str, Any]) -> list[str]:
    lines = ["## OQ gate summary", "", "### counts"]
    oq_gate_counts = _as_dict(summary.get("oq_gate_counts"))

    if not oq_gate_counts and not oqs:
        lines.append("- none")
        lines.append("")
        return lines

    for key in GATE_COUNT_KEYS:
        lines.append(f"- {key}: {oq_gate_counts.get(key, 0)}")
    return lines + [""]


def _render_next_round_agenda(
    *,
    modules: dict[str, Any],
    subtasks: dict[str, Any],
    oqs: dict[str, Any],
    agenda_limit: int,
) -> list[str]:
    lines = ["## Next Round Agenda", ""]
    agenda_items = _build_next_round_agenda(
        modules=modules,
        subtasks=subtasks,
        oqs=oqs,
        agenda_limit=agenda_limit,
    )
    if not agenda_items:
        lines.append("- none")
        return lines + [""]

    for idx, item in enumerate(agenda_items, start=1):
        lines.append(f"### Agenda {idx}: {item['category']}")
        lines.append(f"- entity: {item['entity']}")
        lines.append(f"- current_state: {item['current_state']}")
        lines.append(
            "- blocking_reason_codes: "
            + (", ".join(item["blocking_reason_codes"]) if item["blocking_reason_codes"] else "none")
        )
        lines.append(
            "- required_evidence: "
            + (", ".join(item["required_evidence"]) if item["required_evidence"] else "none")
        )
        lines.append(f"- suggested_owner: {item['suggested_owner']}")
        lines.append("")
    return lines


def _build_next_round_agenda(
    *,
    modules: dict[str, Any],
    subtasks: dict[str, Any],
    oqs: dict[str, Any],
    agenda_limit: int,
) -> list[dict[str, Any]]:
    agenda: list[dict[str, Any]] = []

    for oq_id in sorted(oqs):
        oq = _as_dict(oqs.get(oq_id))
        enforcement = str(oq.get("derived_enforcement", ""))
        reason_code = str(oq.get("derived_reason_code", ""))
        if enforcement not in {"candidate_blocker", "readiness_blocker"} and reason_code not in {
            "oq_candidate_gate",
            "oq_readiness_gate",
        }:
            continue
        agenda.append(
            {
                "category": "必须先决策的 OQ（candidate/readiness gate）",
                "entity": f"oq:{oq_id}",
                "current_state": (
                    f"status_class={str(oq.get('derived_status_class', 'unknown'))}, "
                    f"enforcement={enforcement or 'unknown'}"
                ),
                "blocking_reason_codes": [reason_code] if reason_code else [],
                "required_evidence": ["confirm OQ decision evidence (confirmed/manual override)"],
                "suggested_owner": "governance-owner",
            }
        )

    near_open_entities = _collect_entity_agenda(modules=modules, subtasks=subtasks, near_open_only=True)
    for item in near_open_entities:
        item["category"] = "review_required 的 near-open 实体"
        agenda.append(item)

    blocker_light_entities = _collect_entity_agenda(modules=modules, subtasks=subtasks, near_open_only=False)
    for item in blocker_light_entities:
        if item.get("_hard_blocker_count", 0) <= 0:
            continue
        item["category"] = "hard blocker 最少、最接近可推进的实体"
        agenda.append(item)

    if agenda_limit <= 0:
        return []
    return agenda[:agenda_limit]


def _collect_entity_agenda(
    *,
    modules: dict[str, Any],
    subtasks: dict[str, Any],
    near_open_only: bool,
) -> list[dict[str, Any]]:
    entities: list[dict[str, Any]] = []
    for entity_type, source in (("module", modules), ("subtask", subtasks)):
        for entity_id in sorted(source):
            entity = _as_dict(source.get(entity_id))
            derived = _as_dict(entity.get("derived"))
            review_required = bool(derived.get("review_required"))
            blocker_codes = _collect_blocker_reason_codes(derived)
            hard_blocker_count = len(blocker_codes)
            if near_open_only and (not review_required or hard_blocker_count != 0):
                continue
            entities.append(
                {
                    "entity": f"{entity_type}:{entity_id}",
                    "current_state": (
                        f"review_required={str(review_required).lower()}, "
                        f"hard_blocker_count={hard_blocker_count}"
                    ),
                    "blocking_reason_codes": blocker_codes,
                    "required_evidence": (
                        ["review confirmation evidence"]
                        if review_required
                        else ["resolve blocker evidence", "review confirmation evidence"]
                    ),
                    "suggested_owner": f"{entity_type}-owner",
                    "_hard_blocker_count": hard_blocker_count,
                    "_review_required": review_required,
                }
            )

    entities.sort(
        key=lambda item: (
            item["_hard_blocker_count"],
            0 if item["_review_required"] else 1,
            item["entity"],
        )
    )
    return entities


def _collect_blocker_reason_codes(derived: dict[str, Any]) -> list[str]:
    reason_codes: list[str] = []
    for blocker_key in ("candidate_blockers", "downstream_blockers", "implementation_blockers"):
        for blocker in _as_list(derived.get(blocker_key)):
            if not isinstance(blocker, dict):
                continue
            reason = str(blocker.get("reason_code", "")).strip()
            if reason:
                reason_codes.append(reason)
    return sorted(set(reason_codes))


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def build_render_diagnostics(
    path: Path,
    code: str,
    message: str,
    severity: str = "error",
) -> list[Diagnostic]:
    return [
        make_diagnostic(
            code=code,
            severity=severity,
            entity_type="render",
            entity_id="GLOBAL",
            field_path="render",
            message=message,
            evidence=[
                make_evidence(
                    type="file_scan",
                    path=path.as_posix(),
                    ref="render",
                    value=path.as_posix(),
                )
            ],
        )
    ]
