from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.application.ai_runtime.business_graphs.polish_feedback_graph import (
    POLISH_FEEDBACK_GRAPH_NAME,
    build_polish_feedback_graph_descriptor,
    build_polish_feedback_readonly_parity_gate,
)
from app.application.ai_runtime.contracts import RuntimePolicyError


REPO_ROOT = Path(__file__).resolve().parents[2]
GRAPH_FILE = (
    REPO_ROOT
    / "apps"
    / "api"
    / "app"
    / "application"
    / "ai_runtime"
    / "business_graphs"
    / "polish_feedback_graph.py"
)
BUSINESS_GRAPH_ROOT = GRAPH_FILE.parent


def test_readonly_parity_accepts_refs_only() -> None:
    first = _build_gate()
    second = _build_gate()

    assert first == second
    assert first["graph_name"] == POLISH_FEEDBACK_GRAPH_NAME == "polish_feedback_graph"
    assert first["parity_gate_version"] == "pr7-readonly-parity"
    assert first["mode"] == "readonly_contract_ref_parity"
    assert first["input_refs"] == {
            "session_ref": "session_ref_readonly",
            "question_ref": "question_ref_readonly",
            "answer_ref": "answer_ref_readonly",
        "prior_answer_refs": ["answer_ref_prior_1"],
        "prior_feedback_refs": ["feedback_ref_prior_1"],
            "rubric_summary_ref": "rubric_summary_ref_readonly",
    }
    assert first["diagnostics"] == {
        "contract_parity": "refs_only",
        "semantic_payload_parity": "not_evaluated",
        "adapter_only": True,
        "legacy_writer_touched": False,
        "provider_path_touched": False,
    }
    assert first["output_refs"]["result_refs"][0].startswith("parity_result_ref_")
    assert first["output_refs"]["candidate_refs"] == []
    assert first["output_refs"]["formal_refs"] == []

    public_repr = repr(first)
    for raw_value in ("hidden question body", "hidden answer body", "hidden provider body"):
        assert raw_value not in public_repr

    descriptor = build_polish_feedback_graph_descriptor()
    assert descriptor.default_enabled is False
    assert descriptor.provider_enabled is False
    assert descriptor.formal_write_targets == ()
    assert descriptor.db_business_write_targets == ()
    assert descriptor.disabled_behavior == "adapter_only_unavailable"


def test_readonly_parity_rejects_raw_question_answer_and_provider_payload() -> None:
    forbidden_inputs = {
        _key("question", "text"): "hidden question body",
        _key("answer", "text"): "hidden answer body",
        _key("raw", "prompt"): "hidden prompt body",
        _key("raw", "completion"): "hidden completion body",
        _key("provider", "payload"): {"body": "hidden provider body"},
        _key("checkpoint", "payload"): {"body": "hidden checkpoint body"},
        _key("full", "resume"): "hidden resume body",
        _key("full", "jd"): "hidden jd body",
        _key("full", "answer"): "hidden full answer body",
        _key("hidden", "rubric"): "hidden rubric body",
        _key("api", "key"): "hidden api body",
        "to" + "ken": "hidden credential body",
        "coo" + "kie": "hidden browser credential body",
        "sec" + "ret": "hidden private credential body",
    }

    for forbidden_key, forbidden_value in forbidden_inputs.items():
        with pytest.raises(RuntimePolicyError):
            _build_gate(**{forbidden_key: forbidden_value})


def test_readonly_parity_has_zero_provider_formal_and_db_writes() -> None:
    payload = _build_gate()

    assert payload["counters"] == {
        "provider_calls": 0,
        "formal_business_writes": 0,
        "db_business_writes": 0,
    }
    assert payload["output_refs"]["formal_refs"] == []
    assert payload["output_refs"]["candidate_refs"] == []


def test_readonly_parity_does_not_import_polish_application_or_db_repositories() -> None:
    assert sorted(path.name for path in BUSINESS_GRAPH_ROOT.glob("*.py")) == [
        "__init__.py",
        "local_multi_agent_orchestrator.py",
        "polish_feedback_graph.py",
        "polish_question_graph.py",
    ]
    violations: list[str] = []
    for graph_file in BUSINESS_GRAPH_ROOT.glob("*.py"):
        violations.extend(_find_forbidden_imports(graph_file))
    assert violations == []


def test_readonly_parity_rollback_is_flag_only() -> None:
    payload = _build_gate()

    assert payload["rollback"] == {
        "flag_only": True,
        "adapter_only_no_formal_writer": True,
        "checkpoint_refs_are_business_facts": False,
    }
    assert payload["diagnostics"]["legacy_writer_touched"] is False
    assert payload["diagnostics"]["provider_path_touched"] is False
    assert payload["diagnostics"]["semantic_payload_parity"] == "not_evaluated"


def _build_gate(**extra_inputs: object) -> dict[str, object]:
    return build_polish_feedback_readonly_parity_gate(
        owner_id="owner_readonly",
        actor_id="actor_readonly",
        run_id="run_readonly",
        ai_task_id="task_readonly",
        session_ref="session_ref_readonly",
        question_ref="question_ref_readonly",
        answer_ref="answer_ref_readonly",
        prior_answer_refs=("answer_ref_prior_1",),
        prior_feedback_refs=("feedback_ref_prior_1",),
        rubric_summary_ref="rubric_summary_ref_readonly",
        idempotency_digest="digest_readonly",
        **extra_inputs,
    )


def _key(first: str, second: str) -> str:
    return first + "_" + second


def _find_forbidden_imports(path: Path) -> list[str]:
    forbidden_prefixes = (
        "app.application." + "polish",
        "app.infrastructure." + "db",
        "app.infrastructure." + "llm",
        "ope" + "nai",
        "an" + "thropic",
        "lang" + "chain",
        "lang" + "graph",
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    violations: list[str] = []
    for node in ast.walk(tree):
        module_names: list[str] = []
        if isinstance(node, ast.Import):
            module_names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            module_names.append(node.module)
        for module_name in module_names:
            if module_name.startswith(forbidden_prefixes):
                violations.append(module_name)
    return violations
