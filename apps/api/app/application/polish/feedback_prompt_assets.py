from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
    POLISH_FEEDBACK_GENERATED_CONTRACT_IDS,
    POLISH_FEEDBACK_GENERATED_PAYLOAD_FIELDS,
    POLISH_FEEDBACK_GENERATED_SCHEMA_ID,
    POLISH_FEEDBACK_GENERATED_SCHEMA_VERSION,
    POLISH_FEEDBACK_TASK_TYPE,
)


def build_feedback_prompt_asset(context: object) -> dict[str, Any]:
    """Build the compact runtime prompt asset for generated polish feedback."""

    return {
        "task_type": POLISH_FEEDBACK_TASK_TYPE,
        "prompt_version": POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
        "schema_id": POLISH_FEEDBACK_GENERATED_SCHEMA_ID,
        "schema_version": POLISH_FEEDBACK_GENERATED_SCHEMA_VERSION,
        "contract_ids": list(POLISH_FEEDBACK_GENERATED_CONTRACT_IDS),
        "redaction_boundary": {
            "store_raw_model_io": False,
            "forbidden_outputs": [
                "raw prompt text",
                "model completion text",
                "provider request or response body",
                "secrets or credentials",
                "full resume or full job description",
            ],
        },
        "current_question": {
            "question_id": _get_text(context, "question_id"),
            "question_text": _get_text(context, "question_text", max_chars=12000),
            "polish_theme": _get_text(context, "polish_theme", max_chars=500),
            "progress_node_ref": _get_text(context, "progress_node_ref", max_chars=200),
            "question_sources": _get_list(context, "question_sources"),
            "evidence_refs": _get_list(context, "evidence_refs"),
        },
        "current_answer": {
            "answer_id": _get_text(context, "answer_id"),
            "answer_text": _get_text(context, "answer_text", max_chars=12000),
            "answer_round": _get(context, "answer_round"),
        },
        "same_question_answers": _get_list(context, "same_question_answers"),
        "same_project_turns": _get_list(context, "same_project_turns"),
        "session_recent_turns": _get_list(context, "session_recent_turns"),
        "project_asset_summaries": _get_list(context, "project_asset_summaries"),
        "context_snapshots": {
            "job_snapshot": _get_dict(context, "job_snapshot"),
            "resume_snapshot": _get_dict(context, "resume_snapshot"),
            "progress_node_snapshot": _get_dict(context, "progress_node_snapshot"),
        },
        "output_schema": {
            "schema_id": POLISH_FEEDBACK_GENERATED_SCHEMA_ID,
            "schema_version": POLISH_FEEDBACK_GENERATED_SCHEMA_VERSION,
            "required_status": "generated_or_partial_or_low_confidence",
            "fields": list(POLISH_FEEDBACK_GENERATED_PAYLOAD_FIELDS),
        },
        "validation_rules": [
            "Output schema_id must be polish_feedback_generated_v1.",
            "Do not invent user experience or project facts.",
            "If the answer conflicts with a project asset, ask for clarification instead of choosing for the user.",
            "Every major loss point must be covered by a reference answer section.",
            "Asset updates must be project_asset_update_candidate only and require user confirmation.",
            "Similar content in the same mock interview should be reported as repeated, covered, or conflicting instead of deducting without evidence.",
        ],
    }


def _get(context: object, field_name: str) -> object:
    if isinstance(context, dict):
        return context.get(field_name)
    return getattr(context, field_name, None)


def _get_text(context: object, field_name: str, *, max_chars: int = 240) -> str:
    value = _get(context, field_name)
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text


def _get_dict(context: object, field_name: str) -> dict[str, Any]:
    value = _get(context, field_name)
    if not isinstance(value, dict):
        return {}
    return deepcopy(value)


def _get_list(context: object, field_name: str) -> list[Any]:
    value = _get(context, field_name)
    if not isinstance(value, (list, tuple)):
        return []
    return deepcopy(list(value))
