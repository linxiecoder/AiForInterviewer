from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
MODULE_REF_RE = re.compile(r"\bM\d{2}\b")
OQ_REF_RE = re.compile(r"\bOQ-\d+\b")
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
REPO_PATH_PREFIXES = (
    ".github/",
    "apps/",
    "backend/",
    "client/",
    "docs/",
    "frontend/",
    "infra/",
    "packages/",
    "server/",
    "src/",
    "tests/",
    "tools/",
)
FUTURE_BLUEPRINT_TERMS = (
    "monorepo",
    "apps/web",
    "apps/api",
)
GOVERNANCE_TERMS = (
    "bootstrap-state",
    "confirm-transition",
    "doc-governor",
    "evaluate-state",
    "open-window",
    "render-report",
    "validate-state",
)


def scan_document(
    *,
    repo_root: Path,
    path: str,
    required_sections: list[dict[str, Any]],
    document_registry: dict[str, str],
) -> dict[str, Any]:
    resolved_path = repo_root / path
    exists = resolved_path.exists() and resolved_path.is_file()
    text = resolved_path.read_text(encoding="utf-8") if exists else ""
    headings = [match.group(0).strip() for match in HEADING_RE.finditer(text)]
    section_presence = {
        str(section.get("section_id")): _match_heading(
            headings=headings,
            expected_heading=str(section.get("heading", "")),
        )
        for section in required_sections
        if isinstance(section, dict)
    }
    extracted_document_refs = _extract_document_refs(text=text, document_registry=document_registry)
    extracted_module_refs = sorted(set(MODULE_REF_RE.findall(text)))
    extracted_oq_refs = sorted(set(OQ_REF_RE.findall(text)))

    return {
        "exists": exists,
        "headings": headings,
        "section_presence": section_presence,
        "extracted_refs": {
            "document_refs": extracted_document_refs,
            "module_refs": extracted_module_refs,
            "oq_refs": extracted_oq_refs,
        },
        "repo_truth": _extract_repo_truth(repo_root=repo_root, text=text, headings=headings),
        "direction_drift": _extract_direction_drift(text=text),
        "marker_counts": {
            "todo": len(re.findall(r"\bTODO\b", text, flags=re.IGNORECASE)),
            "tbd": len(re.findall(r"\bTBD\b", text, flags=re.IGNORECASE)),
            "unresolved": len(re.findall(r"待确认|待补充|未决", text)),
        },
        "last_scanned_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


def _match_heading(*, headings: list[str], expected_heading: str) -> bool:
    normalized_expected = expected_heading.strip()
    return any(heading.strip() == normalized_expected for heading in headings)


def _extract_document_refs(*, text: str, document_registry: dict[str, str]) -> list[str]:
    hits: set[str] = set()
    for document_id, document_path in document_registry.items():
        if document_id and document_id in text:
            hits.add(document_id)
            continue
        normalized_path = document_path.replace("\\", "/")
        if normalized_path and normalized_path in text.replace("\\", "/"):
            hits.add(document_id)
    return sorted(hits)


def _extract_repo_truth(
    *,
    repo_root: Path,
    text: str,
    headings: list[str],
) -> dict[str, list[str]]:
    referenced_paths = _iter_repo_path_candidates(text=text, headings=headings)
    existing_paths: list[str] = []
    missing_paths: list[str] = []
    for candidate in referenced_paths:
        if (repo_root / candidate).exists():
            existing_paths.append(candidate)
        else:
            missing_paths.append(candidate)
    return {
        "referenced_paths": referenced_paths,
        "existing_paths": existing_paths,
        "missing_paths": missing_paths,
    }


def _extract_direction_drift(*, text: str) -> dict[str, object]:
    normalized_text = text.lower()
    future_blueprint_terms = sorted(
        {
            term
            for term in FUTURE_BLUEPRINT_TERMS
            if term in normalized_text
        }
    )
    governance_terms = sorted(
        {
            term
            for term in GOVERNANCE_TERMS
            if term in normalized_text
        }
    )
    return {
        "future_blueprint_terms": future_blueprint_terms,
        "governance_terms": governance_terms,
        "governance_term_count": len(governance_terms),
    }


def _iter_repo_path_candidates(*, text: str, headings: list[str]) -> list[str]:
    candidates: set[str] = set()
    for inline_code in INLINE_CODE_RE.findall(text):
        normalized = _normalize_repo_path_candidate(inline_code)
        if normalized:
            candidates.add(normalized)
    for heading in headings:
        match = HEADING_RE.match(heading)
        if not match:
            continue
        normalized = _normalize_repo_path_candidate(match.group(2))
        if normalized:
            candidates.add(normalized)
    return sorted(candidates)


def _normalize_repo_path_candidate(value: str) -> str | None:
    candidate = value.strip().strip("`'\"")
    candidate = candidate.rstrip(".,:;)]}")
    if candidate.startswith("./"):
        candidate = candidate[2:]
    candidate = candidate.replace("\\", "/")
    if (
        not candidate
        or "/" not in candidate
        or " " in candidate
        or "://" in candidate
        or candidate.startswith("/")
        or "*" in candidate
    ):
        return None
    if not any(candidate.startswith(prefix) for prefix in REPO_PATH_PREFIXES):
        return None
    return candidate
