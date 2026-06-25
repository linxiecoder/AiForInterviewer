from __future__ import annotations

from app.application.polish.feedback_generation_service import FeedbackGenerationService

from tests.api.test_polish_feedback_acceptance_support import (
    AcceptanceDeterministicTransport,
    candidate_payload,
    context,
    generate_payload,
)


def test_same_question_answer_summary_does_not_fallback_to_historical_answer_text() -> None:
    leaked_history = "PREVIOUS_FULL_ANSWER_SHOULD_NOT_BECOME_SUMMARY"
    transport = AcceptanceDeterministicTransport([candidate_payload(82)])
    service = FeedbackGenerationService(llm_transport=transport)

    generate_payload(
        service,
        context(
            answer_id="answer_no_historical_answer_text_fallback",
            previous_answers=[
                {
                    "answer_id": "answer_history_without_summary",
                    "answer_text": leaked_history,
                    "feedback_summary": "history summary",
                    "loss_point_ids": ["lp_recovery"],
                }
            ],
        ),
    )

    same_question_answers = transport.requests[0].evidence_bundle["same_question_answers"]
    assert same_question_answers[0]["answer_summary"] == ""
    assert leaked_history not in str(transport.requests[0].evidence_bundle)


def test_session_recent_turn_summary_does_not_fallback_to_historical_answer_text(monkeypatch) -> None:
    from app.application.polish import feedback_generation_service

    leaked_history = "RECENT_FULL_ANSWER_SHOULD_NOT_BECOME_SUMMARY"
    transport = AcceptanceDeterministicTransport([candidate_payload(82)])
    service = FeedbackGenerationService(llm_transport=transport)
    value = context(answer_id="answer_no_recent_answer_text_fallback")
    value["session_recent_turns"] = [
        {
            "question_id": "question_recent_raw_only",
            "answer_id": "answer_recent_raw_only",
            "answer_text": leaked_history,
            "feedback_summary": "history summary",
        }
    ]
    captured_context: dict[str, object] = {}
    original_builder = feedback_generation_service.build_feedback_prompt_asset

    def capture_context(context_value):
        captured_context.update(context_value)
        return original_builder(context_value)

    monkeypatch.setattr(feedback_generation_service, "build_feedback_prompt_asset", capture_context)
    generate_payload(service, value)

    recent_turns = captured_context["session_recent_turns"]
    assert isinstance(recent_turns, list)
    assert recent_turns[0]["answer_summary"] == ""
    assert leaked_history not in str(transport.requests[0].evidence_bundle)
    assert leaked_history not in str(recent_turns)


def test_recovered_reference_answer_title_warning_keeps_generated_status() -> None:
    payload = candidate_payload(82)
    reference_answer = payload["reference_answer"]
    assert isinstance(reference_answer, dict)
    sections = reference_answer["sections"]
    assert isinstance(sections, list)
    for section in sections:
        assert isinstance(section, dict)
        section.pop("title")
    service = FeedbackGenerationService(llm_transport=AcceptanceDeterministicTransport([payload]))

    generated_payload = generate_payload(service, context(answer_id="answer_recovered_reference_titles"))

    assert generated_payload["status"] == "generated"
    assert "reference_answer_section_title_generated" in generated_payload["feedback_metadata"]["validation_warnings"]


def test_feedback_context_input_refs_are_stably_sorted_and_cropped() -> None:
    evidence_refs = [f"evidence_{index:02d}" for index in range(24, -1, -1)]
    value = context(answer_id="answer_stable_context_refs")
    value["evidence_refs"] = [*evidence_refs, "evidence_03"]
    value["canonical_project_assets"] = {
        "items": [
            {"asset_id": "asset_z", "status": "asset_confirmed", "title": "Z"},
            {"asset_id": "asset_a", "status": "asset_confirmed", "title": "A"},
        ]
    }
    transport = AcceptanceDeterministicTransport([candidate_payload(82)])
    service = FeedbackGenerationService(llm_transport=transport)

    generate_payload(service, value)

    dynamic_refs = transport.requests[0].input_refs[3:]
    assert dynamic_refs[:20] == tuple(f"evidence_{index:02d}" for index in range(20))
    assert dynamic_refs[20:22] == ("asset_a", "asset_z")


def test_question_sources_keep_provenance_refs_after_stable_sorting(monkeypatch) -> None:
    from app.application.polish import feedback_generation_service

    value = context(answer_id="answer_question_sources_keep_refs")
    value["evidence_refs"] = ["ref_job_reliability", "source_resume_payment"]
    value["question_sources"] = [
        {
            "index": 2,
            "source_type": "resume_project",
            "title": "Payment project",
            "excerpt": "Project evidence",
            "source_ref": "source_resume_payment",
            "evidence_refs": ["evidence_resume_payment"],
        },
        {
            "index": 1,
            "source_type": "job_requirement",
            "title": "Reliability requirement",
            "excerpt": "Job evidence",
            "ref": "ref_job_reliability",
            "ref_id": "ref_id_job_reliability",
            "source_refs": ["source_job_reliability"],
        },
    ]
    captured_context: dict[str, object] = {}
    original_builder = feedback_generation_service.build_feedback_prompt_asset

    def capture_context(context_value):
        captured_context.update(context_value)
        return original_builder(context_value)

    monkeypatch.setattr(feedback_generation_service, "build_feedback_prompt_asset", capture_context)
    transport = AcceptanceDeterministicTransport([candidate_payload(82)])
    service = FeedbackGenerationService(llm_transport=transport)

    generate_payload(service, value)

    question_sources = captured_context["question_sources"]
    assert isinstance(question_sources, list)
    prompt_sources = transport.requests[0].evidence_bundle["current_question"]["question_sources"]
    assert question_sources[0]["ref"] == "ref_job_reliability"
    assert question_sources[0]["ref_id"] == "ref_id_job_reliability"
    assert question_sources[0]["source_refs"] == ["source_job_reliability"]
    assert question_sources[1]["source_ref"] == "source_resume_payment"
    assert question_sources[1]["ref_id"] == "source_resume_payment"
    assert question_sources[1]["evidence_refs"] == ["evidence_resume_payment"]
    assert prompt_sources[0]["ref"] == "ref_job_reliability"
    assert prompt_sources[1]["ref"] == "source_resume_payment"
