import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import shutil
import tempfile
import unittest
import uuid
import yaml

from tools.doc_governor import schema
from tools.doc_governor.cli import main


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
        },
        "oqs": {},
        "modules": {
            "M01": {
                "meta": {"path": module_path},
                "facts": {
                    "upstream_module_ids": [],
                    "related_oq_ids": [],
                    "legacy_locked": False,
                    "declared_blocker_refs": [],
                    "docs": docs,
                },
                "state": {
                    "confirmed": {
                        "maturity": None,
                        "candidate_status": "none",
                        "review_status": "unreviewed",
                        "readiness": "blocked",
                        "blocker_refs": [],
                        "last_transition_id": None,
                        "last_confirmed_at": None,
                        "last_confirmed_by": None,
                    }
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
                },
                "state": {
                    "confirmed": {
                        "implementation_doc_state": "missing",
                        "maturity": None,
                        "candidate_status": "none",
                        "review_status": "unreviewed",
                        "readiness": "blocked",
                        "blocker_refs": [],
                        "last_transition_id": None,
                        "last_confirmed_at": None,
                        "last_confirmed_by": None,
                    }
                },
            }
        },
    }


class ValidateSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root = Path(tempfile.gettempdir()) / f"doc-governor-validate-{uuid.uuid4().hex}"
        self.temp_root.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def _write_state(self, state: dict) -> Path:
        file_path = self.temp_root / "DOC_STATE.bootstrap.yaml"
        file_path.write_text(yaml.safe_dump(state), encoding="utf-8")
        return file_path

    def _run_cli(self, state_path: Path) -> tuple[int, dict]:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["validate-state", "--input", str(state_path)])
        payload = json.loads(stdout.getvalue())
        return exit_code, payload

    def _assert_common_diagnostic_shape(self, payload: dict) -> None:
        for item in payload["diagnostics"]:
            self.assertIn("code", item)
            self.assertIn("severity", item)
            self.assertIn("entity_type", item)
            self.assertIn("entity_id", item)
            self.assertIn("field_path", item)
            self.assertIn("message", item)
            self.assertIn("evidence", item)
            self.assertTrue(item["evidence"], f"{item['code']} has empty evidence")

    def test_schema_version_missing(self) -> None:
        state = _build_valid_state()
        del state["schema_version"]
        state_path = self._write_state(state)

        exit_code, payload = self._run_cli(state_path)
        codes = {item["code"] for item in payload["diagnostics"]}

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["counts"]["error"], 1)
        self.assertIn("SCHEMA_MISSING_REQUIRED_FIELD", codes)

    def test_unknown_enum_value(self) -> None:
        state = _build_valid_state()
        state["modules"]["M01"]["state"]["confirmed"]["candidate_status"] = "invalid"
        state_path = self._write_state(state)

        exit_code, payload = self._run_cli(state_path)
        codes = [item["code"] for item in payload["diagnostics"]]

        self.assertEqual(exit_code, 1)
        self.assertIn("SCHEMA_UNKNOWN_ENUM_VALUE", codes)

    def test_invalid_typed_blocker_ref(self) -> None:
        state = _build_valid_state()
        state["modules"]["M01"]["state"]["confirmed"]["blocker_refs"] = ["invalid:ref"]
        state_path = self._write_state(state)

        exit_code, payload = self._run_cli(state_path)
        codes = [item["code"] for item in payload["diagnostics"]]
        self.assertEqual(exit_code, 1)
        self.assertIn("SCHEMA_INVALID_TYPED_REF", codes)

    def test_module_and_subtask_path_id_mismatch(self) -> None:
        state = _build_valid_state()
        state["modules"]["M01"]["meta"]["path"] = "docs/modules/M02-test/"
        state["subtasks"]["ST01_01"]["meta"]["path"] = (
            "docs/modules/M01-test/sub_modules/ST01_09-test/"
        )
        state_path = self._write_state(state)

        exit_code, payload = self._run_cli(state_path)
        codes = [item["code"] for item in payload["diagnostics"]]
        self.assertEqual(exit_code, 1)
        self.assertIn("SCHEMA_PATH_ID_MISMATCH", codes)

    def test_unknown_doc_slot(self) -> None:
        state = _build_valid_state()
        state["modules"]["M01"]["facts"]["docs"]["unexpected"] = {
            "exists": True,
            "template_like": False,
        }
        state_path = self._write_state(state)

        exit_code, payload = self._run_cli(state_path)
        codes = [item["code"] for item in payload["diagnostics"]]
        self.assertIn("SCHEMA_UNKNOWN_DOC_SLOT", codes)
        self.assertEqual(exit_code, 1)

    def test_diagnostic_structure_and_evidence(self) -> None:
        state = _build_valid_state()
        state["modules"]["M01"]["state"]["confirmed"]["candidate_status"] = "invalid"
        state_path = self._write_state(state)

        exit_code, payload = self._run_cli(state_path)
        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["counts"]["error"], 1)
        self.assertIsInstance(payload["counts"], dict)
        self.assertIn("diagnostics", payload)
        self.assertEqual(len(payload["diagnostics"]), 1)
        self._assert_common_diagnostic_shape(payload)

    def test_validate_state_exit_code_and_schema_success(self) -> None:
        state = _build_valid_state()
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["readiness"] = "downstream_ready"
        state_path = self._write_state(state)
        exit_code, payload = self._run_cli(state_path)

        self.assertEqual(exit_code, 1)
        codes = {item["code"] for item in payload["diagnostics"]}
        self.assertIn("RULE_ILLEGAL_STATE_COMBINATION", codes)

    def test_validate_state_exit_code_success_for_valid_state(self) -> None:
        state = _build_valid_state()
        state_path = self._write_state(state)
        exit_code, payload = self._run_cli(state_path)

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["counts"]["error"], 0)


if __name__ == "__main__":
    unittest.main()
