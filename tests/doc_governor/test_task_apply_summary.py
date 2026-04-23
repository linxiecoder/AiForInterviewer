import json
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.task_apply import execute_task_readiness_fix
from tools.doc_governor.task_apply_summary import (
    build_task_apply_summary,
    render_task_apply_summary_markdown,
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


def _before_payload() -> dict:
    common_global = [
        "gate:requirement_id_missing",
        "gate:implementation_doc_not_active",
        "policy:formal_window_closed",
    ]
    return {
        "requirements": {},
        "modules": {
            "M01": {"derived": {"blocker_refs": []}},
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
                        "gate:required_tests_missing",
                        "gate:acceptance_criteria_missing",
                        "policy:language_non_compliant_lang_heading_not_chinese_by_default",
                    ]
                }
            },
        },
    }


def _after_payload() -> dict:
    common_global = [
        "gate:requirement_id_missing",
        "gate:implementation_doc_not_active",
        "policy:formal_window_closed",
    ]
    return {
        "requirements": {},
        "modules": {
            "M01": {"derived": {"blocker_refs": []}},
            "M09": {"derived": {"blocker_refs": []}},
        },
        "subtasks": {
            "ST01_01": {
                "derived": {
                    "blocker_refs": common_global
                    + [
                        "gate:implementation_scope_unclear",
                        "gate:required_tests_missing",
                        "gate:acceptance_criteria_missing",
                    ]
                }
            },
            "ST09_03": {
                "derived": {
                    "blocker_refs": common_global
                    + [
                        "gate:implementation_scope_unclear",
                        "gate:required_tests_missing",
                        "gate:acceptance_criteria_missing",
                    ]
                }
            },
        },
    }


class TaskApplySummaryTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "task-apply-summary"

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
                "- 梳理 apply summary 输出。\n\n"
                "## 5. 技术方案\n"
                "- 在 apply 后重新总结缺口。\n"
            ),
        )
        _write_text(
            self.temp_root,
            "docs/modules/M09-test/sub_modules/ST09_03-test/SUBTASK_IMPLEMENTATION.md",
            (
                "# API Overview\n\n"
                "Current status: draft / reviewable / implementation-ready / blocked\n\n"
                "## 3. Goal\n"
                "- 输出 apply summary。\n"
            ),
        )

        execute_task_readiness_fix(
            state_path=self.state_path,
            evaluate_payload=_before_payload(),
            entity_id="ST09_03",
            apply_changes=True,
        )
        execute_task_readiness_fix(
            state_path=self.state_path,
            evaluate_payload=_before_payload(),
            entity_id="ST01_01",
            apply_changes=True,
        )


    def test_summarizes_resolved_and_remaining_blockers(self) -> None:
        summary = build_task_apply_summary(
            state_path=self.state_path,
            after_evaluate_payload=_after_payload(),
            entity_ids=["ST09_03"],
        )
        resolved = summary["resolved_blockers"]
        remaining = summary["remaining_blockers"]
        manual = summary["manual_fill_remaining"]

        self.assertTrue(any(item["blocker"] == "doc:implementation_doc" for item in resolved))
        self.assertTrue(any(item["blocker"] == "policy:language_non_compliant_lang_heading_not_chinese_by_default" for item in resolved))
        self.assertTrue(any(item["blocker"] == "gate:implementation_scope_unclear" for item in remaining))
        self.assertEqual(manual[0]["fields"], ["allowed_modify_paths", "required_tests", "acceptance_criteria"])

    def test_detects_shift_from_template_problem_to_manual_fill_gap(self) -> None:
        summary = build_task_apply_summary(
            state_path=self.state_path,
            after_evaluate_payload=_after_payload(),
            entity_ids=["ST09_03"],
        )
        gap = summary["newly_exposed_gaps"][0]
        self.assertEqual(gap["task_id"], "ST09_03")
        self.assertIn("allowed_modify_paths", gap["fields"])
        self.assertIn("结构性问题已初步清掉", gap["reason"])
        manual = summary["manual_fill_remaining"][0]
        self.assertEqual(
            manual["fields"],
            ["allowed_modify_paths", "required_tests", "acceptance_criteria"],
        )

    def test_outputs_task_level_next_actions(self) -> None:
        summary = build_task_apply_summary(
            state_path=self.state_path,
            after_evaluate_payload=_after_payload(),
            entity_ids=["ST01_01", "ST09_03"],
        )
        task_map = {item["task_id"]: item for item in summary["task_status_after_apply"]}
        st01 = task_map["ST01_01"]
        self.assertTrue(st01["closer_to_implementation_ready"])
        self.assertIn("manual_fill", st01["remaining_gap_categories"])
        self.assertTrue(any(item["scope"] == "task" and item["task_id"] == "ST01_01" for item in summary["next_actions"]))

    def test_supports_markdown_render_and_multi_task(self) -> None:
        summary = build_task_apply_summary(
            state_path=self.state_path,
            after_evaluate_payload=_after_payload(),
            entity_ids=["ST01_01", "ST09_03"],
        )
        markdown = render_task_apply_summary_markdown(summary)
        self.assertEqual(summary["summary"]["selected_task_count"], 2)
        self.assertIn("任务 apply 结果总结", markdown)
        self.assertIn("ST01_01", markdown)


if __name__ == "__main__":
    unittest.main()
