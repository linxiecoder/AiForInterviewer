import io
import json
import os
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path
from contextlib import redirect_stdout

import yaml

from tools.doc_governor import schema
from tools.doc_governor.cli import main


def _base_confirm_state() -> dict:
    module_docs = {
        slot: {"exists": True, "template_like": False}
        for slot in schema.MODULE_DOC_SLOTS
    }
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
        "requirements": {},
        "modules": {
            "M01": {
                "meta": {"path": "docs/modules/M01-test/"},
                "facts": {
                    "upstream_module_ids": [],
                    "related_oq_ids": [],
                    "legacy_locked": False,
                    "declared_blocker_refs": [],
                    "docs": module_docs,
                },
                "state": {"confirmed": schema.make_default_confirmed_state("module")},
            }
        },
        "subtasks": {
            "ST01_01": {
                "meta": {"module_id": "M01", "path": "docs/modules/M01/sub_modules/ST01_01-test/"},
                "facts": {
                    "upstream_module_ids": [],
                    "related_oq_ids": [],
                    "legacy_locked": False,
                    "declared_blocker_refs": [],
                    "design_doc": {"exists": True, "template_like": False},
                    "implementation_doc": {"exists": True, "template_like": False},
                },
                "state": {"confirmed": schema.make_default_confirmed_state("subtask")},
            }
        },
    }


class ConfirmTransitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root = Path(tempfile.gettempdir()) / f"doc-governor-confirm-{uuid.uuid4().hex}"
        self.temp_root.mkdir(exist_ok=True)
        self.state_dir = self.temp_root / "docs" / "governance"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.state_dir / "DOC_STATE.yaml"
        self.bootstrap_path = self.state_dir / "DOC_STATE.bootstrap.yaml"
        self.history_path = self.state_dir / "transition_history.jsonl"
        self._write_state(_base_confirm_state())

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def _write_state(self, state: dict) -> None:
        self.state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

    def _read_state(self) -> dict:
        return yaml.safe_load(self.state_path.read_text(encoding="utf-8"))

    def _write_round_template(self, round_id: str, *, content: str | None = None) -> Path:
        rounds_dir = self.temp_root / "docs" / "governance" / "rounds"
        rounds_dir.mkdir(parents=True, exist_ok=True)
        round_path = rounds_dir / f"{round_id}.md"
        round_path.write_text(content or f"# Round\n\nDecision: summary\n", encoding="utf-8")
        return round_path

    def _run_cli(self, *args: str) -> tuple[int, dict]:
        original = Path.cwd()
        os.chdir(self.temp_root)
        try:
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(["confirm-transition", *args])
            payload = json.loads(output.getvalue())
            return exit_code, payload
        finally:
            os.chdir(original)

    def test_official_state_missing_fails(self) -> None:
        self.state_path.unlink()
        exit_code, payload = self._run_cli(
            "--entity-type",
            "module",
            "--entity-id",
            "M01",
            "--proposed-changes",
            json.dumps({"review_status": "unreviewed"}),
            "--mode",
            "dry-run",
        )
        self.assertEqual(exit_code, 1)
        self.assertTrue(payload["diagnostics"])
        self.assertEqual(payload["diagnostics"][0]["code"], "SCHEMA_MISSING_REQUIRED_FIELD")

    def test_dry_run_does_not_write_state_or_history(self) -> None:
        before_state = self.state_path.read_text(encoding="utf-8")
        exit_code, payload = self._run_cli(
            "--entity-type",
            "subtask",
            "--entity-id",
            "ST01_01",
            "--proposed-changes",
            json.dumps(
                {
                    "candidate_status": "candidate",
                    "review_status": "pending_confirmation",
                }
            ),
            "--evidence-ref",
            "oq:OQ-01",
            "--mode",
            "dry-run",
        )
        self.assertEqual(exit_code, 0)
        self.assertFalse(self.history_path.exists())
        self.assertEqual(before_state, self.state_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["mode"], "dry-run")
        self.assertTrue(payload["ok"])

    def test_approve_updates_state_and_appends_history(self) -> None:
        exit_code, payload = self._run_cli(
            "--entity-type",
            "subtask",
            "--entity-id",
            "ST01_01",
            "--proposed-changes",
            json.dumps(
                {
                    "candidate_status": "candidate",
                    "review_status": "pending_confirmation",
                }
            ),
            "--evidence-ref",
            "oq:OQ-01",
            "--mode",
            "approve",
            "--actor",
            "alice",
            "--reason",
            "advance candidate",
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(self.history_path.exists())
        history_line = self.history_path.read_text(encoding="utf-8").strip().splitlines()[-1]
        history = json.loads(history_line)
        self.assertEqual(history["entity_type"], "subtask")
        self.assertEqual(history["entity_id"], "ST01_01")
        self.assertIsNone(history["round_id"])
        self.assertFalse(history["dry_run"])
        self.assertIn("transition_id", history)
        self.assertIn("transition_id", payload)
        self.assertEqual(payload["changed_fields"], history["changed_fields"])

        state = self._read_state()
        confirmed = state["subtasks"]["ST01_01"]["state"]["confirmed"]
        self.assertEqual(confirmed["candidate_status"], "candidate")
        self.assertEqual(confirmed["review_status"], "pending_confirmation")
        self.assertEqual(confirmed["last_confirmed_by"], "alice")
        self.assertIsNotNone(confirmed["last_transition_id"])
        self.assertIsNotNone(confirmed["last_confirmed_at"])
        self.assertEqual(history["applied_state"]["last_confirmed_by"], "alice")

    def test_approve_with_round_id_appends_history_round_reference(self) -> None:
        self._write_round_template("R-2026-04-01")
        exit_code, _payload = self._run_cli(
            "--entity-type",
            "subtask",
            "--entity-id",
            "ST01_01",
            "--proposed-changes",
            json.dumps(
                {
                    "candidate_status": "candidate",
                    "review_status": "pending_confirmation",
                }
            ),
            "--evidence-ref",
            "oq:OQ-01",
            "--mode",
            "approve",
            "--actor",
            "alice",
            "--reason",
            "Decision: advance candidate",
            "--round-id",
            "R-2026-04-01",
        )
        self.assertEqual(exit_code, 0)
        history_line = self.history_path.read_text(encoding="utf-8").strip().splitlines()[-1]
        history = json.loads(history_line)
        self.assertEqual(history["round_id"], "R-2026-04-01")

    def test_reject_writes_history_only(self) -> None:
        before = self._read_state()
        exit_code, payload = self._run_cli(
            "--entity-type",
            "subtask",
            "--entity-id",
            "ST01_01",
            "--proposed-changes",
            json.dumps(
                {
                    "readiness": "not_ready",
                    "candidate_status": "candidate",
                    "review_status": "pending_confirmation",
                }
            ),
            "--evidence-ref",
            "oq:OQ-01",
            "--mode",
            "reject",
            "--actor",
            "alice",
            "--reason",
            "not ready",
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["mode"] == "reject")
        self.assertTrue(payload["ok"])
        self.assertTrue(self.history_path.exists())
        history = json.loads(self.history_path.read_text(encoding="utf-8").strip().splitlines()[-1])
        self.assertTrue(history["dry_run"] is False)
        self.assertEqual(history["applied_state"], before["subtasks"]["ST01_01"]["state"]["confirmed"])
        after = self._read_state()
        self.assertEqual(after["subtasks"]["ST01_01"]["state"]["confirmed"], before["subtasks"]["ST01_01"]["state"]["confirmed"])

    def test_forbidden_system_fields_rejected(self) -> None:
        exit_code, payload = self._run_cli(
            "--entity-type",
            "module",
            "--entity-id",
            "M01",
            "--proposed-changes",
            json.dumps({"last_confirmed_by": "alice"}),
            "--mode",
            "dry-run",
        )
        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["diagnostics"][0]["code"], "CONFIRM_FORBIDDEN_PROPOSED_CHANGE")

    def test_invalid_state_machine_change_rejected(self) -> None:
        exit_code, payload = self._run_cli(
            "--entity-type",
            "subtask",
            "--entity-id",
            "ST01_01",
            "--proposed-changes",
            json.dumps(
                {
                    "candidate_status": "candidate",
                    "review_status": "approved",
                }
            ),
            "--evidence-ref",
            "oq:OQ-01",
            "--mode",
            "dry-run",
        )
        self.assertEqual(exit_code, 1)
        self.assertIn(
            "RULE_ILLEGAL_STATE_COMBINATION",
            {item["code"] for item in payload["diagnostics"]},
        )

    def test_candidate_promotion_requires_evidence(self) -> None:
        exit_code, payload = self._run_cli(
            "--entity-type",
            "subtask",
            "--entity-id",
            "ST01_01",
            "--proposed-changes",
            json.dumps(
                {
                    "candidate_status": "candidate",
                    "review_status": "pending_confirmation",
                }
            ),
            "--mode",
            "approve",
            "--actor",
            "alice",
            "--reason",
            "missing evidence",
        )
        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["diagnostics"][0]["code"], "CONFIRM_EVIDENCE_REQUIRED")

    def test_group_change_constraint_missing_review(self) -> None:
        exit_code, payload = self._run_cli(
            "--entity-type",
            "subtask",
            "--entity-id",
            "ST01_01",
            "--proposed-changes",
            json.dumps({"candidate_status": "candidate"}),
            "--evidence-ref",
            "oq:OQ-01",
            "--mode",
            "dry-run",
        )
        self.assertEqual(exit_code, 1)
        self.assertIn(
            "RULE_ILLEGAL_STATE_COMBINATION",
            {item["code"] for item in payload["diagnostics"]},
        )

    def test_input_bootstrap_state_is_forbidden(self) -> None:
        self.bootstrap_path.write_text("bootstrap-content", encoding="utf-8")
        exit_code, payload = self._run_cli(
            "--input",
            str(self.bootstrap_path),
            "--entity-type",
            "module",
            "--entity-id",
            "M01",
            "--proposed-changes",
            json.dumps({"review_status": "unreviewed"}),
            "--mode",
            "dry-run",
        )
        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["diagnostics"][0]["code"], "CONFIRM_STATE_PATH_FORBIDDEN")
        self.assertEqual(self.bootstrap_path.read_text(encoding="utf-8"), "bootstrap-content")

    def test_bootstrap_default_oq_source_blocks_approve(self) -> None:
        state = self._read_state()
        state["oqs"] = {
            "OQ-01": {
                "title": "bootstrap default candidate gate",
                "status": "open",
                "gate_level": "candidate_gate",
                "resolution_policy": "proposed_default_ok",
                "affects": {"kind": "subtask", "ids": ["ST01_01"]},
                "gate_policy_source": schema.OQ_POLICY_SOURCE_BOOTSTRAP_DEFAULT,
            }
        }
        state["subtasks"]["ST01_01"]["facts"]["related_oq_ids"] = ["OQ-01"]
        self._write_state(state)

        exit_code, payload = self._run_cli(
            "--entity-type",
            "subtask",
            "--entity-id",
            "ST01_01",
            "--proposed-changes",
            json.dumps(
                {
                    "candidate_status": "candidate",
                    "review_status": "pending_confirmation",
                }
            ),
            "--evidence-ref",
            "oq:OQ-01",
            "--mode",
            "approve",
            "--actor",
            "alice",
            "--reason",
            "promote candidate",
        )
        self.assertEqual(exit_code, 1)
        self.assertIn(
            "CONFIRM_BOOTSTRAP_DEFAULT_OQ_POLICY_BLOCKS_APPROVE",
            [item["code"] for item in payload["diagnostics"]],
        )

    def test_approve_rejects_when_requirement_asset_blocker_unresolved(self) -> None:
        state = self._read_state()
        state["requirements"] = {
            "RQ01": {
                "meta": {"path": ".", "scope_kind": "root_requirement_cluster"},
                "facts": {
                    "module_ids": ["M01"],
                    "task_ids": [],
                    "asset_slots": {
                        "plan_latest": {"exists": False, "path": "PLAN_LATEST.md"},
                        "module_index": {"exists": True, "path": "MODULE_INDEX.md"},
                        "task_index": {"exists": True, "path": "TASK_INDEX.md"},
                    },
                    "compliance": {
                        "naming_ok": True,
                        "path_ok": True,
                        "relations_ok": True,
                        "language_ok": True,
                        "violations": [],
                    },
                },
                "state": {
                    "confirmed": schema.make_default_confirmed_state("requirement"),
                    "tracking": schema.make_default_tracking_state(),
                },
            }
        }
        self._write_state(state)

        exit_code, payload = self._run_cli(
            "--entity-type",
            "module",
            "--entity-id",
            "M01",
            "--proposed-changes",
            json.dumps({"review_status": "unreviewed"}),
            "--mode",
            "approve",
            "--actor",
            "alice",
            "--reason",
            "blocked by requirement asset",
        )
        self.assertEqual(exit_code, 1)
        self.assertIn(
            "CONFIRM_HARD_GATE_BLOCKERS_PRESENT",
            {item["code"] for item in payload["diagnostics"]},
        )
        self.assertTrue(
            any(
                "policy:asset_missing_plan_latest" in json.dumps(item["evidence"], ensure_ascii=False)
                for item in payload["diagnostics"]
            )
        )

    def test_approve_rejects_when_language_policy_blocker_unresolved(self) -> None:
        state = self._read_state()
        state["requirements"] = {
            "RQ01": {
                "meta": {"path": ".", "scope_kind": "root_requirement_cluster"},
                "facts": {
                    "module_ids": ["M01"],
                    "task_ids": ["ST01_01"],
                    "asset_slots": {
                        "plan_latest": {"exists": True, "path": "PLAN_LATEST.md"},
                        "module_index": {"exists": True, "path": "MODULE_INDEX.md"},
                        "task_index": {"exists": True, "path": "TASK_INDEX.md"},
                    },
                    "compliance": {
                        "naming_ok": True,
                        "path_ok": True,
                        "relations_ok": True,
                        "language_ok": False,
                        "violations": ["language_non_compliant_missing_zh_cn"],
                    },
                },
                "state": {
                    "confirmed": schema.make_default_confirmed_state("requirement"),
                    "tracking": schema.make_default_tracking_state(),
                },
            }
        }
        self._write_state(state)

        exit_code, payload = self._run_cli(
            "--entity-type",
            "subtask",
            "--entity-id",
            "ST01_01",
            "--proposed-changes",
            json.dumps(
                {
                    "candidate_status": "candidate",
                    "review_status": "pending_confirmation",
                }
            ),
            "--evidence-ref",
            "oq:OQ-01",
            "--mode",
            "approve",
            "--actor",
            "alice",
            "--reason",
            "blocked by language policy",
        )
        self.assertEqual(exit_code, 1)
        self.assertIn(
            "CONFIRM_HARD_GATE_BLOCKERS_PRESENT",
            {item["code"] for item in payload["diagnostics"]},
        )
        self.assertTrue(
            any(
                "policy:language_non_compliant_missing_zh_cn"
                in json.dumps(item["evidence"], ensure_ascii=False)
                for item in payload["diagnostics"]
            )
        )

    def test_reject_input_validation_output(self) -> None:
        exit_code, payload = self._run_cli(
            "--entity-type",
            "module",
            "--entity-id",
            "M01",
            "--proposed-changes",
            json.dumps({"review_status": "approved"}),
            "--mode",
            "approve",
            "--actor",
            "alice",
            "--reason",
            "invalid module transition",
        )
        self.assertEqual(exit_code, 1)
        self.assertIn(
            "RULE_ILLEGAL_STATE_COMBINATION",
            {item["code"] for item in payload["diagnostics"]},
        )

    def test_real_sample_confirm_output_summary(self) -> None:
        exit_code, payload = self._run_cli(
            "--entity-type",
            "module",
            "--entity-id",
            "M01",
            "--proposed-changes",
            json.dumps({"review_status": "unreviewed"}),
            "--mode",
            "dry-run",
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["entity_type"], "module")
        self.assertEqual(payload["entity_id"], "M01")
        self.assertEqual(payload["transition_id"], payload.get("transition_id"))
        self.assertTrue(payload["ok"])

    def test_round_mode_requires_reason_with_decision_anchor(self) -> None:
        self._write_round_template("R001")
        exit_code, payload = self._run_cli(
            "--entity-type",
            "module",
            "--entity-id",
            "M01",
            "--proposed-changes",
            json.dumps({"review_status": "unreviewed"}),
            "--mode",
            "approve",
            "--actor",
            "alice",
            "--round-id",
            "R001",
            "--reason",
            "summary only",
        )
        self.assertEqual(exit_code, 1)
        self.assertIn(
            "CONFIRM_REASON_MISSING_DECISION_ANCHOR",
            {item["code"] for item in payload["diagnostics"]},
        )

    def test_round_mode_accepts_reason_with_decision_anchor(self) -> None:
        self._write_round_template("R002")
        exit_code, payload = self._run_cli(
            "--entity-type",
            "module",
            "--entity-id",
            "M01",
            "--proposed-changes",
            json.dumps({"review_status": "unreviewed"}),
            "--mode",
            "approve",
            "--actor",
            "alice",
            "--round-id",
            "R002",
            "--reason",
            "Decision: allow transition",
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])


if __name__ == "__main__":
    unittest.main()
