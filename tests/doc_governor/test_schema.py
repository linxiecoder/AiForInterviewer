import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml


class SchemaContractTests(unittest.TestCase):
    def test_module_doc_slots_are_frozen(self) -> None:
        from tools.doc_governor import schema

        self.assertEqual(
            list(schema.MODULE_DOC_SLOTS.keys()),
            [
                "requirements",
                "design",
                "api",
                "schema",
                "logic",
                "task_index",
                "dependencies",
                "open_questions",
                "execution_log",
            ],
        )
        self.assertEqual(set(schema.REQUIRED_MODULE_SLOTS), set(schema.MODULE_DOC_SLOTS))

    def test_subtask_doc_slots_are_frozen(self) -> None:
        from tools.doc_governor import schema

        self.assertEqual(
            list(schema.SUBTASK_DOC_SLOTS.keys()),
            ["design_doc", "implementation_doc"],
        )
        self.assertEqual(set(schema.REQUIRED_SUBTASK_SLOTS), set(schema.SUBTASK_DOC_SLOTS))

    def test_state_paths_and_schema_version_are_frozen(self) -> None:
        from tools.doc_governor import schema

        self.assertEqual(schema.SCHEMA_VERSION, 1)
        self.assertEqual(
            schema.BOOTSTRAP_STATE_PATH,
            "docs/governance/DOC_STATE.bootstrap.yaml",
        )
        self.assertEqual(
            schema.BOOTSTRAP_REPORT_PATH,
            "docs/governance/BOOTSTRAP_REPORT.md",
        )
        self.assertEqual(
            schema.OFFICIAL_STATE_PATH,
            "docs/governance/DOC_STATE.yaml",
        )

    def test_default_confirmed_state_factory_is_centralized(self) -> None:
        from tools.doc_governor import schema

        module_state = schema.make_default_confirmed_state("module")
        self.assertEqual(
            module_state,
            {
                "maturity": None,
                "window_status": "closed",
                "window_opened_at": None,
                "window_opened_by": None,
                "window_reason": None,
                "candidate_status": "none",
                "review_status": "unreviewed",
                "readiness": "blocked",
                "blocker_refs": [],
                "last_transition_id": None,
                "last_confirmed_at": None,
                "last_confirmed_by": None,
            },
        )

        subtask_state = schema.make_default_confirmed_state("subtask")
        self.assertEqual(
            subtask_state,
            {
                "implementation_doc_state": "missing",
                "maturity": None,
                "window_status": "closed",
                "window_opened_at": None,
                "window_opened_by": None,
                "window_reason": None,
                "candidate_status": "none",
                "review_status": "unreviewed",
                "readiness": "blocked",
                "blocker_refs": [],
                "last_transition_id": None,
                "last_confirmed_at": None,
                "last_confirmed_by": None,
            },
        )

    def test_typed_blocker_ref_regex_matches_expected_refs(self) -> None:
        from tools.doc_governor import schema

        self.assertIsNotNone(schema.TYPED_BLOCKER_REF_RE.fullmatch("oq:OQ-021"))
        self.assertIsNotNone(
            schema.TYPED_BLOCKER_REF_RE.fullmatch("gate:formal_window_closed")
        )
        self.assertIsNotNone(schema.TYPED_BLOCKER_REF_RE.fullmatch("legacy:locked"))
        self.assertIsNone(schema.TYPED_BLOCKER_REF_RE.fullmatch("OQ-021"))

    def test_governance_round_contract_constants_are_frozen(self) -> None:
        from tools.doc_governor import schema

        self.assertEqual(schema.GOVERNANCE_ROUND_STATUSES, ("open", "closed"))
        self.assertEqual(
            schema.GOVERNANCE_ROUND_REQUIRED_FIELDS,
            (
                "round_id",
                "topic",
                "scope",
                "status",
                "opened_at",
                "opened_by",
                "decision_refs",
            ),
        )

    def test_validate_state_without_governance_rounds_is_backward_compatible(self) -> None:
        from tools.doc_governor.validate import validate_state_file

        state = _build_minimal_state()
        with TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "DOC_STATE.yaml"
            state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
            diagnostics = validate_state_file(state_path)

        self.assertFalse(
            [item for item in diagnostics if item.severity == "error"],
            "Expected no schema errors when governance_rounds is absent.",
        )

    def test_validate_state_with_valid_governance_rounds(self) -> None:
        from tools.doc_governor.validate import validate_state_file

        state = _build_minimal_state()
        state["governance_rounds"] = [
            {
                "round_id": "R-2026-04-01",
                "topic": "Candidate gate review",
                "scope": "ST01_01",
                "status": "open",
                "opened_at": "2026-04-01T09:00:00Z",
                "opened_by": "alice",
                "decision_refs": ["decision:DR-001"],
            }
        ]
        with TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "DOC_STATE.yaml"
            state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
            diagnostics = validate_state_file(state_path)

        self.assertFalse(
            [item for item in diagnostics if item.severity == "error"],
            "Expected no schema errors for a valid governance_rounds payload.",
        )

    def test_validate_state_with_invalid_governance_rounds(self) -> None:
        from tools.doc_governor.validate import validate_state_file

        state = _build_minimal_state()
        state["governance_rounds"] = [
            {
                "round_id": "R-2026-04-01",
                "topic": "Candidate gate review",
                "scope": "ST01_01",
                "status": "done",
                "opened_at": "2026/04/01 09:00:00",
                "opened_by": "alice",
                "decision_refs": ["decision:DR-001"],
            }
        ]
        with TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "DOC_STATE.yaml"
            state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
            diagnostics = validate_state_file(state_path)

        codes = {item.code for item in diagnostics}
        self.assertIn("SCHEMA_INVALID_GOVERNANCE_ROUND_ENUM", codes)
        self.assertIn("SCHEMA_INVALID_GOVERNANCE_ROUND_TIME", codes)


def _build_minimal_state() -> dict:
    from tools.doc_governor import schema

    module_docs = {
        slot: {"exists": True, "template_like": False}
        for slot in schema.MODULE_DOC_SLOTS
    }
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
        "modules": {
            "M01": {
                "meta": {"path": "docs/modules/M01-test/"},
                "facts": {
                    "upstream_module_ids": [],
                    "related_oq_ids": [],
                    "legacy_locked": False,
                    "declared_blocker_refs": [],
                    "docs": module_docs,
                },
                "state": {"confirmed": schema.make_default_confirmed_state("module")},
            }
        },
        "subtasks": {
            "ST01_01": {
                "meta": {"module_id": "M01", "path": "docs/modules/M01/sub_modules/ST01_01-test/"},
                "facts": {
                    "upstream_module_ids": [],
                    "related_oq_ids": [],
                    "legacy_locked": False,
                    "declared_blocker_refs": [],
                    "design_doc": {"exists": True, "template_like": False},
                    "implementation_doc": {"exists": True, "template_like": False},
                },
                "state": {"confirmed": schema.make_default_confirmed_state("subtask")},
            }
        },
    }


if __name__ == "__main__":
    unittest.main()
