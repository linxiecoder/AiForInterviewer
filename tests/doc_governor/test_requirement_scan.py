from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
