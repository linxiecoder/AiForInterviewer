from __future__ import annotations

POLISH_FEEDBACK_GENERATED_SCHEMA_ID = "polish_feedback_generated_v1"
POLISH_FEEDBACK_GENERATED_SCHEMA_VERSION = "1.0"
POLISH_FEEDBACK_AGENT_PROMPT_VERSION = "polish_feedback_agent_prompt.v1"
POLISH_FEEDBACK_TASK_TYPE = "polish_feedback_generation"
POLISH_FEEDBACK_GENERATED_CONTRACT_IDS = (
    "P-POLISH-003",
    "P-POLISH-004",
    "P-POLISH-005",
)
POLISH_FEEDBACK_FUTURE_CONTRACT_HINTS = ("P-POLISH-009",)

POLISH_FEEDBACK_GENERATED_PAYLOAD_FIELDS = (
    "schema_id",
    "schema_version",
    "status",
    "contract_ids",
    "feedback_text",
    "answer_summary",
    "score_result",
    "explicit_score",
    "implicit_score",
    "scoring_dimensions",
    "loss_points",
    "reference_answer",
    "knowledge_points",
    "technical_principles",
    "same_question_effect",
    "project_asset_consistency_check",
    "session_similarity_check",
    "project_asset_update_candidates",
    "next_recommended_actions",
    "low_confidence_flags",
    "trace_refs",
    "feedback_metadata",
)
