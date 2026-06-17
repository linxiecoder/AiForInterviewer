"""SQLAlchemy repository for persisted polish candidates."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from datetime import UTC, datetime
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.shared.clock import utc_now
from app.infrastructure.db.models.asset import Asset, AssetVersion
from app.infrastructure.db.models.polish_candidate import PolishCandidateRecord
from app.infrastructure.db.models.reference import UserConfirmation
from app.infrastructure.db.models.training import TrainingRecommendation
from app.infrastructure.db.models.weakness import Weakness
from app.infrastructure.db.session import get_session_factory


STATUS_CANDIDATE = "candidate"
STATUS_CONFIRMED = "confirmed"
STATUS_DISMISSED = "dismissed"
STATUS_MERGED = "merged"
STATUS_ARCHIVED = "archived"
CANDIDATE_TYPE_WEAKNESS = "weakness_candidate"
CANDIDATE_TYPE_ASSET = "asset_candidate"
CANDIDATE_TYPE_TRAINING_SUGGESTION = "training_suggestion_candidate"
CANDIDATE_TYPE_ORAL_SCRIPT = "oral_script_candidate"
CANDIDATE_TYPE_POLISHED_ANSWER = "polished_answer_candidate"
SUPPORTED_CANDIDATE_TYPES = {
    CANDIDATE_TYPE_WEAKNESS,
    CANDIDATE_TYPE_ASSET,
    CANDIDATE_TYPE_TRAINING_SUGGESTION,
    CANDIDATE_TYPE_ORAL_SCRIPT,
    CANDIDATE_TYPE_POLISHED_ANSWER,
}
ASSET_CANDIDATE_TYPES = {
    CANDIDATE_TYPE_ASSET,
    CANDIDATE_TYPE_ORAL_SCRIPT,
    CANDIDATE_TYPE_POLISHED_ANSWER,
}
FORBIDDEN_CANDIDATE_PAYLOAD_KEYS = {
    "prompt",
    "raw_prompt",
    "system_prompt",
    "completion",
    "raw_completion",
    "provider_payload",
    "raw_provider_payload",
    "provider_response",
    "raw_provider_response",
    "hidden_rubric",
    "full_evidence_text",
    "full_resume",
    "full_jd",
    "token",
    "api_key",
    "cookie",
    "secret",
    "hidden_scoring",
    "hidden_scoring_rules",
}
FORBIDDEN_CANDIDATE_VALUE_MARKERS = tuple(
    key
    for key in FORBIDDEN_CANDIDATE_PAYLOAD_KEYS
    if key
    not in {
        "api_key",
        "cookie",
        "secret",
        "token",
    }
)
FORBIDDEN_CANDIDATE_ASSIGNMENT_PATTERNS = (
    re.compile(r"api[_-]?key\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"cookie\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"token\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"secret\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"\bbearer\s+[a-z0-9._~+/=-]+", re.IGNORECASE),
)


class PolishCandidateActionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class SqlAlchemyPolishCandidateRepository:
    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()

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
                if candidate.status != STATUS_CANDIDATE:
                    raise PolishCandidateActionError(
                        "candidate_not_confirmable",
                        "Only candidate status can be confirmed",
                    )
                now = utc_now()
                previous_status = candidate.status
                candidate.status = STATUS_CONFIRMED
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
                if candidate.candidate_type == CANDIDATE_TYPE_WEAKNESS:
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
                elif candidate.candidate_type == CANDIDATE_TYPE_TRAINING_SUGGESTION:
                    formal_ref = _create_formal_training_recommendation_from_candidate(
                        session=session,
                        candidate=candidate,
                        actor_id=actor_id,
                        confirmation_ref=confirmation_ref,
                        now=now,
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
                candidate.status = STATUS_DISMISSED
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
                if target.status in {STATUS_DISMISSED, STATUS_MERGED}:
                    raise PolishCandidateActionError("invalid_merge_target", "Merge target is not active")

                now = utc_now()
                previous_status = candidate.status
                candidate.status = STATUS_MERGED
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
                candidate.status = STATUS_ARCHIVED
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
    if candidate.status != STATUS_CANDIDATE:
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


def _create_formal_training_recommendation_from_candidate(
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
    candidate_payload = dict(candidate.candidate_payload_json or {})
    recommendation_id = f"trainrec_{_stable_hash('|'.join([candidate.owner_id, candidate.candidate_id]), 24)}"
    recommendation = TrainingRecommendation(
        id=recommendation_id,
        owner_id=candidate.owner_id,
        actor_id=actor_id,
        record_version=1,
        status="confirmed",
        created_at=now,
        updated_at=now,
        trace_ref_ids=_ref_id_list(trace_refs),
        evidence_ref_ids=_ref_id_list(evidence_refs),
        normalized_topic=_normalized_title(candidate.title),
        title=candidate.title,
        summary=candidate.summary,
        reason=candidate.reason,
        confidence_level=candidate.confidence_level,
        source_refs_json=source_refs,
        evidence_refs_json=evidence_refs,
        trace_refs_json=trace_refs,
        candidate_ref_json={"resource_type": "polish_candidate", "resource_id": candidate.candidate_id},
        target_weakness_refs_json=_refs_of_type([*source_refs, *evidence_refs], {"weakness", "weakness_candidate"}),
        question_pattern=_optional_text(candidate_payload.get("question_pattern")),
        expected_answer_dimensions_json=_string_list(candidate_payload.get("expected_answer_dimensions")),
        created_from_candidate_id=candidate.candidate_id,
        user_confirmation_ref_json=confirmation_ref,
        ai_task_id=None,
        confirmation_id=confirmation_ref["resource_id"],
        dismissed_at=None,
    )
    session.add(recommendation)
    return {"resource_type": "training_recommendation", "resource_id": recommendation_id}


def _model_to_candidate_dict(model: PolishCandidateRecord) -> dict[str, Any]:
    return _safe_candidate_value(
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
        _safe_candidate_value(dict(item))
        for item in value
        if isinstance(item, dict)
    ]


def _safe_dict(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    safe = _safe_candidate_value(dict(value))
    return safe if isinstance(safe, dict) else None


def _safe_candidate_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _safe_candidate_value(item)
            for key, item in value.items()
            if not _is_forbidden_candidate_key(str(key))
        }
    if isinstance(value, list):
        return [_safe_candidate_value(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_candidate_value(item) for item in value]
    if isinstance(value, str):
        return _safe_candidate_text(value)
    return value


def _is_forbidden_candidate_key(key: str) -> bool:
    normalized = key.strip().lower()
    return normalized in FORBIDDEN_CANDIDATE_PAYLOAD_KEYS or "prompt" in normalized


def _safe_candidate_text(value: str) -> str:
    normalized = re.sub(r"[\s-]+", "_", value.lower())
    if any(marker in normalized for marker in FORBIDDEN_CANDIDATE_VALUE_MARKERS):
        return "redacted_sensitive_detail"
    if any(pattern.search(value) for pattern in FORBIDDEN_CANDIDATE_ASSIGNMENT_PATTERNS):
        return "redacted_sensitive_detail"
    return value


def _required_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _optional_text(value: Any) -> str | None:
    return _required_text(value)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


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
    if candidate_type == CANDIDATE_TYPE_ORAL_SCRIPT:
        return "oral_script"
    if candidate_type == CANDIDATE_TYPE_POLISHED_ANSWER:
        return "polished_answer"
    return "asset"


def _asset_fact_source(candidate_type: str, candidate_payload: dict[str, Any]) -> str:
    fact_source = _optional_text(candidate_payload.get("fact_source"))
    if fact_source:
        return fact_source
    if candidate_type in {CANDIDATE_TYPE_ORAL_SCRIPT, CANDIDATE_TYPE_POLISHED_ANSWER}:
        return "model_suggested_phrasing"
    return "user_fact"
