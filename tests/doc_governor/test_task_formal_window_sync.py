import unittest
from pathlib import Path

import yaml

from tests.doc_governor.test_cli_smoke import _build_state, _write_packet_ready_task_docs
from tools.doc_governor.task_formal_window_sync import (
    build_task_formal_window_sync_preview,
    execute_task_formal_window_sync,
)
from tools.testing.temp_artifacts import ManagedTempArtifactsTestCase


def _evaluate_payload(*, blocker_refs=("policy:formal_window_closed",)) -> dict:
    return {
        "subtasks": {
            "ST01_01": {
                "derived": {
                    "requirement_ids": ["RQ01"],
                    "blocker_refs": list(blocker_refs),
                }
            }
        },
        "requirements": {},
        "modules": {},
    }


class TaskFormalWindowSyncTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "task-formal-window-sync"

    def _official_state_path(self) -> Path:
        path = self.temp_root / "docs" / "governance" / "DOC_STATE.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _write_state(self, state: dict) -> Path:
        path = self._official_state_path()
        path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
        return path

    def _ready_state(self) -> dict:
        state = _build_state()
        state["global_policy"]["formal_window_open"] = False
        confirmed = state["subtasks"]["ST01_01"]["state"]["confirmed"]
        confirmed["implementation_doc_state"] = "active_working_doc"
        confirmed["readiness"] = "downstream_ready"
        confirmed["formal_window_status"] = "closed"
        confirmed["implementation_approval_status"] = "none"
        return state

    def test_preview_allows_formal_window_when_task_is_window_only(self) -> None:
        state_path = self._write_state(self._ready_state())
        _write_packet_ready_task_docs(self.temp_root)

        payload = build_task_formal_window_sync_preview(
            state_path=state_path,
            evaluate_payload=_evaluate_payload(),
            entity_ids=["ST01_01"],
        )

        self.assertEqual(payload["summary"]["selected_task_count"], 1)
        self.assertEqual(payload["summary"]["formal_window_apply_candidate_count"], 1)
        task = payload["tasks"][0]
        self.assertEqual(task["task_id"], "ST01_01")
        self.assertTrue(task["apply_allowed"])
        self.assertEqual(task["dependency_stage"], "can_consider_readiness_but_not_formal")
        self.assertEqual(task["bridge_classification"], "already_window_only")
        self.assertEqual(task["target_entity"], "subtasks.ST01_01")
        self.assertEqual(
            task["proposed_field"],
            "subtasks.ST01_01.state.confirmed.formal_window_status",
        )
        self.assertEqual(task["proposed_value"], "open")
        self.assertFalse(task["implementation_ready_after_apply"])
        self.assertEqual(payload["write_target_field"], "subtasks.<id>.state.confirmed.formal_window_status")

    def test_preview_allows_formal_window_even_before_readiness_sync(self) -> None:
        state = self._ready_state()
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["readiness"] = "blocked"
        state_path = self._write_state(state)
        _write_packet_ready_task_docs(self.temp_root)

        payload = build_task_formal_window_sync_preview(
            state_path=state_path,
            evaluate_payload=_evaluate_payload(),
            entity_ids=["ST01_01"],
        )

        self.assertEqual(payload["summary"]["formal_window_apply_candidate_count"], 1)
        task = payload["tasks"][0]
        self.assertTrue(task["apply_allowed"])
        self.assertEqual(task["status"], "can_open_formal_window")

    def test_apply_writes_only_scoped_formal_window_status(self) -> None:
        state_path = self._write_state(self._ready_state())
        _write_packet_ready_task_docs(self.temp_root)

        result = execute_task_formal_window_sync(
            state_path=state_path,
            evaluate_payload=_evaluate_payload(),
            entity_ids=["ST01_01"],
            apply_changes=True,
            actor="alice",
            reason="open formal window",
        )

        self.assertEqual(result["mode"], "apply")
        self.assertEqual(result["summary"]["applied_task_count"], 1)
        updated = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        self.assertFalse(updated["global_policy"]["formal_window_open"])
        confirmed = updated["subtasks"]["ST01_01"]["state"]["confirmed"]
        self.assertEqual(confirmed["formal_window_status"], "open")
        self.assertEqual(confirmed["readiness"], "downstream_ready")
        self.assertEqual(confirmed["implementation_doc_state"], "active_working_doc")

    def test_apply_is_blocked_when_content_gate_remains(self) -> None:
        state_path = self._write_state(self._ready_state())

        with self.assertRaisesRegex(ValueError, "apply denied"):
            execute_task_formal_window_sync(
                state_path=state_path,
                evaluate_payload=_evaluate_payload(),
                entity_ids=["ST01_01"],
                apply_changes=True,
                actor="alice",
                reason="open formal window",
            )


if __name__ == "__main__":
    unittest.main()
