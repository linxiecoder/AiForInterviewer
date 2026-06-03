"""Pure answer coverage policy for Polish feedback review."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class CoverageLevel(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    MISSING = "missing"


@dataclass(frozen=True)
class AnswerCoverageInput:
    answer_text: str
    expected_points: tuple[str, ...] = ()
    loss_point_reasons: tuple[str, ...] = ()
    contradicted_asset_claims: tuple[str, ...] = ()


@dataclass(frozen=True)
class AnswerCoverageDecision:
    expected_points: tuple[str, ...] = ()
    covered_points: tuple[str, ...] = ()
    missing_points: tuple[str, ...] = ()
    weak_points: tuple[str, ...] = ()
    contradicted_points: tuple[str, ...] = ()
    coverage_level: CoverageLevel = CoverageLevel.MISSING
    reason_codes: tuple[str, ...] = ()

    def to_legacy_dict(self) -> dict[str, list[str]]:
        return {
            "expected_points": list(self.expected_points),
            "covered_points": list(self.covered_points),
            "missing_points": list(self.missing_points),
            "weak_points": list(self.weak_points),
            "contradicted_points": list(self.contradicted_points),
        }


class AnswerCoveragePolicy:
    @classmethod
    def evaluate(cls, value: AnswerCoverageInput) -> AnswerCoverageDecision:
        expected_points = _unique(value.expected_points)
        covered_points: list[str] = []
        missing_points: list[str] = []
        weak_points: list[str] = []
        reason_codes: list[str] = []

        for point in expected_points:
            if _point_covered(point, value.answer_text):
                covered_points.append(point)
                reason_codes.append("expected_point_covered")
            elif _point_weakly_covered(point, value.answer_text):
                weak_points.append(point)
                missing_points.append(point)
                reason_codes.append("expected_point_weakly_covered")
            else:
                missing_points.append(point)
                reason_codes.append("expected_point_missing")

        for reason in value.loss_point_reasons:
            text = _clean(reason, max_chars=240)
            if text and text not in weak_points:
                weak_points.append(text)
                reason_codes.append("loss_point_reason_marked_weak")

        contradicted_points = _unique(value.contradicted_asset_claims)
        if contradicted_points:
            reason_codes.append("asset_claim_contradicted")

        covered = _unique(covered_points)
        missing = _unique(missing_points)
        weak = _unique(weak_points)
        return AnswerCoverageDecision(
            expected_points=expected_points,
            covered_points=covered,
            missing_points=missing,
            weak_points=weak,
            contradicted_points=contradicted_points,
            coverage_level=_coverage_level(expected_points=expected_points, missing_points=missing, weak_points=weak),
            reason_codes=tuple(dict.fromkeys(reason_codes)),
        )


def _coverage_level(
    *,
    expected_points: tuple[str, ...],
    missing_points: tuple[str, ...],
    weak_points: tuple[str, ...],
) -> CoverageLevel:
    if not expected_points:
        return CoverageLevel.MISSING
    if not missing_points and not weak_points:
        return CoverageLevel.COMPLETE
    return CoverageLevel.PARTIAL


def _point_covered(point: str, answer_text: str) -> bool:
    point_text = point.casefold()
    answer = answer_text.casefold()
    if point_text and point_text in answer:
        return True
    point_terms = _keywords(point)
    answer_terms = _keywords(answer_text)
    if not point_terms:
        return False
    overlap = point_terms & answer_terms
    return len(overlap) >= min(2, len(point_terms)) or any(len(term) >= 4 for term in overlap)


def _point_weakly_covered(point: str, answer_text: str) -> bool:
    return bool(_keywords(point) & _keywords(answer_text))


def contains_similar_point(points: tuple[str, ...], point: str) -> bool:
    return any(_point_covered(point, candidate) or _point_covered(candidate, point) for candidate in points)


def _keywords(value: object) -> set[str]:
    text = _clean(value, max_chars=2000).casefold()
    raw_terms = re.findall(r"[a-z0-9_+#.-]{2,}|[\u4e00-\u9fff]{2,}", text)
    terms: set[str] = set(raw_terms)
    for term in raw_terms:
        if re.fullmatch(r"[\u4e00-\u9fff]{4,}", term):
            terms.update(term[index : index + 2] for index in range(0, min(len(term) - 1, 18)))
            terms.update(term[index : index + 4] for index in range(0, min(len(term) - 3, 16)))
    return {term for term in terms if term not in {"this", "that", "with", "and", "the", "我会", "说明"}}


def _unique(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = _clean(value, max_chars=240)
        if text and text not in result:
            result.append(text)
    return tuple(result)


def _clean(value: object, *, max_chars: int = 240) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text
