from __future__ import annotations

import ast
from dataclasses import asdict
from pathlib import Path

from app.application.transcript_analysis.models import G004Input, TranscriptInput
from app.application.transcript_analysis.parser import TranscriptParser
from app.application.transcript_analysis.service import TranscriptAnalysisService


def test_transcript_analysis_handles_empty_transcript() -> None:
    service = TranscriptAnalysisService()

    output = service.analyze(
        G004Input(
            transcript=TranscriptInput(
                question_text="",
                answer_text="",
            )
        )
    )

    assert output.schema_id == "transcript_analysis_v1"
    assert output.intent_classification == "short_answer"
    assert output.reasoning_structure["main_claim"] is None
    assert output.reasoning_structure["supporting_points"] == []
    assert output.extracted_insights["answer_span_count"] == 0
    assert any(signal.signal_type == "absence" for signal in output.skill_signals)


def test_transcript_analysis_extracts_observations_from_normal_qa() -> None:
    service = TranscriptAnalysisService()

    output = service.analyze(
        G004Input(
            transcript=TranscriptInput(
                question_text="Why did you choose a queue for this workflow?",
                answer_text=(
                    "I chose a queue because it decouples the API from slow work. "
                    "Then a worker can retry failed jobs with the same idempotency key."
                ),
            )
        )
    )

    assert output.intent_classification == "reasoning_based"
    assert output.reasoning_structure["main_claim"] == {
        "text": "I chose a queue because it decouples the API from slow work.",
        "evidence_ref": "span_1",
    }
    assert output.reasoning_structure["supporting_points"] == [
        {
            "text": "Then a worker can retry failed jobs with the same idempotency key.",
            "evidence_ref": "span_2",
        }
    ]
    assert {signal.dimension for signal in output.skill_signals} <= {
        "communication",
        "reasoning",
        "structure",
        "correctness",
    }
    assert {signal.signal_type for signal in output.skill_signals} <= {
        "presence",
        "absence",
        "pattern",
        "gap",
        "inconsistency",
    }
    assert output.behavioral_patterns[0].evidence_refs
    assert output.extracted_insights["answer_span_count"] == 2


def test_transcript_parser_splits_long_answer_into_sentence_spans() -> None:
    parser = TranscriptParser()
    answer = "First I define the boundary. Next I isolate side effects. Finally I verify replay behavior."

    context = parser.parse(
        TranscriptInput(
            question_text="Walk me through your approach.",
            answer_text=answer,
        )
    )

    assert [span["span_id"] for span in context.answer_spans] == ["span_1", "span_2", "span_3"]
    assert [span["text"] for span in context.answer_spans] == [
        "First I define the boundary.",
        "Next I isolate side effects.",
        "Finally I verify replay behavior.",
    ]


def test_g003_feedback_status_does_not_affect_output() -> None:
    service = TranscriptAnalysisService()
    transcript = TranscriptInput(
        question_text="Explain the tradeoff.",
        answer_text="The queue adds delay, but it separates request latency from worker retries.",
    )

    generated = service.analyze(
        G004Input(
            transcript=transcript,
            g003_feedback=(
                {
                    "feedback_id": "fb_generated",
                    "status": "generated",
                    "label": "excellent",
                },
            ),
        )
    )
    failed = service.analyze(
        G004Input(
            transcript=transcript,
            g003_feedback=(
                {
                    "feedback_id": "fb_failed",
                    "status": "validation_failed",
                    "label": "poor",
                },
            ),
        )
    )

    assert asdict(generated) == asdict(failed)


def test_transcript_analysis_does_not_import_g003_or_feedback_services() -> None:
    module_root = Path(__file__).resolve().parents[2] / "apps" / "api" / "app" / "application" / "transcript_analysis"
    forbidden_imports = {
        "app.application.polish.feedback_generation_service",
        "app.application.polish.feedback_application_service",
        "app.application.polish.feedback_models",
        "app.application.polish.feedback_schema",
        "app.application.polish.feedback_validation",
        "app.application.polish",
        "app.domain.shared.enums",
    }
    violations: list[str] = []

    for path in sorted(module_root.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in forbidden_imports:
                        violations.append(f"{path.name}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module in forbidden_imports:
                violations.append(f"{path.name}: from {node.module} import ...")

    assert violations == []
