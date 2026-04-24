import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.cli import main
from tools.doc_governor.task_doc_state_sync import (
    build_task_doc_state_sync_plan,
    execute_task_doc_state_sync,
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
            "design_doc": {"exists": False, "template_like": True},
            "implementation_doc": {"exists": False, "template_like": True},
            "compliance": schema.make_default_compliance_state(),
        },
        "state": {
            "confirmed": task_state,
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


def _write_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_seeded_docs(root: Path) -> None:
    task_root = root / "docs/modules/M01-test/sub_modules/ST01_01-test"
    _write_markdown(
        task_root / "SUBTASK_DESIGN.md",
        "\n".join(
            [
                "# 子任务设计文档",
                "",
                "## 1. 基本信息",
                "",
                "- 子任务 ID：ST01_01",
                "- 所属模块：M01",
                "",
                "## 3. 子任务目标",
                "",
                "- 为 task doc state sync 提供最小设计输入。",
                "",
                "## 5. 技术方案",
                "",
                "- 读取子任务目录下的正式双文档。",
                "- 只同步最小文档槽位事实，不推进更高层状态。",
                "",
            ]
        ),
    )
    _write_markdown(
        task_root / "SUBTASK_IMPLEMENTATION.md",
        "\n".join(
            [
                "# 子任务实施文档",
                "",
                "## 1. 基本信息",
                "",
                "- 子任务 ID：ST01_01",
                "- 所属模块：M01",
                "",
                "## 3. 本轮实施目标",
                "",
                "- 补齐 task 文档槽位与最小状态同步。",
                "",
                "## 5. 允许修改范围",
                "",
                "- 允许修改：`tools/doc_governor/task_doc_state_sync.py`",
                "- 禁止修改：`docs/governance/DOC_STATE.yaml` 之外的无关状态。",
                "",
                "## 7. 测试与验证",
                "",
                "- 运行：`python -m pytest tests/doc_governor/test_task_doc_state_sync.py -q`",
                "",
                "## 8. 完成判定",
                "",
                "- 设计文档与实施文档槽位已同步进 state。",
                "- `implementation_doc_state`、`readiness`、`formal_window_open` 未被自动推进。",
                "",
            ]
        ),
    )


def _write_incomplete_implementation_doc(root: Path) -> None:
    task_root = root / "docs/modules/M01-test/sub_modules/ST01_01-test"
    _write_markdown(
        task_root / "SUBTASK_IMPLEMENTATION.md",
        "\n".join(
            [
                "# 子任务实施文档",
                "",
                "## 3. 本轮实施目标",
                "",
                "- 只有部分章节。",
                "",
                "## 5. 允许修改范围",
                "",
                "- 允许修改：`tools/doc_governor/task_doc_state_sync.py`",
                "",
            ]
        ),
    )


class TaskDocStateSyncTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "task-doc-state-sync"

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

    def test_dry_run_reports_planned_slot_sync_and_state_paths(self) -> None:
        _write_seeded_docs(self.temp_root)

        plan = build_task_doc_state_sync_plan(
            state_path=self.state_path,
            entity_ids=["ST01_01"],
        )

        self.assertEqual(plan["mode"], "dry_run")
        self.assertEqual(plan["summary"]["selected_task_count"], 1)
        self.assertEqual(plan["summary"]["planned_slot_count"], 2)
        self.assertEqual(plan["summary"]["planned_task_count"], 1)
        task = plan["tasks"][0]
        self.assertEqual(task["requirement_id"], "RQ01")
        self.assertEqual(task["relation_source"], "requirement_container")
        self.assertTrue(task["apply_allowed"])

        design_slot = next(item for item in task["slots"] if item["slot_name"] == "design_doc")
        self.assertTrue(design_slot["minimal_sync_ready"])
        self.assertTrue(design_slot["apply_allowed"])
        self.assertIn("subtasks.ST01_01.facts.design_doc.exists", design_slot["target_paths"])
        self.assertIn("subtasks.ST01_01.facts.docs.design_doc.path", design_slot["target_paths"])
        self.assertEqual(
            design_slot["desired_state"]["path"],
            "docs/modules/M01-test/sub_modules/ST01_01-test/SUBTASK_DESIGN.md",
        )

    def test_apply_updates_doc_slot_facts_only_and_preserves_higher_state(self) -> None:
        _write_seeded_docs(self.temp_root)

        result = execute_task_doc_state_sync(
            state_path=self.state_path,
            entity_ids=["ST01_01"],
            apply_changes=True,
        )

        self.assertEqual(result["mode"], "apply")
        self.assertEqual(result["summary"]["written_task_count"], 1)
        self.assertEqual(result["summary"]["written_slot_count"], 2)

        state = yaml.safe_load(self.state_path.read_text(encoding="utf-8"))
        task = state["subtasks"]["ST01_01"]
        self.assertEqual(task["facts"]["design_doc"], {"exists": True, "template_like": False})
        self.assertEqual(
            task["facts"]["implementation_doc"],
            {"exists": True, "template_like": False},
        )
        self.assertEqual(
            task["facts"]["docs"]["design_doc"]["path"],
            "docs/modules/M01-test/sub_modules/ST01_01-test/SUBTASK_DESIGN.md",
        )
        self.assertEqual(
            task["facts"]["docs"]["implementation_doc"]["path"],
            "docs/modules/M01-test/sub_modules/ST01_01-test/SUBTASK_IMPLEMENTATION.md",
        )
        self.assertEqual(
            task["state"]["confirmed"]["implementation_doc_state"],
            "missing",
        )

    def test_existing_formal_state_is_not_downgraded_by_incomplete_disk_doc(self) -> None:
        state = _build_state()
        state["subtasks"]["ST01_01"]["facts"]["implementation_doc"] = {
            "exists": True,
            "template_like": False,
        }
        self._write_state(state)
        _write_seeded_docs(self.temp_root)
        _write_incomplete_implementation_doc(self.temp_root)

        plan = build_task_doc_state_sync_plan(
            state_path=self.state_path,
            entity_ids=["ST01_01"],
        )

        implementation_slot = next(
            item for item in plan["tasks"][0]["slots"] if item["slot_name"] == "implementation_doc"
        )
        self.assertEqual(
            implementation_slot["decision"],
            "blocked_existing_formal_state_conflict",
        )
        self.assertIn("不自动覆盖已有正式文档判断", implementation_slot["reason"])

    def test_ambiguous_requirement_relation_is_rejected(self) -> None:
        state = _build_state()
        state["requirements"]["RQ02"] = _requirement_entry(
            "RQ02",
            module_ids=["M01"],
            task_ids=["ST01_01"],
        )
        self._write_state(state)
        _write_seeded_docs(self.temp_root)

        plan = build_task_doc_state_sync_plan(
            state_path=self.state_path,
            entity_ids=["ST01_01"],
        )
        self.assertEqual(
            plan["tasks"][0]["decision"],
            "blocked_requirement_relation_ambiguous",
        )
        with self.assertRaisesRegex(ValueError, "存在不允许 apply 的 task"):
            execute_task_doc_state_sync(
                state_path=self.state_path,
                entity_ids=["ST01_01"],
                apply_changes=True,
            )

    def test_cli_command_exists_and_supports_dry_run_and_apply(self) -> None:
        _write_seeded_docs(self.temp_root)
        output_plan = self.temp_root / "task-doc-state-sync.json"

        dry_run_code, dry_run_output = self._run_cli(
            "apply-task-doc-state-sync",
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
        self.assertEqual(dry_run_payload["summary"]["planned_slot_count"], 2)
        self.assertTrue(output_plan.exists())

        apply_code, apply_output = self._run_cli(
            "apply-task-doc-state-sync",
            "--input",
            str(self.state_path),
            "--entity-id",
            "ST01_01",
            "--apply",
        )
        self.assertEqual(apply_code, 0)
        apply_payload = json.loads(apply_output)
        self.assertEqual(apply_payload["mode"], "apply")
        self.assertEqual(apply_payload["summary"]["written_slot_count"], 2)


if __name__ == "__main__":
    unittest.main()
