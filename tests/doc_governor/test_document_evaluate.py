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
        "documents": {},
    }


def _document_entry(*, doc_type: str, path: str, required_sections: list[tuple[str, str]], relations: dict | None = None) -> dict:
    return {
        "meta": {
            "doc_type": doc_type,
            "title": f"{doc_type} document",
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


class DocumentEvaluateTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "document-evaluate"

    def setUp(self) -> None:
        super().setUp()
        (self.temp_root / "docs" / "governance").mkdir(parents=True, exist_ok=True)
        self.state_path = self.temp_root / "docs" / "governance" / "DOC_STATE.yaml"

    def _run_cli(self, *args: str) -> tuple[int, dict]:
        original = Path.cwd()
        try:
            stdout = io.StringIO()
            os.chdir(self.temp_root)
            with redirect_stdout(stdout):
                exit_code = main(list(args))
            payload = json.loads(stdout.getvalue())
            return exit_code, payload
        finally:
            os.chdir(original)

    def _write_state(self, state: dict) -> None:
        self.state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

    def _write_doc(self, relative_path: str, content: str) -> None:
        path = self.temp_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_design_document_required_sections_present(self) -> None:
        state = _base_state()
        state["documents"]["DOC-SPEC-P1"] = _document_entry(
            doc_type="design",
            path="docs/superpowers/specs/spec.md",
            required_sections=[
                ("goal", "## 1. 文档目标"),
                ("architecture", "## 5. 系统架构"),
            ],
        )
        self._write_state(state)
        self._write_doc(
            "docs/superpowers/specs/spec.md",
            "# Spec\n\n## 1. 文档目标\n\n说明。\n\n## 5. 系统架构\n\n说明。\n",
        )

        exit_code, payload = self._run_cli("evaluate-state", "--input", str(self.state_path))
        self.assertEqual(exit_code, 0)
        document = payload["documents"]["DOC-SPEC-P1"]
        self.assertTrue(document["facts"]["section_presence"]["goal"])
        self.assertTrue(document["facts"]["section_presence"]["architecture"])
        self.assertEqual(document["derived"]["missing_required_sections"], [])
        self.assertEqual(document["derived"]["document_blockers"], [])

    def test_plan_document_missing_section_blocks(self) -> None:
        state = _base_state()
        state["documents"]["DOC-PLAN-P1"] = _document_entry(
            doc_type="plan",
            path="docs/superpowers/plans/plan.md",
            required_sections=[
                ("scope", "## 范围说明"),
                ("milestones", "## 二级任务分解与执行顺序"),
            ],
        )
        self._write_state(state)
        self._write_doc(
            "docs/superpowers/plans/plan.md",
            "# Plan\n\n## 范围说明\n\n说明。\n",
        )

        exit_code, payload = self._run_cli("evaluate-state", "--input", str(self.state_path))
        self.assertEqual(exit_code, 0)
        blockers = payload["documents"]["DOC-PLAN-P1"]["derived"]["document_blockers"]
        self.assertTrue(
            any(item["reason_code"] == "missing_required_section" for item in blockers)
        )
        self.assertEqual(
            payload["documents"]["DOC-PLAN-P1"]["derived"]["missing_required_sections"],
            ["milestones"],
        )

    def test_document_relation_refs_detected(self) -> None:
        state = _base_state()
        state["documents"]["DOC-SPEC-P1"] = _document_entry(
            doc_type="design",
            path="docs/superpowers/specs/spec.md",
            required_sections=[
                ("goal", "## 1. 文档目标"),
            ],
            relations={
                "document_refs": ["DOC-PLAN-P1"],
                "module_refs": ["M02"],
                "oq_refs": ["OQ-004"],
            },
        )
        state["documents"]["DOC-PLAN-P1"] = _document_entry(
            doc_type="plan",
            path="docs/superpowers/plans/plan.md",
            required_sections=[
                ("scope", "## 范围说明"),
            ],
        )
        self._write_state(state)
        self._write_doc(
            "docs/superpowers/specs/spec.md",
            "# Spec\n\n## 1. 文档目标\n\n依赖 `M02`，需与 `OQ-004` 对齐。\n\n另见 `docs/superpowers/plans/plan.md`。\n",
        )
        self._write_doc(
            "docs/superpowers/plans/plan.md",
            "# Plan\n\n## 范围说明\n\n说明。\n",
        )

        exit_code, payload = self._run_cli("evaluate-state", "--input", str(self.state_path))
        self.assertEqual(exit_code, 0)
        document = payload["documents"]["DOC-SPEC-P1"]
        self.assertEqual(document["facts"]["extracted_refs"]["document_refs"], ["DOC-PLAN-P1"])
        self.assertEqual(document["facts"]["extracted_refs"]["module_refs"], ["M02"])
        self.assertEqual(document["facts"]["extracted_refs"]["oq_refs"], ["OQ-004"])
        self.assertEqual(document["derived"]["missing_relation_refs"], [])

    def test_document_repo_truth_mismatch_blocks_stale_target(self) -> None:
        state = _base_state()
        state["documents"]["DOC-PLAN-P1"] = _document_entry(
            doc_type="plan",
            path="docs/superpowers/plans/plan.md",
            required_sections=[
                ("scope", "## Scope"),
            ],
        )
        self._write_state(state)
        self._write_doc(
            "docs/superpowers/plans/plan.md",
            (
                "# Plan\n\n"
                "## Scope\n\n"
                "Current implementation still targets `apps/api/app/main.py` and "
                "`apps/web/src/app/page.tsx` in a monorepo layout.\n"
            ),
        )

        exit_code, payload = self._run_cli("evaluate-state", "--input", str(self.state_path))
        self.assertEqual(exit_code, 0)
        document = payload["documents"]["DOC-PLAN-P1"]
        blocker_codes = {item["reason_code"] for item in document["derived"]["document_blockers"]}
        self.assertIn("document_repo_truth_mismatch", blocker_codes)
        self.assertEqual(
            document["facts"]["repo_truth"]["missing_paths"],
            ["apps/api/app/main.py", "apps/web/src/app/page.tsx"],
        )
        self.assertEqual(
            document["facts"]["direction_drift"]["future_blueprint_terms"],
            ["apps/api", "apps/web", "monorepo"],
        )
        self.assertFalse(document["derived"]["assessed_ready"])


if __name__ == "__main__":
    unittest.main()
