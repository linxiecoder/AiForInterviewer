import io
import json
import os
import shutil
import tempfile
import unittest
import uuid
from contextlib import redirect_stdout
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.cli import main
from tools.testing.temp_artifacts import ManagedTempArtifactsTestCase


def _document_entry(*, doc_type: str, path: str) -> dict:
    return {
        "meta": {
            "doc_type": doc_type,
            "title": f"{doc_type} doc",
            "path": path,
            "required_sections": [
                {"section_id": "goal", "heading": "## 1. 文档目标"},
                {"section_id": "architecture", "heading": "## 5. 系统架构"},
            ],
            "relations": {
                "document_refs": [],
                "module_refs": [],
                "oq_refs": [],
            },
        },
        "facts": {
            "exists": True,
            "headings": [],
            "section_presence": {},
            "extracted_refs": {
                "document_refs": [],
                "module_refs": [],
                "oq_refs": [],
            },
            "marker_counts": {
                "todo": 0,
                "tbd": 0,
                "unresolved": 0,
            },
            "last_scanned_at": None,
        },
        "state": {"confirmed": schema.make_default_confirmed_state("document")},
    }


class CodexPacketTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "codex-packet"

    def setUp(self) -> None:
        super().setUp()
        (self.temp_root / "docs" / "governance").mkdir(parents=True, exist_ok=True)
        self.state_path = self.temp_root / "docs" / "governance" / "DOC_STATE.yaml"
        state = {
            "schema_version": schema.SCHEMA_VERSION,
            "global_policy": {
                "auto_open_enabled": False,
                "require_confirmation_for_state_writeback": True,
                "strict_template_gate": True,
                "formal_window_open": False,
                "paths": {
                    "modules_root": "docs/modules",
                    "open_questions_doc": "OPEN_QUESTIONS.md",
                    "task_index_doc": "TASK_INDEX.md",
                },
            },
            "oqs": {},
            "modules": {},
            "subtasks": {},
            "documents": {
                "DOC-SPEC-P1": _document_entry(
                    doc_type="design",
                    path="docs/superpowers/specs/spec.md",
                ),
            },
        }
        self.state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
        self._write_doc("docs/superpowers/specs/spec.md", "# Spec\n\n## 1. 文档目标\n\n说明。\n")
        exit_code, _ = self._run_cli(
            "generate-round-template",
            "--round-id",
            "R-PACKET-01",
            "--state",
            str(self.state_path),
            "--entity-type",
            "document",
            "--entity-id",
            "DOC-SPEC-P1",
        )
        self.assertEqual(exit_code, 0)

    def _write_doc(self, relative_path: str, content: str) -> None:
        path = self.temp_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _read_state(self) -> dict:
        return yaml.safe_load(self.state_path.read_text(encoding="utf-8"))

    def _run_cli(self, *args: str) -> tuple[int, dict]:
        original = Path.cwd()
        try:
            os.chdir(self.temp_root)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(list(args))
            payload = json.loads(stdout.getvalue())
            return exit_code, payload
        finally:
            os.chdir(original)

    def test_generate_codex_packet_outputs_json_markdown_and_command(self) -> None:
        exit_code, payload = self._run_cli(
            "generate-codex-packet",
            "--round-id",
            "R-PACKET-01",
            "--state",
            str(self.state_path),
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])

        packet_dir = self.temp_root / "docs" / "governance" / "packets"
        packet_json_path = packet_dir / "R-PACKET-01.packet.json"
        prompt_path = packet_dir / "R-PACKET-01.prompt.md"
        exec_path = packet_dir / "R-PACKET-01.exec.txt"
        self.assertTrue(packet_json_path.exists())
        self.assertTrue(prompt_path.exists())
        self.assertTrue(exec_path.exists())

        packet = json.loads(packet_json_path.read_text(encoding="utf-8"))
        self.assertEqual(packet["round_id"], "R-PACKET-01")
        self.assertEqual(packet["target_documents"][0]["document_id"], "DOC-SPEC-P1")
        self.assertIn("docs/superpowers/specs/spec.md", packet["allowed_modify_paths"])
        self.assertIn("docs/governance/DOC_STATE.yaml", packet["forbidden_modify_paths"])

        prompt = prompt_path.read_text(encoding="utf-8")
        self.assertIn("## 本轮目标", prompt)
        self.assertIn("DOC-SPEC-P1", prompt)
        self.assertIn("## 禁止修改范围", prompt)

        command_text = exec_path.read_text(encoding="utf-8")
        self.assertIn("codex.cmd", command_text)
        self.assertIn("exec", command_text)

        state = self._read_state()
        round_entry = state["governance_rounds"][0]
        self.assertEqual(round_entry["status"], "in_progress")
        self.assertEqual(round_entry["packet_paths"]["packet_json"], "docs/governance/packets/R-PACKET-01.packet.json")


if __name__ == "__main__":
    unittest.main()
