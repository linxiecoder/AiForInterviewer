"""Training recommendation HTTP adapters."""

from __future__ import annotations

import hashlib
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db_session_factory, require_authenticated_actor
from app.api.envelope import success_envelope
from app.api.errors import raise_api_error
from app.domain.auth.entities import CurrentActor
from app.domain.shared.clock import utc_now
from app.infrastructure.db.models.reference import UserConfirmation
from app.infrastructure.db.models.training import TrainingRecommendation, TrainingTask


router = APIRouter(prefix="/training-suggestions", tags=["training"])


@router.get("")
async def list_training_suggestions(
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    with session_factory() as session:
        recommendations = session.scalars(
            select(TrainingRecommendation)
            .where(TrainingRecommendation.owner_id == actor.owner_id)
            .order_by(TrainingRecommendation.created_at, TrainingRecommendation.id)
        ).all()
        return success_envelope(
            resource_type="training_suggestion_list",
            data=[_recommendation_response(item) for item in recommendations],
        )


@router.post("/{recommendation_id}/dismiss")
async def dismiss_training_suggestion(
    recommendation_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    with session_factory() as session:
        recommendation = _get_recommendation(session, owner_id=actor.owner_id, recommendation_id=recommendation_id)
        if recommendation is None:
            _not_found()
        if recommendation.status not in {"confirmed", "candidate"}:
            _conflict("training_recommendation_not_dismissable", "Training recommendation cannot be dismissed.")
        now = utc_now()
        previous_status = recommendation.status
        recommendation.status = "dismissed"
        recommendation.dismissed_at = now
        recommendation.updated_at = now
        confirmation_ref = _create_training_action_confirmation(
            session=session,
            owner_id=actor.owner_id,
            actor_id=actor.actor_id,
            target_ref_id=recommendation.id,
            action="dismiss_training_recommendation",
            before_summary=previous_status,
            after_summary="dismissed",
            trace_ref_ids=recommendation.trace_ref_ids,
            evidence_ref_ids=recommendation.evidence_ref_ids,
        )
        recommendation.user_confirmation_ref_json = confirmation_ref
        session.commit()
        return success_envelope(resource_type="training_suggestion", data=_recommendation_response(recommendation))


@router.post("/{recommendation_id}/tasks")
async def start_training_task(
    recommendation_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    with session_factory() as session:
        recommendation = _get_recommendation(session, owner_id=actor.owner_id, recommendation_id=recommendation_id)
        if recommendation is None:
            _not_found()
        if recommendation.status not in {"confirmed", "completed"}:
            _conflict("training_recommendation_not_startable", "Training task requires a confirmed recommendation.")
        existing_task = session.scalar(
            select(TrainingTask).where(
                TrainingTask.owner_id == actor.owner_id,
                TrainingTask.training_recommendation_id == recommendation.id,
            )
        )
        if existing_task is not None:
            return success_envelope(resource_type="training_task", data=_task_response(existing_task))

        now = utc_now()
        task_id = f"traint_{_stable_hash('|'.join([actor.owner_id, recommendation.id]), 24)}"
        confirmation_ref = _create_training_action_confirmation(
            session=session,
            owner_id=actor.owner_id,
            actor_id=actor.actor_id,
            target_ref_id=recommendation.id,
            action="start_training_task",
            before_summary=recommendation.status,
            after_summary=f"task:{task_id}",
            trace_ref_ids=recommendation.trace_ref_ids,
            evidence_ref_ids=recommendation.evidence_ref_ids,
        )
        task = TrainingTask(
            id=task_id,
            owner_id=actor.owner_id,
            actor_id=actor.actor_id,
            record_version=1,
            status="in_progress",
            created_at=now,
            updated_at=now,
            trace_ref_ids=list(recommendation.trace_ref_ids or []),
            evidence_ref_ids=list(recommendation.evidence_ref_ids or []),
            training_recommendation_id=recommendation.id,
            title=recommendation.title,
            summary=recommendation.summary,
            target_weakness_refs_json=list(recommendation.target_weakness_refs_json or []),
            question_pattern=recommendation.question_pattern,
            expected_answer_dimensions_json=list(recommendation.expected_answer_dimensions_json or []),
            source_refs_json=list(recommendation.source_refs_json or []),
            evidence_refs_json=list(recommendation.evidence_refs_json or []),
            trace_refs_json=list(recommendation.trace_refs_json or []),
            explicit_action_ref_json=confirmation_ref,
            progress_update_hint_json=None,
            started_at=now,
            completed_at=None,
        )
        session.add(task)
        session.commit()
        return success_envelope(resource_type="training_task", data=_task_response(task))


@router.post("/{recommendation_id}/tasks/{task_id}/complete")
async def complete_training_task(
    recommendation_id: str,
    task_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    with session_factory() as session:
        recommendation = _get_recommendation(session, owner_id=actor.owner_id, recommendation_id=recommendation_id)
        if recommendation is None:
            _not_found()
        task = session.scalar(
            select(TrainingTask).where(
                TrainingTask.owner_id == actor.owner_id,
                TrainingTask.id == task_id,
                TrainingTask.training_recommendation_id == recommendation.id,
            )
        )
        if task is None:
            _not_found()
        now = utc_now()
        task.status = "completed"
        task.completed_at = now
        task.updated_at = now
        recommendation.status = "completed"
        recommendation.updated_at = now
        progress_hint = {
            "resource_type": "training_progress_hint",
            "training_task_id": task.id,
            "training_recommendation_id": recommendation.id,
            "target_weakness_refs": list(task.target_weakness_refs_json or []),
            "question_pattern": task.question_pattern,
            "expected_answer_dimensions": list(task.expected_answer_dimensions_json or []),
            "writes_formal_memory": False,
            "message": "训练完成只生成进展更新提示，不自动修改长期记忆。",
        }
        task.progress_update_hint_json = progress_hint
        session.commit()
        return success_envelope(resource_type="training_task", data=_task_response(task))


def _get_recommendation(
    session: Session,
    *,
    owner_id: str,
    recommendation_id: str,
) -> TrainingRecommendation | None:
    return session.scalar(
        select(TrainingRecommendation).where(
            TrainingRecommendation.owner_id == owner_id,
            TrainingRecommendation.id == recommendation_id,
        )
    )


def _create_training_action_confirmation(
    *,
    session: Session,
    owner_id: str,
    actor_id: str,
    target_ref_id: str,
    action: str,
    before_summary: str,
    after_summary: str,
    trace_ref_ids: list[str] | None,
    evidence_ref_ids: list[str] | None,
) -> dict[str, str]:
    confirmation_id = f"uc_{_stable_hash('|'.join([owner_id, target_ref_id, action]), 24)}"
    confirmation = UserConfirmation(
        id=confirmation_id,
        owner_id=owner_id,
        actor_id=actor_id,
        record_version=1,
        status="recorded",
        created_at=utc_now(),
        updated_at=utc_now(),
        trace_ref_ids=list(trace_ref_ids or []),
        evidence_ref_ids=list(evidence_ref_ids or []),
        target_ref_id=target_ref_id,
        audit_event_id=None,
        action=action,
        before_summary=before_summary,
        after_summary=after_summary,
    )
    session.add(confirmation)
    return {"resource_type": "user_confirmation", "resource_id": confirmation_id}


def _recommendation_response(recommendation: TrainingRecommendation) -> dict[str, Any]:
    return {
        "training_recommendation_id": recommendation.id,
        "owner_id": recommendation.owner_id,
        "status": recommendation.status,
        "title": recommendation.title,
        "summary": recommendation.summary,
        "reason": recommendation.reason,
        "confidence_level": recommendation.confidence_level,
        "source_refs": list(recommendation.source_refs_json or []),
        "evidence_refs": list(recommendation.evidence_refs_json or []),
        "trace_refs": list(recommendation.trace_refs_json or []),
        "candidate_ref": recommendation.candidate_ref_json,
        "target_weakness_refs": list(recommendation.target_weakness_refs_json or []),
        "question_pattern": recommendation.question_pattern,
        "expected_answer_dimensions": list(recommendation.expected_answer_dimensions_json or []),
        "created_from_candidate_id": recommendation.created_from_candidate_id,
        "user_confirmation_ref": recommendation.user_confirmation_ref_json,
        "created_at": recommendation.created_at.isoformat(),
        "updated_at": recommendation.updated_at.isoformat(),
    }


def _task_response(task: TrainingTask) -> dict[str, Any]:
    return {
        "training_task_id": task.id,
        "training_recommendation_id": task.training_recommendation_id,
        "owner_id": task.owner_id,
        "status": task.status,
        "title": task.title,
        "summary": task.summary,
        "target_weakness_refs": list(task.target_weakness_refs_json or []),
        "question_pattern": task.question_pattern,
        "expected_answer_dimensions": list(task.expected_answer_dimensions_json or []),
        "explicit_action_ref": task.explicit_action_ref_json,
        "progress_update_hint": task.progress_update_hint_json,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


def _not_found() -> None:
    raise_api_error(
        status_code=404,
        code="not_found_or_inaccessible",
        message="Training recommendation or task not found.",
    )


def _conflict(code: str, message: str) -> None:
    raise_api_error(status_code=409, code=code, message=message)


def _stable_hash(value: str, size: int = 16) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:size]
