import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

import yaml


class SchemaContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root = Path(tempfile.gettempdir()) / f"doc-governor-schema-{uuid.uuid4().hex}"
        self.temp_root.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_requirement_defaults_and_helpers_are_available(self) -> None:
        from tools.doc_governor import schema

        requirement_state = schema.make_default_confirmed_state("requirement")
        self.assertEqual(
            requirement_state,
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
        self.assertEqual(
            schema.make_default_tracking_state(),
            {
                "active_round_id": None,
                "last_round_id": None,
            },
        )
        self.assertEqual(
            schema.make_default_compliance_state(),
            {
                "naming_ok": None,
                "path_ok": None,
                "relations_ok": None,
                "language_ok": None,
                "violations": [],
            },
        )

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

    def test_document_contract_constants_are_frozen(self) -> None:
        from tools.doc_governor import schema

        self.assertEqual(schema.DOCUMENT_TYPES, ("design", "plan"))
        self.assertEqual(schema.DOCUMENT_STATUSES, ("draft", "active", "blocked", "ready"))

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

        document_state = schema.make_default_confirmed_state("document")
        self.assertEqual(
            document_state,
            {
                "maturity": None,
                "status": "draft",
                "review_status": "unreviewed",
                "blocker_refs": [],
                "active_round_id": None,
                "last_round_id": None,
                "last_transition_id": None,
                "last_confirmed_at": None,
                "last_confirmed_by": None,
            },
        )

    def test_typed_blocker_ref_regex_matches_expected_refs(self) -> None:
        from tools.doc_governor import schema

        self.assertIsNotNone(schema.TYPED_BLOCKER_REF_RE.fullmatch("oq:OQ-021"))
        self.assertIsNotNone(schema.TYPED_BLOCKER_REF_RE.fullmatch("requirement:RQ01"))
        self.assertIsNotNone(
            schema.TYPED_BLOCKER_REF_RE.fullmatch("gate:formal_window_closed")
        )
        self.assertIsNotNone(schema.TYPED_BLOCKER_REF_RE.fullmatch("legacy:locked"))
        self.assertIsNotNone(
            schema.TYPED_BLOCKER_REF_RE.fullmatch("doc:DOC-SPEC-P1#architecture")
        )
        self.assertIsNone(schema.TYPED_BLOCKER_REF_RE.fullmatch("OQ-021"))

    def test_governance_round_contract_constants_are_frozen(self) -> None:
        from tools.doc_governor import schema

        self.assertEqual(
            schema.GOVERNANCE_ROUND_STATUSES,
            ("open", "in_progress", "review", "closed"),
        )
        self.assertEqual(
            schema.GOVERNANCE_ROUND_REQUIRED_FIELDS,
            (
                "round_id",
                "workflow",
                "topic",
                "scope",
                "status",
                "opened_at",
                "opened_by",
                "decision_refs",
                "target_documents",
                "required_evidence_refs",
                "exit_criteria",
                "writeback_items",
            ),
        )

    def test_validate_state_without_governance_rounds_is_backward_compatible(self) -> None:
        from tools.doc_governor.validate import validate_state_file

        state = _build_minimal_state()
        state_path = self.temp_root / "DOC_STATE.yaml"
        state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
        diagnostics = validate_state_file(state_path)

        self.assertFalse(
            [item for item in diagnostics if item.severity == "error"],
            "Expected no schema errors when governance_rounds is absent.",
        )

    def test_validate_state_with_valid_governance_rounds(self) -> None:
        from tools.doc_governor.validate import validate_state_file

        state = _build_minimal_state()
        state["documents"] = {
            "DOC-SPEC-P1": _build_document_entry(
                doc_type="design",
                path="docs/superpowers/specs/spec.md",
            )
        }
        state["governance_rounds"] = [
            {
                "round_id": "R-2026-04-01",
                "workflow": "document_refinement",
                "topic": "Candidate gate review",
                "scope": "documents:DOC-SPEC-P1",
                "status": "open",
                "opened_at": "2026-04-01T09:00:00Z",
                "opened_by": "alice",
                "decision_refs": ["decision:DR-001"],
                "target_documents": [
                    {
                        "document_id": "DOC-SPEC-P1",
                        "target_sections": ["goal", "architecture"],
                    }
                ],
                "required_evidence_refs": ["doc:DOC-SPEC-P1#goal", "oq:OQ-004"],
                "exit_criteria": ["required sections complete"],
                "writeback_items": ["回写下一轮 agenda"],
            }
        ]
        state_path = self.temp_root / "DOC_STATE.yaml"
        state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
        diagnostics = validate_state_file(state_path)

        self.assertFalse(
            [item for item in diagnostics if item.severity == "error"],
            "Expected no schema errors for a valid governance_rounds payload.",
        )

    def test_validate_state_with_invalid_governance_rounds(self) -> None:
        from tools.doc_governor.validate import validate_state_file

        state = _build_minimal_state()
        state["documents"] = {
            "DOC-SPEC-P1": _build_document_entry(
                doc_type="design",
                path="docs/superpowers/specs/spec.md",
            )
        }
        state["governance_rounds"] = [
            {
                "round_id": "R-2026-04-01",
                "workflow": "document_refinement",
                "topic": "Candidate gate review",
                "scope": "documents:DOC-SPEC-P1",
                "status": "done",
                "opened_at": "2026/04/01 09:00:00",
                "opened_by": "alice",
                "decision_refs": ["decision:DR-001"],
                "target_documents": [
                    {
                        "document_id": "DOC-SPEC-P1",
                        "target_sections": ["goal"],
                    }
                ],
                "required_evidence_refs": ["doc:DOC-SPEC-P1#goal"],
                "exit_criteria": ["required sections complete"],
                "writeback_items": [],
            }
        ]
        state_path = self.temp_root / "DOC_STATE.yaml"
        state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
        diagnostics = validate_state_file(state_path)

        codes = {item.code for item in diagnostics}
        self.assertIn("SCHEMA_INVALID_GOVERNANCE_ROUND_ENUM", codes)
        self.assertIn("SCHEMA_INVALID_GOVERNANCE_ROUND_TIME", codes)

    def test_validate_state_with_documents(self) -> None:
        from tools.doc_governor.validate import validate_state_file

        state = _build_minimal_state()
        state["documents"] = {
            "DOC-SPEC-P1": _build_document_entry(
                doc_type="design",
                path="docs/superpowers/specs/spec.md",
            ),
            "DOC-PLAN-P1": _build_document_entry(
                doc_type="plan",
                path="docs/superpowers/plans/plan.md",
            ),
        }
        state_path = self.temp_root / "DOC_STATE.yaml"
        state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
        diagnostics = validate_state_file(state_path)

        self.assertFalse(
            [item for item in diagnostics if item.severity == "error"],
            "Expected no schema errors for valid documents payload.",
        )


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
                "meta": {"path": "docs/modules/M01-test/"},
                "facts": {
                    "upstream_module_ids": [],
                    "related_oq_ids": [],
                    "legacy_locked": False,
                    "declared_blocker_refs": [],
                    "docs": module_docs,
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
                "meta": {"module_id": "M01", "path": "docs/modules/M01/sub_modules/ST01_01-test/"},
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


def _build_document_entry(*, doc_type: str, path: str) -> dict:
    from tools.doc_governor import schema

    return {
        "meta": {
            "doc_type": doc_type,
            "title": f"{doc_type} doc",
            "path": path,
            "required_sections": [
                {"section_id": "goal", "heading": "## 1. 文档目标"},
                {"section_id": "architecture", "heading": "## 5. 系统架构"},
            ],
            "relations": {
                "document_refs": [],
                "module_refs": [],
                "oq_refs": [],
            },
        },
        "facts": {
            "exists": True,
            "headings": [],
            "section_presence": {},
            "extracted_refs": {
                "document_refs": [],
                "module_refs": [],
                "oq_refs": [],
            },
            "marker_counts": {
                "todo": 0,
                "tbd": 0,
                "unresolved": 0,
            },
            "last_scanned_at": None,
        },
        "state": {"confirmed": schema.make_default_confirmed_state("document")},
    }


if __name__ == "__main__":
    unittest.main()
