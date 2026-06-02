"""Unified Polish interview context builders."""

from __future__ import annotations

from typing import Any

from app.application.polish.context.source_support import SourceSupportSummaryService


class InterviewContextBuilder:
    def __init__(self, *, source_support_service: SourceSupportSummaryService | None = None) -> None:
        self._source_support_service = source_support_service or SourceSupportSummaryService()

    def build_question_context(self, progress_context: dict[str, Any]) -> dict[str, Any]:
        context = dict(progress_context)
        canonical_project_assets = _canonical_project_assets(context)
        result = self._source_support_service.build(canonical_project_assets=canonical_project_assets)
        summary = result.summary.to_dict()
        context["source_support_summary"] = summary
        context["source_support_level"] = summary["level"]
        if result.warnings:
            context["warnings"] = _merge_sequence(context.get("warnings"), result.warnings)
        if result.blocking_issues:
            context["blocking_issues"] = _merge_dict_sequence(context.get("blocking_issues"), result.blocking_issues)

        pack = context.get("canonical_evidence_pack")
        if isinstance(pack, dict):
            canonical_pack = dict(pack)
            canonical_pack["source_support_summary"] = summary
            canonical_pack["source_support_level"] = summary["level"]
            if result.warnings:
                canonical_pack["warnings"] = _merge_sequence(canonical_pack.get("warnings"), result.warnings)
            if result.blocking_issues:
                canonical_pack["blocking_issues"] = _merge_dict_sequence(
                    canonical_pack.get("blocking_issues"),
                    result.blocking_issues,
                )
            context["canonical_evidence_pack"] = canonical_pack
        return context


def _canonical_project_assets(context: dict[str, Any]) -> dict[str, Any]:
    value = context.get("canonical_project_assets")
    if isinstance(value, dict):
        return value
    pack = context.get("canonical_evidence_pack")
    if isinstance(pack, dict) and isinstance(pack.get("canonical_project_assets"), dict):
        return pack["canonical_project_assets"]
    return {"available": False, "selection_policy": "rule_based_keyword_overlap_v1", "items": []}


def _merge_sequence(existing: object, additions: tuple[str, ...]) -> list[str]:
    values: list[str] = []
    if isinstance(existing, list):
        values.extend(str(item) for item in existing if str(item))
    elif isinstance(existing, tuple):
        values.extend(str(item) for item in existing if str(item))
    for item in additions:
        if item and item not in values:
            values.append(item)
    return values


def _merge_dict_sequence(existing: object, additions: tuple[dict[str, str], ...]) -> list[dict[str, str]]:
    values: list[dict[str, str]] = []
    if isinstance(existing, list):
        values.extend(dict(item) for item in existing if isinstance(item, dict))
    elif isinstance(existing, tuple):
        values.extend(dict(item) for item in existing if isinstance(item, dict))
    for item in additions:
        copied = dict(item)
        if copied not in values:
            values.append(copied)
    return values
