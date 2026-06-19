from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.application.polish.entities import PolishFeedback, PolishTaskStatus
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import AiTaskStatus
from app.domain.shared.refs import TraceRef
from app.infrastructure.db.models.ai_task import AiTask, AiTaskResult
from app.infrastructure.db.repositories.polish import SqlAlchemyPolishRepository
from tests.api.test_polish_api import ACTOR_A, OWNER_A, _session_factory


def test_feedback_task_result_persistence_rolls_back_feedback_when_task_write_fails() -> None:
    session_factory = _session_factory()
    repository = SqlAlchemyPolishRepository(session_factory)
    now = utc_now()
    duplicate_task_id = "task_feedback_atomic_duplicate"
    duplicate_result_id = f"{duplicate_task_id}_result"
    with session_factory() as db:
        db.add(
            AiTask(
                id=duplicate_task_id,
                owner_id=OWNER_A,
                actor_id=ACTOR_A.actor_id,
                record_version=1,
                status=str(AiTaskStatus.SUCCEEDED),
                trace_ref_ids=["feedback_existing"],
                evidence_ref_ids=None,
                task_type="polish_feedback_generation",
                contract_ids=["P-POLISH-005"],
                idempotency_record_id=None,
                target_ref_id="answer_atomicity_001",
                created_at=now,
                updated_at=now,
            )
        )
        db.add(
            AiTaskResult(
                id=duplicate_result_id,
                owner_id=OWNER_A,
                actor_id=ACTOR_A.actor_id,
                record_version=1,
                status=str(AiTaskStatus.SUCCEEDED),
                trace_ref_ids=["feedback_existing"],
                evidence_ref_ids=None,
                ai_task_id=duplicate_task_id,
                result_sequence="0",
                validation_result_ref_id=None,
                trace_ref_id="feedback_existing",
                result_ref_id="feedback_existing",
                created_at=now,
                updated_at=now,
            )
        )
        db.commit()

    feedback = PolishFeedback(
        feedback_id="feedback_atomicity_should_rollback",
        owner_id=OWNER_A,
        actor_id=ACTOR_A.actor_id,
        session_id="session_atomicity_001",
        answer_id="answer_atomicity_001",
        ai_task_id=duplicate_task_id,
        score_result_id=None,
        feedback_summary='{"status":"generated","feedback_text":"should rollback"}',
        status="generated",
        created_at=now,
        updated_at=now,
    )
    task = PolishTaskStatus(
        ai_task_id=duplicate_task_id,
        task_type="polish_feedback_generation",
        status=AiTaskStatus.SUCCEEDED,
        contract_ids=("P-POLISH-005",),
        retryable=False,
        result_ref=TraceRef(
            trace_ref_id=feedback.feedback_id,
            trace_type="feedback",
            created_at=now,
        ),
        user_visible_status="反馈已生成",
    )

    with pytest.raises(IntegrityError):
        repository.add_feedback_task_result(
            feedback,
            task,
            owner_id=OWNER_A,
            actor_id=ACTOR_A.actor_id,
            target_ref_id=feedback.answer_id,
        )

    with session_factory() as db:
        assert (
            db.execute(
                text("select count(*) from feedback where id = :feedback_id"),
                {"feedback_id": feedback.feedback_id},
            ).scalar_one()
            == 0
        )
        assert (
            db.execute(
                text("select count(*) from ai_task_results where ai_task_id = :task_id"),
                {"task_id": duplicate_task_id},
            ).scalar_one()
            == 1
        )
