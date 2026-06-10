"""Scoring use cases."""

from __future__ import annotations

from typing import Any

from app.application.common.result import ApplicationResult
from app.application.scoring.commands import CreateScoreResultCommand
from app.application.scoring.ports import ScoringRepository
from app.application.scoring.queries import GetScoreResultQuery, ListScoreResultsQuery
from app.domain.scoring.entities import ScoreDimension
from app.domain.scoring.policies import ScoringPolicy, ScoringPolicyError
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import ScoreType
from app.domain.shared.errors import DomainError
from app.domain.shared.ids import ResourceIdPrefix, generate_resource_id

SCORE_VERSION = "aiforinterviewer.scoring.result.v1"
VALIDATION_STATUS = "valid"
SCORE_SCALE = "0_100_product_scale"


class ScoringUseCases:
    def __init__(self, repository: ScoringRepository):
        self._repository = repository

    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="scoring_partial")

    def create(self, command: CreateScoreResultCommand) -> ApplicationResult[dict[str, Any]]:
        target_error = _validate_target(command)
        if target_error is not None:
            return ApplicationResult(error=target_error)

        try:
            score_type = _score_type_value(command.score_type)
            dimensions = ScoringPolicy.validate_dimensions(
                rubric_version=command.rubric_version,
                dimensions=command.dimensions,
            )
            computed_score = ScoringPolicy.compute_overall_score(dimensions)
            if command.overall_score is not None and command.overall_score != computed_score:
                return ApplicationResult(
                    error=DomainError(
                        code="validation_failed",
                        message="overall_score must match deterministic dimension score.",
                    )
                )
            primary_bottleneck = ScoringPolicy.select_primary_bottleneck(dimensions)
            next_action_type = ScoringPolicy.derive_next_action_type(
                target_type=command.target_type,
                target_parent_type=command.target_parent_type,
                source_module=command.source_module,
                primary_bottleneck=primary_bottleneck,
                requested_next_action_type=command.next_action_type,
            )
        except ScoringPolicyError as exc:
            return ApplicationResult(
                error=DomainError(code="validation_failed", message=str(exc))
            )

        now = utc_now()
        confidence = _average_confidence(dimensions)
        score_result = {
            "score_result_id": generate_resource_id(ResourceIdPrefix.SCORE),
            "owner_id": command.owner_id,
            "actor_id": command.actor_id,
            "status": VALIDATION_STATUS,
            "score_type": score_type,
            "target_type": command.target_type,
            "target_id": command.target_id,
            "target_parent_type": command.target_parent_type,
            "target_parent_id": command.target_parent_id,
            "source_module": command.source_module,
            "source_event": command.source_event,
            "score_value": computed_score,
            "overall_score": computed_score,
            "score_scale": SCORE_SCALE,
            "score_version": SCORE_VERSION,
            "rubric_version": command.rubric_version,
            "validation_status": VALIDATION_STATUS,
            "confidence": confidence,
            "confidence_level": _confidence_level(confidence),
            "dimension_scores": _dimension_scores(dimensions),
            "evidence_links": tuple(command.evidence_links),
            "primary_bottleneck": primary_bottleneck,
            "next_action_type": next_action_type,
            "generated_by_task_id": None,
            "allowed_as_formal_score": True,
            "created_at": now,
            "updated_at": now,
            "generated_at": now,
        }
        return ApplicationResult(value=self._repository.add_score_result(score_result))

    def get(self, query: GetScoreResultQuery) -> ApplicationResult[dict[str, Any]]:
        found = self._repository.get_score_result(
            owner_id=query.owner_id,
            score_result_id=query.score_result_id,
        )
        if found is None:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Score result not found.")
            )
        return ApplicationResult(value=found)

    def list(self, query: ListScoreResultsQuery) -> ApplicationResult[tuple[dict[str, Any], ...]]:
        if (query.target_parent_type is None) != (query.target_parent_id is None):
            return ApplicationResult(
                error=DomainError(
                    code="validation_failed",
                    message="target_parent_type and target_parent_id must be provided together.",
                )
            )
        return ApplicationResult(
            value=self._repository.list_score_results(
                owner_id=query.owner_id,
                target_type=_normalize_optional(query.target_type),
                target_id=_normalize_optional(query.target_id),
                target_parent_type=_normalize_optional(query.target_parent_type),
                target_parent_id=_normalize_optional(query.target_parent_id),
            )
        )

    def list_for_target_parent(
        self,
        *,
        owner_id: str,
        target_parent_type: str,
        target_parent_id: str,
    ) -> ApplicationResult[tuple[dict[str, Any], ...]]:
        return self.list(
            ListScoreResultsQuery(
                owner_id=owner_id,
                target_parent_type=target_parent_type,
                target_parent_id=target_parent_id,
            )
        )


def _validate_target(command: CreateScoreResultCommand) -> DomainError | None:
    if not command.owner_id.strip() or not command.actor_id.strip():
        return DomainError(code="validation_failed", message="owner_id and actor_id are required.")
    if not command.target_type.strip() or not command.target_id.strip():
        return DomainError(code="validation_failed", message="target_type and target_id are required.")
    if (command.target_parent_type is None) != (command.target_parent_id is None):
        return DomainError(
            code="validation_failed",
            message="target_parent_type and target_parent_id must be provided together.",
        )
    if command.overall_score is not None and not 0 <= command.overall_score <= 100:
        return DomainError(code="validation_failed", message="overall_score must be between 0 and 100.")
    return None


def _score_type_value(score_type: ScoreType | str) -> str:
    value = score_type.value if isinstance(score_type, ScoreType) else str(score_type)
    allowed = {item.value for item in ScoreType}
    if value not in allowed:
        raise ScoringPolicyError(f"unsupported score_type: {value}")
    return value


def _dimension_scores(dimensions: tuple[ScoreDimension, ...]) -> list[dict[str, Any]]:
    weight = int(100 / len(dimensions)) if dimensions else 0
    return [
        {
            "dimension_key": dimension.name,
            "dimension_score": dimension.score,
            "score": dimension.score,
            "weight": weight,
            "confidence": dimension.confidence,
            "evidence_links": list(dimension.evidence_links),
        }
        for dimension in dimensions
    ]


def _average_confidence(dimensions: tuple[ScoreDimension, ...]) -> float:
    if not dimensions:
        return 0.0
    return round(sum(dimension.confidence for dimension in dimensions) / len(dimensions), 4)


def _confidence_level(confidence: float) -> str:
    if confidence >= 0.8:
        return "high"
    if confidence >= 0.6:
        return "medium"
    if confidence > 0:
        return "low"
    return "insufficient"


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
