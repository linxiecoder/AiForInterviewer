from __future__ import annotations

from app.application.polish.feedback_generation_service import FeedbackGenerationService

from tests.api.test_polish_feedback_acceptance_support import (
    AcceptanceDeterministicTransport,
    acceptance_test_matrix,
    addressed_loss_point_ids,
    candidate_payload,
    context,
    dimension_scores_1_to_5,
    generate_payload,
    loss_point_ids,
    reference_answer_text,
    score_value,
)


def test_ac_001_same_question_same_answer_independent_runs_normalize_volatile_candidates() -> None:
    limits = acceptance_test_matrix["AC-001"]["threshold_pending"]
    volatile_scores = [82, 94, 76, 88, 91]
    previous_payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([candidate_payload(80)])),
        context(answer_id="answer_stability_previous_generated"),
    )
    previous_answer = {
        "answer_id": "answer_stability_previous",
        "answer_text": str(context()["answer_text"]),
        "loss_point_ids": sorted(loss_point_ids(previous_payload)),
        "score_result": {"score_value": score_value(previous_payload)},
        "generated_feedback_payload": previous_payload,
    }
    transport = AcceptanceDeterministicTransport([candidate_payload(score) for score in volatile_scores])
    service = FeedbackGenerationService(llm_transport=transport)

    payloads = [
        generate_payload(
            service,
            context(
                answer_id=f"answer_stability_{index}",
                previous_answers=[previous_answer],
            ),
        )
        for index in range(len(volatile_scores))
    ]

    score_values = [score_value(payload) for payload in payloads]
    dimension_values = [score for payload in payloads for score in dimension_scores_1_to_5(payload)]
    loss_sets = [loss_point_ids(payload) for payload in payloads]

    assert max(score_values) - min(score_values) <= limits["total_score_max_delta"], "AC-001 same_answer_stability"
    assert (
        max(dimension_values) - min(dimension_values) <= limits["dimension_score_1_to_5_max_delta"]
    ), "AC-001 same_answer_stability dimension_scores"
    assert all(losses == loss_sets[0] for losses in loss_sets), "AC-001 same_answer_stability loss_points"


def test_ac_002_improvement_trend_distinguishes_fixed_loss_points_from_regression() -> None:
    previous_loss_ids = {"lp_recovery", "lp_observability"}
    improved = generate_payload(
        FeedbackGenerationService(
            llm_transport=AcceptanceDeterministicTransport([candidate_payload(83, loss_ids=[])])
        ),
        context(
            answer_id="answer_improved",
            answer_text="我会说明异步解耦、失败恢复、幂等键、观测指标和人工介入边界。",
            previous_answers=[
                {
                    "answer_id": "answer_previous_low",
                    "covered_points": ["异步解耦"],
                    "loss_point_ids": sorted(previous_loss_ids),
                    "score_result": {"score_value": 67},
                }
            ],
        ),
    )
    improved_change = improved["answer_change_analysis"]

    assert improved_change["trend"] == "improved", "AC-002 improvement_trend positive case"
    assert improved_change["score_delta"] > 0, "AC-002 improvement_trend score_delta"
    assert previous_loss_ids <= set(improved_change["fixed_loss_points"]), "AC-002 improvement_trend fixed_loss_points"

    regressed = generate_payload(
        FeedbackGenerationService(
            llm_transport=AcceptanceDeterministicTransport([candidate_payload(72, loss_ids=sorted(previous_loss_ids))])
        ),
        context(
            answer_id="answer_regressed",
            answer_text="我主要会用 MQ 解耦。",
            previous_answers=[
                {
                    "answer_id": "answer_previous_high",
                    "covered_points": ["异步解耦", "失败恢复", "幂等键", "观测指标", "人工介入边界"],
                    "loss_point_ids": sorted(previous_loss_ids),
                    "score_result": {"score_value": 84},
                }
            ],
        ),
    )
    regressed_change = regressed["answer_change_analysis"]

    assert regressed_change["trend"] != "improved", "AC-002 improvement_trend regression counterexample"
    assert regressed_change["score_delta"] < 0, "AC-002 improvement_trend regression score_delta"


def test_ac_003_reference_answer_replay_overrides_low_candidate_replay_score() -> None:
    source_payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([candidate_payload(80)])),
        context(answer_id="answer_reference_source"),
    )
    source_loss_ids = loss_point_ids(source_payload)

    assert addressed_loss_point_ids(source_payload) == source_loss_ids, "AC-003 reference_answer_replay loss refs"

    replay_payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([candidate_payload(61, loss_ids=[])])),
        context(
            answer_id="answer_reference_replay",
            answer_text=reference_answer_text(source_payload),
            previous_answers=[
                {
                    "answer_id": "answer_reference_source",
                    "loss_point_ids": sorted(source_loss_ids),
                    "score_result": {"score_value": score_value(source_payload)},
                    "generated_feedback_payload": source_payload,
                }
            ],
        ),
    )

    assert (
        score_value(replay_payload) >= acceptance_test_matrix["AC-003"]["threshold_pending"]["replay_score_floor"]
    ), "AC-003 reference_answer_replay high_score"
    assert loss_point_ids(replay_payload).isdisjoint(source_loss_ids), "AC-003 reference_answer_replay clear_loss_points"


def test_ac_012_failed_or_invalid_generation_is_not_exposed_as_successful_feedback() -> None:
    invalid_result = FeedbackGenerationService(
        llm_transport=AcceptanceDeterministicTransport([{"feedback_text": "missing required payload"}])
    ).generate_feedback_v1(context(answer_id="answer_invalid_generation"))
    failed_result = FeedbackGenerationService(
        llm_transport=AcceptanceDeterministicTransport([candidate_payload(82)], fail_generation=True)
    ).generate_feedback_v1(context(answer_id="answer_failed_generation"))

    assert invalid_result.succeeded is False, "AC-012 validation failed must not pseudo-succeed"
    assert invalid_result.payload is None
    assert invalid_result.metadata["llm_output_validation_status"] == "invalid"
    assert failed_result.succeeded is False, "AC-012 generation failed must not pseudo-succeed"
    assert failed_result.payload is None
    assert failed_result.metadata["provider_status"] == "failed"


def test_ac_001_ac_002_ac_003_ac_012_matrix_keeps_c_049_to_c_054_deferred_open_question_guard() -> None:
    for candidate_id in ("C-049", "C-050", "C-051", "C-052", "C-053", "C-054"):
        assert acceptance_test_matrix[candidate_id]["status"] == "Deferred/Open Question"
        assert acceptance_test_matrix[candidate_id]["threshold_pending"] is True

    assert acceptance_test_matrix["OQ-007"]["threshold_pending"] is True
    assert acceptance_test_matrix["OQ-008"]["threshold_pending"] is True
