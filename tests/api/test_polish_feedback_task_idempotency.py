from __future__ import annotations

import threading
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextlib import AbstractContextManager, nullcontext

import pytest
from sqlalchemy import text

import app.api.v1.polish as polish_api
from app.application.polish import feedback_application_service as feedback_app_service
from app.application.polish.commands import CreatePolishFeedbackTaskCommand
from app.application.polish.feedback_application_service import (
    _feedback_idempotency_record_id,
    _feedback_request_body_hash,
)
from app.application.polish.feedback_generation_service import (
    FeedbackGenerationContext,
    FeedbackGenerationResult,
    FeedbackGenerationService,
)
from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
    POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
    POLISH_FEEDBACK_TASK_TYPE,
)
from app.application.llm.types import LlmTransportRequest
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import AiTaskStatus
from app.infrastructure.db.models.ai_task import AiTask, AiTaskResult
from app.infrastructure.db.repositories.polish import SqlAlchemyPolishRepository
from app.infrastructure.db.session import DbSettings, build_session_factory, initialize_schema
from tests.api.asgi_client import call_json
from tests.api.test_polish_api import (
    ACTOR_A,
    OWNER_A,
    _isolated_polish_app,
    _run_inline_threadpool,
    _session_factory,
)
from tests.api.test_polish_feedback_runtime import (
    _BlockingFeedbackTransport,
    _RecordingFeedbackTransport,
    _create_answer_ready_for_feedback,
)


def test_feedback_requires_idempotency_key_before_generation(monkeypatch) -> None:
    monkeypatch.setattr(polish_api, "run_in_threadpool", _run_inline_threadpool)
    session_factory = _session_factory()
    llm_transport = _RecordingFeedbackTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=llm_transport)
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)

    status, body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
    )

    assert status == 400
    assert body["error"]["code"] == "idempotency_required"
    assert body["error"]["details"]["field"] == "Idempotency-Key"
    assert body["error"]["retryable"] is True
    assert len(llm_transport.feedback_requests) == 0
    assert _count_rows(session_factory, "ai_tasks", "target_ref_id", answer_id) == 0
    assert _count_rows(session_factory, "feedback", "answer_id", answer_id) == 0


def test_feedback_idempotency_key_replays_task_result_without_second_generation(monkeypatch) -> None:
    monkeypatch.setattr(polish_api, "run_in_threadpool", _run_inline_threadpool)
    session_factory = _session_factory()
    llm_transport = _RecordingFeedbackTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=llm_transport)
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)

    first_status, first_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
        headers={"Idempotency-Key": "feedback-replay-key-001"},
    )
    calls_after_first_request = len(llm_transport.feedback_requests)
    second_status, second_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
        headers={"Idempotency-Key": "feedback-replay-key-001"},
    )

    assert first_status == 202
    for retired_top_level_key in ("feedback_text", "score_result", "low_confidence_flags", "trace_refs"):
        assert retired_top_level_key not in first_body["data"]
    assert first_body["data"]["summary"] == first_body["data"]["feedback_payload"]["feedback_text"]
    assert "score_ref" in first_body["data"]
    assert "loss_point_refs" in first_body["data"]
    assert second_status == 202
    for retired_top_level_key in ("feedback_text", "score_result", "low_confidence_flags", "trace_refs"):
        assert retired_top_level_key not in second_body["data"]
    assert second_body["data"]["ai_task_id"] == first_body["data"]["ai_task_id"]
    assert second_body["data"]["feedback_id"] == first_body["data"]["feedback_id"]
    assert second_body["data"]["feedback_payload"]["feedback_id"] == first_body["data"]["feedback_id"]
    assert calls_after_first_request > 0
    assert len(llm_transport.feedback_requests) == calls_after_first_request
    assert _count_rows(session_factory, "ai_tasks", "target_ref_id", answer_id) == 1
    assert _count_rows(session_factory, "feedback", "answer_id", answer_id) == 1
    assert _count_rows(session_factory, "ai_task_results", "ai_task_id", first_body["data"]["ai_task_id"]) == 1


def test_feedback_idempotency_key_conflict_rejects_different_body_without_second_write(monkeypatch) -> None:
    monkeypatch.setattr(polish_api, "run_in_threadpool", _run_inline_threadpool)
    session_factory = _session_factory()
    llm_transport = _RecordingFeedbackTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=llm_transport)
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)

    first_status, first_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
        headers={"Idempotency-Key": "feedback-conflict-key-001"},
    )
    calls_after_first_request = len(llm_transport.feedback_requests)
    conflict_status, conflict_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={
            "answer_id": answer_id,
            "scoring_context": {"rubric_version": "different-request-body"},
        },
        headers={"Idempotency-Key": "feedback-conflict-key-001"},
    )

    assert first_status == 202
    assert first_body["data"]["feedback_status"] == "generated"
    assert conflict_status == 409
    assert conflict_body["error"]["code"] == "idempotency_conflict"
    assert calls_after_first_request > 0
    assert len(llm_transport.feedback_requests) == calls_after_first_request
    assert _count_rows(session_factory, "ai_tasks", "target_ref_id", answer_id) == 1
    assert _count_rows(session_factory, "feedback", "answer_id", answer_id) == 1


def test_feedback_same_key_duplicate_requests_do_not_depend_on_process_local_lock(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    settings = DbSettings(database_url=f"sqlite+pysqlite:///{(tmp_path / 'feedback-durable.sqlite').as_posix()}")
    session_factory = build_session_factory(settings)
    initialize_schema(session_factory=session_factory)
    llm_transport = _BlockingFeedbackTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=llm_transport)
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)
    lookup_barrier = threading.Barrier(2)
    original_lookup = SqlAlchemyPolishRepository.get_feedback_task_idempotency_record

    def no_feedback_lock(
        *,
        owner_id: str,
        session_id: str,
        answer_id: str,
    ) -> AbstractContextManager[None]:
        return nullcontext()

    def synchronized_missing_lookup(
        self: SqlAlchemyPolishRepository,
        *,
        owner_id: str,
        idempotency_key: str,
        request_body_hash: str,
    ) -> dict[str, object]:
        result = original_lookup(
            self,
            owner_id=owner_id,
            idempotency_key=idempotency_key,
            request_body_hash=request_body_hash,
        )
        if result.get("status") == "missing":
            lookup_barrier.wait(timeout=2)
        return result

    monkeypatch.setattr(feedback_app_service, "_feedback_generation_lock", no_feedback_lock)
    monkeypatch.setattr(
        SqlAlchemyPolishRepository,
        "get_feedback_task_idempotency_record",
        synchronized_missing_lookup,
    )
    monkeypatch.setattr(
        FeedbackGenerationService,
        "generate_feedback_v1",
        _single_provider_feedback_generation,
    )

    def request_feedback() -> tuple[int, dict]:
        return call_json(
            app,
            f"/api/v1/polish-sessions/{session_id}/feedback",
            "POST",
            json_body={"answer_id": answer_id},
            headers={"Idempotency-Key": "feedback-durable-duplicate-001"},
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(request_feedback) for _ in range(2)]
        assert llm_transport.first_feedback_entered.wait(timeout=2)
        completed_before_release, pending_before_release = wait(
            futures,
            timeout=2,
            return_when=FIRST_COMPLETED,
        )
        assert len(completed_before_release) == 1
        assert len(pending_before_release) == 1
        duplicate_status, duplicate_body = completed_before_release.pop().result(timeout=2)
        assert duplicate_status == 202
        assert duplicate_body["data"]["status"] == "running"
        provider_generation_count_proof = llm_transport.feedback_calls
        assert provider_generation_count_proof == 1
        llm_transport.release_feedback.set()
        results = [future.result(timeout=2) for future in futures]

    assert {status for status, _body in results} == {202}
    task_ids = {body["data"]["ai_task_id"] for _status, body in results}
    assert len(task_ids) == 1
    ai_task_id = task_ids.pop()
    assert duplicate_body["data"]["ai_task_id"] == ai_task_id
    assert _count_rows(session_factory, "ai_tasks", "target_ref_id", answer_id) == 1
    assert _count_rows(session_factory, "feedback", "answer_id", answer_id) == 1
    assert _count_rows(session_factory, "ai_task_results", "ai_task_id", ai_task_id) == 1

    replay_status, replay_body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
        headers={"Idempotency-Key": "feedback-durable-duplicate-001"},
    )

    assert replay_status == 202
    assert replay_body["data"]["ai_task_id"] == ai_task_id
    assert replay_body["data"]["feedback_status"] == "generated"
    assert llm_transport.feedback_calls == 1
    assert provider_generation_count_proof == 1


def test_feedback_same_key_different_body_conflict_does_not_depend_on_process_local_lock(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    settings = DbSettings(database_url=f"sqlite+pysqlite:///{(tmp_path / 'feedback-conflict.sqlite').as_posix()}")
    session_factory = build_session_factory(settings)
    initialize_schema(session_factory=session_factory)
    llm_transport = _BlockingFeedbackTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=llm_transport)
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)
    lookup_barrier = threading.Barrier(2)
    original_lookup = SqlAlchemyPolishRepository.get_feedback_task_idempotency_record

    def no_feedback_lock(
        *,
        owner_id: str,
        session_id: str,
        answer_id: str,
    ) -> AbstractContextManager[None]:
        return nullcontext()

    def synchronized_missing_lookup(
        self: SqlAlchemyPolishRepository,
        *,
        owner_id: str,
        idempotency_key: str,
        request_body_hash: str,
    ) -> dict[str, object]:
        result = original_lookup(
            self,
            owner_id=owner_id,
            idempotency_key=idempotency_key,
            request_body_hash=request_body_hash,
        )
        if result.get("status") == "missing":
            lookup_barrier.wait(timeout=2)
        return result

    monkeypatch.setattr(feedback_app_service, "_feedback_generation_lock", no_feedback_lock)
    monkeypatch.setattr(
        SqlAlchemyPolishRepository,
        "get_feedback_task_idempotency_record",
        synchronized_missing_lookup,
    )
    monkeypatch.setattr(
        FeedbackGenerationService,
        "generate_feedback_v1",
        _single_provider_feedback_generation,
    )

    def request_feedback(json_body: dict[str, object]) -> tuple[int, dict]:
        return call_json(
            app,
            f"/api/v1/polish-sessions/{session_id}/feedback",
            "POST",
            json_body=json_body,
            headers={"Idempotency-Key": "feedback-durable-conflict-001"},
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(request_feedback, {"answer_id": answer_id}),
            executor.submit(
                request_feedback,
                {
                    "answer_id": answer_id,
                    "scoring_context": {"rubric_version": "different-request-body"},
                },
            ),
        ]
        assert llm_transport.first_feedback_entered.wait(timeout=2)
        try:
            completed_before_release, pending_before_release = wait(
                futures,
                timeout=2,
                return_when=FIRST_COMPLETED,
            )
            assert len(completed_before_release) == 1
            assert len(pending_before_release) == 1
            conflict_status, conflict_body = next(iter(completed_before_release)).result(timeout=2)
            assert conflict_status == 409
            assert conflict_body["error"]["code"] == "idempotency_conflict"
            different_body_conflict_proof = llm_transport.feedback_calls
            assert different_body_conflict_proof == 1
        finally:
            llm_transport.release_feedback.set()

        results = [future.result(timeout=2) for future in futures]

    assert sorted(status for status, _body in results) == [202, 409]
    success_body = next(body for status, body in results if status == 202)
    ai_task_id = success_body["data"]["ai_task_id"]
    assert _count_rows(session_factory, "ai_tasks", "target_ref_id", answer_id) == 1
    assert _count_rows(session_factory, "feedback", "answer_id", answer_id) == 1
    assert _count_rows(session_factory, "ai_task_results", "ai_task_id", ai_task_id) == 1
    assert llm_transport.feedback_calls == 1


def _single_provider_feedback_generation(
    self: FeedbackGenerationService,
    context: FeedbackGenerationContext,
) -> FeedbackGenerationResult:
    assert self._llm_transport is not None
    self._llm_transport.generate(
        LlmTransportRequest(
            contract_ids=POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
            task_type=POLISH_FEEDBACK_TASK_TYPE,
            input_refs=(context.answer_id,),
            evidence_bundle={
                "current_question": {"question_id": context.question_id},
                "current_answer": {"answer_id": context.answer_id},
            },
            stage="single_feedback_generation",
            thinking_enabled=False,
        )
    )
    return FeedbackGenerationResult(
        succeeded=True,
        payload=_single_provider_feedback_payload(),
        metadata={
            "provider_status": "called",
            "llm_called": True,
            "validation_stage": "single_feedback_generation",
            "stage": "single_feedback_generation",
            "generation_stages": [
                {
                    "stage": "single_feedback_generation",
                    "provider_status": "called",
                    "validation_status": "valid",
                    "thinking_enabled": False,
                }
            ],
        },
    )


def _single_provider_feedback_payload() -> dict[str, object]:
    return {
        "schema_id": POLISH_FEEDBACK_FINAL_SCHEMA_ID,
        "schema_version": POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
        "status": "generated",
        "contract_ids": list(POLISH_FEEDBACK_FINAL_CONTRACT_IDS),
        "feedback_id": "",
        "feedback_text": "Durable feedback idempotency generated one provider result.",
        "answer_summary": "Candidate answer covers idempotency, retry, and observable persistence.",
        "score_result": {
            "score_type": "polish_answer",
            "score_value": 1,
            "reasoning": "Deterministic test payload for durable idempotency.",
            "adaptive_rubric": {
                "rubric_version": "polish_answer.progress_adaptive_rubric.v1",
                "progress_state_ref": "progress_node_reliability",
                "dimensions": [],
            },
            "dimension_scores": [],
            "adaptive_insights": {
                "weak_skills": [],
                "strong_skills": [],
                "unstable_skills": [],
                "overweighted_skills": [],
                "underweighted_skills": [],
            },
            "signals": [],
            "progress_updates": [],
        },
        "loss_points": [
            {
                "loss_point_id": "lp_durable_idempotency_detail",
                "severity": "minor",
                "reason": "需要补充 durable single-writer 与 replay 边界说明。",
            }
        ],
        "reference_answer": {
            "sections": [
                {
                    "section_id": "section_durable_idempotency",
                    "title": "参考回答",
                    "content": "Use a durable task identity and replay persisted results for duplicate requests.",
                    "addresses_loss_point_ids": ["lp_durable_idempotency_detail"],
                }
            ]
        },
        "asset_consistency_check": {"status": "passed", "issues": []},
        "answer_coverage": {
            "covered_points": ["idempotency key", "retryable errors"],
            "missing_points": ["durable single-writer detail"],
        },
        "answer_change_analysis": {"status": "first_attempt", "summary": "Initial answer."},
        "feedback_cards": [
            {
                "card_id": "card_durable_idempotency",
                "title": "Durable idempotency",
                "summary": "Duplicate same-key requests replay one durable task and result.",
            }
        ],
        "next_recommended_actions": ["补充数据库幂等写入边界"],
        "low_confidence_flags": [],
        "trace_refs": ["trace_single_provider_feedback_generation"],
        "feedback_metadata": {"test_generation_mode": "single_provider"},
    }


@pytest.mark.parametrize(
    ("ai_task_id", "with_result"),
    (
        ("task_feedback_orphan_task_001", False),
        ("task_feedback_orphan_result_001", True),
    ),
)
def test_feedback_idempotency_key_orphan_state_returns_safe_retryable_error_without_generation(
    monkeypatch,
    ai_task_id: str,
    with_result: bool,
) -> None:
    monkeypatch.setattr(polish_api, "run_in_threadpool", _run_inline_threadpool)
    session_factory = _session_factory()
    llm_transport = _RecordingFeedbackTransport()
    app = _isolated_polish_app(session_factory, ACTOR_A, llm_transport=llm_transport)
    session_id, answer_id = _create_answer_ready_for_feedback(app, session_factory)
    idempotency_key = f"feedback-orphan-key-{ai_task_id}"
    command = CreatePolishFeedbackTaskCommand(
        owner_id=OWNER_A,
        actor_id=ACTOR_A.actor_id,
        session_id=session_id,
        answer_id=answer_id,
        internal_scoring_context=None,
    )
    request_body_hash = _feedback_request_body_hash(command)
    now = utc_now()

    with session_factory() as db:
        db.add(
            AiTask(
                id=ai_task_id,
                owner_id=OWNER_A,
                actor_id=ACTOR_A.actor_id,
                record_version=1,
                status=str(AiTaskStatus.SUCCEEDED),
                trace_ref_ids=[ai_task_id],
                evidence_ref_ids=None,
                task_type=POLISH_FEEDBACK_TASK_TYPE,
                contract_ids=list(POLISH_FEEDBACK_FINAL_CONTRACT_IDS),
                idempotency_record_id=_feedback_idempotency_record_id(
                    idempotency_key,
                    request_body_hash,
                ),
                target_ref_id=answer_id,
                created_at=now,
                updated_at=now,
            )
        )
        if with_result:
            db.add(
                AiTaskResult(
                    id=f"{ai_task_id}_result",
                    owner_id=OWNER_A,
                    actor_id=ACTOR_A.actor_id,
                    record_version=1,
                    status=str(AiTaskStatus.SUCCEEDED),
                    trace_ref_ids=[ai_task_id],
                    evidence_ref_ids=None,
                    ai_task_id=ai_task_id,
                    result_sequence="0",
                    validation_result_ref_id=None,
                    trace_ref_id=ai_task_id,
                    result_ref_id="missing_feedback_ref",
                    created_at=now,
                    updated_at=now,
                )
            )
        db.commit()

    status, body = call_json(
        app,
        f"/api/v1/polish-sessions/{session_id}/feedback",
        "POST",
        json_body={"answer_id": answer_id},
        headers={"Idempotency-Key": idempotency_key},
    )

    assert status == 400
    assert body["error"]["code"] == "generation_failed"
    assert body["error"]["retryable"] is True
    assert body["error"]["details"]["reason"] == "orphan_feedback_task_result"
    assert body["error"]["details"]["ai_task_id"] == ai_task_id
    assert len(llm_transport.feedback_requests) == 0
    assert _count_rows(session_factory, "feedback", "answer_id", answer_id) == 0
    assert _count_rows(session_factory, "ai_tasks", "target_ref_id", answer_id) == 1


def _count_rows(session_factory, table_name: str, column_name: str, value: str) -> int:
    with session_factory() as db:
        return int(
            db.execute(
                text(f"select count(*) from {table_name} where {column_name} = :value"),
                {"value": value},
            ).scalar_one()
        )
