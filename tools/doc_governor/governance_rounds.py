from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_state(state_path: str | Path) -> dict[str, Any]:
    import yaml

    path = Path(state_path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def write_state(state_path: str | Path, state: dict[str, Any]) -> None:
    import yaml

    path = Path(state_path)
    path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_document_round_plan(
    *,
    round_id: str,
    evaluate_payload: dict[str, Any],
    state: dict[str, Any],
    entity_id: str | None,
) -> dict[str, Any]:
    documents = evaluate_payload.get("documents")
    documents = documents if isinstance(documents, dict) else {}
    selected_ids = [entity_id] if entity_id else sorted(documents.keys())
    target_documents: list[dict[str, Any]] = []
    required_evidence_refs: list[str] = []
    writeback_items: list[str] = []

    state_documents = state.get("documents")
    state_documents = state_documents if isinstance(state_documents, dict) else {}

    for document_id in selected_ids:
        document = documents.get(document_id)
        state_document = state_documents.get(document_id)
        if not isinstance(document, dict) or not isinstance(state_document, dict):
            continue
        derived = document.get("derived")
        derived = derived if isinstance(derived, dict) else {}
        meta = state_document.get("meta")
        meta = meta if isinstance(meta, dict) else {}
        required_section_ids = [
            str(section.get("section_id"))
            for section in meta.get("required_sections", [])
            if isinstance(section, dict) and str(section.get("section_id", "")).strip()
        ]
        target_sections = derived.get("missing_required_sections")
        target_sections = target_sections if isinstance(target_sections, list) and target_sections else required_section_ids
        target_documents.append(
            {
                "document_id": document_id,
                "target_sections": target_sections,
            }
        )
        required_evidence_refs.extend(
            f"doc:{document_id}#{section_id}" for section_id in target_sections if isinstance(section_id, str) and section_id
        )
        for ref in derived.get("missing_relation_refs", []):
            if isinstance(ref, str) and ref:
                required_evidence_refs.append(ref)
        for ref in _relation_refs(meta):
            required_evidence_refs.append(ref)
        if derived.get("missing_required_sections"):
            writeback_items.append(
                f"{document_id}: 补齐章节 {', '.join(str(item) for item in derived.get('missing_required_sections', []))}"
            )
        if derived.get("missing_relation_refs"):
            writeback_items.append(
                f"{document_id}: 补齐引用 {', '.join(str(item) for item in derived.get('missing_relation_refs', []))}"
            )

    selected_ids = [item["document_id"] for item in target_documents]
    return {
        "ok": bool(target_documents),
        "workflow": "document_refinement",
        "round_id": round_id,
        "topic": "spec/plan document refinement",
        "scope": f"documents:{','.join(selected_ids)}" if selected_ids else "documents:none",
        "target_documents": target_documents,
        "required_evidence_refs": sorted(set(required_evidence_refs)),
        "exit_criteria": [
            "required sections complete",
            "declared relation refs present",
            "no unresolved hard blockers remain",
        ],
        "writeback_items": writeback_items or ["若仍存在阻塞，回写下一轮 agenda"],
        "summary": {
            "target_document_count": len(target_documents),
        },
    }


def register_round_from_plan(
    *,
    state_path: str | Path,
    plan_payload: dict[str, Any],
    round_id: str,
    opened_by: str = "doc-governor",
) -> dict[str, Any]:
    state = load_state(state_path)
    rounds = state.get("governance_rounds")
    if not isinstance(rounds, list):
        rounds = []
        state["governance_rounds"] = rounds
    existing = find_round(state, round_id)
    if existing is not None:
        raise ValueError(f"round already exists: {round_id}")

    record = {
        "round_id": round_id,
        "workflow": str(plan_payload.get("workflow", "document_refinement")),
        "topic": str(plan_payload.get("topic", "document refinement")),
        "scope": str(plan_payload.get("scope", "")),
        "status": "open",
        "opened_at": now_utc_iso(),
        "opened_by": opened_by,
        "started_at": None,
        "review_at": None,
        "closed_at": None,
        "closed_by": None,
        "close_reason": None,
        "decision_refs": [],
        "target_documents": _copy_list(plan_payload.get("target_documents")),
        "required_evidence_refs": _copy_str_list(plan_payload.get("required_evidence_refs")),
        "exit_criteria": _copy_str_list(plan_payload.get("exit_criteria")),
        "writeback_items": _copy_str_list(plan_payload.get("writeback_items")),
        "packet_paths": {
            "round_plan_json": None,
            "packet_json": None,
            "prompt_md": None,
            "exec_cmd_txt": None,
        },
        "result_summary": None,
    }
    rounds.append(record)
    _assign_active_round(state=state, round_id=round_id, target_documents=record["target_documents"])
    write_state(state_path, state)
    return record


def update_round_status(
    *,
    state_path: str | Path,
    round_id: str,
    status: str,
    actor: str,
    close_reason: str | None = None,
    decision_refs: list[str] | None = None,
    result_summary: str | None = None,
    packet_paths: dict[str, str] | None = None,
) -> dict[str, Any]:
    state = load_state(state_path)
    round_entry = find_round(state, round_id)
    if round_entry is None:
        raise ValueError(f"round not found: {round_id}")

    now = now_utc_iso()
    round_entry["status"] = status
    if status == "in_progress":
        round_entry["started_at"] = now
    elif status == "review":
        round_entry["review_at"] = now
    elif status == "closed":
        round_entry["closed_at"] = now
        round_entry["closed_by"] = actor
        round_entry["close_reason"] = close_reason
        round_entry["result_summary"] = result_summary
        if decision_refs:
            existing = round_entry.get("decision_refs")
            existing = existing if isinstance(existing, list) else []
            round_entry["decision_refs"] = sorted(set(existing + decision_refs))
        _clear_active_round(
            state=state,
            round_id=round_id,
            target_documents=round_entry.get("target_documents"),
        )

    if packet_paths:
        round_entry["packet_paths"] = {
            **(round_entry.get("packet_paths") if isinstance(round_entry.get("packet_paths"), dict) else {}),
            **packet_paths,
        }

    write_state(state_path, state)
    return round_entry


def find_round(state: dict[str, Any], round_id: str) -> dict[str, Any] | None:
    rounds = state.get("governance_rounds")
    if not isinstance(rounds, list):
        return None
    for item in rounds:
        if not isinstance(item, dict):
            continue
        if str(item.get("round_id")) == str(round_id):
            return item
    return None


def _assign_active_round(
    *,
    state: dict[str, Any],
    round_id: str,
    target_documents: list[dict[str, Any]],
) -> None:
    documents = state.get("documents")
    if not isinstance(documents, dict):
        return
    for target in target_documents:
        if not isinstance(target, dict):
            continue
        document_id = str(target.get("document_id", ""))
        document = documents.get(document_id)
        if not isinstance(document, dict):
            continue
        confirmed = _confirmed_state(document)
        active_round_id = confirmed.get("active_round_id")
        if active_round_id not in {None, "", round_id}:
            raise ValueError(f"document already active in another round: {document_id}")
        confirmed["active_round_id"] = round_id


def _clear_active_round(
    *,
    state: dict[str, Any],
    round_id: str,
    target_documents: Any,
) -> None:
    documents = state.get("documents")
    if not isinstance(documents, dict):
        return
    for target in target_documents if isinstance(target_documents, list) else []:
        if not isinstance(target, dict):
            continue
        document_id = str(target.get("document_id", ""))
        document = documents.get(document_id)
        if not isinstance(document, dict):
            continue
        confirmed = _confirmed_state(document)
        if confirmed.get("active_round_id") == round_id:
            confirmed["active_round_id"] = None
        confirmed["last_round_id"] = round_id


def _confirmed_state(document: dict[str, Any]) -> dict[str, Any]:
    state_obj = document.get("state")
    if not isinstance(state_obj, dict):
        state_obj = {}
        document["state"] = state_obj
    confirmed = state_obj.get("confirmed")
    if not isinstance(confirmed, dict):
        confirmed = {}
        state_obj["confirmed"] = confirmed
    return confirmed


def _relation_refs(meta: dict[str, Any]) -> list[str]:
    relations = meta.get("relations")
    relations = relations if isinstance(relations, dict) else {}
    refs: list[str] = []
    refs.extend(f"doc:{item}" for item in relations.get("document_refs", []) if isinstance(item, str) and item)
    refs.extend(f"module:{item}" for item in relations.get("module_refs", []) if isinstance(item, str) and item)
    refs.extend(f"oq:{item}" for item in relations.get("oq_refs", []) if isinstance(item, str) and item)
    return refs


def _copy_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _copy_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item.strip()]
