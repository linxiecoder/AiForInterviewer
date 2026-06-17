from __future__ import annotations

import inspect
import json
from typing import Any

import httpx

from app.application.llm.types import LlmTransportRequest, LlmTransportResult
from app.application.polish import feedback_agent as feedback_agent_module
from app.application.polish.feedback_agent import (
    FEEDBACK_GENERATION_MAX_TOKENS,
    FeedbackGenerationAgent,
)
from app.application.polish.feedback_prompt_assets import build_feedback_prompt_asset
from app.domain.shared.enums import ConfidenceLevel, ValidationStatus
from app.infrastructure.llm.openai_compatible import (
    OpenAICompatibleLlmSettings,
    OpenAICompatibleLlmTransport,
)


def test_openai_compatible_transport_uses_request_max_tokens_without_mutating_settings() -> None:
    observed_max_tokens: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        observed_max_tokens.append(payload["max_tokens"])
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl_budget",
                "model": "deepseek-v4-pro",
                "choices": [{"finish_reason": "stop", "message": {"content": '{"status":"success"}'}}],
            },
        )

    settings = OpenAICompatibleLlmSettings(
        api_key="test-key",
        model="deepseek-v4-pro",
        base_url="https://llm.example/v1",
        max_tokens=8000,
    )
    transport = OpenAICompatibleLlmTransport(
        settings,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    transport.generate(
        LlmTransportRequest(
            contract_ids=("P-REQUEST-BUDGET-001",),
            task_type="polish_question_generation",
            max_tokens=3200,
        )
    )
    transport.generate(
        LlmTransportRequest(
            contract_ids=("P-REQUEST-BUDGET-001",),
            task_type="job_match_analysis",
            max_tokens=6400,
        )
    )

    assert observed_max_tokens == [3200, 6400]
    assert settings.max_tokens == 8000
    assert transport._settings.max_tokens == 8000


def test_feedback_agent_uses_request_budget_without_shared_transport_settings_mutation() -> None:
    transport = _SettingsRecordingTransport()

    envelope = FeedbackGenerationAgent(transport=transport).invoke_provider_v1(
        prompt_asset=build_feedback_prompt_asset(_feedback_context()),
        input_refs=("answer_001",),
    )

    assert envelope.metadata["llm_called"] is True
    assert transport.request_max_tokens == [FEEDBACK_GENERATION_MAX_TOKENS]
    assert transport.settings_max_tokens_during_generate == [8000]
    assert transport._settings.max_tokens == 8000


def test_feedback_agent_source_has_no_shared_settings_budget_mutation() -> None:
    source = inspect.getsource(feedback_agent_module)

    assert "_temporary_transport_max_tokens" not in source
    assert 'object.__setattr__(request, "max_tokens"' not in source
    assert 'setattr(transport, "_settings"' not in source


class _SettingsRecordingTransport:
    def __init__(self) -> None:
        self._settings = OpenAICompatibleLlmSettings(
            api_key="test-key",
            model="deepseek-v4-pro",
            base_url="https://llm.example/v1",
            max_tokens=8000,
        )
        self.request_max_tokens: list[int | None] = []
        self.settings_max_tokens_during_generate: list[int] = []

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        self.request_max_tokens.append(request.max_tokens)
        self.settings_max_tokens_during_generate.append(self._settings.max_tokens)
        return LlmTransportResult(
            result={"payload": _feedback_payload()},
            validation_status=ValidationStatus.VALID,
            confidence_level=ConfidenceLevel.MEDIUM,
            low_confidence_flags=(),
            trace_refs=("trace_provider_001",),
            evidence_refs=("evidence_provider_001",),
            metadata={"provider_status": "called"},
        )


def _feedback_context() -> dict[str, Any]:
    return {
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
        "job_snapshot": {
            "job_id": "job_001",
            "requirements": ["reliable backend design", "failure recovery"],
        },
        "resume_snapshot": {
            "resume_id": "resume_001",
            "projects": ["payment platform"],
        },
        "progress_node_snapshot": {
            "node_ref": "progress_node_reliability",
            "title": "Reliability design",
            "expected_capability": "Explains retry, compensation, idempotency, and alerts.",
        },
        "progress_state": {
            "progress_state_ref": "progress_node_reliability",
            "current_priority": {
                "progress_node_ref": "progress_node_reliability",
                "title": "Reliability design",
                "expected_capability": "Explains retry, compensation, idempotency, and alerts.",
            },
            "weak_skill_refs": ["recovery_boundaries", "alert_thresholds"],
            "strong_skill_refs": ["structured_answer"],
            "node_states": [
                {"progress_node_ref": "progress_node_reliability", "status": "in_progress"},
            ],
        },
    }


def _feedback_payload() -> dict[str, Any]:
    return {
        "feedback_text": "The answer covers async decoupling but should define recovery boundaries.",
        "answer_summary": "The answer mentions queues, idempotency, retry jobs, and alerts.",
        "score_result": {
            "score_type": "polish_answer",
            "score_value": 78,
            "progress_state_ref": "progress_node_reliability",
            "reasoning": "Recovery details are thin.",
            "adaptive_rubric": {"rubric_version": "polish_answer.progress_adaptive_rubric.v1"},
            "dimension_scores": [],
            "adaptive_insights": {"weak_skills": ["recovery_boundaries"]},
            "signals": ["weakness_detected"],
            "progress_updates": [],
        },
        "loss_points": [
            {
                "loss_point_id": "lp_recovery",
                "severity": "major",
                "reason": "Recovery stop conditions are not explicit.",
            }
        ],
        "reference_answer": {
            "sections": [
                {
                    "section_id": "ref_recovery",
                    "title": "Recovery boundary",
                    "content": "Explain retry, compensation, idempotency, dead letters, and handoff.",
                    "addresses_loss_point_ids": ["lp_recovery"],
                }
            ]
        },
        "low_confidence_flags": [],
        "evidence_refs": ["resume_project_payment"],
    }
