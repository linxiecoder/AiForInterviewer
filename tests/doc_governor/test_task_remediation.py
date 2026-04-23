import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.task_remediation import (
    build_task_remediation_plan,
    render_task_remediation_markdown,
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
            "confirmed": schema.make_default_confirmed_state("subtask"),
            "tracking": schema.make_default_tracking_state(),
        },
    }


def _write_text(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _evaluate_payload() -> dict:
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
                    "blocker_refs": [
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
                    "blocker_refs": [
                        "doc:implementation_doc",
                        "gate:implementation_scope_unclear",
                        "gate:acceptance_criteria_missing",
                    ]
                }
            },
            "ST02_03": {
                "derived": {
                    "blocker_refs": [
                        "doc:implementation_doc",
                        "module:M02",
                        "doc:api",
                        "doc:open_questions",
                    ]
                }
            },
        },
    }


class TaskRemediationPlanTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "task-remediation"

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
        self.state_path.write_text(
            yaml.safe_dump(state, sort_keys=False),
            encoding="utf-8",
        )

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
                "## Step 2\n"
                "- TODO\n"
            ),
        )
        _write_text(
            self.temp_root,
            "docs/modules/M09-test/sub_modules/ST09_03-test/SUBTASK_DESIGN.md",
            (
                "# 子任务设计文档\n\n"
                "## 3. 子任务目标\n"
                "- 梳理生命周期规则。\n"
                "## 5. 技术方案\n"
                "- 保留现有规则说明。\n"
            ),
        )
        _write_text(
            self.temp_root,
            "docs/modules/M09-test/sub_modules/ST09_03-test/SUBTASK_IMPLEMENTATION.md",
            (
                "# 子任务实施文档\n\n"
                "## 3. 本轮实施目标\n"
                "- 先梳理规则迁移边界。\n"
                "## 7. 测试与验证\n"
                "- `python -m pytest tests/doc_governor/test_task_remediation.py -q`\n"
            ),
        )
        _write_text(
            self.temp_root,
            "docs/modules/M02-test/sub_modules/ST02_03-test/SUBTASK_DESIGN.md",
            (
                "# 子任务设计文档\n\n"
                "## 3. 子任务目标\n"
                "- 收敛授权矩阵。\n"
            ),
        )
        _write_text(
            self.temp_root,
            "docs/modules/M02-test/sub_modules/ST02_03-test/SUBTASK_IMPLEMENTATION.md",
            (
                "# API Overview\n\n"
                "This document is still in English template mode.\n\n"
                "## 3. Goal\n"
                "- Describe the migration.\n"
            ),
        )


    def test_identifies_template_and_language_issues(self) -> None:
        plan = build_task_remediation_plan(
            state_path=self.state_path,
            evaluate_payload=_evaluate_payload(),
        )
        findings = {item["task_id"]: item for item in plan["document_findings"]}
        st01 = findings["ST01_01"]
        self.assertTrue(st01["implementation_doc"]["template_like"])
        self.assertTrue(st01["design_doc"]["template_like"])
        self.assertTrue(st01["implementation_doc"]["old_status_semantics"])
        self.assertGreater(st01["implementation_doc"]["language_violation_count"], 0)

    def test_distinguishes_carry_over_and_manual_fill(self) -> None:
        plan = build_task_remediation_plan(
            state_path=self.state_path,
            evaluate_payload=_evaluate_payload(),
        )
        carry_over = {item["task_id"]: item for item in plan["carry_over_candidates"]}
        manual_fill = {item["task_id"]: item for item in plan["manual_fill_required"]}
        st09_carry = carry_over["ST09_03"]
        st09_manual = manual_fill["ST09_03"]
        self.assertIn("goal", st09_carry["fields"])
        self.assertIn("required_tests", st09_carry["fields"])
        self.assertIn("allowed_modify_paths", st09_manual["fields"])
        self.assertIn("acceptance_criteria", st09_manual["fields"])

    def test_preserves_module_inherited_blockers_and_samples(self) -> None:
        plan = build_task_remediation_plan(
            state_path=self.state_path,
            evaluate_payload=_evaluate_payload(),
        )
        blocking = {item["task_id"]: item for item in plan["blocking_issues"]}
        st02 = blocking["ST02_03"]
        self.assertIn("module:M02", st02["module_inherited_blockers"])
        sample_map = {item["example_kind"]: item["task_id"] for item in plan["sample_tasks"]}
        self.assertEqual(sample_map["old_template_case"], "ST01_01")
        self.assertEqual(sample_map["pilot_candidate"], "ST09_03")
        self.assertEqual(sample_map["module_inherited_case"], "ST02_03")

    def test_supports_entity_scope_and_markdown_render(self) -> None:
        plan = build_task_remediation_plan(
            state_path=self.state_path,
            evaluate_payload=_evaluate_payload(),
            entity_id="M09",
        )
        markdown = render_task_remediation_markdown(plan)
        self.assertEqual(plan["summary"]["selected_scope"], "module")
        self.assertEqual(plan["summary"]["selected_task_count"], 1)
        self.assertIn("任务文档整改规划", markdown)
        self.assertIn("ST09_03", markdown)


if __name__ == "__main__":
    unittest.main()
