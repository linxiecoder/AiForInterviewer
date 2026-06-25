from __future__ import annotations

import pytest

from app.application.polish.feedback_generation_service import FeedbackGenerationService
from app.application.polish.feedback_stability import apply_step4_stability_controls

from tests.api.test_polish_feedback_acceptance_support import (
    AcceptanceDeterministicTransport,
    acceptance_test_matrix,
    addressed_loss_point_ids,
    candidate_payload,
    context,
    generate_payload,
    loss_point_ids,
    reference_answer_text,
    score_value,
)


def _direct_replay_context(*, answer_text: str = "alpha beta gamma delta epsilon") -> dict[str, object]:
    reference_section = {
        "section_id": "ref_direct",
        "content": "alpha beta gamma delta epsilon",
        "addresses_loss_point_ids": ["lp_direct"],
    }
    historical_payload = {
        "status": "generated",
        "score_result": {"score_value": 80.0},
        "loss_points": [{"loss_point_id": "lp_direct", "deduction": 8.0, "reason": reference_section["content"]}],
        "reference_answer": {"sections": [reference_section]},
    }
    return {
        "_step4_raw_answer_text": answer_text,
        "answer_text": answer_text,
        "question_metadata": {"expected_answer_dimensions": []},
        "same_question_answers": [
            {
                "answer_id": "answer_direct_history",
                "answer_text": "different historical answer",
                "loss_point_ids": ["lp_direct"],
                "loss_points": historical_payload["loss_points"],
                "reference_answer_sections": [reference_section],
                "generated_feedback_payload": historical_payload,
            }
        ],
    }


def _direct_replay_candidate(
    *,
    answer_coverage: dict[str, list[str]] | None = None,
) -> dict[str, object]:
    coverage = answer_coverage or {
        "covered_points": [],
        "missing_points": [],
        "weak_points": [],
        "contradicted_points": [],
    }
    return {
        "status": "generated",
        "feedback_text": "candidate",
        "answer_summary": "candidate",
        "score_result": {
            "score_type": "polish_answer",
            "score_value": 61.0,
            "dimension_scores": [
                {"dimension": dimension, "score": 61.0}
                for dimension in ("correctness", "depth", "tradeoff", "structure", "awareness")
            ],
        },
        "loss_points": [{"loss_point_id": "lp_direct", "deduction": 8.0, "reason": "alpha beta gamma delta epsilon"}],
        "reference_answer": {
            "sections": [
                {
                    "section_id": "ref_direct",
                    "content": "alpha beta gamma delta epsilon",
                    "addresses_loss_point_ids": ["lp_direct"],
                }
            ]
        },
        "answer_coverage": coverage,
        "next_recommended_actions": ["continue_next_question"],
        "feedback_metadata": {},
    }


def test_ac_003_reference_answer_replay_uses_system_reference_text_as_answer() -> None:
    source_payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([candidate_payload(80)])),
        context(answer_id="answer_reference_source_for_stability"),
    )
    source_loss_ids = loss_point_ids(source_payload)
    replay_answer_text = reference_answer_text(source_payload)

    replay_payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([candidate_payload(61, loss_ids=[])])),
        context(
            answer_id="answer_reference_replay_for_stability",
            answer_text=replay_answer_text,
            previous_answers=[
                {
                    "answer_id": "answer_reference_source_for_stability",
                    "loss_point_ids": sorted(source_loss_ids),
                    "score_result": {"score_value": score_value(source_payload)},
                    "generated_feedback_payload": source_payload,
                }
            ],
        ),
    )

    assert addressed_loss_point_ids(source_payload) == source_loss_ids
    assert replay_answer_text
    assert score_value(replay_payload) >= acceptance_test_matrix["AC-003"]["threshold_pending"]["replay_score_floor"]
    assert loss_point_ids(replay_payload).isdisjoint(source_loss_ids)


@pytest.mark.parametrize("status", ["partial", "low_confidence", ""])
def test_reference_answer_replay_rejects_non_generated_historical_payload_status(status: str) -> None:
    source_payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([candidate_payload(80)])),
        context(answer_id=f"answer_reference_source_status_{status or 'missing'}"),
    )
    source_payload = dict(source_payload) | ({"status": status} if status else {})
    source_loss_ids = loss_point_ids(source_payload)

    replay_payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([candidate_payload(61)])),
        context(
            answer_id=f"answer_reference_replay_status_{status or 'missing'}",
            answer_text=reference_answer_text(source_payload),
            previous_answers=[
                {
                    "answer_id": "answer_reference_source_status",
                    "loss_point_ids": sorted(source_loss_ids),
                    "score_result": {"score_value": score_value(source_payload)},
                    "generated_feedback_payload": source_payload,
                }
            ],
        ),
    )

    assert score_value(replay_payload) == 61.0
    assert replay_payload["feedback_metadata"].get("reference_answer_replay_detected") is not True


def test_reference_answer_replay_rejects_feedback_payload_and_payload_aliases() -> None:
    source_payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([candidate_payload(80)])),
        context(answer_id="answer_reference_source_alias_payload"),
    )
    source_loss_ids = loss_point_ids(source_payload)

    replay_payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([candidate_payload(61)])),
        context(
            answer_id="answer_reference_replay_alias_payload",
            answer_text=reference_answer_text(source_payload),
            previous_answers=[
                {
                    "answer_id": "answer_reference_source_alias_payload",
                    "loss_point_ids": sorted(source_loss_ids),
                    "score_result": {"score_value": score_value(source_payload)},
                    "feedback_payload": source_payload,
                    "payload": source_payload,
                }
            ],
        ),
    )

    assert score_value(replay_payload) == 61.0
    assert replay_payload["feedback_metadata"].get("reference_answer_replay_detected") is not True


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("missing_points", "missing replay proof"),
        ("weak_points", "weak replay proof"),
        ("weak_points", "alpha beta gamma delta epsilon"),
        ("contradicted_points", "contradicted replay proof"),
    ],
)
def test_reference_answer_replay_rejects_unresolved_coverage_before_floor(field_name: str, value: str) -> None:
    coverage = {"covered_points": [], "missing_points": [], "weak_points": [], "contradicted_points": []}
    coverage[field_name] = [value]
    candidate = _direct_replay_candidate(answer_coverage=coverage)
    candidate["feedback_metadata"] = {"phase4_validation_warnings": ["answer_coverage_missing_from_llm_policy_generated"]}

    replay_payload = apply_step4_stability_controls(candidate, _direct_replay_context())

    assert replay_payload["score_result"]["score_value"] == 61.0
    assert replay_payload["answer_coverage"][field_name] == [value]
    assert replay_payload["feedback_metadata"].get("reference_answer_replay_detected") is not True


@pytest.mark.parametrize(
    "answer_text",
    [
        "alpha beta gamma delta",
        "not alpha beta gamma delta epsilon",
        "alpha beta gamma delta epsilon keyword dump",
    ],
)
def test_reference_answer_replay_rejects_non_equivalent_answers(answer_text: str) -> None:
    replay_payload = apply_step4_stability_controls(
        _direct_replay_candidate(),
        _direct_replay_context(answer_text=answer_text),
    )

    assert replay_payload["score_result"]["score_value"] == 61.0
    assert replay_payload["feedback_metadata"].get("reference_answer_replay_detected") is not True


def test_reference_answer_replay_floor_syncs_score_related_payload_fields() -> None:
    replay_payload = apply_step4_stability_controls(_direct_replay_candidate(), _direct_replay_context())

    assert replay_payload["score_result"]["score_value"] == 88.0
    assert replay_payload["feedback_metadata"]["reference_answer_replay_score_floor"] == 88.0
    assert replay_payload["loss_points"] == []
    assert replay_payload["answer_coverage"]["missing_points"] == []
    assert replay_payload["answer_coverage"]["weak_points"] == []
    assert replay_payload["answer_coverage"]["contradicted_points"] == []
    assert replay_payload["next_recommended_actions"] == ["review_reference_answer"]


def test_reference_answer_replay_keeps_candidate_when_unresolved_loss_point_remains() -> None:
    source_payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([candidate_payload(80)])),
        context(answer_id="answer_reference_source_with_extra_candidate_loss"),
    )
    source_loss_ids = loss_point_ids(source_payload)
    replay_candidate = candidate_payload(61, loss_ids=sorted([*source_loss_ids, "lp_scalability"]))

    replay_payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([replay_candidate])),
        context(
            answer_id="answer_reference_replay_keeps_candidate_for_extra_loss",
            answer_text=reference_answer_text(source_payload),
            previous_answers=[
                {
                    "answer_id": "answer_reference_source_with_extra_candidate_loss",
                    "loss_point_ids": sorted(source_loss_ids),
                    "score_result": {"score_value": score_value(source_payload)},
                    "generated_feedback_payload": source_payload,
                }
            ],
        ),
    )

    assert score_value(replay_payload) == 61.0
    assert replay_payload["feedback_metadata"].get("reference_answer_replay_detected") is not True
    assert "lp_scalability" in loss_point_ids(replay_payload)


def test_reference_answer_replay_floor_preserves_dimension_score_semantics() -> None:
    source_payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([candidate_payload(80)])),
        context(answer_id="answer_reference_source_dimension_semantics"),
    )
    source_loss_ids = loss_point_ids(source_payload)
    replay_candidate = candidate_payload(61, loss_ids=[])
    for index, dimension in enumerate(replay_candidate["score_result"]["dimension_scores"]):
        dimension["score"] = [56, 60, 62, 65, 58][index]

    replay_payload = generate_payload(
        FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([replay_candidate])),
        context(
            answer_id="answer_reference_replay_dimension_semantics",
            answer_text=reference_answer_text(source_payload),
            previous_answers=[
                {
                    "answer_id": "answer_reference_source_dimension_semantics",
                    "loss_point_ids": sorted(source_loss_ids),
                    "score_result": {"score_value": score_value(source_payload)},
                    "generated_feedback_payload": source_payload,
                }
            ],
        ),
    )
    score_result = replay_payload["score_result"]
    dimension_values = [float(item["score"]) for item in score_result["dimension_scores"] if isinstance(item, dict)]

    assert score_value(replay_payload) >= acceptance_test_matrix["AC-003"]["threshold_pending"]["replay_score_floor"]
    assert replay_payload["feedback_metadata"]["reference_answer_replay_score_floor"] == score_value(replay_payload)
    assert len(set(dimension_values)) > 1
    assert set(dimension_values) != {score_value(replay_payload)}
