from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .evaluate import evaluate_state_file


DEFAULT_PACKET_DIR = Path("docs/governance/packets")


def generate_implementation_packet(
    *,
    state_path: str,
    entity_id: str,
    evaluate_payload: dict[str, Any],
    output_dir: str | None = None,
) -> dict[str, Any]:
    state_file = Path(state_path)
    state = _load_state(state_file)
    subtasks = state.get("subtasks")
    subtasks = subtasks if isinstance(subtasks, dict) else {}
    subtask = subtasks.get(entity_id)
    if not isinstance(subtask, dict):
        raise ValueError(f"subtask not found: {entity_id}")

    live_diagnostics, live_payload = evaluate_state_file(state_file)
    errors = [item for item in live_diagnostics if item.severity == "error"]
    if errors:
        raise ValueError(
            "validate/evaluate gate failed; errors="
            + ", ".join(item.code for item in errors)
        )

    evaluate_payload = live_payload if isinstance(live_payload, dict) else evaluate_payload
    evaluate_subtasks = evaluate_payload.get("subtasks")
    evaluate_subtasks = evaluate_subtasks if isinstance(evaluate_subtasks, dict) else {}
    evaluate_entry = evaluate_subtasks.get(entity_id)
    evaluate_entry = evaluate_entry if isinstance(evaluate_entry, dict) else {}
    derived = evaluate_entry.get("derived")
    derived = derived if isinstance(derived, dict) else {}
    packet_inputs = derived.get("implementation_packet_inputs")
    packet_inputs = packet_inputs if isinstance(packet_inputs, dict) else {}
    path_conflicts = _as_list_of_dicts(packet_inputs.get("path_conflicts"))
    if path_conflicts:
        raise ValueError(
            "path scope conflict: "
            + "; ".join(
                f"{item.get('allowed', '')} conflicts with {item.get('forbidden', '')}"
                for item in path_conflicts
            )
        )
    confirmed = _as_dict(_as_dict(subtask.get("state")).get("confirmed"))
    if confirmed.get("formal_window_status", "closed") != "open":
        raise ValueError(
            "implementation packet requires subtask formal_window_status=open"
        )
    if not bool(derived.get("implementation_ready")):
        blocker_refs = derived.get("blocker_refs")
        blocker_refs = blocker_refs if isinstance(blocker_refs, list) else []
        raise ValueError(
            "implementation_ready=false; blockers="
            + ", ".join(str(item) for item in blocker_refs if isinstance(item, str))
        )

    _assert_packet_inputs_ready(
        entity_id=entity_id,
        subtask=subtask,
        derived=derived,
        packet_inputs=packet_inputs,
    )
    requirement_id = packet_inputs.get("requirement_id")
    requirement_id = requirement_id if isinstance(requirement_id, str) and requirement_id else None
    if requirement_id is None:
        raise ValueError("implementation packet missing unique requirement_id")

    meta = subtask.get("meta")
    meta = meta if isinstance(meta, dict) else {}
    facts = subtask.get("facts")
    facts = facts if isinstance(facts, dict) else {}
    module_id = str(meta.get("module_id", "")).strip()
    if not module_id:
        raise ValueError("implementation packet missing module_id")

    requirement = _as_dict(_as_dict(state.get("requirements")).get(requirement_id))
    requirement_facts = _as_dict(requirement.get("facts"))
    requirement_assets = _as_dict(requirement_facts.get("asset_slots"))
    official_doc_paths = _as_dict(packet_inputs.get("official_doc_paths"))

    packet = {
        "schema_version": 1,
        "artifact_kind": "implementation_packet",
        "runtime_artifact": True,
        "generated_at": _now_utc_iso(),
        "task_id": entity_id,
        "module_id": module_id,
        "requirement_id": requirement_id,
        "implementation_ready": True,
        "goal": str(packet_inputs.get("goal", "")).strip(),
        "allowed_modify_paths": _as_string_list(packet_inputs.get("allowed_modify_paths")),
        "forbidden_paths": _dedupe_strings(
            _as_string_list(packet_inputs.get("forbidden_paths"))
            + [
                "docs/governance/DOC_STATE.yaml",
                "docs/governance/DOC_STATE.bootstrap.yaml",
            ]
        ),
        "required_tests": _as_string_list(packet_inputs.get("required_tests")),
        "acceptance_criteria": _as_string_list(packet_inputs.get("acceptance_criteria")),
        "upstream_refs": _build_upstream_refs(
            task_id=entity_id,
            module_id=module_id,
            requirement_id=requirement_id,
            facts=facts,
        ),
        "artifact_constraints": {
            "runtime_artifact": True,
            "required_requirement_assets": sorted(
                slot_name
                for slot_name, slot_value in requirement_assets.items()
                if isinstance(slot_name, str)
                and isinstance(slot_value, dict)
                and bool(slot_value.get("exists"))
            ),
            "required_task_doc_slots": ["design_doc", "implementation_doc"],
            "official_doc_paths": {
                "design_doc": str(official_doc_paths.get("design_doc", "")).strip(),
                "implementation_doc": str(official_doc_paths.get("implementation_doc", "")).strip(),
            },
        },
        "language_constraints": {
            "docs_must_be_chinese_first": True,
            "allowed_english_categories": [
                "code",
                "command",
                "path",
                "config_key",
                "api_name",
                "class_name",
                "function_name",
                "field_name",
                "standard_term",
            ],
            "blocking_violations": _as_list_of_dicts(packet_inputs.get("language_violations")),
        },
    }

    output_dir_path = _resolve_output_dir(state_file, output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    packet_json_path = output_dir_path / f"{entity_id}.implementation.packet.json"
    packet_md_path = output_dir_path / f"{entity_id}.implementation.packet.md"
    packet_json_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")
    packet_md_path.write_text(_render_markdown(packet), encoding="utf-8")
    return {
        "ok": True,
        "task_id": entity_id,
        "packet_json_path": packet_json_path.as_posix(),
        "packet_markdown_path": packet_md_path.as_posix(),
        "summary": {
            "module_id": module_id,
            "requirement_id": requirement_id,
            "allowed_modify_paths_count": len(packet["allowed_modify_paths"]),
            "required_tests_count": len(packet["required_tests"]),
            "acceptance_criteria_count": len(packet["acceptance_criteria"]),
        },
    }


def _assert_packet_inputs_ready(
    *,
    entity_id: str,
    subtask: dict[str, Any],
    derived: dict[str, Any],
    packet_inputs: dict[str, Any],
) -> None:
    facts = _as_dict(subtask.get("facts"))
    state = _as_dict(subtask.get("state"))
    confirmed = _as_dict(state.get("confirmed"))
    design_doc = _as_dict(facts.get("design_doc"))
    implementation_doc = _as_dict(facts.get("implementation_doc"))
    blockers: list[str] = []

    if not bool(design_doc.get("exists")):
        blockers.append("design_doc missing")
    if bool(design_doc.get("template_like")):
        blockers.append("design_doc template-like")
    if not bool(implementation_doc.get("exists")):
        blockers.append("implementation_doc missing")
    if bool(implementation_doc.get("template_like")):
        blockers.append("implementation_doc template-like")
    if confirmed.get("implementation_doc_state") != "active_working_doc":
        blockers.append("implementation_doc_state must be active_working_doc")
    if confirmed.get("formal_window_status", "closed") != "open":
        blockers.append("formal_window_status must be open")
    if (
        confirmed.get("implementation_approval_status", "none") != "approved"
        and confirmed.get("readiness") != "implementation_ready"
    ):
        blockers.append("implementation approval missing")
    if not _as_string_list(packet_inputs.get("acceptance_criteria")):
        blockers.append("acceptance criteria missing")
    if not _as_string_list(packet_inputs.get("required_tests")):
        blockers.append("required tests missing")
    if not str(packet_inputs.get("goal", "")).strip():
        blockers.append("implementation goal missing")
    if not _as_string_list(packet_inputs.get("allowed_modify_paths")):
        blockers.append("allowed_modify_paths missing")
    if not _as_string_list(packet_inputs.get("forbidden_paths")):
        blockers.append("forbidden_paths missing")
    path_conflicts = _as_list_of_dicts(packet_inputs.get("path_conflicts"))
    if path_conflicts:
        blockers.append(
            "path scope conflict: "
            + "; ".join(
                f"{item.get('allowed', '')} conflicts with {item.get('forbidden', '')}"
                for item in path_conflicts
            )
        )
    if _as_list_of_dicts(packet_inputs.get("language_violations")):
        blockers.append("language violations present")
    if _as_string_list(derived.get("blocker_refs")):
        blockers.append("blocking diagnostics present")

    if blockers:
        raise ValueError(
            f"implementation packet gate failed for {entity_id}: "
            + "; ".join(blockers)
        )


def _render_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# 任务实施 Packet",
        "",
        "## 基本信息",
        f"- task_id: {packet.get('task_id', '')}",
        f"- module_id: {packet.get('module_id', '')}",
        f"- requirement_id: {packet.get('requirement_id', '')}",
        f"- runtime_artifact: {packet.get('runtime_artifact', False)}",
        "",
        "## 任务目标",
        f"- {packet.get('goal', '')}",
        "",
        "## 允许修改范围",
    ]
    lines.extend(f"- {item}" for item in packet.get("allowed_modify_paths", []))
    lines.extend(
        [
            "",
            "## 禁止修改范围",
        ]
    )
    lines.extend(f"- {item}" for item in packet.get("forbidden_paths", []))
    lines.extend(
        [
            "",
            "## 测试要求",
        ]
    )
    lines.extend(f"- {item}" for item in packet.get("required_tests", []))
    lines.extend(
        [
            "",
            "## 完成判定",
        ]
    )
    lines.extend(f"- {item}" for item in packet.get("acceptance_criteria", []))
    lines.extend(
        [
            "",
            "## 上游引用",
        ]
    )
    lines.extend(f"- {item}" for item in packet.get("upstream_refs", []))
    lines.extend(
        [
            "",
            "## 工件约束",
            f"- official design doc: {packet.get('artifact_constraints', {}).get('official_doc_paths', {}).get('design_doc', '')}",
            f"- official implementation doc: {packet.get('artifact_constraints', {}).get('official_doc_paths', {}).get('implementation_doc', '')}",
            "",
            "## 语言约束",
            "- 正式文档默认中文为主",
            "- 英文仅用于必要技术标识",
        ]
    )
    return "\n".join(lines) + "\n"


def _load_state(state_path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - environment guard
        raise ValueError(f"PyYAML is required to load state file: {exc}") from exc

    try:
        raw = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"state file not found: {state_path}") from exc
    if not isinstance(raw, dict):
        raise ValueError("state file must contain a mapping")
    return raw


def _resolve_output_dir(state_path: Path, output_dir: str | None) -> Path:
    if output_dir:
        return Path(output_dir)
    default_root = state_path.resolve().parent
    if default_root.name == "governance":
        return default_root / DEFAULT_PACKET_DIR.name
    return default_root / DEFAULT_PACKET_DIR.name


def _build_upstream_refs(
    *,
    task_id: str,
    module_id: str,
    requirement_id: str,
    facts: dict[str, Any],
) -> list[str]:
    refs = [
        f"requirement:{requirement_id}",
        f"module:{module_id}",
        f"subtask:{task_id}",
    ]
    refs.extend(
        f"module:{item}"
        for item in _as_string_list(facts.get("upstream_module_ids"))
        if item != module_id
    )
    refs.extend(f"oq:{item}" for item in _as_string_list(facts.get("related_oq_ids")))
    return _dedupe_strings(refs)


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return _dedupe_strings([str(item).strip() for item in value if str(item).strip()])


def _as_list_of_dicts(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _dedupe_strings(items: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return ordered


def _now_utc_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
