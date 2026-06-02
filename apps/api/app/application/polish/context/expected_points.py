"""Expected-point construction for Polish feedback context."""

from __future__ import annotations

from typing import Any


class ExpectedPointsBuilder:
    def build(self, context: object) -> list[str]:
        question_metadata = _ctx_dict(context, "question_metadata")
        progress_node = _ctx_dict(context, "progress_node_snapshot")
        canonical_assets = _canonical_project_assets(context)
        job_snapshot = _ctx_dict(context, "job_snapshot")
        points: list[str] = []
        points.extend(_string_list(question_metadata.get("expected_answer_dimensions"), max_items=12, max_item_chars=240))
        points.append(_clean(progress_node.get("expected_capability"), max_chars=240))
        points.extend(_string_list(progress_node.get("missing_points"), max_items=8, max_item_chars=160))
        for item in _asset_items(canonical_assets):
            points.append(_clean(item.get("summary") or item.get("content_excerpt") or item.get("title"), max_chars=240))
        points.extend(_string_list(job_snapshot.get("requirements"), max_items=8, max_item_chars=180))
        return _unique([point for point in points if point])[:12]


def _ctx_dict(context: object, field_name: str) -> dict[str, Any]:
    value = context.get(field_name) if isinstance(context, dict) else getattr(context, field_name, None)
    return value if isinstance(value, dict) else {}


def _canonical_project_assets(context: object) -> dict[str, Any]:
    value = _ctx_dict(context, "canonical_project_assets")
    if not value:
        return {"available": False, "items": []}
    items = value.get("items")
    return {
        "available": bool(value.get("available")) and isinstance(items, list) and bool(items),
        "items": items if isinstance(items, list) else [],
    }


def _asset_items(canonical_assets: dict[str, Any]) -> list[dict[str, Any]]:
    items = canonical_assets.get("items")
    if not isinstance(items, list):
        return []
    return [
        item
        for item in items
        if isinstance(item, dict) and _clean(item.get("status"), max_chars=80) == "asset_confirmed"
    ][:5]


def _string_list(value: object, *, max_items: int = 20, max_item_chars: int = 240) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    result: list[str] = []
    for item in value[:max_items]:
        text = _clean(item, max_chars=max_item_chars)
        if text:
            result.append(text)
    return result


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def _clean(value: object, *, max_chars: int = 240) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text
