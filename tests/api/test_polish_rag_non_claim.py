from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.application.polish.canonical_evidence import CanonicalEvidenceService
from app.application.polish.feedback_prompt_assets import build_feedback_prompt_asset
from app.application.polish.question_blueprint import EvidenceScope, QuestionBlueprint
from app.application.polish.question_generation_prompts import (
    build_question_prompt_asset,
    build_question_provider_request,
)


OWNER_ID = "owner_rag_non_claim"
SESSION_ID = "session_rag_non_claim"


def test_canonical_pack_marks_rag_chunks_unavailable_without_claiming_retrieval() -> None:
    pack = CanonicalEvidenceService(_AssetRepository([_asset()])).build_pack(
        owner_id=OWNER_ID,
        session_id=SESSION_ID,
        query_inputs=("FastAPI PostgreSQL workflow reliability",),
    )

    rag_chunks = pack["retrieved_rag_chunks"]

    assert rag_chunks["available"] is False
    assert rag_chunks["items"] == []
    assert rag_chunks["unavailable_reason"] == "full_retrieval_not_enabled"
    assert rag_chunks["user_message"] == "资产已保存，但本次生成未启用知识库检索。"
    assert rag_chunks["non_claim_policy"] == "canonical_project_assets_are_not_retrieved_rag_chunks"


def test_question_prompt_carries_rag_unavailable_non_claim_separately_from_canonical_assets() -> None:
    canonical_assets = _canonical_assets()
    rag_chunks = _rag_chunks()
    scope = EvidenceScope(
        progress_node_ref="node_backend_workflow",
        node_title="后端工作流可靠性",
        expected_capability="说明真实实现链路和验证方式",
        canonical_project_assets=canonical_assets,
        retrieved_rag_chunks=rag_chunks,
        source_support_level="direct_project_evidence",
    )
    blueprint = QuestionBlueprint(
        question_kind="project_deep_dive",
        claim_mode="evidence_grounded",
        progress_node_ref="node_backend_workflow",
        node_title="后端工作流可靠性",
        expected_capability="说明真实实现链路和验证方式",
        primary_evidence_ref=None,
        primary_evidence_text=None,
        evidence_refs=(),
    )

    prompt_asset = build_question_prompt_asset(blueprint, scope)
    provider_request = build_question_provider_request(prompt_asset, blueprint=blueprint, scope=scope)

    assert prompt_asset["input_data"]["canonical_project_assets"]["available"] is True
    assert prompt_asset["input_data"]["retrieved_rag_chunks"] == rag_chunks
    assert provider_request["canonical_evidence"]["retrieved_rag_chunks"] == rag_chunks
    provider_json = json.dumps(provider_request, ensure_ascii=False, sort_keys=True)
    assert "资产已保存，但本次生成未启用知识库检索。" in provider_json
    assert "AI 已经检索并使用知识库" not in provider_json


def test_question_provider_request_exposes_compact_field_contracts_and_adjacent_rule() -> None:
    scope = EvidenceScope(
        progress_node_ref="node_backend_workflow",
        node_title="后端工作流可靠性",
        expected_capability="说明真实实现链路和验证方式",
        canonical_project_assets=_canonical_assets(),
        retrieved_rag_chunks=_rag_chunks(),
        source_support_level="adjacent_project_evidence",
    )
    blueprint = QuestionBlueprint(
        question_kind="project_deep_dive",
        claim_mode="evidence_grounded",
        progress_node_ref="node_backend_workflow",
        node_title="后端工作流可靠性",
        expected_capability="说明真实实现链路和验证方式",
        primary_evidence_ref="asset_backend_workflow",
        primary_evidence_text="Backend workflow automation uses FastAPI APIs and PostgreSQL persistence.",
        evidence_refs=("asset_backend_workflow",),
    )

    prompt_asset = build_question_prompt_asset(blueprint, scope)
    provider_request = build_question_provider_request(prompt_asset, blueprint=blueprint, scope=scope)

    assert "prompt" not in provider_request
    assert "output_schema" not in provider_request
    contract = provider_request["expected_output_contract"]
    field_contracts = contract["field_contracts"]
    assert {
        "question_text",
        "scoring_rubric",
        "confidence",
        "clarification_needed",
        "missing_context",
        "evidence_refs",
    }.issubset(field_contracts)
    assert field_contracts["scoring_rubric"]["items"] == {
        "type": "object",
        "required_fields": ["dimension", "signals"],
        "field_contracts": {
            "dimension": "string",
            "signals": "array<string>",
        },
        "do_not_use_fields": ["signal", "expected_signals"],
    }
    assert field_contracts["confidence"]["allowed"] == ["high", "medium", "low"]
    assert field_contracts["clarification_needed"]["true_only_when"] == (
        "resume_and_evidence_refs_unavailable_or_no_valid_question_text"
    )
    assert field_contracts["question_text"]["prefer_implementation_detail_or_technical_decision_first"] is True
    assert field_contracts["question_text"]["broad_tradeoff_should_move_to_follow_ups"] is True
    assert field_contracts["evidence_refs"]["allowed_refs"] == ["asset_backend_workflow"]
    assert field_contracts["evidence_refs"]["must_be_subset_of_allowed_refs"] is True
    assert contract["adjacent_project_evidence_rule"]["hypothetical_wording_required"] is True
    assert contract["adjacent_project_evidence_rule"]["forbid_completed_experience_claim"] is True
    pacing_policy = contract["interview_pacing_policy"]
    assert pacing_policy["active_for_request"] is True
    assert pacing_policy["depth_progression"] == [
        "implementation_detail",
        "why_this_choice",
        "tradeoff_or_failure_follow_up",
    ]
    assert "复杂检索" in pacing_policy["avoid_in_main_question"][0]
    assert provider_request["safety_rules_summary"]["adjacent_project_evidence_rule"] == (
        "use hypothetical wording; do not state the candidate already implemented the target capability"
    )
    assert "broad tradeoffs in follow_ups" in provider_request["safety_rules_summary"]["real_interview_pacing"]


def test_feedback_prompt_carries_rag_unavailable_non_claim_separately_from_canonical_assets() -> None:
    rag_chunks = _rag_chunks()
    prompt_asset = build_feedback_prompt_asset(
        {
            "owner_id": OWNER_ID,
            "actor_id": "actor_rag_non_claim",
            "session_id": SESSION_ID,
            "question_id": "question_rag_non_claim",
            "answer_id": "answer_rag_non_claim",
            "question_text": "How did you build the backend workflow?",
            "answer_text": "I used FastAPI and PostgreSQL.",
            "canonical_project_assets": _canonical_assets(),
            "retrieved_rag_chunks": rag_chunks,
        }
    )

    assert prompt_asset["input_data"]["canonical_project_assets"]["available"] is True
    assert prompt_asset["input_data"]["retrieved_rag_chunks"] == rag_chunks
    assert prompt_asset["provider_prompt"]["retrieved_rag_chunks"] == rag_chunks
    provider_json = json.dumps(prompt_asset["provider_prompt"], ensure_ascii=False, sort_keys=True)
    assert "资产已保存，但本次生成未启用知识库检索。" in provider_json
    assert "AI 已经检索并使用知识库" not in provider_json


def test_polish_runtime_does_not_call_full_retrieval_from_rag_non_claim_slice() -> None:
    combined_source = "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in (
            "apps/api/app/application/polish/canonical_evidence.py",
            "apps/api/app/application/polish/progress_context.py",
            "apps/api/app/application/polish/question_generation_prompts.py",
            "apps/api/app/application/polish/feedback_prompt_assets.py",
        )
    )

    assert re.search(r"\b(vector_query|similarity_search|retrieve_chunks|rerank_chunks)\b", combined_source) is None


def _rag_chunks() -> dict[str, Any]:
    return {
        "available": False,
        "items": [],
        "unavailable_reason": "full_retrieval_not_enabled",
        "user_message": "资产已保存，但本次生成未启用知识库检索。",
        "non_claim_policy": "canonical_project_assets_are_not_retrieved_rag_chunks",
    }


def _canonical_assets() -> dict[str, Any]:
    return {
        "available": True,
        "selection_policy": "rule_based_keyword_overlap_v1",
        "items": [
            {
                "asset_id": "asset_backend_workflow",
                "status": "asset_confirmed",
                "asset_type": "project_story",
                "title": "Backend workflow automation",
                "summary": "Candidate built backend workflow automation with FastAPI and PostgreSQL.",
                "content_excerpt": "Owns FastAPI APIs, PostgreSQL persistence, retries, and observability.",
            }
        ],
    }


class _AssetRepository:
    def __init__(self, assets: list[dict[str, Any]]) -> None:
        self._assets = assets

    def list_assets(
        self,
        *,
        owner_id: str,
        status: str | None = None,
        asset_type: str | None = None,
        q: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        rows = [
            asset
            for asset in self._assets
            if asset["owner_id"] == owner_id
            and (status is None or asset["status"] == status)
            and (asset_type is None or asset["asset_type"] == asset_type)
        ]
        return tuple({key: value for key, value in asset.items() if key != "content"} for asset in rows)

    def get_asset(self, *, owner_id: str, asset_id: str) -> dict[str, Any] | None:
        return next(
            (
                dict(asset)
                for asset in self._assets
                if asset["owner_id"] == owner_id and asset["asset_id"] == asset_id
            ),
            None,
        )


def _asset() -> dict[str, Any]:
    return {
        "owner_id": OWNER_ID,
        "asset_id": "asset_backend_workflow",
        "status": "asset_confirmed",
        "asset_type": "project_story",
        "title": "Backend workflow automation",
        "summary": "FastAPI and PostgreSQL project fact.",
        "content": "FastAPI and PostgreSQL workflow automation.",
        "current_version_id": "asset_backend_workflow_v1",
        "source_refs": [{"resource_type": "review", "resource_id": "review_001"}],
        "evidence_refs": [{"resource_type": "answer", "resource_id": "answer_001"}],
    }
