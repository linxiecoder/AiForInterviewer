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
GOVERNANCE_ROUND_STATUSES = ("open", "closed")
GOVERNANCE_ROUND_REQUIRED_FIELDS = (
    "round_id",
    "topic",
    "scope",
    "status",
    "opened_at",
    "opened_by",
    "decision_refs",
)

TYPED_BLOCKER_REF_RE = re.compile(
    r"^(?:"
    r"oq:OQ-\d+"
    r"|requirement:RQ\d{2}"
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
    "asset_policy": {
        "requirement_mode": "root_requirement_cluster",
    },
    "paths": {
        "modules_root": "docs/modules",
        "open_questions_doc": "OPEN_QUESTIONS.md",
        "task_index_doc": "TASK_INDEX.md",
    },
}

OQ_DEFAULT_GATE_LEVEL = "observe_only"
OQ_DEFAULT_RESOLUTION_POLICY = "proposed_default_ok"
OQ_POLICY_SOURCE_EXPLICIT = "explicit"
OQ_POLICY_SOURCE_BOOTSTRAP_DEFAULT = "bootstrap_default"
OQ_POLICY_SOURCES = (OQ_POLICY_SOURCE_EXPLICIT, OQ_POLICY_SOURCE_BOOTSTRAP_DEFAULT)
OQ_DEFAULT_POLICY_SOURCE = OQ_POLICY_SOURCE_BOOTSTRAP_DEFAULT

_DEFAULT_CONFIRMED_STATE = {
    "requirement": {
        "maturity": None,
        "candidate_status": "none",
        "review_status": "unreviewed",
        "readiness": "blocked",
        "window_status": "closed",
        "window_opened_at": None,
        "window_opened_by": None,
        "window_reason": None,
        "blocker_refs": [],
        "last_transition_id": None,
        "last_confirmed_at": None,
        "last_confirmed_by": None,
    },
    "module": {
        "maturity": None,
        "candidate_status": "none",
        "review_status": "unreviewed",
        "readiness": "blocked",
        "window_status": "closed",
        "window_opened_at": None,
        "window_opened_by": None,
        "window_reason": None,
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
        "window_status": "closed",
        "window_opened_at": None,
        "window_opened_by": None,
        "window_reason": None,
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


def make_default_tracking_state() -> dict[str, object]:
    return {
        "active_round_id": None,
        "last_round_id": None,
    }


def make_default_compliance_state() -> dict[str, object]:
    return {
        "naming_ok": None,
        "path_ok": None,
        "relations_ok": None,
        "language_ok": None,
        "violations": [],
    }
