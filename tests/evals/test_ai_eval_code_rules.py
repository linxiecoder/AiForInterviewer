from __future__ import annotations

from pathlib import Path

import pytest

from evals.graders.code_rules import grade_case, grade_dataset, load_jsonl


REPO_ROOT = Path(__file__).resolve().parents[2]
DATASETS = (
    REPO_ROOT / "evals" / "datasets" / "question_generation.jsonl",
    REPO_ROOT / "evals" / "datasets" / "feedback_asset_consistency.jsonl",
    REPO_ROOT / "evals" / "datasets" / "feedback_answer_change.jsonl",
    REPO_ROOT / "evals" / "datasets" / "asset_candidate.jsonl",
)


def test_load_jsonl_reads_dataset_cases() -> None:
    cases = load_jsonl(DATASETS[0])

    assert len(cases) >= 3
    assert {case["case_id"] for case in cases} >= {
        "qg_direct_project_evidence",
        "qg_job_gap_only",
        "qg_adjacent_project_evidence",
    }


@pytest.mark.parametrize("dataset", DATASETS)
def test_builtin_dataset_lint_passes(dataset: Path) -> None:
    summary = grade_dataset(dataset)

    assert summary["total"] > 0
    assert summary["failed"] == 0
    assert summary["passed"] == summary["total"]
    assert summary["score"] == 1


def test_forbidden_sensitive_keys_are_caught() -> None:
    result = grade_case(
        {
            "case_id": "contains_secret_key",
            "task_type": "question_generation",
            "input": {"raw_prompt": "do not store"},
            "expected": {"question_mode": "hypothetical_design"},
            "must_have": [],
            "must_not_have": [],
            "grader_notes": "Should fail before domain grading.",
        }
    )

    assert result["passed"] is False
    assert "forbidden_key:input.raw_prompt" in result["failures"]


def test_forbidden_sensitive_keys_are_caught_in_candidate_output() -> None:
    result = grade_case(
        {
            "case_id": "candidate_output_contains_provider_payload",
            "task_type": "asset_candidate",
            "input": {"feedback_summary": "Candidate described reusable project expression."},
            "expected": {"project_asset_update_candidates": []},
            "candidate_output": {"provider_payload": {"id": "raw-provider-response"}},
            "must_have": [],
            "must_not_have": [],
            "grader_notes": "Candidate output must also be sanitized before report use.",
        }
    )

    assert result["passed"] is False
    assert "forbidden_key:candidate_output.provider_payload" in result["failures"]


def test_unknown_task_type_fails() -> None:
    result = grade_case(
        {
            "case_id": "unknown_task_type",
            "task_type": "unknown_eval_task",
            "input": {},
            "expected": {},
            "must_have": [],
            "must_not_have": [],
            "grader_notes": "Unsupported task types should not silently pass.",
        }
    )

    assert result["passed"] is False
    assert "unsupported_task_type:unknown_eval_task" in result["failures"]


def test_candidate_output_is_used_for_must_have_and_must_not_have() -> None:
    result = grade_case(
        {
            "case_id": "candidate_output_text_checks",
            "task_type": "question_generation",
            "input": {"source_support_level": "job_gap_only"},
            "expected": {"question_mode": "能力补偿题"},
            "candidate_output": {"question": "你负责过 Redis 缓存治理吗？"},
            "must_have": ["Redis"],
            "must_not_have": ["你负责过"],
            "grader_notes": "When candidate output exists, string rules apply to output instead of expected lint.",
        }
    )

    assert result["passed"] is False
    assert "must_not_have_present:你负责过" in result["failures"]
    assert not any(failure.startswith("must_have_missing:Redis") for failure in result["failures"])


def test_rag_non_claim_eval_blocks_knowledge_base_retrieval_claim() -> None:
    result = grade_case(
        {
            "case_id": "rag_unavailable_non_claim",
            "task_type": "question_generation",
            "input": {
                "source_support_level": "direct_project_evidence",
                "retrieved_rag_chunks": {
                    "available": False,
                    "items": [],
                    "unavailable_reason": "full_retrieval_not_enabled",
                },
            },
            "expected": {
                "required_question_focus": ["真实实现链路", "职责边界", "关键取舍", "验证方式"],
            },
            "candidate_output": {
                "question": "AI 已经检索并使用知识库，请结合检索片段说明实现链路。"
            },
            "must_have": [],
            "must_not_have": ["AI 已经检索并使用知识库", "检索片段"],
            "grader_notes": "available=false means saved assets exist, but this generation did not use knowledge base retrieval.",
        }
    )

    assert result["passed"] is False
    assert "must_not_have_present:AI 已经检索并使用知识库" in result["failures"]
    assert "must_not_have_present:检索片段" in result["failures"]


def test_archived_asset_excluded_sample_is_recognized() -> None:
    cases = load_jsonl(REPO_ROOT / "evals" / "datasets" / "feedback_asset_consistency.jsonl")
    archived_case = next(case for case in cases if case["case_id"] == "fb_archived_asset_excluded")

    result = grade_case(archived_case)

    assert result["passed"] is True
    assert "archived_asset_historical_reference_only" in result["checked_rules"]


def test_asset_candidate_requires_user_confirmation() -> None:
    result = grade_case(
        {
            "case_id": "candidate_without_confirmation",
            "task_type": "asset_candidate",
            "input": {"feedback_summary": "Candidate described a reusable FastAPI project expression."},
            "expected": {
                "project_asset_update_candidates": [
                    {
                        "candidate_id": "asset_candidate_missing_confirmation",
                        "status": "asset_candidate_generated",
                        "summary": "FastAPI workflow expression",
                    }
                ]
            },
            "must_have": [],
            "must_not_have": ["asset_confirmed", "asset_archived"],
            "grader_notes": "Every asset candidate must require user confirmation.",
        }
    )

    assert result["passed"] is False
    assert "asset_candidate_user_confirmation_required" in result["failures"]
