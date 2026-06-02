"""Test-only LLM fake facade.

Production app code must not import from ``tests`` modules. Runtime provider
configuration must also keep rejecting ``LLM_PROVIDER=fake``; this facade exists
only for explicit test injection.
"""

from app.infrastructure.llm.fake_transport import FakeLlmTransport


SUPPORTED_FAKE_TASK_TYPES = frozenset(
    {
        "job_match_analysis",
        "polish_feedback",
        "polish_progress_quality_first_menu",
        "polish_progress_tree_state",
        "polish_question_generation",
        "report_generation",
        "review_analysis",
        "weakness_extraction",
        "asset_candidate_extraction",
        "training_suggestion_generation",
    }
)

__all__ = ["FakeLlmTransport", "SUPPORTED_FAKE_TASK_TYPES"]
