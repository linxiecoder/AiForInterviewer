from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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

    plan_payload = plan_open_window(
        state=state,
        history=history,
        evaluate_json=evaluate_json,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
    )

    near_open_but_blocked = _as_entity_list(plan_payload.get("near_open_but_blocked"))
    hard_blocked = _as_entity_list(plan_payload.get("hard_blocked"))

    output_path = Path("docs/governance/rounds") / f"{normalized_round_id}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        _build_round_template(
            round_id=normalized_round_id,
            near_open_but_blocked=near_open_but_blocked,
            hard_blocked=hard_blocked,
        ),
        encoding="utf-8",
    )

    return {
        "ok": bool(plan_payload.get("ok", False)),
        "round_id": normalized_round_id,
        "output_path": output_path.as_posix(),
        "decision_anchor": DECISION_SUMMARY_ANCHOR,
        "near_open_but_blocked": near_open_but_blocked,
        "hard_blocked": hard_blocked,
        "near_open_but_blocked_count": len(near_open_but_blocked),
        "hard_blocked_count": len(hard_blocked),
        "summary": plan_payload.get("summary", {}),
        "parse_errors": plan_payload.get("parse_errors", []),
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
    near_open_but_blocked: list[dict[str, Any]],
    hard_blocked: list[dict[str, Any]],
) -> str:
    lines: list[str] = [
        f"# Discussion Round {round_id}",
        "",
        "## 最小输入字段",
        "- round_goal:",
        "- entities_in_scope:",
        "- decision_criteria:",
        "- required_evidence_refs:",
        "- exit_criteria:",
        "",
        f"{DECISION_SUMMARY_ANCHOR} ",
        "",
        "## near_open_but_blocked（来自 plan-open-window）",
    ]
    lines.extend(_render_entity_lines(near_open_but_blocked))
    lines.extend([
        "",
        "## hard_blocked（来自 plan-open-window）",
    ])
    lines.extend(_render_entity_lines(hard_blocked))
    lines.extend(
        [
            "",
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
