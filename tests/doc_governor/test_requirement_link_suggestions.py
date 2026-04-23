import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.requirement_link_suggestions import (
    build_requirement_link_suggestions,
    render_requirement_link_suggestions_markdown,
)
from tools.testing.temp_artifacts import ManagedTempArtifactsTestCase


def _requirement_entry(
    requirement_id: str,
    *,
    module_ids: list[str] | None = None,
    task_ids: list[str] | None = None,
    path: str = ".",
) -> dict:
    return {
        "meta": {"path": path, "scope_kind": "root_requirement_cluster"},
        "facts": {
            "module_ids": module_ids or [],
            "task_ids": task_ids or [],
            "asset_slots": {
                "plan_latest": {"exists": True, "path": "PLAN_LATEST.md"},
                "module_index": {"exists": True, "path": "MODULE_INDEX.md"},
                "task_index": {"exists": True, "path": "TASK_INDEX.md"},
            },
            "compliance": schema.make_default_compliance_state(),
        },
        "state": {
            "confirmed": schema.make_default_confirmed_state("requirement"),
            "tracking": schema.make_default_tracking_state(),
        },
    }


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
    module_id: str = "M01",
    path: str | None = None,
) -> dict:
    return {
        "meta": {
            "module_id": module_id,
            "path": path or f"docs/modules/{module_id}-test/sub_modules/{task_id}-test/",
        },
        "facts": {
            "upstream_module_ids": [module_id] if module_id else [],
            "related_oq_ids": [],
            "legacy_locked": False,
            "declared_blocker_refs": [],
            "design_doc": {"exists": True, "template_like": False},
            "implementation_doc": {"exists": True, "template_like": False},
        },
        "state": {
            "confirmed": schema.make_default_confirmed_state("subtask"),
            "tracking": schema.make_default_tracking_state(),
        },
    }


def _build_state() -> dict:
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
        "modules": {"M01": _module_entry("M01"), "M02": _module_entry("M02")},
        "subtasks": {"ST01_01": _subtask_entry("ST01_01")},
    }


class RequirementLinkSuggestionTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "requirement-link-suggestions"

    def setUp(self) -> None:
        super().setUp()
        self.state_path = self.temp_root / "docs" / "governance" / "DOC_STATE.yaml"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def _write_state(self, state: dict) -> None:
        self.state_path.write_text(
            yaml.safe_dump(state, sort_keys=False),
            encoding="utf-8",
        )

    def test_resolves_single_high_confidence_candidate(self) -> None:
        state = _build_state()
        state["requirements"] = {
            "RQ01": _requirement_entry("RQ01", module_ids=["M01"], task_ids=["ST01_01"])
        }
        self._write_state(state)

        suggestions = build_requirement_link_suggestions(state_path=self.state_path)

        self.assertEqual(suggestions["summary"]["resolved_count"], 1)
        resolved = suggestions["resolved_candidates"][0]
        self.assertEqual(resolved["task_id"], "ST01_01")
        self.assertEqual(resolved["selected_requirement_id"], "RQ01")
        self.assertFalse(resolved["needs_manual_confirmation"])
        self.assertEqual(resolved["confidence"]["level"], "high")

    def test_marks_multiple_candidates_as_ambiguous(self) -> None:
        state = _build_state()
        state["requirements"] = {
            "RQ01": _requirement_entry("RQ01", module_ids=["M01"]),
            "RQ02": _requirement_entry("RQ02", module_ids=["M01"]),
        }
        self._write_state(state)

        suggestions = build_requirement_link_suggestions(state_path=self.state_path)

        self.assertEqual(suggestions["summary"]["ambiguous_count"], 1)
        ambiguous = suggestions["ambiguous_candidates"][0]
        self.assertEqual(ambiguous["task_id"], "ST01_01")
        self.assertEqual(ambiguous["candidate_requirement_ids"], ["RQ01", "RQ02"])
        self.assertTrue(ambiguous["needs_manual_confirmation"])
        self.assertIsNone(ambiguous["selected_requirement_id"])

    def test_moves_to_unresolved_when_evidence_is_too_weak(self) -> None:
        state = _build_state()
        state["requirements"] = {}
        state["modules"] = {}
        state["subtasks"] = {
            "ST01_01": _subtask_entry("ST01_01", module_id="", path="")
        }
        self._write_state(state)

        suggestions = build_requirement_link_suggestions(state_path=self.state_path)

        self.assertEqual(suggestions["summary"]["unresolved_count"], 1)
        unresolved = suggestions["unresolved_tasks"][0]
        self.assertEqual(unresolved["task_id"], "ST01_01")
        self.assertTrue(unresolved["needs_manual_confirmation"])

    def test_supports_entity_id_scope_and_markdown_render(self) -> None:
        state = _build_state()
        state["requirements"] = {
            "RQ01": _requirement_entry("RQ01", module_ids=["M01"], task_ids=["ST01_01"]),
            "RQ02": _requirement_entry("RQ02", module_ids=["M02"], task_ids=["ST02_01"]),
        }
        state["subtasks"]["ST02_01"] = _subtask_entry("ST02_01", module_id="M02")
        self._write_state(state)

        suggestions = build_requirement_link_suggestions(
            state_path=self.state_path,
            entity_id="M01",
        )
        markdown = render_requirement_link_suggestions_markdown(suggestions)

        self.assertEqual(suggestions["summary"]["selected_scope"], "module")
        self.assertEqual(suggestions["summary"]["selected_task_count"], 1)
        self.assertIn("任务 requirement 关系建议", markdown)
        self.assertIn("ST01_01", markdown)


if __name__ == "__main__":
    unittest.main()
