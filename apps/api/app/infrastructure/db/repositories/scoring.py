"""SQLAlchemy repository for scoring results."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.application.scoring.ports import ScoringRepository
from app.domain.shared.refs import ResourceRef
from app.infrastructure.db.models.scoring import ScoreResult
from app.infrastructure.db.repositories.base import SqlAlchemyRepository


class SqlAlchemyScoringRepository(SqlAlchemyRepository, ScoringRepository):
    def __init__(
        self,
        session_factory: sessionmaker[Session] | None = None,
        *,
        session: Session | None = None,
    ) -> None:
        super().__init__(session_factory, session=session)

    def get_ref(self, score_result_id: str) -> ResourceRef | None:
        with self.session_scope() as session:
            found = session.get(ScoreResult, score_result_id)
        if found is None:
            return None
        return ResourceRef(resource_type="score_result", resource_id=score_result_id)

    def add_score_result(self, score_result: dict[str, Any]) -> dict[str, Any]:
        with self.session_scope() as session:
            model = ScoreResult(
                id=score_result["score_result_id"],
                owner_id=score_result["owner_id"],
                actor_id=score_result["actor_id"],
                record_version=1,
                status=score_result["status"],
                created_at=score_result["created_at"],
                updated_at=score_result["updated_at"],
                trace_ref_ids=[],
                evidence_ref_ids=[],
                score_type=score_result["score_type"],
                target_type=score_result["target_type"],
                target_id=score_result["target_id"],
                target_parent_type=score_result.get("target_parent_type"),
                target_parent_id=score_result.get("target_parent_id"),
                source_module=score_result.get("source_module"),
                source_event=score_result.get("source_event"),
                target_ref_id=score_result["target_id"],
                score_rule_version_id=None,
                ai_task_id=score_result.get("generated_by_task_id"),
                score_value=score_result["score_value"],
                overall_score=score_result["overall_score"],
                confidence=score_result["confidence"],
                confidence_level=score_result["confidence_level"],
                score_version=score_result["score_version"],
                rubric_version=score_result["rubric_version"],
                primary_bottleneck=score_result["primary_bottleneck"],
                next_action_type=score_result["next_action_type"],
                dimension_scores_json=list(score_result["dimension_scores"]),
                evidence_links_json=list(score_result.get("evidence_links") or []),
                generated_at=score_result["generated_at"],
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return _score_result_response(model)

    def get_score_result(self, *, owner_id: str, score_result_id: str) -> dict[str, Any] | None:
        with self.session_scope() as session:
            model = session.scalar(
                select(ScoreResult).where(
                    ScoreResult.owner_id == owner_id,
                    ScoreResult.id == score_result_id,
                )
            )
            if model is None:
                return None
            return _score_result_response(model)

    def list_score_results(
        self,
        *,
        owner_id: str,
        target_type: str | None = None,
        target_id: str | None = None,
        target_parent_type: str | None = None,
        target_parent_id: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        with self.session_scope() as session:
            query = select(ScoreResult).where(ScoreResult.owner_id == owner_id)
            if target_type is not None:
                query = query.where(ScoreResult.target_type == target_type)
            if target_id is not None:
                query = query.where(ScoreResult.target_id == target_id)
            if target_parent_type is not None:
                query = query.where(ScoreResult.target_parent_type == target_parent_type)
            if target_parent_id is not None:
                query = query.where(ScoreResult.target_parent_id == target_parent_id)
            rows = session.scalars(query.order_by(ScoreResult.created_at.asc(), ScoreResult.id.asc())).all()
            return tuple(_score_result_response(row) for row in rows)


def _score_result_response(model: ScoreResult) -> dict[str, Any]:
    return {
        "score_result_id": model.id,
        "owner_id": model.owner_id,
        "actor_id": model.actor_id,
        "status": model.status,
        "score_type": model.score_type,
        "target_type": model.target_type,
        "target_id": model.target_id,
        "target_ref": {
            "resource_type": model.target_type,
            "resource_id": model.target_id,
        },
        "target_parent_type": model.target_parent_type,
        "target_parent_id": model.target_parent_id,
        "target_parent_ref": _resource_ref(model.target_parent_type, model.target_parent_id),
        "source_module": model.source_module,
        "source_event": model.source_event,
        "score_value": model.score_value,
        "overall_score": model.overall_score,
        "score_scale": "0_100_product_scale",
        "score_version": model.score_version,
        "rubric_version": model.rubric_version,
        "validation_status": model.status,
        "confidence": model.confidence,
        "confidence_level": model.confidence_level,
        "dimension_scores": list(model.dimension_scores_json or []),
        "evidence_links": list(model.evidence_links_json or []),
        "evidence_refs": list(model.evidence_ref_ids or []),
        "trace_refs": list(model.trace_ref_ids or []),
        "primary_bottleneck": model.primary_bottleneck,
        "next_action_type": model.next_action_type,
        "generated_by_task_id": model.ai_task_id,
        "allowed_as_formal_score": True,
        "created_at": model.created_at.isoformat(),
        "updated_at": model.updated_at.isoformat(),
        "generated_at": model.generated_at.isoformat() if model.generated_at else None,
    }


def _resource_ref(resource_type: str | None, resource_id: str | None) -> dict[str, str] | None:
    if not resource_type or not resource_id:
        return None
    return {"resource_type": resource_type, "resource_id": resource_id}
