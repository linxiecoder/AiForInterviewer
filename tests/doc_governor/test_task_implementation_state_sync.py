import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.cli import main
from tools.doc_governor.task_implementation_state_sync import (
    build_task_implementation_state_sync_plan,
    execute_task_implementation_state_sync,
)
from tools.testing.temp_artifacts import ManagedTempArtifactsTestCase


def _requirement_entry(
    requirement_id: str,
    *,
    module_ids: list[str],
    task_ids: list[str],
) -> dict:
    return {
        "meta": {"path": ".", "scope_kind": "root_requirement_cluster"},
        "facts": {
            "module_ids": module_ids,
            "task_ids": task_ids,
            "asset_slots": {
                "plan_latest": {"exists": True, "path": "PLAN_LATEST.md"},
                "module_index": {"exists": True, "path": "MODULE_INDEX.md"},
                "task_index": {"exists": True, "path": "TASK_INDEX.md"},
            },
            "compliance": schema.make_default_compliance_state(),
        },
        "state": {
            "confirmed": schema.make_default_confirmed_state("requirement"),
            "tracking": schema.make_default_tracking_state(),
        },
    }


def _module_entry(module_id: str) -> dict:
    return {
        "meta": {"path": f"docs/modules/{module_id}-test/"},
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


def _subtask_entry(task_id: str, *, module_id: str) -> dict:
    task_state = schema.make_default_confirmed_state("subtask")
    task_state["implementation_doc_state"] = "missing"
    return {
        "meta": {
            "module_id": module_id,
            "path": f"docs/modules/{module_id}-test/sub_modules/{task_id}-test/",
        },
        "facts": {
            "upstream_module_ids": [module_id],
            "related_oq_ids": [],
            "legacy_locked": False,
            "declared_blocker_refs": [],
            "design_doc": {"exists": True, "template_like": True},
            "implementation_doc": {"exists": True, "template_like": True},
            "compliance": schema.make_default_compliance_state(),
        },
        "state": {
            "confirmed": task_state,
            "tracking": schema.make_default_tracking_state(),
        },
    }


def _write_text(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_ready_task_docs(root: Path) -> None:
    task_root = "docs/modules/M01-test/sub_modules/ST01_01-test"
    _write_text(
        root,
        f"{task_root}/SUBTASK_DESIGN.md",
        (
            "# 子任务名称\n\n"
            "## 3. 子任务目标\n\n"
            "- ST01_01\n"
            "## 5. 设计文档\n\n"
            "- 这不是具体实现文档。\n"
        ),
    )
    _write_text(
        root,
        f"{task_root}/SUBTASK_IMPLEMENTATION.md",
        (
            "# 子任务实施文档\n\n"
            "## 3. 本轮实施目标\n"
            "- 完成 implementation state 写回验证\n\n"
            "## 5. 允许修改\n"
            "### 5.1 允许修改\n"
            "- `tools/doc_governor/task_implementation_state_sync.py`\n\n"
            "### 5.2 禁止修改\n"
            "- `docs/governance/DOC_STATE.yaml`\n\n"
            "## 7. 测试与验证\n"
            "### 7.1 自动验证\n"
            "- `python -m pytest tests/doc_governor/test_task_implementation_state_sync.py -q`\n\n"
            "## 8. 完成判定\n"
            "- 完成并通过相关测试。\n"
        ),
    )


def _write_incomplete_task_docs(root: Path) -> None:
    task_root = "docs/modules/M01-test/sub_modules/ST01_01-test"
    _write_text(
        root,
        f"{task_root}/SUBTASK_DESIGN.md",
        "# 子任务名称\n\n## 3. 子任务目标\n- ST01_01\n",
    )
    _write_text(
        root,
        f"{task_root}/SUBTASK_IMPLEMENTATION.md",
        "# 子任务实施文档\n\n## 3. 本轮实施目标\n- 完成 implementation state 写回验证\n",
    )


def _minimal_evaluate_payload(
    *,
    requirement_ids: tuple[str, ...] = ("RQ01",),
    blocker_refs: tuple[str, ...] = (),
) -> dict:
    return {
        "subtasks": {
            "ST01_01": {
                "derived": {
                    "requirement_ids": list(requirement_ids),
                    "implementation_blocker_refs": list(blocker_refs),
                }
            }
        }
    }


def _build_state() -> dict:
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
        "requirements": {
            "RQ01": _requirement_entry("RQ01", module_ids=["M01"], task_ids=["ST01_01"]),
        },
        "modules": {
            "M01": _module_entry("M01"),
        },
        "subtasks": {
            "ST01_01": _subtask_entry("ST01_01", module_id="M01"),
        },
    }


class TaskImplementationStateSyncTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "task-implementation-state-sync"

    def setUp(self) -> None:
        super().setUp()
        self.state_path = self.temp_root / "docs" / "governance" / "DOC_STATE.yaml"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_state(_build_state())

    def _write_state(self, state: dict) -> None:
        self.state_path.write_text(
            yaml.safe_dump(state, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    def _run_cli(self, *args: str) -> tuple[int, str]:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            try:
                exit_code = main(list(args))
            except SystemExit as exc:
                exit_code = int(exc.code)
        return exit_code, stdout.getvalue()

    def test_build_plan_planned_for_eligible_task(self) -> None:
        _write_ready_task_docs(self.temp_root)
        payload = _minimal_evaluate_payload()
        plan = build_task_implementation_state_sync_plan(
            state_path=self.state_path,
            evaluate_payload=payload,
            entity_ids=["ST01_01"],
        )

        self.assertEqual(plan["mode"], "dry_run")
        self.assertEqual(plan["summary"]["selected_task_count"], 1)
        self.assertEqual(plan["summary"]["planned_task_count"], 1)
        task = plan["tasks"][0]
        self.assertEqual(task["task_id"], "ST01_01")
        self.assertEqual(task["decision"], "planned")
        self.assertTrue(task["apply_allowed"])
        self.assertEqual(
            task["target_state_path"],
            "subtasks.ST01_01.state.confirmed.implementation_doc_state",
        )

    def test_execute_apply_only_writes_implementation_doc_state(self) -> None:
        _write_ready_task_docs(self.temp_root)
        state_before = yaml.safe_load(self.state_path.read_text(encoding="utf-8"))
        payload = _minimal_evaluate_payload()
        result = execute_task_implementation_state_sync(
            state_path=self.state_path,
            evaluate_payload=payload,
            entity_ids=["ST01_01"],
            apply_changes=True,
        )

        self.assertEqual(result["mode"], "apply")
        state_after = yaml.safe_load(self.state_path.read_text(encoding="utf-8"))
        task_before = state_before["subtasks"]["ST01_01"]
        task_after = state_after["subtasks"]["ST01_01"]

        self.assertEqual(task_after["state"]["confirmed"]["implementation_doc_state"], "active_working_doc")
        self.assertEqual(
            task_after["state"]["confirmed"]["readiness"],
            task_before["state"]["confirmed"]["readiness"],
        )
        self.assertEqual(task_after["state"]["confirmed"]["window_status"], task_before["state"]["confirmed"]["window_status"])
        self.assertEqual(
            task_after["facts"]["design_doc"],
            task_before["facts"]["design_doc"],
        )
        self.assertEqual(
            task_after["facts"]["implementation_doc"],
            task_before["facts"]["implementation_doc"],
        )

    def test_apply_is_blocked_when_requirement_relation_is_ambiguous(self) -> None:
        _write_ready_task_docs(self.temp_root)
        payload = _minimal_evaluate_payload(
            requirement_ids=("RQ01", "RQ02"),
        )

        plan = build_task_implementation_state_sync_plan(
            state_path=self.state_path,
            evaluate_payload=payload,
            entity_ids=["ST01_01"],
        )
        task = plan["tasks"][0]
        self.assertEqual(task["decision"], "blocked_requirement_relation_ambiguous")
        self.assertFalse(task["apply_allowed"])

        with self.assertRaisesRegex(ValueError, "apply 不允许"):
            execute_task_implementation_state_sync(
                state_path=self.state_path,
                evaluate_payload=payload,
                entity_ids=["ST01_01"],
                apply_changes=True,
            )

    def test_blocked_when_design_or_impl_artifacts_not_ready(self) -> None:
        _write_incomplete_task_docs(self.temp_root)
        payload = _minimal_evaluate_payload(blocker_refs=("doc:design_doc",))
        plan = build_task_implementation_state_sync_plan(
            state_path=self.state_path,
            evaluate_payload=payload,
            entity_ids=["ST01_01"],
        )
        task = plan["tasks"][0]
        self.assertEqual(task["decision"], "blocked_doc_artifacts_not_ready")
        self.assertFalse(task["apply_allowed"])

    def test_cli_command_supports_dry_run_and_apply(self) -> None:
        _write_ready_task_docs(self.temp_root)
        output_plan = self.temp_root / "task-implementation-state-sync.json"
        evaluate_payload_path = self.temp_root / "evaluate.json"
        evaluate_payload = _minimal_evaluate_payload()
        evaluate_payload_path.write_text(
            json.dumps(evaluate_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        dry_run_code, dry_run_output = self._run_cli(
            "apply-task-implementation-state-sync",
            "--input",
            str(self.state_path),
            "--entity-id",
            "ST01_01",
            "--evaluate-json",
            str(evaluate_payload_path),
            "--output-plan",
            str(output_plan),
        )
        self.assertEqual(dry_run_code, 0)
        dry_run_payload = json.loads(dry_run_output)
        self.assertEqual(dry_run_payload["mode"], "dry_run")
        self.assertEqual(dry_run_payload["summary"]["planned_task_count"], 1)
        self.assertTrue(output_plan.exists())

        apply_code, apply_output = self._run_cli(
            "apply-task-implementation-state-sync",
            "--input",
            str(self.state_path),
            "--entity-id",
            "ST01_01",
            "--evaluate-json",
            str(evaluate_payload_path),
            "--apply",
        )
        self.assertEqual(apply_code, 0)
        apply_payload = json.loads(apply_output)
        self.assertEqual(apply_payload["mode"], "apply")
        self.assertEqual(apply_payload["summary"]["written_task_count"], 1)


if __name__ == "__main__":
    unittest.main()
