"""SQLAlchemy repository for Weakness list/detail and explicit status actions."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.weaknesses.ports import WeaknessActionError, WeaknessRepository
from app.domain.shared.clock import utc_now
from app.domain.shared.refs import ResourceRef
from app.infrastructure.db.models.reference import UserConfirmation
from app.infrastructure.db.models.weakness import Weakness
from app.infrastructure.db.repositories.base import SqlAlchemyRepository
from app.infrastructure.db.session import get_session_factory


class SqlAlchemyWeaknessRepository(SqlAlchemyRepository, WeaknessRepository):
    def __init__(
        self,
        session_factory: sessionmaker[Session] | None = None,
        *,
        session: Session | None = None,
    ) -> None:
        super().__init__(session_factory, session=session)

    def get_ref(self, weakness_id: str) -> ResourceRef | None:
        with self.session_scope() as session:
            found = session.get(Weakness, weakness_id)
        if found is None:
            return None
        return ResourceRef(resource_type="weakness", resource_id=weakness_id)

    def list_weaknesses(
        self,
        *,
        owner_id: str,
        status: str | None = None,
        severity: str | None = None,
        q: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        with self.session_scope() as session:
            query = select(Weakness).where(Weakness.owner_id == owner_id)
            if status is not None:
                query = query.where(Weakness.status == status)
            if severity is not None:
                query = query.where(Weakness.severity_hint == severity)
            rows = session.scalars(query.order_by(Weakness.updated_at.desc(), Weakness.id)).all()
            filtered = _filter_weaknesses_by_query(rows, q)
            return tuple(_weakness_response(weakness) for weakness in filtered)

    def get_weakness(self, *, owner_id: str, weakness_id: str) -> dict[str, Any] | None:
        with self.session_scope() as session:
            weakness = _get_weakness(session, owner_id=owner_id, weakness_id=weakness_id)
            return _weakness_response(weakness, include_detail=True) if weakness is not None else None

    def update_status(
        self,
        *,
        owner_id: str,
        actor_id: str,
        weakness_id: str,
        status: str,
    ) -> dict[str, Any]:
        with self.session_scope() as session:
            try:
                weakness = _get_weakness(session, owner_id=owner_id, weakness_id=weakness_id)
                if weakness is None:
                    _not_found()
                now = utc_now()
                previous_status = weakness.status
                weakness.status = status
                weakness.updated_at = now
                confirmation_ref = _create_confirmation(
                    session=session,
                    owner_id=owner_id,
                    actor_id=actor_id,
                    target_ref_id=weakness.id,
                    action="update_weakness_status",
                    before_summary=previous_status,
                    after_summary=status,
                    trace_ref_ids=weakness.trace_ref_ids,
                    evidence_ref_ids=weakness.evidence_ref_ids,
                )
                weakness.user_confirmation_ref_json = confirmation_ref
                session.commit()
                return _weakness_response(weakness, include_detail=True)
            except Exception:
                session.rollback()
                raise

    @classmethod
    def clear_state(cls) -> None:
        session_factory = get_session_factory()
        with session_factory() as session:
            session.execute(delete(Weakness))
            session.commit()


def _get_weakness(session: Session, *, owner_id: str, weakness_id: str) -> Weakness | None:
    return session.scalar(select(Weakness).where(Weakness.owner_id == owner_id, Weakness.id == weakness_id))


def _weakness_response(weakness: Weakness, *, include_detail: bool = False) -> dict[str, Any]:
    response = {
        "weakness_id": weakness.id,
        "owner_id": weakness.owner_id,
        "status": weakness.status,
        "title": weakness.title,
        "summary": weakness.summary,
        "severity": weakness.severity_hint,
        "confidence_level": weakness.confidence_level,
        "dimension": _dimension_from_loss_points(weakness.loss_point_refs_json),
        "source_refs": list(weakness.source_refs_json or []),
        "evidence_refs": list(weakness.evidence_refs_json or []),
        "trace_refs": list(weakness.trace_refs_json or []),
        "occurrence_count": weakness.occurrence_count or 0,
        "first_seen_at": weakness.first_seen_at.isoformat() if weakness.first_seen_at else None,
        "last_seen_at": weakness.last_seen_at.isoformat() if weakness.last_seen_at else None,
        "archived_at": weakness.archived_at.isoformat() if weakness.archived_at else None,
        "created_from_candidate_id": weakness.created_from_candidate_id,
        "user_confirmation_ref": weakness.user_confirmation_ref_json,
        "suggested_training_actions": _suggested_training_actions(weakness.status),
        "created_at": weakness.created_at.isoformat(),
        "updated_at": weakness.updated_at.isoformat(),
    }
    if include_detail:
        response["related_refs"] = {
            "sessions": list(weakness.session_refs_json or []),
            "feedback": list(weakness.feedback_refs_json or []),
            "questions": list(weakness.question_refs_json or []),
            "answers": list(weakness.answer_refs_json or []),
            "loss_points": list(weakness.loss_point_refs_json or []),
            "repeated_loss_points": list(weakness.repeated_loss_point_refs_json or []),
        }
    return response


def _dimension_from_loss_points(raw_loss_points: list[dict[str, Any]] | None) -> str | None:
    if not raw_loss_points:
        return None
    first = raw_loss_points[0]
    value = first.get("dimension")
    return value if isinstance(value, str) else None


def _suggested_training_actions(status: str) -> list[str]:
    if status in {"resolved", "ignored"}:
        return []
    return ["enter_polish_mode", "mark_for_training"]


def _filter_weaknesses_by_query(rows: list[Weakness], q: str | None) -> list[Weakness]:
    needle = (q or "").strip().lower()
    if not needle:
        return rows
    return [weakness for weakness in rows if _weakness_search_text(weakness).find(needle) >= 0]


def _weakness_search_text(weakness: Weakness) -> str:
    values: list[str] = [
        weakness.title or "",
        weakness.summary or "",
        weakness.status or "",
        weakness.severity_hint or "",
        weakness.confidence_level or "",
        _dimension_from_loss_points(weakness.loss_point_refs_json) or "",
        " ".join(_suggested_training_actions(weakness.status)),
    ]
    values.extend(_json_ref_text(weakness.source_refs_json))
    values.extend(_json_ref_text(weakness.evidence_refs_json))
    values.extend(_json_ref_text(weakness.loss_point_refs_json))
    values.extend(_json_ref_text(weakness.repeated_loss_point_refs_json))
    return "\n".join(values).lower()


def _json_ref_text(refs: list[dict[str, Any]] | None) -> list[str]:
    values: list[str] = []
    for ref in refs or []:
        for value in ref.values():
            if isinstance(value, str):
                values.append(value)
    return values


def _create_confirmation(
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
    confirmation_id = f"uc_{uuid4().hex[:24]}"
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


def _not_found() -> None:
    raise WeaknessActionError(code="not_found_or_inaccessible", message="Weakness not found.")
