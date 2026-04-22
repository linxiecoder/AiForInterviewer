from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .governance_rounds import register_round_from_plan
from .window_plan import plan_open_window

DECISION_SUMMARY_ANCHOR = "Decision:"


def generate_round_template(
    *,
    round_id: str,
    state: str,
    history: str,
    evaluate_json: str | None,
    entity_type: str | None,
    entity_id: str | None,
    limit: int | None,
    plan_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_round_id = (round_id or "").strip()
    if not normalized_round_id:
        return {
            "ok": False,
            "diagnostics": [
                {
                    "code": "ROUND_TEMPLATE_ROUND_ID_REQUIRED",
                    "severity": "error",
                    "message": "round-id is required",
                    "field_path": "--round-id",
                }
            ],
        }

    if plan_payload is None:
        legacy_plan = plan_open_window(
            state=state,
            history=history,
            evaluate_json=evaluate_json,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
        )
        near_open_but_blocked = _as_entity_list(legacy_plan.get("near_open_but_blocked"))
        hard_blocked = _as_entity_list(legacy_plan.get("hard_blocked"))
        plan_payload = {
            "ok": bool(legacy_plan.get("ok", False)),
            "workflow": "open_window_review",
            "round_id": normalized_round_id,
            "topic": "open-window review",
            "scope": str(legacy_plan.get("scope", {})),
            "target_documents": [],
            "required_evidence_refs": [],
            "exit_criteria": ["round notes captured"],
            "writeback_items": [],
            "legacy_near_open_but_blocked": near_open_but_blocked,
            "legacy_hard_blocked": hard_blocked,
            "summary": legacy_plan.get("summary", {}),
            "parse_errors": legacy_plan.get("parse_errors", []),
        }
    else:
        near_open_but_blocked = _as_entity_list(plan_payload.get("legacy_near_open_but_blocked"))
        hard_blocked = _as_entity_list(plan_payload.get("legacy_hard_blocked"))

    output_path = Path("docs/governance/rounds") / f"{normalized_round_id}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        _build_round_template(
            round_id=normalized_round_id,
            plan_payload=plan_payload,
            near_open_but_blocked=near_open_but_blocked,
            hard_blocked=hard_blocked,
        ),
        encoding="utf-8",
    )

    registered_round = register_round_from_plan(
        state_path=state,
        plan_payload=plan_payload,
        round_id=normalized_round_id,
    )

    return {
        "ok": bool(plan_payload.get("ok", False)),
        "round_id": normalized_round_id,
        "output_path": output_path.as_posix(),
        "decision_anchor": DECISION_SUMMARY_ANCHOR,
        "target_documents": plan_payload.get("target_documents", []),
        "required_evidence_refs": plan_payload.get("required_evidence_refs", []),
        "writeback_items": plan_payload.get("writeback_items", []),
        "near_open_but_blocked": near_open_but_blocked,
        "hard_blocked": hard_blocked,
        "near_open_but_blocked_count": len(near_open_but_blocked),
        "hard_blocked_count": len(hard_blocked),
        "summary": plan_payload.get("summary", {}),
        "parse_errors": plan_payload.get("parse_errors", []),
        "registered_round": registered_round,
    }


def load_round_decision_anchor(*, round_id: str, rounds_root: str = "docs/governance/rounds") -> str | None:
    round_path = Path(rounds_root) / f"{round_id}.md"
    if not round_path.exists():
        return None
    text = round_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(DECISION_SUMMARY_ANCHOR):
            return DECISION_SUMMARY_ANCHOR
    return DECISION_SUMMARY_ANCHOR


def _build_round_template(
    *,
    round_id: str,
    plan_payload: dict[str, Any],
    near_open_but_blocked: list[dict[str, Any]],
    hard_blocked: list[dict[str, Any]],
) -> str:
    lines: list[str] = [
        f"# Discussion Round {round_id}",
        "",
        "## 最小输入字段",
        f"- round_goal: {plan_payload.get('topic', '')}",
        f"- entities_in_scope: {plan_payload.get('scope', '')}",
        "- decision_criteria:",
        f"- required_evidence_refs: {json.dumps(plan_payload.get('required_evidence_refs', []), ensure_ascii=False)}",
        f"- exit_criteria: {json.dumps(plan_payload.get('exit_criteria', []), ensure_ascii=False)}",
        "",
        f"{DECISION_SUMMARY_ANCHOR} ",
        "",
    ]

    target_documents = plan_payload.get("target_documents")
    if isinstance(target_documents, list) and target_documents:
        lines.extend(["## target_documents"])
        for target in target_documents:
            if not isinstance(target, dict):
                continue
            lines.append(
                f"- {target.get('document_id', '')}: sections={json.dumps(target.get('target_sections', []), ensure_ascii=False)}"
            )
        lines.extend(["", "## writeback_items"])
        writeback_items = plan_payload.get("writeback_items")
        if isinstance(writeback_items, list) and writeback_items:
            lines.extend(f"- {item}" for item in writeback_items if isinstance(item, str))
        else:
            lines.append("- (none)")
        lines.extend([""])
    else:
        lines.extend(["## near_open_but_blocked（来自 plan-open-window）"])
        lines.extend(_render_entity_lines(near_open_but_blocked))
        lines.extend(["", "## hard_blocked（来自 plan-open-window）"])
        lines.extend(_render_entity_lines(hard_blocked))
        lines.extend([""])

    lines.extend(
        [
            "## 讨论记录",
            "- 结论:",
            "- 待办:",
            "- 风险:",
            "",
        ]
    )
    return "\n".join(lines)


def _render_entity_lines(items: list[dict[str, Any]]) -> list[str]:
    if not items:
        return ["- (none)"]
    lines: list[str] = []
    for item in items:
        entity_type = _as_text(item.get("entity_type"))
        entity_id = _as_text(item.get("entity_id"))
        reason = _summarize_blockers(item)
        lines.append(f"- {entity_type}:{entity_id} | blockers={reason}")
    return lines


def _summarize_blockers(item: dict[str, Any]) -> str:
    blockers = item.get("blockers")
    if isinstance(blockers, list) and blockers:
        return json.dumps(blockers, ensure_ascii=False)
    hard_blockers = item.get("hard_blockers")
    if isinstance(hard_blockers, list) and hard_blockers:
        return json.dumps(hard_blockers, ensure_ascii=False)
    return "[]"


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _as_entity_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]
