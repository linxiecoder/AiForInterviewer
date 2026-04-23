import unittest
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.evaluate import evaluate_state_file
from tools.doc_governor.task_state_apply import execute_task_state_apply
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


class TaskStateApplyTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "task-state-apply"

    def setUp(self) -> None:
        super().setUp()
        self.state_path = self.temp_root / "docs" / "governance" / "DOC_STATE.yaml"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.history_path = self.state_path.parent / "transition_history.jsonl"

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
                        "task_ids": ["ST01_01", "ST01_02"],
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
                "- 让 task state apply wrapper 能安全推进 implementation_doc_state。\n\n"
                "## 5. 技术方案\n"
                "- 底层继续走 confirm-transition。\n"
            ),
        )
        _write_text(
            self.temp_root,
            "docs/modules/M01-test/sub_modules/ST01_01-test/SUBTASK_IMPLEMENTATION.md",
            (
                "# 子任务实施文档\n\n"
                "## 3. 本轮实施目标\n"
                "- 为 implementation_doc_state 提供受约束 dry-run/apply wrapper。\n\n"
                "## 5. 允许修改范围\n\n"
                "### 5.1 允许修改\n"
                "- `tools/doc_governor/task_state_apply.py`\n\n"
                "### 5.2 禁止修改\n"
                "- `docs/governance/DOC_STATE.yaml`\n\n"
                "## 7. 测试与验证\n\n"
                "### 7.1 自动化验证\n"
                "- `python -m pytest tests/doc_governor/test_task_state_apply.py -q`\n\n"
                "## 8. 完成判定\n"
                "- wrapper 能通过 confirm-transition 做受控 state 推进。\n"
            ),
        )

        _write_text(
            self.temp_root,
            "docs/modules/M01-test/sub_modules/ST01_02-test/SUBTASK_DESIGN.md",
            (
                "# 子任务设计文档\n\n"
                "## 3. 子任务目标\n"
                "- 保留内容缺口，验证 apply 会被拒绝。\n\n"
                "## 5. 技术方案\n"
                "- 本任务故意不补测试要求。\n"
            ),
        )
        _write_text(
            self.temp_root,
            "docs/modules/M01-test/sub_modules/ST01_02-test/SUBTASK_IMPLEMENTATION.md",
            (
                "# 子任务实施文档\n\n"
                "## 3. 本轮实施目标\n"
                "- 故意保持内容 blocker。\n\n"
                "## 5. 允许修改范围\n\n"
                "### 5.1 允许修改\n"
                "- `tools/doc_governor/task_state_apply.py`\n\n"
                "### 5.2 禁止修改\n"
                "- `docs/governance/DOC_STATE.yaml`\n\n"
                "## 8. 完成判定\n"
                "- 故意缺 `required_tests`，用于验证阻断。\n"
            ),
        )

    def _evaluate(self) -> dict:
        diagnostics, payload = evaluate_state_file(self.state_path)
        self.assertEqual([item for item in diagnostics if item.severity == "error"], [])
        return payload

    def test_dry_run_reports_confirm_transition_preview_without_writing_state(self) -> None:
        before = self.state_path.read_text(encoding="utf-8")
        result = execute_task_state_apply(
            state_path=self.state_path,
            evaluate_payload=self._evaluate(),
            entity_ids=["ST01_01"],
            apply_changes=False,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "dry_run")
        self.assertEqual(result["summary"]["eligible_task_count"], 1)
        task = result["tasks"][0]
        self.assertTrue(task["apply_allowed"])
        self.assertEqual(task["recommended_value"], "active_working_doc")
        self.assertEqual(task["write_target_path"], self.state_path.as_posix())
        self.assertTrue(task["dry_run_result"]["ok"])
        self.assertTrue(task["suggest_preflight_open_window"])
        self.assertEqual(before, self.state_path.read_text(encoding="utf-8"))
        self.assertFalse(self.history_path.exists())

    def test_apply_updates_implementation_doc_state_via_confirm_transition(self) -> None:
        result = execute_task_state_apply(
            state_path=self.state_path,
            evaluate_payload=self._evaluate(),
            entity_ids=["ST01_01"],
            apply_changes=True,
            actor="alice",
            reason="activate implementation doc state",
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "apply")
        self.assertEqual(result["summary"]["applied_task_count"], 1)
        task = result["tasks"][0]
        self.assertTrue(task["apply_result"]["ok"])

        state = yaml.safe_load(self.state_path.read_text(encoding="utf-8"))
        confirmed = state["subtasks"]["ST01_01"]["state"]["confirmed"]
        self.assertEqual(confirmed["implementation_doc_state"], "active_working_doc")
        self.assertEqual(confirmed["last_confirmed_by"], "alice")
        self.assertTrue(self.history_path.exists())

    def test_apply_rejects_when_content_blockers_remain(self) -> None:
        with self.assertRaisesRegex(ValueError, "存在不允许 apply 的 task"):
            execute_task_state_apply(
                state_path=self.state_path,
                evaluate_payload=self._evaluate(),
                entity_ids=["ST01_02"],
                apply_changes=True,
                actor="alice",
                reason="activate implementation doc state",
            )

    def test_apply_requires_actor_and_reason(self) -> None:
        with self.assertRaisesRegex(ValueError, "apply 模式必须显式提供 --actor"):
            execute_task_state_apply(
                state_path=self.state_path,
                evaluate_payload=self._evaluate(),
                entity_ids=["ST01_01"],
                apply_changes=True,
                reason="activate implementation doc state",
            )

        with self.assertRaisesRegex(ValueError, "apply 模式必须显式提供 --reason"):
            execute_task_state_apply(
                state_path=self.state_path,
                evaluate_payload=self._evaluate(),
                entity_ids=["ST01_01"],
                apply_changes=True,
                actor="alice",
            )

    def test_limits_selected_task_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "一次最多只允许处理 3 个 task"):
            execute_task_state_apply(
                state_path=self.state_path,
                evaluate_payload=self._evaluate(),
                entity_ids=["ST01_01", "ST01_02", "ST01_03", "ST01_04"],
                apply_changes=False,
            )


if __name__ == "__main__":
    unittest.main()
