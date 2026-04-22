import io
import json
import shutil
import tempfile
import unittest
import uuid
from contextlib import redirect_stdout
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.cli import main


FIXTURES_REPO = Path(__file__).parent / "fixtures" / "repo" / "prose_contamination"


def _base_state() -> dict:
    module_docs = {
        slot: {"exists": True, "template_like": False}
        for slot in schema.MODULE_DOC_SLOTS
    }
    subtask_state = schema.make_default_confirmed_state("subtask")
    subtask_state["implementation_doc_state"] = "active_working_doc"
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


def _module_entry(module_id: str) -> dict:
    module_docs = {
        slot: {"exists": True, "template_like": False} for slot in schema.MODULE_DOC_SLOTS
    }
    return {
        "meta": {"path": f"docs/modules/{module_id}-name/"},
        "facts": {
            "upstream_module_ids": [],
            "related_oq_ids": [],
            "legacy_locked": False,
            "declared_blocker_refs": [],
            "docs": module_docs,
        },
        "state": {"confirmed": schema.make_default_confirmed_state("module")},
    }


def _subtask_entry(subtask_id: str, module_id: str) -> dict:
    return {
        "meta": {"module_id": module_id, "path": f"docs/modules/{module_id}/sub_modules/{subtask_id}-name/"},
        "facts": {
            "upstream_module_ids": [module_id],
            "related_oq_ids": [],
            "legacy_locked": False,
            "declared_blocker_refs": [],
            "design_doc": {"exists": True, "template_like": False},
            "implementation_doc": {"exists": True, "template_like": False},
        },
        "state": {"confirmed": schema.make_default_confirmed_state("subtask")},
    }


def _subtask_implementation_missing_entry(subtask_id: str, module_id: str) -> dict:
    entry = _subtask_entry(subtask_id, module_id)
    entry["facts"]["implementation_doc"] = {"exists": False, "template_like": False}
    return entry


def _write_state(state: dict, root: Path) -> Path:
    path = root / "DOC_STATE.bootstrap.yaml"
    path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
    return path


class EvaluateStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root = Path(tempfile.gettempdir()) / f"doc-governor-eval-{uuid.uuid4().hex}"
        self.temp_root.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def run_cli(self, *args: str) -> tuple[int, dict]:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(list(args))
        payload = json.loads(stdout.getvalue())
        return exit_code, payload

    def test_gate_level_and_resolution_policy_matrix(self) -> None:
        state = _base_state()
        state["oqs"] = {
            "OQ-01": {
                "title": "observe-review",
                "status": "open",
                "gate_level": "observe_only",
                "resolution_policy": "proposed_default_ok",
                "affects": {"kind": "module", "ids": ["M01"]},
            },
            "OQ-02": {
                "title": "candidate-review-1",
                "status": "proposed-default",
                "gate_level": "candidate_gate",
                "resolution_policy": "proposed_default_ok",
                "affects": {"kind": "subtask", "ids": ["ST01_01"]},
            },
            "OQ-03": {
                "title": "candidate-review-2",
                "status": "open",
                "gate_level": "candidate_gate",
                "resolution_policy": "confirmed_only",
                "affects": {"kind": "subtask", "ids": ["ST01_01"]},
            },
            "OQ-04": {
                "title": "readiness-block",
                "status": "open",
                "gate_level": "readiness_gate",
                "resolution_policy": "manual_override_only",
                "affects": {"kind": "subtask", "ids": ["ST01_01"]},
            },
        }
        state_path = _write_state(state, self.temp_root)

        exit_code, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        self.assertEqual(exit_code, 0)
        oqs = payload["oqs"]
        self.assertEqual(oqs["OQ-01"]["derived_enforcement"], "review_only")
        self.assertEqual(oqs["OQ-02"]["derived_enforcement"], "review_only")
        self.assertEqual(oqs["OQ-03"]["derived_enforcement"], "candidate_blocker")
        self.assertEqual(oqs["OQ-04"]["derived_enforcement"], "readiness_blocker")
        self.assertEqual(
            payload["summary"]["oq_gate_counts"]["observe_only.review_only"], 1
        )
        self.assertEqual(payload["summary"]["oq_gate_counts"]["candidate_gate.review_only"], 1)
        self.assertEqual(payload["summary"]["oq_gate_counts"]["candidate_gate.candidate_blocker"], 1)
        self.assertEqual(payload["summary"]["oq_gate_counts"]["readiness_gate.readiness_blocker"], 1)

    def test_review_required_truth_table(self) -> None:
        state = _base_state()
        state["modules"] = {
            "M01": _module_entry("M01"),
            "M02": _module_entry("M02"),
        }
        state["subtasks"] = {
            "ST01_01": _subtask_implementation_missing_entry("ST01_01", "M01")
        }
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = "inactive_template"
        state["oqs"] = {
            "OQ-01": {
                "title": "observe-review",
                "status": "open",
                "gate_level": "observe_only",
                "resolution_policy": "proposed_default_ok",
                "affects": {"kind": "module", "ids": ["M01"]},
            }
        }
        state["modules"]["M01"]["facts"]["related_oq_ids"] = ["OQ-01"]
        state["modules"]["M02"]["facts"]["related_oq_ids"] = []
        state["subtasks"]["ST01_01"]["facts"]["related_oq_ids"] = ["OQ-01"]

        state_path = _write_state(state, self.temp_root)
        _, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        modules = payload["modules"]
        subtasks = payload["subtasks"]

        self.assertEqual(modules["M01"]["derived"]["review_reasons"], ["downstream_ready_no_hard_blocker", "oq_review_only"])
        self.assertTrue(modules["M01"]["derived"]["assessed_downstream_ready"])
        self.assertEqual(
            modules["M02"]["derived"]["review_reasons"],
            ["downstream_ready_no_hard_blocker"],
        )

        self.assertEqual(
            subtasks["ST01_01"]["derived"]["review_reasons"],
            ["implementation_doc_activation_recommended", "oq_review_only"],
        )
        self.assertTrue(subtasks["ST01_01"]["derived"]["implementation_doc_activation_recommended"])

    def test_legacy_lock_adds_blockers(self) -> None:
        state = _base_state()
        state["modules"] = {
            "M01": _module_entry("M01"),
        }
        state["subtasks"] = {"ST01_01": _subtask_entry("ST01_01", "M01")}
        state["modules"]["M01"]["facts"]["legacy_locked"] = True
        state["subtasks"]["ST01_01"]["facts"]["legacy_locked"] = True
        state["subtasks"]["ST01_01"]["facts"]["upstream_module_ids"] = []

        state_path = _write_state(state, self.temp_root)
        _, payload = self.run_cli("evaluate-state", "--input", str(state_path))

        module_blockers = payload["modules"]["M01"]["derived"]["downstream_blockers"]
        subtask_blockers = payload["subtasks"]["ST01_01"]["derived"]["downstream_blockers"]
        self.assertTrue(any(item["reason_code"] == "legacy_locked" for item in module_blockers))
        self.assertTrue(any(item["reason_code"] == "legacy_locked" for item in subtask_blockers))

    def test_required_doc_and_template_like_blockers(self) -> None:
        state = _base_state()
        state["modules"] = {"M01": _module_entry("M01")}
        state["modules"]["M01"]["facts"]["docs"]["requirements"]["exists"] = False

        state["subtasks"] = {"ST01_01": _subtask_entry("ST01_01", "M01")}
        state["subtasks"]["ST01_01"]["facts"]["design_doc"]["template_like"] = True

        state_path = _write_state(state, self.temp_root)
        _, payload = self.run_cli("evaluate-state", "--input", str(state_path))

        module_blockers = payload["modules"]["M01"]["derived"]["downstream_blockers"]
        subtask_blockers = payload["subtasks"]["ST01_01"]["derived"]["downstream_blockers"]
        self.assertTrue(any(item["reason_code"] == "missing_required_doc_slot" for item in module_blockers))
        self.assertTrue(
            any(
                item["reason_code"] == "template_like_required_doc_slot"
                for item in subtask_blockers
            )
        )

    def test_upstream_module_blocking_propagates(self) -> None:
        state = _base_state()
        state["modules"] = {"M01": _module_entry("M01"), "M02": _module_entry("M02")}
        state["modules"]["M01"]["facts"]["docs"]["schema"]["exists"] = False
        state["subtasks"] = {"ST01_01": _subtask_entry("ST01_01", "M02")}
        state["subtasks"]["ST01_01"]["facts"]["upstream_module_ids"] = ["M01"]

        state_path = _write_state(state, self.temp_root)
        _, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        blockers = payload["subtasks"]["ST01_01"]["derived"]["downstream_blockers"]
        self.assertTrue(any(item["reason_code"] == "upstream_module_not_ready" for item in blockers))

    def test_implementation_related_blockers(self) -> None:
        state = _base_state()
        state["modules"] = {"M01": _module_entry("M01")}
        state["subtasks"] = {"ST01_01": _subtask_entry("ST01_01", "M01")}
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = "inactive_template"
        state_path = _write_state(state, self.temp_root)

        _, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        blockers = payload["subtasks"]["ST01_01"]["derived"]["implementation_blockers"]
        self.assertTrue(
            any(item["reason_code"] == "implementation_doc_not_active" for item in blockers)
        )

        state["global_policy"]["formal_window_open"] = False
        state_path = _write_state(state, self.temp_root)
        _, payload_closed = self.run_cli("evaluate-state", "--input", str(state_path))
        blockers_closed = payload_closed["subtasks"]["ST01_01"]["derived"]["implementation_blockers"]
        self.assertTrue(
            any(item["reason_code"] == "formal_window_closed" for item in blockers_closed)
        )

    def test_implementation_doc_activation_recommendation(self) -> None:
        state = _base_state()
        state["modules"] = {"M01": _module_entry("M01")}
        state["subtasks"] = {
            "ST01_01": _subtask_entry("ST01_01", "M01"),
            "ST01_02": _subtask_entry("ST01_02", "M01"),
        }
        state["subtasks"]["ST01_01"]["facts"]["implementation_doc"] = {
            "exists": True,
            "template_like": True,
        }
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = (
            "inactive_template"
        )
        state["subtasks"]["ST01_01"]["facts"]["upstream_module_ids"] = []
        state["subtasks"]["ST01_02"]["state"]["confirmed"]["implementation_doc_state"] = (
            "inactive_template"
        )
        state["subtasks"]["ST01_02"]["facts"]["implementation_doc"] = {
            "exists": True,
            "template_like": False,
        }
        state["subtasks"]["ST01_02"]["facts"]["upstream_module_ids"] = []

        state_path = _write_state(state, self.temp_root)
        _, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        self.assertTrue(
            payload["subtasks"]["ST01_01"]["derived"][
                "implementation_doc_activation_recommended"
            ]
        )
        self.assertFalse(
            payload["subtasks"]["ST01_02"]["derived"][
                "implementation_doc_activation_recommended"
            ]
        )

    def test_summary_fields_and_counts(self) -> None:
        state = _base_state()
        state["modules"] = {"M01": _module_entry("M01"), "M02": _module_entry("M02")}
        state["modules"]["M02"]["facts"]["docs"]["requirements"]["exists"] = False

        state["subtasks"] = {
            "ST01_01": _subtask_entry("ST01_01", "M01"),
            "ST01_02": _subtask_implementation_missing_entry("ST01_02", "M01"),
        }
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = (
            "active_working_doc"
        )
        state["subtasks"]["ST01_01"]["facts"]["upstream_module_ids"] = ["M02"]
        state["subtasks"]["ST01_02"]["state"]["confirmed"]["implementation_doc_state"] = (
            "active_working_doc"
        )
        state["subtasks"]["ST01_02"]["facts"]["upstream_module_ids"] = []

        state_path = _write_state(state, self.temp_root)
        _, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        summary = payload["summary"]
        self.assertIn("modules_review_required", summary)
        self.assertIn("subtasks_review_required", summary)
        self.assertIn("modules_blocked_count", summary)
        self.assertIn("subtasks_blocked_count", summary)
        self.assertIn("blocked_by_reason_code", summary)
        self.assertIn("oq_gate_counts", summary)
        self.assertEqual(summary["modules_blocked_count"], 1)
        self.assertEqual(summary["subtasks_blocked_count"], 2)

    def test_evaluate_state_does_not_write_back_state(self) -> None:
        state = _base_state()
        state["modules"] = {"M01": _module_entry("M01")}
        state["subtasks"] = {"ST01_01": _subtask_implementation_missing_entry("ST01_01", "M01")}
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = (
            "inactive_template"
        )
        state["subtasks"]["ST01_01"]["facts"]["upstream_module_ids"] = []
        state["subtasks"]["ST01_01"]["facts"]["implementation_doc"]["exists"] = False
        state["subtasks"]["ST01_01"]["facts"]["implementation_doc"]["template_like"] = False

        state_path = _write_state(state, self.temp_root)
        before = state_path.read_bytes()

        self.run_cli("evaluate-state", "--input", str(state_path))
        after = state_path.read_bytes()
        self.assertEqual(before, after)

    def test_empty_state_is_successful(self) -> None:
        state = _base_state()
        state["modules"] = {}
        state["subtasks"] = {}
        state["oqs"] = {}
        state_path = _write_state(state, self.temp_root)

        exit_code, payload = self.run_cli("evaluate-state", "--input", str(state_path))
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["summary"]["modules_review_required"], 0)
        self.assertEqual(payload["summary"]["subtasks_review_required"], 0)
        self.assertEqual(payload["summary"]["modules_blocked_count"], 0)
        self.assertEqual(payload["summary"]["subtasks_blocked_count"], 0)
        self.assertEqual(payload["modules"], {})
        self.assertEqual(payload["subtasks"], {})

    def test_real_repo_evaluate_summary(self) -> None:
        repo_root = self.temp_root / "real_repo"
        shutil.copytree(FIXTURES_REPO, repo_root)
        exit_code, payload_bootstrap = self.run_cli(
            "bootstrap-state",
            "--repo-root",
            str(repo_root),
            "--overwrite",
        )
        self.assertEqual(exit_code, 0)
        exit_code, payload = self.run_cli(
            "evaluate-state",
            "--input",
            str(repo_root / "docs" / "governance" / "DOC_STATE.bootstrap.yaml"),
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("summary", payload)
        self.assertIn("modules", payload)
        self.assertIn("subtasks", payload)
        self.assertIn("summary", payload)
        self.assertIn("modules_review_required", payload["summary"])
        self.assertIn("subtasks_review_required", payload["summary"])
        self.assertGreaterEqual(payload["summary"]["modules_review_required"], 0)

    def test_evaluate_does_not_apply_oq_defaults(self) -> None:
        state = _base_state()
        state["oqs"] = {
            "OQ-201": {
                "title": "missing policy fields",
                "status": "open",
                "affects": {"modules": ["M01"], "subtasks": []},
            }
        }
        state["modules"] = {"M01": _module_entry("M01")}
        state["subtasks"] = {"ST01_01": _subtask_entry("ST01_01", "M01")}
        state["subtasks"]["ST01_01"]["facts"]["upstream_module_ids"] = []

        state_path = _write_state(state, self.temp_root)
        exit_code, payload = self.run_cli(
            "evaluate-state",
            "--input",
            str(state_path),
        )
        self.assertEqual(exit_code, 1)
        self.assertTrue(
            any(
                item["code"] == "SCHEMA_MISSING_REQUIRED_FIELD"
                and item["field_path"] == "oqs.OQ-201.gate_level"
                for item in payload["diagnostics"]
            )
        )


if __name__ == "__main__":
    unittest.main()
