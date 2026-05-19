"""Deterministic fake LLM transport for contract tests."""

from __future__ import annotations

import re
from json import dumps
from typing import Any

from app.domain.shared.enums import ConfidenceLevel, ValidationStatus
from app.domain.shared.ids import stable_resource_id
from app.schemas.job_match import (
    DimensionScore,
    JobMatchResultPayload,
    JobRequirementChunk,
    MatchedRequirement,
    ResumeChunk,
    ResumeEvidence,
    SourceEvidenceRef,
)
from app.infrastructure.llm.types import LlmTransportRequest, LlmTransportResult


class FakeLlmTransport:
    status = "deterministic_fake_only"

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        if request.task_type == "job_match_analysis":
            return _generate_fake_job_match(request)
        seed = dumps(
            {
                "contract_ids": sorted(request.contract_ids),
                "task_type": request.task_type,
                "input_refs": sorted(request.input_refs),
                "evidence_keys": sorted(request.evidence_bundle.keys()),
            },
            ensure_ascii=True,
            sort_keys=True,
        )
        has_evidence = bool(request.evidence_bundle)
        validation_status = ValidationStatus.VALID if has_evidence else ValidationStatus.VALID_WITH_WARNINGS
        confidence_level = ConfidenceLevel.MEDIUM if has_evidence else ConfidenceLevel.LOW
        low_confidence_flags = () if has_evidence else ("evidence_missing",)
        trace_ref = stable_resource_id("trace", f"fake-llm-trace:{seed}")
        evidence_ref = stable_resource_id("trace", f"fake-llm-evidence:{seed}")
        return LlmTransportResult(
            result={
                "transport": "fake",
                "task_type": request.task_type,
                "contract_ids": list(request.contract_ids),
                "result_ref": stable_resource_id("task", f"fake-llm-result:{seed}"),
                "summary": "deterministic skeleton result",
            },
            validation_status=validation_status,
            confidence_level=confidence_level,
            low_confidence_flags=low_confidence_flags,
            trace_refs=(trace_ref,),
            evidence_refs=(evidence_ref,),
        )


def _generate_fake_job_match(request: LlmTransportRequest) -> LlmTransportResult:
    resume_chunks = _resume_chunks(request.evidence_bundle)
    job_chunks = _job_requirement_chunks(request.evidence_bundle)
    seed = dumps(
        {
            "contract_ids": sorted(request.contract_ids),
            "task_type": request.task_type,
            "input_refs": sorted(request.input_refs),
            "source_digest": request.evidence_bundle.get("source_digest"),
        },
        ensure_ascii=True,
        sort_keys=True,
    )
    trace_ref = stable_resource_id("trace", f"fake-job-match-trace:{seed}")
    evidence_ref = stable_resource_id("trace", f"fake-job-match-evidence:{seed}")
    payload = _fake_job_match_payload(resume_chunks, job_chunks)
    return LlmTransportResult(
        result={
            "transport": "fake",
            "task_type": request.task_type,
            "contract_ids": list(request.contract_ids),
            "result_ref": stable_resource_id("task", f"fake-job-match-result:{seed}"),
            "model_name": "fake_llm_job_match_v1",
            "prompt_version": "P-JOBMATCH-001+P-JOBMATCH-002+P-JOBMATCH-003.v1",
            "job_match_result_payload": payload.model_dump(mode="json"),
        },
        validation_status=ValidationStatus.VALID,
        confidence_level=ConfidenceLevel.MEDIUM,
        low_confidence_flags=(),
        trace_refs=(trace_ref,),
        evidence_refs=(evidence_ref,),
    )


def _fake_job_match_payload(
    resume_chunks: list[ResumeChunk],
    job_chunks: list[JobRequirementChunk],
) -> JobMatchResultPayload:
    resume_text = "\n".join(chunk.text for chunk in resume_chunks)
    job_text = "\n".join(chunk.text for chunk in job_chunks)
    resume_tokens = _tokens(resume_text)
    job_tokens = _tokens(job_text)
    overlap = resume_tokens & job_tokens
    overlap_ratio = len(overlap) / max(1, min(len(resume_tokens), len(job_tokens)))
    has_overlap = bool(overlap)
    resume_chunk_id = resume_chunks[0].chunk_id
    job_chunk_id = job_chunks[0].chunk_id
    evidence = [SourceEvidenceRef(chunk_id=resume_chunk_id)]

    requirement_alignment = _bounded_score(15 + round(15 * overlap_ratio), 8, 30)
    experience_evidence = _bounded_score(14 + min(len(resume_chunks), 3) * 2 + (3 if has_overlap else 0), 8, 25)
    skill_coverage = _bounded_score(9 + round(10 * overlap_ratio), 5, 20)
    gap_risk = 13 if has_overlap else 8
    readiness_actions = 8 if has_overlap else 5
    overall_score = (
        requirement_alignment
        + experience_evidence
        + skill_coverage
        + gap_risk
        + readiness_actions
    )
    overall_level = (
        "strong_match"
        if overall_score >= 80
        else "medium_match"
        if overall_score >= 60
        else "weak_match"
    )
    confidence = "medium" if has_overlap else "low"

    return JobMatchResultPayload(
        overall_score=overall_score,
        overall_level=overall_level,
        confidence=confidence,
        summary=f"基于 LLM 分析链路读取到的岗位与简历证据，当前匹配分为 {overall_score} / 100。",
        dimension_scores=[
            DimensionScore(
                key="requirement_alignment",
                score=requirement_alignment,
                max_score=30,
                rationale="LLM 分析链路识别出岗位关键要求与简历证据之间的直接重合点。",
                supporting_evidence=evidence,
                gaps=[] if has_overlap else ["岗位关键要求与简历证据的直接重合不足。"],
                confidence=confidence,
            ),
            DimensionScore(
                key="experience_evidence",
                score=experience_evidence,
                max_score=25,
                rationale="简历片段提供了可追问的经历、项目或工作流证据。",
                supporting_evidence=evidence,
                gaps=[],
                confidence=confidence,
            ),
            DimensionScore(
                key="skill_coverage",
                score=skill_coverage,
                max_score=20,
                rationale="技能覆盖分来自岗位文本与简历文本中的技能证据交集。",
                supporting_evidence=evidence,
                gaps=[] if overlap else ["需要补充更明确的技能证据。"],
                confidence=confidence,
            ),
            DimensionScore(
                key="gap_risk",
                score=gap_risk,
                max_score=15,
                rationale="缺口风险根据未覆盖要求和可追问证据完整度进行降级。",
                supporting_evidence=evidence,
                gaps=["面试中继续确认经验深度。"],
                confidence="medium",
            ),
            DimensionScore(
                key="readiness_actions",
                score=readiness_actions,
                max_score=10,
                rationale="后续准备动作可基于当前证据形成聚焦追问。",
                supporting_evidence=evidence,
                gaps=[],
                confidence="medium",
            ),
        ],
        matched_requirements=[
            MatchedRequirement(
                requirement_chunk_id=job_chunk_id,
                resume_evidence_chunk_ids=[resume_chunk_id],
                rationale="LLM 分析链路将岗位要求与最相关的简历证据建立了引用关系。",
                confidence=confidence,
            )
        ],
        missing_requirements=[],
        resume_evidence=[
            ResumeEvidence(
                chunk_id=resume_chunk_id,
                summary="用于岗位匹配分析的主要简历证据。",
                confidence=confidence,
            )
        ],
        risk_flags=[],
        interview_focus=["围绕匹配度最高的证据追问候选人的真实参与深度。"],
        suggested_questions=["请结合岗位要求说明这段经历中最能证明匹配度的具体产出。"],
        markdown_report="# 岗位匹配分析\n\n本结果由 LLM 分析链路基于当前岗位与简历证据生成。",
    )


def _resume_chunks(evidence_bundle: dict[str, Any]) -> list[ResumeChunk]:
    return [
        ResumeChunk.model_validate(chunk)
        for chunk in evidence_bundle.get("resume_chunks", [])
    ]


def _job_requirement_chunks(evidence_bundle: dict[str, Any]) -> list[JobRequirementChunk]:
    return [
        JobRequirementChunk.model_validate(chunk)
        for chunk in evidence_bundle.get("job_requirement_chunks", [])
    ]


def _tokens(text: str) -> set[str]:
    lowered = text.lower()
    ascii_tokens = set(re.findall(r"[a-z0-9]{2,}", lowered))
    cjk_tokens: set[str] = set()
    for segment in re.findall(r"[\u4e00-\u9fff]+", lowered):
        if len(segment) == 1:
            cjk_tokens.add(segment)
        else:
            cjk_tokens.update(segment[index : index + 2] for index in range(len(segment) - 1))
    return ascii_tokens | cjk_tokens


def _bounded_score(value: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, value))
