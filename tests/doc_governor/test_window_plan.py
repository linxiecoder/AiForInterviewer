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
        "meta": {
            "module_id": module_id,
            "path": f"docs/modules/{module_id}/sub_modules/{subtask_id}-test/",
        },
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


class PlanOpenWindowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root = Path(tempfile.gettempdir()) / f"doc-governor-window-plan-{uuid.uuid4().hex}"
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

    def _write_evaluate_json(self, payload: dict) -> Path:
        path = self.temp_root / "evaluate.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def _write_history(self, lines: list[dict]) -> None:
        content = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in lines)
        self.history_path.write_text(content, encoding="utf-8")

    def _run_cli(self, command: str, *args: str) -> tuple[int, dict]:
        original = Path.cwd()
        os.chdir(self.temp_root)
        try:
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main([command, *args])
            payload = json.loads(output.getvalue())
            return exit_code, payload
        finally:
            os.chdir(original)

    def _entity_key_set(self, entities: list[dict], *, entity_type_key="entity_type", entity_id_key="entity_id") -> set[str]:
        return {f"{entity[entity_type_key]}::{entity[entity_id_key]}" for entity in entities}

    def test_missing_official_state_fails(self) -> None:
        exit_code, payload = self._run_cli("plan-open-window", "--state", str(self.state_path))
        self.assertEqual(exit_code, 1)
        self.assertFalse(payload["ok"])
        self.assertIn(
            "PRE_FLIGHT_STATE_NOT_FOUND",
            [item.get("code") for item in payload.get("parse_errors", [])],
        )

    def test_empty_state_ok_with_empty_plan(self) -> None:
        self._write_state(_default_state())
        exit_code, payload = self._run_cli("plan-open-window", "--state", str(self.state_path))
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["eligible_to_apply"], [])
        self.assertEqual(payload["near_open_but_blocked"], [])
        self.assertEqual(payload["hard_blocked"], [])
        self.assertEqual(payload["summary"]["eligible_to_apply_count"], 0)
        self.assertEqual(payload["summary"]["near_open_but_blocked_count"], 0)
        self.assertEqual(payload["summary"]["hard_blocked_count"], 0)

    def test_batch_multiple_entities_analysis(self) -> None:
        state = _default_state()
        state["modules"]["M01"] = _module_entry("M01")
        state["modules"]["M02"] = _module_entry("M02")
        state["subtasks"]["ST01_01"] = _subtask_entry("ST01_01", "M01", readiness="blocked")
        self._write_state(state)

        exit_code, payload = self._run_cli("plan-open-window", "--state", str(self.state_path))
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(len(payload["eligible_to_apply"]), 2)
        self.assertEqual(len(payload["hard_blocked"]), 1)
        self.assertEqual(len(payload["near_open_but_blocked"]), 0)
        eligible_ids = self._entity_key_set(payload["eligible_to_apply"])
        self.assertIn("module::M01", eligible_ids)
        self.assertIn("module::M02", eligible_ids)

    def test_eligible_near_open_and_hard_classification(self) -> None:
        state = _default_state()
        state["modules"]["M01"] = _module_entry("M01")
        state["modules"]["M02"] = _module_entry("M02")
        state["subtasks"]["ST01_01"] = _subtask_entry("ST01_01", "M01", readiness="blocked")
        self._write_state(state)

        evaluate_payload = {
            "summary": {},
            "modules": {
                "M01": {
                    "derived": {
                        "candidate_blocker_refs": [],
                        "downstream_blocker_refs": [],
                        "implementation_blocker_refs": [],
                        "oq_review_only_refs": [],
                        "review_reasons": ["none"],
                    }
                },
                "M02": {
                    "derived": {
                        "candidate_blocker_refs": [],
                        "downstream_blocker_refs": [],
                        "implementation_blocker_refs": [],
                        "oq_review_only_refs": [],
                        "review_reasons": ["oq_review_only"],
                    }
                },
            },
            "subtasks": {
                "ST01_01": {
                    "derived": {
                        "candidate_blocker_refs": [],
                        "downstream_blocker_refs": [],
                        "implementation_blocker_refs": [],
                        "oq_review_only_refs": [],
                        "review_reasons": [],
                    }
                }
            },
            "oqs": {},
        }
        evaluate_path = self._write_evaluate_json(evaluate_payload)

        exit_code, payload = self._run_cli(
            "plan-open-window",
            "--state",
            str(self.state_path),
            "--evaluate-json",
            str(evaluate_path),
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(len(payload["eligible_to_apply"]), 1)
        self.assertEqual(len(payload["near_open_but_blocked"]), 1)
        self.assertEqual(len(payload["hard_blocked"]), 1)

        eligible_keys = self._entity_key_set(payload["eligible_to_apply"])
        near_keys = self._entity_key_set(payload["near_open_but_blocked"])
        hard_keys = self._entity_key_set(payload["hard_blocked"])
        self.assertEqual(eligible_keys, {"module::M01"})
        self.assertEqual(near_keys, {"module::M02"})
        self.assertEqual(hard_keys, {"subtask::ST01_01"})
        self.assertEqual(eligible_keys.isdisjoint(near_keys), True)
        self.assertEqual(eligible_keys.isdisjoint(hard_keys), True)
        self.assertEqual(near_keys.isdisjoint(hard_keys), True)

    def test_evaluate_json_priority_over_live_evaluate(self) -> None:
        state = _default_state()
        state["modules"]["M01"] = _module_entry("M01")
        self._write_state(state)

        evaluate_payload = {
            "summary": {},
            "modules": {
                "M01": {
                    "derived": {
                        "candidate_blocker_refs": ["module:M00"],
                        "downstream_blocker_refs": [],
                        "implementation_blocker_refs": [],
                        "oq_review_only_refs": [],
                        "review_reasons": [],
                    }
                }
            },
            "subtasks": {},
            "oqs": {},
        }
        evaluate_path = self._write_evaluate_json(evaluate_payload)

        exit_code, payload = self._run_cli(
            "plan-open-window",
            "--state", str(self.state_path), "--evaluate-json", str(evaluate_path)
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["evaluation_source"], "json")
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["summary"]["eligible_to_apply_count"], 0)
        self.assertEqual(payload["summary"]["hard_blocked_count"], 1)
        self.assertEqual(payload["summary"]["preflight_blocked_count"], 1)

    def test_missing_history_does_not_block(self) -> None:
        state = _default_state()
        state["modules"]["M01"] = _module_entry("M01")
        self._write_state(state)
        if self.history_path.exists():
            self.history_path.unlink()

        exit_code, payload_missing = self._run_cli("plan-open-window", "--state", str(self.state_path))
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload_missing["ok"])
        self.assertEqual(payload_missing["summary"]["eligible_to_apply_count"], 1)
        self.assertEqual(payload_missing["summary"]["hard_blocked_count"], 0)
        self.assertEqual(payload_missing["summary"]["near_open_but_blocked_count"], 0)

        self._write_history([])
        exit_code, payload_with_history = self._run_cli(
            "plan-open-window",
            "--state",
            str(self.state_path),
            "--history",
            str(self.history_path),
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload_with_history["summary"]["eligible_to_apply_count"], 1)
        self.assertEqual(payload_with_history["summary"]["hard_blocked_count"], 0)
        self.assertEqual(payload_with_history["summary"]["near_open_but_blocked_count"], 0)

    def test_planner_no_side_effect_to_state_files(self) -> None:
        state = _default_state()
        state["modules"]["M01"] = _module_entry("M01")
        self._write_state(state)
        self.bootstrap_path.write_text("bootstrap-static", encoding="utf-8")
        self._write_history(
            [
                {
                    "transition_id": "T-001",
                    "timestamp": "2025-01-01T00:00:00Z",
                    "entity_type": "module",
                    "entity_id": "M01",
                    "result": "approved",
                    "actor": "alice",
                }
            ]
        )

        before_state = self.state_path.read_bytes()
        before_bootstrap = self.bootstrap_path.read_bytes()
        before_history = self.history_path.read_bytes()

        exit_code, _ = self._run_cli(
            "plan-open-window",
            "--state",
            str(self.state_path),
            "--history",
            str(self.history_path),
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(before_state, self.state_path.read_bytes())
        self.assertEqual(before_bootstrap, self.bootstrap_path.read_bytes())
        self.assertEqual(before_history, self.history_path.read_bytes())

    def test_would_change_by_entity_only_contains_window_fields(self) -> None:
        state = _default_state()
        state["modules"]["M01"] = _module_entry("M01")
        state["modules"]["M02"] = _module_entry("M02")
        self._write_state(state)

        exit_code, payload = self._run_cli("plan-open-window", "--state", str(self.state_path))
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["would_change_by_entity"])
        expected_keys = {
            "entity_type",
            "entity_id",
            "window_status",
            "window_opened_at",
            "window_opened_by",
            "window_reason",
        }
        for item in payload["would_change_by_entity"]:
            self.assertEqual(set(item.keys()), expected_keys)
            self.assertEqual(item["window_status"], "open")
            self.assertIsNotNone(item["window_opened_at"])
            self.assertIsNone(item["window_opened_by"])
            self.assertIsNone(item["window_reason"])

    def test_bootstrap_default_oq_policy_cannot_auto_enable_open(self) -> None:
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

        exit_code, payload = self._run_cli("plan-open-window", "--state", str(self.state_path))
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["summary"]["eligible_to_apply_count"], 0)
        self.assertEqual(payload["summary"]["hard_blocked_count"], 1)
        self.assertEqual(payload["hard_blocked"][0]["entity_type"], "module")
        self.assertEqual(payload["hard_blocked"][0]["entity_id"], "M01")
        self.assertTrue(
            any(
                reason["code"] == "bootstrap_default_oq_policy_requires_confirmation"
                for reason in payload["hard_blocked"][0]["blockers"]
            )
        )

    def test_plan_round_queue_order_by_blocker_and_reject(self) -> None:
        state = _default_state()
        state["modules"]["M01"] = _module_entry("M01")
        state["modules"]["M02"] = _module_entry("M02")
        state["subtasks"]["ST01_01"] = _subtask_entry("ST01_01", "M01", readiness="blocked")
        self._write_state(state)
        self._write_history(
            [
                {"transition_id": "1", "timestamp": "2026-01-01T00:00:00Z", "entity_type": "subtask", "entity_id": "ST01_01", "result": "rejected", "actor": "a"},
                {"transition_id": "2", "timestamp": "2026-01-02T00:00:00Z", "entity_type": "subtask", "entity_id": "ST01_01", "result": "rejected", "actor": "a"},
            ]
        )
        evaluate_payload = {
            "summary": {},
            "modules": {
                "M01": {"derived": {"candidate_blocker_refs": [], "downstream_blocker_refs": [], "implementation_blocker_refs": [], "oq_review_only_refs": [], "review_reasons": []}},
                "M02": {"derived": {"candidate_blocker_refs": [], "downstream_blocker_refs": [], "implementation_blocker_refs": [], "oq_review_only_refs": [], "review_reasons": ["oq_review_only"]}},
            },
            "subtasks": {
                "ST01_01": {"derived": {"candidate_blocker_refs": ["module:M00", "gate:x"], "downstream_blocker_refs": [], "implementation_blocker_refs": [], "oq_review_only_refs": [], "review_reasons": []}},
            },
            "oqs": {},
        }
        evaluate_path = self._write_evaluate_json(evaluate_payload)

        exit_code, payload = self._run_cli(
            "plan-round",
            "--state",
            str(self.state_path),
            "--history",
            str(self.history_path),
            "--evaluate-json",
            str(evaluate_path),
            "--round-id",
            "round-test",
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["round_id"], "round-test")
        self.assertEqual(payload["queues"]["can_approve_now"][0]["recommended_action"], "approve")
        self.assertEqual(payload["queues"]["must_review"][0]["recommended_action"], "defer")
        self.assertEqual(payload["queues"]["blocked_hard"][0]["recommended_action"], "reject")
        self.assertEqual(payload["queues"]["blocked_hard"][0]["entity_id"], "ST01_01")

    def test_apply_round_batch_consistency(self) -> None:
        state = _default_state()
        state["modules"]["M01"] = _module_entry("M01")
        state["modules"]["M02"] = _module_entry("M02")
        self._write_state(state)

        plan_payload = {
            "round_id": "round-apply-1",
            "queues": {
                "can_approve_now": [
                    {
                        "entity_type": "module",
                        "entity_id": "M01",
                        "recommended_action": "approve",
                        "proposed_changes": {},
                        "evidence_refs": [],
                    }
                ],
                "blocked_hard": [
                    {
                        "entity_type": "module",
                        "entity_id": "M02",
                        "recommended_action": "reject",
                        "proposed_changes": {},
                        "evidence_refs": [],
                    }
                ],
                "must_review": [
                    {
                        "entity_type": "module",
                        "entity_id": "M03",
                        "recommended_action": "defer",
                    }
                ],
            },
        }
        plan_path = self.temp_root / "round-plan.json"
        plan_path.write_text(json.dumps(plan_payload, ensure_ascii=False), encoding="utf-8")

        exit_code, payload = self._run_cli(
            "apply-round",
            "--round-id",
            "round-apply-1",
            "--from-plan",
            str(plan_path),
            "--state",
            str(self.state_path),
            "--actor",
            "tester",
            "--reason",
            "batch apply",
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["summary"]["total"], 3)
        self.assertEqual(payload["summary"]["applied"], 2)
        self.assertEqual(payload["summary"]["skipped"], 1)
        self.assertEqual(payload["summary"]["failed"], 0)

        lines = [line for line in self.history_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(lines), 2)


if __name__ == "__main__":
    unittest.main()
