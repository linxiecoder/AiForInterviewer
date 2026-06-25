from __future__ import annotations

from typing import Any

from app.application.polish.payload_helpers import (
    _clean,
    _dict_items,
    _int_value,
    _mapping,
    _number,
    _stable_string_values,
)

_STEP4_CONTEXT_SOURCE_MAX_ITEMS = 8


def normalize_question_source_refs(source: dict[str, Any]) -> tuple[str, ...]:
    refs = [
        _clean(source.get("ref"), max_chars=160),
        _clean(source.get("ref_id"), max_chars=160),
        _clean(source.get("source_ref"), max_chars=160),
        *_stable_string_values(source.get("source_refs"), max_items=20, max_chars=160),
        *_stable_string_values(source.get("evidence_refs"), max_items=20, max_chars=160),
    ]
    return tuple(dict.fromkeys(ref for ref in refs if ref))


def _stable_question_source_items(value: object, *, max_items: int) -> tuple[dict[str, Any], ...]:
    items: list[dict[str, Any]] = []
    for item in _dict_items(value):
        refs = normalize_question_source_refs(item)
        ref = _clean(item.get("ref"), max_chars=160) or (refs[0] if refs else "")
        ref_id = _clean(item.get("ref_id") or item.get("source_ref") or ref, max_chars=160)
        source_ref = _clean(item.get("source_ref") or ref_id or ref, max_chars=160)
        items.append(
            {
                "index": _int_value(item.get("index")),
                "source_type": _clean(item.get("source_type"), max_chars=80),
                "title": _clean(item.get("title"), max_chars=240),
                "excerpt": _clean(item.get("excerpt"), max_chars=1000),
                "ref": ref or ref_id or source_ref,
                "ref_id": ref_id,
                "source_ref": source_ref,
                "source_refs": list(_stable_string_values(item.get("source_refs"), max_items=20, max_chars=160)),
                "evidence_refs": list(_stable_string_values(item.get("evidence_refs"), max_items=20, max_chars=160)),
                "availability": _clean(item.get("availability"), max_chars=80),
            }
        )
    return tuple(sorted(items, key=_source_sort_key)[:max_items])


def _stable_same_question_answer_items(value: object, *, max_items: int) -> tuple[dict[str, Any], ...]:
    items: list[dict[str, Any]] = []
    for item in _dict_items(value):
        answer_coverage = _mapping(item.get("answer_coverage")) or {}
        score_result = _mapping(item.get("score_result")) or {}
        feedback_payload = _previous_feedback_payload(item)
        items.append(
            {
                "answer_id": _clean(item.get("answer_id"), max_chars=120),
                "answer_round": _int_value(item.get("answer_round")),
                "answer_text": _clean(item.get("answer_text"), max_chars=12000),
                "answer_summary": _clean(item.get("answer_summary"), max_chars=700),
                "answer_summary_source": "answer_summary"
                if _clean(item.get("answer_summary"), max_chars=700)
                else "",
                "feedback_summary": _clean(item.get("feedback_summary") or item.get("feedback_text"), max_chars=700),
                "loss_point_ids": list(_stable_string_values(item.get("loss_point_ids"), max_items=40, max_chars=120)),
                "loss_points": list(_stable_loss_point_items(item.get("loss_points"), max_items=20)),
                "covered_points": list(
                    _stable_string_values(
                        item.get("covered_points") or answer_coverage.get("covered_points"),
                        max_items=40,
                        max_chars=240,
                    )
                ),
                "missing_points": list(
                    _stable_string_values(
                        item.get("missing_points") or answer_coverage.get("missing_points"),
                        max_items=40,
                        max_chars=240,
                    )
                ),
                "answer_coverage": {
                    "covered_points": list(
                        _stable_string_values(answer_coverage.get("covered_points"), max_items=40, max_chars=240)
                    ),
                    "missing_points": list(
                        _stable_string_values(answer_coverage.get("missing_points"), max_items=40, max_chars=240)
                    ),
                },
                "score_result": {"score_value": score_result.get("score_value")}
                if score_result.get("score_value") is not None
                else {},
                "reference_answer_text": _stable_previous_reference_answer_text(item),
                "reference_answer_sections": list(_stable_previous_reference_answer_sections(item)),
                "generated_feedback_payload": _stable_previous_feedback_payload(feedback_payload),
            }
        )
    return tuple(sorted(items, key=_answer_sort_key)[-max_items:])


def _stable_previous_feedback_payload(value: dict[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {}
    score_result = _mapping(value.get("score_result")) or {}
    return {
        "status": _clean(value.get("status"), max_chars=40),
        "score_result": {"score_value": score_result.get("score_value")}
        if score_result.get("score_value") is not None
        else {},
        "loss_points": list(_stable_loss_point_items(value.get("loss_points"), max_items=20)),
        "reference_answer": {
            "sections": list(_stable_previous_reference_answer_sections({"generated_feedback_payload": value})),
        },
    }


def _stable_previous_reference_answer_sections(value: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    feedback_payload = _previous_feedback_payload(value)
    if feedback_payload is None:
        return ()
    reference_answer = _mapping(feedback_payload.get("reference_answer"))
    if reference_answer is None:
        return ()
    sections: list[dict[str, Any]] = []
    for section in _dict_items(reference_answer.get("sections")):
        content = _clean(section.get("content"), max_chars=4000)
        if content:
            sections.append(
                {
                    "section_id": _clean(section.get("section_id"), max_chars=120),
                    "content": content,
                    "addresses_loss_point_ids": list(
                        _stable_string_values(
                            section.get("addresses_loss_point_ids"),
                            max_items=40,
                            max_chars=120,
                        )
                    ),
                }
            )
    return tuple(sections[:20])


def _stable_previous_reference_answer_text(value: dict[str, Any]) -> str:
    feedback_payload = _previous_feedback_payload(value)
    if feedback_payload is None:
        return ""
    reference_answer = _mapping(feedback_payload.get("reference_answer"))
    if reference_answer is None:
        return ""
    return _clean(
        " ".join(
            content
            for section in _dict_items(reference_answer.get("sections"))
            if (content := _clean(section.get("content"), max_chars=4000))
        ),
        max_chars=12000,
    )


def _previous_feedback_payload(value: dict[str, Any]) -> dict[str, Any] | None:
    payload = _mapping(value.get("generated_feedback_payload"))
    if payload is None:
        return None
    if _clean(payload.get("status"), max_chars=40) == "generated":
        return dict(payload)
    return None


def _stable_recent_turn_items(value: object, *, max_items: int) -> tuple[dict[str, Any], ...]:
    items = [
        {
            "question_id": _clean(item.get("question_id"), max_chars=120),
            "question_summary": _clean(item.get("question_summary") or item.get("question_text"), max_chars=500),
            "progress_node_ref": _clean(item.get("progress_node_ref"), max_chars=120),
            "answer_id": _clean(item.get("answer_id"), max_chars=120),
            "answer_round": _int_value(item.get("answer_round")),
            "answer_summary": _clean(item.get("answer_summary"), max_chars=700),
            "feedback_summary": _clean(item.get("feedback_summary") or item.get("feedback_text"), max_chars=700),
        }
        for item in _dict_items(value)
    ]
    return tuple(sorted(items, key=_turn_sort_key)[-max_items:])


def _stable_asset_summary_items(value: object, *, max_items: int) -> tuple[dict[str, Any], ...]:
    return tuple(sorted((_stable_asset_item(item) for item in _dict_items(value)), key=_asset_sort_key)[:max_items])


def _stable_canonical_project_assets(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    normalized = dict(value)
    normalized["items"] = [
        dict(item) for item in _stable_asset_summary_items(value.get("items"), max_items=_STEP4_CONTEXT_SOURCE_MAX_ITEMS)
    ]
    return normalized


def _stable_retrieved_rag_chunks(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    normalized = dict(value)
    chunks = [
        {
            "chunk_id": _clean(item.get("chunk_id") or item.get("id"), max_chars=120),
            "source_ref": _clean(item.get("source_ref") or item.get("ref_id"), max_chars=160),
            "text": _clean(item.get("text") or item.get("content"), max_chars=1000),
        }
        for item in _dict_items(value.get("items"))
    ]
    normalized["items"] = sorted(chunks, key=_rag_sort_key)[:_STEP4_CONTEXT_SOURCE_MAX_ITEMS]
    return normalized


def _stable_asset_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset_id": _clean(item.get("asset_id") or item.get("asset_ref"), max_chars=120),
        "status": _clean(item.get("status"), max_chars=80),
        "asset_type": _clean(item.get("asset_type"), max_chars=80),
        "title": _clean(item.get("title"), max_chars=240),
        "summary": _clean(item.get("summary") or item.get("content_excerpt"), max_chars=800),
        "content_excerpt": _clean(item.get("content_excerpt"), max_chars=800),
        "source_refs": list(_stable_string_values(item.get("source_refs"), max_items=20, max_chars=160)),
        "evidence_refs": list(_stable_string_values(item.get("evidence_refs"), max_items=20, max_chars=160)),
        "current_version_id": _clean(item.get("current_version_id"), max_chars=120),
        "priority": _int_value(item.get("priority")),
        "relevance_reason": _clean(item.get("relevance_reason"), max_chars=240),
    }


def _stable_loss_point_items(value: object, *, max_items: int) -> tuple[dict[str, Any], ...]:
    items = [
        {
            "loss_point_id": _clean(item.get("loss_point_id"), max_chars=120),
            "reason": _clean(item.get("reason"), max_chars=240),
            "deduction": _number(item.get("deduction") or item.get("deducted_points")),
        }
        for item in _dict_items(value)
    ]
    return tuple(sorted(items, key=lambda item: item["loss_point_id"])[:max_items])


def _source_sort_key(item: dict[str, Any]) -> tuple[int, int, str, str]:
    priority = item.get("priority")
    index = item.get("index")
    return (
        priority if isinstance(priority, int) else 1000,
        index if isinstance(index, int) else 1000,
        str(item.get("source_type") or ""),
        str(item.get("ref") or ""),
    )


def _answer_sort_key(item: dict[str, Any]) -> tuple[int, str]:
    round_value = item.get("answer_round")
    return (round_value if isinstance(round_value, int) else -1, str(item.get("answer_id") or ""))


def _turn_sort_key(item: dict[str, Any]) -> tuple[str, int, str]:
    round_value = item.get("answer_round")
    return (
        str(item.get("question_id") or ""),
        round_value if isinstance(round_value, int) else -1,
        str(item.get("answer_id") or ""),
    )


def _asset_sort_key(item: dict[str, Any]) -> tuple[int, str, str]:
    priority = item.get("priority")
    return (
        priority if isinstance(priority, int) else 1000,
        str(item.get("asset_type") or ""),
        str(item.get("asset_id") or ""),
    )


def _rag_sort_key(item: dict[str, Any]) -> tuple[str, str]:
    return (str(item.get("source_ref") or ""), str(item.get("chunk_id") or ""))
