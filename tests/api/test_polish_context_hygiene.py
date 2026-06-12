from __future__ import annotations

import inspect
import json
from typing import Any

from app.application.polish import feedback_generation_service, question_generation_service, question_metadata
from app.application.polish.context_hygiene import (
    ContextHygieneStatus,
    assert_safe_context_metadata,
    build_context_hygiene_metadata,
    normalize_context_hygiene_metadata,
)


def test_context_hygiene_metadata_normalizes_to_safe_short_contract() -> None:
    metadata = build_context_hygiene_metadata(
        status="fallback",
        safe_context_metadata={
            "context_compaction_applied": True,
            "provider_payload": {"secret": "must not leak"},
            "raw_prompt": "must not leak",
            "full_resume": "must not leak",
        },
        fallback_reason="llm_transport_unavailable",
        validation_errors=(
            "provider_payload raw_prompt full_resume token=hidden must not leak",
            "candidate_schema_invalid",
        ),
    )

    payload = metadata.to_dict()
    normalized = normalize_context_hygiene_metadata(payload)

    assert metadata.context_hygiene_status is ContextHygieneStatus.FALLBACK
    assert normalized["context_hygiene_status"] == "fallback"
    assert normalized["safe_context_metadata"]["context_compaction_applied"] is True
    assert normalized["fallback_reason"] == "llm_transport_unavailable"
    assert "candidate_schema_invalid" in normalized["validation_signals"]["validation_errors"]
    assert_safe_context_metadata(normalized["safe_context_metadata"])
    serialized = json.dumps(normalized, ensure_ascii=False, sort_keys=True)
    for forbidden in ("raw_prompt", "provider_payload", "full_resume", "token=hidden"):
        assert forbidden not in serialized


def test_question_and_feedback_generation_use_shared_context_hygiene_contract() -> None:
    source_by_module: dict[str, Any] = {
        "question_generation_service": question_generation_service,
        "feedback_generation_service": feedback_generation_service,
        "question_metadata": question_metadata,
    }

    question_source = inspect.getsource(source_by_module["question_generation_service"])
    feedback_source = inspect.getsource(source_by_module["feedback_generation_service"])
    metadata_source = inspect.getsource(source_by_module["question_metadata"])

    assert "build_context_hygiene_metadata" in question_source
    assert "build_context_hygiene_metadata" in feedback_source
    assert "normalize_context_hygiene_metadata" in metadata_source
