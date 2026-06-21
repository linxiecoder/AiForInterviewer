# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
# ─── How to run ───
# PYTHONPATH=apps/api python scripts/qa/seed_polish_feedback_frontend_smoke.py

from __future__ import annotations

import contextlib
import io
import json
from dataclasses import dataclass
from datetime import timedelta
from typing import Final

from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
    POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
)
from app.application.polish.ports import PolishAnswer, PolishFeedback
from app.domain.shared.clock import utc_now
from app.infrastructure.db.repositories.polish import SqlAlchemyPolishRepository
from app.infrastructure.db.session import DbSettings, build_session_factory
from scripts.qa import seed_authenticated_frontend_smoke as auth_seed


QUESTION_ID: Final = "que_auth_frontend_smoke"


@dataclass(frozen=True, slots=True)
class FeedbackSmokeState:
    answer_id: str
    feedback_id: str | None
    status: str
    answer_text: str
    feedback_text: str | None
    retryable: bool = False


def main() -> None:
    auth_seed_result = _seed_authenticated_base()
    owner_id = auth_seed_result["owner_id"]
    session_id = auth_seed_result["session_id"]
    session_factory = build_session_factory(DbSettings(database_url=auth_seed._required_smoke_database_url()))
    repository = SqlAlchemyPolishRepository(session_factory)
    now = utc_now()

    states = (
        FeedbackSmokeState(
            answer_id="ans_feedback_smoke_pending",
            feedback_id=None,
            status="pending",
            answer_text="Pending smoke answer: 等待反馈生成。",
            feedback_text=None,
        ),
        FeedbackSmokeState(
            answer_id="ans_feedback_smoke_generated",
            feedback_id="fb_feedback_smoke_generated",
            status="generated",
            answer_text="Generated smoke answer: 先说明业务目标，再解释 API 和前端验证路径。",
            feedback_text="反馈 smoke generated：先讲业务目标，再补 API 和页面证据。",
        ),
        FeedbackSmokeState(
            answer_id="ans_feedback_smoke_failed",
            feedback_id="fb_feedback_smoke_failed",
            status="generation_failed",
            answer_text="Failed smoke answer: provider unavailable path.",
            feedback_text="反馈生成失败，可重试；页面不得暴露 raw provider payload。",
            retryable=True,
        ),
    )

    for index, state in enumerate(states, start=1):
        timestamp = now + timedelta(seconds=index)
        repository.add_answer(
            PolishAnswer(
                answer_id=state.answer_id,
                owner_id=owner_id,
                actor_id=owner_id,
                session_id=session_id,
                question_id=QUESTION_ID,
                answer_round=index,
                answer_text=state.answer_text,
                status="answered",
                created_at=timestamp,
                updated_at=timestamp,
            )
        )
        if state.feedback_id is not None:
            repository.add_feedback(
                PolishFeedback(
                    feedback_id=state.feedback_id,
                    owner_id=owner_id,
                    actor_id=owner_id,
                    session_id=session_id,
                    answer_id=state.answer_id,
                    ai_task_id=f"task_{state.feedback_id}",
                    score_result_id=None,
                    feedback_summary=json.dumps(_feedback_payload(state), ensure_ascii=False),
                    status=state.status,
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )

    print(
        json.dumps(
            {
                "session_id": session_id,
                "owner_id": owner_id,
                "answers": [
                    {
                        "answer_id": state.answer_id,
                        "feedback_id": state.feedback_id,
                        "status": state.status,
                    }
                    for state in states
                ],
            },
            ensure_ascii=True,
        )
    )


def _seed_authenticated_base() -> dict[str, str]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        auth_seed.main()
    raw_result = json.loads(output.getvalue().strip())
    return {
        "session_id": str(raw_result["session_id"]),
        "owner_id": str(raw_result["owner_id"]),
    }


def _feedback_payload(state: FeedbackSmokeState) -> dict[str, str | bool | list[str] | list[dict[str, str | int]] | dict[str, str | bool | list[str]] | None]:
    base: dict[str, str | bool | list[str] | list[dict[str, str | int]] | dict[str, str | bool | list[str]] | None] = {
        "schema_id": POLISH_FEEDBACK_FINAL_SCHEMA_ID,
        "schema_version": POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
        "contract_ids": list(POLISH_FEEDBACK_FINAL_CONTRACT_IDS),
        "status": state.status,
        "feedback_id": state.feedback_id,
        "feedback_text": state.feedback_text,
        "answer_summary": "smoke answer summary",
        "low_confidence_flags": [],
        "trace_refs": [{"trace_ref_id": f"trace_{state.answer_id}", "trace_type": "smoke"}],
        "feedback_metadata": {
            "llm_called": False,
            "smoke_state": state.status,
            "retryable": state.retryable,
        },
    }
    if state.status == "generated":
        base.update(
            {
                "score_result": {"score": "82", "score_type": "polish_answer"},
                "loss_points": [{"index": 1, "summary": "缺少 API 与页面证据串联"}],
                "reference_answer": {"summary": "先讲业务目标，再补 API、页面和失败路径证据。"},
                "feedback_cards": [{"card_type": "overall", "title": "总体反馈"}],
                "next_recommended_actions": ["continue_same_question"],
            }
        )
    else:
        base.update(
            {
                "validation_errors": ["smoke_generation_failed"],
                "retryable": state.retryable,
                "next_recommended_actions": ["retry_same_question", "continue_same_question"],
            }
        )
    return base


if __name__ == "__main__":
    main()
