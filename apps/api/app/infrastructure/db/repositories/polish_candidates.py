"""SQLAlchemy repository for persisted polish candidates."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.application.polish.candidates import (
    CandidateStatus,
    CandidateType,
    normalize_candidate_payload,
)
from app.infrastructure.db.models.polish_candidate import PolishCandidateRecord
from app.infrastructure.db.session import get_session_factory


CANDIDATE_PAYLOAD_FIELDS = (
    "weakness_candidates",
    "asset_candidates",
    "training_suggestion_candidates",
    "oral_script_candidates",
    "polished_answer_candidates",
)
SUPPORTED_CANDIDATE_TYPES = {item.value for item in CandidateType}


class SqlAlchemyPolishCandidateRepository:
    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()

    def upsert_from_feedback_payload(
        self,
        owner_id: str,
        feedback_payload: dict[str, Any],
    ) -> tuple[dict[str, Any], ...]:
        candidates = list(candidate_payloads_from_feedback_payload(feedback_payload))
        if not candidates:
            return ()

        persisted: list[dict[str, Any]] = []
        seen_merge_keys: set[str] = set()
        with self._session_factory() as session:
            for candidate in candidates:
                candidate_model = _candidate_dict_to_model(owner_id, candidate)
                if candidate_model is None:
                    continue
                if candidate_model.merge_key in seen_merge_keys:
                    continue
                seen_merge_keys.add(candidate_model.merge_key)
                existing = session.scalar(
                    select(PolishCandidateRecord).where(
                        PolishCandidateRecord.owner_id == owner_id,
                        PolishCandidateRecord.merge_key == candidate_model.merge_key,
                    )
                )
                if existing is not None:
                    persisted.append(_model_to_candidate_dict(existing))
                    continue
                session.add(candidate_model)
                persisted.append(_model_to_candidate_dict(candidate_model))
            session.commit()
        return tuple(persisted)

    def list_candidates(
        self,
        *,
        owner_id: str,
        status: str | None = None,
        candidate_type: str | None = None,
        session_id: str | None = None,
        source_type: str | None = None,
        confidence_level: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[dict[str, Any], ...]:
        with self._session_factory() as session:
            statement = select(PolishCandidateRecord).where(PolishCandidateRecord.owner_id == owner_id)
            if status:
                statement = statement.where(PolishCandidateRecord.status == status)
            if candidate_type:
                statement = statement.where(PolishCandidateRecord.candidate_type == candidate_type)
            if session_id:
                statement = statement.where(PolishCandidateRecord.session_id == session_id)
            if source_type:
                statement = statement.where(PolishCandidateRecord.source_type == source_type)
            if confidence_level:
                statement = statement.where(PolishCandidateRecord.confidence_level == confidence_level)
            rows = session.scalars(
                statement.order_by(PolishCandidateRecord.created_at, PolishCandidateRecord.candidate_id)
                .offset(max(offset, 0))
                .limit(max(min(limit, 100), 1))
            ).all()
            return tuple(_model_to_candidate_dict(row) for row in rows)

    def get_candidate(self, *, owner_id: str, candidate_id: str) -> dict[str, Any] | None:
        with self._session_factory() as session:
            row = session.scalar(
                select(PolishCandidateRecord).where(
                    PolishCandidateRecord.owner_id == owner_id,
                    PolishCandidateRecord.candidate_id == candidate_id,
                )
            )
            if row is None:
                return None
            return _model_to_candidate_dict(row)


def candidate_payloads_from_feedback_payload(feedback_payload: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    candidates: list[dict[str, Any]] = []
    for field_name in CANDIDATE_PAYLOAD_FIELDS:
        value = feedback_payload.get(field_name)
        if not isinstance(value, list):
            continue
        candidates.extend(item for item in value if isinstance(item, dict))
    return tuple(candidates)


def _candidate_dict_to_model(owner_id: str, candidate: dict[str, Any]) -> PolishCandidateRecord | None:
    candidate_id = _required_text(candidate.get("candidate_id"))
    candidate_type = _required_text(candidate.get("candidate_type"))
    merge_key = _required_text(candidate.get("merge_key"))
    if candidate_id is None or merge_key is None or candidate_type not in SUPPORTED_CANDIDATE_TYPES:
        return None

    status = _required_text(candidate.get("status")) or CandidateStatus.CANDIDATE.value
    if status != CandidateStatus.CANDIDATE.value:
        return None

    return PolishCandidateRecord(
        candidate_id=candidate_id,
        owner_id=owner_id,
        candidate_type=candidate_type,
        status=status,
        source_type=_required_text(candidate.get("source_type")) or "structured_feedback",
        source_refs_json=_safe_ref_list(candidate.get("source_refs")),
        evidence_refs_json=_safe_ref_list(candidate.get("evidence_refs")),
        trace_refs_json=_safe_ref_list(candidate.get("trace_refs")),
        session_id=_required_text(candidate.get("session_id")) or "",
        question_id=_required_text(candidate.get("question_id")) or "",
        answer_id=_required_text(candidate.get("answer_id")) or "",
        feedback_id=_required_text(candidate.get("feedback_id")) or "",
        title=_required_text(candidate.get("title")) or "候选对象",
        summary=_required_text(candidate.get("summary")) or "",
        evidence_excerpt=_required_text(candidate.get("evidence_excerpt")) or "",
        reason=_required_text(candidate.get("reason")) or "",
        confidence_level=_required_text(candidate.get("confidence_level")) or "medium",
        merge_key=merge_key,
        merge_target_candidate_id=_optional_text(candidate.get("merge_target_candidate_id")),
        target_formal_ref_json=_safe_dict(candidate.get("target_formal_ref")),
        candidate_payload_json=_safe_dict(candidate.get("candidate_payload")) or {},
        user_confirmation_required=bool(candidate.get("user_confirmation_required", True)),
        created_at=_parse_datetime(candidate.get("created_at")),
        updated_at=_parse_datetime(candidate.get("updated_at")),
        dismissed_at=_parse_optional_datetime(candidate.get("dismissed_at")),
        confirmed_at=_parse_optional_datetime(candidate.get("confirmed_at")),
        archived_at=_parse_optional_datetime(candidate.get("archived_at")),
    )


def _model_to_candidate_dict(model: PolishCandidateRecord) -> dict[str, Any]:
    return normalize_candidate_payload(
        {
            "candidate_id": model.candidate_id,
            "owner_id": model.owner_id,
            "candidate_type": model.candidate_type,
            "status": model.status,
            "source_type": model.source_type,
            "source_refs": list(model.source_refs_json or []),
            "evidence_refs": list(model.evidence_refs_json or []),
            "trace_refs": list(model.trace_refs_json or []),
            "session_id": model.session_id,
            "question_id": model.question_id,
            "answer_id": model.answer_id,
            "feedback_id": model.feedback_id,
            "title": model.title,
            "summary": model.summary,
            "evidence_excerpt": model.evidence_excerpt,
            "reason": model.reason,
            "confidence_level": model.confidence_level,
            "merge_key": model.merge_key,
            "merge_target_candidate_id": model.merge_target_candidate_id,
            "target_formal_ref": model.target_formal_ref_json,
            "candidate_payload": dict(model.candidate_payload_json or {}),
            "user_confirmation_required": model.user_confirmation_required,
            "created_at": _isoformat(model.created_at),
            "updated_at": _isoformat(model.updated_at),
            "dismissed_at": _optional_isoformat(model.dismissed_at),
            "confirmed_at": _optional_isoformat(model.confirmed_at),
            "archived_at": _optional_isoformat(model.archived_at),
        }
    )


def _safe_ref_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, dict)):
        return []
    return [
        normalize_candidate_payload(dict(item))
        for item in value
        if isinstance(item, dict)
    ]


def _safe_dict(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return normalize_candidate_payload(dict(value))


def _required_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _optional_text(value: Any) -> str | None:
    return _required_text(value)


def _parse_datetime(value: Any) -> datetime:
    parsed = _parse_optional_datetime(value)
    return parsed or datetime.now(UTC)


def _parse_optional_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        return parsed
    return None


def _isoformat(value: datetime) -> str:
    return value.isoformat()


def _optional_isoformat(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None
