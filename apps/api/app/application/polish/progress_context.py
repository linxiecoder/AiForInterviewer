"""Progress tree context assembly for polish sessions."""

from __future__ import annotations

import json
import re
from hashlib import sha256
from typing import Any

from app.application.job_match.entities import JobMatchAnalysis
from app.application.polish.canonical_evidence import empty_retrieved_rag_chunks
from app.application.polish.entities import PolishSessionDetail, PolishSessionTurn
from app.application.polish.progress_evidence import has_sufficient_initial_evidence
from app.domain.jobs.entities import Job, JobVersion
from app.domain.resumes.entities import Resume, ResumeVersion


UNNAMED_JOB_TITLE = "未命名岗位"
UNNAMED_RESUME_TITLE = "未命名简历"
MAX_CONTEXT_TEXT_CHARS = 6000
MAX_CONTEXT_LIST_ITEMS = 50


def build_polish_progress_context(
    session_detail: PolishSessionDetail,
    *,
    job: Job | None,
    job_version: JobVersion | None,
    resume: Resume | None,
    resume_version: ResumeVersion | None,
    match_analysis: JobMatchAnalysis | None,
    weaknesses: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
    assets: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
    canonical_evidence_pack: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the backend-only semantic context for progress tree LLM calls."""

    session = session_detail.session
    job_snapshot = _build_job_snapshot(session_detail, job=job, job_version=job_version)
    resume_snapshot = _build_resume_snapshot(session_detail, resume=resume, resume_version=resume_version)
    match_context = _build_match_context(match_analysis)
    weakness_context = _build_collection_context(weaknesses)
    asset_context = _build_collection_context(assets)
    canonical_project_assets = _canonical_project_assets(canonical_evidence_pack)
    retrieved_rag_chunks = _retrieved_rag_chunks(canonical_evidence_pack)
    turns = _build_turn_context(session_detail.turns)
    context = {
        "session": {
            "session_id": session.session_id,
            "mode": "polish",
            "topic": session.topic_id,
            "subtopic": session.subtopic_id,
            "custom_topic": session.custom_topic_text_summary,
        },
        "job_snapshot": job_snapshot,
        "resume_snapshot": resume_snapshot,
        "match_context": match_context,
        "weakness_context": weakness_context,
        "asset_context": asset_context,
        "canonical_project_assets": canonical_project_assets,
        "retrieved_rag_chunks": retrieved_rag_chunks,
        "canonical_evidence_pack": _compact_canonical_evidence_pack(canonical_evidence_pack),
        "turns": turns,
    }
    context["content_digest"] = stable_digest(
        {
            "session": context["session"],
            "job_snapshot": {
                "job_id": job_snapshot["job_id"],
                "job_version_id": job_snapshot["job_version_id"],
                "content_digest": job_snapshot["content_digest"],
            },
            "resume_snapshot": {
                "resume_id": resume_snapshot["resume_id"],
                "resume_version_id": resume_snapshot["resume_version_id"],
                "content_digest": resume_snapshot["content_digest"],
            },
            "match_context": match_context,
            "canonical_project_assets": canonical_project_assets,
            "retrieved_rag_chunks": retrieved_rag_chunks,
            "source_support_level": context["canonical_evidence_pack"].get("source_support_level"),
            "canonical_evidence_digest": context["canonical_evidence_pack"].get("context_digest"),
            "turns": turns,
        }
    )
    return context


def has_sufficient_progress_context(context: dict[str, Any]) -> bool:
    return has_sufficient_initial_evidence(context)


def stable_digest(value: dict[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


def truncate_text(value: object | None, max_chars: int = MAX_CONTEXT_TEXT_CHARS) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    if not text:
        return None
    return text[:max_chars]


def clean_list(values: list[object] | tuple[object, ...], limit: int = MAX_CONTEXT_LIST_ITEMS) -> list[str]:
    result: list[str] = []
    for value in values:
        text = truncate_text(value, max_chars=640)
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def _build_job_snapshot(
    session_detail: PolishSessionDetail,
    *,
    job: Job | None,
    job_version: JobVersion | None,
) -> dict[str, Any]:
    responsibilities = clean_list(job_version.responsibilities if job_version is not None else [])
    requirements = clean_list(job_version.requirements if job_version is not None else [])
    other_notes = truncate_text(job_version.other_notes if job_version is not None else None)
    snapshot = {
        "job_id": job.job_id if job is not None else session_detail.session.job_id,
        "job_version_id": (
            job_version.job_version_id if job_version is not None else session_detail.session.job_version_id
        ),
        "title": truncate_text(job.title if job is not None else session_detail.job_title) or UNNAMED_JOB_TITLE,
        "company": job.company if job is not None else session_detail.job_company,
        "department": job.department if job is not None else None,
        "responsibilities": responsibilities,
        "requirements": requirements,
        "other_notes": other_notes,
        "application_status": job.application_status if job is not None else None,
    }
    snapshot["content_digest"] = stable_digest(
        {
            "job_id": snapshot["job_id"],
            "job_version_id": snapshot["job_version_id"],
            "responsibilities": responsibilities,
            "requirements": requirements,
            "other_notes": other_notes,
        }
    )
    return snapshot


def _build_resume_snapshot(
    session_detail: PolishSessionDetail,
    *,
    resume: Resume | None,
    resume_version: ResumeVersion | None,
) -> dict[str, Any]:
    markdown_text = resume_version.markdown_text if resume_version is not None else ""
    summary = _markdown_summary(markdown_text)
    skills = _extract_markdown_section_items(markdown_text, ("技能", "技术栈", "skills", "skill"))
    project_experiences = _extract_markdown_section_items(markdown_text, ("项目", "project"))
    work_experiences = _extract_markdown_section_items(markdown_text, ("工作", "实习", "经历", "experience"))

    snapshot = {
        "resume_id": resume.resume_id if resume is not None else session_detail.session.resume_id,
        "resume_version_id": (
            resume_version.resume_version_id
            if resume_version is not None
            else session_detail.session.resume_version_id
        ),
        "title": truncate_text(resume.title if resume is not None else session_detail.resume_title)
        or UNNAMED_RESUME_TITLE,
        "markdown_text": markdown_text,
        "summary": summary,
        "skills": skills,
        "project_experiences": project_experiences,
        "work_experiences": work_experiences,
    }
    snapshot["content_digest"] = stable_digest(
        {
            "resume_id": snapshot["resume_id"],
            "resume_version_id": snapshot["resume_version_id"],
            "markdown_text": markdown_text,
            "skills": skills,
            "project_experiences": project_experiences,
            "work_experiences": work_experiences,
        }
    )
    return snapshot


def _build_match_context(match_analysis: JobMatchAnalysis | None) -> dict[str, Any]:
    if match_analysis is None:
        return {
            "available": False,
            "analysis_id": None,
            "overall_score": None,
            "summary": None,
            "matched_points": [],
            "missing_points": [],
            "improvement_points": [],
            "interview_focus": [],
            "suggested_questions": [],
        }

    payload = match_analysis.result_payload_json or {}
    return {
        "available": True,
        "analysis_id": match_analysis.analysis_id,
        "overall_score": match_analysis.overall_score or _coerce_int(payload.get("overall_score")),
        "summary": _payload_text(payload, ("summary", "overall_summary", "conclusion")),
        "matched_points": _payload_items(
            payload,
            ("matched_points", "match_points", "matched_requirements", "strengths"),
        ),
        "missing_points": _payload_items(
            payload,
            ("missing_points", "missing_requirements", "gaps", "risks"),
        ),
        "improvement_points": _payload_items(
            payload,
            ("improvement_points", "recommendations", "improvement_suggestions"),
        ),
        "interview_focus": _payload_items(payload, ("interview_focus", "focus", "focus_points")),
        "suggested_questions": _payload_items(payload, ("suggested_questions", "questions")),
    }


def _build_collection_context(
    items: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
) -> dict[str, Any]:
    if not items:
        return {"available": False, "items": []}
    safe_items = []
    for item in items[:MAX_CONTEXT_LIST_ITEMS]:
        safe_items.append(
            {
                "title": truncate_text(item.get("title")),
                "summary": truncate_text(item.get("summary")),
                "evidence": truncate_text(item.get("evidence")),
                "severity": truncate_text(item.get("severity")),
                "content_excerpt": truncate_text(item.get("content_excerpt")),
            }
        )
    return {"available": True, "items": safe_items}


def _canonical_project_assets(canonical_evidence_pack: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(canonical_evidence_pack, dict):
        return {"available": False, "selection_policy": "rule_based_keyword_overlap_v1", "items": []}
    value = canonical_evidence_pack.get("canonical_project_assets")
    if not isinstance(value, dict):
        return {"available": False, "selection_policy": "rule_based_keyword_overlap_v1", "items": []}
    items = value.get("items") if isinstance(value.get("items"), list) else []
    safe_items: list[dict[str, Any]] = []
    for item in items[:5]:
        if not isinstance(item, dict):
            continue
        if truncate_text(item.get("status"), max_chars=80) != "asset_confirmed":
            continue
        safe_items.append(
            {
                "asset_id": truncate_text(item.get("asset_id"), max_chars=160),
                "status": truncate_text(item.get("status"), max_chars=80),
                "asset_type": truncate_text(item.get("asset_type"), max_chars=80),
                "title": truncate_text(item.get("title"), max_chars=160),
                "summary": truncate_text(item.get("summary"), max_chars=480),
                "content_excerpt": truncate_text(item.get("content_excerpt"), max_chars=480),
                "source_refs": _safe_refs(item.get("source_refs")),
                "evidence_refs": _safe_refs(item.get("evidence_refs")),
                "current_version_id": truncate_text(item.get("current_version_id"), max_chars=160),
                "priority": item.get("priority") if isinstance(item.get("priority"), int) else None,
                "relevance_reason": truncate_text(item.get("relevance_reason"), max_chars=240),
            }
        )
    return {
        "available": bool(value.get("available")) and bool(safe_items),
        "selection_policy": truncate_text(value.get("selection_policy"), max_chars=120)
        or "rule_based_keyword_overlap_v1",
        "items": safe_items,
    }


def _compact_canonical_evidence_pack(canonical_evidence_pack: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(canonical_evidence_pack, dict):
        return {}
    return {
        "schema_version": truncate_text(canonical_evidence_pack.get("schema_version"), max_chars=120),
        "owner_ref": _safe_ref(canonical_evidence_pack.get("owner_ref")),
        "session_ref": _safe_ref(canonical_evidence_pack.get("session_ref")),
        "job_snapshot_ref": _safe_ref(canonical_evidence_pack.get("job_snapshot_ref")),
        "resume_snapshot_ref": _safe_ref(canonical_evidence_pack.get("resume_snapshot_ref")),
        "progress_node_ref": truncate_text(canonical_evidence_pack.get("progress_node_ref"), max_chars=160),
        "source_support_level": truncate_text(canonical_evidence_pack.get("source_support_level"), max_chars=120),
        "context_digest": truncate_text(canonical_evidence_pack.get("context_digest"), max_chars=160),
        "retrieved_rag_chunks": _retrieved_rag_chunks(canonical_evidence_pack),
        "warnings": clean_list(tuple(canonical_evidence_pack.get("warnings") or ()), limit=10),
        "blocking_issues": clean_list(tuple(canonical_evidence_pack.get("blocking_issues") or ()), limit=10),
    }


def _retrieved_rag_chunks(canonical_evidence_pack: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(canonical_evidence_pack, dict):
        return empty_retrieved_rag_chunks()
    value = canonical_evidence_pack.get("retrieved_rag_chunks")
    if not isinstance(value, dict):
        return empty_retrieved_rag_chunks()
    items = value.get("items") if isinstance(value.get("items"), list) else []
    return {
        "available": bool(value.get("available")) and bool(items),
        "items": items if bool(value.get("available")) else [],
        "unavailable_reason": truncate_text(value.get("unavailable_reason"), max_chars=120)
        or "full_retrieval_not_enabled",
        "user_message": truncate_text(value.get("user_message"), max_chars=160)
        or "资产已保存，但本次生成未启用知识库检索。",
        "non_claim_policy": truncate_text(value.get("non_claim_policy"), max_chars=160)
        or "canonical_project_assets_are_not_retrieved_rag_chunks",
    }


def _safe_refs(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    refs: list[dict[str, str]] = []
    for item in value[:8]:
        safe_ref = _safe_ref(item)
        if safe_ref:
            refs.append(safe_ref)
    return refs


def _safe_ref(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): text
        for key, raw_value in value.items()
        if (text := truncate_text(raw_value, max_chars=160))
    }


def _build_turn_context(turns: tuple[PolishSessionTurn, ...]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, turn in enumerate(turns, start=1):
        latest_answer = turn.answers[-1] if turn.answers else None
        result.append(
            {
                "turn_index": index,
                "question_id": turn.question_id,
                "question_text": truncate_text(turn.question_text),
                "progress_node_ref": truncate_text(turn.progress_node_ref),
                "question_metadata": turn.question_metadata,
                "created_at": _isoformat(turn.question_created_at),
                "answer_text": truncate_text(latest_answer.answer_text if latest_answer is not None else None),
                "feedback_text": truncate_text(
                    latest_answer.feedback_text if latest_answer is not None else None
                ),
                "score": None,
                "answer_round": latest_answer.answer_round if latest_answer is not None else None,
                "feedback_created_at": (
                    _isoformat(latest_answer.feedback_created_at) if latest_answer is not None else None
                ),
                "answers": [
                    {
                        "answer_id": answer.answer_id,
                        "answer_text": truncate_text(answer.answer_text),
                        "feedback_id": answer.feedback_id,
                        "feedback_text": truncate_text(answer.feedback_text),
                        "score": None,
                        "answer_round": answer.answer_round,
                        "created_at": _isoformat(answer.answer_created_at),
                        "feedback_created_at": _isoformat(answer.feedback_created_at),
                    }
                    for answer in turn.answers
                ],
            }
        )
    return result


def _markdown_summary(markdown_text: str | None) -> str | None:
    if not markdown_text:
        return None
    lines = [
        re.sub(r"^#+\s*", "", line).strip("-* \t")
        for line in markdown_text.splitlines()
        if line.strip()
    ]
    return truncate_text(" ".join(line for line in lines if line), max_chars=480)


def _extract_markdown_section_items(markdown_text: str | None, keywords: tuple[str, ...]) -> list[str]:
    if not markdown_text:
        return []
    lines = markdown_text.splitlines()
    in_section = False
    collected: list[str] = []
    for line in lines:
        stripped = line.strip()
        heading_match = re.match(r"^#{1,6}\s*(.+)$", stripped)
        if heading_match:
            heading = heading_match.group(1).lower()
            in_section = any(keyword.lower() in heading for keyword in keywords)
            continue
        if in_section and stripped:
            collected.append(stripped.strip("-* \t"))
        if len(collected) >= MAX_CONTEXT_LIST_ITEMS:
            break
    if collected:
        return clean_list(collected)
    fallback_lines = [
        line.strip("-* \t")
        for line in lines
        if any(keyword.lower() in line.lower() for keyword in keywords)
    ]
    return clean_list(fallback_lines)


def _payload_text(payload: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str):
            return truncate_text(value, max_chars=1200)
        if isinstance(value, dict):
            text = _first_text(*_payload_items(value, tuple(value.keys())))
            if text:
                return text
    return None


def _payload_items(payload: dict[str, Any], keys: tuple[str, ...]) -> list[str]:
    items: list[str] = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    items.extend(clean_list(list(item.values())))
                else:
                    items.extend(clean_list([item]))
        elif isinstance(value, dict):
            items.extend(clean_list(list(value.values())))
        elif value is not None:
            items.extend(clean_list([value]))
    return clean_list(items)


def _first_text(*values: object | None) -> str:
    for value in values:
        if isinstance(value, (list, tuple)):
            nested = _first_text(*value)
            if nested:
                return nested
            continue
        text = truncate_text(value, max_chars=320)
        if text:
            return text
    return ""


def _coerce_int(value: object | None) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _isoformat(value) -> str | None:
    if value is None:
        return None
    return value.isoformat()
