from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.bootstrap import build_bootstrap_state
from tools.doc_governor.evaluate import evaluate_state_file
from tools.doc_governor.requirement_scan import scan_requirements
from tools.testing.temp_artifacts import ManagedTempArtifactsTestCase


def _module_scan_entry(path: str) -> dict:
    return {
        "meta": {"path": path},
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
    }


def _subtask_scan_entry(*, module_id: str, path: str) -> dict:
    return {
        "meta": {"module_id": module_id, "path": path},
        "facts": {
            "upstream_module_ids": [module_id],
            "related_oq_ids": [],
            "legacy_locked": False,
            "declared_blocker_refs": [],
            "design_doc": {"exists": True, "template_like": False},
            "implementation_doc": {"exists": False, "template_like": False},
        },
    }


class MultiRequirementPathsTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "multi-requirement-paths"

    def _write_root_assets(self) -> None:
        (self.temp_root / "PLAN_LATEST.md").write_text("# 计划\n", encoding="utf-8")
        (self.temp_root / "MODULE_INDEX.md").write_text("# 模块\n", encoding="utf-8")

    def _write_task_index(self, text: str) -> None:
        (self.temp_root / "TASK_INDEX.md").write_text(text.strip() + "\n", encoding="utf-8")

    def test_bootstrap_scan_can_surface_requirement_ambiguity_for_evaluate(self) -> None:
        self._write_root_assets()
        self._write_task_index(
            """
| Task ID | 名称 | 父任务 | 前置依赖 | Requirement ID | 对应文档路径 |
| --- | --- | --- | --- | --- | --- |
| RQ01 | 用户入口需求 | - | - | - | `docs/requirements/RQ01-user-entry/` |
| RQ02 | 面试执行需求 | - | - | - | `docs/requirements/RQ02-interview-flow/` |
| M01 | 用户模块 | - | - | RQ01 | `docs/modules/M01-user/` |
| ST01_01 | 登录流程 | M01 | M01 | RQ01, RQ02 | `docs/modules/M01-user/sub_modules/ST01_01-login/` |
            """
        )

        modules = {"M01": _module_scan_entry("docs/modules/M01-user/")}
        subtasks = {
            "ST01_01": _subtask_scan_entry(
                module_id="M01",
                path="docs/modules/M01-user/sub_modules/ST01_01-login/",
            )
        }
        requirement_result = scan_requirements(
            repo_root=self.temp_root,
            modules=modules,
            subtasks=subtasks,
        )

        scan_result = {
            "diagnostics": list(requirement_result["diagnostics"]),
            "oqs": {},
            "requirements": requirement_result["requirements"],
            "modules": modules,
            "subtasks": subtasks,
            "module_requirement_ids": requirement_result["module_requirement_ids"],
            "subtask_requirement_ids": requirement_result["subtask_requirement_ids"],
        }
        state, diagnostics = build_bootstrap_state(scan_result)
        self.assertEqual([item for item in diagnostics if item.severity == "error"], [])

        state_path = self.temp_root / "docs" / "governance" / "DOC_STATE.yaml"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")

        eval_diagnostics, payload = evaluate_state_file(state_path)
        self.assertEqual([item for item in eval_diagnostics if item.severity == "error"], [])
        blockers = payload["subtasks"]["ST01_01"]["derived"]["implementation_blocker_refs"]
        self.assertIn("gate:requirement_id_ambiguous", blockers)
