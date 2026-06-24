from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.application.polish.entities import PolishAnswer, PolishFeedback, PolishQuestion, PolishSessionTurn
from app.application.polish.use_cases import _PolishUseCaseOperations, _latest_feedback_by_answer_id


OWNER_ID = "owner_effective_feedback"
ACTOR_ID = "actor_effective_feedback"
SESSION_ID = "session_effective_feedback"
QUESTION_ID = "question_effective_feedback"
BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


@dataclass(frozen=True, slots=True)
class _ProjectionRepository:
    questions: tuple[PolishQuestion, ...]
    answers: tuple[PolishAnswer, ...]
    feedbacks: tuple[PolishFeedback, ...]

    def list_questions_for_session(self, owner_id: str, session_id: str) -> tuple[PolishQuestion, ...]:
        return tuple(
            sorted(
                (
                    question
                    for question in self.questions
                    if question.owner_id == owner_id and question.session_id == session_id
                ),
                key=lambda question: (question.created_at, question.question_id),
            )
        )

    def list_answers_for_session(self, owner_id: str, session_id: str) -> tuple[PolishAnswer, ...]:
        return tuple(
            sorted(
                (
                    answer
                    for answer in self.answers
                    if answer.owner_id == owner_id and answer.session_id == session_id
                ),
                key=lambda answer: (
                    answer.question_id,
                    answer.answer_round,
                    answer.created_at,
                    answer.answer_id,
                ),
            )
        )

    def list_feedbacks_for_session(self, owner_id: str, session_id: str) -> tuple[PolishFeedback, ...]:
        return tuple(
            sorted(
                (
                    feedback
                    for feedback in self.feedbacks
                    if feedback.owner_id == owner_id and feedback.session_id == session_id
                ),
                key=lambda feedback: (feedback.answer_id, feedback.created_at, feedback.feedback_id),
            )
        )


def test_latest_failed_record_does_not_override_earlier_generated_effective_feedback() -> None:
    generated_feedback = _feedback(
        feedback_id="feedback_generated_first",
        answer_id="answer_effective",
        status="generated",
        feedback_summary=_generated_summary("旧的有效反馈仍是当前可见反馈。", score_value=82),
        created_at=_time(20),
        score_result_id="score_generated_first",
    )
    latest_failed_feedback = _feedback(
        feedback_id="feedback_generation_failed_latest",
        answer_id="answer_effective",
        status="generation_failed",
        feedback_summary=_failed_summary(),
        created_at=_time(30),
    )
    repository = _repository(
        answers=(_answer("answer_effective", answer_round=1, created_at=_time(10)),),
        feedbacks=(generated_feedback, latest_failed_feedback),
    )

    turns = _project_turns(repository)

    assert repository.list_feedbacks_for_session(OWNER_ID, SESSION_ID)[-1].feedback_id == latest_failed_feedback.feedback_id
    answer = turns[0].answers[0]
    assert answer.feedback_id == generated_feedback.feedback_id
    assert answer.score_result_id == "score_generated_first"
    assert answer.feedback_text == "旧的有效反馈仍是当前可见反馈。"
    assert answer.feedback_payload is not None
    assert answer.feedback_payload["status"] == "generated"
    assert answer.feedback_payload["score_result"] == {"score_type": "polish_answer", "score_value": 82}
    assert answer.feedback_payload["next_recommended_actions"] == ["continue_same_question"]


def test_same_question_multiple_answer_rounds_keep_order_and_independent_effective_feedback() -> None:
    answer_round_2 = _answer("answer_round_2", answer_round=2, created_at=_time(12))
    answer_round_1 = _answer("answer_round_1", answer_round=1, created_at=_time(11))
    repository = _repository(
        answers=(answer_round_2, answer_round_1),
        feedbacks=(
            _feedback(
                feedback_id="feedback_round_1_generated",
                answer_id="answer_round_1",
                status="generated",
                feedback_summary=_generated_summary("第一轮有效反馈。", score_value=71),
                created_at=_time(21),
                score_result_id="score_round_1_generated",
            ),
            _feedback(
                feedback_id="feedback_round_1_failed_latest",
                answer_id="answer_round_1",
                status="validation_failed",
                feedback_summary=_failed_summary(),
                created_at=_time(31),
            ),
            _feedback(
                feedback_id="feedback_round_2_generated",
                answer_id="answer_round_2",
                status="generated",
                feedback_summary=_generated_summary("第二轮有效反馈。", score_value=86),
                created_at=_time(22),
                score_result_id="score_round_2_generated",
            ),
        ),
    )

    turns = _project_turns(repository)

    answers = turns[0].answers
    assert [answer.answer_id for answer in answers] == ["answer_round_1", "answer_round_2"]
    assert answers[0].feedback_id == "feedback_round_1_generated"
    assert answers[0].feedback_payload is not None
    assert answers[0].feedback_payload["score_result"]["score_value"] == 71
    assert answers[1].feedback_id == "feedback_round_2_generated"
    assert answers[1].feedback_payload is not None
    assert answers[1].feedback_payload["score_result"]["score_value"] == 86


def test_legacy_json_summary_and_plain_text_feedback_can_be_effective() -> None:
    repository = _repository(
        answers=(
            _answer("answer_legacy_json", answer_round=1, created_at=_time(11)),
            _answer("answer_legacy_text", answer_round=2, created_at=_time(12)),
        ),
        feedbacks=(
            _feedback(
                feedback_id="feedback_legacy_json",
                answer_id="answer_legacy_json",
                status="generated",
                feedback_summary=_legacy_json_summary(),
                created_at=_time(21),
            ),
            _feedback(
                feedback_id="feedback_legacy_text",
                answer_id="answer_legacy_text",
                status="generated",
                feedback_summary="旧 plain text feedback 仍应展示。",
                created_at=_time(22),
            ),
        ),
    )

    turns = _project_turns(repository)

    legacy_json, legacy_text = turns[0].answers
    assert legacy_json.feedback_id == "feedback_legacy_json"
    assert legacy_json.feedback_text == "旧 JSON summary 仍应展示。"
    assert legacy_json.feedback_payload is not None
    assert legacy_json.feedback_payload["feedback_text"] == "旧 JSON summary 仍应展示。"
    assert legacy_text.feedback_id == "feedback_legacy_text"
    assert legacy_text.feedback_text == "旧 plain text feedback 仍应展示。"
    assert legacy_text.feedback_payload is not None
    assert legacy_text.feedback_payload["status"] == "generated"
    assert legacy_text.feedback_payload["feedback_text"] == "旧 plain text feedback 仍应展示。"
    assert legacy_text.feedback_payload["score_result"] is None
    assert legacy_text.feedback_payload["loss_points"] == []
    assert legacy_text.feedback_payload["reference_answer"] is None
    assert legacy_text.feedback_payload["next_recommended_actions"] == []


def test_failure_record_stays_in_history_but_not_answer_effective_payload_score_or_actions() -> None:
    failure = _feedback(
        feedback_id="feedback_only_failure",
        answer_id="answer_only_failure",
        status="timed_out",
        feedback_summary=_failed_summary(),
        created_at=_time(21),
    )
    repository = _repository(
        answers=(_answer("answer_only_failure", answer_round=1, created_at=_time(11)),),
        feedbacks=(failure,),
    )

    turns = _project_turns(repository)

    assert repository.list_feedbacks_for_session(OWNER_ID, SESSION_ID) == (failure,)
    answer = turns[0].answers[0]
    assert answer.feedback_id is None
    assert answer.score_result_id is None
    assert answer.feedback_payload is None


def test_selector_keeps_history_input_unchanged_while_effective_feedback_is_generated() -> None:
    generated = _feedback(
        feedback_id="feedback_history_generated",
        answer_id="answer_history",
        status="generated",
        feedback_summary=_generated_summary("历史中较早的 generated 才是 effective。", score_value=79),
        created_at=_time(21),
    )
    failed = _feedback(
        feedback_id="feedback_history_failed_latest",
        answer_id="answer_history",
        status="generation_failed",
        feedback_summary=_failed_summary(),
        created_at=_time(31),
    )
    history = (generated, failed)

    effective = _latest_feedback_by_answer_id(history)

    assert [feedback.feedback_id for feedback in history] == [
        "feedback_history_generated",
        "feedback_history_failed_latest",
    ]
    assert effective["answer_history"].feedback_id == "feedback_history_generated"


def _repository(
    *,
    answers: tuple[PolishAnswer, ...],
    feedbacks: tuple[PolishFeedback, ...],
) -> _ProjectionRepository:
    return _ProjectionRepository(
        questions=(_question(),),
        answers=answers,
        feedbacks=feedbacks,
    )


def _project_turns(repository: _ProjectionRepository) -> tuple[PolishSessionTurn, ...]:
    operations = _PolishUseCaseOperations.__new__(_PolishUseCaseOperations)
    operations._polish_repository = repository
    return operations._build_session_turns(OWNER_ID, SESSION_ID)


def _question() -> PolishQuestion:
    return PolishQuestion(
        question_id=QUESTION_ID,
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        ai_task_id="task_question_effective",
        question_text="请说明如何设计失败可恢复的异步链路。",
        status="generated",
        created_at=_time(1),
        updated_at=_time(1),
    )


def _answer(answer_id: str, *, answer_round: int, created_at: datetime) -> PolishAnswer:
    return PolishAnswer(
        answer_id=answer_id,
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        question_id=QUESTION_ID,
        answer_round=answer_round,
        answer_text=f"{answer_id} 的回答正文。",
        status="submitted",
        created_at=created_at,
        updated_at=created_at,
    )


def _feedback(
    *,
    feedback_id: str,
    answer_id: str,
    status: str,
    feedback_summary: str,
    created_at: datetime,
    score_result_id: str | None = None,
) -> PolishFeedback:
    return PolishFeedback(
        feedback_id=feedback_id,
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        answer_id=answer_id,
        ai_task_id=f"task_{feedback_id}",
        score_result_id=score_result_id,
        feedback_summary=feedback_summary,
        status=status,
        created_at=created_at,
        updated_at=created_at,
    )


def _generated_summary(feedback_text: str, *, score_value: int) -> str:
    return json.dumps(
        {
            "status": "generated",
            "feedback_text": feedback_text,
            "score_result": {"score_type": "polish_answer", "score_value": score_value},
            "loss_points": [],
            "reference_answer": None,
            "next_recommended_actions": ["continue_same_question"],
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _legacy_json_summary() -> str:
    return json.dumps(
        {
            "feedback_summary": "旧 JSON summary 仍应展示。",
            "loss_points": [],
            "reference_answer": None,
            "score_result": {"score_type": "polish_answer", "score_value": 75},
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _failed_summary() -> str:
    return json.dumps(
        {
            "status": "generation_failed",
            "feedback_text": "失败记录不应成为当前有效反馈。",
            "score_result": {"score_type": "polish_answer", "score_value": 1},
            "next_recommended_actions": ["retry_same_question", "continue_same_question"],
            "error": {"code": "provider_timeout"},
            "retryable": True,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _time(seconds: int) -> datetime:
    return BASE_TIME + timedelta(seconds=seconds)
