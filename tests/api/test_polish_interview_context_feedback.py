from __future__ import annotations

import json

from app.application.polish.canonical_evidence import CanonicalEvidenceService
from app.application.polish.commands import CreatePolishFeedbackTaskCommand
from app.application.polish.entities import PolishAnswer
from app.domain.shared.enums import AiTaskStatus
from app.domain.shared.clock import utc_now
from tests.api.test_polish_canonical_evidence import _AssetRepository, _FeedbackGenerationServiceStub, _asset
from tests.api.test_polish_question_refactor_phase1 import ACTOR_ID, OWNER_ID, SESSION_ID, _command, _use_cases


def test_interview_context_builder_adds_source_support_summary_to_feedback_context() -> None:
    from app.application.polish.context.interview_context import InterviewContextBuilder

    context = InterviewContextBuilder().build_feedback_context(
        {
            "canonical_project_assets": {
                "available": True,
                "items": [
                    {
                        "asset_id": "asset_backend_workflow",
                        "status": "asset_confirmed",
                        "asset_type": "project_story",
                    }
                ],
            },
            "canonical_evidence_pack": {
                "schema_version": "canonical_evidence_pack.v1",
                "source_support_level": "insufficient_context",
                "context_digest": "canonical_digest",
            },
        }
    )

    assert context["source_support_summary"]["level"] == "direct_project_evidence"
    assert context["source_support_level"] == "direct_project_evidence"
    assert context["canonical_evidence_pack"]["source_support_summary"] == context["source_support_summary"]
    assert context["canonical_evidence_pack"]["source_support_level"] == "direct_project_evidence"


def test_feedback_generation_context_receives_unified_canonical_evidence_from_use_case() -> None:
    asset_repository = _AssetRepository(
        [
            _asset(
                owner_id=OWNER_ID,
                asset_id="asset_backend_workflow",
                status="asset_confirmed",
                asset_type="project_story",
                title="Backend workflow automation",
                summary="Candidate built backend workflow automation with FastAPI and PostgreSQL.",
                content="Owns FastAPI APIs, PostgreSQL persistence, retries, and observability.",
            )
        ]
    )
    feedback_generation_service = _FeedbackGenerationServiceStub()
    use_cases, repository = _use_cases(ai_orchestration_facade=None)
    use_cases._canonical_evidence_service = CanonicalEvidenceService(asset_repository)
    use_cases._feedback_generation_service = feedback_generation_service

    question_result = use_cases.create_question_task(_command())
    assert question_result.is_success
    question = repository.questions[0]
    answer = PolishAnswer(
        answer_id="answer_with_unified_context",
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        question_id=question.question_id,
        answer_round=1,
        answer_text="I owned FastAPI APIs with PostgreSQL persistence and retry handling.",
        status="saved",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    repository.answers = [answer]
    repository.feedbacks = []
    repository.get_answer = lambda owner_id, answer_id: next(
        (item for item in repository.answers if item.owner_id == owner_id and item.answer_id == answer_id),
        None,
    )
    repository.list_answers_for_session = lambda owner_id, session_id: tuple(
        item for item in repository.answers if item.owner_id == owner_id and item.session_id == session_id
    )
    repository.add_feedback = lambda feedback: repository.feedbacks.append(feedback)
    repository.list_feedbacks_for_session = lambda owner_id, session_id: tuple(
        item for item in repository.feedbacks if item.owner_id == owner_id and item.session_id == session_id
    )

    feedback_result = use_cases.create_feedback_task(
        CreatePolishFeedbackTaskCommand(
            owner_id=OWNER_ID,
            actor_id=ACTOR_ID,
            session_id=SESSION_ID,
            answer_id=answer.answer_id,
        )
    )

    assert feedback_result.is_success
    assert feedback_result.value.status == AiTaskStatus.SUCCEEDED
    assert len(feedback_generation_service.contexts) == 1
    feedback_context = feedback_generation_service.contexts[0]
    assert feedback_context.source_support_summary["level"] == "direct_project_evidence"
    assert feedback_context.source_support_level == "direct_project_evidence"
    assert feedback_context.canonical_evidence_pack["source_support_summary"] == feedback_context.source_support_summary
    feedback_payload = json.loads(repository.feedbacks[0].feedback_summary)
    assert feedback_payload["status"] == "generated"
