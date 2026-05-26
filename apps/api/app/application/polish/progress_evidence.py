"""Deterministic evidence chunking for polish progress tree prompts."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Literal

from app.application.polish.question_generation_policy import (
    SEMANTIC_JOB_SOURCE_TYPES,
    SEMANTIC_RESUME_SOURCE_TYPES,
    SOURCE_PRIORITY_POLICY_BY_PURPOSE,
)


ProgressEvidencePurpose = Literal["initial_plan", "state_refresh", "next_question"]

MAX_CHUNK_TEXT_CHARS = 1200
DEFAULT_SELECTION_LIMITS: dict[ProgressEvidencePurpose, tuple[int, int]] = {
    "initial_plan": (18, 9000),
    "state_refresh": (12, 7000),
    "next_question": (8, 5000),
}

ORDER_BY_PURPOSE = SOURCE_PRIORITY_POLICY_BY_PURPOSE


@dataclass(frozen=True)
class ProgressEvidenceChunk:
    chunk_id: str
    source_type: str
    source_ref: dict[str, Any]
    title: str
    text: str
    keywords: tuple[str, ...]
    priority: int
    reason: str
    sequence: int

    def to_prompt_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "source_type": self.source_type,
            "source_ref": self.source_ref,
            "title": self.title,
            "text": self.text,
            "keywords": list(self.keywords),
            "priority": self.priority,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ProgressEvidenceSelection:
    selected_chunks: tuple[ProgressEvidenceChunk, ...]
    dropped_context_summary: dict[str, Any]


@dataclass(frozen=True)
class _MarkdownSection:
    title: str
    text: str


def build_progress_evidence_chunks(context: dict[str, Any]) -> list[ProgressEvidenceChunk]:
    counters: Counter[str] = Counter()
    chunks: list[ProgressEvidenceChunk] = []

    def add_chunk(
        source_type: str,
        *,
        source_ref: dict[str, Any],
        title: object | None,
        text: object | None,
        priority: int,
        reason: str,
    ) -> None:
        clean_text = _clean_text(text, max_chars=MAX_CHUNK_TEXT_CHARS)
        if not clean_text:
            return
        clean_title = _clean_text(title, max_chars=120) or _summarize_title(clean_text)
        counters[source_type] += 1
        chunks.append(
            ProgressEvidenceChunk(
                chunk_id=f"{source_type}_{counters[source_type]:03d}",
                source_type=source_type,
                source_ref={key: value for key, value in source_ref.items() if value is not None},
                title=clean_title,
                text=clean_text,
                keywords=_keywords(f"{clean_title} {clean_text}"),
                priority=priority,
                reason=reason,
                sequence=len(chunks),
            )
        )

    _add_job_chunks(context, add_chunk)
    _add_resume_chunks(context, add_chunk)
    _add_match_chunks(context, add_chunk)
    _add_turn_chunks(context, add_chunk)
    _add_collection_chunks(context, add_chunk, key="weakness_context", source_type="weakness")
    _add_collection_chunks(context, add_chunk, key="asset_context", source_type="asset_summary")
    return chunks


def has_sufficient_initial_evidence(context: dict[str, Any]) -> bool:
    chunks = build_progress_evidence_chunks(context)
    has_job = any(chunk.source_type in SEMANTIC_JOB_SOURCE_TYPES for chunk in chunks)
    has_resume = any(chunk.source_type in SEMANTIC_RESUME_SOURCE_TYPES for chunk in chunks)
    return has_job and has_resume


def select_progress_tree_evidence_chunks(
    context: dict[str, Any],
    *,
    purpose: ProgressEvidencePurpose,
    max_chunks: int | None = None,
    max_chars: int | None = None,
    existing_plan: dict[str, Any] | None = None,
    existing_state: dict[str, Any] | None = None,
    progress_node_ref: str | None = None,
    source_priority_policy: dict[str, dict[str, int]] | None = None,
) -> ProgressEvidenceSelection:
    chunks = build_progress_evidence_chunks(context)
    default_max_chunks, default_max_chars = DEFAULT_SELECTION_LIMITS[purpose]
    max_chunks = max_chunks or default_max_chunks
    max_chars = max_chars or default_max_chars
    focus_chunk_ids = _focus_chunk_ids(
        existing_plan=existing_plan,
        existing_state=existing_state,
        progress_node_ref=progress_node_ref,
    )
    order = (source_priority_policy or ORDER_BY_PURPOSE).get(purpose, ORDER_BY_PURPOSE[purpose])
    ranked_chunks = sorted(
        chunks,
        key=lambda chunk: (
            0 if chunk.chunk_id in focus_chunk_ids else 1,
            order.get(chunk.source_type, 99),
            -chunk.priority,
            -_turn_index(chunk) if purpose in {"state_refresh", "next_question"} else chunk.sequence,
            chunk.sequence,
        ),
    )

    selected: list[ProgressEvidenceChunk] = []
    selected_chars = 0
    if purpose == "initial_plan":
        for source_type in (
            "job_requirement",
            "match_gap",
            "match_focus",
            "resume_project",
            "resume_skill",
        ):
            selected_ids = {item.chunk_id for item in selected}
            candidate = next(
                (
                    chunk
                    for chunk in ranked_chunks
                    if chunk.source_type == source_type and chunk.chunk_id not in selected_ids
                ),
                None,
            )
            if candidate is None:
                continue
            chunk_chars = len(candidate.text)
            if len(selected) < max_chunks and selected_chars + chunk_chars <= max_chars:
                selected.append(candidate)
                selected_chars += chunk_chars

    selected_ids = {chunk.chunk_id for chunk in selected}
    for chunk in ranked_chunks:
        if chunk.chunk_id in selected_ids:
            continue
        chunk_chars = len(chunk.text)
        if len(selected) >= max_chunks or selected_chars + chunk_chars > max_chars:
            continue
        selected.append(chunk)
        selected_ids.add(chunk.chunk_id)
        selected_chars += chunk_chars

    dropped = [chunk for chunk in chunks if chunk.chunk_id not in selected_ids]
    dropped_source_types = sorted({chunk.source_type for chunk in dropped})
    truncated_reasons = []
    if len(chunks) > max_chunks:
        truncated_reasons.append("max_chunks")
    if sum(len(chunk.text) for chunk in chunks) > max_chars:
        truncated_reasons.append("max_chars")
    return ProgressEvidenceSelection(
        selected_chunks=tuple(selected),
        dropped_context_summary={
            "dropped_chunks_count": len(dropped),
            "dropped_source_types": dropped_source_types,
            "truncated_reason": "+".join(truncated_reasons) if truncated_reasons else "none",
        },
    )


def build_progress_prompt_context(
    context: dict[str, Any],
    *,
    purpose: ProgressEvidencePurpose,
    existing_plan: dict[str, Any] | None = None,
    existing_state: dict[str, Any] | None = None,
    progress_node_ref: str | None = None,
    max_chunks: int | None = None,
    max_chars: int | None = None,
    source_priority_policy: dict[str, dict[str, int]] | None = None,
) -> dict[str, Any]:
    selection = select_progress_tree_evidence_chunks(
        context,
        purpose=purpose,
        max_chunks=max_chunks,
        max_chars=max_chars,
        existing_plan=existing_plan,
        existing_state=existing_state,
        progress_node_ref=progress_node_ref,
        source_priority_policy=source_priority_policy,
    )
    return {
        "context_metadata": _context_metadata(context),
        "selected_evidence_chunks": [chunk.to_prompt_dict() for chunk in selection.selected_chunks],
        "dropped_context_summary": selection.dropped_context_summary,
        "match_context_summary": _match_context_summary(context.get("match_context", {})),
        "turns_summary": _turns_summary(context.get("turns", [])),
    }


def _add_job_chunks(context: dict[str, Any], add_chunk) -> None:
    job = context.get("job_snapshot", {})
    source_ref = {
        "job_id": job.get("job_id"),
        "job_version_id": job.get("job_version_id"),
    }
    for item in _string_list(job.get("requirements")):
        add_chunk(
            "job_requirement",
            source_ref=source_ref,
            title=item,
            text=item,
            priority=100,
            reason="岗位硬性要求，优先用于生成能力节点",
        )
    for item in _string_list(job.get("responsibilities")):
        add_chunk(
            "job_responsibility",
            source_ref=source_ref,
            title=item,
            text=item,
            priority=82,
            reason="岗位职责，补充能力场景边界",
        )
    for paragraph in _split_paragraphs(job.get("other_notes")):
        add_chunk(
            "job_other_note",
            source_ref=source_ref,
            title=paragraph,
            text=paragraph,
            priority=50,
            reason="岗位补充说明",
        )


def _add_resume_chunks(context: dict[str, Any], add_chunk) -> None:
    resume = context.get("resume_snapshot", {})
    source_ref = {
        "resume_id": resume.get("resume_id"),
        "resume_version_id": resume.get("resume_version_id"),
    }
    markdown_text = _clean_text(resume.get("markdown_text"), max_chars=None, preserve_lines=True)
    emitted: set[tuple[str, str]] = set()

    if markdown_text:
        for section in _split_markdown_sections(markdown_text):
            source_type = _resume_source_type(section.title)
            priority = _resume_priority(source_type)
            reason = _resume_reason(source_type)
            for title, text in _resume_section_items(section, source_type):
                key = (source_type, text)
                if key in emitted:
                    continue
                emitted.add(key)
                add_chunk(
                    source_type,
                    source_ref=source_ref,
                    title=title,
                    text=text,
                    priority=priority,
                    reason=reason,
                )

    fallback_fields = (
        ("resume_project", "project_experiences"),
        ("resume_skill", "skills"),
        ("resume_work_experience", "work_experiences"),
        ("resume_summary", "summary"),
    )
    for source_type, field_name in fallback_fields:
        for item in _string_list(resume.get(field_name)):
            key = (source_type, item)
            if key in emitted:
                continue
            emitted.add(key)
            add_chunk(
                source_type,
                source_ref=source_ref,
                title=item,
                text=item,
                priority=_resume_priority(source_type),
                reason=_resume_reason(source_type),
            )


def _add_match_chunks(context: dict[str, Any], add_chunk) -> None:
    match_context = context.get("match_context", {})
    if not match_context.get("available"):
        return
    source_ref = {
        "analysis_id": match_context.get("analysis_id"),
        "overall_score": match_context.get("overall_score"),
    }
    for item in _string_list(match_context.get("missing_points")):
        add_chunk(
            "match_gap",
            source_ref=source_ref,
            title=item,
            text=item,
            priority=99,
            reason="岗位匹配缺口，适合进入优先打磨节点",
        )
    for item in _string_list(match_context.get("interview_focus")):
        add_chunk(
            "match_focus",
            source_ref=source_ref,
            title=item,
            text=item,
            priority=98,
            reason="面试重点方向",
        )
    for item in _string_list(match_context.get("suggested_questions")):
        add_chunk(
            "match_suggested_question",
            source_ref=source_ref,
            title=item,
            text=item,
            priority=72,
            reason="岗位匹配分析建议追问",
        )


def _add_turn_chunks(context: dict[str, Any], add_chunk) -> None:
    turns = context.get("turns") or []
    total = len(turns)
    for index, turn in enumerate(turns, start=1):
        if not isinstance(turn, dict):
            continue
        source_ref = {
            "turn_index": turn.get("turn_index") or index,
            "question_id": turn.get("question_id"),
        }
        recency_boost = max(0, index - max(0, total - 5))
        add_chunk(
            "turn_question",
            source_ref=source_ref,
            title=f"第 {source_ref['turn_index']} 轮问题",
            text=turn.get("question_text"),
            priority=58 + recency_boost,
            reason="历史问题，用于避免重复和保持追问连续性",
        )
        add_chunk(
            "turn_answer",
            source_ref=source_ref,
            title=f"第 {source_ref['turn_index']} 轮回答",
            text=turn.get("answer_text"),
            priority=60 + recency_boost,
            reason="历史回答摘要，用于刷新掌握状态",
        )
        add_chunk(
            "turn_feedback",
            source_ref=source_ref,
            title=f"第 {source_ref['turn_index']} 轮反馈",
            text=turn.get("feedback_text"),
            priority=94 + recency_boost,
            reason="历史反馈和缺口，优先用于状态刷新",
        )


def _add_collection_chunks(context: dict[str, Any], add_chunk, *, key: str, source_type: str) -> None:
    collection = context.get(key, {})
    if not collection.get("available"):
        return
    for index, item in enumerate(collection.get("items", []), start=1):
        if not isinstance(item, dict):
            continue
        text = _first_text(item.get("summary"), item.get("evidence"), item.get("content_excerpt"))
        add_chunk(
            source_type,
            source_ref={"item_index": index},
            title=item.get("title") or text,
            text=text,
            priority=68 if source_type == "weakness" else 48,
            reason="薄弱项证据" if source_type == "weakness" else "资产摘要证据",
        )


def _split_markdown_sections(markdown_text: str) -> list[_MarkdownSection]:
    sections: list[_MarkdownSection] = []
    current_title = "summary"
    current_lines: list[str] = []
    for line in markdown_text.splitlines():
        heading_match = re.match(r"^#{1,6}\s*(.+)$", line.strip())
        if heading_match:
            _append_section(sections, current_title, current_lines)
            current_title = heading_match.group(1).strip()
            current_lines = []
            continue
        current_lines.append(line)
    _append_section(sections, current_title, current_lines)
    return sections


def _append_section(sections: list[_MarkdownSection], title: str, lines: list[str]) -> None:
    text = "\n".join(line.rstrip() for line in lines).strip()
    if text:
        sections.append(_MarkdownSection(title=title, text=text))


def _resume_section_items(section: _MarkdownSection, source_type: str) -> list[tuple[str, str]]:
    if source_type in {"resume_project", "resume_work_experience"}:
        paragraphs = _split_paragraphs(section.text)
        if len(paragraphs) > 1:
            return [(_summarize_title(paragraph), paragraph) for paragraph in paragraphs]
    return [(section.title, section.text)]


def _resume_source_type(title: str) -> str:
    normalized = title.lower()
    if any(keyword in normalized for keyword in ("项目", "project", "作品", "开源", "竞赛")):
        return "resume_project"
    if any(keyword in normalized for keyword in ("技能", "技术栈", "skills", "skill", "stack")):
        return "resume_skill"
    if any(keyword in normalized for keyword in ("工作", "实习", "经历", "experience", "employment")):
        return "resume_work_experience"
    if any(keyword in normalized for keyword in ("教育", "education", "学历")):
        return "resume_education"
    return "resume_summary"


def _resume_priority(source_type: str) -> int:
    return {
        "resume_project": 92,
        "resume_skill": 88,
        "resume_work_experience": 78,
        "resume_education": 42,
        "resume_summary": 45,
    }.get(source_type, 45)


def _resume_reason(source_type: str) -> str:
    return {
        "resume_project": "简历项目经历，优先用于生成技术深挖节点",
        "resume_skill": "简历技能栈，用于匹配岗位技术要求",
        "resume_work_experience": "工作经历，用于生成业务抽象和协作推进节点",
        "resume_education": "教育经历，作为辅助背景",
        "resume_summary": "简历摘要，作为低优先级背景",
    }.get(source_type, "简历证据")


def _context_metadata(context: dict[str, Any]) -> dict[str, Any]:
    session = context.get("session", {})
    job = context.get("job_snapshot", {})
    resume = context.get("resume_snapshot", {})
    return {
        "session_id": session.get("session_id"),
        "mode": session.get("mode"),
        "topic": session.get("topic"),
        "subtopic": session.get("subtopic"),
        "custom_target": session.get("custom_topic"),
        "job_id": job.get("job_id"),
        "job_version_id": job.get("job_version_id"),
        "job_title": job.get("title"),
        "job_company": job.get("company"),
        "resume_id": resume.get("resume_id"),
        "resume_version_id": resume.get("resume_version_id"),
        "resume_title": resume.get("title"),
        "content_digest": context.get("content_digest"),
    }


def _match_context_summary(match_context: dict[str, Any]) -> dict[str, Any]:
    return {
        "available": bool(match_context.get("available")),
        "analysis_id": match_context.get("analysis_id"),
        "overall_score": match_context.get("overall_score"),
        "summary": _clean_text(match_context.get("summary"), max_chars=480),
        "missing_points_count": len(_string_list(match_context.get("missing_points"))),
        "interview_focus_count": len(_string_list(match_context.get("interview_focus"))),
        "suggested_questions_count": len(_string_list(match_context.get("suggested_questions"))),
    }


def _turns_summary(turns: object) -> list[dict[str, Any]]:
    if not isinstance(turns, list):
        return []
    result: list[dict[str, Any]] = []
    for index, turn in enumerate(turns[-5:], start=max(1, len(turns) - 4)):
        if not isinstance(turn, dict):
            continue
        result.append(
            {
                "turn_index": turn.get("turn_index") or index,
                "question_summary": _clean_text(turn.get("question_text"), max_chars=240),
                "answer_summary": _clean_text(turn.get("answer_text"), max_chars=240),
                "feedback_summary": _clean_text(turn.get("feedback_text"), max_chars=240),
            }
        )
    return result


def _focus_chunk_ids(
    *,
    existing_plan: dict[str, Any] | None,
    existing_state: dict[str, Any] | None,
    progress_node_ref: str | None,
) -> set[str]:
    if not existing_plan:
        return set()
    target_ref = progress_node_ref
    if not target_ref and existing_state:
        current_priority = existing_state.get("current_priority")
        if isinstance(current_priority, dict):
            target_ref = current_priority.get("progress_node_ref")
    if not target_ref:
        return set()
    node = _find_node(existing_plan.get("nodes", []), target_ref)
    if not node:
        return set()
    return set(_string_list(node.get("evidence_chunk_ids"), limit=20))


def _find_node(nodes: object, target_ref: str) -> dict[str, Any] | None:
    if not isinstance(nodes, list):
        return None
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if node.get("progress_node_ref") == target_ref:
            return node
        child = _find_node(node.get("children", []), target_ref)
        if child is not None:
            return child
    return None


def _turn_index(chunk: ProgressEvidenceChunk) -> int:
    value = chunk.source_ref.get("turn_index")
    return value if isinstance(value, int) else 0


def _split_paragraphs(value: object | None) -> list[str]:
    text = _clean_text(value, max_chars=None, preserve_lines=True)
    if not text:
        return []
    parts = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    return parts or [text]


def _string_list(value: object, limit: int = 20) -> list[str]:
    if isinstance(value, (list, tuple)):
        raw_items = value
    elif value is None:
        raw_items = []
    else:
        raw_items = [value]
    result: list[str] = []
    for item in raw_items:
        text = _clean_text(item, max_chars=640)
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def _first_text(*values: object | None) -> str | None:
    for value in values:
        text = _clean_text(value, max_chars=640)
        if text:
            return text
    return None


def _clean_text(
    value: object | None,
    *,
    max_chars: int | None = MAX_CHUNK_TEXT_CHARS,
    preserve_lines: bool = False,
) -> str | None:
    if value is None:
        return None
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    if preserve_lines:
        text = "\n".join(" ".join(line.split()) for line in text.splitlines()).strip()
    else:
        text = " ".join(text.split())
    if not text:
        return None
    return text[:max_chars] if max_chars is not None else text


def _summarize_title(text: str) -> str:
    title = _clean_text(text, max_chars=80) or "未命名证据"
    return title


def _keywords(text: str) -> tuple[str, ...]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_+#.-]{1,}|[\u4e00-\u9fff]{2,}", text)
    result: list[str] = []
    for token in tokens:
        normalized = token.lower()
        if normalized not in result:
            result.append(normalized)
        if len(result) >= 12:
            break
    return tuple(result)
