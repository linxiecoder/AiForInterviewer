"""Pure answer change policy for repeated Polish answer review."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.domain.polish.policies.answer_coverage_policy import contains_similar_point


class AnswerChangeTrend(str, Enum):
    IMPROVED = "improved"
    REGRESSED = "regressed"
    MIXED = "mixed"
    UNCHANGED = "unchanged"
    FIRST_ATTEMPT = "first_attempt"


@dataclass(frozen=True)
class PreviousAnswerSnapshot:
    answer_id: str | None = None
    covered_points: tuple[str, ...] = ()
    loss_point_ids: tuple[str, ...] = ()
    score_value: float | None = None


@dataclass(frozen=True)
class AnswerChangeInput:
    current_covered_points: tuple[str, ...] = ()
    current_loss_point_ids: tuple[str, ...] = ()
    current_score_value: float | None = None
    previous_answers: tuple[PreviousAnswerSnapshot, ...] = ()
    llm_regressed_points: tuple[str, ...] = ()
    llm_repeated_loss_point_ids: tuple[str, ...] = ()
    llm_score_delta: float | None = None


@dataclass(frozen=True)
class AnswerChangeDecision:
    has_prior_attempts: bool
    previous_answer_refs: tuple[str, ...] = ()
    retained_points: tuple[str, ...] = ()
    newly_added_points: tuple[str, ...] = ()
    regressed_points: tuple[str, ...] = ()
    repeated_loss_points: tuple[str, ...] = ()
    fixed_loss_points: tuple[str, ...] = ()
    score_delta: float | None = None
    trend: AnswerChangeTrend = AnswerChangeTrend.FIRST_ATTEMPT
    reason_codes: tuple[str, ...] = ()

    def to_legacy_dict(self) -> dict[str, object]:
        return {
            "has_prior_attempts": self.has_prior_attempts,
            "previous_answer_refs": list(self.previous_answer_refs),
            "retained_points": list(self.retained_points),
            "newly_added_points": list(self.newly_added_points),
            "regressed_points": list(self.regressed_points),
            "repeated_loss_points": list(self.repeated_loss_points),
            "fixed_loss_points": list(self.fixed_loss_points),
            "score_delta": self.score_delta,
            "trend": self.trend.value,
        }


class AnswerChangePolicy:
    @classmethod
    def evaluate(cls, value: AnswerChangeInput) -> AnswerChangeDecision:
        current_covered = _unique(value.current_covered_points)
        if not value.previous_answers:
            return AnswerChangeDecision(
                has_prior_attempts=False,
                newly_added_points=current_covered,
                trend=AnswerChangeTrend.FIRST_ATTEMPT,
                reason_codes=("no_prior_attempts",),
            )

        reason_codes: list[str] = []
        previous_refs = _unique(tuple(answer.answer_id or "" for answer in value.previous_answers))
        prior_covered = _unique(
            tuple(point for answer in value.previous_answers for point in answer.covered_points)
        )
        retained_points = tuple(point for point in prior_covered if contains_similar_point(current_covered, point))
        regressed_points = tuple(point for point in prior_covered if not contains_similar_point(current_covered, point))
        newly_added_points = tuple(point for point in current_covered if not contains_similar_point(prior_covered, point))

        current_loss_ids = _unique(value.current_loss_point_ids)
        previous_loss_ids = _unique(tuple(loss_id for answer in value.previous_answers for loss_id in answer.loss_point_ids))
        repeated_loss_points = tuple(loss_id for loss_id in previous_loss_ids if loss_id in current_loss_ids)
        fixed_loss_points = tuple(loss_id for loss_id in previous_loss_ids if loss_id not in current_loss_ids)

        merged_regressed = _unique((*regressed_points, *value.llm_regressed_points))
        merged_repeated = _unique((*repeated_loss_points, *value.llm_repeated_loss_point_ids))
        score_delta = _score_delta(
            current_score=value.current_score_value,
            previous_scores=tuple(answer.score_value for answer in value.previous_answers),
            fallback=value.llm_score_delta,
        )
        trend = _trend(
            regressed_points=merged_regressed,
            fixed_loss_points=fixed_loss_points,
            newly_added_points=newly_added_points,
            score_delta=score_delta,
        )
        if retained_points:
            reason_codes.append("points_retained")
        if newly_added_points:
            reason_codes.append("points_newly_added")
        if merged_regressed:
            reason_codes.append("points_regressed")
        if merged_repeated:
            reason_codes.append("loss_points_repeated")
        if fixed_loss_points:
            reason_codes.append("loss_points_fixed")
        if score_delta is not None:
            reason_codes.append("score_delta_available")

        return AnswerChangeDecision(
            has_prior_attempts=True,
            previous_answer_refs=previous_refs,
            retained_points=_unique(retained_points),
            newly_added_points=_unique(newly_added_points),
            regressed_points=merged_regressed,
            repeated_loss_points=merged_repeated,
            fixed_loss_points=_unique(fixed_loss_points),
            score_delta=score_delta,
            trend=trend,
            reason_codes=tuple(dict.fromkeys(reason_codes)),
        )


def _score_delta(
    *,
    current_score: float | None,
    previous_scores: tuple[float | None, ...],
    fallback: float | None,
) -> float | None:
    clean_previous_scores = [score for score in previous_scores if score is not None]
    if current_score is None or not clean_previous_scores:
        return fallback
    return round(current_score - clean_previous_scores[-1], 2)


def _trend(
    *,
    regressed_points: tuple[str, ...],
    fixed_loss_points: tuple[str, ...],
    newly_added_points: tuple[str, ...],
    score_delta: float | None,
) -> AnswerChangeTrend:
    improved_signal = bool(fixed_loss_points or newly_added_points) or (score_delta is not None and score_delta > 0)
    regressed_signal = bool(regressed_points) or (score_delta is not None and score_delta < 0)
    if improved_signal and regressed_signal:
        return AnswerChangeTrend.MIXED
    if regressed_signal:
        return AnswerChangeTrend.REGRESSED
    if improved_signal:
        return AnswerChangeTrend.IMPROVED
    return AnswerChangeTrend.UNCHANGED


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
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
