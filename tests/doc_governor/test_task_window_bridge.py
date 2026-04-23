import unittest
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.evaluate import evaluate_state_file
from tools.doc_governor.task_window_bridge import build_task_window_bridge
from tools.testing.temp_artifacts import ManagedTempArtifactsTestCase


def _module_entry(
    module_id: str,
    *,
    missing_slots: tuple[str, ...] = (),
) -> dict:
    docs = {
        slot: {"exists": True, "template_like": False}
        for slot in schema.MODULE_DOC_SLOTS
    }
    for slot in missing_slots:
        docs[slot] = {"exists": False, "template_like": True}
    return {
        "meta": {"path": f"docs/modules/{module_id}-test/"},
        "facts": {
            "upstream_module_ids": [],
            "related_oq_ids": [],
            "legacy_locked": False,
            "declared_blocker_refs": [],
            "docs": docs,
            "compliance": schema.make_default_compliance_state(),
        },
        "state": {
            "confirmed": schema.make_default_confirmed_state("module"),
            "tracking": schema.make_default_tracking_state(),
        },
    }


def _requirement_entry(*, module_ids: list[str], task_ids: list[str]) -> dict:
    confirmed = schema.make_default_confirmed_state("requirement")
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
            "confirmed": confirmed,
            "tracking": schema.make_default_tracking_state(),
        },
    }


def _subtask_entry(
    task_id: str,
    *,
    module_id: str,
    implementation_doc_state: str = "missing",
) -> dict:
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


class TaskWindowBridgeTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "task-window-bridge"

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
            "requirements": {
                "RQ01": _requirement_entry(
                    module_ids=["M01", "M02", "M09"],
                    task_ids=["ST01_01", "ST02_03", "ST09_03"],
                )
            },
            "modules": {
                "M01": _module_entry("M01"),
                "M02": _module_entry("M02", missing_slots=("api", "open_questions")),
                "M09": _module_entry("M09"),
            },
            "subtasks": {
                "ST01_01": _subtask_entry("ST01_01", module_id="M01"),
                "ST02_03": _subtask_entry("ST02_03", module_id="M02"),
                "ST09_03": _subtask_entry("ST09_03", module_id="M09"),
            },
        }
        self.state_path.write_text(
            yaml.safe_dump(state, sort_keys=False),
            encoding="utf-8",
        )

        _write_text(
            self.temp_root,
            "docs/modules/M09-test/sub_modules/ST09_03-test/SUBTASK_DESIGN.md",
            (
                "# 子任务设计文档\n\n"
                "## 3. 子任务目标\n"
                "- 作为接近 open-window 的样本。\n\n"
                "## 5. 技术方案\n"
                "- 当前只差 implementation_doc_state 和 formal window。\n"
            ),
        )
        _write_text(
            self.temp_root,
            "docs/modules/M09-test/sub_modules/ST09_03-test/SUBTASK_IMPLEMENTATION.md",
            (
                "# 子任务实施文档\n\n"
                "## 3. 本轮实施目标\n"
                "- 让 bridge 能判断激活后只剩 formal window。\n\n"
                "## 5. 允许修改范围\n\n"
                "### 5.1 允许修改\n"
                "- `tools/doc_governor/task_window_bridge.py`\n\n"
                "### 5.2 禁止修改\n"
                "- `docs/governance/DOC_STATE.yaml`\n\n"
                "## 7. 测试与验证\n"
                "- `python -m pytest tests/doc_governor/test_task_window_bridge.py -q`\n\n"
                "## 8. 完成判定\n"
                "- 输出 bridge 判断结果。\n"
            ),
        )

        _write_text(
            self.temp_root,
            "docs/modules/M01-test/sub_modules/ST01_01-test/SUBTASK_DESIGN.md",
            (
                "# 子任务设计文档\n\n"
                "## 3. 子任务目标\n"
                "- 作为内容 blocker 样本。\n\n"
                "## 5. 技术方案\n"
                "- 故意保留后续人工字段缺口。\n"
            ),
        )
        _write_text(
            self.temp_root,
            "docs/modules/M01-test/sub_modules/ST01_01-test/SUBTASK_IMPLEMENTATION.md",
            (
                "# 子任务实施文档\n\n"
                "## 3. 本轮实施目标\n"
                "- 故意不补 tests 与 acceptance。\n\n"
                "## 5. 允许修改范围\n\n"
                "### 5.1 允许修改\n"
                "- `tools/doc_governor/task_window_bridge.py`\n\n"
                "### 5.2 禁止修改\n"
                "- `docs/governance/DOC_STATE.yaml`\n"
            ),
        )

        _write_text(
            self.temp_root,
            "docs/modules/M02-test/sub_modules/ST02_03-test/SUBTASK_DESIGN.md",
            (
                "# 子任务设计文档\n\n"
                "## 3. 子任务目标\n"
                "- 作为模块继承 blocker 样本。\n\n"
                "## 5. 技术方案\n"
                "- task 自身结构完整，但模块层仍未闭合。\n"
            ),
        )
        _write_text(
            self.temp_root,
            "docs/modules/M02-test/sub_modules/ST02_03-test/SUBTASK_IMPLEMENTATION.md",
            (
                "# 子任务实施文档\n\n"
                "## 3. 本轮实施目标\n"
                "- 验证模块 blocker 不会被误判成 task 层局部问题。\n\n"
                "## 5. 允许修改范围\n\n"
                "### 5.1 允许修改\n"
                "- `tools/doc_governor/task_window_bridge.py`\n\n"
                "### 5.2 禁止修改\n"
                "- `docs/governance/DOC_STATE.yaml`\n\n"
                "## 7. 测试与验证\n"
                "- `python -m pytest tests/doc_governor/test_task_window_bridge.py -q`\n\n"
                "## 8. 完成判定\n"
                "- 保持模块 blocker 留在模块层。\n"
            ),
        )

    def _evaluate(self) -> dict:
        diagnostics, payload = evaluate_state_file(self.state_path)
        self.assertEqual([item for item in diagnostics if item.severity == "error"], [])
        return payload

    def test_distinguishes_candidate_and_blocked_tasks(self) -> None:
        payload = build_task_window_bridge(
            state_path=self.state_path,
            evaluate_payload=self._evaluate(),
            entity_ids=["ST09_03", "ST01_01", "ST02_03"],
        )

        self.assertEqual(payload["summary"]["selected_task_count"], 3)
        self.assertEqual(
            payload["summary"]["candidate_tasks_after_state_activation_count"],
            1,
        )
        self.assertEqual(
            payload["summary"]["blocked_before_open_window_count"],
            2,
        )

        candidate = payload["candidate_tasks_after_state_activation"][0]
        self.assertEqual(candidate["task_id"], "ST09_03")
        self.assertEqual(
            candidate["classification"],
            "window_only_after_state_activation",
        )
        self.assertEqual(
            candidate["predicted_post_activation_blockers"],
            ["policy:formal_window_closed"],
        )

        blocked = {
            item["task_id"]: item for item in payload["blocked_before_open_window"]
        }
        self.assertEqual(blocked["ST01_01"]["classification"], "content_blocked")
        self.assertIn("required_tests", blocked["ST01_01"]["manual_fill_fields"])
        self.assertIn(
            "acceptance_criteria",
            blocked["ST01_01"]["manual_fill_fields"],
        )

        self.assertEqual(
            blocked["ST02_03"]["classification"],
            "module_level_blocked",
        )
        self.assertIn(
            "module:M02",
            blocked["ST02_03"]["current_effective_blockers"],
        )

    def test_outputs_prerequisites_and_predictions(self) -> None:
        payload = build_task_window_bridge(
            state_path=self.state_path,
            evaluate_payload=self._evaluate(),
            entity_ids=["ST09_03", "ST01_01", "ST02_03"],
        )

        prerequisites = {
            item["task_id"]: item for item in payload["state_activation_prerequisites"]
        }
        self.assertTrue(prerequisites["ST09_03"]["content_blockers_cleared"])
        self.assertFalse(prerequisites["ST01_01"]["content_blockers_cleared"])
        self.assertFalse(prerequisites["ST02_03"]["module_level_blockers_cleared"])

        predicted = {
            item["task_id"]: item
            for item in payload["predicted_post_activation_blockers"]
        }
        self.assertTrue(predicted["ST09_03"]["window_only_after_state_activation"])
        self.assertFalse(predicted["ST01_01"]["window_only_after_state_activation"])
        self.assertFalse(predicted["ST02_03"]["window_only_after_state_activation"])

    def test_examples_and_next_steps_cover_named_samples(self) -> None:
        payload = build_task_window_bridge(
            state_path=self.state_path,
            evaluate_payload=self._evaluate(),
            entity_ids=["ST09_03", "ST01_01", "ST02_03"],
        )

        examples = {item["task_id"]: item for item in payload["task_examples"]}
        self.assertTrue(examples["ST09_03"]["why_close_to_open_window"])
        self.assertTrue(examples["ST01_01"]["why_not_open_window_yet"])
        self.assertIn("module:M02", examples["ST02_03"]["module_level_blockers"])

        titles = [item["title"] for item in payload["recommended_next_step"]]
        self.assertIn("优先看首批 state activation 候选", titles)
        self.assertIn("先继续处理内容层缺口", titles)
        self.assertIn("先解决模块继承 blocker", titles)


if __name__ == "__main__":
    unittest.main()
