from __future__ import annotations

import re
from typing import Final


_SEMANTIC_TEXT_SEPARATORS: Final = ",.;: /|()[]{}<>\n\r\t\uff0c\u3002\uff1b\u3001\uff1a\uff01\uff08\uff09\u3010\u3011"
_ENGLISH_NEGATION_PATTERN: Final = re.compile(
    r"\b(?:not|never|cannot|can't|cant|no|without)\b",
    re.IGNORECASE,
)
_CJK_NEGATION_TERMS: Final = (
    "\u4e0d",
    "\u6ca1\u6709",
    "\u4e0d\u662f",
    "\u4e0d\u80fd",
    "\u65e0\u6cd5",
    "\u5e76\u975e",
    "\u4e0d\u4f1a",
)


def semantic_text(value: object, *, max_chars: int = 12000) -> str:
    text = _clean(value, max_chars=max_chars).lower()
    for separator in _SEMANTIC_TEXT_SEPARATORS:
        text = text.replace(separator, "")
    return "".join(text.split())


def semantic_terms(value: object, *, max_chars: int = 4000) -> tuple[str, ...]:
    text = _clean(value, max_chars=max_chars)
    normalized = text
    for separator in _SEMANTIC_TEXT_SEPARATORS:
        normalized = normalized.replace(separator, " ")
    return tuple(
        dict.fromkeys(
            term
            for raw_term in normalized.split()
            if (term := semantic_text(raw_term, max_chars=max_chars)) and len(term) >= 2
        )
    )


def answers_are_semantically_equivalent(current_answer_text: str, previous_answer_text: str) -> bool:
    current = semantic_text(current_answer_text)
    previous = semantic_text(previous_answer_text)
    if not current or not previous or has_negation_conflict(current_answer_text, previous_answer_text):
        return False
    return current == previous


def answer_covers_reference_section(answer_text: str, section_content: str) -> bool:
    if has_negation_conflict(answer_text, section_content):
        return False
    answer_norm = semantic_text(answer_text)
    section_norm = semantic_text(section_content)
    if not answer_norm or not section_norm:
        return False
    if section_norm in answer_norm:
        return True
    section_terms = semantic_terms(section_content)
    if not section_terms:
        return False
    matched_terms = [term for term in section_terms if term in answer_norm]
    return len(matched_terms) >= max(2, round(len(section_terms) * 0.6))


def answer_strongly_matches_reference(answer_text: str, reference_answer_text: str) -> bool:
    if has_negation_conflict(answer_text, reference_answer_text):
        return False
    answer_norm = semantic_text(answer_text)
    reference_norm = semantic_text(reference_answer_text)
    if not answer_norm or not reference_norm:
        return False
    if answer_norm == reference_norm:
        return True
    answer_terms = semantic_terms(answer_text)
    reference_terms = semantic_terms(reference_answer_text)
    if not answer_terms or not reference_terms:
        return False
    return answer_terms == reference_terms and abs(len(answer_norm) - len(reference_norm)) <= 4


def has_negation_conflict(answer_text: str, reference_answer_text: str) -> bool:
    return _has_negation(answer_text) != _has_negation(reference_answer_text)


def text_matches_reference_terms(value: object, match_terms: tuple[str, ...]) -> bool:
    text = semantic_text(value)
    if not text:
        return False
    for term in match_terms:
        term_text = semantic_text(term)
        if term_text and (term_text in text or text in term_text):
            return True
    return False


def _has_negation(value: object) -> bool:
    text = _clean(value, max_chars=12000).lower()
    return bool(_ENGLISH_NEGATION_PATTERN.search(text)) or any(term in text for term in _CJK_NEGATION_TERMS)


def _clean(value: object, *, max_chars: int = 240) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text
