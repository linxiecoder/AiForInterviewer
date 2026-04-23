import json
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.task_apply import (
    execute_task_readiness_fix,
    render_task_readiness_fix_plan_markdown,
)
from tools.testing.temp_artifacts import ManagedTempArtifactsTestCase


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
        },
        "state": {
            "confirmed": schema.make_default_confirmed_state("module"),
            "tracking": schema.make_default_tracking_state(),
        },
    }


def _subtask_entry(
    task_id: str,
    *,
    module_id: str,
    design_template_like: bool,
    implementation_template_like: bool,
) -> dict:
    confirmed = schema.make_default_confirmed_state("subtask")
    confirmed["implementation_doc_state"] = "missing"
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
            "design_doc": {"exists": True, "template_like": design_template_like},
            "implementation_doc": {"exists": True, "template_like": implementation_template_like},
        },
        "state": {
            "confirmed": confirmed,
            "tracking": schema.make_default_tracking_state(),
        },
    }


def _write_text(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _evaluate_payload() -> dict:
    common_global = [
        "gate:requirement_id_missing",
        "gate:implementation_doc_not_active",
        "policy:formal_window_closed",
    ]
    return {
        "requirements": {},
        "modules": {
            "M01": {"derived": {"blocker_refs": []}},
            "M02": {"derived": {"blocker_refs": ["doc:api", "doc:open_questions"]}},
            "M09": {"derived": {"blocker_refs": []}},
        },
        "subtasks": {
            "ST01_01": {
                "derived": {
                    "blocker_refs": common_global
                    + [
                        "doc:implementation_doc",
                        "doc:design_doc",
                        "gate:implementation_scope_unclear",
                        "gate:required_tests_missing",
                        "gate:acceptance_criteria_missing",
                        "policy:language_non_compliant_lang_heading_not_chinese_by_default",
                    ]
                }
            },
            "ST09_03": {
                "derived": {
                    "blocker_refs": common_global
                    + [
                        "doc:implementation_doc",
                        "gate:implementation_scope_unclear",
                        "gate:acceptance_criteria_missing",
                    ]
                }
            },
            "ST02_03": {
                "derived": {
                    "blocker_refs": common_global
                    + [
                        "doc:implementation_doc",
                        "module:M02",
                        "doc:api",
                        "doc:open_questions",
                    ]
                }
            },
        },
    }


class TaskApplyTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "task-apply"

    def setUp(self) -> None:
        super().setUp()
        self.state_path = self.temp_root / "docs" / "governance" / "DOC_STATE.yaml"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        state = {
            "schema_version": schema.SCHEMA_VERSION,
            "global_policy": {
                "auto_open_enabled": False,
                "require_confirmation_for_state_writeback": True,
                "strict_template_gate": True,
                "formal_window_open": False,
                "paths": {
                    "modules_root": "docs/modules",
                    "open_questions_doc": "OPEN_QUESTIONS.md",
                    "task_index_doc": "TASK_INDEX.md",
                },
            },
            "oqs": {},
            "requirements": {},
            "modules": {
                "M01": _module_entry("M01"),
                "M02": _module_entry("M02"),
                "M09": _module_entry("M09"),
            },
            "subtasks": {
                "ST01_01": _subtask_entry(
                    "ST01_01",
                    module_id="M01",
                    design_template_like=True,
                    implementation_template_like=True,
                ),
                "ST09_03": _subtask_entry(
                    "ST09_03",
                    module_id="M09",
                    design_template_like=False,
                    implementation_template_like=True,
                ),
                "ST02_03": _subtask_entry(
                    "ST02_03",
                    module_id="M02",
                    design_template_like=False,
                    implementation_template_like=True,
                ),
            },
        }
        self.state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

        _write_text(
            self.temp_root,
            "docs/modules/M01-test/sub_modules/ST01_01-test/SUBTASK_DESIGN.md",
            (
                "# Subtask Design\n\n"
                "Current status: draft / reviewable / downstream-ready / blocked\n\n"
                "## Step 1\n"
                "- TODO\n"
            ),
        )
        _write_text(
            self.temp_root,
            "docs/modules/M01-test/sub_modules/ST01_01-test/SUBTASK_IMPLEMENTATION.md",
            (
                "# Subtask Implementation\n\n"
                "Current status: draft / reviewable / implementation-ready / blocked\n\n"
                "## Step 1\n"
                "- TODO\n"
            ),
        )
        _write_text(
            self.temp_root,
            "docs/modules/M09-test/sub_modules/ST09_03-test/SUBTASK_DESIGN.md",
            (
                "# 子任务设计文档\n\n"
                "## 3. 子任务目标\n"
                "- 梳理 apply 输出。\n\n"
                "## 5. 技术方案\n"
                "- 在 preview 基础上落最小章节骨架。\n"
            ),
        )
        _write_text(
            self.temp_root,
            "docs/modules/M09-test/sub_modules/ST09_03-test/SUBTASK_IMPLEMENTATION.md",
            (
                "# API Overview\n\n"
                "Current status: draft / reviewable / implementation-ready / blocked\n\n"
                "## 3. Goal\n"
                "- 输出 apply 计划。\n"
            ),
        )
        _write_text(
            self.temp_root,
            "docs/modules/M02-test/sub_modules/ST02_03-test/SUBTASK_DESIGN.md",
            (
                "# 子任务设计文档\n\n"
                "## 3. 子任务目标\n"
                "- 说明模块依赖链。\n"
            ),
        )
        _write_text(
            self.temp_root,
            "docs/modules/M02-test/sub_modules/ST02_03-test/SUBTASK_IMPLEMENTATION.md",
            (
                "# API Overview\n\n"
                "This document is still in English template mode.\n"
            ),
        )


    def test_dry_run_outputs_plan_without_modifying_files(self) -> None:
        implementation_path = self.temp_root / "docs/modules/M09-test/sub_modules/ST09_03-test/SUBTASK_IMPLEMENTATION.md"
        before = implementation_path.read_text(encoding="utf-8")

        result = execute_task_readiness_fix(
            state_path=self.state_path,
            evaluate_payload=_evaluate_payload(),
            entity_id="ST09_03",
            apply_changes=False,
        )

        after = implementation_path.read_text(encoding="utf-8")
        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "dry_run")
        self.assertEqual(before, after)
        self.assertEqual(result["summary"]["written_file_count"], 0)
        self.assertEqual(result["tasks"][0]["task_id"], "ST09_03")
        markdown = render_task_readiness_fix_plan_markdown(result)
        self.assertIn("任务 readiness 修复执行计划", markdown)

    def test_apply_writes_minimal_markdown_skeleton_only(self) -> None:
        implementation_path = self.temp_root / "docs/modules/M09-test/sub_modules/ST09_03-test/SUBTASK_IMPLEMENTATION.md"
        state_before = self.state_path.read_text(encoding="utf-8")

        result = execute_task_readiness_fix(
            state_path=self.state_path,
            evaluate_payload=_evaluate_payload(),
            entity_id="ST09_03",
            apply_changes=True,
        )

        implementation_text = implementation_path.read_text(encoding="utf-8")
        state_after = self.state_path.read_text(encoding="utf-8")

        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "apply")
        self.assertEqual(result["summary"]["written_file_count"], 1)
        self.assertIn("# 子任务实施文档", implementation_text)
        self.assertIn("## 5. 允许修改范围", implementation_text)
        self.assertIn("待人工填写：allowed_modify_paths", implementation_text)
        self.assertIn("待人工填写：required_tests", implementation_text)
        self.assertIn("待人工填写：acceptance_criteria", implementation_text)
        self.assertNotIn("Current status:", implementation_text)
        self.assertEqual(state_before, state_after)

    def test_requirement_seed_stays_blocked_when_manual_confirmation_is_required(self) -> None:
        result = execute_task_readiness_fix(
            state_path=self.state_path,
            evaluate_payload=_evaluate_payload(),
            entity_id="ST09_03",
            apply_changes=True,
        )

        requirement_action = result["requirement_seed_actions"][0]
        self.assertEqual(requirement_action["status"], "blocked_manual_confirmation")
        self.assertFalse(requirement_action["apply_allowed"])

    def test_deferred_task_is_rejected_for_apply(self) -> None:
        result = execute_task_readiness_fix(
            state_path=self.state_path,
            evaluate_payload=_evaluate_payload(),
            entity_id="ST02_03",
            apply_changes=False,
        )
        self.assertFalse(result["tasks"][0]["apply_allowed"])

        with self.assertRaisesRegex(ValueError, "存在不允许 apply 的 task"):
            execute_task_readiness_fix(
                state_path=self.state_path,
                evaluate_payload=_evaluate_payload(),
                entity_id="ST02_03",
                apply_changes=True,
            )

    def test_only_target_files_can_be_written(self) -> None:
        design_path = self.temp_root / "docs/modules/M01-test/sub_modules/ST01_01-test/SUBTASK_DESIGN.md"
        implementation_path = self.temp_root / "docs/modules/M01-test/sub_modules/ST01_01-test/SUBTASK_IMPLEMENTATION.md"
        unrelated_path = self.temp_root / "docs/modules/M02-test/sub_modules/ST02_03-test/SUBTASK_IMPLEMENTATION.md"

        unrelated_before = unrelated_path.read_text(encoding="utf-8")
        result = execute_task_readiness_fix(
            state_path=self.state_path,
            evaluate_payload=_evaluate_payload(),
            entity_id="ST01_01",
            apply_changes=True,
        )

        self.assertTrue(result["ok"])
        self.assertTrue(design_path.exists())
        self.assertTrue(implementation_path.exists())
        self.assertEqual(unrelated_before, unrelated_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
