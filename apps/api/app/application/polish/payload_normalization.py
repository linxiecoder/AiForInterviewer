from __future__ import annotations

from typing import Any

from app.application.polish.payload_helpers import _stable_string_values
from app.application.polish.question_source_normalization import (
    _stable_asset_summary_items,
    _stable_canonical_project_assets,
    _stable_question_source_items,
    _stable_recent_turn_items,
    _stable_retrieved_rag_chunks,
    _stable_same_question_answer_items,
)

_STEP4_SAME_ANSWER_CONTEXT_MAX_ITEMS = 5
_STEP4_CONTEXT_SOURCE_MAX_ITEMS = 8
_STEP4_CONTEXT_REF_MAX_ITEMS = 20


def payload_normalization(context: dict[str, Any]) -> dict[str, Any]:
    stable = dict(context)
    stable["evidence_refs"] = list(
        _stable_string_values(
            stable.get("evidence_refs"),
            max_items=_STEP4_CONTEXT_REF_MAX_ITEMS,
            max_chars=200,
        )
    )
    stable["question_sources"] = list(
        _stable_question_source_items(
            stable.get("question_sources"),
            max_items=_STEP4_CONTEXT_SOURCE_MAX_ITEMS,
        )
    )
    stable["same_question_answers"] = list(
        _stable_same_question_answer_items(
            stable.get("same_question_answers"),
            max_items=_STEP4_SAME_ANSWER_CONTEXT_MAX_ITEMS,
        )
    )
    stable["session_recent_turns"] = list(_stable_recent_turn_items(stable.get("session_recent_turns"), max_items=3))
    stable["project_asset_summaries"] = list(
        _stable_asset_summary_items(
            stable.get("project_asset_summaries"),
            max_items=_STEP4_CONTEXT_SOURCE_MAX_ITEMS,
        )
    )
    stable["canonical_project_assets"] = _stable_canonical_project_assets(stable.get("canonical_project_assets"))
    if "retrieved_rag_chunks" in stable and stable.get("retrieved_rag_chunks") is not None:
        stable["retrieved_rag_chunks"] = _stable_retrieved_rag_chunks(stable.get("retrieved_rag_chunks"))
    return stable
