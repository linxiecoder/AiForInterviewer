"""SQLAlchemy repository for persisted polish candidates."""

from __future__ import annotations

import hashlib
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
from app.domain.shared.clock import utc_now
from app.infrastructure.db.models.asset import Asset, AssetVersion
from app.infrastructure.db.models.polish_candidate import PolishCandidateRecord
from app.infrastructure.db.models.reference import UserConfirmation
from app.infrastructure.db.models.weakness import Weakness
from app.infrastructure.db.session import get_session_factory


CANDIDATE_PAYLOAD_FIELDS = (
    "weakness_candidates",
    "asset_candidates",
    "training_suggestion_candidates",
    "oral_script_candidates",
    "polished_answer_candidates",
)
SUPPORTED_CANDIDATE_TYPES = {item.value for item in CandidateType}
ASSET_CANDIDATE_TYPES = {
    CandidateType.ASSET.value,
    CandidateType.ORAL_SCRIPT.value,
    CandidateType.POLISHED_ANSWER.value,
}


class PolishCandidateActionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


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

    def confirm_candidate(self, *, owner_id: str, actor_id: str, candidate_id: str) -> dict[str, Any]:
        with self._session_factory() as session:
            try:
                candidate = _get_candidate_record(session, owner_id=owner_id, candidate_id=candidate_id)
                if candidate is None:
                    raise PolishCandidateActionError("not_found_or_inaccessible", "Polish candidate not found")
                if candidate.status != CandidateStatus.CANDIDATE.value:
                    raise PolishCandidateActionError(
                        "candidate_not_confirmable",
                        "Only candidate status can be confirmed",
                    )
                if candidate.candidate_type == CandidateType.TRAINING_SUGGESTION.value:
                    raise PolishCandidateActionError(
                        "unsupported_candidate_type",
                        "Training suggestion confirmation is deferred to Phase 5C",
                    )

                now = utc_now()
                previous_status = candidate.status
                candidate.status = CandidateStatus.CONFIRMED.value
                candidate.confirmed_at = now
                candidate.updated_at = now
                candidate.user_confirmation_required = False
                confirmation_ref = _create_user_confirmation_from_candidate(
                    session=session,
                    candidate=candidate,
                    actor_id=actor_id,
                    action="confirm",
                    now=now,
                    before_summary=previous_status,
                )
                asset_version_ref: dict[str, str] | None = None
                if candidate.candidate_type == CandidateType.WEAKNESS.value:
                    formal_ref = _create_formal_weakness_from_candidate(
                        session=session,
                        candidate=candidate,
                        actor_id=actor_id,
                        confirmation_ref=confirmation_ref,
                        now=now,
                    )
                elif candidate.candidate_type in ASSET_CANDIDATE_TYPES:
                    formal_ref, asset_version_ref = _create_formal_asset_from_candidate(
                        session=session,
                        candidate=candidate,
                        actor_id=actor_id,
                        confirmation_ref=confirmation_ref,
                    )
                else:
                    raise PolishCandidateActionError(
                        "unsupported_candidate_type",
                        "Candidate type cannot be confirmed in this phase",
                    )

                candidate.target_formal_ref_json = formal_ref
                session.commit()
                return _candidate_action_result(
                    action="confirm",
                    candidate=candidate,
                    formal_ref=formal_ref,
                    asset_version_ref=asset_version_ref,
                )
            except Exception:
                session.rollback()
                raise

    def dismiss_candidate(self, *, owner_id: str, actor_id: str, candidate_id: str) -> dict[str, Any]:
        with self._session_factory() as session:
            try:
                candidate = _get_confirmable_state_candidate(
                    session,
                    owner_id=owner_id,
                    candidate_id=candidate_id,
                    error_code="candidate_not_dismissable",
                    message="Only candidate status can be dismissed",
                )
                now = utc_now()
                previous_status = candidate.status
                candidate.status = CandidateStatus.DISMISSED.value
                candidate.dismissed_at = now
                candidate.updated_at = now
                candidate.user_confirmation_required = False
                _create_user_confirmation_from_candidate(
                    session=session,
                    candidate=candidate,
                    actor_id=actor_id,
                    action="dismiss",
                    now=now,
                    before_summary=previous_status,
                )
                session.commit()
                return _candidate_action_result(action="dismiss", candidate=candidate)
            except Exception:
                session.rollback()
                raise

    def merge_candidate(
        self,
        *,
        owner_id: str,
        actor_id: str,
        candidate_id: str,
        target_candidate_id: str,
    ) -> dict[str, Any]:
        with self._session_factory() as session:
            try:
                candidate = _get_confirmable_state_candidate(
                    session,
                    owner_id=owner_id,
                    candidate_id=candidate_id,
                    error_code="candidate_not_mergeable",
                    message="Only candidate status can be merged",
                )
                target = _get_candidate_record(session, owner_id=owner_id, candidate_id=target_candidate_id)
                if target is None or target.candidate_id == candidate.candidate_id:
                    raise PolishCandidateActionError("invalid_merge_target", "Merge target is invalid")
                if target.status in {CandidateStatus.DISMISSED.value, CandidateStatus.MERGED.value}:
                    raise PolishCandidateActionError("invalid_merge_target", "Merge target is not active")

                now = utc_now()
                previous_status = candidate.status
                candidate.status = CandidateStatus.MERGED.value
                candidate.merge_target_candidate_id = target.candidate_id
                candidate.updated_at = now
                candidate.user_confirmation_required = False
                _create_user_confirmation_from_candidate(
                    session=session,
                    candidate=candidate,
                    actor_id=actor_id,
                    action="merge",
                    now=now,
                    before_summary=previous_status,
                    after_summary=f"merged_into:{target.candidate_id}",
                )
                session.commit()
                return _candidate_action_result(action="merge", candidate=candidate)
            except Exception:
                session.rollback()
                raise

    def archive_candidate(self, *, owner_id: str, actor_id: str, candidate_id: str) -> dict[str, Any]:
        with self._session_factory() as session:
            try:
                candidate = _get_confirmable_state_candidate(
                    session,
                    owner_id=owner_id,
                    candidate_id=candidate_id,
                    error_code="candidate_not_archivable",
                    message="Only candidate status can be archived",
                )
                now = utc_now()
                previous_status = candidate.status
                candidate.status = CandidateStatus.ARCHIVED.value
                candidate.archived_at = now
                candidate.updated_at = now
                candidate.user_confirmation_required = False
                _create_user_confirmation_from_candidate(
                    session=session,
                    candidate=candidate,
                    actor_id=actor_id,
                    action="archive",
                    now=now,
                    before_summary=previous_status,
                )
                session.commit()
                return _candidate_action_result(action="archive", candidate=candidate)
            except Exception:
                session.rollback()
                raise


def _get_candidate_record(
    session: Session,
    *,
    owner_id: str,
    candidate_id: str,
) -> PolishCandidateRecord | None:
    return session.scalar(
        select(PolishCandidateRecord).where(
            PolishCandidateRecord.owner_id == owner_id,
            PolishCandidateRecord.candidate_id == candidate_id,
        )
    )


def _get_confirmable_state_candidate(
    session: Session,
    *,
    owner_id: str,
    candidate_id: str,
    error_code: str,
    message: str,
) -> PolishCandidateRecord:
    candidate = _get_candidate_record(session, owner_id=owner_id, candidate_id=candidate_id)
    if candidate is None:
        raise PolishCandidateActionError("not_found_or_inaccessible", "Polish candidate not found")
    if candidate.status != CandidateStatus.CANDIDATE.value:
        raise PolishCandidateActionError(error_code, message)
    return candidate


def _candidate_action_result(
    *,
    action: str,
    candidate: PolishCandidateRecord,
    formal_ref: dict[str, str] | None = None,
    asset_version_ref: dict[str, str] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "action": action,
        "candidate": _model_to_candidate_dict(candidate),
        "formal_ref": formal_ref,
    }
    if asset_version_ref is not None:
        result["asset_version_ref"] = asset_version_ref
    return result


def _create_user_confirmation_from_candidate(
    *,
    session: Session,
    candidate: PolishCandidateRecord,
    actor_id: str,
    action: str,
    now: datetime,
    before_summary: str,
    after_summary: str | None = None,
) -> dict[str, str]:
    confirmation_id = f"uc_{_stable_hash('|'.join([candidate.owner_id, candidate.candidate_id, action]), 24)}"
    confirmation = UserConfirmation(
        id=confirmation_id,
        owner_id=candidate.owner_id,
        actor_id=actor_id,
        record_version=1,
        status="recorded",
        created_at=now,
        updated_at=now,
        trace_ref_ids=_ref_id_list(candidate.trace_refs_json),
        evidence_ref_ids=_ref_id_list(candidate.evidence_refs_json),
        target_ref_id=candidate.candidate_id,
        audit_event_id=None,
        action=f"{action}_polish_candidate",
        before_summary=before_summary,
        after_summary=after_summary or action,
    )
    session.add(confirmation)
    return {"resource_type": "user_confirmation", "resource_id": confirmation_id}


def _create_formal_weakness_from_candidate(
    *,
    session: Session,
    candidate: PolishCandidateRecord,
    actor_id: str,
    confirmation_ref: dict[str, str],
    now: datetime,
) -> dict[str, str]:
    source_refs = list(candidate.source_refs_json or [])
    evidence_refs = list(candidate.evidence_refs_json or [])
    trace_refs = list(candidate.trace_refs_json or [])
    weakness_id = f"weak_{_stable_hash('|'.join([candidate.owner_id, candidate.candidate_id]), 24)}"
    weakness = Weakness(
        id=weakness_id,
        owner_id=candidate.owner_id,
        actor_id=actor_id,
        record_version=1,
        status="active",
        created_at=now,
        updated_at=now,
        trace_ref_ids=_ref_id_list(trace_refs),
        evidence_ref_ids=_ref_id_list(evidence_refs),
        normalized_title=_normalized_title(candidate.title),
        title=candidate.title,
        summary=candidate.summary,
        severity_hint=_severity_hint(candidate.confidence_level),
        confidence_level=candidate.confidence_level,
        source_refs_json=source_refs,
        session_refs_json=_refs_of_type(source_refs, {"polish_session", "session"}),
        feedback_refs_json=_refs_of_type(source_refs, {"feedback"}),
        question_refs_json=_refs_of_type(source_refs, {"question"}),
        answer_refs_json=_refs_of_type(source_refs, {"answer"}),
        loss_point_refs_json=_refs_of_type([*source_refs, *evidence_refs], {"loss_point"}),
        repeated_loss_point_refs_json=_refs_of_type([*source_refs, *evidence_refs], {"repeated_loss_point"}),
        evidence_refs_json=evidence_refs,
        trace_refs_json=trace_refs,
        created_from_candidate_id=candidate.candidate_id,
        user_confirmation_ref_json=confirmation_ref,
        occurrence_count=1,
        first_seen_at=now,
        last_seen_at=now,
        archived_at=None,
    )
    session.add(weakness)
    return {"resource_type": "weakness", "resource_id": weakness_id}


def _create_formal_asset_from_candidate(
    *,
    session: Session,
    candidate: PolishCandidateRecord,
    actor_id: str,
    confirmation_ref: dict[str, str],
) -> tuple[dict[str, str], dict[str, str]]:
    now = utc_now()
    source_refs = list(candidate.source_refs_json or [])
    evidence_refs = list(candidate.evidence_refs_json or [])
    trace_refs = list(candidate.trace_refs_json or [])
    candidate_payload = dict(candidate.candidate_payload_json or {})
    asset_id = f"asset_{_stable_hash('|'.join([candidate.owner_id, candidate.candidate_id]), 24)}"
    version_id = f"assetv_{_stable_hash('|'.join([asset_id, candidate.candidate_id, '1']), 24)}"
    content = candidate.evidence_excerpt or candidate.summary
    asset = Asset(
        id=asset_id,
        owner_id=candidate.owner_id,
        actor_id=actor_id,
        record_version=1,
        status="active",
        created_at=now,
        updated_at=now,
        trace_ref_ids=_ref_id_list(trace_refs),
        evidence_ref_ids=_ref_id_list(evidence_refs),
        normalized_title=_normalized_title(candidate.title),
        asset_type=_formal_asset_type(candidate.candidate_type),
        title=candidate.title,
        summary=candidate.summary,
        content=content,
        current_version_id=version_id,
        source_refs_json=source_refs,
        evidence_refs_json=evidence_refs,
        trace_refs_json=trace_refs,
        resume_version_ref_json=_first_ref(source_refs, {"resume_version", "resume"}),
        job_version_ref_json=_first_ref(source_refs, {"job_version", "job"}),
        question_pattern=_optional_text(candidate_payload.get("question_pattern")),
        created_from_candidate_id=candidate.candidate_id,
        user_confirmation_ref_json=confirmation_ref,
        fact_source=_asset_fact_source(candidate.candidate_type, candidate_payload),
    )
    asset_version = AssetVersion(
        id=version_id,
        owner_id=candidate.owner_id,
        actor_id=actor_id,
        record_version=1,
        status="current",
        created_at=now,
        updated_at=now,
        trace_ref_ids=_ref_id_list(trace_refs),
        evidence_ref_ids=_ref_id_list(evidence_refs),
        asset_id=asset_id,
        version_number=1,
        content=content,
        edit_summary="created_from_candidate_confirmation",
        created_by_actor_id=actor_id,
        created_from_candidate_id=candidate.candidate_id,
    )
    session.add(asset)
    session.add(asset_version)
    return (
        {"resource_type": "asset", "resource_id": asset_id},
        {"resource_type": "asset_version", "resource_id": version_id},
    )


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


def _stable_hash(value: str, size: int = 16) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:size]


def _normalized_title(value: str) -> str:
    return (value or "candidate").strip().lower()[:200] or "candidate"


def _severity_hint(confidence_level: str | None) -> str:
    if confidence_level == "high":
        return "high"
    if confidence_level == "low":
        return "low"
    return "medium"


def _ref_id_list(refs: Iterable[dict[str, Any]] | None) -> list[str]:
    ref_ids: list[str] = []
    for ref in refs or []:
        resource_id = ref.get("resource_id") or ref.get("trace_ref_id")
        if resource_id:
            ref_ids.append(str(resource_id))
    return ref_ids


def _refs_of_type(refs: Iterable[dict[str, Any]], resource_types: set[str]) -> list[dict[str, Any]]:
    return [
        dict(ref)
        for ref in refs
        if str(ref.get("resource_type") or ref.get("trace_type") or "") in resource_types
    ]


def _first_ref(refs: Iterable[dict[str, Any]], resource_types: set[str]) -> dict[str, Any] | None:
    matching = _refs_of_type(refs, resource_types)
    return matching[0] if matching else None


def _formal_asset_type(candidate_type: str) -> str:
    if candidate_type == CandidateType.ORAL_SCRIPT.value:
        return "oral_script"
    if candidate_type == CandidateType.POLISHED_ANSWER.value:
        return "polished_answer"
    return "asset"


def _asset_fact_source(candidate_type: str, candidate_payload: dict[str, Any]) -> str:
    fact_source = _optional_text(candidate_payload.get("fact_source"))
    if fact_source:
        return fact_source
    if candidate_type in {CandidateType.ORAL_SCRIPT.value, CandidateType.POLISHED_ANSWER.value}:
        return "model_suggested_phrasing"
    return "user_fact"
