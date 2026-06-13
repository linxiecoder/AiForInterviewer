from __future__ import annotations

import inspect
from typing import Any

from app.application.llm.agent_io import (
    LegacyAgentOutputEnvelope,
)
from app.application.llm.types import LlmTransportRequest, LlmTransportResult
from app.application.polish import feedback_generation_service
from app.application.polish.feedback_agent import FeedbackGenerationAgent
from app.application.polish.feedback_prompt_assets import build_feedback_prompt_asset
from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
    POLISH_FEEDBACK_CANDIDATE_PAYLOAD_FIELDS,
    POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
    POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
    POLISH_FEEDBACK_TASK_TYPE,
)
from app.application.polish.feedback_validation import (
    validate_feedback_candidate_payload,
    validate_final_feedback_payload,
)
from app.domain.shared.enums import ConfidenceLevel, ValidationStatus


def _context() -> dict[str, Any]:
    return {
        "owner_id": "owner_001",
        "actor_id": "user_001",
        "session_id": "sess_001",
        "question_id": "question_001",
        "answer_id": "answer_001",
        "question_text": "How would you recover failed async payment messages?",
        "answer_text": "I would use a queue, idempotency keys, retry jobs, and alerts.",
        "answer_round": 2,
        "polish_theme": "payment reliability",
        "progress_node_ref": "progress_node_reliability",
        "question_sources": [
            {
                "source_type": "progress_node",
                "source_ref": "progress_node_reliability",
                "title": "Reliability",
                "excerpt": "Recover failed async work with bounded retry and observability.",
            }
        ],
        "evidence_refs": ["resume_project_payment", "job_requirement_reliability"],
        "same_question_answers": [
            {
                "answer_id": "answer_prev",
                "answer_summary": "Previous answer missed recovery stop conditions.",
            }
        ],
        "same_project_turns": [
            {
                "question_id": "question_project",
                "answer_id": "answer_project",
                "feedback_summary": "Earlier turn mentioned idempotency keys.",
            }
        ],
        "session_recent_turns": [
            {
                "question_id": "question_recent",
                "answer_id": "answer_recent",
                "feedback_summary": "Monitoring metrics were already discussed.",
            }
        ],
        "project_asset_summaries": [
            {
                "asset_id": "asset_payment",
                "summary": "Payment project contains retry, compensation, and alerting notes.",
            }
        ],
        "job_snapshot": {
            "job_id": "job_001",
            "requirements": ["reliable backend design", "failure recovery"],
            "full_jd": "must not leak",
        },
        "resume_snapshot": {
            "resume_id": "resume_001",
            "projects": ["payment platform"],
            "raw_prompt": "must not leak",
        },
        "progress_node_snapshot": {
            "node_ref": "progress_node_reliability",
            "title": "Reliability design",
            "expected_capability": "Explains retry, compensation, idempotency, and alerts.",
            "missing_points": ["stop conditions", "alert thresholds"],
            "provider_payload": "must not leak",
        },
    }


def _generated_payload(*, low_confidence_flags: list[str] | None = None) -> dict[str, Any]:
    return {
        "feedback_text": "The answer covers async decoupling but should define recovery boundaries.",
        "answer_summary": "The answer mentions queues, idempotency, retry jobs, and alerts.",
        "score_reasoning": [
            {"dimension": "reliability", "rationale": "Recovery boundaries and alert thresholds remain underspecified."},
        ],
        "loss_points": [
            {
                "loss_point_id": "lp_recovery",
                "severity": "major",
                "evidence_refs": ["resume_project_payment"],
                "reason": "Recovery stop conditions are not explicit.",
            },
        ],
        "reference_answer": {
            "sections": [
                {
                    "section_id": "ref_recovery",
                    "title": "Recovery boundary",
                    "content": "Explain retry, compensation, idempotency, dead letters, and handoff.",
                    "addresses_loss_point_ids": ["lp_recovery"],
                },
                {
                    "section_id": "ref_metrics",
                    "title": "Metrics",
                    "content": "Explain queue depth, failure rate, recovery latency, and alert thresholds.",
                    "addresses_loss_point_ids": ["lp_recovery"],
                },
            ]
        },
        "same_question_effect": {
            "improved_points": ["Added async decoupling"],
            "repeated_loss_point_ids": ["lp_metrics"],
            "regressed_points": [],
            "next_retry_focus": ["recovery boundaries"],
            "score_delta": 6,
        },
        "project_asset_update_candidates": [
            {
                "candidate_type": "project_asset_update_candidate",
                "candidate_ref": "asset_candidate_payment_recovery",
                "user_confirmation_required": True,
                "target_asset_ref": {"resource_type": "asset", "resource_id": "asset_payment"},
                "summary": "Add recovery and alerting material to the payment asset.",
            }
        ],
        "low_confidence_flags": low_confidence_flags or [],
        "evidence_refs": ["resume_project_payment", "job_requirement_reliability"],
    }


class _PayloadTransport:
    def __init__(
        self,
        result: dict[str, Any],
        *,
        low_confidence_flags: tuple[str, ...] = (),
        evidence_refs: tuple[str, ...] = ("evidence_provider_001",),
    ) -> None:
        self.result = result
        self.low_confidence_flags = low_confidence_flags
        self.evidence_refs = evidence_refs
        self.requests: list[LlmTransportRequest] = []

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        self.requests.append(request)
        return LlmTransportResult(
            result=self.result,
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.MEDIUM,
            low_confidence_flags=self.low_confidence_flags,
            trace_refs=("trace_provider_001",),
            evidence_refs=self.evidence_refs,
        )


def test_feedback_prompt_builder_uses_agent_prompt_bundle_standard_shape() -> None:
    source = inspect.getsource(build_feedback_prompt_asset)
    asset = build_feedback_prompt_asset(_context())

    assert "AgentPromptBundle(" in source
    assert ".to_prompt_asset_dict()" in source
    assert {
        "task_type",
        "prompt_version",
        "schema_id",
        "schema_version",
        "prompt",
        "input_data",
        "output_schema",
        "system_role",
        "developer_constraints",
        "user_task",
        "input_contract",
    } <= set(asset)
    assert asset["task_type"] == POLISH_FEEDBACK_TASK_TYPE
    assert asset["prompt_version"] == POLISH_FEEDBACK_AGENT_PROMPT_VERSION
    assert asset["schema_id"] == POLISH_FEEDBACK_FINAL_SCHEMA_ID
    assert asset["schema_version"] == POLISH_FEEDBACK_FINAL_SCHEMA_VERSION


def test_feedback_agent_sends_compact_provider_prompt_with_required_contract_fields() -> None:
    transport = _PayloadTransport({"payload": _generated_payload()})
    prompt_asset = build_feedback_prompt_asset(_context())

    FeedbackGenerationAgent(transport=transport).generate(
        prompt_asset=prompt_asset,
        input_refs=("answer_001",),
    )

    provider_prompt = transport.requests[-1].evidence_bundle
    assert provider_prompt["task_type"] == POLISH_FEEDBACK_TASK_TYPE
    assert provider_prompt["prompt_version"] == POLISH_FEEDBACK_AGENT_PROMPT_VERSION
    assert provider_prompt["prompt"] == prompt_asset["prompt"]
    assert provider_prompt["output_schema"] == prompt_asset["output_schema"]
    assert provider_prompt["output_schema"]["schema_id"] == POLISH_FEEDBACK_FINAL_SCHEMA_ID
    assert provider_prompt["input_contract"]["answer_text_policy"] == "structured_answer_signal_primary_input"
    assert provider_prompt["input_contract"]["answer_text_max_chars"] == 1200
    assert provider_prompt["input_contract"]["answer_text_is_bounded"] is True
    assert provider_prompt["input_contract"]["full_answer_forbidden"] is True
    assert "answer_text" not in provider_prompt["current_answer"]
    assert provider_prompt["current_answer"]["structured_answer"]["claims"]
    assert provider_prompt["current_answer"]["answer_text_policy"] == "structured_answer_signal_primary_input"
    assert provider_prompt["current_answer"]["answer_text_max_chars"] == 1200
    assert provider_prompt["current_answer"]["answer_text_is_bounded"] is True
    assert provider_prompt["current_answer"]["full_answer_forbidden"] is True
    assert "input_data" not in provider_prompt
    assert "developer_constraints" not in provider_prompt
    assert "refusal_and_low_confidence_policy" not in provider_prompt


def test_feedback_prompt_required_json_schema_separates_core_and_optional_fields() -> None:
    provider_prompt = build_feedback_prompt_asset(_context())["provider_prompt"]
    required_fields = set(provider_prompt["required_json_schema"]["required_fields"])
    candidate_fields = set(POLISH_FEEDBACK_CANDIDATE_PAYLOAD_FIELDS)
    assert required_fields == {
        "feedback_text",
        "answer_summary",
        "loss_points",
        "reference_answer.sections",
        "low_confidence_flags",
        "evidence_refs",
    }
    assert set(provider_prompt["output_schema"]["fields"]) == candidate_fields
    assert not provider_prompt["required_json_schema"]["not_applicable_fields"]
    assert "score_reasoning" not in provider_prompt["required_json_schema"]["required_fields"]
    assert "score_reasoning" in provider_prompt["required_json_schema"]["optional_fields"]
    assert "score_result" not in provider_prompt["required_json_schema"]["required_fields"]
    assert "asset_consistency_check" not in provider_prompt["required_json_schema"]["required_fields"]
    assert "answer_coverage" not in provider_prompt["required_json_schema"]["required_fields"]
    assert "feedback_cards" not in provider_prompt["required_json_schema"]["required_fields"]
    assert "next_recommended_actions" not in provider_prompt["required_json_schema"]["required_fields"]
    assert set(provider_prompt["required_json_schema"]["optional_fields"]) >= {
        "score_reasoning",
        "project_asset_update_candidates",
        "same_question_effect",
    }
    requirements_text = "\n".join(provider_prompt["output_requirements"]).lower()
    assert "feedback_text, answer_summary, loss_points" in requirements_text
    assert "optional candidate fields" in requirements_text
    for final_field in ("schema_id", "schema_version", "contract_ids", "feedback_id"):
        assert final_field not in provider_prompt["output_schema"]["fields"]


def test_feedback_agent_fails_closed_when_compact_provider_prompt_missing() -> None:
    transport = _PayloadTransport({"payload": _generated_payload()})
    prompt_asset = build_feedback_prompt_asset(_context())
    prompt_asset.pop("provider_prompt")

    envelope = FeedbackGenerationAgent(transport=transport).generate(
        prompt_asset=prompt_asset,
        input_refs=("answer_001",),
    )

    assert envelope.succeeded is False
    assert envelope.validation_errors == ("provider_request_validation_failed",)
    assert envelope.metadata["provider_status"] == "not_called"
    assert transport.requests == []


def test_feedback_agent_blocks_forbidden_provider_prompt_before_transport() -> None:
    transport = _PayloadTransport({"payload": _generated_payload()})
    prompt_asset = build_feedback_prompt_asset(_context())
    prompt_asset["provider_prompt"]["nested"] = [{"full_asset_body": "must not reach provider"}]

    envelope = FeedbackGenerationAgent(transport=transport).generate(
        prompt_asset=prompt_asset,
        input_refs=("answer_001",),
    )

    assert envelope.succeeded is False
    assert envelope.validation_errors == ("provider_request_validation_failed",)
    assert envelope.metadata["provider_status"] == "not_called"
    assert transport.requests == []


def test_feedback_agent_blocks_full_answer_before_transport() -> None:
    transport = _PayloadTransport({"payload": _generated_payload()})
    prompt_asset = build_feedback_prompt_asset(_context())
    prompt_asset["provider_prompt"]["current_answer"]["nested"] = {"full_answer": "must not reach provider"}

    envelope = FeedbackGenerationAgent(transport=transport).generate(
        prompt_asset=prompt_asset,
        input_refs=("answer_001",),
    )

    assert envelope.succeeded is False
    assert envelope.validation_errors == ("provider_request_validation_failed",)
    assert envelope.metadata["provider_status"] == "not_called"
    assert transport.requests == []


def test_feedback_prompt_asset_includes_agent_safety_policy_rules() -> None:
    asset = build_feedback_prompt_asset(_context())
    policy = asset["refusal_and_low_confidence_policy"]
    policy_text = "\n".join(policy["safety_rules"])

    assert policy["safety_policy"]["json_only"] is True
    for marker in ("raw_prompt", "provider_payload", "full_resume", "full_jd", "token", "secret"):
        assert marker in policy_text or marker in policy["safety_policy"]["forbidden_output_markers"]
    assert "不得编造项目经历" in policy_text
    assert "low confidence" in policy_text


def test_feedback_prompt_asset_serializes_evidence_items_and_focus_target() -> None:
    asset = build_feedback_prompt_asset(_context())
    input_data = asset["input_data"]

    evidence_items = input_data["evidence_items"]
    assert any(item["ref"] == "answer_001" and item["source_type"] == "answer_excerpt" for item in evidence_items)
    assert any(
        item["ref"] == "asset_payment" and item["source_type"] == "project_asset_summary"
        for item in evidence_items
    )
    assert all("chunk_id" not in item and "text" not in item for item in evidence_items)

    focus_target = input_data["focus_target"]
    assert focus_target["ref"] == "answer_001"
    assert focus_target["title"] == "question_001"
    assert focus_target["expected_capability"] == "Explains retry, compensation, idempotency, and alerts."
    assert focus_target["missing_points"] == ["stop conditions", "alert thresholds"]
    assert not _contains_forbidden_key(focus_target)
    assert not _contains_forbidden_key(evidence_items)


def test_feedback_agent_returns_agent_output_envelope_for_valid_provider_payload() -> None:
    transport = _PayloadTransport(
        {"payload": _generated_payload(low_confidence_flags=["payload_low_confidence"])},
        low_confidence_flags=("provider_low_confidence",),
        evidence_refs=("provider_evidence",),
    )
    envelope = FeedbackGenerationAgent(transport=transport).generate(
        prompt_asset=build_feedback_prompt_asset(_context()),
        input_refs=("answer_001",),
    )

    assert isinstance(envelope, LegacyAgentOutputEnvelope)
    assert envelope.succeeded is True
    assert envelope.task_type == POLISH_FEEDBACK_TASK_TYPE
    assert envelope.schema_id == POLISH_FEEDBACK_FINAL_SCHEMA_ID
    assert envelope.schema_version == POLISH_FEEDBACK_FINAL_SCHEMA_VERSION
    assert envelope.prompt_version == POLISH_FEEDBACK_AGENT_PROMPT_VERSION
    assert envelope.payload["feedback_text"] == "The answer covers async decoupling but should define recovery boundaries."
    assert envelope.payload["score_reasoning"] == [{"dimension": "reliability", "rationale": "Recovery boundaries and alert thresholds remain underspecified."}]
    assert envelope.payload["loss_points"][0]["loss_point_id"] == "lp_recovery"
    assert envelope.payload["low_confidence_flags"] == ["payload_low_confidence"]
    assert envelope.payload["evidence_refs"] == ["resume_project_payment", "job_requirement_reliability"]
    assert "score_result" not in envelope.payload
    assert "asset_consistency_check" not in envelope.payload
    assert envelope.low_confidence_flags == ("provider_low_confidence", "payload_low_confidence")
    assert envelope.evidence_refs == (
        "provider_evidence",
        "resume_project_payment",
        "job_requirement_reliability",
    )


def test_feedback_agent_invalid_provider_payload_returns_envelope_validation_errors() -> None:
    envelope = FeedbackGenerationAgent(transport=_PayloadTransport({"payload": ["not-a-dict"]})).generate(
        prompt_asset=build_feedback_prompt_asset(_context()),
        input_refs=("answer_001",),
    )

    assert isinstance(envelope, LegacyAgentOutputEnvelope)
    assert envelope.succeeded is False
    assert envelope.payload == {}
    assert envelope.validation_errors == ("feedback_payload_schema_invalid",)


def test_feedback_agent_envelope_payload_dict_filters_unsafe_metadata_keys() -> None:
    envelope = FeedbackGenerationAgent(
        transport=_PayloadTransport(
            {
                "payload": _generated_payload(),
                "metadata": {"provider_payload": "must not leak"},
                "provider_payload": "must not leak",
                "raw_completion": "must not leak",
            }
        )
    ).generate(
        prompt_asset=build_feedback_prompt_asset(_context()),
        input_refs=("answer_001",),
    )

    assert not _contains_forbidden_key(envelope.to_payload_dict().get("metadata", {}))
    assert "provider_payload" not in envelope.to_payload_dict()
    assert "raw_completion" not in envelope.to_payload_dict()


def test_service_fails_closed_when_envelope_has_validation_errors() -> None:
    result = feedback_generation_service.FeedbackGenerationService(
        llm_transport=_PayloadTransport({"payload": ["not-a-dict"]})
    ).generate(_context())

    assert result.succeeded is False
    assert result.payload is None
    assert result.validation_errors == ("feedback_payload_schema_invalid",)


def test_service_calls_candidate_and_final_validator_after_envelope_parse(monkeypatch: Any) -> None:
    calls: list[dict[str, Any]] = []

    def spy_candidate(payload: object) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
        calls.append({"validator": "candidate", "payload": payload})
        return validate_feedback_candidate_payload(payload)

    def spy_final(payload: object, *, require_feedback_id: bool = False) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
        calls.append({"validator": "final", "payload": payload, "require_feedback_id": require_feedback_id})
        return validate_final_feedback_payload(payload, require_feedback_id=require_feedback_id)

    monkeypatch.setattr(feedback_generation_service, "validate_feedback_candidate_payload", spy_candidate)
    monkeypatch.setattr(feedback_generation_service, "validate_final_feedback_payload", spy_final)

    result = feedback_generation_service.FeedbackGenerationService(
        llm_transport=_PayloadTransport({"payload": _generated_payload()})
    ).generate(_context())

    assert result.succeeded is True
    assert len(calls) >= 2
    assert calls[0]["validator"] == "candidate"
    assert calls[1]["validator"] == "final"
    assert calls[1]["require_feedback_id"] is False


def _contains_forbidden_key(value: object) -> bool:
    forbidden = {
        "raw_prompt",
        "system_prompt",
        "developer_prompt",
        "completion",
        "raw_completion",
        "provider_payload",
        "raw_provider_payload",
        "provider_response",
        "raw_provider_response",
        "full_resume",
        "full_jd",
        "full_answer",
        "full_asset_body",
        "api_key",
        "token",
        "secret",
        "cookie",
    }
    if isinstance(value, dict):
        return any(str(key).lower() in forbidden or _contains_forbidden_key(nested) for key, nested in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_key(item) for item in value)
    return False
