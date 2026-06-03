"""Application adapter for Polish question grounding policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.application.polish.question_blueprint import QuestionBlueprint
from app.domain.polish.policies.question_grounding_policy import (
    QuestionGroundingInput,
    QuestionGroundingPolicy,
)


@dataclass(frozen=True)
class GroundingResult:
    passed: bool
    validation_errors: tuple[str, ...] = ()
    blocking_errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


def validate_question_grounding(
    *,
    blueprint: QuestionBlueprint,
    question_text: str,
    primary_source_type: str | None,
    source_support_level: str | None = None,
    evidence_refs: tuple[str, ...] = (),
    canonical_project_assets: dict[str, Any] | None = None,
) -> GroundingResult:
    decision = QuestionGroundingPolicy.evaluate(
        QuestionGroundingInput(
            question_text=question_text,
            claim_mode=blueprint.claim_mode,
            primary_evidence_ref=blueprint.primary_evidence_ref,
            primary_evidence_text=blueprint.primary_evidence_text,
            evidence_refs=tuple(ref for ref in evidence_refs if str(ref).strip()),
            primary_source_type=primary_source_type,
            source_support_level=source_support_level,
            confirmed_asset_texts=_canonical_asset_texts(canonical_project_assets),
        )
    )
    return GroundingResult(
        passed=decision.passed,
        validation_errors=decision.reason_codes,
        blocking_errors=decision.blocking_reason_codes,
        warnings=decision.warning_reason_codes,
    )


def _canonical_asset_texts(canonical_project_assets: dict[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(canonical_project_assets, dict):
        return ()
    items = canonical_project_assets.get("items") if isinstance(canonical_project_assets.get("items"), list) else []
    parts: list[str] = []
    for item in items[:5]:
        if not isinstance(item, dict):
            continue
        if str(item.get("status") or "").strip() != "asset_confirmed":
            continue
        parts.extend(
            str(item.get(key) or "")
            for key in ("title", "summary", "content_excerpt")
            if str(item.get(key) or "").strip()
        )
    return tuple(parts)
