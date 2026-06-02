from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

API_SRC = Path(__file__).resolve().parents[2] / "apps" / "api"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from app.application.polish.canonical_evidence import CanonicalEvidenceService
from app.application.polish.context.source_support import SourceSupportSummaryService


OWNER_ID = "owner_phase2_eval_seed"


def test_phase2_source_support_eval_seed_matrix_covers_all_levels_and_asset_rules() -> None:
    cases: tuple[dict[str, Any], ...] = (
        {
            "case_id": "phase2_direct_confirmed_asset",
            "kwargs": {
                "canonical_project_assets": {
                    "available": True,
                    "items": [{"asset_id": "asset_direct", "status": "asset_confirmed"}],
                }
            },
            "level": "direct_project_evidence",
            "reason": "canonical_asset_confirmed",
        },
        {
            "case_id": "phase2_adjacent_resume_project",
            "kwargs": {
                "evidence_chunks": (
                    {
                        "chunk_id": "resume_project_adjacent",
                        "source_type": "resume_project",
                        "text": "候选人做过后台自动化，但未直接覆盖目标能力。",
                    },
                )
            },
            "level": "adjacent_project_evidence",
            "reason": "project_evidence_without_confirmed_canonical_asset",
        },
        {
            "case_id": "phase2_job_gap_only",
            "kwargs": {
                "evidence_chunks": (
                    {"chunk_id": "match_gap_payment", "source_type": "match_gap", "text": "岗位缺口：支付可靠性。"},
                )
            },
            "level": "job_gap_only",
            "reason": "job_gap_without_project_evidence",
        },
        {
            "case_id": "phase2_insufficient_context",
            "kwargs": {},
            "level": "insufficient_context",
            "reason": "no_confirmed_canonical_asset",
        },
    )

    observed_levels: set[str] = set()
    for case in cases:
        result = SourceSupportSummaryService().build(**case["kwargs"])
        summary = result.summary.to_dict()
        observed_levels.add(summary["level"])
        assert summary["level"] == case["level"], case["case_id"]
        assert case["reason"] in summary["reason_codes"], case["case_id"]

    assert observed_levels == {
        "direct_project_evidence",
        "adjacent_project_evidence",
        "job_gap_only",
        "insufficient_context",
    }

    archived_result = SourceSupportSummaryService().build(
        canonical_project_assets={
            "available": True,
            "items": [{"asset_id": "asset_archived", "status": "asset_archived"}],
        }
    )
    assert archived_result.summary.level == "insufficient_context"

    conflict_result = SourceSupportSummaryService().build(
        canonical_project_assets={
            "available": True,
            "items": [
                {"asset_id": "asset_a", "status": "asset_confirmed"},
                {"asset_id": "asset_b", "status": "asset_confirmed", "conflict_type": "technology_stack_conflict"},
            ],
        }
    )
    assert conflict_result.summary.level == "insufficient_context"
    assert conflict_result.blocking_issues[0]["hitl_required"] == "true"

    answer_result = SourceSupportSummaryService().build(
        current_answer_refs=({"resource_type": "answer", "resource_id": "answer_current"},)
    )
    assert answer_result.summary.level == "insufficient_context"
    assert answer_result.warnings == ("current_answer_not_canonical_evidence",)


def test_phase2_canonical_evidence_eval_seed_keeps_context_digest_stable_and_summary_sensitive() -> None:
    repository = _AssetRepository(
        [
            _asset(asset_id="asset_backend", summary="FastAPI PostgreSQL workflow."),
        ]
    )
    service = CanonicalEvidenceService(repository)

    first = service.build_pack(owner_id=OWNER_ID, session_id="session_eval", query_inputs=("FastAPI",))
    second = service.build_pack(owner_id=OWNER_ID, session_id="session_eval", query_inputs=("FastAPI",))
    missing = CanonicalEvidenceService().build_pack(
        owner_id=OWNER_ID,
        session_id="session_eval",
        query_inputs=("FastAPI",),
    )

    assert first["context_digest"] == second["context_digest"]
    assert first["source_support_summary"]["level"] == "direct_project_evidence"
    assert missing["source_support_summary"]["level"] == "insufficient_context"
    assert first["context_digest"] != missing["context_digest"]


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
        del q
        return tuple(
            asset
            for asset in self._assets
            if asset["owner_id"] == owner_id
            and (status is None or asset["status"] == status)
            and (asset_type is None or asset["asset_type"] == asset_type)
        )

    def get_asset(self, *, owner_id: str, asset_id: str) -> dict[str, Any] | None:
        return next(
            (dict(asset) for asset in self._assets if asset["owner_id"] == owner_id and asset["asset_id"] == asset_id),
            None,
        )


def _asset(*, asset_id: str, summary: str) -> dict[str, Any]:
    return {
        "owner_id": OWNER_ID,
        "asset_id": asset_id,
        "status": "asset_confirmed",
        "asset_type": "project_story",
        "title": "Backend workflow",
        "summary": summary,
        "content": summary,
        "current_version_id": f"{asset_id}_v1",
    }
