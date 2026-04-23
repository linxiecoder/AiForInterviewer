import unittest
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.evaluate import evaluate_state_file
from tools.doc_governor.task_state_writeback import (
    build_task_state_writeback_preview,
    render_task_state_writeback_markdown,
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
            "compliance": schema.make_default_compliance_state(),
        },
        "state": {
            "confirmed": schema.make_default_confirmed_state("module"),
            "tracking": schema.make_default_tracking_state(),
        },
    }


def _subtask_entry(task_id: str, *, module_id: str, implementation_doc_state: str) -> dict:
    confirmed = schema.make_default_confirmed_state("subtask")
    confirmed["implementation_doc_state"] = implementation_doc_state
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
            "design_doc": {"exists": True, "template_like": False},
            "implementation_doc": {"exists": True, "template_like": False},
            "compliance": schema.make_default_compliance_state(),
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


class TaskStateWritebackPreviewTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "task-state-writeback"

    def setUp(self) -> None:
        super().setUp()
        self.state_path = self.temp_root / "docs" / "governance" / "DOC_STATE.yaml"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        requirement_state = schema.make_default_confirmed_state("requirement")
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
            "requirements": {
                "RQ01": {
                    "meta": {"path": ".", "scope_kind": "root_requirement_cluster"},
                    "facts": {
                        "module_ids": ["M01"],
                        "task_ids": ["ST01_01", "ST01_02", "ST01_03"],
                        "asset_slots": {
                            "plan_latest": {"exists": True, "path": "PLAN_LATEST.md"},
                            "module_index": {"exists": True, "path": "MODULE_INDEX.md"},
                            "task_index": {"exists": True, "path": "TASK_INDEX.md"},
                        },
                        "compliance": schema.make_default_compliance_state(),
                    },
                    "state": {
                        "confirmed": requirement_state,
                        "tracking": schema.make_default_tracking_state(),
                    },
                }
            },
            "modules": {
                "M01": _module_entry("M01"),
            },
            "subtasks": {
                "ST01_01": _subtask_entry(
                    "ST01_01",
                    module_id="M01",
                    implementation_doc_state="missing",
                ),
                "ST01_02": _subtask_entry(
                    "ST01_02",
                    module_id="M01",
                    implementation_doc_state="missing",
                ),
                "ST01_03": _subtask_entry(
                    "ST01_03",
                    module_id="M01",
                    implementation_doc_state="active_working_doc",
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
                "# 子任务设计文档\n\n"
                "## 3. 子任务目标\n"
                "- 让 state writeback preview 能判断是否可以激活实施文档状态。\n\n"
                "## 5. 技术方案\n"
                "- 只做 preview，不直接写正式 state。\n"
            ),
        )
        _write_text(
            self.temp_root,
            "docs/modules/M01-test/sub_modules/ST01_01-test/SUBTASK_IMPLEMENTATION.md",
            (
                "# 子任务实施文档\n\n"
                "## 3. 本轮实施目标\n"
                "- 为 state writeback preview 产出 confirm-transition 建议。\n\n"
                "## 5. 允许修改范围\n\n"
                "### 5.1 允许修改\n"
                "- `tools/doc_governor/task_state_writeback.py`\n\n"
                "### 5.2 禁止修改\n"
                "- `docs/governance/DOC_STATE.yaml`\n\n"
                "## 7. 测试与验证\n\n"
                "### 7.1 自动化验证\n"
                "- `python -m pytest tests/doc_governor/test_task_state_writeback.py -q`\n\n"
                "## 8. 完成判定\n"
                "- 能输出 implementation_doc_state 的建议写回方案。\n"
            ),
        )

        _write_text(
            self.temp_root,
            "docs/modules/M01-test/sub_modules/ST01_02-test/SUBTASK_DESIGN.md",
            (
                "# 子任务设计文档\n\n"
                "## 3. 子任务目标\n"
                "- 这是一个仍然缺测试字段的 task。\n\n"
                "## 5. 技术方案\n"
                "- 先保持缺口，验证 preview 会阻断写回。\n"
            ),
        )
        _write_text(
            self.temp_root,
            "docs/modules/M01-test/sub_modules/ST01_02-test/SUBTASK_IMPLEMENTATION.md",
            (
                "# 子任务实施文档\n\n"
                "## 3. 本轮实施目标\n"
                "- 故意不补测试要求。\n\n"
                "## 5. 允许修改范围\n\n"
                "### 5.1 允许修改\n"
                "- `tools/doc_governor/task_state_writeback.py`\n\n"
                "### 5.2 禁止修改\n"
                "- `docs/governance/DOC_STATE.yaml`\n\n"
                "## 8. 完成判定\n"
                "- 故意缺 `required_tests`，用于验证阻断。\n"
            ),
        )

        _write_text(
            self.temp_root,
            "docs/modules/M01-test/sub_modules/ST01_03-test/SUBTASK_DESIGN.md",
            (
                "# 子任务设计文档\n\n"
                "## 3. 子任务目标\n"
                "- 这是一个已激活的 task。\n\n"
                "## 5. 技术方案\n"
                "- 验证 preview 会输出 no-op。\n"
            ),
        )
        _write_text(
            self.temp_root,
            "docs/modules/M01-test/sub_modules/ST01_03-test/SUBTASK_IMPLEMENTATION.md",
            (
                "# 子任务实施文档\n\n"
                "## 3. 本轮实施目标\n"
                "- 已经是 active_working_doc。\n\n"
                "## 5. 允许修改范围\n\n"
                "### 5.1 允许修改\n"
                "- `tools/doc_governor/task_state_writeback.py`\n\n"
                "### 5.2 禁止修改\n"
                "- `docs/governance/DOC_STATE.yaml`\n\n"
                "## 7. 测试与验证\n\n"
                "### 7.1 自动化验证\n"
                "- `python -m pytest tests/doc_governor/test_task_state_writeback.py -q`\n\n"
                "## 8. 完成判定\n"
                "- 已经满足内容层要求。\n"
            ),
        )

    def _evaluate(self) -> dict:
        diagnostics, payload = evaluate_state_file(self.state_path)
        self.assertEqual([item for item in diagnostics if item.severity == "error"], [])
        return payload

    def test_marks_task_as_activation_candidate_when_only_state_window_blockers_remain(self) -> None:
        preview = build_task_state_writeback_preview(
            state_path=self.state_path,
            evaluate_payload=self._evaluate(),
            entity_ids=["ST01_01"],
        )

        self.assertEqual(preview["summary"]["activation_candidate_count"], 1)
        item = preview["tasks"][0]
        self.assertEqual(item["task_id"], "ST01_01")
        self.assertEqual(item["status"], "eligible_activation")
        self.assertEqual(
            item["proposed_changes"],
            {"implementation_doc_state": "active_working_doc"},
        )
        self.assertEqual(
            item["predicted_blocker_refs_after_writeback"],
            ["policy:formal_window_closed"],
        )
        self.assertTrue(item["window_only_after_writeback"])
        self.assertIn("confirm-transition", item["suggested_confirm_command"])

    def test_blocks_writeback_when_non_state_blockers_still_remain(self) -> None:
        preview = build_task_state_writeback_preview(
            state_path=self.state_path,
            evaluate_payload=self._evaluate(),
            entity_ids=["ST01_02"],
        )

        item = preview["tasks"][0]
        self.assertEqual(item["status"], "blocked_other_blockers")
        self.assertFalse(item["eligible_for_writeback"])
        self.assertEqual(item["proposed_changes"], {})
        self.assertIn("manual_fill", item["remaining_gap_categories"])

    def test_marks_already_active_task_as_noop(self) -> None:
        preview = build_task_state_writeback_preview(
            state_path=self.state_path,
            evaluate_payload=self._evaluate(),
            entity_ids=["ST01_03"],
        )

        item = preview["tasks"][0]
        self.assertEqual(item["status"], "already_active")
        self.assertFalse(item["eligible_for_writeback"])
        self.assertEqual(item["proposed_changes"], {})
        self.assertEqual(
            item["predicted_blocker_refs_after_writeback"],
            ["policy:formal_window_closed"],
        )

    def test_supports_markdown_render_and_multi_task_summary(self) -> None:
        preview = build_task_state_writeback_preview(
            state_path=self.state_path,
            evaluate_payload=self._evaluate(),
            entity_ids=["ST01_01", "ST01_02", "ST01_03"],
        )

        markdown = render_task_state_writeback_markdown(preview)
        self.assertEqual(preview["summary"]["selected_task_count"], 3)
        self.assertIn("任务 state 写回预览", markdown)
        self.assertIn("ST01_01", markdown)
        self.assertIn("ST01_02", markdown)
        self.assertIn("ST01_03", markdown)


if __name__ == "__main__":
    unittest.main()
