from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

from app.application.llm import agent_io
from app.application.polish.entities import PolishQuestionSource
from app.application.polish.progress_prompts import (
    POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
    build_progress_tree_state_refresh_prompt,
)
from app.application.polish.progress_v2_prompts import (
    POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION,
    POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID,
    POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_VERSION,
    POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE,
    build_progress_quality_first_menu_prompt,
)
from app.application.polish.question_blueprint import EvidenceScope, QuestionBlueprint
from app.application.polish.question_generation_prompts import build_question_prompt_asset
from app.application.polish.question_generation_service import _parse_llm_question_payload


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read_source(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def _question_blueprint() -> QuestionBlueprint:
    return QuestionBlueprint(
        question_kind="project_deep_dive",
        claim_mode="evidence_grounded",
        progress_node_ref="node_payments",
        node_title="Payment consistency",
        expected_capability="Explain idempotency, retry, and compensation.",
        primary_evidence_ref="resume_project_001",
        primary_evidence_text="Built payment retry and compensation workflows.",
        evidence_refs=("resume_project_001",),
    )


def _question_scope() -> EvidenceScope:
    return EvidenceScope(
        progress_node_ref="node_payments",
        node_title="Payment consistency",
        expected_capability="Explain idempotency, retry, and compensation.",
        primary_evidence_ref="resume_project_001",
        primary_evidence_text="Built payment retry and compensation workflows.",
        primary_source_type="resume_project",
        evidence_refs=("resume_project_001",),
        question_sources=(
            PolishQuestionSource(
                index=1,
                source_type="resume_project",
                title="Payment platform",
                excerpt="Built payment retry and compensation workflows.",
                ref_id="resume_project_001",
                availability="available",
            ),
        ),
    )


def _progress_context() -> dict[str, Any]:
    return {
        "session": {
            "session_id": "sess_test",
            "mode": "polish",
            "topic": "topic_technical_depth",
            "subtopic": None,
            "custom_topic": None,
        },
        "job_snapshot": {
            "job_id": "job_test",
            "job_version_id": "job_ver_test",
            "title": "Backend Engineer",
            "company": "ACME",
            "department": "Engineering",
            "responsibilities": ["Own backend APIs."],
            "requirements": ["Python, FastAPI, and distributed workflow experience."],
            "other_notes": "PostgreSQL is a plus.",
            "application_status": "draft",
            "content_digest": "job-digest",
        },
        "resume_snapshot": {
            "resume_id": "res_test",
            "resume_version_id": "res_ver_test",
            "title": "Backend Resume",
            "markdown_text": "## Project\nBuilt backend workflow automation with retries.",
            "summary": "Backend engineer.",
            "skills": [],
            "project_experiences": [],
            "work_experiences": [],
            "content_digest": "resume-digest",
        },
        "match_context": {
            "available": False,
            "overall_score": None,
            "summary": None,
            "matched_points": [],
            "missing_points": [],
            "improvement_points": [],
            "interview_focus": [],
            "suggested_questions": [],
        },
        "weakness_context": {"items": []},
        "asset_context": {"items": []},
        "turns": [
            {
                "turn_index": 1,
                "question_text": "How did you handle retries?",
                "answer_text": "I used idempotency keys and retry queues.",
                "feedback_text": "Needs more detail on compensation.",
                "answers": [],
            }
        ],
        "content_digest": "context-digest",
    }


def _existing_progress_plan() -> dict[str, Any]:
    return {
        "status": "ready",
        "nodes": [
            {
                "progress_node_ref": "node_payments",
                "title": "Payment consistency",
                "expected_capability": "Explain idempotency and compensation.",
                "children": [],
            }
        ],
    }


def test_agent_io_module_has_no_reverse_business_or_transport_dependencies() -> None:
    source = _read_source("apps/api/app/application/llm/agent_io.py")

    assert "app.application.polish" not in source
    assert "app.domain" not in source
    assert "app.infrastructure" not in source
    assert "FakeLlmTransport" not in source


def test_shared_agent_io_types_are_exported() -> None:
    for type_name in (
        "AgentEvidenceItem",
        "AgentFocusTarget",
        "AgentPromptBundle",
        "AgentOutputEnvelope",
        "AgentSafetyPolicy",
    ):
        assert hasattr(agent_io, type_name)
        assert inspect.isclass(getattr(agent_io, type_name))
    assert hasattr(agent_io, "DEFAULT_AGENT_SAFETY_POLICY")
    assert isinstance(agent_io.DEFAULT_AGENT_SAFETY_POLICY, agent_io.AgentSafetyPolicy)


def test_prompt_builders_use_agent_prompt_bundle_and_safety_policy_source_contract() -> None:
    for builder in (
        build_question_prompt_asset,
        build_progress_quality_first_menu_prompt,
        build_progress_tree_state_refresh_prompt,
    ):
        source = inspect.getsource(builder)
        assert "AgentPromptBundle(" in source
        assert "AgentSafetyPolicy(" in source or "DEFAULT_AGENT_SAFETY_POLICY" in source


def test_question_prompt_keeps_input_data_top_level_contract() -> None:
    prompt_asset = build_question_prompt_asset(_question_blueprint(), _question_scope())

    assert {
        "prompt_version",
        "schema_id",
        "schema_version",
        "task_type",
        "prompt",
        "input_data",
        "output_schema",
    } <= set(prompt_asset)
    assert "context" not in prompt_asset
    assert prompt_asset["input_data"]["evidence_refs"] == ["resume_project_001"]


def test_progress_initial_prompt_keeps_context_top_level_contract() -> None:
    bundle = build_progress_quality_first_menu_prompt(_progress_context())

    assert set(bundle) == {
        "source_digest",
        "task_type",
        "prompt_version",
        "schema_id",
        "schema_version",
        "prompt",
        "context",
        "output_schema",
    }
    assert "input_data" not in bundle
    assert bundle["source_digest"] == "context-digest"
    assert bundle["task_type"] == POLISH_PROGRESS_QUALITY_FIRST_MENU_TASK_TYPE
    assert bundle["prompt_version"] == POLISH_PROGRESS_QUALITY_FIRST_MENU_PROMPT_VERSION
    assert bundle["schema_id"] == POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_ID
    assert bundle["schema_version"] == POLISH_PROGRESS_QUALITY_FIRST_MENU_SCHEMA_VERSION


def test_progress_state_refresh_prompt_keeps_context_and_compatibility_fields() -> None:
    existing_plan = _existing_progress_plan()
    existing_state = {
        "status": "ready",
        "node_states": [],
        "current_priority": {"progress_node_ref": "node_payments"},
    }

    bundle = build_progress_tree_state_refresh_prompt(
        context=_progress_context(),
        existing_plan=existing_plan,
        existing_state=existing_state,
    )

    assert {
        "source_digest",
        "task_type",
        "prompt_version",
        "schema_id",
        "schema_version",
        "prompt",
        "context",
        "output_schema",
        "selected_evidence_chunks",
        "dropped_context_summary",
        "match_context_summary",
        "turns_summary",
        "existing_progress_tree_plan",
        "existing_progress_tree_state",
    } <= set(bundle)
    assert "input_data" not in bundle
    assert bundle["source_digest"] == "context-digest"
    assert bundle["task_type"] == "polish_progress_tree_state"
    assert bundle["prompt_version"] == POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION
    assert bundle["schema_id"] == POLISH_PROGRESS_TREE_STATE_SCHEMA_ID
    assert bundle["schema_version"] == POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION
    assert bundle["selected_evidence_chunks"] == bundle["context"]["selected_evidence_chunks"]
    assert bundle["dropped_context_summary"] == bundle["context"]["dropped_context_summary"]
    assert bundle["match_context_summary"] == bundle["context"]["match_context_summary"]
    assert bundle["turns_summary"] == bundle["context"]["turns_summary"]
    assert bundle["existing_progress_tree_plan"] == existing_plan
    assert bundle["existing_progress_tree_state"] == existing_state


def test_output_parsers_use_agent_output_envelope_source_contract() -> None:
    from app.application.polish import progress_tree, progress_tree
    from app.application.polish import question_generation_service

    assert "_question_payload_envelope" in _read_source(
        "apps/api/app/application/polish/question_generation_service.py"
    )
    assert "_question_payload_envelope(" in inspect.getsource(
        question_generation_service._parse_llm_question_payload
    )
    assert "AgentOutputEnvelope(" in inspect.getsource(
        question_generation_service._question_payload_envelope
    )

    assert "_quality_first_menu_payload_envelope" in _read_source(
        "apps/api/app/application/polish/progress_tree.py"
    )
    assert "_quality_first_menu_payload_envelope(" in inspect.getsource(
        progress_tree._normalize_quality_first_menu_payload
    )
    assert "AgentOutputEnvelope(" in inspect.getsource(
        progress_tree._quality_first_menu_payload_envelope
    )

    assert "_progress_tree_state_payload_envelope" in _read_source(
        "apps/api/app/application/polish/progress_tree.py"
    )
    assert "_progress_tree_state_payload_envelope(" in inspect.getsource(
        progress_tree._normalize_state
    )
    assert "AgentOutputEnvelope(" in inspect.getsource(
        progress_tree._progress_tree_state_payload_envelope
    )


def test_legacy_parser_return_shapes_stay_stable() -> None:
    from app.application.polish.progress_tree import _normalize_state
    from app.application.polish.progress_tree import _normalize_quality_first_menu_payload

    question_payload = {
        "question_text": "How did you implement payment retry and compensation?",
        "question_kind": "project_deep_dive",
        "focus_dimension": "project_deep_dive",
        "difficulty": "medium",
        "skill_dimension": "Payment consistency",
        "expected_signal": "Explains implementation details and tradeoffs.",
        "follow_ups": ["How did you prevent duplicate processing?"],
        "scoring_rubric": [{"dimension": "grounding", "signals": ["Uses evidence"]}],
        "missing_context": [],
        "evidence_refs": ["resume_project_001"],
        "confidence": "medium",
        "clarification_needed": False,
    }
    parsed_question = _parse_llm_question_payload(
        question_payload,
        blueprint=_question_blueprint(),
    )

    assert isinstance(parsed_question, tuple)
    assert len(parsed_question) == 2
    assert isinstance(parsed_question[0], dict) or parsed_question[0] is None
    assert isinstance(parsed_question[1], tuple)

    failed_progress_initial = _normalize_quality_first_menu_payload(
        {"status": "failed", "menu_categories": []},
        context=_progress_context(),
    )
    assert failed_progress_initial is None

    normalized_state = _normalize_state(
        {
            "status": "ready",
            "node_states": [],
            "current_priority": {
                "progress_node_ref": "node_payments",
                "title": "Payment consistency",
                "expected_capability": "Explain idempotency and compensation.",
            },
        },
        existing_plan=_existing_progress_plan(),
        allow_refresh_failed=True,
        prompt_version=POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
        schema_id=POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
        schema_version=POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
    )
    assert isinstance(normalized_state, dict)


def test_agent_safety_policy_is_limited_to_prompt_builders_in_this_phase() -> None:
    prompt_builder_files = (
        "apps/api/app/application/llm/agent_io.py",
        "apps/api/app/application/polish/question_generation_prompts.py",
        "apps/api/app/application/polish/progress_v2_prompts.py",
        "apps/api/app/application/polish/progress_prompts.py",
    )
    parser_files = (
        "apps/api/app/application/polish/question_generation_service.py",
        "apps/api/app/application/polish/progress_tree.py",
        "apps/api/app/application/polish/progress_tree.py",
    )

    for relative_path in prompt_builder_files:
        assert "AgentSafetyPolicy" in _read_source(relative_path)
    for relative_path in parser_files:
        assert "AgentSafetyPolicy" not in _read_source(relative_path)


def test_no_unplanned_agent_abstractions_are_started() -> None:
    source = _read_source("apps/api/app/application/llm/agent_io.py")

    for type_name in (
        "AgentRuntime",
        "AgentToolCall",
        "AgentParser",
        "AgentGraph",
        "AgentOrchestrator",
        "AgentTransport",
    ):
        assert f"class {type_name}" not in source
