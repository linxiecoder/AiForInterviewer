"""Reserved feedback placeholder for the Polish feedback flow."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.application.polish.entities import PolishAnswer, PolishFeedback, PolishQuestion, PolishSession, PolishTaskStatus
from app.domain.shared.enums import AiTaskStatus
from app.domain.shared.refs import TraceRef


RESERVED_FEEDBACK_SCHEMA_ID = "polish_feedback_reserved_v1"
RESERVED_FEEDBACK_SCHEMA_VERSION = "1.0"
RESERVED_FEEDBACK_CONTRACT_IDS = ("P-POLISH-003",)
RESERVED_FEEDBACK_TEXT = "本阶段反馈能力已预留，暂不生成 LLM 反馈、候选项、参考答案或评分。"


@dataclass(frozen=True)
class ReservedFeedbackArtifacts:
    payload: dict[str, Any]
    feedback: PolishFeedback
    task: PolishTaskStatus


def build_reserved_feedback_artifacts(
    *,
    session: PolishSession,
    question: PolishQuestion,
    answer: PolishAnswer,
    owner_id: str,
    actor_id: str,
    task_id: str,
    feedback_id: str,
    created_at: datetime,
) -> ReservedFeedbackArtifacts:
    payload = build_reserved_feedback_payload(
        session=session,
        question=question,
        answer=answer,
        feedback_id=feedback_id,
    )
    feedback = PolishFeedback(
        feedback_id=feedback_id,
        owner_id=owner_id,
        actor_id=actor_id,
        session_id=session.session_id,
        answer_id=answer.answer_id,
        ai_task_id=task_id,
        score_result_id=None,
        feedback_summary=json.dumps(payload, ensure_ascii=False, sort_keys=True),
        status="reserved",
        created_at=created_at,
        updated_at=created_at,
    )
    task = PolishTaskStatus(
        ai_task_id=task_id,
        task_type="polish_feedback_generation",
        status=AiTaskStatus.SUCCEEDED,
        contract_ids=RESERVED_FEEDBACK_CONTRACT_IDS,
        retryable=False,
        result_ref=TraceRef(trace_ref_id=feedback_id, trace_type="feedback", created_at=created_at),
        user_visible_status="反馈能力已预留",
        score_type=None,
        candidate_refs=(),
        suggestion_refs=(),
    )
    return ReservedFeedbackArtifacts(payload=payload, feedback=feedback, task=task)


def build_reserved_feedback_payload(
    *,
    session: PolishSession,
    question: PolishQuestion,
    answer: PolishAnswer,
    feedback_id: str,
) -> dict[str, Any]:
    return {
        "schema_id": RESERVED_FEEDBACK_SCHEMA_ID,
        "schema_version": RESERVED_FEEDBACK_SCHEMA_VERSION,
        "contract_id": RESERVED_FEEDBACK_CONTRACT_IDS[0],
        "contract_ids": list(RESERVED_FEEDBACK_CONTRACT_IDS),
        "status": "reserved",
        "feedback_id": feedback_id,
        "polish_session_ref": {"resource_type": "polish_session", "resource_id": session.session_id},
        "question_ref": {"resource_type": "question", "resource_id": question.question_id},
        "answer_ref": {"resource_type": "answer", "resource_id": answer.answer_id},
        "feedback_text": RESERVED_FEEDBACK_TEXT,
        "feedback_summary": RESERVED_FEEDBACK_TEXT,
        "score_result": None,
        "score_result_ref": None,
        "loss_points": [],
        "reference_answer": None,
        "knowledge_points": [],
        "technical_principles": [],
        "next_recommended_actions": [],
        "candidate_refs": [],
        "validation_result_ref": None,
        "trace_refs": [],
        "low_confidence_flags": [],
        "user_confirmation_required": False,
        "should_continue_same_question": False,
        "should_generate_next_question": False,
        "legacy_compatibility": {"feedback_text": RESERVED_FEEDBACK_TEXT},
        "feedback_metadata": {
            "reserved": True,
            "phase": "phase_2b",
            "llm_called": False,
            "candidate_extraction_called": False,
            "reference_answer_generated": False,
            "score_result_generated": False,
        },
    }
