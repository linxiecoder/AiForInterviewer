"""Deterministic evidence chunking for polish progress tree prompts."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Literal

from markdown_it import MarkdownIt
from markdown_it.token import Token

from app.application.llm.agent_io import AgentEvidenceItem
from app.application.polish.question_generation_policy import (
    SEMANTIC_JOB_SOURCE_TYPES,
    SEMANTIC_RESUME_SOURCE_TYPES,
    SOURCE_PRIORITY_POLICY_BY_PURPOSE,
)
from app.infrastructure.observability.logging import LogUtil



ProgressEvidencePurpose = Literal["initial_plan", "state_refresh", "next_question"]

MAX_CHUNK_TEXT_CHARS = 1200
ALLOWED_EVIDENCE_REF_EXCERPT_CHARS = 200
DEFAULT_SELECTION_LIMITS: dict[ProgressEvidencePurpose, tuple[int, int]] = {
    "initial_plan": (18, 9000),
    "state_refresh": (12, 7000),
    "next_question": (8, 5000),
}

ORDER_BY_PURPOSE = SOURCE_PRIORITY_POLICY_BY_PURPOSE
_MARKDOWN_PARSER = MarkdownIt("commonmark", {"html": False})
_RESUME_CORE_CONTRIBUTION_HEADINGS = {
    "核心贡献",
    "主要贡献",
    "关键贡献",
    "项目贡献",
    "核心工作",
    "主要工作",
}
_RESUME_STRUCTURE_FIELD_HEADINGS = {
    "项目背景",
    "项目简介",
    "项目描述",
    "项目职责",
    "职责",
    "工作职责",
    "工作业绩",
    "工作内容",
    *_RESUME_CORE_CONTRIBUTION_HEADINGS,
}
_RESUME_CORE_CONTRIBUTION_HEADING_RE = "|".join(
    re.escape(label) for label in sorted(_RESUME_CORE_CONTRIBUTION_HEADINGS, key=len, reverse=True)
)
_RESUME_STRUCTURE_FIELD_HEADING_RE = "|".join(
    re.escape(label) for label in sorted(_RESUME_STRUCTURE_FIELD_HEADINGS, key=len, reverse=True)
)


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

    def to_agent_evidence_item(self) -> AgentEvidenceItem:
        return AgentEvidenceItem(
            ref=self.chunk_id,
            source_type=self.source_type,
            title=self.title,
            excerpt=self.text,
            source_ref=self.source_ref,
            priority=self.priority,
            reason=self.reason,
            keywords=self.keywords,
        )

    def to_prompt_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "ref": self.chunk_id,
            "source_type": self.source_type,
            "source_ref": self.source_ref,
            "title": self.title,
            "text": self.text,
            "excerpt": self.text,
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
    level: int = 0
    parent_title: str | None = None
    breadcrumb: tuple[str, ...] = ()
    line_range: tuple[int, int] | None = None


@dataclass(frozen=True)
class _ResumeSectionItem:
    source_type: str
    title: str
    text: str
    source_ref: dict[str, Any]


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
    ) -> ProgressEvidenceChunk | None:
        clean_text = _clean_text(text, max_chars=MAX_CHUNK_TEXT_CHARS)
        if not clean_text:
            return None
        clean_title = _clean_text(title, max_chars=120) or _summarize_title(clean_text)
        counters[source_type] += 1
        chunk = ProgressEvidenceChunk(
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
        chunks.append(chunk)
        return chunk

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
    selected_ids: set[str] = set()

    def add_candidate(chunk: ProgressEvidenceChunk) -> bool:
        nonlocal selected_chars
        if chunk.chunk_id in selected_ids:
            return False
        chunk_chars = len(chunk.text)
        if len(selected) >= max_chunks or selected_chars + chunk_chars > max_chars:
            return False
        selected.append(chunk)
        selected_ids.add(chunk.chunk_id)
        selected_chars += chunk_chars
        return True

    if purpose == "initial_plan":
        selected_projects: list[ProgressEvidenceChunk] = []
        project_chunks = [chunk for chunk in chunks if chunk.source_type == "resume_project"]
        contribution_chunks = [
            chunk for chunk in chunks if chunk.source_type == "resume_project_contribution"
        ]
        contributions_by_project: dict[tuple[str, str], list[ProgressEvidenceChunk]] = {}
        for contribution in contribution_chunks:
            contributions_by_project.setdefault(_project_key(contribution), []).append(contribution)

        for project in project_chunks[:3]:
            if add_candidate(project):
                selected_projects.append(project)

        for project in selected_projects:
            associated_contributions = contributions_by_project.get(_project_key(project), [])
            for contribution in associated_contributions[:1]:
                add_candidate(contribution)

        for source_type in (
            "job_requirement",
            "match_gap",
            "match_focus",
            "resume_skill",
        ):
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
            add_candidate(candidate)

        for project in selected_projects:
            associated_contributions = contributions_by_project.get(_project_key(project), [])
            selected_contribution_count = sum(
                1
                for contribution in associated_contributions
                if contribution.chunk_id in selected_ids
            )
            for contribution in associated_contributions:
                if selected_contribution_count >= 4:
                    break
                if add_candidate(contribution):
                    selected_contribution_count += 1

    for chunk in ranked_chunks:
        add_candidate(chunk)

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


def _project_key(chunk: ProgressEvidenceChunk) -> tuple[str, str]:
    project_title = str(chunk.source_ref.get("project_title") or chunk.title or "")
    project_sequence = str(chunk.source_ref.get("project_sequence") or "")
    return (project_sequence, project_title)


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
    allowed_evidence_refs = _allowed_evidence_refs_for_prompt(selection.selected_chunks)
    result = {
        "context_metadata": _context_metadata(context),
        "selected_evidence_chunks": [chunk.to_prompt_dict() for chunk in selection.selected_chunks],
        "allowed_evidence_refs": allowed_evidence_refs,
        "dropped_context_summary": selection.dropped_context_summary,
        "match_context_summary": _match_context_summary(context.get("match_context", {})),
        "turns_summary": _turns_summary(context.get("turns", [])),
    }
    LogUtil._log_resume_evidence_debug("allowed_evidence_refs", allowed_evidence_refs)
    return result


def _allowed_evidence_refs_for_prompt(chunks: tuple[ProgressEvidenceChunk, ...]) -> list[dict[str, str]]:
    allowed_refs: list[dict[str, str]] = []
    for chunk in chunks:
        item = chunk.to_agent_evidence_item()
        allowed_refs.append(
            {
                "ref": item.ref,
                "source_type": item.source_type,
                "title": _clean_text(item.title, max_chars=120) or "",
                "excerpt": _clean_text(item.excerpt, max_chars=ALLOWED_EVIDENCE_REF_EXCERPT_CHARS) or "",
            }
        )
    return allowed_refs


def _debug_progress_evidence_enabled(context: dict[str, Any]) -> bool:
    return bool(context.get("debug_progress_evidence") or context.get("debug_resume_chunks"))


def _debug_flatten_markdown(markdown_text: str) -> str:
    return " ".join(markdown_text.replace("\r\n", "\n").replace("\r", "\n").split())


def _debug_resume_chunk(
    chunk: ProgressEvidenceChunk | None,
    *,
    section: _MarkdownSection | None,
) -> dict[str, Any]:
    if chunk is None:
        return {}
    return {
        "ref": chunk.chunk_id,
        "source_type": chunk.source_type,
        "title": chunk.title,
        "excerpt": chunk.text,
        "source_ref": chunk.source_ref,
        "section_title": section.title if section else None,
        "line_range": section.line_range if section else None,
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
    raw_markdown = _clean_text(resume.get("markdown_text"), max_chars=None, preserve_lines=True)
    rehydrated_text = _rehydrate_flattened_resume_markdown(raw_markdown) if raw_markdown else None
    markdown_text = _normalize_resume_project_containers(rehydrated_text) if rehydrated_text else None
    emitted: set[tuple[str, str, str, str, str]] = set()
    markdown_source_types: set[str] = set()
    project_sequence = 0
    debug_enabled = _debug_progress_evidence_enabled(context)
    debug_project_chunks: list[dict[str, Any]] = []
    debug_contribution_chunks: list[dict[str, Any]] = []

    if markdown_text:
        sections = _split_markdown_sections(markdown_text)
        LogUtil._log_resume_evidence_debug(context, stage="raw_markdown", value=markdown_text)
        for section in sections:
            source_type = _infer_resume_section_type(section)
            if source_type == "section_header":
                continue
            if source_type == "resume_project":
                section_items = _chunk_project_section(section, project_sequence=project_sequence + 1)
                if not section_items:
                    continue
                project_sequence = max(
                    project_sequence,
                    *(
                        int(item.source_ref["project_sequence"])
                        for item in section_items
                        if isinstance(item.source_ref.get("project_sequence"), int)
                    ),
                )
            else:
                section_items = _chunk_resume_section(section, source_type)

            for item in section_items:
                key = _resume_dedupe_key(section, item)
                if key in emitted:
                    continue
                emitted.add(key)
                markdown_source_types.add(item.source_type)
                created_chunk = add_chunk(
                    item.source_type,
                    source_ref={**source_ref, **item.source_ref},
                    title=item.title,
                    text=item.text,
                    priority=_resume_priority(item.source_type),
                    reason=_resume_reason(item.source_type),
                )
                if debug_enabled and item.source_type == "resume_project":
                    debug_project_chunks.append(_debug_resume_chunk(created_chunk, section=section))
                elif debug_enabled and item.source_type == "resume_project_contribution":
                    debug_contribution_chunks.append(_debug_resume_chunk(created_chunk, section=section))
    elif debug_enabled:
        LogUtil._log_resume_evidence_debug(context, stage="raw_markdown", value=_debug_flatten_markdown(raw_markdown or ""))

    fallback_fields = (
        ("resume_project", "project_experiences"),
        ("resume_skill", "skills"),
        ("resume_work_experience", "work_experiences"),
        ("resume_summary", "summary"),
    )
    for source_type, field_name in fallback_fields:
        if source_type in markdown_source_types:
            continue
        for item in _string_list(resume.get(field_name)):
            key = (source_type, "fallback", "", "", _stable_text_hash(item))
            if key in emitted:
                continue
            emitted.add(key)
            created_chunk = add_chunk(
                source_type,
                source_ref=source_ref,
                title=item,
                text=item,
                priority=_resume_priority(source_type),
                reason=_resume_reason(source_type),
            )
            if debug_enabled and source_type == "resume_project":
                debug_project_chunks.append(_debug_resume_chunk(created_chunk, section=None))

    if debug_enabled:
        LogUtil._log_resume_evidence_debug(context, stage="project_chunks", value=debug_project_chunks)
        LogUtil._log_resume_evidence_debug(context, stage="contribution_chunks", value=debug_contribution_chunks)


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


def _normalize_resume_markdown(markdown_text: str) -> str:
    markdown_text = _rehydrate_flattened_resume_markdown(markdown_text)
    return _normalize_resume_project_containers(markdown_text)


def _rehydrate_flattened_resume_markdown(markdown_text: str) -> str:
    text = markdown_text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"([^\n])\s+(?=#{1,6}\s+\S)", r"\1\n", text)
    text = re.sub(r"([^\n])\s+(?=:{3,}\s*start\b)", r"\1\n", text, flags=re.IGNORECASE)
    text = re.sub(r"(:{3,}\s*end\s*:*)\s+(?=\S)", r"\1\n", text, flags=re.IGNORECASE)
    text = re.sub(
        rf"([^\n])\s+(?=\*\*(?:{_RESUME_STRUCTURE_FIELD_HEADING_RE})\*\*\s*[：:])",
        r"\1\n",
        text,
    )
    text = re.sub(
        rf"(\*\*(?:{_RESUME_CORE_CONTRIBUTION_HEADING_RE})\*\*\s*[：:]?)\s+(?=-\s+\S)",
        r"\1\n",
        text,
    )
    text = re.sub(
        r"([^\n])\s+(?=-\s+\*\*[^*\n]{1,80}\*\*\s*[：:])",
        r"\1\n",
        text,
    )
    return text


def _normalize_resume_project_containers(markdown_text: str) -> str:
    lines: list[str] = []
    for raw_line in markdown_text.splitlines():
        parsed_header = _parse_resume_project_container_header(raw_line)
        if parsed_header is not None:
            title, company, role = parsed_header
            heading_parts = [part for part in (title, company, role) if part]
            lines.append(f"### {' @ '.join(heading_parts)}")
            continue
        if re.fullmatch(r"\s*:{3,}\s*(?:end|stop)?\s*:*\s*", raw_line, flags=re.IGNORECASE):
            continue
        lines.append(raw_line.rstrip())
    return "\n".join(lines)


def _parse_resume_project_container_header(raw_line: str) -> tuple[str, str | None, str | None] | None:
    match = re.match(
        r"^\s*:{3,}\s*start\b(?P<body>.*?)\s*:{3,}\s*end\s*:*\s*$",
        raw_line,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    raw_parts = [part.strip() for part in re.split(r"\s*:{3,}\s*", match.group("body")) if part.strip()]
    parts = [_clean_resume_container_part(part) for part in raw_parts]
    parts = [part for part in parts if part]
    if not parts:
        return None
    title = parts[0]
    company = parts[1] if len(parts) >= 2 else None
    role = parts[2] if len(parts) >= 3 else None
    return title, company, role


def _clean_resume_container_part(value: str) -> str:
    return _clean_text(_strip_markdown_title_markup(value), max_chars=120) or ""


def _split_markdown_sections(markdown_text: str) -> list[_MarkdownSection]:
    source_lines = markdown_text.splitlines()
    heading_events = _markdown_heading_events(_MARKDOWN_PARSER.parse(markdown_text))
    if not heading_events:
        summary_text = "\n".join(line.rstrip() for line in source_lines).strip()
        return [
            _MarkdownSection(
                title="summary",
                text=summary_text,
                level=0,
                parent_title=None,
                breadcrumb=("summary",),
                line_range=(0, len(source_lines)),
            )
        ] if summary_text else []

    sections: list[_MarkdownSection] = []
    preamble_text = "\n".join(source_lines[: heading_events[0]["start_line"]]).strip()
    if preamble_text:
        sections.append(
            _MarkdownSection(
                title="summary",
                text=preamble_text,
                level=0,
                parent_title=None,
                breadcrumb=("summary",),
                line_range=(0, heading_events[0]["start_line"]),
            )
        )

    heading_stack: list[tuple[int, str]] = []
    for index, event in enumerate(heading_events):
        level = event["level"]
        while heading_stack and heading_stack[-1][0] >= level:
            heading_stack.pop()
        parent_title = heading_stack[-1][1] if heading_stack else None
        breadcrumb = tuple(title for _, title in heading_stack) + (event["title"],)
        section_end = len(source_lines)
        for next_event in heading_events[index + 1 :]:
            if next_event["level"] <= level:
                section_end = next_event["start_line"]
                break
        section_text = "\n".join(line.rstrip() for line in source_lines[event["end_line"] : section_end]).strip()
        sections.append(
            _MarkdownSection(
                title=event["title"],
                text=section_text,
                level=level,
                parent_title=parent_title,
                breadcrumb=breadcrumb,
                line_range=(event["end_line"], section_end),
            )
        )
        heading_stack.append((level, event["title"]))
    return sections


def _markdown_heading_events(tokens: list[Token]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for index, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        inline = tokens[index + 1] if index + 1 < len(tokens) and tokens[index + 1].type == "inline" else None
        line_map = token.map or (inline.map if inline else None)
        if not line_map:
            continue
        title = _clean_text(inline.content if inline else "", max_chars=160) or ""
        if not title:
            continue
        events.append(
            {
                "level": int(token.tag[1]),
                "title": title,
                "start_line": int(line_map[0]),
                "end_line": int(line_map[1]),
            }
        )
    return events


def _infer_resume_section_type(section: _MarkdownSection) -> str:
    if _is_project_item_section(section):
        return "resume_project"
    if _is_work_experience_item_section(section):
        return "resume_work_experience"
    if _is_project_detail_subsection(section):
        return "section_header"
    if _is_project_collection_title(section.title):
        return "section_header" if _section_has_child_heading(section) or not section.text else "resume_project"
    if _is_work_collection_title(section.title):
        return "section_header" if _section_has_child_heading(section) or not section.text else "resume_work_experience"
    if _section_has_child_heading(section) and section.level <= 2:
        return "section_header"
    if _breadcrumb_contains(section.breadcrumb, ("技能", "技术栈", "skills", "skill", "stack")):
        return "resume_skill"
    if _breadcrumb_contains(section.breadcrumb, ("教育", "education", "学历")):
        return "resume_education"
    return "resume_summary"


def _chunk_resume_section(section: _MarkdownSection, source_type: str) -> list[_ResumeSectionItem]:
    if not section.text:
        return []
    if source_type == "resume_work_experience":
        return _chunk_work_experience_section(section)
    if source_type == "resume_skill":
        return _chunk_skill_section(section)
    if source_type == "resume_summary":
        return _chunk_summary_section(section)
    if source_type == "resume_education":
        return [_ResumeSectionItem(source_type=source_type, title=section.title, text=section.text, source_ref={})]
    return []


def _chunk_project_section(section: _MarkdownSection, *, project_sequence: int) -> list[_ResumeSectionItem]:
    heading_parts = _resume_project_heading_parts(section)
    if heading_parts is None:
        block_items = _resume_project_block_items(section.text, first_project_sequence=project_sequence)
        if block_items:
            return block_items
        return _chunk_legacy_project_paragraphs(section, first_project_sequence=project_sequence)

    project_title, company, role = heading_parts
    source_ref: dict[str, Any] = {
        "project_title": project_title,
        "project_sequence": project_sequence,
    }
    if company:
        source_ref["company"] = company
    if role:
        source_ref["role"] = role
    items = [
        _ResumeSectionItem(
            source_type="resume_project",
            title=project_title,
            text=section.text,
            source_ref=source_ref,
        )
    ]
    for contribution_sequence, (contribution_title, contribution_text) in enumerate(
        _extract_project_contributions(section.text),
        start=1,
    ):
        items.append(
            _ResumeSectionItem(
                source_type="resume_project_contribution",
                title=contribution_title,
                text=contribution_text,
                source_ref={
                    **source_ref,
                    "contribution_sequence": contribution_sequence,
                },
            )
        )
    return items


def _chunk_work_experience_section(section: _MarkdownSection) -> list[_ResumeSectionItem]:
    title, company, role = _resume_heading_parts(section.title)
    source_ref: dict[str, Any] = {}
    if company:
        source_ref["company"] = company
    if role:
        source_ref["role"] = role
    if title and _looks_like_duration(title):
        source_ref["duration"] = title
    chunk_title = " @ ".join(part for part in (company, role) if part) or section.title
    return [
        _ResumeSectionItem(
            source_type="resume_work_experience",
            title=chunk_title,
            text=section.text,
            source_ref=source_ref,
        )
    ]


def _chunk_skill_section(section: _MarkdownSection) -> list[_ResumeSectionItem]:
    return [_ResumeSectionItem(source_type="resume_skill", title=section.title, text=section.text, source_ref={})]


def _chunk_summary_section(section: _MarkdownSection) -> list[_ResumeSectionItem]:
    return [_ResumeSectionItem(source_type="resume_summary", title=section.title, text=section.text, source_ref={})]


def _resume_project_heading_parts(section: _MarkdownSection) -> tuple[str, str | None, str | None] | None:
    project_title, company, role = _resume_heading_parts(section.title)
    if (
        not project_title
        or _is_project_structure_title(project_title)
        or _looks_like_company_only(project_title)
        or _looks_like_contribution_title(project_title)
    ):
        return None
    return project_title, company, role


def _resume_heading_parts(title: str) -> tuple[str, str | None, str | None]:
    raw_parts = [part.strip() for part in title.split(" @ ")]
    parts = [_clean_text(_strip_markdown_title_markup(part), max_chars=120) or "" for part in raw_parts]
    parts = [part for part in parts if part]
    if not parts:
        return "", None, None
    return parts[0], parts[1] if len(parts) >= 2 else None, parts[2] if len(parts) >= 3 else None


def _resume_project_block_items(text: str, *, first_project_sequence: int = 1) -> list[_ResumeSectionItem]:
    blocks = _split_project_blocks(text)
    if not blocks:
        return []

    items: list[_ResumeSectionItem] = []
    seen: set[tuple[str, str, str]] = set()
    for project_sequence, (title, block_text) in enumerate(blocks, start=first_project_sequence):
        project_ref = {"project_title": title, "project_sequence": project_sequence}
        candidates = [
            _ResumeSectionItem(
                source_type="resume_project",
                title=title,
                text=block_text,
                source_ref=project_ref,
            )
        ]
        candidates.extend(
            _ResumeSectionItem(
                source_type="resume_project_contribution",
                title=contribution_title,
                text=contribution_text,
                source_ref={**project_ref, "contribution_sequence": contribution_sequence},
            )
            for contribution_sequence, (contribution_title, contribution_text) in enumerate(
                _extract_project_contributions(block_text),
                start=1,
            )
        )
        for candidate in candidates:
            key = (candidate.source_type, candidate.title, candidate.text)
            if key in seen:
                continue
            seen.add(key)
            items.append(candidate)
    return items


def _chunk_legacy_project_paragraphs(
    section: _MarkdownSection,
    *,
    first_project_sequence: int,
) -> list[_ResumeSectionItem]:
    if not _is_project_collection_title(section.title):
        return []
    items: list[_ResumeSectionItem] = []
    for offset, paragraph in enumerate(_split_paragraphs(section.text)):
        project_sequence = first_project_sequence + offset
        items.append(
            _ResumeSectionItem(
                source_type="resume_project",
                title=_summarize_title(paragraph),
                text=paragraph,
                source_ref={
                    "project_title": _summarize_title(paragraph),
                    "project_sequence": project_sequence,
                },
            )
        )
    return items


def _split_project_blocks(text: str) -> list[tuple[str, str]]:
    clean_text = _clean_text(text, max_chars=None, preserve_lines=True)
    if not clean_text:
        return []

    blocks: list[tuple[str, str]] = []
    current_title: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_title, current_lines
        block_text = "\n".join(line for line in current_lines if line.strip()).strip()
        title = current_title or _project_title_from_lines(current_lines)
        if title and block_text:
            blocks.append((title, block_text))
        current_title = None
        current_lines = []

    for raw_line in clean_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        fence_title_text = _project_fence_title_text(line)
        if fence_title_text is not None:
            if current_lines:
                flush()
            if fence_title_text:
                current_title = _project_title_from_line(fence_title_text)
            continue
        if re.fullmatch(r"[-*_]{3,}", line):
            flush()
            continue
        line_title = _project_title_from_line(line)
        if line_title:
            if current_lines:
                flush()
            current_title = line_title
        current_lines.append(line)

    flush()
    return blocks


def _extract_project_contributions(block_text: str) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in _extract_list_items_after_heading(block_text):
        if not (_has_markdown_bold_prefix(item) or _has_leading_title_delimiter(item)):
            continue
        cleaned = _clean_project_contribution_text(item)
        if not cleaned:
            continue
        title = _project_contribution_title(item)
        key = (_normalized_key_text(title), _normalized_key_text(cleaned))
        if key in seen:
            continue
        seen.add(key)
        result.append((title, cleaned))
    return result


def _extract_list_items_after_heading(block_text: str) -> list[str]:
    result: list[str] = []
    active = False
    current_parts: list[str] = []

    def flush() -> None:
        nonlocal current_parts
        if current_parts:
            result.append(" ".join(part.strip() for part in current_parts if part.strip()).strip())
        current_parts = []

    for raw_line in block_text.splitlines():
        line = raw_line.strip()
        if _is_core_contribution_heading(line):
            flush()
            active = True
            continue
        if not active:
            continue
        if re.match(r"^#{1,6}\s+", line) or _is_resume_structure_field_heading(line):
            flush()
            active = False
            continue
        item = _top_level_list_item_text(raw_line)
        if item:
            flush()
            current_parts = [item]
            continue
        if current_parts and raw_line[:1].isspace() and line:
            current_parts.append(line)
            continue
        if not line:
            continue
        flush()
    flush()
    return [item for item in result if item]


def _project_contributions(block_text: str) -> list[str]:
    return [text for _title, text in _extract_project_contributions(block_text)]


def _has_leading_title_delimiter(value: str) -> bool:
    return bool(re.match(r"^.{2,80}?[：:|｜\-—–]+\s*.+$", _strip_markdown_title_markup(value)))


def _project_contribution_title(text: str) -> str:
    cleaned = _strip_markdown_title_markup(text)
    delimiter_match = re.match(r"^(.{2,80}?)[：:|｜\-—–]+\s*(.+)$", cleaned)
    if delimiter_match:
        return _clean_text(delimiter_match.group(1), max_chars=80) or _summarize_title(text)
    return _summarize_title(cleaned)


def _project_fence_title_text(line: str) -> str | None:
    match = re.match(r"^:{3,}\s*(.*?)\s*:*$", line.strip())
    if not match:
        return None
    text = match.group(1).strip()
    normalized = text.lower()
    if not normalized or normalized in {"start", "begin", "end", "stop"}:
        return ""
    text = re.sub(r"^(?:start|begin)\b[\s:：-]*", "", text, flags=re.IGNORECASE).strip()
    if text.lower() in {"end", "stop"}:
        return ""
    return text


def _project_title_from_lines(lines: list[str]) -> str | None:
    for line in lines:
        title = _project_title_from_line(line)
        if title:
            return title
    return None


def _project_title_from_line(line: str) -> str | None:
    list_item = _list_item_text(line)
    raw_title_text = list_item or line
    has_bold_title = _has_markdown_bold_prefix(raw_title_text)
    cleaned = _strip_markdown_title_markup(raw_title_text)
    if not cleaned:
        return None

    title_candidate = cleaned
    has_delimiter = False
    delimiter_match = re.match(r"^(.{2,80}?)[：:|｜\-—–]+\s*(.+)$", cleaned)
    if delimiter_match:
        has_delimiter = True
        title_candidate = delimiter_match.group(1).strip()
    elif len(cleaned) > 80:
        return None

    if _is_project_structure_title(title_candidate):
        return None
    if not _has_semantic_title_text(title_candidate):
        return None
    normalized = title_candidate.lower()
    has_project_marker = any(marker in normalized for marker in ("项目", "project", "作品", "开源", "竞赛"))
    if not (has_project_marker or has_bold_title or (has_delimiter and list_item is None)):
        return None
    return _clean_text(title_candidate, max_chars=120)


def _list_item_text(line: str) -> str | None:
    return _top_level_list_item_text(line)


def _top_level_list_item_text(line: str) -> str | None:
    match = re.match(r"^\s{0,3}(?:[-*+]|\d+[.)]|[（(]?\d+[）)])\s+(.+)$", line)
    if not match:
        return None
    return match.group(1).strip()


def _strip_markdown_title_markup(value: str) -> str:
    text = value.strip()
    bold_prefix_match = re.match(r"^(?:\*\*|__)(.+?)(?:\*\*|__)\s*(.*)$", text)
    if bold_prefix_match:
        text = f"{bold_prefix_match.group(1).strip()}{bold_prefix_match.group(2).strip()}"
    bold_match = re.match(r"^(?:\*\*|__)(.+?)(?:\*\*|__)$", text)
    if bold_match:
        text = bold_match.group(1).strip()
    text = text.strip("*_`# ")
    return text


def _has_markdown_bold_prefix(value: str) -> bool:
    return bool(re.match(r"^\s*(?:\*\*|__).+?(?:\*\*|__)", value.strip()))


def _has_semantic_title_text(value: str) -> bool:
    return bool(re.search(r"[\w\u4e00-\u9fff]", value))


def _clean_project_contribution_text(value: str) -> str:
    text = _clean_text(value, max_chars=MAX_CHUNK_TEXT_CHARS) or ""
    text = re.sub(r"^(?:\*\*|__)(.+?)(?:\*\*|__)\s*([：:].*)$", r"\1\2", text).strip()
    return text.strip("*_` ")


def _is_core_contribution_heading(value: str) -> bool:
    text = _strip_markdown_title_markup(value)
    text = re.sub(r"[：:]\s*$", "", text).strip()
    return text in _RESUME_CORE_CONTRIBUTION_HEADINGS


def _is_resume_structure_field_heading(value: object) -> bool:
    text = _strip_markdown_title_markup(str(value or ""))
    text = re.sub(r"[：:]\s*.*$", "", text).strip().lower()
    text = re.sub(r"\s+", "", text)
    return text in _RESUME_STRUCTURE_FIELD_HEADINGS


def _is_project_structure_title(value: object) -> bool:
    text = _strip_markdown_title_markup(str(value or ""))
    text = re.sub(r"[：:]\s*.*$", "", text).strip().lower()
    text = re.sub(r"\s+", "", text)
    return text in {
        "项目经历",
        "项目经验",
        "项目背景",
        "项目简介",
        "项目描述",
        "核心贡献",
        "主要贡献",
        "关键贡献",
        "项目贡献",
        "核心工作",
        "主要工作",
        "职责",
        "项目职责",
    }


def _resume_source_type(title: str, *, parent_title: str | None = None) -> str:
    breadcrumb = tuple(part for part in (parent_title, title) if part)
    return _infer_resume_section_type(
        _MarkdownSection(title=title, text="", parent_title=parent_title, breadcrumb=breadcrumb)
    )


def _is_project_item_section(section: _MarkdownSection) -> bool:
    if section.level < 3 or not _is_direct_child_of_project_collection(section):
        return False
    project_title, _company, _role = _resume_heading_parts(section.title)
    if not project_title:
        return False
    if _is_project_structure_title(project_title):
        return False
    if _looks_like_company_only(project_title):
        return False
    if _looks_like_contribution_title(project_title):
        return False
    return True


def _is_work_experience_item_section(section: _MarkdownSection) -> bool:
    return section.level >= 3 and _is_direct_child_of_work_collection(section)


def _is_project_detail_subsection(section: _MarkdownSection) -> bool:
    collection_index = _collection_index(section.breadcrumb, _is_project_collection_title)
    if collection_index is None:
        return False
    ancestors_after_collection = section.breadcrumb[collection_index + 1 : -1]
    return any(
        ancestor
        and not _is_project_structure_title(ancestor)
        and not _is_project_collection_title(ancestor)
        for ancestor in ancestors_after_collection
    )


def _is_direct_child_of_project_collection(section: _MarkdownSection) -> bool:
    return bool(section.parent_title and _is_project_collection_title(section.parent_title))


def _is_direct_child_of_work_collection(section: _MarkdownSection) -> bool:
    return bool(section.parent_title and _is_work_collection_title(section.parent_title))


def _is_project_collection_title(value: object) -> bool:
    normalized = _normalized_key_text(value)
    return normalized in {"项目经历", "项目经验", "projects", "projectexperience", "projectexperiences"}


def _is_work_collection_title(value: object) -> bool:
    normalized = _normalized_key_text(value)
    return normalized in {
        "工作经历",
        "工作经验",
        "实习经历",
        "experience",
        "experiences",
        "employment",
        "workexperience",
        "workexperiences",
    }


def _breadcrumb_contains(breadcrumb: tuple[str, ...], keywords: tuple[str, ...]) -> bool:
    normalized_keywords = tuple(keyword.lower() for keyword in keywords)
    for title in breadcrumb:
        normalized = _normalized_key_text(title)
        if any(keyword.lower() in normalized for keyword in normalized_keywords):
            return True
    return False


def _collection_index(breadcrumb: tuple[str, ...], predicate) -> int | None:
    for index, title in enumerate(breadcrumb):
        if predicate(title):
            return index
    return None


def _section_has_child_heading(section: _MarkdownSection) -> bool:
    for line in section.text.splitlines():
        match = re.match(r"^(#{1,6})\s+", line.strip())
        if match and len(match.group(1)) > section.level:
            return True
    return False


def _looks_like_company_only(value: object) -> bool:
    compact = _normalized_key_text(value)
    if not compact:
        return False
    product_markers = ("项目", "project", "平台", "系统", "工具", "服务", "应用", "工作流", "引擎", "库")
    if any(marker in compact for marker in product_markers):
        return False
    company_markers = ("公司", "有限公司", "集团", "企业", "事业部", "inc", "ltd", "llc", "corp", "company")
    return any(marker in compact for marker in company_markers)


def _looks_like_contribution_title(value: object) -> bool:
    compact = _normalized_key_text(value)
    return compact.startswith("贡献项") or compact in {"核心贡献", "主要贡献", "关键贡献", "项目贡献"}


def _looks_like_duration(value: object) -> bool:
    text = _clean_text(value, max_chars=120) or ""
    return bool(re.search(r"\d{4}|\d{2}\.\d{2}|至今|present|now", text, flags=re.IGNORECASE))


def _resume_dedupe_key(section: _MarkdownSection, item: _ResumeSectionItem) -> tuple[str, str, str, str, str]:
    return (
        item.source_type,
        _resume_section_context(section),
        _normalized_key_text(item.source_ref.get("project_title")),
        _normalized_key_text(item.source_ref.get("company")),
        _stable_text_hash(item.text),
    )


def _resume_section_context(section: _MarkdownSection) -> str:
    return " > ".join(section.breadcrumb or (section.title,))


def _stable_text_hash(value: object) -> str:
    normalized = _normalized_key_text(value)
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()


def _normalized_key_text(value: object) -> str:
    text = _strip_markdown_title_markup(str(value or ""))
    text = re.sub(r"[：:]\s*$", "", text).strip().lower()
    return re.sub(r"\s+", "", text)


def _resume_priority(source_type: str) -> int:
    return {
        "resume_project": 92,
        "resume_project_contribution": 91,
        "resume_skill": 88,
        "resume_work_experience": 78,
        "resume_education": 42,
        "resume_summary": 45,
    }.get(source_type, 45)


def _resume_reason(source_type: str) -> str:
    return {
        "resume_project": "简历项目经历，优先用于生成技术深挖节点",
        "resume_project_contribution": "简历项目贡献项，用于生成项目内技术追问点",
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
