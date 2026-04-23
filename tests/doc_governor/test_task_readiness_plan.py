import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.task_readiness_plan import (
    build_task_readiness_plan,
    render_task_readiness_markdown,
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


class TaskReadinessPlanTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "task-readiness-plan"

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
                "- 梳理只读 readiness 规划输出。\n\n"
                "## 5. 技术方案\n"
                "- 复用现有 planner 输出。\n"
            ),
        )
        _write_text(
            self.temp_root,
            "docs/modules/M09-test/sub_modules/ST09_03-test/SUBTASK_IMPLEMENTATION.md",
            (
                "# 子任务实施文档\n\n"
                "## 3. 本轮实施目标\n"
                "- 聚合 readiness plan。\n\n"
                "## 7. 测试与验证\n"
                "- `python -m pytest tests/doc_governor/test_task_readiness_plan.py -q`\n"
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
                "This document is still in English template mode.\n\n"
                "## 3. Goal\n"
                "- Describe the migration.\n"
            ),
        )


    def test_aggregates_existing_planners_into_layered_plan(self) -> None:
        plan = build_task_readiness_plan(
            state_path=self.state_path,
            evaluate_payload=_evaluate_payload(),
        )
        self.assertEqual(plan["summary"]["selected_task_count"], 3)
        prerequisite_titles = {item["title"] for item in plan["global_prerequisites"]}
        self.assertIn("先确认 requirement 映射", prerequisite_titles)
        self.assertIn("最后再处理状态位和开窗", prerequisite_titles)
        module_actions = {item["module_id"]: item for item in plan["module_level_actions"]}
        self.assertIn("M02", module_actions)
        self.assertIn("doc:api", module_actions["M02"]["blocker_refs"])

    def test_outputs_candidate_and_deferred_tasks_with_reasons(self) -> None:
        plan = build_task_readiness_plan(
            state_path=self.state_path,
            evaluate_payload=_evaluate_payload(),
        )
        candidate_map = {item["task_id"]: item for item in plan["candidate_tasks"]}
        deferred_map = {item["task_id"]: item for item in plan["deferred_tasks"]}
        self.assertEqual(plan["candidate_tasks"][0]["task_id"], "ST09_03")
        self.assertIn("更适合先打样", candidate_map["ST09_03"]["reason"])
        self.assertIn("旧模板", candidate_map["ST01_01"]["reason"])
        self.assertIn("模块继承", deferred_map["ST02_03"]["reason"])

    def test_builds_task_action_sequences(self) -> None:
        plan = build_task_readiness_plan(
            state_path=self.state_path,
            evaluate_payload=_evaluate_payload(),
        )
        sequences = {item["task_id"]: item for item in plan["task_action_sequences"]}
        st09_steps = [item["title"] for item in sequences["ST09_03"]["actions"]]
        st02_steps = [item["title"] for item in sequences["ST02_03"]["actions"]]
        self.assertIn("先确认 requirement 映射", st09_steps)
        self.assertIn("先修标题/章节结构与中文规则", st09_steps)
        self.assertIn("将模块 blocker 保留在模块层处理", st02_steps)

    def test_supports_entity_scope_and_markdown_render(self) -> None:
        plan = build_task_readiness_plan(
            state_path=self.state_path,
            evaluate_payload=_evaluate_payload(),
            entity_id="M09",
        )
        markdown = render_task_readiness_markdown(plan)
        self.assertEqual(plan["summary"]["selected_scope"], "module")
        self.assertEqual(plan["summary"]["selected_task_count"], 1)
        self.assertIn("任务 readiness 规划", markdown)
        self.assertIn("ST09_03", markdown)


if __name__ == "__main__":
    unittest.main()
