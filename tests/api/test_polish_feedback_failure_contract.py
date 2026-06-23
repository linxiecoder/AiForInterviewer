from __future__ import annotations

import json

import pytest
from sqlalchemy import text

import app.api.v1.polish as polish_api
from app.application.polish.entities import PolishFeedback, PolishTaskStatus
from app.application.polish.feedback_application_service import (
    _existing_feedback_task,
    _failed_feedback_payload_for_storage,
)
from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
    POLISH_FEEDBACK_TASK_TYPE,
)
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import AiTaskStatus
from app.domain.shared.refs import TraceRef
from app.infrastructure.db.models.ai_task import AiTask, AiTaskResult
from app.infrastructure.db.repositories.polish import SqlAlchemyPolishRepository
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema


def _serialized(payload: object) -> str:
    return json.dumps(payload, default=str, ensure_ascii=False, sort_keys=True)


def test_failed_feedback_payload_contract_is_retryable_and_sanitized() -> None:
    payload = _failed_feedback_payload_for_storage(
        session_id="ses_failed_contract",
        question_id="que_failed_contract",
        answer_id="ans_failed_contract",
        feedback_id="fb_failed_contract",
        validation_errors=("llm_transport_generation_failed",),
        metadata={
            "provider_status": "failed",
            "llm_called": True,
            "provider_payload": {"secret": "provider_payload_should_not_render"},
            "raw_prompt": "raw_prompt_should_not_render",
            "raw_completion": "raw_completion_should_not_render",
            "raw_provider": "raw_provider_should_not_render",
        },
    )
    serialized = _serialized(payload)

    assert payload["status"] == "generation_failed"
    assert payload["retryable"] is True
    assert payload["user_visible_status"] == "反馈生成失败，可重试"
    assert payload["error"]["code"] == "llm_transport_generation_failed"
    assert payload["next_recommended_actions"] == ["retry_same_question", "continue_same_question"]
    assert payload["feedback_metadata"]["provider_status"] == "failed"
    assert payload["feedback_metadata"]["llm_called"] is True
    for forbidden in (
        "provider_payload_should_not_render",
        "raw_prompt_should_not_render",
        "raw_completion_should_not_render",
        "raw_provider_should_not_render",
    ):
        assert forbidden not in serialized


def test_feedback_generation_failed_task_response_aligns_status_and_display_contract() -> None:
    now = utc_now()
    task = PolishTaskStatus(
        ai_task_id="task_feedback_failed_contract",
        task_type="polish_feedback_generation",
        status=AiTaskStatus.GENERATION_FAILED,
        contract_ids=("P-POLISH-005",),
        retryable=True,
        result_ref=TraceRef(
            trace_ref_id="task_feedback_failed_contract",
            trace_type="validation_result",
            created_at=now,
        ),
        user_visible_status="反馈生成失败，可重试",
        validation_errors=("llm_transport_generation_failed",),
    )

    payload = polish_api._task_response(task)
    serialized = _serialized(payload)

    assert payload["status"] == AiTaskStatus.GENERATION_FAILED
    assert payload["retryable"] is True
    assert payload["user_visible_status"] == "反馈生成失败，可重试"
    assert payload["validation_errors"] == ["llm_transport_generation_failed"]
    assert "provider_payload" not in payload
    assert "raw_prompt" not in serialized
    assert "raw_completion" not in serialized
    assert "raw_provider" not in serialized


@pytest.mark.parametrize(
    ("status", "retryable", "visible_status"),
    (
        (AiTaskStatus.CANCELLED, False, "反馈生成已取消"),
        (AiTaskStatus.TIMED_OUT, True, "反馈生成超时，可重试"),
    ),
)
def test_terminal_feedback_replay_keeps_cancelled_and_deadline_status(
    status: AiTaskStatus,
    retryable: bool,
    visible_status: str,
) -> None:
    now = utc_now()
    feedback = PolishFeedback(
        feedback_id=f"fb_terminal_{status.value}",
        owner_id="owner_terminal_feedback",
        actor_id="actor_terminal_feedback",
        session_id="ses_terminal_feedback",
        answer_id="ans_terminal_feedback",
        ai_task_id=f"task_terminal_{status.value}",
        score_result_id=None,
        feedback_summary=json.dumps(
            {
                "status": status.value,
                "retryable": retryable,
                "user_visible_status": visible_status,
                "validation_errors": [f"feedback_generation_{status.value}"],
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        status=status.value,
        created_at=now,
        updated_at=now,
    )

    task = _existing_feedback_task(feedback)

    assert task.status == status
    assert task.retryable is retryable
    assert task.user_visible_status == visible_status
    assert task.validation_errors == (f"feedback_generation_{status.value}",)


@pytest.mark.parametrize(
    ("stored_status", "timeout_expired", "expected_status"),
    (
        (AiTaskStatus.CANCELLED, False, AiTaskStatus.CANCELLED),
        (AiTaskStatus.TIMED_OUT, False, AiTaskStatus.TIMED_OUT),
        (AiTaskStatus.RUNNING, True, AiTaskStatus.TIMED_OUT),
    ),
)
def test_late_provider_write_cannot_overwrite_cancelled_or_deadline_task(
    tmp_path,
    stored_status: AiTaskStatus,
    timeout_expired: bool,
    expected_status: AiTaskStatus,
) -> None:
    settings = DbSettings(
        database_url=f"sqlite+pysqlite:///{(tmp_path / 'late-write.sqlite').as_posix()}"
    )
    session_factory = build_session_factory(settings)
    initialize_schema(session_factory=session_factory)
    repository = SqlAlchemyPolishRepository(session_factory)
    now = utc_now()
    ai_task_id = f"task_late_write_{stored_status.value}_{expected_status.value}"
    idempotency_record_id = f"polish_feedback:late_write_{stored_status.value}:body"
    answer_id = f"ans_late_write_{stored_status.value}"

    with session_factory() as db:
        db.add(
            AiTask(
                id=ai_task_id,
                owner_id="owner_late_write",
                actor_id="actor_late_write",
                record_version=1,
                status=stored_status.value,
                trace_ref_ids=[ai_task_id],
                evidence_ref_ids=None,
                task_type=POLISH_FEEDBACK_TASK_TYPE,
                contract_ids=list(POLISH_FEEDBACK_FINAL_CONTRACT_IDS),
                idempotency_record_id=idempotency_record_id,
                target_ref_id=answer_id,
                timeout_at=now if timeout_expired else None,
                created_at=now,
                updated_at=now,
            )
        )
        if stored_status in {AiTaskStatus.CANCELLED, AiTaskStatus.TIMED_OUT}:
            db.add(
                AiTaskResult(
                    id=f"{ai_task_id}_result",
                    owner_id="owner_late_write",
                    actor_id="actor_late_write",
                    record_version=1,
                    status=stored_status.value,
                    trace_ref_ids=[ai_task_id],
                    evidence_ref_ids=None,
                    ai_task_id=ai_task_id,
                    result_sequence="0",
                    validation_result_ref_id=ai_task_id,
                    trace_ref_id=ai_task_id,
                    result_ref_id=None,
                    created_at=now,
                    updated_at=now,
                    safe_summary_json={
                        "status": stored_status.value,
                        "retryable": stored_status == AiTaskStatus.TIMED_OUT,
                    },
                )
            )
        db.commit()

    repository.add_feedback_task_result(
        PolishFeedback(
            feedback_id=f"fb_late_generated_{stored_status.value}",
            owner_id="owner_late_write",
            actor_id="actor_late_write",
            session_id="ses_late_write",
            answer_id=answer_id,
            ai_task_id=ai_task_id,
            score_result_id=None,
            feedback_summary=json.dumps({"status": "generated", "feedback_text": "late generated"}),
            status="generated",
            created_at=now,
            updated_at=now,
        ),
        PolishTaskStatus(
            ai_task_id=ai_task_id,
            task_type=POLISH_FEEDBACK_TASK_TYPE,
            status=AiTaskStatus.SUCCEEDED,
            contract_ids=POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
            retryable=False,
            result_ref=TraceRef(
                trace_ref_id=f"fb_late_generated_{stored_status.value}",
                trace_type="feedback",
                created_at=now,
            ),
            user_visible_status="反馈已生成",
        ),
        owner_id="owner_late_write",
        actor_id="actor_late_write",
        target_ref_id=answer_id,
        idempotency_record_id=idempotency_record_id,
    )

    with session_factory() as db:
        stored_task = db.get(AiTask, ai_task_id)
        stored_result = db.get(AiTaskResult, f"{ai_task_id}_result")
        generated_feedback_count = db.execute(
            text("select count(*) from feedback where ai_task_id = :ai_task_id and status = 'generated'"),
            {"ai_task_id": ai_task_id},
        ).scalar_one()

    assert stored_task is not None
    assert stored_task.status == expected_status.value
    assert stored_result is not None
    assert stored_result.status == expected_status.value
    assert generated_feedback_count == 0
