from __future__ import annotations

from typing import Any

from app.application.polish.canonical_evidence import CanonicalEvidenceService


OWNER_ID = "owner_phase2_contract"
SESSION_ID = "session_phase2_contract"


def test_canonical_evidence_pack_exposes_source_support_summary_and_derived_legacy_level() -> None:
    repository = _AssetRepository(
        [
            _asset(
                asset_id="asset_backend_workflow",
                title="Backend workflow automation",
                summary="FastAPI and PostgreSQL workflow reliability.",
            )
        ]
    )

    pack = CanonicalEvidenceService(repository).build_pack(
        owner_id=OWNER_ID,
        session_id=SESSION_ID,
        job_id="job_001",
        job_version_id="jobver_001",
        resume_id="resume_001",
        resume_version_id="resumever_001",
        progress_node_ref="progress_node_backend",
        query_inputs=("FastAPI PostgreSQL reliability",),
    )

    assert set(pack) >= {
        "schema_version",
        "owner_ref",
        "session_ref",
        "job_snapshot_ref",
        "resume_snapshot_ref",
        "progress_node_ref",
        "canonical_project_assets",
        "retrieved_rag_chunks",
        "prior_answer_refs",
        "prior_feedback_refs",
        "answer_attempt_refs",
        "source_support_summary",
        "warnings",
        "blocking_issues",
        "context_digest",
    }
    summary = pack["source_support_summary"]
    assert summary["level"] == "direct_project_evidence"
    assert summary["primary_evidence_refs"] == [
        {"resource_type": "asset", "resource_id": "asset_backend_workflow"}
    ]
    assert summary["adjacent_evidence_refs"] == []
    assert summary["job_gap_refs"] == []
    assert summary["missing_context"] == []
    assert summary["reason_codes"] == ["canonical_asset_confirmed"]
    assert summary["confidence"] == "high"
    assert summary["policy_version"]
    assert summary["computed_at"]
    assert pack["source_support_level"] == summary["level"]


def test_canonical_evidence_pack_digest_is_stable_and_covers_source_support_summary() -> None:
    repository = _AssetRepository(
        [
            _asset(
                asset_id="asset_backend_workflow",
                title="Backend workflow automation",
                summary="FastAPI and PostgreSQL workflow reliability.",
            )
        ]
    )

    service = CanonicalEvidenceService(repository)
    first = service.build_pack(
        owner_id=OWNER_ID,
        session_id=SESSION_ID,
        query_inputs=("FastAPI PostgreSQL reliability",),
    )
    second = service.build_pack(
        owner_id=OWNER_ID,
        session_id=SESSION_ID,
        query_inputs=("FastAPI PostgreSQL reliability",),
    )
    missing_support = CanonicalEvidenceService().build_pack(
        owner_id=OWNER_ID,
        session_id=SESSION_ID,
        query_inputs=("FastAPI PostgreSQL reliability",),
    )

    assert first["context_digest"] == second["context_digest"]
    assert first["source_support_summary"] != missing_support["source_support_summary"]
    assert first["context_digest"] != missing_support["context_digest"]


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


def _asset(
    *,
    asset_id: str,
    status: str = "asset_confirmed",
    asset_type: str = "project_story",
    title: str = "Backend workflow automation",
    summary: str = "FastAPI project fact.",
    content: str = "FastAPI and PostgreSQL workflow automation.",
) -> dict[str, Any]:
    return {
        "owner_id": OWNER_ID,
        "asset_id": asset_id,
        "status": status,
        "asset_type": asset_type,
        "title": title,
        "summary": summary,
        "content": content,
        "current_version_id": f"{asset_id}_v1",
        "source_refs": [{"resource_type": "review", "resource_id": "review_001"}],
        "evidence_refs": [{"resource_type": "answer", "resource_id": "answer_001"}],
    }
