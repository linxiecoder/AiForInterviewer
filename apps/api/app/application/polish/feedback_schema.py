from __future__ import annotations

from app.application.polish.feedback_models import (
    FeedbackCandidatePayload,
    FeedbackFinalPayload,
    POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
    POLISH_FEEDBACK_CANDIDATE_MODE,
    POLISH_FEEDBACK_CANDIDATE_TASK,
    POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
    POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
    POLISH_FEEDBACK_FUTURE_CONTRACT_HINTS,
    POLISH_FEEDBACK_TASK_TYPE,
)


# Final payload fields returned by server-side feedback generation API.
POLISH_FEEDBACK_FINAL_PAYLOAD_FIELDS = tuple(FeedbackFinalPayload.model_fields)

# Candidate payload fields produced by LLM model output (pre-server synthesis).
POLISH_FEEDBACK_CANDIDATE_PAYLOAD_FIELDS = tuple(FeedbackCandidatePayload.model_fields)
