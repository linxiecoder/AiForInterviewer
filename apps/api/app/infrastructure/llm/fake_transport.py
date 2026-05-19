"""Deterministic fake LLM transport for contract tests."""

from __future__ import annotations

import re
from json import dumps
from typing import Any

from app.application.polish.progress_prompts import (
    POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
    POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID,
    POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION,
    POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
    POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
)
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
        if request.task_type == "polish_progress_tree_plan":
            return _generate_fake_progress_tree_plan(request)
        if request.task_type == "polish_progress_tree_state":
            return _generate_fake_progress_tree_state(request)
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


def _generate_fake_progress_tree_plan(request: LlmTransportRequest) -> LlmTransportResult:
    context = request.evidence_bundle.get("context") if isinstance(request.evidence_bundle, dict) else {}
    selected_chunks = _selected_evidence_chunks(request.evidence_bundle)
    job_requirement = _chunk_text(
        selected_chunks,
        "job_requirement",
        fallback=_legacy_context_text(context, "job_snapshot", "requirements"),
    )
    job_responsibility = _chunk_text(
        selected_chunks,
        "job_responsibility",
        fallback=_legacy_context_text(context, "job_snapshot", "responsibilities"),
    )
    resume_evidence = _chunk_text(
        selected_chunks,
        "resume_project",
        "resume_skill",
        "resume_work_experience",
        fallback=_legacy_context_text(
            context,
            "resume_snapshot",
            "project_experiences",
            "summary",
            "markdown_text",
        ),
    )
    evidence_chunk_ids = _chunk_ids(
        selected_chunks,
        "job_requirement",
        "resume_project",
        "resume_skill",
        "resume_work_experience",
    )
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
    trace_ref = stable_resource_id("trace", f"fake-polish-progress-plan-trace:{seed}")
    evidence_ref = stable_resource_id("trace", f"fake-polish-progress-plan-evidence:{seed}")
    node_ref = "fake_llm_progress_backend_api"
    child_ref = "fake_llm_progress_backend_api_fastapi"
    return LlmTransportResult(
        result={
            "transport": "fake",
            "task_type": request.task_type,
            "contract_ids": list(request.contract_ids),
            "result_ref": stable_resource_id("task", f"fake-polish-progress-plan-result:{seed}"),
            "model_name": "fake_llm_polish_progress_v1",
            "prompt_version": POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
            "schema_id": POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID,
            "schema_version": POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION,
            "progress_tree_plan": {
                "schema_id": POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID,
                "schema_version": POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION,
                "prompt_version": POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
                "status": "ready",
                "nodes": [
                    {
                        "progress_node_ref": node_ref,
                        "title": "Fake LLM 节点：岗位后端能力验证",
                        "expected_capability": f"围绕岗位要求验证候选人的后端落地能力：{job_requirement}",
                        "related_job_requirements": [job_requirement, job_responsibility],
                        "related_resume_evidence": [resume_evidence],
                        "missing_points": ["Fake LLM 缺口：需要继续证明真实贡献边界"],
                        "evidence_chunk_ids": evidence_chunk_ids,
                        "children": [
                            {
                                "progress_node_ref": child_ref,
                                "title": "Fake LLM 子节点：FastAPI 项目证据",
                                "expected_capability": f"用简历证据说明项目中的技术取舍：{resume_evidence}",
                                "related_job_requirements": [job_requirement, job_responsibility],
                                "related_resume_evidence": [resume_evidence],
                                "missing_points": ["Fake LLM 缺口：需要补充指标和风险处理"],
                                "evidence_chunk_ids": evidence_chunk_ids,
                                "children": [],
                            }
                        ],
                    }
                ],
            },
            "progress_tree_state": {
                "schema_id": POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
                "schema_version": POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
                "prompt_version": POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
                "status": "ready",
                "node_states": [
                    {
                        "progress_node_ref": node_ref,
                        "status": "in_progress",
                        "completed_questions_count": 0,
                        "latest_feedback_summary": None,
                    },
                    {
                        "progress_node_ref": child_ref,
                        "status": "in_progress",
                        "completed_questions_count": 0,
                        "latest_feedback_summary": None,
                    },
                ],
                "current_priority": {
                    "progress_node_ref": child_ref,
                    "title": "Fake LLM 子节点：FastAPI 项目证据",
                    "expected_capability": f"用简历证据说明项目中的技术取舍：{resume_evidence}",
                },
                "updated_from_turns_count": 0,
                "progress": {"progress_percent": 0},
            },
        },
        validation_status=ValidationStatus.VALID,
        confidence_level=ConfidenceLevel.MEDIUM,
        low_confidence_flags=(),
        trace_refs=(trace_ref,),
        evidence_refs=(evidence_ref,),
    )


def _generate_fake_progress_tree_state(request: LlmTransportRequest) -> LlmTransportResult:
    existing_plan = request.evidence_bundle.get("existing_progress_tree_plan", {})
    nodes = _flatten_nodes(existing_plan.get("nodes", []) if isinstance(existing_plan, dict) else [])
    target = nodes[-1] if nodes else {"progress_node_ref": "fake_llm_progress_backend_api_fastapi"}
    node_ref = target.get("progress_node_ref", "fake_llm_progress_backend_api_fastapi")
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
    trace_ref = stable_resource_id("trace", f"fake-polish-progress-state-trace:{seed}")
    evidence_ref = stable_resource_id("trace", f"fake-polish-progress-state-evidence:{seed}")
    return LlmTransportResult(
        result={
            "transport": "fake",
            "task_type": request.task_type,
            "contract_ids": list(request.contract_ids),
            "result_ref": stable_resource_id("task", f"fake-polish-progress-state-result:{seed}"),
            "model_name": "fake_llm_polish_progress_v1",
            "prompt_version": POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
            "schema_id": POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
            "schema_version": POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
            "progress_tree_state": {
                "schema_id": POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
                "schema_version": POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
                "prompt_version": POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
                "status": "ready",
                "node_states": [
                    {
                        "progress_node_ref": item.get("progress_node_ref"),
                        "status": "completed" if item.get("progress_node_ref") == node_ref else "pending",
                        "completed_questions_count": 1 if item.get("progress_node_ref") == node_ref else 0,
                        "latest_feedback_summary": "Fake LLM 状态刷新：回答已覆盖该节点，但仍需补指标。",
                    }
                    for item in nodes
                    if item.get("progress_node_ref")
                ],
                "current_priority": {
                    "progress_node_ref": node_ref,
                    "title": target.get("title", "Fake LLM 当前优先级"),
                    "expected_capability": target.get("expected_capability", "Fake LLM 当前能力要求"),
                },
                "updated_from_turns_count": _turns_count(request.evidence_bundle),
                "progress": {"progress_percent": 135},
            },
        },
        validation_status=ValidationStatus.VALID,
        confidence_level=ConfidenceLevel.MEDIUM,
        low_confidence_flags=(),
        trace_refs=(trace_ref,),
        evidence_refs=(evidence_ref,),
    )


def _flatten_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for node in nodes:
        result.append(node)
        result.extend(_flatten_nodes(node.get("children", [])))
    return result


def _selected_evidence_chunks(evidence_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    chunks = evidence_bundle.get("selected_evidence_chunks")
    if not chunks and isinstance(evidence_bundle.get("context"), dict):
        chunks = evidence_bundle["context"].get("selected_evidence_chunks")
    if not isinstance(chunks, list):
        return []
    return [chunk for chunk in chunks if isinstance(chunk, dict)]


def _chunk_text(chunks: list[dict[str, Any]], *source_types: str, fallback: str | None = None) -> str:
    source_type_set = set(source_types)
    for chunk in chunks:
        if chunk.get("source_type") in source_type_set:
            text = _first_text(chunk.get("text"), chunk.get("title"))
            if text:
                return text
    return fallback or ""


def _chunk_ids(chunks: list[dict[str, Any]], *source_types: str) -> list[str]:
    source_type_set = set(source_types)
    result: list[str] = []
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        if chunk.get("source_type") in source_type_set and isinstance(chunk_id, str) and chunk_id:
            result.append(chunk_id)
    return result[:8]


def _legacy_context_text(
    context: object,
    snapshot_key: str,
    *field_names: str,
) -> str:
    if not isinstance(context, dict):
        return ""
    snapshot = context.get(snapshot_key, {})
    if not isinstance(snapshot, dict):
        return ""
    values: list[Any] = []
    for field_name in field_names:
        value = snapshot.get(field_name)
        if isinstance(value, list):
            values.extend(value)
        else:
            values.append(value)
    return _first_text(*values)


def _turns_count(evidence_bundle: dict[str, Any]) -> int:
    context = evidence_bundle.get("context", {})
    if not isinstance(context, dict):
        return 0
    turns_summary = context.get("turns_summary")
    if isinstance(turns_summary, list):
        return len(turns_summary)
    turns = context.get("turns")
    if isinstance(turns, list):
        return len(turns)
    return 0


def _first_text(*values: object | None) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "Fake LLM 输入证据不足"


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
