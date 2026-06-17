from __future__ import annotations

from typing import Any

import pytest

from app.application.ai_runtime.business_graphs.polish_question_graph import (
    build_polish_question_persistence_plan,
)
from app.application.ai_runtime.contracts import RuntimeConflictError
from app.application.ai_runtime.handoff import AgentPersistenceHandoff
from app.application.polish.entities import PolishQuestion
from app.domain.shared.clock import utc_now


OWNER_ID = "usr_question_final_write"
ACTOR_ID = OWNER_ID
SESSION_ID = "ses_question_final_write"
NODE_REF = "progress_node_question_final_write"


def test_same_generation_intent_uses_same_final_write_key_when_final_content_changes() -> None:
    first = _plan(
        _accepted_candidate(
            candidate_ref="candidate_first",
            question_text="请说明支付链路的一致性设计。",
        )
    )
    retry_with_different_text = _plan(
        _accepted_candidate(
            candidate_ref="candidate_retry",
            question_text="请说明支付链路的幂等设计。",
        )
    )

    assert first.side_effect_key == retry_with_different_text.side_effect_key
    assert first.candidate_digest != retry_with_different_text.candidate_digest


def test_same_generation_intent_same_final_content_replays_existing_question() -> None:
    repository = _MemoryQuestionRepository()
    handoff = AgentPersistenceHandoff()
    first = _plan(_accepted_candidate(candidate_ref="candidate_first"))
    retry = _plan(_accepted_candidate(candidate_ref="candidate_retry"))

    first_result = handoff.write_question_result(first, question_repository=repository, now=utc_now())
    retry_result = handoff.write_question_result(retry, question_repository=repository, now=utc_now())

    assert len(repository.questions) == 1
    assert first_result.created is True
    assert retry_result.created is False
    assert retry_result.question.question_id == first_result.question.question_id


def test_same_generation_intent_different_final_content_conflicts() -> None:
    repository = _MemoryQuestionRepository()
    handoff = AgentPersistenceHandoff()
    first = _plan(
        _accepted_candidate(
            candidate_ref="candidate_first",
            question_text="请说明支付链路的一致性设计。",
        )
    )
    retry_with_different_text = _plan(
        _accepted_candidate(
            candidate_ref="candidate_retry",
            question_text="请说明支付链路的幂等设计。",
        )
    )

    handoff.write_question_result(first, question_repository=repository, now=utc_now())
    with pytest.raises(RuntimeConflictError, match="question final-write intent conflict"):
        handoff.write_question_result(retry_with_different_text, question_repository=repository, now=utc_now())

    assert len(repository.questions) == 1


def test_content_similar_but_different_generation_intent_is_not_deduped() -> None:
    repository = _MemoryQuestionRepository()
    handoff = AgentPersistenceHandoff()
    first = _plan(
        _accepted_candidate(
            candidate_ref="candidate_first",
            question_text="请说明支付链路的一致性设计。",
        )
    )
    different_intent = _plan(
        _accepted_candidate(
            candidate_ref="candidate_second",
            progress_node_ref="progress_node_question_final_write_second",
            question_text="请说明支付链路的一致性设计。",
            question_metadata=_request_metadata(selected_progress_node_ref="progress_node_question_final_write_second"),
        )
    )

    first_result = handoff.write_question_result(first, question_repository=repository, now=utc_now())
    second_result = handoff.write_question_result(different_intent, question_repository=repository, now=utc_now())

    assert first.side_effect_key != different_intent.side_effect_key
    assert len(repository.questions) == 2
    assert first_result.created is True
    assert second_result.created is True


def _plan(candidate: dict[str, Any]) -> Any:
    return build_polish_question_persistence_plan(
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        ai_task_id="aitask_question_final_write",
        agent_run_id="arun_question_final_write",
        candidate=candidate,
        progress_node_ref=str(candidate.get("progress_node_ref") or NODE_REF),
        trace_refs=("trace_question_final_write",),
    )


def _accepted_candidate(**overrides: Any) -> dict[str, Any]:
    metadata = overrides.pop("question_metadata", _request_metadata())
    candidate: dict[str, Any] = {
        "candidate_ref": "candidate_question_final_write",
        "question_text": "请说明支付链路的一致性设计。",
        "question_sources": (
            {
                "index": 1,
                "source_type": "resume_project",
                "title": "支付链路一致性",
                "excerpt": "我负责支付链路状态流转、幂等和失败补偿。",
                "ref_id": "resume_evidence_question_final_write",
                "availability": "available",
            },
        ),
        "progress_node_ref": NODE_REF,
        "evidence_refs": ("resume_evidence_question_final_write",),
        "context_digest": "ctx_question_final_write",
        "question_pattern": "polish_structured_experience",
        "confidence_level": "high",
        "low_confidence_flags": (),
        "question_metadata": metadata,
        "trace_refs": ("trace_question_final_write", "validation_question_final_write"),
        "quality_gate": {"status": "accepted", "passed": True, "blocking_reasons": ()},
        "sanitized": True,
    }
    candidate.update(overrides)
    return candidate


def _request_metadata(*, selected_progress_node_ref: str = NODE_REF) -> dict[str, Any]:
    return {
        "llm_generation_mode": "graph_candidate_handoff",
        "generation_mode": "new_question",
        "request_source": "explicit_selected_category",
        "selected_primary_category_ref": "primary_backend",
        "selected_secondary_category_ref": "secondary_payment",
        "selected_progress_node_ref": selected_progress_node_ref,
        "selected_category_path": ["primary_backend", "secondary_payment"],
        "parent_question_id": "",
        "parent_answer_id": "",
        "parent_feedback_id": "",
        "authorized_feedback_id": "",
        "authorized_answer_id": "",
        "authorized_parent_question_id": "",
        "exclude_question_refs": [],
        "completed_focus_refs": [],
    }


class _MemoryQuestionRepository:
    def __init__(self) -> None:
        self.questions: list[PolishQuestion] = []

    def list_questions_for_session(self, owner_id: str, session_id: str) -> tuple[PolishQuestion, ...]:
        return tuple(
            question
            for question in self.questions
            if question.owner_id == owner_id and question.session_id == session_id
        )

    def add_question(self, question: PolishQuestion) -> None:
        self.questions.append(question)

    def add_question_once(
        self,
        *,
        owner_id: str,
        session_id: str,
        graph_persistence_idempotency_key: str,
        question: PolishQuestion,
    ) -> tuple[PolishQuestion, bool]:
        existing = next(
            (
                stored
                for stored in self.questions
                if stored.owner_id == owner_id
                and stored.session_id == session_id
                and stored.question_metadata.get("graph_persistence_idempotency_key")
                == graph_persistence_idempotency_key
            ),
            None,
        )
        if existing is not None:
            return existing, False
        self.questions.append(question)
        return question, True
