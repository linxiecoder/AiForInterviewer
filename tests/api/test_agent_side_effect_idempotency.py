from __future__ import annotations

import inspect

import pytest

from app.infrastructure.db.repositories.ai_runtime import (
    AgentRunRepository,
    AgentSideEffectRepository,
    IdempotencyConflict,
)
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema


OWNER_A = "owner_a"


def test_side_effect_repository_records_inert_pending_write_idempotently() -> None:
    session_factory = _session_factory()
    run = _create_run(session_factory)
    repository = AgentSideEffectRepository(session_factory)

    first = repository.record_pending_write(
        owner_id=OWNER_A,
        agent_run_id=run["id"],
        side_effect_key_hash="side_key_1",
        body_digest="sha256:body",
        target_kind="question_candidate",
        target_ref_id="candidate_ref_1",
    )
    repeated = repository.record_pending_write(
        owner_id=OWNER_A,
        agent_run_id=run["id"],
        side_effect_key_hash="side_key_1",
        body_digest="sha256:body",
        target_kind="question_candidate",
        target_ref_id="candidate_ref_1",
    )

    assert first["pending_write_ref_id"].startswith("apw_")
    assert repeated == first
    stored_run = AgentRunRepository(session_factory).get_run_for_owner(OWNER_A, run["id"])
    assert stored_run["pending_writes_json"] == [first]


def test_side_effect_repository_conflicts_on_same_key_with_different_digest() -> None:
    session_factory = _session_factory()
    run = _create_run(session_factory)
    repository = AgentSideEffectRepository(session_factory)
    repository.record_pending_write(
        owner_id=OWNER_A,
        agent_run_id=run["id"],
        side_effect_key_hash="side_key_1",
        body_digest="sha256:body",
        target_kind="question_candidate",
        target_ref_id="candidate_ref_1",
    )

    with pytest.raises(IdempotencyConflict):
        repository.record_pending_write(
            owner_id=OWNER_A,
            agent_run_id=run["id"],
            side_effect_key_hash="side_key_1",
            body_digest="sha256:different",
            target_kind="question_candidate",
            target_ref_id="candidate_ref_1",
        )


def test_pr2_side_effect_repository_has_no_formal_business_write_methods() -> None:
    source = inspect.getsource(AgentSideEffectRepository)

    assert not hasattr(AgentSideEffectRepository, "persist_question_once")
    assert not hasattr(AgentSideEffectRepository, "persist_feedback_once")
    assert not hasattr(AgentSideEffectRepository, "persist_report_once")
    assert not hasattr(AgentSideEffectRepository, "persist_candidate_once")
    assert "Question" not in source
    assert "Feedback" not in source
    assert "InterviewReport" not in source
    assert "PolishCandidateRecord" not in source


def _create_run(session_factory):
    return AgentRunRepository(session_factory).create_run(
        owner_id=OWNER_A,
        actor_id="actor_a",
        ai_task_id="task_side_effect",
        graph_name="polish",
        graph_version="v1",
        entrypoint_name="start",
        thread_id="thread_side_effect",
        idempotency_key_hash="idem_side_effect",
    )


def _session_factory():
    factory = build_session_factory(DbSettings(database_url="sqlite+pysqlite:///:memory:"))
    initialize_schema(session_factory=factory)
    return factory
