from __future__ import annotations

from app.application.polish.transcript_signal_parser import (
    TranscriptSignalParser,
    build_fallback_structured_answer,
    structured_answer_to_evaluation_text,
)


def test_transcript_signal_parser_extracts_structured_signals_from_raw_answer() -> None:
    answer_text = (
        "I led the payment migration for three services. "
        "I used FastAPI, PostgreSQL, retry jobs, and alerts. "
        "Maybe cache would help, but the main risk was timeout recovery. "
        "We improved success rate by 20%."
    )

    structured = TranscriptSignalParser().parse(answer_text).to_dict()

    assert structured["schema_id"] == "polish_transcript_signals_v1"
    assert structured["parse_status"] == "parsed"
    assert [claim["text"] for claim in structured["claims"]] == [
        "I led the payment migration for three services.",
        "I used FastAPI, PostgreSQL, retry jobs, and alerts.",
        "Maybe cache would help, but the main risk was timeout recovery.",
        "We improved success rate by 20%.",
    ]
    assert {"fastapi", "postgresql", "retry jobs", "alerts"} <= set(structured["topics"])
    assert structured["sentiment"] == "mixed"
    assert {"maybe", "risk"} <= {indicator["text"] for indicator in structured["confidence_indicators"]}
    assert {"ownership", "impact"} <= {signal["signal_type"] for signal in structured["experience_signals"]}


def test_fallback_structured_answer_wraps_raw_text_when_parser_fails() -> None:
    fallback = build_fallback_structured_answer("Raw answer that could not be parsed.").to_dict()

    assert fallback["parse_status"] == "fallback"
    assert fallback["claims"] == [
        {
            "claim_id": "claim_fallback_1",
            "text": "Raw answer that could not be parsed.",
            "evidence_ref": "answer_fallback",
        }
    ]
    assert fallback["topics"] == []
    assert fallback["sentiment"] is None
    assert fallback["confidence_indicators"] == [
        {
            "indicator_id": "confidence_fallback_1",
            "text": "parser_failed",
            "kind": "parser_fallback",
            "evidence_ref": "answer_fallback",
        }
    ]


def test_structured_answer_to_evaluation_text_uses_structured_fields_only() -> None:
    structured = TranscriptSignalParser().parse("I owned the API. We reduced latency by 30%.").to_dict()

    evaluation_text = structured_answer_to_evaluation_text(structured)

    assert "Claims:" in evaluation_text
    assert "Topics:" in evaluation_text
    assert "Experience signals:" in evaluation_text
    assert "I owned the API." in evaluation_text
    assert "We reduced latency by 30%." in evaluation_text
