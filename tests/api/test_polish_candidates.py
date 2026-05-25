from __future__ import annotations

from datetime import UTC, datetime

from fastapi import FastAPI

from app.api.deps import get_db_session_factory, require_authenticated_actor
from app.api.errors import ApiHttpError, api_http_error_handler
from app.api.v1 import build_api_v1_router
from app.domain.auth.entities import CurrentActor
from app.infrastructure.db.models.polish_candidate import PolishCandidateRecord
from tests.api.asgi_client import call_json
from tests.api.test_polish_api import ACTOR_A, OWNER_A, _session_factory


def test_polish_candidates_list_existing_records_without_feedback_generation() -> None:
    session_factory = _session_factory()
    app = _isolated_candidates_app(session_factory, ACTOR_A)
    _seed_candidate(session_factory, owner_id=OWNER_A)

    status_code, body = call_json(app, "/api/v1/polish-candidates")

    assert status_code == 200
    assert body["resource_type"] == "polish_candidate_list"
    assert len(body["data"]) == 1
    candidate = body["data"][0]
    assert candidate["candidate_id"] == "cand_manual_existing"
    assert candidate["status"] == "candidate"
    assert candidate["candidate_type"] == "weakness_candidate"
    assert candidate["user_confirmation_required"] is True


def test_polish_candidates_response_sanitizes_existing_record_payload() -> None:
    session_factory = _session_factory()
    app = _isolated_candidates_app(session_factory, ACTOR_A)
    _seed_candidate(
        session_factory,
        owner_id=OWNER_A,
        candidate_payload={
            "safe_note": "safe value",
            "raw_prompt": "RAW_PROMPT_SHOULD_NOT_ESCAPE",
            "nested": ["api_key=sk-test-secret"],
        },
    )

    status_code, body = call_json(app, "/api/v1/polish-candidates/cand_manual_existing")

    assert status_code == 200
    payload = body["data"]["candidate_payload"]
    assert payload["safe_note"] == "safe value"
    assert "raw_prompt" not in payload
    assert payload["nested"] == ["redacted_sensitive_detail"]


def test_polish_candidates_list_is_empty_without_persisted_candidates() -> None:
    session_factory = _session_factory()
    app = _isolated_candidates_app(session_factory, ACTOR_A)

    status_code, body = call_json(app, "/api/v1/polish-candidates")

    assert status_code == 200
    assert body["data"] == []


def _isolated_candidates_app(session_factory, actor: CurrentActor) -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(ApiHttpError, api_http_error_handler)
    app.include_router(build_api_v1_router("/api/v1"))

    async def _actor_override() -> CurrentActor:
        return actor

    async def _session_factory_override():
        return session_factory

    app.dependency_overrides[require_authenticated_actor] = _actor_override
    app.dependency_overrides[get_db_session_factory] = _session_factory_override
    return app


def _seed_candidate(
    session_factory,
    *,
    owner_id: str,
    candidate_payload: dict | None = None,
) -> None:
    now = datetime(2026, 5, 26, 9, 0, tzinfo=UTC)
    with session_factory() as session:
        session.add(
            PolishCandidateRecord(
                candidate_id="cand_manual_existing",
                owner_id=owner_id,
                candidate_type="weakness_candidate",
                status="candidate",
                source_type="manual_existing_record",
                source_refs_json=[{"resource_type": "feedback", "resource_id": "trc_manual_existing"}],
                evidence_refs_json=[],
                trace_refs_json=[],
                session_id="psess_manual_existing",
                question_id="ques_manual_existing",
                answer_id="ans_manual_existing",
                feedback_id="trc_manual_existing",
                title="手动候选",
                summary="既有候选摘要",
                evidence_excerpt="既有证据",
                reason="既有候选原因",
                confidence_level="medium",
                merge_key=f"{owner_id}:manual-existing",
                merge_target_candidate_id=None,
                target_formal_ref_json=None,
                candidate_payload_json=candidate_payload or {},
                user_confirmation_required=True,
                created_at=now,
                updated_at=now,
                dismissed_at=None,
                confirmed_at=None,
                archived_at=None,
            )
        )
        session.commit()
