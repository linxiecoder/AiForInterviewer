"""Pure scoring policy for Polish feedback loss-point based scoring."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoringLossPoint:
    """Severity item provided by LLM candidate payload."""

    loss_point_id: str
    severity: str
    reason: str = ""


@dataclass(frozen=True)
class ScoringInput:
    """Structured input for deterministic score calculation."""

    loss_points: tuple[ScoringLossPoint, ...] = ()


@dataclass(frozen=True)
class ScoredLossPoint:
    """Deterministic scoring decision for one loss point."""

    loss_point_id: str
    severity: str
    deduction: float
    is_unknown_severity: bool = False


@dataclass(frozen=True)
class ScoringDecision:
    """Scoring policy output used by application rules."""

    score_type: str
    score_value: float
    scoring_basis: str
    scored_loss_points: tuple[ScoredLossPoint, ...]
    warnings: tuple[str, ...] = ()


class ScoringPolicy:
    @classmethod
    def evaluate(cls, value: ScoringInput) -> ScoringDecision:
        scored_loss_points: list[ScoredLossPoint] = []
        warnings: list[str] = []
        total_deduction = 0.0

        for loss_point in value.loss_points:
            severity = _normalize_severity(loss_point.severity)
            deduction = _deduction_for_severity(severity)
            is_unknown_severity = severity not in _SCORING_SEVERITY_MAP
            if is_unknown_severity:
                warnings.append(f"score_point_unknown_severity:{loss_point.loss_point_id or 'unknown'}")
            total_deduction += deduction
            scored_loss_points.append(
                ScoredLossPoint(
                    loss_point_id=_clean(loss_point.loss_point_id),
                    severity=severity,
                    deduction=deduction,
                    is_unknown_severity=is_unknown_severity,
                )
            )

        score_value = max(0.0, 100.0 - total_deduction)
        score_value = round(score_value, 2)
        decision = ScoringDecision(
            score_type="polish_answer",
            score_value=score_value,
            scoring_basis=_scoring_basis_for(),
            scored_loss_points=tuple(scored_loss_points),
            warnings=tuple(dict.fromkeys(warnings)),
        )
        return decision


_SCORING_SEVERITY_MAP: dict[str, float] = {
    "critical": 20.0,
    "major": 12.0,
    "minor": 6.0,
}


def _deduction_for_severity(severity: str) -> float:
    return _SCORING_SEVERITY_MAP.get(severity, 0.0)


def _normalize_severity(value: object) -> str:
    return _clean(value)


def _scoring_basis_for() -> str:
    return "score_result is computed server-side from loss_point severity."


def _clean(value: object, *, max_chars: int = 80) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text
