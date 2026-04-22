from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
import re
import textwrap
from typing import Pattern

from .diagnostics import Diagnostic, make_diagnostic, make_evidence


HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*$")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
ENGLISH_WORD_RE = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*")
INLINE_CODE_RE = re.compile(r"`[^`]+`")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
URL_RE = re.compile(r"https?://\S+")
PATH_RE = re.compile(
    r"(?:[A-Za-z]:)?(?:[\\/][^\\/\s`]+)+|(?:[\w.-]+/)+[\w./-]+"
)
IDENTIFIER_RE = re.compile(
    r"\b(?:"
    r"[A-Za-z_][A-Za-z0-9_]*\([^\)]*\)"
    r"|[A-Za-z_][A-Za-z0-9_]*(?:[.:][A-Za-z_][A-Za-z0-9_]*)+"
    r"|[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+"
    r"|[a-z]+(?:[A-Z][a-z0-9]+)+"
    r"|[a-z]+_[a-z0-9_]+"
    r")\b"
)
CONFIG_KEY_RE = re.compile(r"\b(?:[A-Z][A-Z0-9_]{1,}|[a-z][a-z0-9_]*\.[a-z0-9_.-]+)\b")
LIST_PREFIX_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")

DEFAULT_ALLOWED_TERMS = frozenset(
    {
        "api",
        "http",
        "https",
        "json",
        "yaml",
        "sql",
        "ui",
        "ux",
        "sdk",
        "cli",
        "url",
        "uri",
        "id",
        "ids",
        "mvp",
        "crud",
        "pytest",
        "pydantic",
        "fastapi",
        "react",
        "typescript",
        "python",
        "javascript",
    }
)


@dataclass(frozen=True)
class LanguagePolicy:
    heading_exact_whitelist: tuple[str, ...] = ()
    heading_pattern_whitelist: tuple[Pattern[str], ...] = ()
    ignored_path_globs: tuple[str, ...] = (
        "**/__pycache__/**",
        "**/.pytest_cache/**",
    )
    allowed_english_terms: frozenset[str] = field(default_factory=lambda: DEFAULT_ALLOWED_TERMS)


def check_repo_language(
    repo_root: str | Path,
    *,
    policy: LanguagePolicy | None = None,
) -> list[Diagnostic]:
    root = Path(repo_root).resolve()
    active_policy = policy or LanguagePolicy()
    diagnostics: list[Diagnostic] = []
    for path in sorted(root.rglob("*.md")):
        relative_path = path.relative_to(root).as_posix()
        diagnostics.extend(
            check_markdown_language(
                path=relative_path,
                text=path.read_text(encoding="utf-8"),
                policy=active_policy,
            )
        )
    return diagnostics


def check_markdown_language(
    *,
    path: str | Path,
    text: str,
    policy: LanguagePolicy | None = None,
    entity_type: str = "doc",
    entity_id: str | None = None,
) -> list[Diagnostic]:
    path_str = str(path).replace("\\", "/")
    active_policy = policy or LanguagePolicy()
    if _is_ignored(path_str, active_policy):
        return []
    text = textwrap.dedent(text)

    resolved_entity_id = entity_id or path_str
    diagnostics: list[Diagnostic] = []

    english_prose_lines: list[tuple[int, str]] = []
    chinese_prose_line_count = 0
    in_code_fence = False
    in_frontmatter = False

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()

        if line_number == 1 and stripped == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            continue

        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue

        heading_match = HEADING_RE.match(raw_line)
        if heading_match is not None:
            heading_text = heading_match.group(1).strip()
            if _heading_should_warn(heading_text, active_policy):
                diagnostics.append(
                    make_diagnostic(
                        code="LANG_HEADING_NOT_CHINESE_BY_DEFAULT",
                        severity="warning",
                        entity_type=entity_type,
                        entity_id=resolved_entity_id,
                        field_path="title",
                        message="标题默认应使用中文，纯英文标题需要进入白名单或改为中文表达。",
                        evidence=[
                            make_evidence(
                                type="language_scan",
                                path=path_str,
                                ref="heading",
                                value=heading_text,
                                line=line_number,
                                snippet=raw_line.strip(),
                            )
                        ],
                    )
                )
            continue

        classification = _classify_body_line(raw_line, active_policy)
        if classification == "english":
            english_prose_lines.append((line_number, raw_line.strip()))
        elif classification == "chinese":
            chinese_prose_line_count += 1

    if english_prose_lines and len(english_prose_lines) > chinese_prose_line_count:
        diagnostics.append(
            make_diagnostic(
                code="LANG_BODY_NOT_CHINESE_DOMINANT",
                severity="warning",
                entity_type=entity_type,
                entity_id=resolved_entity_id,
                field_path="body",
                message="正文默认应以中文为主；检测到英文说明性正文占比过高。",
                evidence=[
                    make_evidence(
                        type="language_scan",
                        path=path_str,
                        ref="english_dominant_lines",
                        value={
                            "english_line_count": len(english_prose_lines),
                            "chinese_line_count": chinese_prose_line_count,
                            "samples": [
                                {"line": line_number, "text": snippet}
                                for line_number, snippet in english_prose_lines[:3]
                            ],
                        },
                    )
                ],
            )
        )

    return diagnostics


def _heading_should_warn(heading_text: str, policy: LanguagePolicy) -> bool:
    if heading_text in policy.heading_exact_whitelist:
        return False
    if any(pattern.search(heading_text) for pattern in policy.heading_pattern_whitelist):
        return False
    if CJK_RE.search(heading_text):
        return False
    return not _is_technical_only_text(heading_text, policy)


def _classify_body_line(raw_line: str, policy: LanguagePolicy) -> str:
    stripped = raw_line.strip()
    if not stripped:
        return "ignore"
    if stripped.startswith("|") and "---" in stripped:
        return "ignore"

    candidate = LIST_PREFIX_RE.sub("", stripped)
    if not candidate:
        return "ignore"
    if _is_technical_only_text(candidate, policy):
        return "ignore"

    sanitized = _sanitize_text(candidate, policy)
    if not sanitized.strip():
        return "ignore"
    if CJK_RE.search(sanitized):
        return "chinese"
    if ENGLISH_WORD_RE.search(sanitized):
        return "english"
    return "ignore"


def _is_technical_only_text(text: str, policy: LanguagePolicy) -> bool:
    sanitized = _sanitize_text(text, policy)
    if not sanitized.strip():
        return True
    if CJK_RE.search(sanitized):
        return False
    words = [item.lower() for item in ENGLISH_WORD_RE.findall(sanitized)]
    if not words:
        return True
    return all(word in policy.allowed_english_terms for word in words)


def _sanitize_text(text: str, policy: LanguagePolicy) -> str:
    sanitized = MARKDOWN_LINK_RE.sub(lambda match: match.group(1), text)
    sanitized = URL_RE.sub(" ", sanitized)
    sanitized = INLINE_CODE_RE.sub(" ", sanitized)
    sanitized = PATH_RE.sub(" ", sanitized)
    sanitized = IDENTIFIER_RE.sub(" ", sanitized)
    sanitized = CONFIG_KEY_RE.sub(" ", sanitized)
    for term in sorted(policy.allowed_english_terms, key=len, reverse=True):
        sanitized = re.sub(rf"\b{re.escape(term)}\b", " ", sanitized, flags=re.IGNORECASE)
    return sanitized


def _is_ignored(path: str, policy: LanguagePolicy) -> bool:
    pure_path = PurePosixPath(path)
    return any(pure_path.match(pattern) for pattern in policy.ignored_path_globs)
