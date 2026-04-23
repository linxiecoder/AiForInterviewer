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


def _build_bootstrap_state() -> dict:
    module_docs = {slot: {"exists": True, "template_like": False} for slot in schema.MODULE_DOC_SLOTS}
    subtask_docs = {"design_doc": {"exists": True, "template_like": False}, "implementation_doc": {"exists": True, "template_like": False}}

    return {
        "schema_version": schema.SCHEMA_VERSION,
        "global_policy": {
            "auto_open_enabled": False,
            "require_confirmation_for_state_writeback": True,
            "strict_template_gate": True,
            "formal_window_open": True,
            "paths": {
                "modules_root": "docs/modules",
                "open_questions_doc": "OPEN_QUESTIONS.md",
                "task_index_doc": "TASK_INDEX.md",
            },
        },
        "oqs": {
            "OQ-01": {
                "title": "explicit policy",
                "status": "open",
                "affects": {"kind": "module", "ids": ["M01"]},
                "gate_level": "observe_only",
                "resolution_policy": "proposed_default_ok",
                "gate_policy_source": schema.OQ_POLICY_SOURCE_EXPLICIT,
            },
            "OQ-02": {
                "title": "bootstrap default",
                "status": "open",
                "affects": {"kind": "subtask", "ids": ["ST01_01"]},
                "gate_level": "observe_only",
                "resolution_policy": "proposed_default_ok",
                "gate_policy_source": schema.OQ_POLICY_SOURCE_BOOTSTRAP_DEFAULT,
            },
        },
        "modules": {
            "M01": {
                "meta": {"path": "docs/modules/M01-test/"},
                "facts": {
                    "upstream_module_ids": [],
                    "related_oq_ids": ["OQ-01", "OQ-02"],
                    "legacy_locked": False,
                    "declared_blocker_refs": [],
                    "docs": module_docs,
                    "recommended_note": "from prose",
                    "derived_cache": {"ok": True},
                    "summary": {"total": 1},
                },
                "state": {
                    "confirmed": {
                        "maturity": None,
                        "candidate_status": "none",
                        "review_status": "unreviewed",
                        "readiness": "blocked",
                        "blocker_refs": ["oq:OQ-01"],
                        "implementation_doc_state": "active_working_doc",
                        "last_transition_id": "abc",
                        "last_confirmed_at": "now",
                        "last_confirmed_by": "system",
                    }
                },
            }
        },
        "subtasks": {
            "ST01_01": {
                "meta": {"module_id": "M01", "path": "docs/modules/M01/sub_modules/ST01_01-test/"},
                "facts": {
                    "upstream_module_ids": [],
                    "related_oq_ids": ["OQ-02"],
                    "legacy_locked": False,
                    "declared_blocker_refs": [],
                    "design_doc": subtask_docs["design_doc"],
                    "implementation_doc": subtask_docs["implementation_doc"],
                    "computed_flag": True,
                    "derived_something": {},
                },
                "state": {
                    "confirmed": {
                        "implementation_doc_state": "active_working_doc",
                        "maturity": None,
                        "candidate_status": "none",
                        "review_status": "unreviewed",
                        "readiness": "blocked",
                        "blocker_refs": ["oq:OQ-02"],
                        "last_transition_id": "abc",
                        "last_confirmed_at": "now",
                        "last_confirmed_by": "system",
                    }
                },
            }
        },
    }


class InitOfficialStateTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "init-state"

    def setUp(self) -> None:
        super().setUp()
        self.docs_root = self.temp_root / "docs" / "governance"
        self.docs_root.mkdir(parents=True, exist_ok=True)
        self.bootstrap_path = self.docs_root / "DOC_STATE.bootstrap.yaml"
        self.official_path = self.docs_root / "DOC_STATE.yaml"
        self.bootstrap_path.write_text(
            yaml.safe_dump(_build_bootstrap_state(), sort_keys=False),
            encoding="utf-8",
        )

    def _run_cli(self, *args: str) -> tuple[int, dict]:
        original = Path.cwd()
        os.chdir(self.temp_root)
        try:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["init-official-state", *args])
            payload = json.loads(stdout.getvalue())
            return exit_code, payload
        finally:
            os.chdir(original)

    def _read_official(self) -> dict:
        return yaml.safe_load(self.official_path.read_text(encoding="utf-8"))

    def test_init_official_state_dry_run_does_not_write(self) -> None:
        exit_code, payload = self._run_cli("--dry-run")
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertFalse(self.official_path.exists())
        self.assertEqual(payload.get("dry_run"), True)

    def test_init_official_state_success_writes_file(self) -> None:
        exit_code, _payload = self._run_cli("--actor", "alice", "--reason", "seed")
        self.assertEqual(exit_code, 0)
        self.assertTrue(self.official_path.exists())
        official = self._read_official()
        self.assertEqual(official["schema_version"], schema.SCHEMA_VERSION)
        self.assertIn("global_policy", official)
        self.assertIn("oqs", official)
        self.assertIn("modules", official)
        self.assertIn("subtasks", official)
        self.assertEqual(official["modules"]["M01"]["state"]["confirmed"]["candidate_status"], "none")
        self.assertIsNone(official["modules"]["M01"]["state"]["confirmed"]["maturity"])
        self.assertEqual(
            official["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"],
            "missing",
        )
        self.assertIsNone(official["subtasks"]["ST01_01"]["state"]["confirmed"]["maturity"])

    def test_existing_official_state_fails_without_force(self) -> None:
        self.official_path.write_text("manual-state", encoding="utf-8")
        exit_code, payload = self._run_cli()
        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["diagnostics"][0]["code"], "INIT_OFFICIAL_STATE_EXISTS")
        self.assertEqual(self.official_path.read_text(encoding="utf-8"), "manual-state")

    def test_oq_gate_policy_source_preserved(self) -> None:
        exit_code, _payload = self._run_cli()
        self.assertEqual(exit_code, 0)
        official = self._read_official()
        self.assertEqual(
            official["oqs"]["OQ-01"]["gate_policy_source"],
            schema.OQ_POLICY_SOURCE_EXPLICIT,
        )
        self.assertEqual(
            official["oqs"]["OQ-02"]["gate_policy_source"],
            schema.OQ_POLICY_SOURCE_BOOTSTRAP_DEFAULT,
        )

    def test_no_report_only_fields_imported(self) -> None:
        exit_code, _payload = self._run_cli()
        self.assertEqual(exit_code, 0)
        official = self._read_official()
        module_facts = official["modules"]["M01"]["facts"]
        subtask_facts = official["subtasks"]["ST01_01"]["facts"]
        self.assertNotIn("recommended_note", module_facts)
        self.assertNotIn("derived_cache", module_facts)
        self.assertNotIn("summary", module_facts)
        self.assertNotIn("computed_flag", subtask_facts)
        self.assertNotIn("derived_something", subtask_facts)

    def test_bootstrap_default_policy_not_used_as_confirmed_truth(self) -> None:
        exit_code, _payload = self._run_cli()
        self.assertEqual(exit_code, 0)
        official = self._read_official()
        self.assertEqual(
            official["subtasks"]["ST01_01"]["state"]["confirmed"]["readiness"],
            "blocked",
        )
        self.assertEqual(
            official["subtasks"]["ST01_01"]["state"]["confirmed"]["candidate_status"],
            "none",
        )
        self.assertEqual(
            official["subtasks"]["ST01_01"]["state"]["confirmed"]["review_status"],
            "unreviewed",
        )

    def test_confirm_transition_precondition_after_init(self) -> None:
        exit_code, _payload = self._run_cli()
        self.assertEqual(exit_code, 0)

        original = Path.cwd()
        os.chdir(self.temp_root)
        try:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                confirm_code = main(
                    [
                        "confirm-transition",
                        "--entity-type",
                        "module",
                        "--entity-id",
                        "M01",
                        "--proposed-changes",
                        json.dumps({"review_status": "unreviewed"}),
                        "--mode",
                        "dry-run",
                    ]
                )
            confirm_payload = json.loads(stdout.getvalue())
        finally:
            os.chdir(original)
        self.assertEqual(confirm_code, 0)
        self.assertTrue(confirm_payload["ok"])
        self.assertEqual(confirm_payload["entity_type"], "module")


if __name__ == "__main__":
    unittest.main()
