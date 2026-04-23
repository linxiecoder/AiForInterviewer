from __future__ import annotations

import textwrap
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

from tools.doc_governor.requirement_scan import scan_requirements
from tools.testing.temp_artifacts import ManagedTempArtifactsTestCase


class RequirementScanTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "requirement-scan"

    def setUp(self) -> None:
        super().setUp()

    def _write_task_index(self, text: str) -> None:
        (self.temp_root / "TASK_INDEX.md").write_text(
            textwrap.dedent(text).strip() + "\n",
            encoding="utf-8",
        )

    def test_scan_root_requirement_cluster_relations(self) -> None:
        (self.temp_root / "PLAN_LATEST.md").write_text("# 计划\n", encoding="utf-8")
        (self.temp_root / "MODULE_INDEX.md").write_text("# 模块\n", encoding="utf-8")
        (self.temp_root / "TASK_INDEX.md").write_text("| Task ID | 对应文档路径 |\n| --- | --- |\n", encoding="utf-8")

        modules = {
            "M01": {"meta": {"path": "docs/modules/M01-user/"}},
            "M02": {"meta": {"path": "docs/modules/M02-interview/"}},
        }
        subtasks = {
            "ST01_01": {"meta": {"module_id": "M01", "path": "docs/modules/M01-user/sub_modules/ST01_01-login/"}},
            "ST02_01": {"meta": {"module_id": "M02", "path": "docs/modules/M02-interview/sub_modules/ST02_01-session/"}},
        }

        result = scan_requirements(
            repo_root=self.temp_root,
            modules=modules,
            subtasks=subtasks,
        )

        self.assertEqual(result["counts"]["requirement"], 1)
        requirement = result["requirements"]["RQ01"]
        self.assertEqual(requirement["meta"]["path"], ".")
        self.assertEqual(requirement["meta"]["scope_kind"], "root_requirement_cluster")
        self.assertEqual(requirement["facts"]["module_ids"], ["M01", "M02"])
        self.assertEqual(requirement["facts"]["task_ids"], ["ST01_01", "ST02_01"])
        self.assertTrue(requirement["facts"]["asset_slots"]["plan_latest"]["exists"])
        self.assertTrue(requirement["facts"]["asset_slots"]["module_index"]["exists"])
        self.assertTrue(requirement["facts"]["asset_slots"]["task_index"]["exists"])

    def test_scan_requires_root_cluster_documents(self) -> None:
        result = scan_requirements(
            repo_root=self.temp_root,
            modules={},
            subtasks={},
        )

        self.assertEqual(result["counts"]["requirement"], 0)
        self.assertEqual(result["requirements"], {})

    def test_scan_supports_multiple_requirements_from_task_index(self) -> None:
        (self.temp_root / "PLAN_LATEST.md").write_text("# 计划\n", encoding="utf-8")
        (self.temp_root / "MODULE_INDEX.md").write_text("# 模块\n", encoding="utf-8")
        self._write_task_index(
            """
            # 任务索引

            | Task ID | 名称 | 父任务 | 前置依赖 | Requirement ID | 对应文档路径 |
            | --- | --- | --- | --- | --- | --- |
            | RQ01 | 用户入口需求 | - | - | - | `docs/requirements/RQ01-user-entry/` |
            | RQ02 | 面试执行需求 | - | - | - | `docs/requirements/RQ02-interview-flow/` |
            | M01 | 用户模块 | - | - | RQ01 | `docs/modules/M01-user/` |
            | M02 | 面试模块 | - | M01 | RQ02 | `docs/modules/M02-interview/` |
            | ST01_01 | 登录流程 | M01 | M01 | RQ01 | `docs/modules/M01-user/sub_modules/ST01_01-login/` |
            | ST02_01 | 面试会话 | M02 | M02 | RQ02 | `docs/modules/M02-interview/sub_modules/ST02_01-session/` |
            """
        )

        modules = {
            "M01": {"meta": {"path": "docs/modules/M01-user/"}},
            "M02": {"meta": {"path": "docs/modules/M02-interview/"}},
        }
        subtasks = {
            "ST01_01": {
                "meta": {
                    "module_id": "M01",
                    "path": "docs/modules/M01-user/sub_modules/ST01_01-login/",
                }
            },
            "ST02_01": {
                "meta": {
                    "module_id": "M02",
                    "path": "docs/modules/M02-interview/sub_modules/ST02_01-session/",
                }
            },
        }

        result = scan_requirements(
            repo_root=self.temp_root,
            modules=modules,
            subtasks=subtasks,
        )

        self.assertEqual(result["counts"]["requirement"], 2)
        self.assertEqual(sorted(result["requirements"].keys()), ["RQ01", "RQ02"])
        self.assertEqual(
            result["requirements"]["RQ01"]["meta"],
            {"path": "docs/requirements/RQ01-user-entry/", "scope_kind": "requirement_dir"},
        )
        self.assertEqual(
            result["requirements"]["RQ02"]["facts"]["module_ids"],
            ["M02"],
        )
        self.assertEqual(
            result["requirements"]["RQ01"]["facts"]["task_ids"],
            ["ST01_01"],
        )
        self.assertEqual(result["module_requirement_ids"]["M01"], ["RQ01"])
        self.assertEqual(result["subtask_requirement_ids"]["ST02_01"], ["RQ02"])

    def test_scan_exposes_ambiguous_requirement_links_from_task_index(self) -> None:
        (self.temp_root / "PLAN_LATEST.md").write_text("# 计划\n", encoding="utf-8")
        (self.temp_root / "MODULE_INDEX.md").write_text("# 模块\n", encoding="utf-8")
        self._write_task_index(
            """
            # 任务索引

            | Task ID | 名称 | 父任务 | 前置依赖 | Requirement ID | 对应文档路径 |
            | --- | --- | --- | --- | --- | --- |
            | RQ01 | 用户入口需求 | - | - | - | `docs/requirements/RQ01-user-entry/` |
            | RQ02 | 面试执行需求 | - | - | - | `docs/requirements/RQ02-interview-flow/` |
            | M01 | 用户模块 | - | - | RQ01 | `docs/modules/M01-user/` |
            | ST01_01 | 登录流程 | M01 | M01 | RQ01, RQ02 | `docs/modules/M01-user/sub_modules/ST01_01-login/` |
            """
        )

        modules = {"M01": {"meta": {"path": "docs/modules/M01-user/"}}}
        subtasks = {
            "ST01_01": {
                "meta": {
                    "module_id": "M01",
                    "path": "docs/modules/M01-user/sub_modules/ST01_01-login/",
                }
            }
        }

        result = scan_requirements(
            repo_root=self.temp_root,
            modules=modules,
            subtasks=subtasks,
        )

        self.assertEqual(result["counts"]["requirement"], 2)
        self.assertEqual(result["subtask_requirement_ids"]["ST01_01"], ["RQ01", "RQ02"])
        self.assertIn("ST01_01", result["requirements"]["RQ01"]["facts"]["task_ids"])
        self.assertIn("ST01_01", result["requirements"]["RQ02"]["facts"]["task_ids"])


if __name__ == "__main__":
    unittest.main()
