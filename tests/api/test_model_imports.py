import importlib
import sys

from app.infrastructure.db.base import Base


MODEL_MODULES = (
    "app.infrastructure.db.models.user",
    "app.infrastructure.db.models.resume",
    "app.infrastructure.db.models.job",
    "app.infrastructure.db.models.binding",
    "app.infrastructure.db.models.interview",
    "app.infrastructure.db.models.question",
    "app.infrastructure.db.models.answer",
    "app.infrastructure.db.models.feedback",
    "app.infrastructure.db.models.polish_candidate",
    "app.infrastructure.db.models.scoring",
    "app.infrastructure.db.models.ai_task",
    "app.infrastructure.db.models.report",
    "app.infrastructure.db.models.review",
    "app.infrastructure.db.models.asset",
    "app.infrastructure.db.models.rag",
    "app.infrastructure.db.models.weakness",
    "app.infrastructure.db.models.training",
    "app.infrastructure.db.models.reference",
    "app.infrastructure.db.models.audit",
    "app.infrastructure.db.models.ai_runtime",
)


def test_sqlalchemy_model_modules_import_without_side_effect_errors() -> None:
    for module_name in MODEL_MODULES:
        importlib.import_module(module_name)

    assert {
        "user_accounts",
        "resumes",
        "resume_versions",
        "jobs",
        "job_versions",
        "resume_job_bindings",
        "interview_sessions",
        "polish_session_details",
        "pressure_session_details",
        "questions",
        "answers",
        "feedback",
        "polish_candidates",
        "score_rule_sets",
        "score_rule_versions",
        "score_dimensions",
        "score_results",
        "score_evidence_links",
        "low_confidence_flags",
        "ai_tasks",
        "ai_task_results",
        "api_request_traces",
        "audit_events",
        "evidence_refs",
        "trace_refs",
        "user_confirmations",
        "agent_runs",
        "agent_node_runs",
        "agent_interrupts",
        "agent_checkpoint_refs",
        "llm_calls",
        "llm_call_payloads",
        "rag_documents",
        "rag_chunks",
    }.issubset(Base.metadata.tables)


def test_ai_runtime_model_import_does_not_load_langgraph_or_langchain() -> None:
    before = set(sys.modules)

    importlib.import_module("app.infrastructure.db.models.ai_runtime")

    loaded = set(sys.modules) - before
    assert not any(module == "langgraph" or module.startswith("langgraph.") for module in loaded)
    assert not any(module == "langchain" or module.startswith("langchain.") for module in loaded)
