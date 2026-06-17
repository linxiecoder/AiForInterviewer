from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.api.v1.polish import _use_cases
from app.application.polish import use_cases as polish_use_cases
from app.application.polish.commands import CreatePolishAnswerCommand
from app.application.polish.entities import PolishAnswer, PolishSession
from app.domain.shared.clock import utc_now
from app.infrastructure.db.models.answer import Answer as AnswerModel
from app.infrastructure.db.repositories.polish import SqlAlchemyPolishRepository
from tests.api.test_polish_api import (
    ACTOR_A,
    OWNER_A,
    _seed_polish_question_for_session,
    _seed_polish_sources,
    _session_factory,
)
from tests.fakes.llm_transport import FakeLlmTransport


def test_answer_idempotency_key_replays_after_process_cache_loss() -> None:
    use_cases, session_factory, session_id, question_id = _create_answer_ready_session()

    first_result = use_cases.create_answer(
        _answer_command(
            session_id=session_id,
            question_id=question_id,
            answer_text="I will verify the API idempotency boundary.",
            idempotency_key="answer-replay-key-001",
        )
    )
    _simulate_process_restart_for_answer_idempotency()

    second_result = use_cases.create_answer(
        _answer_command(
            session_id=session_id,
            question_id=question_id,
            answer_text="I will verify the API idempotency boundary.",
            idempotency_key="answer-replay-key-001",
        )
    )

    assert first_result.is_success
    assert second_result.is_success
    assert second_result.value.answer_id == first_result.value.answer_id
    assert second_result.value.answer_round == 1
    assert _count_answers_for_question(session_factory, question_id) == 1


def test_answer_idempotency_key_conflict_after_process_cache_loss() -> None:
    use_cases, session_factory, session_id, question_id = _create_answer_ready_session()

    first_result = use_cases.create_answer(
        _answer_command(
            session_id=session_id,
            question_id=question_id,
            answer_text="First durable answer payload.",
            idempotency_key="answer-conflict-key-001",
        )
    )
    _simulate_process_restart_for_answer_idempotency()

    conflict_result = use_cases.create_answer(
        _answer_command(
            session_id=session_id,
            question_id=question_id,
            answer_text="Different durable answer payload.",
            idempotency_key="answer-conflict-key-001",
        )
    )

    assert first_result.is_success
    assert not conflict_result.is_success
    assert conflict_result.error.code == "idempotency_conflict"
    assert _count_answers_for_question(session_factory, question_id) == 1


def test_answer_round_is_unique_for_owner_question_at_repository_boundary() -> None:
    session_factory = _session_factory()
    repository = SqlAlchemyPolishRepository(session_factory)
    now = utc_now()
    first = _answer_entity(
        answer_id="ans_round_unique_001",
        answer_round=1,
        answer_text="first answer",
        created_at=now,
    )
    duplicate_round = _answer_entity(
        answer_id="ans_round_unique_002",
        answer_round=1,
        answer_text="duplicate round answer",
        created_at=now,
    )

    repository.add_answer(first)

    with pytest.raises(IntegrityError):
        repository.add_answer(duplicate_round)


def _create_answer_ready_session():
    session_factory = _session_factory()
    binding_id = _seed_polish_sources(session_factory, OWNER_A)
    now = utc_now()
    session_id = "ses_answer_idempotency"
    SqlAlchemyPolishRepository(session_factory).add_session(
        PolishSession(
            session_id=session_id,
            owner_id=OWNER_A,
            actor_id=ACTOR_A.actor_id,
            binding_id=binding_id,
            resume_id=f"res_polish_{OWNER_A}",
            resume_version_id=f"res_ver_polish_{OWNER_A}",
            job_id=f"job_polish_{OWNER_A}",
            job_version_id=f"job_ver_polish_{OWNER_A}",
            status="running",
            topic_id="topic_technical_depth",
            subtopic_id=None,
            custom_topic_text_summary=None,
            created_at=now,
            updated_at=now,
            polish_theme="mixed",
        )
    )
    question_id = _seed_polish_question_for_session(
        session_factory,
        session_id=session_id,
        progress_node_ref="node_answer_idempotency",
        question_id=f"que_idempotency_{session_id}",
    )
    return _use_cases(session_factory, FakeLlmTransport()), session_factory, session_id, question_id


def _answer_command(
    *,
    session_id: str,
    question_id: str,
    answer_text: str,
    idempotency_key: str,
) -> CreatePolishAnswerCommand:
    command = CreatePolishAnswerCommand(
        owner_id=OWNER_A,
        actor_id=ACTOR_A.actor_id,
        session_id=session_id,
        question_id=question_id,
        answer_text=answer_text,
    )
    object.__setattr__(command, "idempotency_key", idempotency_key)
    return command


def _simulate_process_restart_for_answer_idempotency() -> None:
    cache = getattr(polish_use_cases, "_ANSWER_IDEMPOTENCY_CACHE", None)
    if hasattr(cache, "clear"):
        cache.clear()


def _count_answers_for_question(session_factory, question_id: str) -> int:
    with session_factory() as db:
        return int(
            db.scalar(
                select(func.count())
                .select_from(AnswerModel)
                .where(
                    AnswerModel.owner_id == OWNER_A,
                    AnswerModel.question_id == question_id,
                )
            )
            or 0
        )


def _answer_entity(
    *,
    answer_id: str,
    answer_round: int,
    answer_text: str,
    created_at,
) -> PolishAnswer:
    return PolishAnswer(
        answer_id=answer_id,
        owner_id=OWNER_A,
        actor_id=ACTOR_A.actor_id,
        session_id="ses_round_unique",
        question_id="que_round_unique",
        answer_round=answer_round,
        answer_text=answer_text,
        status="saved",
        created_at=created_at,
        updated_at=created_at,
    )
