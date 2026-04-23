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
from tools.doc_governor.requirement_container_seed import (
    build_requirement_container_seed_plan,
    execute_requirement_container_seed,
)
from tools.doc_governor.requirement_seed_apply import build_requirement_seed_apply_plan
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


class RequirementContainerSeedTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "requirement-container-seed"

    def setUp(self) -> None:
        super().setUp()
        self.state_path = self.temp_root / "docs" / "governance" / "DOC_STATE.yaml"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_state(_build_state())
        for name in ("PLAN_LATEST.md", "MODULE_INDEX.md", "TASK_INDEX.md"):
            (self.temp_root / name).write_text(f"# {name}\n", encoding="utf-8")

    def _write_state(self, state: dict) -> None:
        self.state_path.write_text(
            yaml.safe_dump(state, sort_keys=False, allow_unicode=True),
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

    def test_dry_run_outputs_missing_container_without_writing_state(self) -> None:
        plan = build_requirement_container_seed_plan(state_path=self.state_path)

        self.assertEqual(plan["mode"], "dry_run")
        self.assertEqual(plan["summary"]["missing_container_count"], 1)
        container = plan["containers"][0]
        self.assertEqual(container["requirement_id"], "RQ01")
        self.assertEqual(container["decision"], "blocked_manual_confirmation")
        self.assertEqual(container["skeleton_preview"]["facts"]["task_ids"], [])
        self.assertFalse(container["apply_allowed"])
        self.assertEqual(self._read_state()["requirements"], {})

    def test_apply_writes_minimal_requirement_container(self) -> None:
        result = execute_requirement_container_seed(
            state_path=self.state_path,
            entity_ids=["RQ01"],
            apply_changes=True,
            allow_manual_confirmation=True,
        )

        self.assertEqual(result["mode"], "apply")
        self.assertEqual(result["summary"]["applied_write_count"], 1)
        container = result["containers"][0]
        self.assertEqual(container["decision"], "written")
        self.assertEqual(container["target_path"], "requirements.RQ01")

        reloaded = self._read_state()
        requirement = reloaded["requirements"]["RQ01"]
        self.assertEqual(requirement["meta"]["path"], ".")
        self.assertEqual(requirement["meta"]["scope_kind"], "root_requirement_cluster")
        self.assertEqual(requirement["facts"]["module_ids"], ["M01", "M09"])
        self.assertEqual(requirement["facts"]["task_ids"], [])
        self.assertEqual(
            sorted(requirement["facts"]["asset_slots"].keys()),
            ["module_index", "plan_latest", "task_index"],
        )
        self.assertIn("compliance", requirement["facts"])
        self.assertIn("confirmed", requirement["state"])
        self.assertIn("tracking", requirement["state"])

    def test_apply_does_not_touch_other_objects(self) -> None:
        before = self._read_state()

        execute_requirement_container_seed(
            state_path=self.state_path,
            entity_ids=["RQ01"],
            apply_changes=True,
            allow_manual_confirmation=True,
        )

        after = self._read_state()
        self.assertEqual(after["modules"], before["modules"])
        self.assertEqual(after["subtasks"], before["subtasks"])
        self.assertEqual(after["oqs"], before["oqs"])
        self.assertEqual(after["global_policy"], before["global_policy"])

    def test_apply_preserves_unrelated_yaml_text(self) -> None:
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

        execute_requirement_container_seed(
            state_path=self.state_path,
            entity_ids=["RQ01"],
            apply_changes=True,
            allow_manual_confirmation=True,
        )

        final_text = self.state_path.read_text(encoding="utf-8")
        self.assertIn('title: "需要保留引号"', final_text)

    def test_container_seed_unblocks_requirement_not_in_state_precondition(self) -> None:
        before_plan = build_requirement_seed_apply_plan(
            state_path=self.state_path,
            entity_ids=["ST09_03"],
        )
        self.assertEqual(
            before_plan["tasks"][0]["decision"],
            "blocked_requirement_not_in_state",
        )

        execute_requirement_container_seed(
            state_path=self.state_path,
            entity_ids=["RQ01"],
            apply_changes=True,
            allow_manual_confirmation=True,
        )

        after_plan = build_requirement_seed_apply_plan(
            state_path=self.state_path,
            entity_ids=["ST09_03"],
        )
        self.assertEqual(after_plan["tasks"][0]["decision"], "blocked_manual_confirmation")
        self.assertEqual(self._read_state()["requirements"]["RQ01"]["facts"]["task_ids"], [])

    def test_cli_command_exists_and_supports_dry_run_and_apply(self) -> None:
        output_plan = self.temp_root / "container-plan.json"

        dry_run_code, dry_run_output = self._run_cli(
            "apply-requirement-container-seed",
            "--input",
            str(self.state_path),
            "--entity-id",
            "RQ01",
            "--output-plan",
            str(output_plan),
        )
        self.assertEqual(dry_run_code, 0)
        dry_run_payload = json.loads(dry_run_output)
        self.assertEqual(dry_run_payload["mode"], "dry_run")
        self.assertTrue(output_plan.exists())

        apply_code, apply_output = self._run_cli(
            "apply-requirement-container-seed",
            "--input",
            str(self.state_path),
            "--entity-id",
            "RQ01",
            "--apply",
            "--confirm-manual",
        )
        self.assertEqual(apply_code, 0)
        apply_payload = json.loads(apply_output)
        self.assertEqual(apply_payload["mode"], "apply")
        self.assertEqual(apply_payload["summary"]["applied_write_count"], 1)


if __name__ == "__main__":
    unittest.main()
