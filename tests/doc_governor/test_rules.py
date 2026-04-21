import unittest

from tools.doc_governor import schema
from tools.doc_governor.rules import Diagnostic, evaluate_rules


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
        "modules": {
            "M01": {
                "meta": {"path": "docs/modules/M01"},
                "facts": {
                    "upstream_module_ids": [],
                    "related_oq_ids": [],
                    "legacy_locked": False,
                    "declared_blocker_refs": [],
                    "docs": {name: {"exists": True, "template_like": False} for name in schema.MODULE_DOC_SLOTS},
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
                "meta": {"module_id": "M01", "path": "docs/modules/M01/sub_modules/ST01_01-test"},
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


def _extract_codes(diagnostics: list[Diagnostic]) -> set[str]:
    return {item.code for item in diagnostics}


class ValidateRulesTests(unittest.TestCase):
    def test_legacy_lock_candidate_status_forbidden(self) -> None:
        state = _build_state()
        state["subtasks"]["ST01_01"]["facts"]["legacy_locked"] = True
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["candidate_status"] = "candidate"

        codes = _extract_codes(evaluate_rules(state))
        self.assertIn("RULE_LEGACY_LOCK_CANDIDATE_FORBIDDEN", codes)

    def test_legacy_lock_readiness_forbidden(self) -> None:
        state = _build_state()
        state["subtasks"]["ST01_01"]["facts"]["legacy_locked"] = True
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["readiness"] = "downstream_ready"

        codes = _extract_codes(evaluate_rules(state))
        self.assertIn("RULE_LEGACY_LOCK_READINESS_FORBIDDEN", codes)

    def test_downstream_ready_requires_maturity(self) -> None:
        state = _build_state()
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["maturity"] = None
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["readiness"] = "downstream_ready"

        codes = _extract_codes(evaluate_rules(state))
        self.assertIn("RULE_ILLEGAL_STATE_COMBINATION", codes)

    def test_inactive_template_block_implementation_ready(self) -> None:
        state = _build_state()
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = (
            "inactive_template"
        )
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["readiness"] = "implementation_ready"

        codes = _extract_codes(evaluate_rules(state))
        self.assertIn("RULE_INACTIVE_TEMPLATE_IMPLEMENTATION_READY_FORBIDDEN", codes)

    def test_template_like_implementation_not_active_working(self) -> None:
        state = _build_state()
        state["subtasks"]["ST01_01"]["facts"]["implementation_doc"]["template_like"] = True
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["implementation_doc_state"] = (
            "active_working_doc"
        )

        codes = _extract_codes(evaluate_rules(state))
        self.assertIn("RULE_TEMPLATE_ACTIVE_WORKING_DOC_FORBIDDEN", codes)

    def test_formal_window_closed_blocks_candidate(self) -> None:
        state = _build_state()
        state["global_policy"]["formal_window_open"] = False
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["candidate_status"] = "candidate"

        codes = _extract_codes(evaluate_rules(state))
        self.assertIn("RULE_FORMAL_WINDOW_CLOSED_CANDIDATE_FORBIDDEN", codes)

    def test_formal_window_closed_blocks_implementation_ready(self) -> None:
        state = _build_state()
        state["global_policy"]["formal_window_open"] = False
        state["subtasks"]["ST01_01"]["state"]["confirmed"]["readiness"] = "implementation_ready"

        codes = _extract_codes(evaluate_rules(state))
        self.assertIn("RULE_FORMAL_WINDOW_CLOSED_IMPLEMENTATION_READY_FORBIDDEN", codes)


if __name__ == "__main__":
    unittest.main()
