from __future__ import annotations

import json
from typing import Any

from app.application.polish.canonical_evidence import CanonicalEvidenceService
from app.application.polish.commands import CreatePolishFeedbackTaskCommand
from app.application.polish.entities import PolishAnswer, PolishQuestion
from app.application.polish.feedback_generation_service import FeedbackGenerationResult
from app.application.polish.feedback_prompt_assets import build_feedback_prompt_asset
import app.application.polish.use_cases as polish_use_cases_module
from app.domain.shared.clock import utc_now
from app.domain.shared.enums import AiTaskStatus

from tests.api.test_polish_question_graph_integration import (
    ACTOR_ID,
    OWNER_ID,
    SESSION_ID,
    _command,
    _use_cases,
)


def test_canonical_evidence_service_selects_confirmed_safe_owner_assets() -> None:
    repository = _AssetRepository(
        [
            _asset(
                owner_id=OWNER_ID,
                asset_id="asset_archived_story",
                status="asset_archived",
                asset_type="project_story",
                title="Backend workflow automation",
                summary="FastAPI and PostgreSQL project fact.",
                content="FastAPI workflow automation with PostgreSQL queues. " + "DO_NOT_INCLUDE_FULL_BODY " * 80,
            ),
            _asset(
                owner_id=OWNER_ID,
                asset_id="asset_confirmed_note",
                status="asset_confirmed",
                asset_type="technical_note",
                title="PostgreSQL reliability note",
                summary="Retry and idempotency details.",
                content="PostgreSQL transaction retries and idempotency keys.",
            ),
            _asset(owner_id="other_owner", asset_id="asset_other", title="FastAPI other owner"),
            _asset(owner_id=OWNER_ID, asset_id="asset_candidate", status="asset_candidate_generated"),
        ]
    )

    pack = CanonicalEvidenceService(repository).build_pack(
        owner_id=OWNER_ID,
        session_id=SESSION_ID,
        query_inputs=("FastAPI PostgreSQL workflow reliability",),
    )

    canonical_assets = pack["canonical_project_assets"]
    assert canonical_assets["available"] is True
    assert canonical_assets["selection_policy"] == "rule_based_keyword_overlap_v1"
    assert canonical_assets["status_policy"] == "asset_confirmed_only_v1"
    assert canonical_assets["excluded_statuses"]["asset_archived"] == "historical_reference_only"
    assert [item["asset_id"] for item in canonical_assets["items"]] == ["asset_confirmed_note"]
    assert canonical_assets["items"][0]["status"] == "asset_confirmed"
    assert canonical_assets["items"][0]["asset_type"] == "technical_note"
    assert len(canonical_assets["items"][0]["content_excerpt"]) <= 480
    assert "DO_NOT_INCLUDE_FULL_BODY " * 20 not in canonical_assets["items"][0]["content_excerpt"]
    assert pack["source_support_level"] == "direct_project_evidence"
    assert pack["context_digest"]


def test_canonical_evidence_service_returns_unavailable_without_assets() -> None:
    missing_repository_pack = CanonicalEvidenceService().build_pack(
        owner_id=OWNER_ID,
        session_id=SESSION_ID,
        query_inputs=("FastAPI PostgreSQL workflow reliability",),
    )

    assert missing_repository_pack["canonical_project_assets"]["available"] is False
    assert missing_repository_pack["canonical_project_assets"]["items"] == []
    assert missing_repository_pack["canonical_project_assets"]["warnings"] == ["asset_repository_absent"]
    assert missing_repository_pack["canonical_project_assets"]["status_policy"] == "asset_confirmed_only_v1"
    assert missing_repository_pack["source_support_level"] == "insufficient_context"

    unrelated_repository = _AssetRepository(
        [
            _asset(
                owner_id=OWNER_ID,
                asset_id="asset_unrelated",
                title="Frontend design system",
                summary="Button and layout conventions.",
                content="Visual tokens and component spacing.",
            )
        ]
    )
    no_match_pack = CanonicalEvidenceService(unrelated_repository).build_pack(
        owner_id=OWNER_ID,
        session_id=SESSION_ID,
        query_inputs=("FastAPI PostgreSQL workflow reliability",),
    )

    assert no_match_pack["canonical_project_assets"]["available"] is False
    assert no_match_pack["canonical_project_assets"]["items"] == []
    assert no_match_pack["canonical_project_assets"]["status_policy"] == "asset_confirmed_only_v1"
    assert no_match_pack["source_support_level"] == "insufficient_context"


def test_canonical_evidence_service_excludes_archived_assets_as_historical_reference() -> None:
    repository = _AssetRepository(
        [
            _asset(
                owner_id=OWNER_ID,
                asset_id="asset_archived_workflow",
                status="asset_archived",
                asset_type="project_story",
                title="Backend workflow automation",
                summary="Archived FastAPI and PostgreSQL project fact.",
                content="Archived FastAPI workflow automation with PostgreSQL queues.",
            )
        ]
    )

    pack = CanonicalEvidenceService(repository).build_pack(
        owner_id=OWNER_ID,
        session_id=SESSION_ID,
        query_inputs=("FastAPI PostgreSQL workflow reliability",),
    )

    canonical_assets = pack["canonical_project_assets"]
    assert canonical_assets["available"] is False
    assert canonical_assets["items"] == []
    assert canonical_assets["status_policy"] == "asset_confirmed_only_v1"
    assert canonical_assets["excluded_statuses"]["asset_archived"] == "historical_reference_only"
    assert pack["source_support_level"] == "insufficient_context"


def test_canonical_evidence_service_limits_items_and_digest_tracks_asset_summary() -> None:
    assets = [
        _asset(
            owner_id=OWNER_ID,
            asset_id=f"asset_backend_workflow_{index}",
            title=f"FastAPI workflow automation {index}",
            summary=f"FastAPI and PostgreSQL project fact {index}.",
            content=f"FastAPI workflow automation with PostgreSQL queue {index}.",
        )
        for index in range(6)
    ]
    pack = CanonicalEvidenceService(_AssetRepository(assets)).build_pack(
        owner_id=OWNER_ID,
        session_id=SESSION_ID,
        query_inputs=("FastAPI PostgreSQL workflow reliability",),
    )

    assert len(pack["canonical_project_assets"]["items"]) == 5

    changed_assets = [dict(asset) for asset in assets]
    changed_assets[0]["summary"] = "FastAPI and PostgreSQL project fact changed."
    changed_pack = CanonicalEvidenceService(_AssetRepository(changed_assets)).build_pack(
        owner_id=OWNER_ID,
        session_id=SESSION_ID,
        query_inputs=("FastAPI PostgreSQL workflow reliability",),
    )

    assert changed_pack["context_digest"] != pack["context_digest"]

    changed_version_assets = [dict(asset) for asset in assets]
    changed_version_assets[0]["current_version_id"] = "asset_backend_workflow_0_v2"
    changed_version_pack = CanonicalEvidenceService(_AssetRepository(changed_version_assets)).build_pack(
        owner_id=OWNER_ID,
        session_id=SESSION_ID,
        query_inputs=("FastAPI PostgreSQL workflow reliability",),
    )

    assert changed_version_pack["context_digest"] != pack["context_digest"]


def test_polish_question_and_feedback_context_include_canonical_assets(monkeypatch: Any) -> None:
    repository = _AssetRepository(
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
    question_workflow_results: list[Any] = []
    original_question_workflow = polish_use_cases_module.run_question_planned_workflow

    def recording_question_workflow(**kwargs: Any) -> Any:
        workflow_result = original_question_workflow(**kwargs)
        question_workflow_results.append(workflow_result)
        return workflow_result

    monkeypatch.setattr(polish_use_cases_module, "run_question_planned_workflow", recording_question_workflow)
    feedback_generation_service = _FeedbackGenerationServiceStub()
    use_cases, polish_repository = _use_cases(ai_orchestration_facade=None)
    use_cases._canonical_evidence_service = CanonicalEvidenceService(repository)
    use_cases._feedback_generation_service = feedback_generation_service

    question_result = use_cases.create_question_task(_command())
    assert question_result.is_success
    assert question_result.value is not None
    assert question_result.value.status == AiTaskStatus.VALIDATION_FAILED
    assert question_result.value.result_ref.trace_type == "question_candidate"
    assert polish_repository.questions == []
    assert polish_repository.tasks == [question_result.value]
    assert question_workflow_results

    question_workflow_result = question_workflow_results[0]
    question_candidate = question_workflow_result.candidate
    question_metadata = question_candidate["question_metadata"]
    assert question_result.value.result_ref.trace_ref_id == question_workflow_result.question_candidate_ref
    assert any(
        ref.resource_type == "question_candidate"
        and ref.resource_id == question_workflow_result.question_candidate_ref
        for ref in question_result.value.candidate_refs
    )
    assert set(question_result.value.validation_errors) >= {
        "agent_facade_absent",
        "not_configured",
        "deterministic_degraded_generation",
    }
    assert question_metadata["planned_workflow"] == "phase5_question_agent_l2"
    assert question_metadata["candidate_output"] == "question_candidate"
    assert question_metadata["fallback_reported_as_generated_success"] is False
    assert question_metadata["canonical_project_assets_available"] is True
    assert question_metadata["canonical_project_asset_refs"] == ["asset_backend_workflow"]
    assert question_metadata["source_support_level"] == "direct_project_evidence"
    assert "validation_ref_source_support" in question_metadata["validation_refs"]
    assert "validation_ref_question_grounding" in question_metadata["validation_refs"]
    assert question_candidate["context_digest"] != "ctx_pr5_q2"

    question = _question_from_candidate(
        question_candidate,
        owner_id=OWNER_ID,
        actor_id=ACTOR_ID,
        session_id=SESSION_ID,
        ai_task_id=question_result.value.ai_task_id,
    )
    polish_repository.questions = [question]

    answer = PolishAnswer(
        answer_id="answer_with_canonical_asset",
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
    polish_repository.answers = [answer]
    polish_repository.feedbacks = []
    polish_repository.get_answer = lambda owner_id, answer_id: next(
        (item for item in polish_repository.answers if item.owner_id == owner_id and item.answer_id == answer_id),
        None,
    )
    polish_repository.list_answers_for_session = lambda owner_id, session_id: tuple(
        item for item in polish_repository.answers if item.owner_id == owner_id and item.session_id == session_id
    )
    polish_repository.add_feedback = lambda feedback: polish_repository.feedbacks.append(feedback)
    polish_repository.list_feedbacks_for_session = lambda owner_id, session_id: tuple(
        item for item in polish_repository.feedbacks if item.owner_id == owner_id and item.session_id == session_id
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
    assert feedback_context.canonical_project_assets["available"] is True
    assert feedback_context.canonical_project_assets["items"][0]["asset_id"] == "asset_backend_workflow"
    assert feedback_context.project_asset_summaries[0]["asset_id"] == "asset_backend_workflow"
    feedback_payload = json.loads(polish_repository.feedbacks[0].feedback_summary)
    assert feedback_payload["status"] == "generated"
    assert feedback_payload["feedback_metadata"]["candidate_output"] == "feedback_candidate"
    assert feedback_payload["feedback_metadata"]["silent_degradation_reported_as_generated_success"] is False


def test_feedback_prompt_asset_compacts_only_confirmed_canonical_project_assets() -> None:
    context = {
        "owner_id": OWNER_ID,
        "actor_id": ACTOR_ID,
        "session_id": SESSION_ID,
        "question_id": "question_001",
        "answer_id": "answer_001",
        "question_text": "How did you build the backend workflow?",
        "answer_text": "I used FastAPI and PostgreSQL.",
        "canonical_project_assets": {
            "available": True,
            "selection_policy": "rule_based_keyword_overlap_v1",
            "items": [
                {
                    "asset_id": "asset_archived_workflow",
                    "status": "asset_archived",
                    "asset_type": "project_story",
                    "title": "Backend workflow automation",
                    "summary": "Archived FastAPI and PostgreSQL project fact.",
                    "content_excerpt": "Archived excerpt.",
                    "source_refs": [{"resource_type": "review", "resource_id": "review_archived"}],
                    "evidence_refs": [{"resource_type": "answer", "resource_id": "answer_archived"}],
                    "current_version_id": "assetver_archived",
                    "priority": 260,
                    "relevance_reason": "keyword_overlap:fastapi",
                },
                {
                    "asset_id": "asset_confirmed_workflow",
                    "status": "asset_confirmed",
                    "asset_type": "project_story",
                    "title": "Backend workflow automation",
                    "summary": "Confirmed FastAPI and PostgreSQL project fact.",
                    "content_excerpt": "Confirmed excerpt.",
                    "source_refs": [{"resource_type": "review", "resource_id": "review_001"}],
                    "evidence_refs": [{"resource_type": "answer", "resource_id": "answer_001"}],
                    "current_version_id": "assetver_001",
                    "priority": 240,
                    "relevance_reason": "keyword_overlap:fastapi",
                }
            ],
        },
    }

    asset = build_feedback_prompt_asset(context)
    canonical_assets = asset["input_data"]["canonical_project_assets"]
    provider_prompt = asset["provider_prompt"]

    assert canonical_assets["available"] is True
    assert [item["asset_id"] for item in canonical_assets["items"]] == ["asset_confirmed_workflow"]
    assert provider_prompt["canonical_project_assets"]["items"][0]["content_excerpt"] == "Confirmed excerpt."
    provider_data = {key: value for key, value in provider_prompt.items() if key != "prompt"}
    assert "full_resume" not in json.dumps(provider_data, ensure_ascii=False, sort_keys=True)


class _FeedbackGenerationServiceStub:
    def __init__(self) -> None:
        self.contexts: list[Any] = []

    def generate_feedback_v1(self, context: Any) -> FeedbackGenerationResult:
        self.contexts.append(context)
        return FeedbackGenerationResult(
            succeeded=True,
            payload={
                "schema_id": "polish_feedback_generated_v1",
                "schema_version": "1.0",
                "status": "generated",
                "contract_ids": ["P-POLISH-003", "P-POLISH-004", "P-POLISH-005"],
                "feedback_text": "Generated with canonical assets.",
                "answer_summary": "Answer references backend workflow facts.",
                "score_result": {"score_type": "polish_answer", "score_value": 86},
                "loss_points": [],
                "reference_answer": {"sections": []},
                "asset_consistency_check": {
                    "status": "consistent",
                    "checked_asset_refs": ["asset_confirmed_workflow"],
                    "conflicts": [],
                    "unsupported_claims": [],
                    "user_clarification_required": False,
                },
                "answer_coverage": {
                    "expected_points": [],
                    "covered_points": [],
                    "missing_points": [],
                    "weak_points": [],
                    "contradicted_points": [],
                },
                "answer_change_analysis": {
                    "has_prior_attempts": False,
                    "previous_answer_refs": [],
                    "retained_points": [],
                    "newly_added_points": [],
                    "regressed_points": [],
                    "repeated_loss_points": [],
                    "fixed_loss_points": [],
                    "score_delta": None,
                    "trend": "first_attempt",
                },
                "feedback_cards": [{"card_type": "overall", "status": "generated", "payload": {}}],
                "next_recommended_actions": ["continue_same_question"],
                "low_confidence_flags": [],
                "trace_refs": [{"resource_type": "llm_trace", "resource_id": "trace_canonical_assets"}],
                "feedback_metadata": {"llm_called": True},
            },
            metadata={"llm_called": True},
        )


class _AssetRepository:
    def __init__(self, assets: list[dict[str, Any]]) -> None:
        self._assets = assets

    def list_assets(
        self,
        *,
        owner_id: str,
        status: str | None = None,
        asset_type: str | None = None,
        q: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        rows = [
            asset
            for asset in self._assets
            if asset["owner_id"] == owner_id
            and (status is None or asset["status"] == status)
            and (asset_type is None or asset["asset_type"] == asset_type)
        ]
        return tuple({key: value for key, value in asset.items() if key != "content"} for asset in rows)

    def get_asset(self, *, owner_id: str, asset_id: str) -> dict[str, Any] | None:
        return next(
            (
                dict(asset)
                for asset in self._assets
                if asset["owner_id"] == owner_id and asset["asset_id"] == asset_id
            ),
            None,
        )


def _question_from_candidate(
    candidate: dict[str, Any],
    *,
    owner_id: str,
    actor_id: str,
    session_id: str,
    ai_task_id: str,
) -> PolishQuestion:
    now = utc_now()
    return PolishQuestion(
        question_id=str(candidate["candidate_ref"]),
        owner_id=owner_id,
        actor_id=actor_id,
        session_id=session_id,
        ai_task_id=ai_task_id,
        question_text=str(candidate["question_text"]),
        status="candidate_context_for_feedback_test",
        created_at=now,
        updated_at=now,
        progress_node_ref=str(candidate.get("progress_node_ref") or "") or None,
        evidence_refs=tuple(str(ref) for ref in candidate.get("evidence_refs", ()) if str(ref).strip()),
        context_digest=str(candidate.get("context_digest") or "") or None,
        question_metadata=(
            dict(candidate["question_metadata"]) if isinstance(candidate.get("question_metadata"), dict) else {}
        ),
    )


def _asset(
    *,
    owner_id: str,
    asset_id: str,
    status: str = "asset_confirmed",
    asset_type: str = "project_story",
    title: str = "Backend workflow automation",
    summary: str = "FastAPI project fact.",
    content: str = "FastAPI and PostgreSQL workflow automation.",
) -> dict[str, Any]:
    return {
        "owner_id": owner_id,
        "asset_id": asset_id,
        "status": status,
        "asset_type": asset_type,
        "title": title,
        "summary": summary,
        "content": content,
        "current_version_id": f"{asset_id}_v1",
        "source_refs": [{"resource_type": "review", "resource_id": "review_001"}],
        "evidence_refs": [{"resource_type": "answer", "resource_id": "answer_001"}],
    }
