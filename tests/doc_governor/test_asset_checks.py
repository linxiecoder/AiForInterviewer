from __future__ import annotations

import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

from tools.doc_governor.artifact_policy import ArtifactPolicy, AssetSlot
from tools.doc_governor.asset_checks import check_repo_assets


def _build_policy() -> ArtifactPolicy:
    return ArtifactPolicy(
        required_root_docs=("MODULE_INDEX.md",),
        module_slots={
            "design": AssetSlot(
                filename="MODULE_DESIGN.md",
                doc_kind="module_design",
                required_headings=("目标", "范围"),
            ),
            "task_index": AssetSlot(
                filename="MODULE_TASK_INDEX.md",
                doc_kind="module_task_index",
            ),
        },
        subtask_slots={
            "design_doc": AssetSlot(
                filename="SUBTASK_DESIGN.md",
                doc_kind="subtask_design",
                required_headings=("目标", "方案"),
            ),
            "implementation_doc": AssetSlot(
                filename="SUBTASK_IMPLEMENTATION.md",
                doc_kind="subtask_implementation",
                required_headings=("步骤", "验证"),
            ),
        },
        module_index_file="MODULE_INDEX.md",
        module_index_id_headers=("模块ID",),
        module_index_path_headers=("路径",),
        subtask_index_file="MODULE_TASK_INDEX.md",
        subtask_index_id_headers=("Task ID",),
        subtask_index_parent_headers=("父任务",),
        subtask_index_path_headers=("对应文档路径",),
    )


class AssetChecksTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(tempfile.gettempdir()) / f"doc-governor-assets-{uuid.uuid4().hex}"
        self.repo_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.repo_root, ignore_errors=True)

    def _write(self, relative_path: str, text: str) -> Path:
        path = self.repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text.strip() + "\n", encoding="utf-8")
        return path

    def _mkdir(self, relative_path: str) -> Path:
        path = self.repo_root / relative_path
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _write_module_index(self, rows: list[tuple[str, str]]) -> None:
        body = "\n".join(f"| {module_id} | {path} |" for module_id, path in rows)
        self._write(
            "MODULE_INDEX.md",
            f"""
            # 模块索引

            | 模块ID | 路径 |
            | --- | --- |
            {body}
            """,
        )

    def _write_task_index(self, module_dir: str, rows: list[tuple[str, str, str]]) -> None:
        body = "\n".join(f"| {task_id} | {parent} | {path} |" for task_id, parent, path in rows)
        self._write(
            f"{module_dir}/MODULE_TASK_INDEX.md",
            f"""
            # 子任务索引

            | Task ID | 父任务 | 对应文档路径 |
            | --- | --- | --- |
            {body}
            """,
        )

    def _write_valid_module_docs(self, module_dir: str) -> None:
        self._write(
            f"{module_dir}/MODULE_DESIGN.md",
            """
            # 模块设计

            ## 目标
            - 说明模块目标

            ## 范围
            - 说明模块范围
            """,
        )

    def _write_valid_subtask_docs(self, subtask_dir: str) -> None:
        self._write(
            f"{subtask_dir}/SUBTASK_DESIGN.md",
            """
            # 子任务设计

            ## 目标
            - 说明子任务目标

            ## 方案
            - 说明子任务方案
            """,
        )
        self._write(
            f"{subtask_dir}/SUBTASK_IMPLEMENTATION.md",
            """
            # 子任务实施

            ## 步骤
            - 执行步骤

            ## 验证
            - 验证步骤
            """,
        )

    def _codes(self, diagnostics: list) -> set[str]:
        return {item.code for item in diagnostics}

    def _assert_common_diagnostic_shape(self, diagnostics: list) -> None:
        self.assertTrue(diagnostics)
        for item in diagnostics:
            self.assertTrue(item.code)
            self.assertTrue(item.severity)
            self.assertTrue(item.entity_type)
            self.assertIsNotNone(item.entity_id)
            self.assertTrue(item.field_path)
            self.assertTrue(item.message)
            self.assertTrue(item.evidence)

    def test_missing_required_doc_and_incomplete_template_are_reported(self) -> None:
        module_dir = "docs/modules/M01-sample"
        subtask_dir = f"{module_dir}/sub_modules/ST01_01-setup"
        self._write_module_index([("M01", module_dir)])
        self._write_valid_module_docs(module_dir)
        self._write_task_index(module_dir, [("ST01_01", "M01", subtask_dir)])
        self._write(
            f"{subtask_dir}/SUBTASK_DESIGN.md",
            """
            # 子任务设计

            ## 目标
            - 说明子任务目标
            """,
        )

        diagnostics = check_repo_assets(self.repo_root, policy=_build_policy())
        codes = self._codes(diagnostics)

        self.assertIn("ASSET_REQUIRED_DOC_MISSING", codes)
        self.assertIn("ASSET_REQUIRED_HEADING_MISSING", codes)
        self._assert_common_diagnostic_shape(diagnostics)

    def test_index_mismatch_orphan_and_obsolete_paths_are_reported(self) -> None:
        module_dir = "docs/modules/M01-sample"
        subtask_dir = f"{module_dir}/sub_modules/ST01_01-setup"
        self._write_module_index([("M99", "docs/modules/M99-missing")])
        self._write_valid_module_docs(module_dir)
        self._write_task_index(
            module_dir,
            [("ST01_09", "M01", f"{module_dir}/sub_modules/ST01_09-missing")],
        )
        self._write_valid_subtask_docs(subtask_dir)

        diagnostics = check_repo_assets(self.repo_root, policy=_build_policy())
        codes = self._codes(diagnostics)

        self.assertIn("ASSET_INDEX_PATH_MISSING", codes)
        self.assertIn("ASSET_ORPHAN_MODULE_DIR", codes)
        self.assertIn("ASSET_ORPHAN_SUBTASK_DIR", codes)

    def test_invalid_names_and_parent_mismatch_are_reported(self) -> None:
        module_dir = "docs/modules/M01-sample"
        subtask_dir = f"{module_dir}/sub_modules/ST01_01-setup"
        self._write_module_index([("M01", module_dir)])
        self._mkdir("docs/modules/module-alpha")
        self._write_valid_module_docs(module_dir)
        self._write_task_index(module_dir, [("ST01_01", "M02", subtask_dir)])
        self._mkdir(f"{module_dir}/sub_modules/task-alpha")
        self._write_valid_subtask_docs(subtask_dir)

        diagnostics = check_repo_assets(self.repo_root, policy=_build_policy())
        codes = self._codes(diagnostics)

        self.assertIn("ASSET_INVALID_MODULE_DIR_NAME", codes)
        self.assertIn("ASSET_INVALID_SUBTASK_DIR_NAME", codes)
        self.assertIn("ASSET_SUBTASK_PARENT_MISMATCH", codes)


if __name__ == "__main__":
    unittest.main()
