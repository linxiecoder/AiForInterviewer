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


def _document_entry(
    *,
    doc_type: str,
    path: str,
    required_sections: list[tuple[str, str]],
    relations: dict | None = None,
) -> dict:
    return {
        "meta": {
            "doc_type": doc_type,
            "title": f"{doc_type} doc",
            "path": path,
            "required_sections": [
                {"section_id": section_id, "heading": heading}
                for section_id, heading in required_sections
            ],
            "relations": relations
            or {
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


class DocumentIntegrationTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "document-integration"

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
            "oqs": {
                "OQ-004": {
                    "title": "鉴权机制",
                    "status": "proposed-default",
                    "gate_level": "observe_only",
                    "resolution_policy": "proposed_default_ok",
                    "affects": {
                        "modules": ["M02"],
                        "subtasks": [],
                    },
                    "declared_blocker_refs": [],
                }
            },
            "modules": {},
            "subtasks": {},
            "documents": {
                "DOC-SPEC-P1": _document_entry(
                    doc_type="design",
                    path="docs/superpowers/specs/spec.md",
                    required_sections=[
                        ("goal", "## 1. 文档目标"),
                        ("architecture", "## 5. 系统架构"),
                    ],
                    relations={
                        "document_refs": ["DOC-PLAN-P1"],
                        "module_refs": ["M02"],
                        "oq_refs": ["OQ-004"],
                    },
                ),
                "DOC-PLAN-P1": _document_entry(
                    doc_type="plan",
                    path="docs/superpowers/plans/plan.md",
                    required_sections=[
                        ("scope", "## 范围说明"),
                        ("milestones", "## 二级任务分解与执行顺序"),
                    ],
                    relations={
                        "document_refs": ["DOC-SPEC-P1"],
                        "module_refs": [],
                        "oq_refs": ["OQ-004"],
                    },
                ),
            },
        }
        self.state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
        self._write_doc(
            "docs/superpowers/specs/spec.md",
            "# Spec\n\n## 1. 文档目标\n\n引用 `M02` 与 `OQ-004`。\n\n另见 `docs/superpowers/plans/plan.md`。\n",
        )
        self._write_doc(
            "docs/superpowers/plans/plan.md",
            "# Plan\n\n## 范围说明\n\n引用 `OQ-004`。\n\n另见 `docs/superpowers/specs/spec.md`。\n",
        )

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

    def test_spec_and_plan_round_mvp(self) -> None:
        exit_code, evaluate_payload = self._run_cli(
            "evaluate-state",
            "--input",
            str(self.state_path),
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("documents", evaluate_payload)

        exit_code, plan_payload = self._run_cli(
            "plan-round",
            "--state",
            str(self.state_path),
            "--entity-type",
            "document",
            "--round-id",
            "R-DOC-INT-01",
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(plan_payload["round_id"], "R-DOC-INT-01")
        self.assertEqual(len(plan_payload["target_documents"]), 2)

        exit_code, _ = self._run_cli(
            "generate-round-template",
            "--round-id",
            "R-DOC-INT-01",
            "--state",
            str(self.state_path),
            "--entity-type",
            "document",
        )
        self.assertEqual(exit_code, 0)

        exit_code, packet_payload = self._run_cli(
            "generate-codex-packet",
            "--round-id",
            "R-DOC-INT-01",
            "--state",
            str(self.state_path),
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(packet_payload["ok"])

        self._write_doc(
            "docs/superpowers/specs/spec.md",
            "# Spec\n\n## 1. 文档目标\n\n引用 `M02` 与 `OQ-004`。\n\n## 5. 系统架构\n\n架构补齐。\n\n另见 `docs/superpowers/plans/plan.md`。\n",
        )
        self._write_doc(
            "docs/superpowers/plans/plan.md",
            "# Plan\n\n## 范围说明\n\n引用 `OQ-004`。\n\n## 二级任务分解与执行顺序\n\n里程碑补齐。\n\n另见 `docs/superpowers/specs/spec.md`。\n",
        )

        exit_code, _ = self._run_cli(
            "confirm-transition",
            "--input",
            str(self.state_path),
            "--entity-type",
            "document",
            "--entity-id",
            "DOC-SPEC-P1",
            "--proposed-changes",
            json.dumps(
                {
                    "status": "active",
                    "review_status": "approved",
                    "blocker_refs": [],
                    "active_round_id": "R-DOC-INT-01",
                }
            ),
            "--mode",
            "approve",
            "--actor",
            "alice",
            "--reason",
            "Decision: spec ready",
            "--round-id",
            "R-DOC-INT-01",
        )
        self.assertEqual(exit_code, 0)

        exit_code, _ = self._run_cli(
            "confirm-transition",
            "--input",
            str(self.state_path),
            "--entity-type",
            "document",
            "--entity-id",
            "DOC-PLAN-P1",
            "--proposed-changes",
            json.dumps(
                {
                    "status": "active",
                    "review_status": "approved",
                    "blocker_refs": [],
                    "active_round_id": "R-DOC-INT-01",
                }
            ),
            "--mode",
            "approve",
            "--actor",
            "alice",
            "--reason",
            "Decision: plan ready",
            "--round-id",
            "R-DOC-INT-01",
        )
        self.assertEqual(exit_code, 0)

        exit_code, _ = self._run_cli(
            "update-round-status",
            "--round-id",
            "R-DOC-INT-01",
            "--state",
            str(self.state_path),
            "--status",
            "review",
            "--actor",
            "alice",
        )
        self.assertEqual(exit_code, 0)

        exit_code, _ = self._run_cli(
            "update-round-status",
            "--round-id",
            "R-DOC-INT-01",
            "--state",
            str(self.state_path),
            "--status",
            "closed",
            "--actor",
            "alice",
            "--close-reason",
            "completed",
            "--decision-ref",
            "decision:DR-DOC-INT-01",
            "--result-summary",
            "spec/plan refined",
        )
        self.assertEqual(exit_code, 0)

        exit_code, final_payload = self._run_cli(
            "evaluate-state",
            "--input",
            str(self.state_path),
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            final_payload["documents"]["DOC-SPEC-P1"]["derived"]["missing_required_sections"],
            [],
        )
        self.assertEqual(
            final_payload["documents"]["DOC-PLAN-P1"]["derived"]["missing_required_sections"],
            [],
        )
        state = self._read_state()
        round_entry = state["governance_rounds"][0]
        self.assertEqual(round_entry["status"], "closed")
        self.assertEqual(
            state["documents"]["DOC-SPEC-P1"]["state"]["confirmed"]["last_round_id"],
            "R-DOC-INT-01",
        )
        self.assertEqual(
            state["documents"]["DOC-PLAN-P1"]["state"]["confirmed"]["last_round_id"],
            "R-DOC-INT-01",
        )


if __name__ == "__main__":
    unittest.main()
