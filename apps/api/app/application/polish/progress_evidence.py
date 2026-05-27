"""Deterministic evidence chunking for polish progress tree prompts."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Literal

from app.application.llm.agent_io import AgentEvidenceItem
from app.application.polish.question_generation_policy import (
    SEMANTIC_JOB_SOURCE_TYPES,
    SEMANTIC_RESUME_SOURCE_TYPES,
    SOURCE_PRIORITY_POLICY_BY_PURPOSE,
)


ProgressEvidencePurpose = Literal["initial_plan", "state_refresh", "next_question"]

MAX_CHUNK_TEXT_CHARS = 1200
ALLOWED_EVIDENCE_REF_EXCERPT_CHARS = 200
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
    return {
        "context_metadata": _context_metadata(context),
        "selected_evidence_chunks": [chunk.to_prompt_dict() for chunk in selection.selected_chunks],
        "allowed_evidence_refs": _allowed_evidence_refs_for_prompt(selection.selected_chunks),
        "dropped_context_summary": selection.dropped_context_summary,
        "match_context_summary": _match_context_summary(context.get("match_context", {})),
        "turns_summary": _turns_summary(context.get("turns", [])),
    }


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
    markdown_text = _normalize_resume_project_containers(markdown_text) if markdown_text else None
    emitted: set[tuple[str, str]] = set()
    project_sequence = 0
    project_sequences: dict[str, int] = {}

    if markdown_text:
        for section in _split_markdown_sections(markdown_text):
            source_type = _resume_source_type(section.title, parent_title=section.parent_title)
            for item in _resume_section_items(section, source_type):
                key = (item.source_type, item.text)
                if key in emitted:
                    continue
                emitted.add(key)
                item_source_ref = dict(item.source_ref)
                project_title = str(item_source_ref.get("project_title") or item.title or "")
                if item.source_type == "resume_project":
                    project_sequence += 1
                    item_source_ref["project_sequence"] = project_sequence
                    if project_title:
                        project_sequences[project_title] = project_sequence
                elif item.source_type == "resume_project_contribution":
                    if project_title in project_sequences:
                        item_source_ref["project_sequence"] = project_sequences[project_title]
                add_chunk(
                    item.source_type,
                    source_ref={**source_ref, **item_source_ref},
                    title=item.title,
                    text=item.text,
                    priority=_resume_priority(item.source_type),
                    reason=_resume_reason(item.source_type),
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


def _normalize_resume_project_containers(markdown_text: str) -> str:
    lines: list[str] = []
    for raw_line in markdown_text.splitlines():
        parsed_header = _parse_resume_project_container_header(raw_line)
        if parsed_header is not None:
            project_title, company = parsed_header
            heading = f"### {project_title}"
            if company:
                heading = f"{heading} @ {company}"
            lines.append(heading)
            continue
        if re.fullmatch(r"\s*:{3,}\s*(?:end|stop)\s*:*\s*", raw_line, flags=re.IGNORECASE):
            continue
        lines.append(raw_line)
    return "\n".join(lines)


def _parse_resume_project_container_header(raw_line: str) -> tuple[str, str | None] | None:
    match = re.match(
        r"^\s*:{3,}\s*start\s+\*\*(?P<title>.+?)\*\*\s*:{3,}\s*"
        r"(?:(?:\*\*(?P<company>.+?)\*\*)\s*:{3,}\s*)?end\s*:*\s*$",
        raw_line,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    project_title = _clean_text(match.group("title"), max_chars=120)
    if not project_title:
        return None
    company = _clean_text(match.group("company"), max_chars=120)
    return project_title, company


def _split_markdown_sections(markdown_text: str) -> list[_MarkdownSection]:
    sections: list[_MarkdownSection] = []
    current_title = "summary"
    current_level = 0
    current_parent_title: str | None = None
    current_lines: list[str] = []
    heading_stack: dict[int, str] = {}
    for line in markdown_text.splitlines():
        heading_match = re.match(r"^(#{1,6})\s*(.+)$", line.strip())
        if heading_match:
            _append_section(
                sections,
                current_title,
                current_lines,
                level=current_level,
                parent_title=current_parent_title,
            )
            current_level = len(heading_match.group(1))
            current_title = heading_match.group(2).strip()
            current_parent_title = _nearest_parent_title(heading_stack, current_level)
            for level in list(heading_stack):
                if level >= current_level:
                    del heading_stack[level]
            heading_stack[current_level] = current_title
            current_lines = []
            continue
        current_lines.append(line)
    _append_section(
        sections,
        current_title,
        current_lines,
        level=current_level,
        parent_title=current_parent_title,
    )
    return sections


def _nearest_parent_title(heading_stack: dict[int, str], level: int) -> str | None:
    for candidate_level in range(level - 1, 0, -1):
        parent_title = heading_stack.get(candidate_level)
        if parent_title:
            return parent_title
    return None


def _append_section(
    sections: list[_MarkdownSection],
    title: str,
    lines: list[str],
    *,
    level: int = 0,
    parent_title: str | None = None,
) -> None:
    text = "\n".join(line.rstrip() for line in lines).strip()
    if text:
        sections.append(_MarkdownSection(title=title, text=text, level=level, parent_title=parent_title))


def _resume_section_items(section: _MarkdownSection, source_type: str) -> list[_ResumeSectionItem]:
    if source_type == "resume_project":
        heading_parts = _resume_project_heading_parts(section)
        if heading_parts is not None:
            return _resume_project_section_items(section, heading_parts)
        project_items = _resume_project_block_items(section.text, source_type=source_type)
        if project_items:
            return project_items
        paragraphs = _split_paragraphs(section.text)
        if len(paragraphs) > 1:
            return [
                _ResumeSectionItem(
                    source_type=source_type,
                    title=_summarize_title(paragraph),
                    text=paragraph,
                    source_ref={},
                )
                for paragraph in paragraphs
            ]
    if source_type == "resume_work_experience":
        paragraphs = _split_paragraphs(section.text)
        if len(paragraphs) > 1:
            return [
                _ResumeSectionItem(
                    source_type=source_type,
                    title=_summarize_title(paragraph),
                    text=paragraph,
                    source_ref={},
                )
                for paragraph in paragraphs
            ]
    return [_ResumeSectionItem(source_type=source_type, title=section.title, text=section.text, source_ref={})]


def _resume_project_heading_parts(section: _MarkdownSection) -> tuple[str, str | None] | None:
    title = _clean_text(section.title, max_chars=160) or ""
    if _is_project_structure_title(title):
        return None
    company: str | None = None
    if " @ " in title:
        project_title, company = title.split(" @ ", 1)
    else:
        project_title = title
    project_title = _clean_text(_strip_markdown_title_markup(project_title), max_chars=120)
    company = _clean_text(_strip_markdown_title_markup(company), max_chars=120) if company else None
    if not project_title or _is_project_structure_title(project_title):
        return None
    return project_title, company


def _resume_project_section_items(
    section: _MarkdownSection,
    heading_parts: tuple[str, str | None],
) -> list[_ResumeSectionItem]:
    project_title, company = heading_parts
    source_ref: dict[str, Any] = {"project_title": project_title}
    if company:
        source_ref["company"] = company
    items = [
        _ResumeSectionItem(
            source_type="resume_project",
            title=project_title,
            text=section.text,
            source_ref=source_ref,
        )
    ]
    for contribution in _project_contributions(section.text):
        items.append(
            _ResumeSectionItem(
                source_type="resume_project_contribution",
                title=_project_contribution_title(contribution),
                text=contribution,
                source_ref=source_ref,
            )
        )
    return items


def _resume_project_block_items(text: str, *, source_type: str) -> list[_ResumeSectionItem]:
    blocks = _split_project_blocks(text)
    if not blocks:
        return []

    items: list[_ResumeSectionItem] = []
    seen: set[tuple[str, str, str]] = set()
    for project_sequence, (title, block_text) in enumerate(blocks, start=1):
        project_ref = {"project_title": title, "project_sequence": project_sequence}
        candidates = [
            _ResumeSectionItem(
                source_type=source_type,
                title=title,
                text=block_text,
                source_ref=project_ref,
            )
        ]
        if source_type == "resume_project":
            candidates.extend(
                _ResumeSectionItem(
                    source_type="resume_project_contribution",
                    title=_project_contribution_title(contribution),
                    text=contribution,
                    source_ref=project_ref,
                )
                for contribution in _project_contributions(block_text)
            )
        for candidate in candidates:
            key = (candidate.source_type, candidate.title, candidate.text)
            if key in seen:
                continue
            seen.add(key)
            items.append(candidate)
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


def _project_contributions(block_text: str) -> list[str]:
    result: list[str] = []
    saw_contribution_section = False
    in_contribution_section = False
    for raw_line in block_text.splitlines():
        line = raw_line.strip()
        item = _list_item_text(line)
        if not item and _is_core_contribution_heading(line):
            saw_contribution_section = True
            in_contribution_section = True
            continue
        if (
            saw_contribution_section
            and in_contribution_section
            and not item
            and _is_project_structure_title(line)
            and not _is_core_contribution_heading(line)
        ):
            in_contribution_section = False
            continue
        if saw_contribution_section and not in_contribution_section:
            continue
        if not item:
            continue
        cleaned = _clean_project_contribution_text(item)
        if cleaned and cleaned not in result:
            result.append(cleaned)
    return result


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
    match = re.match(r"^(?:[-*+]|\d+[.)]|[（(]?\d+[）)])\s+(.+)$", line.strip())
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
    return text in {"核心贡献", "主要贡献", "关键贡献", "项目贡献", "贡献项", "核心工作", "主要工作"}


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
        "贡献项",
        "核心工作",
        "主要工作",
        "职责",
        "项目职责",
    }


def _resume_source_type(title: str, *, parent_title: str | None = None) -> str:
    normalized = title.lower()
    parent_normalized = (parent_title or "").lower()
    if _is_project_structure_title(title) and any(
        keyword in normalized for keyword in ("背景", "贡献", "职责", "描述", "简介")
    ):
        return "resume_summary"
    if " @ " in title and not _is_project_structure_title(title):
        return "resume_project"
    if (
        parent_title
        and any(keyword in parent_normalized for keyword in ("项目", "project", "作品", "开源", "竞赛"))
        and not _is_project_structure_title(title)
    ):
        return "resume_project"
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
