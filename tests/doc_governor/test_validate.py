import io
from pathlib import Path
import shutil
import tempfile
import unittest
import uuid
import yaml

from tools.doc_governor import schema
from tools.doc_governor.validate import validate_state_file
from tools.testing.temp_artifacts import ManagedTempArtifactsTestCase


def _build_valid_state() -> dict:
    module_path = "docs/modules/M01-test/"
    subtask_path = "docs/modules/M01-test/sub_modules/ST01_01-test/"
    docs = {
        slot: {"exists": True, "template_like": False}
        for slot in schema.MODULE_DOC_SLOTS
    }
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
            "asset_policy": {
                "requirement_mode": "root_requirement_cluster",
            },
        },
        "oqs": {},
        "requirements": {
            "RQ01": {
                "meta": {
                    "path": ".",
                    "scope_kind": "root_requirement_cluster",
                },
                "facts": {
                    "module_ids": ["M01"],
                    "task_ids": ["ST01_01"],
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
        },
        "modules": {
            "M01": {
                "meta": {"path": module_path},
                "facts": {
                    "upstream_module_ids": [],
                    "related_oq_ids": [],
                    "legacy_locked": False,
                    "declared_blocker_refs": [],
                    "docs": docs,
                    "compliance": schema.make_default_compliance_state(),
                },
                "state": {
                    "confirmed": schema.make_default_confirmed_state("module"),
                    "tracking": schema.make_default_tracking_state(),
                },
            }
        },
        "subtasks": {
            "ST01_01": {
                "meta": {
                    "module_id": "M01",
                    "path": subtask_path,
                },
                "facts": {
                    "upstream_module_ids": [],
                    "related_oq_ids": [],
                    "legacy_locked": False,
                    "declared_blocker_refs": [],
                    "design_doc": {"exists": True, "template_like": False},
                    "implementation_doc": {"exists": True, "template_like": False},
                    "compliance": schema.make_default_compliance_state(),
                },
                "state": {
                    "confirmed": schema.make_default_confirmed_state("subtask"),
                    "tracking": schema.make_default_tracking_state(),
                },
            }
        },
    }


class ValidateSchemaTests(ManagedTempArtifactsTestCase):
    managed_temp_dir_label = "validate"

    def setUp(self) -> None:
        super().setUp()

    def _write_state(self, state: dict) -> Path:
        file_path = self.temp_root / "DOC_STATE.bootstrap.yaml"
        file_path.write_text(yaml.safe_dump(state), encoding="utf-8")
        return file_path

    def _run_validate(self, state_path: Path) -> tuple[int, list]:
        diagnostics = validate_state_file(state_path)
        exit_code = 1 if any(item.severity == "error" for item in diagnostics) else 0
        return exit_code, diagnostics

    def _assert_common_diagnostic_shape(self, diagnostics: list) -> None:
        for item in diagnostics:
            self.assertTrue(item.code)
            self.assertTrue(item.severity)
            self.assertTrue(item.entity_type)
            self.assertIsNotNone(item.entity_id)
            self.assertTrue(item.field_path)
            self.assertTrue(item.message)
            self.assertTrue(item.evidence, f"{item.code} has empty evidence")

    def test_schema_version_missing(self) -> None:
        state = _build_valid_state()
        del state["schema_version"]
        state_path = self._write_state(state)

        exit_code, diagnostics = self._run_validate(state_path)
        codes = {item.code for item in diagnostics}

        self.assertEqual(exit_code, 1)
        self.assertIn("SCHEMA_MISSING_REQUIRED_FIELD", codes)

    def test_unknown_enum_value(self) -> None:
        state = _build_valid_state()
        state["modules"]["M01"]["state"]["confirmed"]["candidate_status"] = "invalid"
        state_path = self._write_state(state)

        exit_code, diagnostics = self._run_validate(state_path)
        codes = [item.code for item in diagnostics]

        self.assertEqual(exit_code, 1)
        self.assertIn("SCHEMA_UNKNOWN_ENUM_VALUE", codes)

    def test_invalid_typed_blocker_ref(self) -> None:
        state = _build_valid_state()
        state["modules"]["M01"]["state"]["confirmed"]["blocker_refs"] = ["invalid:ref"]
        state_path = self._write_state(state)

        exit_code, diagnostics = self._run_validate(state_path)
        codes = [item.code for item in diagnostics]
        self.assertEqual(exit_code, 1)
        self.assertIn("SCHEMA_INVALID_TYPED_REF", codes)

    def test_module_and_subtask_path_id_mismatch(self) -> None:
        state = _build_valid_state()
        state["modules"]["M01"]["meta"]["path"] = "docs/modules/M02-test/"
        state["subtasks"]["ST01_01"]["meta"]["path"] = (
            "docs/modules/M01-test/sub_modules/ST01_09-test/"
        )
        state_path = self._write_state(state)

        exit_code, diagnostics = self._run_validate(state_path)
        codes = [item.code for item in diagnostics]
        self.assertEqual(exit_code, 1)
        self.assertIn("SCHEMA_PATH_ID_MISMATCH", codes)

    def test_unknown_doc_slot(self) -> None:
        state = _build_valid_state()
        state["modules"]["M01"]["facts"]["docs"]["unexpected"] = {
            "exists": True,
            "template_like": False,
        }
        state_path = self._write_state(state)

        exit_code, diagnostics = self._run_validate(state_path)
        codes = [item.code for item in diagnostics]
        self.assertIn("SCHEMA_UNKNOWN_DOC_SLOT", codes)
        self.assertEqual(exit_code, 1)

    def test_requirement_path_and_id_validation(self) -> None:
        state = _build_valid_state()
        state["requirements"]["R1"] = state["requirements"].pop("RQ01")
        state["requirements"]["R1"]["meta"]["path"] = "docs/requirements/RQ09-bad/"
        state_path = self._write_state(state)

        exit_code, diagnostics = self._run_validate(state_path)
        codes = [item.code for item in diagnostics]
        self.assertEqual(exit_code, 1)
        self.assertIn("SCHEMA_UNKNOWN_ENUM_VALUE", codes)

    def test_requirement_tracking_and_compliance_shape_validation(self) -> None:
        state = _build_valid_state()
        state["requirements"]["RQ01"]["state"]["tracking"]["active_round_id"] = 123
        state["requirements"]["RQ01"]["facts"]["compliance"]["violations"] = "bad"
        state_path = self._write_state(state)

        exit_code, diagnostics = self._run_validate(state_path)
        codes = [item.code for item in diagnostics]
        self.assertEqual(exit_code, 1)
        self.assertIn("SCHEMA_INVALID_TRACKING_FIELD", codes)
        self.assertIn("SCHEMA_INVALID_COMPLIANCE_FIELD", codes)

    def test_requirement_relation_fields_accept_known_consistent_ids(self) -> None:
        state = _build_valid_state()
        state["modules"]["M01"]["meta"]["requirement_id"] = "RQ01"
        state["modules"]["M01"]["facts"]["requirement_ids"] = ["RQ01"]
        state["subtasks"]["ST01_01"]["meta"]["requirement_id"] = "RQ01"
        state["subtasks"]["ST01_01"]["facts"]["requirement_ids"] = ["RQ01"]
        state_path = self._write_state(state)

        exit_code, diagnostics = self._run_validate(state_path)
        self.assertEqual(exit_code, 0)
        self.assertEqual(len([item for item in diagnostics if item.severity == "error"]), 0)

    def test_requirement_relation_rejects_invalid_and_unknown_ids(self) -> None:
        state = _build_valid_state()
        state["modules"]["M01"]["meta"]["requirement_id"] = "BAD"
        state["subtasks"]["ST01_01"]["facts"]["requirement_ids"] = ["RQ09"]
        state_path = self._write_state(state)

        exit_code, diagnostics = self._run_validate(state_path)
        codes = [item.code for item in diagnostics]
        self.assertEqual(exit_code, 1)
        self.assertIn("SCHEMA_INVALID_REQUIREMENT_RELATION_ID", codes)
        self.assertIn("SCHEMA_UNKNOWN_REQUIREMENT_RELATION_ID", codes)

    def test_requirement_relation_conflict_and_ambiguity_are_explicit(self) -> None:
        state = _build_valid_state()
        state["requirements"]["RQ02"] = {
            "meta": {
                "path": "docs/requirements/RQ02-second/",
                "scope_kind": "requirement_dir",
            },
            "facts": {
                "module_ids": [],
                "task_ids": [],
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
        state["modules"]["M01"]["meta"]["requirement_id"] = "RQ01"
        state["modules"]["M01"]["facts"]["requirement_ids"] = ["RQ01", "RQ02"]
        state["subtasks"]["ST01_01"]["meta"]["requirement_id"] = "RQ02"
        state["subtasks"]["ST01_01"]["facts"]["requirement_ids"] = ["RQ01"]
        state_path = self._write_state(state)

        exit_code, diagnostics = self._run_validate(state_path)
        codes = [item.code for item in diagnostics]
        self.assertEqual(exit_code, 1)
        self.assertIn("SCHEMA_REQUIREMENT_RELATION_AMBIGUOUS", codes)
        self.assertIn("SCHEMA_REQUIREMENT_RELATION_CONFLICT", codes)

    def test_requirement_relation_consistency_keeps_legacy_rq01_container_only_state_valid(self) -> None:
        state = _build_valid_state()
        state_path = self._write_state(state)

        exit_code, diagnostics = self._run_validate(state_path)
        consistency_codes = {
            item.code
            for item in diagnostics
            if item.code.startswith("SCHEMA_REQUIREMENT_RELATION_")
            and item.code
            not in {
                "SCHEMA_REQUIREMENT_RELATION_AMBIGUOUS",
                "SCHEMA_REQUIREMENT_RELATION_CONFLICT",
            }
        }
        self.assertEqual(exit_code, 0)
        self.assertEqual(consistency_codes, set())

    def test_requirement_relation_consistency_infers_legacy_root_cluster_without_policy(self) -> None:
        state = _build_valid_state()
        del state["global_policy"]["asset_policy"]
        state_path = self._write_state(state)

        exit_code, diagnostics = self._run_validate(state_path)
        consistency_codes = {
            item.code
            for item in diagnostics
            if item.code.startswith("SCHEMA_REQUIREMENT_RELATION_")
        }
        self.assertEqual(exit_code, 0)
        self.assertEqual(consistency_codes, set())

    def test_requirement_relation_consistency_missing_sides_are_warnings(self) -> None:
        state = _build_valid_state()
        state["requirements"]["RQ02"] = {
            "meta": {
                "path": "docs/requirements/RQ02-second/",
                "scope_kind": "requirement_dir",
            },
            "facts": {
                "module_ids": ["M02"],
                "task_ids": [],
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
        state["modules"]["M02"] = {
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
                "compliance": schema.make_default_compliance_state(),
            },
            "state": {
                "confirmed": schema.make_default_confirmed_state("module"),
                "tracking": schema.make_default_tracking_state(),
            },
        }
        state["subtasks"]["ST02_01"] = {
            "meta": {
                "module_id": "M02",
                "path": "docs/modules/M02-test/sub_modules/ST02_01-test/",
                "requirement_id": "RQ02",
            },
            "facts": {
                "upstream_module_ids": [],
                "related_oq_ids": [],
                "legacy_locked": False,
                "declared_blocker_refs": [],
                "design_doc": {"exists": True, "template_like": False},
                "implementation_doc": {"exists": True, "template_like": False},
                "requirement_ids": ["RQ02"],
                "compliance": schema.make_default_compliance_state(),
            },
            "state": {
                "confirmed": schema.make_default_confirmed_state("subtask"),
                "tracking": schema.make_default_tracking_state(),
            },
        }
        state_path = self._write_state(state)

        exit_code, diagnostics = self._run_validate(state_path)
        by_code = {}
        for item in diagnostics:
            by_code.setdefault(item.code, []).append(item)
        self.assertEqual(exit_code, 0)
        self.assertIn("SCHEMA_REQUIREMENT_RELATION_ENTITY_MISSING", by_code)
        self.assertIn("SCHEMA_REQUIREMENT_RELATION_CONTAINER_MISSING", by_code)
        self.assertTrue(
            any(item.entity_type == "module" and item.entity_id == "M02" for item in by_code["SCHEMA_REQUIREMENT_RELATION_ENTITY_MISSING"])
        )
        self.assertTrue(
            any(item.entity_type == "subtask" and item.entity_id == "ST02_01" for item in by_code["SCHEMA_REQUIREMENT_RELATION_CONTAINER_MISSING"])
        )
        self.assertTrue(
            any(
                "entity back-link is missing" in item.message
                for item in by_code["SCHEMA_REQUIREMENT_RELATION_ENTITY_MISSING"]
            )
        )
        self.assertEqual(len([item for item in diagnostics if item.severity == "error"]), 0)

    def test_requirement_relation_consistency_drift_conflict_and_container_ambiguity_are_explicit(self) -> None:
        state = _build_valid_state()
        state["requirements"]["RQ02"] = {
            "meta": {
                "path": "docs/requirements/RQ02-second/",
                "scope_kind": "requirement_dir",
            },
            "facts": {
                "module_ids": ["M02", "M03"],
                "task_ids": ["ST03_01"],
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
        state["requirements"]["RQ01"]["facts"]["module_ids"] = ["M01", "M03"]
        state["requirements"]["RQ01"]["facts"]["task_ids"] = ["ST01_01", "ST03_01"]
        state["modules"]["M02"] = {
            "meta": {"path": "docs/modules/M02-test/", "requirement_id": "RQ01"},
            "facts": {
                "upstream_module_ids": [],
                "related_oq_ids": [],
                "legacy_locked": False,
                "declared_blocker_refs": [],
                "docs": {
                    slot: {"exists": True, "template_like": False}
                    for slot in schema.MODULE_DOC_SLOTS
                },
                "requirement_ids": ["RQ01"],
                "compliance": schema.make_default_compliance_state(),
            },
            "state": {
                "confirmed": schema.make_default_confirmed_state("module"),
                "tracking": schema.make_default_tracking_state(),
            },
        }
        state["modules"]["M03"] = {
            "meta": {"path": "docs/modules/M03-test/"},
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
        state["subtasks"]["ST03_01"] = {
            "meta": {
                "module_id": "M03",
                "path": "docs/modules/M03-test/sub_modules/ST03_01-test/",
                "requirement_id": "RQ01",
            },
            "facts": {
                "upstream_module_ids": [],
                "related_oq_ids": [],
                "legacy_locked": False,
                "declared_blocker_refs": [],
                "design_doc": {"exists": True, "template_like": False},
                "implementation_doc": {"exists": True, "template_like": False},
                "requirement_ids": ["RQ01"],
                "compliance": schema.make_default_compliance_state(),
            },
            "state": {
                "confirmed": schema.make_default_confirmed_state("subtask"),
                "tracking": schema.make_default_tracking_state(),
            },
        }
        state_path = self._write_state(state)

        exit_code, diagnostics = self._run_validate(state_path)
        codes = [item.code for item in diagnostics]
        self.assertEqual(exit_code, 0)
        self.assertIn("SCHEMA_REQUIREMENT_RELATION_CONTAINER_CONFLICT", codes)
        self.assertIn("SCHEMA_REQUIREMENT_RELATION_DRIFT", codes)
        self.assertIn("SCHEMA_REQUIREMENT_RELATION_AMBIGUOUS", codes)

    def test_diagnostic_structure_and_evidence(self) -> None:
        state = _build_valid_state()
        state["modules"]["M01"]["state"]["confirmed"]["candidate_status"] = "invalid"
        state_path = self._write_state(state)

        exit_code, diagnostics = self._run_validate(state_path)
        self.assertEqual(exit_code, 1)
        self.assertEqual(len(diagnostics), 1)
        self._assert_common_diagnostic_shape(diagnostics)

    def test_validate_state_exit_code_and_schema_success(self) -> None:
        state = _build_valid_state()
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["readiness"] = "downstream_ready"
        state_path = self._write_state(state)
        exit_code, diagnostics = self._run_validate(state_path)

        self.assertEqual(exit_code, 1)
        codes = {item.code for item in diagnostics}
        self.assertIn("RULE_ILLEGAL_STATE_COMBINATION", codes)

    def test_validate_state_exit_code_success_for_valid_state(self) -> None:
        state = _build_valid_state()
        state_path = self._write_state(state)
        exit_code, diagnostics = self._run_validate(state_path)

        self.assertEqual(exit_code, 0)
        self.assertEqual(len([item for item in diagnostics if item.severity == "error"]), 0)


if __name__ == "__main__":
    unittest.main()
