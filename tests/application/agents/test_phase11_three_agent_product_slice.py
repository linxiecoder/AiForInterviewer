from __future__ import annotations

from pathlib import Path

from app.application.agents.orchestration import build_minimal_three_agent_product_slice
from app.application.agents.orchestration.minimal_three_agent_slice import (
    ASSET_TO_TRAINING_HANDOFF_TYPE,
    BUSINESS_AGENT_IDS,
    FEEDBACK_TO_ASSET_HANDOFF_TYPE,
    PRODUCT_SLICE_STATUS_BLOCKED,
    PRODUCT_SLICE_STATUS_FAILED_CLOSED,
    PRODUCT_SLICE_STATUS_READY,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
FORBIDDEN_WIRING_ROOTS = (
    REPO_ROOT / "apps/api/app/application/ai_runtime",
    REPO_ROOT / "apps/api/app/application/polish",
    REPO_ROOT / "apps/api/app/api",
    REPO_ROOT / "apps/api/app/domain",
    REPO_ROOT / "apps/api/app/infrastructure",
)
ALLOWED_DEFAULT_OFF_LOCAL_RUNTIME_WIRING = frozenset(
    {
        "apps/api/app/application/ai_runtime/business_graphs/local_multi_agent_orchestrator.py",
        "apps/api/app/application/ai_runtime/facade.py",
        "apps/api/app/application/ai_runtime/registry.py",
        "apps/api/app/infrastructure/ai_runtime/langgraph/in_memory_runtime.py",
    }
)
FORBIDDEN_MVP_TRAINING_FLOW_TERMS = (
    "Weakness -> Training",
    "Training -> Weakness resolved",
    "Training Center",
    "/training",
    "TrainingPlan",
    "TrainingDrill",
    "TrainingTask",
    "weakness_resolved",
)


def test_happy_path_creates_candidate_only_three_business_agent_workflow() -> None:
    result = _slice()

    assert result.status == PRODUCT_SLICE_STATUS_READY
    assert result.failure_reason == ""
    assert result.orchestrator_agent_id == "interview_orchestrator_agent"
    assert result.participant_agent_ids == BUSINESS_AGENT_IDS
    assert set(result.participant_agent_ids) == {
        "polish_feedback_agent",
        "asset_candidate_agent",
        "training_plan_agent",
    }
    assert set(result.candidate_refs) == {
        "feedback_candidate",
        "asset_update_candidate",
        "training_plan_candidate",
    }
    assert result.candidate_refs["feedback_candidate"] == "feedback_candidate_ref_1"
    assert result.candidate_refs["asset_update_candidate"].startswith("asset_update_candidate_ref_")
    assert result.candidate_refs["training_plan_candidate"].startswith("training_plan_candidate_ref_")
    assert result.formal_write_blocked is True
    assert result.asset_update_user_confirmation_required is True
    assert result.hitl_required is True
    assert result.blocking_reasons == ()
    assert all(candidate.formal_write_blocked is True for candidate in result.candidates)
    assert {
        candidate.candidate_type: candidate.user_confirmation_required for candidate in result.candidates
    }["asset_update_candidate"] is True


def test_handoff_refs_connect_feedback_to_asset_and_asset_to_training() -> None:
    result = _slice()

    handoffs = {handoff.handoff_type: handoff for handoff in result.handoff_refs}
    feedback_to_asset = handoffs[FEEDBACK_TO_ASSET_HANDOFF_TYPE]
    asset_to_training = handoffs[ASSET_TO_TRAINING_HANDOFF_TYPE]

    assert feedback_to_asset.source_agent_id == "polish_feedback_agent"
    assert feedback_to_asset.target_agent_id == "asset_candidate_agent"
    assert feedback_to_asset.source_candidate_ref == result.candidate_refs["feedback_candidate"]
    assert feedback_to_asset.candidate_type == "asset_update_candidate"
    assert feedback_to_asset.candidate_ref == result.candidate_refs["asset_update_candidate"]
    assert feedback_to_asset.formal_write_blocked is True
    assert feedback_to_asset.user_confirmation_required is True

    assert asset_to_training.source_agent_id == "asset_candidate_agent"
    assert asset_to_training.target_agent_id == "training_plan_agent"
    assert asset_to_training.source_candidate_ref == result.candidate_refs["asset_update_candidate"]
    assert asset_to_training.candidate_type == "training_plan_candidate"
    assert asset_to_training.candidate_ref == result.candidate_refs["training_plan_candidate"]
    assert asset_to_training.formal_write_blocked is True


def test_training_plan_candidate_is_not_mvp_weakness_reentry_or_resolution_flow() -> None:
    result = _slice()
    candidates = {candidate.candidate_type: candidate for candidate in result.candidates}
    training_candidate = candidates["training_plan_candidate"]
    source = (REPO_ROOT / "apps/api/app/application/agents/orchestration/minimal_three_agent_slice.py").read_text(
        encoding="utf-8"
    )

    assert result.metadata["candidate_only"] is True
    assert result.metadata["llm_call_count"] == 0
    assert result.metadata["provider_call_count"] == 0
    assert result.metadata["external_call_count"] == 0
    assert training_candidate.formal_write_blocked is True
    assert training_candidate.user_confirmation_required is False
    assert training_candidate.depends_on_candidate_refs == (
        result.candidate_refs["feedback_candidate"],
        result.candidate_refs["asset_update_candidate"],
    )
    assert "weakness" not in " ".join(result.candidate_refs)
    for term in FORBIDDEN_MVP_TRAINING_FLOW_TERMS:
        assert term not in source


def test_trace_refs_and_validation_refs_remain_separated() -> None:
    result = _slice()

    assert result.validation_refs == ("validation_ref_feedback", "validation_ref_asset")
    assert "trace_ref_feedback" in result.trace_refs
    assert "validation_ref_feedback" not in result.trace_refs
    assert {handoff.handoff_ref for handoff in result.handoff_refs}.isdisjoint(result.validation_refs)
    for event in result.timeline_events:
        assert event["validation_refs"] == result.validation_refs
        assert event["handoff_refs"] == tuple(handoff.handoff_ref for handoff in result.handoff_refs)
        assert set(event["handoff_refs"]).isdisjoint(event["validation_refs"])


def test_missing_feedback_candidate_ref_fails_closed() -> None:
    result = _slice(feedback_candidate_ref="")

    assert result.status == PRODUCT_SLICE_STATUS_FAILED_CLOSED
    assert result.failure_reason == "missing_required_refs"
    assert "missing:feedback_candidate_ref" in result.blocking_reasons
    assert result.candidate_refs == {}
    assert result.formal_write_blocked is True


def test_missing_validation_refs_fails_closed() -> None:
    result = _slice(validation_refs=())

    assert result.status == PRODUCT_SLICE_STATUS_FAILED_CLOSED
    assert result.failure_reason == "missing_required_refs"
    assert "missing:validation_refs" in result.blocking_reasons
    assert result.handoff_refs == ()


def test_asset_conflict_blocks_and_is_trace_visible() -> None:
    result = _slice(asset_conflict_ref="asset_conflict_ref_1")

    assert result.status == PRODUCT_SLICE_STATUS_BLOCKED
    assert result.failure_reason == "asset_conflict"
    assert result.blocking_reasons == ("asset_conflict",)
    assert result.candidate_refs == {"feedback_candidate": "feedback_candidate_ref_1"}
    assert "asset_update_candidate" not in result.candidate_refs
    assert "training_plan_candidate" not in result.candidate_refs
    assert result.metadata["asset_conflict_ref"] == "asset_conflict_ref_1"
    assert result.metadata["interrupt_refs"] == ("asset_conflict_ref_1",)
    assert result.timeline_events[0]["failure_reason"] == "asset_conflict"


def test_formal_write_requested_blocks_and_is_not_success() -> None:
    result = _slice(formal_write_requested=True, formal_write_requested_ref="formal_write_interrupt_ref_1")

    assert result.status == PRODUCT_SLICE_STATUS_BLOCKED
    assert result.status != PRODUCT_SLICE_STATUS_READY
    assert result.failure_reason == "formal_write_requested"
    assert result.blocking_reasons == ("formal_write_requested",)
    assert result.candidate_refs == {}
    assert result.metadata["interrupt_refs"] == ("formal_write_interrupt_ref_1",)
    assert result.formal_write_blocked is True


def test_low_confidence_flags_are_trace_visible_without_formal_output() -> None:
    result = _slice(low_confidence_flags=("source_gap", "validation_partial"))

    assert result.status == PRODUCT_SLICE_STATUS_READY
    assert result.metadata["low_confidence_flags"] == ("source_gap", "validation_partial")
    for event in result.timeline_events:
        assert event["low_confidence_flags"] == ("source_gap", "validation_partial")
        assert event["formal_write_blocked"] is True


def test_unsafe_metadata_is_sanitized_recursively() -> None:
    result = _slice(
        metadata={
            "safe_ref": "trace_ref_ok",
            "raw_prompt": "hidden",
            "nested": {
                "full_resume": "hidden",
                "kept": "ok",
                "items": [{"api_key": "hidden", "asset_ref": "asset_ref_1"}],
            },
            "formal_write_result": "hidden",
        }
    )

    assert result.metadata["safe_ref"] == "trace_ref_ok"
    assert "raw_prompt" not in result.metadata
    assert "formal_write_result" not in result.metadata
    assert result.metadata["nested"] == {"kept": "ok", "items": [{"asset_ref": "asset_ref_1"}]}


def test_slice_source_has_no_external_execution_or_storage_calls() -> None:
    source = (REPO_ROOT / "apps/api/app/application/agents/orchestration/minimal_three_agent_slice.py").read_text(
        encoding="utf-8"
    )
    forbidden_tokens = (
        "LlmTransportRequest",
        "provider_boundary",
        "OpenAI",
        "Anthropic",
        "FakeLlmTransport",
        "sqlalchemy",
        "Session(",
        "unit_of_work",
        "repository.",
        ".commit(",
        ".flush(",
    )

    for token in forbidden_tokens:
        assert token not in source


def test_orchestrator_is_only_wired_through_default_off_local_runtime_roots() -> None:
    wired_files = [
        path.relative_to(REPO_ROOT).as_posix()
        for root in FORBIDDEN_WIRING_ROOTS
        for path in _python_files(root)
        if "interview_orchestrator_agent" in path.read_text(encoding="utf-8")
    ]

    assert [path for path in wired_files if path not in ALLOWED_DEFAULT_OFF_LOCAL_RUNTIME_WIRING] == []


def _slice(**overrides: object):
    params: dict[str, object] = {
        "owner_id": "owner_1",
        "session_ref": "session_ref_1",
        "feedback_candidate_ref": "feedback_candidate_ref_1",
        "answer_ref": "answer_ref_1",
        "question_ref": "question_ref_1",
        "evidence_refs": ("evidence_ref_1", "evidence_ref_2"),
        "source_trace_refs": ("trace_ref_feedback",),
        "validation_refs": ("validation_ref_feedback", "validation_ref_asset"),
        "idempotency_key": "idem_1",
    }
    params.update(overrides)
    return build_minimal_three_agent_product_slice(**params)


def _python_files(root: Path) -> tuple[Path, ...]:
    if not root.exists():
        return ()
    return tuple(sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts))
