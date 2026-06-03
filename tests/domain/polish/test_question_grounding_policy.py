from __future__ import annotations

from app.domain.polish.policies.question_grounding_policy import (
    QuestionGroundingAction,
    QuestionGroundingInput,
    QuestionGroundingPolicy,
)


def test_direct_project_evidence_allows_grounded_real_project_question() -> None:
    decision = QuestionGroundingPolicy.evaluate(
        QuestionGroundingInput(
            question_text="你在库存扣减链路中是怎么实现分布式锁和事务消息一致性的？",
            claim_mode="evidence_grounded",
            primary_evidence_ref="resume_project_1",
            primary_evidence_text="库存扣减链路使用分布式锁和事务消息保证最终一致性。",
            evidence_refs=("resume_project_1",),
            primary_source_type="resume_project",
            source_support_level="direct_project_evidence",
        )
    )

    assert decision.passed
    assert decision.action == QuestionGroundingAction.ALLOW
    assert decision.reason_codes == ()


def test_adjacent_project_evidence_blocks_completed_experience_claim() -> None:
    decision = QuestionGroundingPolicy.evaluate(
        QuestionGroundingInput(
            question_text="你实现过分布式锁后，如何处理半消息回查？",
            claim_mode="evidence_grounded",
            primary_evidence_ref="resume_project_weak",
            primary_evidence_text="候选人做过大文件异步处理管道。",
            evidence_refs=("resume_project_weak",),
            primary_source_type="resume_project",
            source_support_level="adjacent_project_evidence",
        )
    )

    assert not decision.passed
    assert decision.action == QuestionGroundingAction.BLOCK
    assert "adjacent_project_evidence_forbidden_completed_experience_claim" in decision.blocking_reason_codes


def test_job_gap_only_does_not_allow_candidate_experience_claim() -> None:
    decision = QuestionGroundingPolicy.evaluate(
        QuestionGroundingInput(
            question_text="你负责过分布式一致性项目时怎么做失败补偿？",
            claim_mode="job_gap_probe",
            primary_evidence_ref="job_req_1",
            primary_evidence_text="岗位要求分布式一致性设计能力。",
            evidence_refs=("job_req_1",),
            primary_source_type="job_requirement",
            source_support_level="job_gap_only",
        )
    )

    assert not decision.passed
    assert "job_gap_only_forbidden_candidate_experience_claim" in decision.blocking_reason_codes
    assert "job_gap_probe_forbidden_claim:你负责过" in decision.blocking_reason_codes


def test_insufficient_context_requires_clarification_for_factual_question() -> None:
    decision = QuestionGroundingPolicy.evaluate(
        QuestionGroundingInput(
            question_text="你在项目里怎么实现分布式锁？",
            claim_mode="evidence_grounded",
            primary_evidence_ref=None,
            primary_evidence_text=None,
            evidence_refs=(),
            primary_source_type=None,
            source_support_level="insufficient_context",
        )
    )

    assert not decision.passed
    assert decision.action == QuestionGroundingAction.CLARIFY
    assert decision.requires_clarification
    assert "insufficient_context_requires_clarification" in decision.blocking_reason_codes
    assert "empty_evidence_refs_for_factual_question" in decision.blocking_reason_codes


def test_confirmed_assets_block_unsupported_completed_stack_claim_conflict() -> None:
    decision = QuestionGroundingPolicy.evaluate(
        QuestionGroundingInput(
            question_text="你实现了 FastAPI 工作流中的 Redis 分布式锁后，故障恢复怎么验证？",
            claim_mode="evidence_grounded",
            primary_evidence_ref="asset_backend_workflow",
            primary_evidence_text="Backend workflow automation uses FastAPI APIs and PostgreSQL persistence.",
            evidence_refs=("asset_backend_workflow",),
            primary_source_type="asset_summary",
            source_support_level="direct_project_evidence",
            confirmed_asset_texts=(
                "Backend workflow automation Candidate built FastAPI APIs with PostgreSQL persistence.",
            ),
        )
    )

    assert not decision.passed
    assert "unsupported_technology_stack_as_completed_experience" in decision.blocking_reason_codes
    assert "question_conflicts_with_canonical_assets" in decision.blocking_reason_codes
