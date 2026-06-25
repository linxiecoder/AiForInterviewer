from __future__ import annotations

from app.application.polish.feedback_generation_service import FeedbackGenerationService

from tests.api.test_polish_feedback_acceptance_support import (
    AcceptanceDeterministicTransport,
    acceptance_test_matrix,
    candidate_payload,
    context,
    dimension_scores_1_to_5,
    generate_payload,
    loss_point_ids,
    score_value,
)


def test_ac_001_same_answer_stability_uses_five_independent_submissions() -> None:
    limits = acceptance_test_matrix["AC-001"]["threshold_pending"]
    volatile_scores = [82, 94, 76, 88, 91]
    answer_ids = [f"answer_stability_independent_{index}" for index in range(5)]
    transport = AcceptanceDeterministicTransport([candidate_payload(score) for score in volatile_scores])
    service = FeedbackGenerationService(llm_transport=transport)
    previous_payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([candidate_payload(80)])),
        context(answer_id="answer_stability_previous_generated"),
    )
    previous_answer = {
        "answer_id": "answer_stability_previous_generated",
        "answer_text": str(context()["answer_text"]),
        "loss_point_ids": sorted(loss_point_ids(previous_payload)),
        "score_result": {"score_value": score_value(previous_payload)},
        "generated_feedback_payload": previous_payload,
    }

    payloads = [
        generate_payload(service, context(answer_id=answer_id, previous_answers=[previous_answer]))
        for answer_id in answer_ids
    ]
    score_values = [score_value(payload) for payload in payloads]
    dimension_values = [score for payload in payloads for score in dimension_scores_1_to_5(payload)]

    assert len(set(answer_ids)) == 5
    assert max(score_values) - min(score_values) <= limits["total_score_max_delta"]
    assert max(dimension_values) - min(dimension_values) <= limits["dimension_score_1_to_5_max_delta"]


def test_first_round_feedback_keeps_candidate_score_without_stability_deduction() -> None:
    payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([candidate_payload(61)])),
        context(answer_id="answer_first_round_score_unchanged"),
    )

    assert score_value(payload) == 61.0
    assert payload["feedback_metadata"].get("same_answer_stability_applied") is not True
    assert payload["feedback_metadata"].get("reference_answer_replay_detected") is not True


def test_same_answer_stability_requires_historical_answer_text() -> None:
    previous_payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([candidate_payload(80)])),
        context(answer_id="answer_previous_without_text_generated"),
    )

    payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([candidate_payload(94)])),
        context(
            answer_id="answer_current_without_historical_text_match",
            previous_answers=[
                {
                    "answer_id": "answer_previous_without_text",
                    "answer_summary": str(context()["answer_text"]),
                    "loss_point_ids": sorted(loss_point_ids(previous_payload)),
                    "score_result": {"score_value": score_value(previous_payload)},
                    "generated_feedback_payload": previous_payload,
                }
            ],
        ),
    )

    assert score_value(payload) == 94.0
    assert payload["feedback_metadata"].get("same_answer_stability_applied") is not True


def test_same_answer_stability_rejects_different_historical_answer_text_with_generated_payload() -> None:
    previous_payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([candidate_payload(80)])),
        context(answer_id="answer_previous_different_text_generated"),
    )

    payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([candidate_payload(94)])),
        context(
            answer_id="answer_current_different_historical_text",
            previous_answers=[
                {
                    "answer_id": "answer_previous_different_text",
                    "answer_text": "I would only use local cache throttling and skip queue recovery details.",
                    "loss_point_ids": sorted(loss_point_ids(previous_payload)),
                    "score_result": {"score_value": score_value(previous_payload)},
                    "generated_feedback_payload": previous_payload,
                }
            ],
        ),
    )

    assert score_value(payload) == 94.0
    assert payload["feedback_metadata"].get("same_answer_stability_applied") is not True


def test_same_answer_stability_accepts_normalized_same_historical_answer_text() -> None:
    answer_text = str(context()["answer_text"])
    previous_payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([candidate_payload(80)])),
        context(answer_id="answer_previous_equivalent_text_generated"),
    )

    payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([candidate_payload(94)])),
        context(
            answer_id="answer_current_equivalent_historical_text",
            answer_text=answer_text,
            previous_answers=[
                {
                    "answer_id": "answer_previous_equivalent_text",
                    "answer_text": f"  {answer_text}  ",
                    "loss_point_ids": sorted(loss_point_ids(previous_payload)),
                    "score_result": {"score_value": score_value(previous_payload)},
                    "generated_feedback_payload": previous_payload,
                }
            ],
        ),
    )

    assert score_value(payload) == 84.0
    assert payload["feedback_metadata"].get("same_answer_stability_applied") is True
