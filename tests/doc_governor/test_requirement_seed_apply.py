import io
import json
import shutil
import tempfile
import unittest
import uuid
from contextlib import redirect_stdout
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.cli import main
from tools.doc_governor.evaluate import evaluate_state_file
from tools.doc_governor.requirement_seed_apply import (
    build_requirement_seed_apply_plan,
    execute_requirement_seed_apply,
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
            "compliance": schema.make_default_compliance_state(),
        },
        "state": {
            "confirmed": schema.make_default_confirmed_state("module"),
            "tracking": schema.make_default_tracking_state(),
        },
    }


def _subtask_entry(
    task_id: str,
    *,
    module_id: str,
) -> dict:
    confirmed = schema.make_default_confirmed_state("subtask")
    confirmed["implementation_doc_state"] = "active_working_doc"
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


def _build_state() -> dict:
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
        "requirements": {},
        "modules": {
            "M01": _module_entry("M01"),
            "M09": _module_entry("M09"),
        },
        "subtasks": {
            "ST01_01": _subtask_entry("ST01_01", module_id="M01"),
            "ST09_03": _subtask_entry("ST09_03", module_id="M09"),
        },
    }


class RequirementSeedApplyTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "requirement-seed-apply"

    def setUp(self) -> None:
        super().setUp()
        self.state_path = self.temp_root / "docs" / "governance" / "DOC_STATE.yaml"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def _write_state(self, state: dict) -> None:
        self.state_path.write_text(
            yaml.safe_dump(state, sort_keys=False),
            encoding="utf-8",
        )

    def _read_state(self) -> dict:
        return yaml.safe_load(self.state_path.read_text(encoding="utf-8"))

    def _run_cli(self, *args: str) -> tuple[int, str]:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            try:
                exit_code = main(list(args))
            except SystemExit as exc:
                exit_code = int(exc.code)
        return exit_code, stdout.getvalue()

    def test_dry_run_outputs_plan_without_writing_state(self) -> None:
        state = _build_state()
        state["requirements"] = {
            "RQ09": _requirement_entry("RQ09", module_ids=["M09"]),
        }
        self._write_state(state)

        plan = build_requirement_seed_apply_plan(
            state_path=self.state_path,
            entity_ids=["ST09_03"],
        )

        self.assertEqual(plan["mode"], "dry_run")
        self.assertEqual(plan["summary"]["planned_write_count"], 0)
        task = plan["tasks"][0]
        self.assertEqual(task["task_id"], "ST09_03")
        self.assertEqual(task["decision"], "blocked_manual_confirmation")
        self.assertFalse(task["apply_allowed"])
        reloaded = self._read_state()
        self.assertEqual(reloaded["requirements"]["RQ09"]["facts"]["task_ids"], [])

    def test_apply_writes_requirement_relation_when_manually_confirmed_and_unique(self) -> None:
        state = _build_state()
        state["requirements"] = {
            "RQ09": _requirement_entry("RQ09", module_ids=["M09"]),
        }
        self._write_state(state)

        result = execute_requirement_seed_apply(
            state_path=self.state_path,
            entity_ids=["ST09_03"],
            apply_changes=True,
            allow_manual_confirmation=True,
        )

        self.assertEqual(result["mode"], "apply")
        self.assertEqual(result["summary"]["applied_write_count"], 1)
        task = result["tasks"][0]
        self.assertEqual(task["decision"], "written")
        self.assertEqual(task["selected_requirement_id"], "RQ09")
        self.assertEqual(result["affected_tasks"], ["ST09_03"])
        self.assertEqual(result["result_summary"]["affected_tasks"], ["ST09_03"])
        reloaded = self._read_state()
        self.assertEqual(reloaded["requirements"]["RQ09"]["facts"]["task_ids"], ["ST09_03"])

        diagnostics, payload = evaluate_state_file(self.state_path)
        self.assertFalse(any(item.severity == "error" for item in diagnostics))
        blockers = payload["subtasks"]["ST09_03"]["derived"]["blocker_refs"]
        self.assertNotIn("gate:requirement_id_missing", blockers)

    def test_apply_uses_append_if_missing_for_multiple_tasks_on_same_requirement(self) -> None:
        state = _build_state()
        state["requirements"] = {
            "RQ01": _requirement_entry("RQ01", module_ids=["M01", "M09"]),
        }
        self._write_state(state)

        result = execute_requirement_seed_apply(
            state_path=self.state_path,
            entity_ids=["ST09_03", "ST01_01"],
            apply_changes=True,
            allow_manual_confirmation=True,
        )

        self.assertEqual(result["summary"]["applied_write_count"], 2)
        reloaded = self._read_state()
        self.assertEqual(reloaded["requirements"]["RQ01"]["facts"]["task_ids"], ["ST09_03", "ST01_01"])
        written_links = result["result_summary"]["written_requirement_links"]
        self.assertEqual([item["task_id"] for item in written_links], ["ST09_03", "ST01_01"])
        self.assertEqual(result["affected_tasks"], ["ST09_03", "ST01_01"])

    def test_apply_returns_already_linked_without_duplicate_write(self) -> None:
        state = _build_state()
        state["requirements"] = {
            "RQ09": _requirement_entry("RQ09", module_ids=["M09"], task_ids=["ST09_03"]),
        }
        self._write_state(state)

        before_text = self.state_path.read_text(encoding="utf-8")
        result = execute_requirement_seed_apply(
            state_path=self.state_path,
            entity_ids=["ST09_03"],
            apply_changes=True,
            allow_manual_confirmation=True,
        )

        self.assertEqual(result["summary"]["applied_write_count"], 0)
        self.assertEqual(result["tasks"][0]["decision"], "already_linked")
        after_text = self.state_path.read_text(encoding="utf-8")
        self.assertEqual(after_text, before_text)

    def test_apply_preserves_unrelated_yaml_text(self) -> None:
        state = _build_state()
        state["requirements"] = {
            "RQ09": _requirement_entry("RQ09", module_ids=["M09"]),
        }
        self._write_state(state)
        original_text = self.state_path.read_text(encoding="utf-8")
        patched_text = original_text.replace(
            "oqs: {}\n",
            (
                "oqs:\n"
                "  OQ-001:\n"
                "    title: \"需要保留引号\"\n"
                "    status: open\n"
                "    affects:\n"
                "      modules: []\n"
                "      subtasks: []\n"
                "    declared_blocker_refs: []\n"
                "    gate_level: observe_only\n"
                "    gate_policy_source: bootstrap_default\n"
                "    resolution_policy: proposed_default_ok\n"
            ),
        )
        self.state_path.write_text(patched_text, encoding="utf-8")

        execute_requirement_seed_apply(
            state_path=self.state_path,
            entity_ids=["ST09_03"],
            apply_changes=True,
            allow_manual_confirmation=True,
        )

        final_text = self.state_path.read_text(encoding="utf-8")
        self.assertIn('title: "需要保留引号"', final_text)

    def test_apply_rejects_when_manual_confirmation_required_by_default(self) -> None:
        state = _build_state()
        state["requirements"] = {
            "RQ09": _requirement_entry("RQ09", module_ids=["M09"]),
        }
        self._write_state(state)

        with self.assertRaisesRegex(ValueError, "存在不允许 apply 的 task"):
            execute_requirement_seed_apply(
                state_path=self.state_path,
                entity_ids=["ST09_03"],
                apply_changes=True,
            )

        reloaded = self._read_state()
        self.assertEqual(reloaded["requirements"]["RQ09"]["facts"]["task_ids"], [])

    def test_apply_rejects_when_candidates_are_ambiguous(self) -> None:
        state = _build_state()
        state["requirements"] = {
            "RQ01": _requirement_entry("RQ01", module_ids=["M01"]),
            "RQ02": _requirement_entry("RQ02", module_ids=["M01"]),
        }
        self._write_state(state)

        plan = build_requirement_seed_apply_plan(
            state_path=self.state_path,
            entity_ids=["ST01_01"],
            allow_manual_confirmation=True,
        )

        task = plan["tasks"][0]
        self.assertEqual(task["decision"], "blocked_ambiguous")
        self.assertFalse(task["apply_allowed"])
        with self.assertRaisesRegex(ValueError, "存在不允许 apply 的 task"):
            execute_requirement_seed_apply(
                state_path=self.state_path,
                entity_ids=["ST01_01"],
                apply_changes=True,
                allow_manual_confirmation=True,
            )

    def test_apply_does_not_touch_unrelated_tasks(self) -> None:
        state = _build_state()
        state["requirements"] = {
            "RQ01": _requirement_entry("RQ01", module_ids=["M01"], task_ids=["ST01_01"]),
            "RQ09": _requirement_entry("RQ09", module_ids=["M09"]),
        }
        self._write_state(state)

        execute_requirement_seed_apply(
            state_path=self.state_path,
            entity_ids=["ST09_03"],
            apply_changes=True,
            allow_manual_confirmation=True,
        )

        reloaded = self._read_state()
        self.assertEqual(reloaded["requirements"]["RQ01"]["facts"]["task_ids"], ["ST01_01"])
        self.assertEqual(reloaded["requirements"]["RQ09"]["facts"]["task_ids"], ["ST09_03"])

    def test_cli_command_exists_and_supports_dry_run_and_apply(self) -> None:
        state = _build_state()
        state["requirements"] = {
            "RQ09": _requirement_entry("RQ09", module_ids=["M09"]),
        }
        self._write_state(state)
        output_plan = self.temp_root / "seed-plan.json"

        dry_run_code, dry_run_output = self._run_cli(
            "apply-requirement-seed",
            "--input",
            str(self.state_path),
            "--entity-id",
            "ST09_03",
            "--output-plan",
            str(output_plan),
        )
        self.assertEqual(dry_run_code, 0)
        dry_run_payload = json.loads(dry_run_output)
        self.assertEqual(dry_run_payload["mode"], "dry_run")
        self.assertEqual(dry_run_payload["tasks"][0]["decision"], "blocked_manual_confirmation")
        self.assertTrue(output_plan.exists())

        apply_code, apply_output = self._run_cli(
            "apply-requirement-seed",
            "--input",
            str(self.state_path),
            "--entity-id",
            "ST09_03",
            "--apply",
            "--confirm-manual",
        )
        self.assertEqual(apply_code, 0)
        apply_payload = json.loads(apply_output)
        self.assertEqual(apply_payload["mode"], "apply")
        self.assertEqual(apply_payload["summary"]["applied_write_count"], 1)


if __name__ == "__main__":
    unittest.main()
