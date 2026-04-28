import io
import json
from contextlib import redirect_stdout
from typing import Any

import yaml

from tools.doc_governor.cli import main
from tools.doc_governor.task_state_dependency_map import build_task_state_dependency_map
from tools.testing.temp_artifacts import ManagedTempArtifactsTestCase


def _build_state(
    *, formal_window_open: bool = True, tasks: dict[str, dict[str, Any]] | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    if tasks is None:
        tasks = {}
    normalized_tasks = {
        task_id: {
            "meta": {"module_id": task["module_id"]},
            "state": {
                "confirmed": {
                    "implementation_doc_state": task["implementation_doc_state"],
                    "readiness": task["readiness"],
                    "formal_window_status": "open" if formal_window_open else "closed",
                }
            },
        }
        for task_id, task in tasks.items()
    }
    state = {
        "schema_version": 1,
        "global_policy": {"formal_window_open": formal_window_open},
        "requirements": {},
        "modules": {},
        "subtasks": normalized_tasks,
    }
    evaluate_payload = {
        "subtasks": {
            task_id: {"derived": {"blocker_refs": task["blockers"]}}
            for task_id, task in tasks.items()
        }
    }
    return state, evaluate_payload


class TaskStateDependencyMapTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "task-state-dependency-map"

    def setUp(self) -> None:
        super().setUp()
        self.state_path = self.temp_root / "DOC_STATE.yaml"

    def _run_preview(
        self, task_states: dict[str, dict[str, Any]], *, formal_window_open: bool = True, task_id: str
    ) -> dict[str, Any]:
        state, evaluate_payload = _build_state(
            formal_window_open=formal_window_open,
            tasks=task_states,
        )
        self.state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
        return build_task_state_dependency_map(
            state_path=self.state_path,
            evaluate_payload=evaluate_payload,
            entity_ids=[task_id],
        )

    def test_dependency_stage_stay_in_content_layer(self) -> None:
        preview = self._run_preview(
            {
                "T01": {
                    "module_id": "M01",
                    "implementation_doc_state": "active_working_doc",
                    "readiness": "downstream_ready",
                    "blockers": ["doc:implementation_doc"],
                }
            },
            task_id="T01",
        )
        item = preview["tasks"][0]
        self.assertEqual(item["dependency_stage"], "stay_in_content_layer")
        self.assertTrue(item["is_active_working_doc"])
        self.assertEqual(item["readiness_gap_blockers"], ["doc:implementation_doc"])
        self.assertEqual(item["content_layer_blockers"], ["doc:implementation_doc"])
        self.assertEqual(item["state_layer_blockers"], [])

    def test_dependency_stage_can_consider_readiness_but_not_formal(self) -> None:
        preview = self._run_preview(
            {
                "T02": {
                    "module_id": "M01",
                    "implementation_doc_state": "active_working_doc",
                    "readiness": "downstream_ready",
                    "blockers": [],
                }
            },
            formal_window_open=False,
            task_id="T02",
        )
        item = preview["tasks"][0]
        self.assertEqual(item["dependency_stage"], "can_consider_readiness_but_not_formal")
        self.assertEqual(item["gate_result"], "pass")
        self.assertEqual(item["open_window_gap_blockers"], ["policy:formal_window_closed"])
        self.assertEqual(item["formal_window_blockers"], ["policy:formal_window_closed"])
        self.assertTrue(item["can_continue_readiness"])
        self.assertFalse(item["can_enter_preflight_open_window"])
        self.assertTrue(item["can_open_formal_window"])
        self.assertFalse(item["can_generate_implementation_packet"])
        self.assertFalse(item["can_mark_implementation_ready"])

    def test_dependency_stage_ready_for_preflight_open_window(self) -> None:
        preview = self._run_preview(
            {
                "T03": {
                    "module_id": "M01",
                    "implementation_doc_state": "active_working_doc",
                    "readiness": "downstream_ready",
                    "blockers": [],
                }
            },
            formal_window_open=True,
            task_id="T03",
        )
        item = preview["tasks"][0]
        self.assertEqual(item["dependency_stage"], "ready_for_preflight_open_window")
        self.assertEqual(item["gate_result"], "pass")
        self.assertEqual(item["open_window_gap_blockers"], [])
        self.assertFalse(item["formal_window_blockers"])
        self.assertTrue(item["can_enter_preflight_open_window"])
        self.assertTrue(item["can_open_formal_window"])
        self.assertFalse(item["can_generate_implementation_packet"])
        self.assertFalse(item["can_mark_implementation_ready"])

    def test_dependency_stage_should_not_enter_open_window(self) -> None:
        preview = self._run_preview(
            {
                "T04": {
                    "module_id": "M01",
                    "implementation_doc_state": "active_working_doc",
                    "readiness": "downstream_ready",
                    "blockers": ["state:manual_fill_needed"],
                }
            },
            task_id="T04",
        )
        item = preview["tasks"][0]
        self.assertEqual(item["dependency_stage"], "should_not_enter_open_window")
        self.assertEqual(item["open_window_gap_blockers"], ["state:manual_fill_needed"])
        self.assertEqual(item["state_layer_blockers"], ["state:manual_fill_needed"])

    def test_cli_preview_outputs_markdown(self) -> None:
        payload = _build_state(
            formal_window_open=True,
            tasks={
                "T05": {
                    "module_id": "M01",
                    "implementation_doc_state": "active_working_doc",
                    "readiness": "downstream_ready",
                    "blockers": [],
                }
            },
        )[1]
        self.state_path.write_text(
            yaml.safe_dump(
                {
                    "schema_version": 1,
                    "global_policy": {"formal_window_open": True},
                    "requirements": {},
                    "modules": {},
                    "subtasks": {
                        "T05": {
                            "meta": {"module_id": "M01"},
                            "state": {
                                "confirmed": {
                                    "implementation_doc_state": "active_working_doc",
                                    "readiness": "downstream_ready",
                                    "formal_window_status": "open",
                                }
                            },
                        }
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        eval_path = self.temp_root / "evaluate.json"
        eval_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = main(
                [
                    "preview-task-state-dependency-map",
                    "--input",
                    str(self.state_path),
                    "--evaluate-json",
                    str(eval_path),
                    "--format",
                    "markdown",
                    "--entity-id",
                    "T05",
                ]
            )
        output = stdout.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("T05", output)
        self.assertIn("gate_result: pass", output)
        self.assertIn("can_generate_implementation_packet=false", output)
        self.assertIn("可转向 preflight-open-window", output)
