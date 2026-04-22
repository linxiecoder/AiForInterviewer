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
    lines.extend(_render_round_delta(delta_summary))
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


def _render_round_delta(delta_summary: dict[str, Any]) -> list[str]:
    lines = ["## Round Delta", ""]
    if not delta_summary:
        lines.append("- none")
        return lines + [""]

    blocker_changes = _as_dict(delta_summary.get("blocker_changes"))
    lines.append("### Blocker changes")
    lines.append(f"- added_count: {blocker_changes.get('added_count', 0)}")
    lines.append(f"- closed_count: {blocker_changes.get('closed_count', 0)}")

    lines.append("")
    lines.append("### Review required changes")
    lines.extend(
        _render_delta_boolean(
            label="modules",
            payload=_as_dict(_as_dict(delta_summary.get("review_required_changes")).get("modules")),
        )
    )
    lines.extend(
        _render_delta_boolean(
            label="subtasks",
            payload=_as_dict(_as_dict(delta_summary.get("review_required_changes")).get("subtasks")),
        )
    )

    lines.append("")
    lines.append("### Readiness changes")
    lines.extend(
        _render_delta_boolean(
            label="modules_downstream",
            payload=_as_dict(_as_dict(delta_summary.get("readiness_changes")).get("modules_downstream")),
        )
    )
    lines.extend(
        _render_delta_boolean(
            label="subtasks_downstream",
            payload=_as_dict(_as_dict(delta_summary.get("readiness_changes")).get("subtasks_downstream")),
        )
    )
    lines.extend(
        _render_delta_boolean(
            label="subtasks_implementation",
            payload=_as_dict(_as_dict(delta_summary.get("readiness_changes")).get("subtasks_implementation")),
        )
    )
    return lines + [""]


def _render_delta_boolean(*, label: str, payload: dict[str, Any]) -> list[str]:
    if not payload:
        return [f"- {label}: before=0 after=0 delta=0"]
    return [
        f"- {label}: before={payload.get('before_true_count', 0)} after={payload.get('after_true_count', 0)} delta={payload.get('delta_true_count', 0)}",
        f"  - changed_to_true: {len(_as_list(payload.get('changed_to_true')))}",
        f"  - changed_to_false: {len(_as_list(payload.get('changed_to_false')))}",
    ]


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
