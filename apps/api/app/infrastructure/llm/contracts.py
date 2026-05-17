"""LLM contract baseline constants."""

SUPPORTED_FAKE_TASK_TYPES = frozenset(
    {
        "job_match_analysis",
        "polish_feedback",
        "report_generation",
        "review_analysis",
        "weakness_extraction",
        "asset_candidate_extraction",
        "training_suggestion_generation",
    }
)

