"""LLM contract baseline constants."""

SUPPORTED_FAKE_TASK_TYPES = frozenset(
    {
        "job_match_analysis",
        "polish_feedback",
        "polish_progress_tree_plan",
        "polish_progress_tree_state",
        "report_generation",
        "review_analysis",
        "weakness_extraction",
        "asset_candidate_extraction",
        "training_suggestion_generation",
    }
)
