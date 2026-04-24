import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.cli import main
from tools.doc_governor.task_skeleton_seed import (
    build_task_skeleton_seed_plan,
    execute_task_skeleton_seed,
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
            "design_doc": {"exists": False, "template_like": True},
            "implementation_doc": {"exists": False, "template_like": True},
            "compliance": schema.make_default_compliance_state(),
        },
        "state": {
            "confirmed": schema.make_default_confirmed_state("subtask"),
            "tracking": schema.make_default_tracking_state(),
        },
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
            "RQ01": _requirement_entry(
                "RQ01",
                module_ids=["M01"],
                task_ids=["ST01_01"],
            )
        },
        "modules": {
            "M01": _module_entry("M01"),
        },
        "subtasks": {
            "ST01_01": _subtask_entry("ST01_01", module_id="M01"),
        },
    }


class TaskSkeletonSeedTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "task-skeleton-seed"

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

    def test_dry_run_outputs_plan_without_writing_files(self) -> None:
        plan = build_task_skeleton_seed_plan(
            state_path=self.state_path,
            entity_ids=["ST01_01"],
        )

        self.assertEqual(plan["mode"], "dry_run")
        self.assertEqual(plan["summary"]["selected_task_count"], 1)
        self.assertEqual(plan["summary"]["planned_file_count"], 2)
        self.assertEqual(plan["tasks"][0]["requirement_id"], "RQ01")
        self.assertEqual(plan["tasks"][0]["relation_source"], "requirement_container")
        self.assertFalse(
            (self.temp_root / "docs/modules/M01-test/sub_modules/ST01_01-test/SUBTASK_DESIGN.md").exists()
        )

    def test_apply_writes_minimal_design_and_implementation_skeleton(self) -> None:
        result = execute_task_skeleton_seed(
            state_path=self.state_path,
            entity_ids=["ST01_01"],
            apply_changes=True,
        )

        self.assertEqual(result["mode"], "apply")
        self.assertEqual(result["summary"]["written_file_count"], 2)

        design_path = self.temp_root / "docs/modules/M01-test/sub_modules/ST01_01-test/SUBTASK_DESIGN.md"
        implementation_path = self.temp_root / "docs/modules/M01-test/sub_modules/ST01_01-test/SUBTASK_IMPLEMENTATION.md"
        design_text = design_path.read_text(encoding="utf-8")
        implementation_text = implementation_path.read_text(encoding="utf-8")

        self.assertIn("# 子任务设计文档", design_text)
        self.assertIn("## 3. 子任务目标", design_text)
        self.assertIn("## 5. 技术方案", design_text)
        self.assertIn("待人工填写：技术方案", design_text)

        self.assertIn("# 子任务实施文档", implementation_text)
        self.assertIn("## 3. 本轮实施目标", implementation_text)
        self.assertIn("## 5. 允许修改范围", implementation_text)
        self.assertIn("## 7. 测试与验证", implementation_text)
        self.assertIn("## 8. 完成判定", implementation_text)
        self.assertIn("待人工填写：allowed_modify_paths", implementation_text)
        self.assertIn("待人工填写：required_tests", implementation_text)
        self.assertIn("待人工填写：acceptance_criteria", implementation_text)

    def test_native_requirement_relation_without_container_still_allows_seed(self) -> None:
        state = _build_state()
        state["requirements"]["RQ01"]["facts"]["task_ids"] = []
        state["subtasks"]["ST01_01"]["meta"]["requirement_id"] = "RQ01"
        state["subtasks"]["ST01_01"]["facts"]["requirement_ids"] = ["RQ01"]
        self._write_state(state)

        plan = build_task_skeleton_seed_plan(
            state_path=self.state_path,
            entity_ids=["ST01_01"],
        )
        self.assertEqual(plan["tasks"][0]["relation_source"], "entity_native")
        self.assertEqual(plan["tasks"][0]["decision"], "planned")

    def test_ambiguous_requirement_relation_is_rejected(self) -> None:
        state = _build_state()
        state["requirements"]["RQ02"] = _requirement_entry(
            "RQ02",
            module_ids=["M01"],
            task_ids=["ST01_01"],
        )
        self._write_state(state)

        plan = build_task_skeleton_seed_plan(
            state_path=self.state_path,
            entity_ids=["ST01_01"],
        )
        self.assertEqual(
            plan["tasks"][0]["decision"],
            "blocked_requirement_relation_ambiguous",
        )
        with self.assertRaisesRegex(ValueError, "存在不允许 apply 的 task"):
            execute_task_skeleton_seed(
                state_path=self.state_path,
                entity_ids=["ST01_01"],
                apply_changes=True,
            )

    def test_cli_command_exists_and_supports_dry_run_and_apply(self) -> None:
        output_plan = self.temp_root / "skeleton-plan.json"

        dry_run_code, dry_run_output = self._run_cli(
            "apply-task-skeleton-seed",
            "--input",
            str(self.state_path),
            "--entity-id",
            "ST01_01",
            "--output-plan",
            str(output_plan),
        )
        self.assertEqual(dry_run_code, 0)
        dry_run_payload = json.loads(dry_run_output)
        self.assertEqual(dry_run_payload["mode"], "dry_run")
        self.assertTrue(output_plan.exists())

        apply_code, apply_output = self._run_cli(
            "apply-task-skeleton-seed",
            "--input",
            str(self.state_path),
            "--entity-id",
            "ST01_01",
            "--apply",
        )
        self.assertEqual(apply_code, 0)
        apply_payload = json.loads(apply_output)
        self.assertEqual(apply_payload["mode"], "apply")
        self.assertEqual(apply_payload["summary"]["written_file_count"], 2)


if __name__ == "__main__":
    unittest.main()
