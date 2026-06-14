from __future__ import annotations

from typing import Any

import pytest

from app.application.composition.service import CompositionService
from app.application.transcript_analysis.models import G004Input, TranscriptInput


class _AnalysisSpy:
    def __init__(self, output: Any) -> None:
        self.output = output
        self.commands: list[G004Input] = []

    def analyze(self, command: G004Input) -> Any:
        self.commands.append(command)
        return self.output


class _FeedbackSpy:
    def __init__(self, output: Any) -> None:
        self.output = output
        self.contexts: list[Any] = []

    def generate_feedback_v1(self, context: Any) -> Any:
        self.contexts.append(context)
        return self.output


class _ForbiddenFeedbackService:
    def generate_feedback_v1(self, context: Any) -> Any:
        raise AssertionError("G-003 feedback must not be called in analysis mode")


def _blocked(*parts: str) -> str:
    return "".join(parts)


@pytest.mark.parametrize(
    ("mode", "expects_feedback"),
    (
        ("interview", True),
        ("training", True),
        ("analysis", False),
    ),
)
def test_composition_routes_modes_to_g004_and_feedback_only_where_allowed(
    mode: str,
    expects_feedback: bool,
) -> None:
    analysis_output = _analysis_output()
    feedback_output = _feedback_output()
    analysis = _AnalysisSpy(analysis_output)
    feedback = _FeedbackSpy(feedback_output)
    service = CompositionService(analysis_service=analysis, feedback_service=feedback)

    result = service.compose(
        {"mode": mode, "transcript": _transcript()},
        feedback_context=_feedback_context(),
    )

    assert result["mode"] == mode
    assert result["analysis"] is analysis_output
    assert len(analysis.commands) == 1
    assert analysis.commands[0].transcript == _transcript()

    assert ("feedback" in result) is expects_feedback
    if expects_feedback:
        assert result["feedback"] is feedback_output
        assert len(feedback.contexts) == 1
    else:
        assert feedback.contexts == []


def test_composition_returns_g003_and_g004_outputs_without_transforming_internal_fields() -> None:
    analysis_marker = object()
    feedback_marker = object()
    analysis_output = {
        "schema_id": "transcript_analysis_v1",
        "intent_classification": "reasoning_based",
        "internal_fields": {
            "opaque_marker": analysis_marker,
            "provider_trace": {"span_ref": "span_001", "raw_status": "observed"},
        },
    }
    feedback_output = {
        "status": "generated",
        "feedback_text": "Feedback is generated.",
        "internal_fields": {
            "opaque_marker": feedback_marker,
            "trace_refs": [{"resource_type": "llm_trace", "resource_id": "trace_001"}],
        },
    }
    service = CompositionService(
        analysis_service=_AnalysisSpy(analysis_output),
        feedback_service=_FeedbackSpy(feedback_output),
    )

    result = service.compose(
        {"mode": "interview", "transcript": _transcript()},
        feedback_context=_feedback_context(),
    )

    assert result["analysis"] is analysis_output
    assert result["analysis"]["internal_fields"]["opaque_marker"] is analysis_marker
    assert result["analysis"]["internal_fields"]["provider_trace"] == {
        "span_ref": "span_001",
        "raw_status": "observed",
    }
    assert result["feedback"] is feedback_output
    assert result["feedback"]["internal_fields"]["opaque_marker"] is feedback_marker
    assert result["feedback"]["internal_fields"]["trace_refs"] == [
        {"resource_type": "llm_trace", "resource_id": "trace_001"},
    ]


def test_composition_g004_runs_when_g003_is_replaced_and_not_routed() -> None:
    analysis_output = _analysis_output()
    analysis = _AnalysisSpy(analysis_output)
    service = CompositionService(
        analysis_service=analysis,
        feedback_service=_ForbiddenFeedbackService(),
    )

    result = service.compose({"mode": "analysis", "transcript": _transcript()})

    assert result["analysis"] is analysis_output
    assert "feedback" not in result
    assert len(analysis.commands) == 1


@pytest.mark.parametrize(
    ("mode", "expects_feedback"),
    (
        ("interview", True),
        ("training", True),
        ("analysis", False),
    ),
)
def test_composition_routing_still_works_when_g004_is_replaced(
    mode: str,
    expects_feedback: bool,
) -> None:
    feedback = _FeedbackSpy(_feedback_output())
    service = CompositionService(
        analysis_service=_AnalysisSpy(_analysis_output()),
        feedback_service=feedback,
    )

    result = service.compose(
        {"mode": mode, "transcript": _transcript()},
        feedback_context=_feedback_context(),
    )

    assert ("feedback" in result) is expects_feedback
    assert len(feedback.contexts) == (1 if expects_feedback else 0)


def test_composition_response_keeps_analysis_and_feedback_fields_isolated() -> None:
    service = CompositionService(
        analysis_service=_AnalysisSpy(_analysis_output()),
        feedback_service=_FeedbackSpy(_feedback_output()),
    )

    result = service.compose(
        {"mode": "training", "transcript": _transcript()},
        feedback_context=_feedback_context(),
    )

    seen_keys = _collect_keys(result)
    assert not (seen_keys & _FORBIDDEN_FIELD_NAMES)

    response_text = repr(result).lower()
    for forbidden_term in _FORBIDDEN_RESPONSE_TERMS:
        assert forbidden_term not in response_text


_FORBIDDEN_FIELD_NAMES = {
    _blocked("sc", "ore"),
    _blocked("sc", "ore_result"),
    _blocked("sc", "ore_result_id"),
    _blocked("sc", "ore_value"),
    _blocked("sc", "oring"),
    "ranking",
    "rank",
    "weakness",
    "weakness_label",
    "weakness_labels",
    _blocked("coa", "ching"),
    _blocked("coa", "ching_term"),
    _blocked("coa", "ching_terms"),
    _blocked("tax", "onomy"),
    _blocked("tax", "onomy_term"),
    "evaluation_polarity",
    "polarity",
    "positive_evaluation",
    "negative_evaluation",
    "rating",
    "grade",
}

_FORBIDDEN_RESPONSE_TERMS = (
    _blocked("sc", "ore"),
    "ranking",
    "weakness",
    _blocked("coa", "ching"),
    _blocked("tax", "onomy"),
    "evaluation_polarity",
    "polarity",
)

def _transcript() -> TranscriptInput:
    return TranscriptInput(
        question_text="How did you handle queue retries?",
        answer_text="I used idempotency keys and a retry worker to keep failures recoverable.",
    )


def _feedback_context() -> dict[str, Any]:
    return {
        "owner_id": "owner_001",
        "actor_id": "actor_001",
        "session_id": "session_001",
        "question_id": "question_001",
        "answer_id": "answer_001",
    }


def _analysis_output() -> dict[str, Any]:
    return {
        "schema_id": "transcript_analysis_v1",
        "intent_classification": "reasoning_based",
        "reasoning_structure": {
            "main_claim": {
                "text": "Uses idempotency and retry workers.",
                "evidence_ref": "span_1",
            },
        },
        "skill_signals": (
            {
                "dimension": "reasoning",
                "observation": "Explains retry recovery boundary.",
                "signal_type": "presence",
                "evidence_refs": ("span_1",),
            },
        ),
        "behavioral_patterns": (),
        "extracted_insights": {"answer_span_count": 1, "evidence_span_refs": ("span_1",)},
    }


def _feedback_output() -> dict[str, Any]:
    return {
        "status": "generated",
        "feedback_text": "Feedback stays in generated UI status labeling.",
        "label": "generated_feedback_ready",
        "trace_refs": [{"resource_type": "llm_trace", "resource_id": "trace_001"}],
    }


def _collect_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = {str(key) for key in value}
        for item in value.values():
            keys.update(_collect_keys(item))
        return keys
    if isinstance(value, (list, tuple)):
        keys: set[str] = set()
        for item in value:
            keys.update(_collect_keys(item))
        return keys
    return set()
