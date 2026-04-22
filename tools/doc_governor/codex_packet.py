from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .governance_rounds import find_round, load_state, now_utc_iso, update_round_status


CODEX_CMD_PATH = r"C:\Users\Administrator\AppData\Roaming\npm\codex.cmd"
PACKETS_DIR = Path("docs/governance/packets")


def generate_codex_packet(
    *,
    state_path: str,
    round_id: str,
) -> dict[str, Any]:
    state = load_state(state_path)
    round_entry = find_round(state, round_id)
    if round_entry is None:
        raise ValueError(f"round not found: {round_id}")

    documents = state.get("documents")
    documents = documents if isinstance(documents, dict) else {}
    target_documents: list[dict[str, Any]] = []
    allowed_modify_paths: list[str] = []

    for target in round_entry.get("target_documents", []):
        if not isinstance(target, dict):
            continue
        document_id = str(target.get("document_id", ""))
        document = documents.get(document_id)
        if not isinstance(document, dict):
            continue
        meta = document.get("meta")
        meta = meta if isinstance(meta, dict) else {}
        path = str(meta.get("path", ""))
        allowed_modify_paths.append(path)
        target_documents.append(
            {
                "document_id": document_id,
                "path": path,
                "allowed_sections": [
                    section
                    for section in target.get("target_sections", [])
                    if isinstance(section, str) and section
                ],
            }
        )

    packet = {
        "schema_version": 1,
        "workflow": str(round_entry.get("workflow", "document_refinement")),
        "round_id": round_id,
        "generated_at": now_utc_iso(),
        "repo_root": str(Path(state_path).resolve().parents[2]).replace("\\", "/"),
        "codex_cli": {
            "command_path": CODEX_CMD_PATH.replace("\\", "/"),
            "recommended_subcommand": "exec",
        },
        "round_goal": str(round_entry.get("topic", "")),
        "target_documents": target_documents,
        "allowed_modify_paths": allowed_modify_paths,
        "forbidden_modify_paths": [
            "docs/governance/DOC_STATE.yaml",
            "docs/governance/DOC_STATE.bootstrap.yaml",
            "OPEN_QUESTIONS.md",
            "TASK_INDEX.md",
            "DOCUMENT_MATURITY.md",
            "DOCUMENT_PROGRESS.md",
            "docs/modules/**",
        ],
        "governance_constraints": [
            "不得把正文中的自称 ready/candidate 直接写成 confirmed state",
            "不得改 modules/subtasks/OQ 的既有治理语义",
            "不得扩展到未授权文件",
        ],
        "required_evidence_refs": [
            ref for ref in round_entry.get("required_evidence_refs", []) if isinstance(ref, str)
        ],
        "decision_refs": [
            ref for ref in round_entry.get("decision_refs", []) if isinstance(ref, str)
        ],
        "exit_criteria": [
            ref for ref in round_entry.get("exit_criteria", []) if isinstance(ref, str)
        ],
        "writeback_suggestions": [
            ref for ref in round_entry.get("writeback_items", []) if isinstance(ref, str)
        ],
    }

    packet_dir = PACKETS_DIR
    packet_dir.mkdir(parents=True, exist_ok=True)
    packet_json_path = packet_dir / f"{round_id}.packet.json"
    prompt_md_path = packet_dir / f"{round_id}.prompt.md"
    exec_cmd_path = packet_dir / f"{round_id}.exec.txt"

    packet_json_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")
    prompt_md_path.write_text(_build_prompt(packet), encoding="utf-8")
    exec_cmd_path.write_text(_build_exec_command(round_id), encoding="utf-8")

    update_round_status(
        state_path=state_path,
        round_id=round_id,
        status="in_progress",
        actor="doc-governor",
        packet_paths={
            "packet_json": packet_json_path.as_posix(),
            "prompt_md": prompt_md_path.as_posix(),
            "exec_cmd_txt": exec_cmd_path.as_posix(),
        },
    )

    return {
        "ok": True,
        "round_id": round_id,
        "packet_json_path": packet_json_path.as_posix(),
        "prompt_md_path": prompt_md_path.as_posix(),
        "exec_cmd_path": exec_cmd_path.as_posix(),
    }


def _build_prompt(packet: dict[str, Any]) -> str:
    lines = [
        "# Doc Governor Round Packet",
        "",
        "## 本轮目标",
        f"- {packet.get('round_goal', '')}",
        "",
        "## 目标文档",
    ]
    for target in packet.get("target_documents", []):
        lines.append(
            f"- {target.get('document_id', '')} -> {target.get('path', '')}"
        )
        lines.append(
            f"- 允许修改章节：{', '.join(target.get('allowed_sections', [])) or '(none)'}"
        )

    lines.extend(
        [
            "",
            "## 允许修改范围",
        ]
    )
    lines.extend(f"- {path}" for path in packet.get("allowed_modify_paths", []))
    lines.extend(
        [
            "",
            "## 禁止修改范围",
        ]
    )
    lines.extend(f"- {path}" for path in packet.get("forbidden_modify_paths", []))
    lines.extend(
        [
            "",
            "## 必须遵守的治理约束",
        ]
    )
    lines.extend(f"- {item}" for item in packet.get("governance_constraints", []))
    lines.extend(
        [
            "",
            "## 必须引用的 evidence / decision",
            f"- evidence: {', '.join(packet.get('required_evidence_refs', [])) or 'none'}",
            f"- decision: {', '.join(packet.get('decision_refs', [])) or 'none'}",
            "",
            "## Exit Criteria",
        ]
    )
    lines.extend(f"- {item}" for item in packet.get("exit_criteria", []))
    lines.extend(
        [
            "",
            "## 回写建议",
        ]
    )
    lines.extend(f"- {item}" for item in packet.get("writeback_suggestions", []))
    lines.extend(
        [
            "",
            "## 输出要求",
            "- 只修改允许范围内文档",
            "- 说明本轮改了什么",
            "- 说明哪些阻塞仍在",
            "- 如发现新问题，只写入本轮 notes，不自行扩散到全局状态文件",
            "",
        ]
    )
    return "\n".join(lines)


def _build_exec_command(round_id: str) -> str:
    prompt = f"docs\\governance\\packets\\{round_id}.prompt.md"
    events = f"docs\\governance\\packets\\{round_id}.events.jsonl"
    last = f"docs\\governance\\packets\\{round_id}.last_message.md"
    return "\n".join(
        [
            f'$prompt = "{prompt}"',
            f'$events = "{events}"',
            f'$last = "{last}"',
            "",
            'Get-Content -LiteralPath $prompt -Encoding UTF8 |',
            f'  & "{CODEX_CMD_PATH}" exec `',
            '    -C "." `',
            '    --sandbox workspace-write `',
            '    --output-last-message $last `',
            '    --json - |',
            '  Tee-Object -FilePath $events',
            "",
        ]
    )
