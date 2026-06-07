from __future__ import annotations

POLISH_FEEDBACK_FINAL_SCHEMA_ID = "polish_feedback_generated_v1"
POLISH_FEEDBACK_FINAL_SCHEMA_VERSION = "1.0"
POLISH_FEEDBACK_AGENT_PROMPT_VERSION = "polish_feedback_agent_prompt.v1"
POLISH_FEEDBACK_TASK_TYPE = "polish_feedback_generation"
POLISH_FEEDBACK_CANDIDATE_MODE = "candidate_compact"
POLISH_FEEDBACK_CANDIDATE_TASK = "polish_feedback_candidate_v1"
POLISH_FEEDBACK_FINAL_CONTRACT_IDS = (
    "P-POLISH-003",
    "P-POLISH-004",
    "P-POLISH-005",
)
POLISH_FEEDBACK_FUTURE_CONTRACT_HINTS = ("P-POLISH-009",)

# Final payload fields returned by server-side feedback generation API.
POLISH_FEEDBACK_FINAL_PAYLOAD_FIELDS = (
    "schema_id",
    "schema_version",
    "status",
    "contract_ids",
    "feedback_id",
    "feedback_text",
    "answer_summary",
    "score_result",
    "loss_points",
    "reference_answer",
    "asset_consistency_check",
    "answer_coverage",
    "answer_change_analysis",
    "feedback_cards",
    "next_recommended_actions",
    "low_confidence_flags",
    "trace_refs",
    "feedback_metadata",
)

# Candidate payload fields produced by LLM model output (pre-server synthesis).
POLISH_FEEDBACK_CANDIDATE_PAYLOAD_FIELDS = (
    "feedback_text",
    "answer_summary",
    "score_reasoning",
    "loss_points",
    "reference_answer",
    "same_question_effect",
    "project_asset_update_candidates",
    "low_confidence_flags",
    "evidence_refs",
)
