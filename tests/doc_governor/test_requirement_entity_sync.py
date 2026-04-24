import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import yaml

from tools.doc_governor import schema
from tools.doc_governor.cli import main
from tools.doc_governor.requirement_entity_sync import (
    build_requirement_entity_sync_plan,
    execute_requirement_entity_sync,
)
from tools.doc_governor.validate import validate_state_file
from tools.testing.temp_artifacts import ManagedTempArtifactsTestCase


def _requirement_entry(
    requirement_id: str,
    *,
    module_ids: list[str],
    task_ids: list[str],
) -> dict:
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


def _subtask_entry(task_id: str, *, module_id: str) -> dict:
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
        "requirements": {
            "RQ01": _requirement_entry(
                "RQ01",
                module_ids=["M01", "M09"],
                task_ids=["ST01_01", "ST09_03"],
            )
        },
        "modules": {
            "M01": _module_entry("M01"),
            "M09": _module_entry("M09"),
        },
        "subtasks": {
            "ST01_01": _subtask_entry("ST01_01", module_id="M01"),
            "ST09_03": _subtask_entry("ST09_03", module_id="M09"),
        },
    }


class RequirementEntitySyncTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "requirement-entity-sync"

    def setUp(self) -> None:
        super().setUp()
        self.state_path = self.temp_root / "docs" / "governance" / "DOC_STATE.yaml"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_state(_build_state())

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

    def test_dry_run_outputs_plan_without_writing_state(self) -> None:
        before = self.state_path.read_text(encoding="utf-8")

        plan = build_requirement_entity_sync_plan(
            state_path=self.state_path,
            entity_ids=["RQ01"],
        )

        self.assertEqual(plan["mode"], "dry_run")
        self.assertEqual(plan["summary"]["selected_requirement_count"], 1)
        self.assertEqual(plan["summary"]["selected_module_count"], 2)
        self.assertEqual(plan["summary"]["selected_task_count"], 2)
        self.assertEqual(plan["summary"]["planned_write_count"], 4)
        self.assertTrue(
            all(item["decision"] == "planned" for item in plan["entity_relations"])
        )
        self.assertEqual(before, self.state_path.read_text(encoding="utf-8"))

    def test_apply_writes_entity_side_requirement_relations_and_clears_validate_warning(self) -> None:
        result = execute_requirement_entity_sync(
            state_path=self.state_path,
            entity_ids=["RQ01"],
            apply_changes=True,
        )

        self.assertEqual(result["mode"], "apply")
        self.assertEqual(result["summary"]["applied_write_count"], 4)

        reloaded = self._read_state()
        for entity_type, entity_id in (
            ("modules", "M01"),
            ("modules", "M09"),
            ("subtasks", "ST01_01"),
            ("subtasks", "ST09_03"),
        ):
            entity = reloaded[entity_type][entity_id]
            self.assertEqual(entity["meta"]["requirement_id"], "RQ01")
            self.assertEqual(entity["facts"]["requirement_ids"], ["RQ01"])

        diagnostics = validate_state_file(self.state_path)
        codes = [item.code for item in diagnostics]
        self.assertNotIn("SCHEMA_REQUIREMENT_RELATION_ENTITY_MISSING", codes)

    def test_apply_rejects_conflicting_entity_relation(self) -> None:
        state = _build_state()
        state["requirements"]["RQ02"] = _requirement_entry(
            "RQ02",
            module_ids=[],
            task_ids=[],
        )
        state["modules"]["M09"]["meta"]["requirement_id"] = "RQ02"
        state["modules"]["M09"]["facts"]["requirement_ids"] = ["RQ02"]
        self._write_state(state)

        plan = build_requirement_entity_sync_plan(
            state_path=self.state_path,
            entity_ids=["RQ01"],
        )
        relation_map = {
            (item["entity_type"], item["entity_id"]): item for item in plan["entity_relations"]
        }
        self.assertEqual(
            relation_map[("module", "M09")]["decision"],
            "blocked_entity_conflict",
        )

        with self.assertRaisesRegex(ValueError, "存在不允许 apply 的 relation"):
            execute_requirement_entity_sync(
                state_path=self.state_path,
                entity_ids=["RQ01"],
                apply_changes=True,
            )

    def test_cli_command_exists_and_supports_dry_run_and_apply(self) -> None:
        output_plan = self.temp_root / "entity-sync-plan.json"

        dry_run_code, dry_run_output = self._run_cli(
            "apply-requirement-entity-sync",
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
            "apply-requirement-entity-sync",
            "--input",
            str(self.state_path),
            "--entity-id",
            "RQ01",
            "--apply",
        )
        self.assertEqual(apply_code, 0)
        apply_payload = json.loads(apply_output)
        self.assertEqual(apply_payload["mode"], "apply")
        self.assertEqual(apply_payload["summary"]["applied_write_count"], 4)


if __name__ == "__main__":
    unittest.main()
