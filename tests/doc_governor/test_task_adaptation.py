import json
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.task_adaptation import build_task_adaptation_plan, render_task_adaptation_markdown
from tools.testing.temp_artifacts import ManagedTempArtifactsTestCase


def _state_with_tasks() -> dict:
    return {
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
                },
                "state": {"confirmed": schema.make_default_confirmed_state("module")},
            },
            "M02": {
                "meta": {"path": "docs/modules/M02-test/"},
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
                "state": {"confirmed": schema.make_default_confirmed_state("module")},
            },
            "M09": {
                "meta": {"path": "docs/modules/M09-test/"},
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
                "state": {"confirmed": schema.make_default_confirmed_state("module")},
            },
        },
        "subtasks": {
            "ST01_01": {
                "meta": {
                    "module_id": "M01",
                    "path": "docs/modules/M01-test/sub_modules/ST01_01/",
                },
                "facts": {
                    "upstream_module_ids": ["M01"],
                    "related_oq_ids": [],
                    "legacy_locked": False,
                    "declared_blocker_refs": [],
                    "design_doc": {"exists": True, "template_like": True},
                    "implementation_doc": {"exists": True, "template_like": True},
                },
                "state": {"confirmed": schema.make_default_confirmed_state("subtask")},
            },
            "ST01_02": {
                "meta": {
                    "module_id": "M01",
                    "path": "docs/modules/M01-test/sub_modules/ST01_02/",
                },
                "facts": {
                    "upstream_module_ids": ["M01"],
                    "related_oq_ids": [],
                    "legacy_locked": False,
                    "declared_blocker_refs": [],
                    "design_doc": {"exists": True, "template_like": True},
                    "implementation_doc": {"exists": True, "template_like": True},
                },
                "state": {"confirmed": schema.make_default_confirmed_state("subtask")},
            },
            "ST02_03": {
                "meta": {
                    "module_id": "M02",
                    "path": "docs/modules/M02-test/sub_modules/ST02_03/",
                },
                "facts": {
                    "upstream_module_ids": ["M02"],
                    "related_oq_ids": [],
                    "legacy_locked": False,
                    "declared_blocker_refs": [],
                    "design_doc": {"exists": True, "template_like": False},
                    "implementation_doc": {"exists": True, "template_like": True},
                },
                "state": {"confirmed": schema.make_default_confirmed_state("subtask")},
            },
            "ST09_03": {
                "meta": {
                    "module_id": "M09",
                    "path": "docs/modules/M09-test/sub_modules/ST09_03/",
                },
                "facts": {
                    "upstream_module_ids": ["M09"],
                    "related_oq_ids": [],
                    "legacy_locked": False,
                    "declared_blocker_refs": [],
                    "design_doc": {"exists": True, "template_like": False},
                    "implementation_doc": {"exists": True, "template_like": True},
                },
                "state": {"confirmed": schema.make_default_confirmed_state("subtask")},
            },
        },
    }


def _derived(refs: list[str]) -> dict:
    return {
        "current_gate": "implementation_ready",
        "blocker_refs": refs,
        "candidate_blocker_refs": [],
        "downstream_blocker_refs": [ref for ref in refs if ref.startswith("doc:") or ref.startswith("module:")],
        "implementation_blocker_refs": [
            ref
            for ref in refs
            if ref.startswith("gate:") or ref.startswith("policy:")
        ],
        "implementation_ready": False,
    }


def _evaluate_payload() -> dict:
    common_refs = [
        "gate:requirement_id_missing",
        "doc:implementation_doc",
        "gate:implementation_scope_unclear",
        "gate:required_tests_missing",
        "gate:acceptance_criteria_missing",
        "policy:language_non_compliant_lang_heading_not_chinese_by_default",
        "policy:formal_window_closed",
        "gate:implementation_doc_not_active",
    ]
    return {
        "summary": {
            "subtasks_total": 4,
            "subtasks_blocked_count": 4,
        },
        "requirements": {},
        "modules": {
            "M01": {"derived": {"blocker_refs": []}},
            "M02": {"derived": {"blocker_refs": ["doc:api", "doc:open_questions"]}},
            "M09": {"derived": {"blocker_refs": []}},
        },
        "subtasks": {
            "ST01_01": {"derived": _derived(common_refs + ["doc:design_doc"])},
            "ST01_02": {"derived": _derived(common_refs + ["doc:design_doc"])},
            "ST02_03": {
                "derived": _derived(common_refs + ["module:M02", "doc:api", "doc:open_questions"])
            },
            "ST09_03": {"derived": _derived(common_refs)},
        },
    }


class TaskAdaptationPlanTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "task-adaptation"

    def setUp(self) -> None:
        super().setUp()
        self.state_path = self.temp_root / "docs" / "governance" / "DOC_STATE.yaml"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(
            yaml.safe_dump(_state_with_tasks(), sort_keys=False),
            encoding="utf-8",
        )

    def test_build_plan_groups_blockers_and_recommends_order(self) -> None:
        plan = build_task_adaptation_plan(
            state_path=self.state_path,
            evaluate_payload=_evaluate_payload(),
        )
        self.assertEqual(plan["summary"]["selected_task_count"], 4)
        self.assertEqual(plan["summary"]["global_problem_count"], 2)
        categories = {item["category"] for item in plan["blocker_groups"]}
        self.assertIn("global", categories)
        self.assertIn("template_structure", categories)
        self.assertIn("module_inherited", categories)
        self.assertEqual(plan["recommended_order"][0]["focus"], "requirement_relation")
        self.assertEqual(plan["recommended_order"][1]["focus"], "implementation_doc_migration")

    def test_build_plan_outputs_candidate_tasks_examples_and_uncertainty(self) -> None:
        plan = build_task_adaptation_plan(
            state_path=self.state_path,
            evaluate_payload=_evaluate_payload(),
        )
        self.assertEqual(plan["candidate_tasks"][0]["task_id"], "ST09_03")
        self.assertIn("low_blocker_count", plan["candidate_tasks"][0]["reason_keys"])
        self.assertIn("ST01_01", {item["task_id"] for item in plan["ambiguous_candidates"]})
        self.assertTrue(plan["needs_manual_confirmation"])
        example_kinds = {item["example_kind"]: item["task_id"] for item in plan["task_examples"]}
        self.assertEqual(example_kinds["pilot_candidate"], "ST09_03")
        self.assertEqual(example_kinds["old_template_case"], "ST01_01")
        self.assertEqual(example_kinds["module_inherited_case"], "ST02_03")

    def test_build_plan_can_scope_to_module(self) -> None:
        plan = build_task_adaptation_plan(
            state_path=self.state_path,
            evaluate_payload=_evaluate_payload(),
            entity_id="M02",
        )
        self.assertEqual(plan["summary"]["selected_task_count"], 1)
        self.assertEqual(plan["summary"]["selected_entity_id"], "M02")
        self.assertEqual(plan["candidate_tasks"][0]["task_id"], "ST02_03")
        self.assertEqual(plan["module_level_findings"][0]["module_id"], "M02")

    def test_render_markdown_contains_human_readable_sections(self) -> None:
        plan = build_task_adaptation_plan(
            state_path=self.state_path,
            evaluate_payload=_evaluate_payload(),
        )
        markdown = render_task_adaptation_markdown(plan)
        self.assertIn("# 任务适配规划", markdown)
        self.assertIn("## 摘要", markdown)
        self.assertIn("ST09_03", markdown)


if __name__ == "__main__":
    unittest.main()
