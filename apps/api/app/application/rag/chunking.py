"""Semantic-aware chunking for asset RAG ingestion."""

from __future__ import annotations

from dataclasses import dataclass
import re


DEFAULT_TARGET_CHUNK_CHARS = 1000
DEFAULT_MAX_CHUNK_CHARS = 2000
DEFAULT_MIN_CHUNK_CHARS = 160
DEFAULT_FALLBACK_OVERLAP_CHARS = 120

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_LIST_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)")


@dataclass(frozen=True)
class RagChunkDraft:
    chunk_index: int
    heading_path: tuple[str, ...]
    content: str
    char_count: int

    @property
    def embedding_input(self) -> str:
        heading = " > ".join(self.heading_path).strip()
        return f"{heading}\n\n{self.content}".strip() if heading else self.content


@dataclass(frozen=True)
class _Block:
    heading_path: tuple[str, ...]
    content: str
    kind: str


def chunk_markdown_semantically(
    content: str,
    *,
    target_chunk_chars: int = DEFAULT_TARGET_CHUNK_CHARS,
    max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS,
    min_chunk_chars: int = DEFAULT_MIN_CHUNK_CHARS,
    fallback_overlap_chars: int = DEFAULT_FALLBACK_OVERLAP_CHARS,
) -> tuple[RagChunkDraft, ...]:
    blocks = _markdown_blocks(content)
    chunks: list[_Block] = []
    current: _Block | None = None

    def flush_current() -> None:
        nonlocal current
        if current is not None and current.content.strip():
            chunks.append(current)
        current = None

    for block in blocks:
        if len(block.content) > max_chunk_chars and block.kind != "code":
            flush_current()
            chunks.extend(
                _fallback_split_block(
                    block,
                    max_chunk_chars=max_chunk_chars,
                    overlap_chars=fallback_overlap_chars,
                )
            )
            continue

        if current is None:
            current = block
            continue

        combined_len = len(current.content) + 2 + len(block.content)
        same_heading = current.heading_path == block.heading_path
        should_merge = same_heading and (combined_len <= target_chunk_chars or (
            same_heading and len(current.content) < min_chunk_chars and combined_len <= max_chunk_chars
        ))
        if should_merge:
            current = _Block(
                heading_path=current.heading_path or block.heading_path,
                content=f"{current.content.rstrip()}\n\n{block.content.lstrip()}".strip(),
                kind="mixed" if current.kind != block.kind else current.kind,
            )
        else:
            flush_current()
            current = block

    flush_current()
    return tuple(
        RagChunkDraft(
            chunk_index=index,
            heading_path=chunk.heading_path,
            content=chunk.content,
            char_count=len(chunk.content),
        )
        for index, chunk in enumerate(chunks)
    )


def _markdown_blocks(content: str) -> list[_Block]:
    lines = content.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    blocks: list[_Block] = []
    heading_path: list[str] = []
    pending_heading: list[str] = []
    buffer: list[str] = []
    kind: str | None = None
    in_code = False
    code_fence = ""

    def emit() -> None:
        nonlocal buffer, kind
        text = "\n".join(buffer).strip()
        if text:
            blocks.append(_Block(tuple(heading_path), text, kind or "paragraph"))
        buffer = []
        kind = None

    def ensure_pending(next_kind: str) -> None:
        nonlocal pending_heading, kind
        if pending_heading:
            buffer.extend(pending_heading)
            pending_heading = []
        kind = next_kind

    for line in lines:
        heading_match = _HEADING_RE.match(line)
        fence_match = _FENCE_RE.match(line)

        if in_code:
            buffer.append(line)
            if line.strip().startswith(code_fence):
                emit()
                in_code = False
                code_fence = ""
            continue

        if fence_match:
            emit()
            ensure_pending("code")
            buffer.append(line)
            in_code = True
            code_fence = fence_match.group(1)
            continue

        if heading_match:
            emit()
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            heading_path = [*heading_path[: level - 1], title]
            pending_heading = [line]
            continue

        if not line.strip():
            if pending_heading:
                pending_heading.append(line)
                continue
            emit()
            continue

        next_kind = "list" if _LIST_RE.match(line) else "paragraph"
        if kind is not None and kind != next_kind:
            emit()
        ensure_pending(next_kind)
        buffer.append(line)

    if pending_heading and not buffer:
        buffer.extend(pending_heading)
        pending_heading = []
        kind = "paragraph"
    emit()
    if blocks:
        return blocks
    stripped = content.strip()
    return [_Block(tuple(), stripped, "paragraph")] if stripped else []


def _fallback_split_block(
    block: _Block,
    *,
    max_chunk_chars: int,
    overlap_chars: int,
) -> list[_Block]:
    text = block.content
    chunks: list[_Block] = []
    start = 0
    while start < len(text):
        end = min(start + max_chunk_chars, len(text))
        if end < len(text):
            end = _best_boundary(text, start=start, hard_end=end)
        part = text[start:end].strip()
        if part:
            chunks.append(_Block(block.heading_path, part, block.kind))
        if end >= len(text):
            break
        start = max(end - overlap_chars, start + 1)
    return chunks


def _best_boundary(text: str, *, start: int, hard_end: int) -> int:
    window_start = max(start + 1, hard_end - 400)
    candidates = [
        text.rfind(boundary, window_start, hard_end)
        for boundary in ("\n\n", "\n", "。", ".", "；", ";", "，", ",", " ")
    ]
    best = max(candidates)
    if best <= start:
        return hard_end
    return best + 1
