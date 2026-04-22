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


def _base_docs() -> dict[str, dict[str, bool]]:
    return {name: {"exists": True, "template_like": False} for name in schema.MODULE_DOC_SLOTS}


def _default_state() -> dict:
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
        "oqs": {},
        "modules": {},
        "subtasks": {},
    }


def _module_entry(module_id: str, readiness: str = "downstream_ready") -> dict:
    confirmed = schema.make_default_confirmed_state("module")
    confirmed["readiness"] = readiness
    return {
        "meta": {"path": f"docs/modules/{module_id}-test/"},
        "facts": {
            "upstream_module_ids": [],
            "related_oq_ids": [],
            "legacy_locked": False,
            "declared_blocker_refs": [],
            "docs": _base_docs(),
        },
        "state": {"confirmed": confirmed},
    }


def _subtask_entry(
    subtask_id: str,
    module_id: str,
    readiness: str = "downstream_ready",
    implementation_state: str = "active_working_doc",
) -> dict:
    confirmed = schema.make_default_confirmed_state("subtask")
    confirmed["readiness"] = readiness
    confirmed["implementation_doc_state"] = implementation_state
    return {
        "meta": {"module_id": module_id, "path": f"docs/modules/{module_id}/sub_modules/{subtask_id}-test/"},
        "facts": {
            "upstream_module_ids": [],
            "related_oq_ids": [],
            "legacy_locked": False,
            "declared_blocker_refs": [],
            "design_doc": {"exists": True, "template_like": False},
            "implementation_doc": {"exists": True, "template_like": False},
        },
        "state": {"confirmed": confirmed},
    }


class OpenWindowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root = Path(tempfile.gettempdir()) / f"doc-governor-open-window-{uuid.uuid4().hex}"
        self.temp_root.mkdir(exist_ok=True)
        self.governance_root = self.temp_root / "docs" / "governance"
        self.governance_root.mkdir(parents=True, exist_ok=True)
        self.state_path = self.governance_root / "DOC_STATE.yaml"
        self.bootstrap_path = self.governance_root / "DOC_STATE.bootstrap.yaml"
        self.history_path = self.governance_root / "transition_history.jsonl"

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def _write_state(self, state: dict) -> None:
        self.state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

    def _run_cli(self, *args: str) -> tuple[int, dict]:
        original = Path.cwd()
        os.chdir(self.temp_root)
        try:
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(["open-window", *args])
            payload = json.loads(output.getvalue())
            return exit_code, payload
        finally:
            os.chdir(original)

    def _read_state(self) -> dict:
        return yaml.safe_load(self.state_path.read_text(encoding="utf-8"))

    def test_single_entity_minimal_success(self) -> None:
        state = _default_state()
        state["modules"]["M01"] = _module_entry("M01")
        state["modules"]["M01"]["state"]["confirmed"]["candidate_status"] = "none"
        self._write_state(state)
        self.bootstrap_path.write_text("bootstrap", encoding="utf-8")
        before_bootstrap = self.bootstrap_path.read_text(encoding="utf-8")

        exit_code, payload = self._run_cli(
            "--state", str(self.state_path),
            "--history", str(self.history_path),
            "--entity-type", "module",
            "--entity-id", "M01",
            "--mode", "apply",
            "--actor", "alice",
            "--reason", "manual open",
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["mode"], "apply")

        state_data = self._read_state()
        confirmed = state_data["modules"]["M01"]["state"]["confirmed"]
        self.assertEqual(confirmed["window_status"], "open")
        self.assertEqual(confirmed["window_opened_by"], "alice")
        self.assertEqual(confirmed["window_reason"], "manual open")
        self.assertIsNotNone(confirmed["window_opened_at"])
        self.assertEqual(confirmed["candidate_status"], "none")
        self.assertEqual(confirmed["readiness"], "downstream_ready")

        self.assertTrue(self.history_path.exists())
        history_line = self.history_path.read_text(encoding="utf-8").strip().splitlines()[-1]
        history = json.loads(history_line)
        self.assertEqual(history["action"], "open-window")
        self.assertEqual(history["source"], "preflight")
        self.assertEqual(history["entity_type"], "module")
        self.assertEqual(history["entity_id"], "M01")
        self.assertEqual(history["before_state"]["window_status"], "closed")
        self.assertEqual(history["applied_state"]["window_status"], "open")

        self.assertEqual(before_bootstrap, self.bootstrap_path.read_text(encoding="utf-8"))

    def test_apply_blocked_entity_fails(self) -> None:
        state = _default_state()
        blocked_module = _module_entry("M01", readiness="blocked")
        state["modules"]["M01"] = blocked_module
        self._write_state(state)

        before_state = self.state_path.read_bytes()
        exit_code, payload = self._run_cli(
            "--state", str(self.state_path),
            "--history", str(self.history_path),
            "--entity-type", "module",
            "--entity-id", "M01",
            "--mode", "apply",
            "--actor", "alice",
            "--reason", "manual open",
        )
        self.assertEqual(exit_code, 1)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["diagnostics"][0]["code"], "OPEN_WINDOW_ENTITY_BLOCKED")
        self.assertEqual(payload["preflight"]["summary"]["blocked_count"], 1)
        self.assertEqual(before_state, self.state_path.read_bytes())
        self.assertFalse(self.history_path.exists())

    def test_apply_review_required_unconfirmed_entity_fails(self) -> None:
        state = _default_state()
        state["oqs"] = {
            "OQ-01": {
                "title": "Review required by policy",
                "status": "open",
                "gate_level": "observe_only",
                "resolution_policy": "proposed_default_ok",
                "affects": {"kind": "module", "ids": ["M01"]},
            }
        }
        state["modules"]["M01"] = _module_entry("M01")
        state["modules"]["M01"]["facts"]["related_oq_ids"] = ["OQ-01"]
        self._write_state(state)

        before_state = self.state_path.read_bytes()
        exit_code, payload = self._run_cli(
            "--state", str(self.state_path),
            "--history", str(self.history_path),
            "--entity-type", "module",
            "--entity-id", "M01",
            "--mode", "apply",
            "--actor", "alice",
            "--reason", "manual open",
        )
        self.assertEqual(exit_code, 1)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["diagnostics"][0]["code"], "OPEN_WINDOW_REVIEW_REQUIRED_UNCONFIRMED")
        self.assertEqual(before_state, self.state_path.read_bytes())
        self.assertFalse(self.history_path.exists())

    def test_bootstrap_default_oq_policy_cannot_auto_open(self) -> None:
        state = _default_state()
        state["oqs"] = {
            "OQ-01": {
                "title": "Bootstrap default",
                "status": "open",
                "gate_level": "candidate_gate",
                "resolution_policy": "proposed_default_ok",
                "affects": {"kind": "module", "ids": ["M01"]},
                "gate_policy_source": schema.OQ_POLICY_SOURCE_BOOTSTRAP_DEFAULT,
            }
        }
        state["modules"]["M01"] = _module_entry("M01")
        state["modules"]["M01"]["facts"]["related_oq_ids"] = ["OQ-01"]
        self._write_state(state)

        before_state = self.state_path.read_bytes()
        exit_code, payload = self._run_cli(
            "--state", str(self.state_path),
            "--history", str(self.history_path),
            "--entity-type", "module",
            "--entity-id", "M01",
            "--mode", "apply",
            "--actor", "alice",
            "--reason", "manual open",
        )
        self.assertEqual(exit_code, 1)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["diagnostics"][0]["code"], "OPEN_WINDOW_ENTITY_BLOCKED")
        self.assertFalse(payload["preflight"]["summary"]["eligible_count"])
        self.assertFalse(payload["preflight"]["summary"]["blocked_count"] == 0)
        self.assertEqual(before_state, self.state_path.read_bytes())
        self.assertFalse(self.history_path.exists())

    def test_dry_run_does_not_write_files(self) -> None:
        state = _default_state()
        state["modules"]["M01"] = _module_entry("M01")
        self._write_state(state)
        self.bootstrap_path.write_text("bootstrap", encoding="utf-8")
        before_state = self.state_path.read_bytes()
        before_bootstrap = self.bootstrap_path.read_bytes()

        exit_code, payload = self._run_cli(
            "--state", str(self.state_path),
            "--history", str(self.history_path),
            "--entity-type", "module",
            "--entity-id", "M01",
            "--mode", "dry-run",
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertFalse(self.history_path.exists())
        self.assertEqual(payload["would_apply"], True)
        self.assertEqual(payload["mode"], "dry-run")
        self.assertEqual(before_state, self.state_path.read_bytes())
        self.assertEqual(before_bootstrap, self.bootstrap_path.read_bytes())

    def test_apply_only_changes_window_fields(self) -> None:
        state = _default_state()
        module = _module_entry("M01")
        module["state"]["confirmed"]["candidate_status"] = "candidate"
        module["state"]["confirmed"]["review_status"] = "approved"
        module["state"]["confirmed"]["readiness"] = "implementation_ready"
        module["state"]["confirmed"]["maturity"] = "L6"
        state["modules"]["M01"] = module
        self._write_state(state)

        exit_code, _ = self._run_cli(
            "--state", str(self.state_path),
            "--history", str(self.history_path),
            "--entity-type", "module",
            "--entity-id", "M01",
            "--mode", "apply",
            "--actor", "alice",
            "--reason", "only window control",
        )
        self.assertEqual(exit_code, 0)

        confirmed = self._read_state()["modules"]["M01"]["state"]["confirmed"]
        self.assertEqual(confirmed["window_status"], "open")
        self.assertEqual(confirmed["candidate_status"], "candidate")
        self.assertEqual(confirmed["review_status"], "approved")
        self.assertEqual(confirmed["readiness"], "implementation_ready")
        self.assertEqual(confirmed["maturity"], "L6")

    def test_open_window_does_not_modify_bootstrap_state_file(self) -> None:
        state = _default_state()
        state["modules"]["M01"] = _module_entry("M01")
        self._write_state(state)
        self.bootstrap_path.write_text("bootstrap-content", encoding="utf-8")

        before_bootstrap = self.bootstrap_path.read_bytes()
        exit_code, _ = self._run_cli(
            "--state", str(self.state_path),
            "--history", str(self.history_path),
            "--entity-type", "module",
            "--entity-id", "M01",
            "--mode", "apply",
            "--actor", "alice",
            "--reason", "without touching bootstrap",
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(before_bootstrap, self.bootstrap_path.read_bytes())

    def test_already_open_entity_apply_fails_with_WINDOW_ALREADY_OPEN(self) -> None:
        state = _default_state()
        state["modules"]["M01"] = _module_entry("M01")
        self._write_state(state)

        first_exit_code, _ = self._run_cli(
            "--state", str(self.state_path),
            "--history", str(self.history_path),
            "--entity-type", "module",
            "--entity-id", "M01",
            "--mode", "apply",
            "--actor", "alice",
            "--reason", "first open",
        )
        self.assertEqual(first_exit_code, 0)
        before_second = self.state_path.read_text(encoding="utf-8")
        before_history_lines = self.history_path.read_text(encoding="utf-8").splitlines()

        second_exit_code, payload = self._run_cli(
            "--state", str(self.state_path),
            "--history", str(self.history_path),
            "--entity-type", "module",
            "--entity-id", "M01",
            "--mode", "apply",
            "--actor", "alice",
            "--reason", "second open",
        )
        self.assertEqual(second_exit_code, 1)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["diagnostics"][0]["code"], "WINDOW_ALREADY_OPEN")
        self.assertEqual(before_second, self.state_path.read_text(encoding="utf-8"))
        self.assertEqual(len(before_history_lines), len(self.history_path.read_text(encoding="utf-8").splitlines()))

    def test_history_append_record_action_open_window(self) -> None:
        state = _default_state()
        state["subtasks"]["ST01_01"] = _subtask_entry("ST01_01", "M01")
        self._write_state(state)

        exit_code, _ = self._run_cli(
            "--state", str(self.state_path),
            "--history", str(self.history_path),
            "--entity-type", "subtask",
            "--entity-id", "ST01_01",
            "--mode", "apply",
            "--actor", "bob",
            "--reason", "subtask open",
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(self.history_path.exists())

        history = json.loads(self.history_path.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(history["action"], "open-window")
        self.assertIn("source", history)
        self.assertEqual(history["source"], "preflight")
        self.assertEqual(history["actor"], "bob")
        self.assertEqual(history["changed_fields"], [
            "window_status",
            "window_opened_at",
            "window_opened_by",
            "window_reason",
        ])
        self.assertEqual(history["before_state"]["window_status"], "closed")
        self.assertEqual(history["applied_state"]["window_status"], "open")


if __name__ == "__main__":
    unittest.main()
