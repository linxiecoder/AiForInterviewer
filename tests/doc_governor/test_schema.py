import unittest


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


if __name__ == "__main__":
    unittest.main()
