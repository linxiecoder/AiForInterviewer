from __future__ import annotations

from dataclasses import replace

import pytest

from app.application.polish.entities import PolishSession
from app.domain.shared.clock import utc_now
from app.infrastructure.db.repositories.polish import SqlAlchemyPolishRepository
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema


OWNER_ID = "usr_progress_stale_owner"
ACTOR_ID = "usr_progress_stale_actor"
SESSION_ID = "ses_progress_stale_guard"


def test_progress_tree_update_rejects_stale_base_version_without_overwriting_newer_state() -> None:
    repository = _repository()
    repository.add_session(_session())
    stale_session = repository.get_session(OWNER_ID, SESSION_ID)
    fresh_session = repository.get_session(OWNER_ID, SESSION_ID)
    assert stale_session is not None
    assert fresh_session is not None

    repository.update_progress_tree(
        replace(
            fresh_session,
            updated_at=utc_now(),
            progress_percent=80,
            progress_tree_state=_state(progress_percent=80),
        )
    )

    with pytest.raises(RuntimeError, match="stale_version_conflict"):
        repository.update_progress_tree(
            replace(
                stale_session,
                updated_at=utc_now(),
                progress_percent=10,
                progress_tree_state=_state(progress_percent=10),
            )
        )

    persisted = repository.get_session(OWNER_ID, SESSION_ID)
    assert persisted is not None
    assert persisted.progress_percent == 80
    assert persisted.progress_tree_state["progress"]["progress_percent"] == 80
    assert getattr(persisted, "record_version", None) == 2


def test_progress_tree_update_accepts_fresh_base_version_once_and_advances_record_version() -> None:
    repository = _repository()
    repository.add_session(_session())
    loaded = repository.get_session(OWNER_ID, SESSION_ID)
    assert loaded is not None

    repository.update_progress_tree(
        replace(
            loaded,
            updated_at=utc_now(),
            progress_percent=35,
            progress_tree_state=_state(progress_percent=35),
        )
    )

    persisted = repository.get_session(OWNER_ID, SESSION_ID)
    assert persisted is not None
    assert persisted.progress_percent == 35
    assert persisted.progress_tree_state["progress"]["progress_percent"] == 35
    assert getattr(persisted, "record_version", None) == 2


def test_session_status_update_rejects_stale_base_version_without_overwriting_newer_status() -> None:
    repository = _repository()
    repository.add_session(_session())
    stale_session = repository.get_session(OWNER_ID, SESSION_ID)
    fresh_session = repository.get_session(OWNER_ID, SESSION_ID)
    assert stale_session is not None
    assert fresh_session is not None

    repository.save_session_status(replace(fresh_session, updated_at=utc_now(), status="ended"))

    with pytest.raises(RuntimeError, match="stale_version_conflict"):
        repository.save_session_status(replace(stale_session, updated_at=utc_now(), status="deleted"))

    persisted = repository.get_session(OWNER_ID, SESSION_ID)
    assert persisted is not None
    assert persisted.status == "ended"
    assert getattr(persisted, "record_version", None) == 2


def _repository() -> SqlAlchemyPolishRepository:
    session_factory = build_session_factory(DbSettings(database_url="sqlite+pysqlite:///:memory:"))
    initialize_schema(session_factory=session_factory)
    return SqlAlchemyPolishRepository(session_factory)


def _session() -> PolishSession:
    now = utc_now()
    return PolishSession(
        session_id=SESSION_ID,
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        binding_id="bind_progress_stale_guard",
        resume_id="res_progress_stale_guard",
        resume_version_id="res_ver_progress_stale_guard",
        job_id="job_progress_stale_guard",
        job_version_id="job_ver_progress_stale_guard",
        status="running",
        topic_id="topic_technical_depth",
        subtopic_id=None,
        custom_topic_text_summary=None,
        created_at=now,
        updated_at=now,
        polish_theme="mixed",
        progress_tree_status="ready",
        progress_percent=0,
        progress_tree_plan={
            "status": "ready",
            "context_digest": "digest-progress-stale",
            "nodes": [
                {
                    "progress_node_ref": "node_progress_stale",
                    "title": "Progress stale guard",
                    "expected_capability": "Versioned progress update",
                    "children": [],
                }
            ],
        },
        progress_tree_state=_state(progress_percent=0),
    )


def _state(*, progress_percent: int) -> dict:
    return {
        "status": "ready",
        "node_states": [
            {
                "progress_node_ref": "node_progress_stale",
                "status": "in_progress" if progress_percent < 100 else "completed",
                "completed_questions_count": 0,
                "latest_feedback_summary": None,
            }
        ],
        "current_priority": {
            "progress_node_ref": "node_progress_stale",
            "title": "Progress stale guard",
            "expected_capability": "Versioned progress update",
        },
        "updated_from_turns_count": 0,
        "progress": {"progress_percent": progress_percent},
    }
