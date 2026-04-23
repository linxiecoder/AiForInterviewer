import json
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.evaluate import evaluate_state_file
from tools.doc_governor.task_packet import generate_implementation_packet
from tools.testing.temp_artifacts import ManagedTempArtifactsTestCase


def _build_state() -> dict:
    requirement_state = schema.make_default_confirmed_state("requirement")
    module_state = schema.make_default_confirmed_state("module")
    task_state = schema.make_default_confirmed_state("subtask")
    task_state["implementation_doc_state"] = "active_working_doc"
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
            "RQ01": {
                "meta": {"path": ".", "scope_kind": "root_requirement_cluster"},
                "facts": {
                    "module_ids": ["M01"],
                    "task_ids": ["ST01_01"],
                    "asset_slots": {
                        "plan_latest": {"exists": True, "path": "PLAN_LATEST.md"},
                        "module_index": {"exists": True, "path": "MODULE_INDEX.md"},
                        "task_index": {"exists": True, "path": "TASK_INDEX.md"},
                    },
                    "compliance": {
                        "naming_ok": True,
                        "path_ok": True,
                        "relations_ok": True,
                        "language_ok": True,
                        "violations": [],
                    },
                },
                "state": {
                    "confirmed": requirement_state,
                    "tracking": schema.make_default_tracking_state(),
                },
            }
        },
        "modules": {
            "M01": {
                "meta": {"path": "docs/modules/M01-test/"},
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
                    "confirmed": module_state,
                    "tracking": schema.make_default_tracking_state(),
                },
            }
        },
        "subtasks": {
            "ST01_01": {
                "meta": {
                    "module_id": "M01",
                    "path": "docs/modules/M01-test/sub_modules/ST01_01-test/",
                },
                "facts": {
                    "upstream_module_ids": ["M01"],
                    "related_oq_ids": [],
                    "legacy_locked": False,
                    "declared_blocker_refs": [],
                    "design_doc": {"exists": True, "template_like": False},
                    "implementation_doc": {"exists": True, "template_like": False},
                    "compliance": schema.make_default_compliance_state(),
                },
                "state": {
                    "confirmed": task_state,
                    "tracking": schema.make_default_tracking_state(),
                },
            }
        },
    }


def _write_text(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TaskPacketTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "task-packet"

    def setUp(self) -> None:
        super().setUp()
        self.state_path = self.temp_root / "docs" / "governance" / "DOC_STATE.yaml"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(
            yaml.safe_dump(_build_state(), sort_keys=False),
            encoding="utf-8",
        )
        _write_text(
            self.temp_root,
            "docs/modules/M01-test/sub_modules/ST01_01-test/SUBTASK_DESIGN.md",
            (
                "# 子任务设计文档\n\n"
                "## 3. 子任务目标\n\n"
                "- 本子任务要解决的问题：补齐 task-centered implementation packet。\n"
            ),
        )
        _write_text(
            self.temp_root,
            "docs/modules/M01-test/sub_modules/ST01_01-test/SUBTASK_IMPLEMENTATION.md",
            (
                "# 子任务实施文档\n\n"
                "## 3. 本轮实施目标\n\n"
                "- 本轮准备完成什么：生成 implementation packet。\n\n"
                "## 5. 允许修改范围\n\n"
                "### 5.1 允许修改\n"
                "- 允许修改的文件：`apps/api/app/main.py`\n"
                "- 允许修改的文件：`tests/doc_governor/test_task_packet.py`\n\n"
                "### 5.2 禁止修改\n"
                "- 本轮不应修改的目录 / 文件：`docs/governance/DOC_STATE.yaml`\n\n"
                "## 7. 测试与验证\n\n"
                "### 7.1 自动化验证\n"
                "- 计划运行的测试：`python -m pytest tests/doc_governor/test_task_packet.py -q`\n\n"
                "## 8. 完成判定\n\n"
                "- 满足哪些条件可视为本轮完成：packet 文件成功生成并内容完整。\n"
            ),
        )


    def test_generate_implementation_packet_outputs_json_and_markdown(self) -> None:
        diagnostics, payload = evaluate_state_file(self.state_path)
        self.assertEqual([item for item in diagnostics if item.severity == "error"], [])

        output_dir = self.temp_root / "docs" / "governance" / "packets-out"
        result = generate_implementation_packet(
            state_path=str(self.state_path),
            entity_id="ST01_01",
            evaluate_payload=payload,
            output_dir=str(output_dir),
        )
        self.assertTrue(result["ok"])

        packet_json_path = output_dir / "ST01_01.implementation.packet.json"
        packet_md_path = output_dir / "ST01_01.implementation.packet.md"
        self.assertTrue(packet_json_path.exists())
        self.assertTrue(packet_md_path.exists())

        packet = json.loads(packet_json_path.read_text(encoding="utf-8"))
        self.assertEqual(packet["task_id"], "ST01_01")
        self.assertEqual(packet["module_id"], "M01")
        self.assertEqual(packet["requirement_id"], "RQ01")
        self.assertTrue(packet["runtime_artifact"])
        self.assertIn("apps/api/app/main.py", packet["allowed_modify_paths"])
        self.assertIn(
            "python -m pytest tests/doc_governor/test_task_packet.py -q",
            packet["required_tests"],
        )
        self.assertIn("requirement:RQ01", packet["upstream_refs"])

        markdown = packet_md_path.read_text(encoding="utf-8")
        self.assertIn("## 任务目标", markdown)
        self.assertIn("## 允许修改范围", markdown)
        self.assertIn("ST01_01", markdown)

    def test_generate_implementation_packet_uses_native_subtask_requirement_relation(self) -> None:
        state = _build_state()
        state["requirements"] = {
            "RQ01": state["requirements"]["RQ01"],
            "RQ02": {
                "meta": {
                    "path": "docs/requirements/RQ02-interview-flow/",
                    "scope_kind": "requirement_dir",
                },
                "facts": {
                    "module_ids": ["M01"],
                    "task_ids": [],
                    "asset_slots": {
                        "plan_latest": {"exists": True, "path": "PLAN_LATEST.md"},
                        "module_index": {"exists": True, "path": "MODULE_INDEX.md"},
                        "task_index": {"exists": True, "path": "TASK_INDEX.md"},
                    },
                    "compliance": {
                        "naming_ok": True,
                        "path_ok": True,
                        "relations_ok": True,
                        "language_ok": True,
                        "violations": [],
                    },
                },
                "state": {
                    "confirmed": schema.make_default_confirmed_state("requirement"),
                    "tracking": schema.make_default_tracking_state(),
                },
            },
        }
        state["modules"]["M01"]["meta"]["requirement_id"] = "RQ02"
        state["modules"]["M01"]["facts"]["requirement_ids"] = ["RQ02"]
        state["subtasks"]["ST01_01"]["meta"]["requirement_id"] = "RQ02"
        state["subtasks"]["ST01_01"]["facts"]["requirement_ids"] = ["RQ02"]
        self.state_path.write_text(
            yaml.safe_dump(state, sort_keys=False),
            encoding="utf-8",
        )

        diagnostics, payload = evaluate_state_file(self.state_path)
        self.assertEqual([item for item in diagnostics if item.severity == "error"], [])
        self.assertEqual(
            payload["subtasks"]["ST01_01"]["derived"]["implementation_packet_inputs"]["requirement_id"],
            "RQ02",
        )


if __name__ == "__main__":
    unittest.main()
