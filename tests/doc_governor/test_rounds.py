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


def _base_state() -> dict:
    return {
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
            "DOC-PLAN-P1": _document_entry(
                doc_type="plan",
                path="docs/superpowers/plans/plan.md",
            ),
        },
    }


class GovernanceRoundsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root = Path(tempfile.gettempdir()) / f"doc-governor-rounds-{uuid.uuid4().hex}"
        self.temp_root.mkdir(exist_ok=True)
        (self.temp_root / "docs" / "governance").mkdir(parents=True, exist_ok=True)
        self.state_path = self.temp_root / "docs" / "governance" / "DOC_STATE.yaml"
        self._write_doc("docs/superpowers/specs/spec.md", "# Spec\n\n## 1. 文档目标\n\n说明。\n")
        self._write_doc("docs/superpowers/plans/plan.md", "# Plan\n\n## 1. 文档目标\n\n说明。\n")
        self._write_state(_base_state())

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def _write_state(self, state: dict) -> None:
        self.state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

    def _read_state(self) -> dict:
        return yaml.safe_load(self.state_path.read_text(encoding="utf-8"))

    def _write_doc(self, relative_path: str, content: str) -> None:
        path = self.temp_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

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

    def test_generate_round_template_registers_open_round(self) -> None:
        exit_code, payload = self._run_cli(
            "generate-round-template",
            "--round-id",
            "R-ROUND-01",
            "--state",
            str(self.state_path),
            "--entity-type",
            "document",
            "--entity-id",
            "DOC-SPEC-P1",
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        round_path = self.temp_root / "docs" / "governance" / "rounds" / "R-ROUND-01.md"
        self.assertTrue(round_path.exists())

        state = self._read_state()
        round_entry = state["governance_rounds"][0]
        self.assertEqual(round_entry["round_id"], "R-ROUND-01")
        self.assertEqual(round_entry["status"], "open")
        self.assertEqual(round_entry["target_documents"][0]["document_id"], "DOC-SPEC-P1")
        confirmed = state["documents"]["DOC-SPEC-P1"]["state"]["confirmed"]
        self.assertEqual(confirmed["active_round_id"], "R-ROUND-01")

    def test_update_round_status_review_to_closed(self) -> None:
        exit_code, _ = self._run_cli(
            "generate-round-template",
            "--round-id",
            "R-ROUND-02",
            "--state",
            str(self.state_path),
            "--entity-type",
            "document",
            "--entity-id",
            "DOC-SPEC-P1",
        )
        self.assertEqual(exit_code, 0)

        exit_code, review_payload = self._run_cli(
            "update-round-status",
            "--round-id",
            "R-ROUND-02",
            "--state",
            str(self.state_path),
            "--status",
            "review",
            "--actor",
            "alice",
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(review_payload["ok"])

        exit_code, closed_payload = self._run_cli(
            "update-round-status",
            "--round-id",
            "R-ROUND-02",
            "--state",
            str(self.state_path),
            "--status",
            "closed",
            "--actor",
            "alice",
            "--close-reason",
            "completed",
            "--decision-ref",
            "decision:DR-ROUND-02",
            "--result-summary",
            "round finished",
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(closed_payload["ok"])

        state = self._read_state()
        round_entry = state["governance_rounds"][0]
        self.assertEqual(round_entry["status"], "closed")
        self.assertEqual(round_entry["closed_by"], "alice")
        self.assertEqual(round_entry["close_reason"], "completed")
        self.assertIn("decision:DR-ROUND-02", round_entry["decision_refs"])
        confirmed = state["documents"]["DOC-SPEC-P1"]["state"]["confirmed"]
        self.assertIsNone(confirmed["active_round_id"])
        self.assertEqual(confirmed["last_round_id"], "R-ROUND-02")


if __name__ == "__main__":
    unittest.main()
