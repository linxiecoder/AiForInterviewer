from __future__ import annotations

import copy
import re


SCHEMA_VERSION = 1

BOOTSTRAP_STATE_PATH = "docs/governance/DOC_STATE.bootstrap.yaml"
BOOTSTRAP_REPORT_PATH = "docs/governance/BOOTSTRAP_REPORT.md"
OFFICIAL_STATE_PATH = "docs/governance/DOC_STATE.yaml"

MODULE_DOC_SLOTS = {
    "requirements": "MODULE_REQUIREMENTS.md",
    "design": "MODULE_DESIGN.md",
    "api": "MODULE_API_DESIGN.md",
    "schema": "MODULE_SCHEMA_DESIGN.md",
    "logic": "MODULE_LOGIC_DESIGN.md",
    "task_index": "MODULE_TASK_INDEX.md",
    "dependencies": "MODULE_DEPENDENCIES.md",
    "open_questions": "MODULE_OPEN_QUESTIONS.md",
    "execution_log": "MODULE_EXECUTION_LOG.md",
}

SUBTASK_DOC_SLOTS = {
    "design_doc": "SUBTASK_DESIGN.md",
    "implementation_doc": "SUBTASK_IMPLEMENTATION.md",
}

REQUIRED_MODULE_SLOTS = tuple(MODULE_DOC_SLOTS.keys())
REQUIRED_SUBTASK_SLOTS = tuple(SUBTASK_DOC_SLOTS.keys())

MATURITY_LEVELS = tuple(f"L{index}" for index in range(8))
CANDIDATE_STATUSES = ("none", "observe", "candidate")
REVIEW_STATUSES = ("unreviewed", "pending_confirmation", "approved", "rejected")
READINESS_STATUSES = ("blocked", "not_ready", "downstream_ready", "implementation_ready")
IMPLEMENTATION_DOC_STATES = ("missing", "inactive_template", "active_working_doc")

TYPED_BLOCKER_REF_RE = re.compile(
    r"^(?:"
    r"oq:OQ-\d{3}"
    r"|module:M\d{2}"
    r"|subtask:ST\d{2}_\d{2}"
    r"|gate:[a-z0-9_]+"
    r"|policy:[a-z0-9_]+"
    r"|doc:[a-z0-9_.]+"
    r"|legacy:locked"
    r")$"
)

GLOBAL_POLICY_DEFAULTS = {
    "auto_open_enabled": False,
    "require_confirmation_for_state_writeback": True,
    "strict_template_gate": True,
    "formal_window_open": False,
    "paths": {
        "modules_root": "docs/modules",
        "open_questions_doc": "OPEN_QUESTIONS.md",
        "task_index_doc": "TASK_INDEX.md",
    },
}

_DEFAULT_CONFIRMED_STATE = {
    "module": {
        "maturity": None,
        "candidate_status": "none",
        "review_status": "unreviewed",
        "readiness": "blocked",
        "blocker_refs": [],
        "last_transition_id": None,
        "last_confirmed_at": None,
        "last_confirmed_by": None,
    },
    "subtask": {
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
}


def make_default_confirmed_state(entity_type: str) -> dict[str, object]:
    if entity_type not in _DEFAULT_CONFIRMED_STATE:
        raise ValueError(f"Unsupported entity type: {entity_type}")
    return copy.deepcopy(_DEFAULT_CONFIRMED_STATE[entity_type])
