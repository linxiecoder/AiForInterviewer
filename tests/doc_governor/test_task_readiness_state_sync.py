import unittest
import json
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.task_readiness_state_sync import (
    build_task_readiness_state_sync_preview,
    execute_task_readiness_state_sync,
)
from tools.testing.temp_artifacts import ManagedTempArtifactsTestCase


def _subtask_entry(
    task_id: str,
    *,
    module_id: str,
    readiness: str,
    implementation_doc_state: str = "active_working_doc",
    design_template_like: bool = False,
    implementation_template_like: bool = False,
) -> dict:
    confirmed = schema.make_default_confirmed_state("subtask")
    confirmed["maturity"] = "L4"
    confirmed["readiness"] = readiness
    confirmed["implementation_doc_state"] = implementation_doc_state
    return {
        "meta": {
            "module_id": module_id,
            "path": f"docs/modules/{module_id}-test/sub_modules/{task_id}/",
        },
        "facts": {
            "upstream_module_ids": [module_id],
            "related_oq_ids": [],
            "legacy_locked": False,
            "declared_blocker_refs": [],
            "design_doc": {"exists": True, "template_like": design_template_like},
            "implementation_doc": {
                "exists": True,
                "template_like": implementation_template_like,
            },
            "compliance": schema.make_default_compliance_state(),
        },
        "state": {
            "confirmed": confirmed,
            "tracking": schema.make_default_tracking_state(),
        },
    }


def _build_state(
    *,
    readiness: str,
    implementation_doc_state: str = "active_working_doc",
    formal_window_open: bool = True,
    design_template_like: bool = False,
    implementation_template_like: bool = False,
) -> dict:
    global_policy = dict(schema.GLOBAL_POLICY_DEFAULTS)
    global_policy["formal_window_open"] = formal_window_open
    return {
        "schema_version": schema.SCHEMA_VERSION,
        "global_policy": global_policy,
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
                    "docs": {
                        slot: {"exists": True, "template_like": False}
                        for slot in schema.MODULE_DOC_SLOTS
                    },
                    "compliance": schema.make_default_compliance_state(),
                },
                "state": {
                    "confirmed": schema.make_default_confirmed_state("module"),
                    "tracking": schema.make_default_tracking_state(),
                },
            }
        },
        "subtasks": {
            "ST01_01": _subtask_entry(
                "ST01_01",
                module_id="M01",
                readiness=readiness,
                implementation_doc_state=implementation_doc_state,
                design_template_like=design_template_like,
                implementation_template_like=implementation_template_like,
            )
        },
    }


def _evaluate_payload(
    *,
    requirement_ids=("RQ01",),
    blocker_refs=(),
) -> dict:
    return {
        "subtasks": {
            "ST01_01": {
                "derived": {
                    "requirement_ids": list(requirement_ids),
                    "blocker_refs": list(blocker_refs),
                }
            }
        },
        "requirements": {},
        "modules": {},
    }


class TaskReadinessStateSyncTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "task-readiness-state-sync"

    def _official_state_path(self) -> Path:
        path = self.temp_root / "docs" / "governance" / "DOC_STATE.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _write_state(self, state: dict) -> Path:
        path = self._official_state_path()
        path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
        return path

    def test_preview_blocked_to_downstream_readiness(self) -> None:
        state_path = self._write_state(
            _build_state(readiness="blocked", implementation_doc_state="active_working_doc")
        )
        evaluate_payload = _evaluate_payload()
        payload = build_task_readiness_state_sync_preview(
            state_path=state_path,
            evaluate_payload=evaluate_payload,
            entity_ids=["ST01_01"],
        )

        self.assertEqual(payload["summary"]["selected_task_count"], 1)
        self.assertEqual(payload["summary"]["readiness_apply_candidate_count"], 1)
        task = payload["tasks"][0]
        self.assertEqual(task["task_id"], "ST01_01")
        self.assertTrue(task["apply_allowed"])
        self.assertEqual(task["target_readiness"], "downstream_ready")
        self.assertEqual(task["status"], "can_advance_to_downstream_ready")

    def test_preview_blocks_without_unique_requirement_relation(self) -> None:
        state_path = self._write_state(
            _build_state(readiness="blocked", implementation_doc_state="active_working_doc")
        )
        evaluate_payload = _evaluate_payload(requirement_ids=())
        payload = build_task_readiness_state_sync_preview(
            state_path=state_path,
            evaluate_payload=evaluate_payload,
            entity_ids=["ST01_01"],
        )

        self.assertEqual(payload["summary"]["readiness_apply_candidate_count"], 0)
        task = payload["tasks"][0]
        self.assertFalse(task["apply_allowed"])
        self.assertIn("requirement relation", str(task["reason"]))
        self.assertEqual(task["status"], "blocked_by_requirement_relation")

    def test_preview_allows_preflight_step_to_implementation_ready(self) -> None:
        state_path = self._write_state(
            _build_state(readiness="downstream_ready", formal_window_open=True)
        )
        evaluate_payload = _evaluate_payload()
        payload = build_task_readiness_state_sync_preview(
            state_path=state_path,
            evaluate_payload=evaluate_payload,
            entity_ids=["ST01_01"],
        )

        task = payload["tasks"][0]
        self.assertEqual(task["dependency_stage"], "ready_for_preflight_open_window")
        self.assertEqual(task["target_readiness"], "implementation_ready")
        self.assertEqual(task["status"], "can_advance_to_implementation_ready")

    def test_apply_writes_only_readiness(self) -> None:
        state_path = self._write_state(
            _build_state(readiness="downstream_ready", formal_window_open=True)
        )
        evaluate_payload = _evaluate_payload()

        result = execute_task_readiness_state_sync(
            state_path=state_path,
            evaluate_payload=evaluate_payload,
            entity_ids=["ST01_01"],
            apply_changes=True,
            actor="alice",
            reason="advance readiness",
        )

        self.assertEqual(result["mode"], "apply")
        self.assertEqual(result["summary"]["applied_task_count"], 1)
        updated = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        confirmed = updated["subtasks"]["ST01_01"]["state"]["confirmed"]
        self.assertEqual(confirmed["readiness"], "implementation_ready")
        self.assertEqual(confirmed["implementation_doc_state"], "active_working_doc")

    def test_apply_is_blocked_when_content_layer_blocker_exists(self) -> None:
        state_path = self._write_state(
            _build_state(
                readiness="blocked",
                implementation_doc_state="active_working_doc",
                design_template_like=True,
            )
        )
        evaluate_payload = _evaluate_payload(blocker_refs=("doc:design_doc",))

        with self.assertRaisesRegex(ValueError, "apply denied"):
            execute_task_readiness_state_sync(
                state_path=state_path,
                evaluate_payload=evaluate_payload,
                entity_ids=["ST01_01"],
                apply_changes=True,
                actor="alice",
                reason="advance readiness",
            )


if __name__ == "__main__":
    unittest.main()
