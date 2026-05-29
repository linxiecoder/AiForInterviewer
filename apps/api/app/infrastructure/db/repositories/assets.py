"""SQLAlchemy repository for Asset list/detail and explicit archive actions."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.assets.ports import AssetActionError, AssetRepository
from app.domain.shared.clock import utc_now
from app.domain.shared.ids import ResourceIdPrefix, generate_resource_id
from app.domain.shared.refs import ResourceRef
from app.infrastructure.db.models.asset import Asset, AssetVersion
from app.infrastructure.db.models.rag import RagChunk, RagDocument
from app.infrastructure.db.models.reference import UserConfirmation
from app.infrastructure.db.repositories.base import SqlAlchemyRepository
from app.infrastructure.db.session import get_session_factory


class SqlAlchemyAssetRepository(SqlAlchemyRepository, AssetRepository):
    def __init__(
        self,
        session_factory: sessionmaker[Session] | None = None,
        *,
        session: Session | None = None,
    ) -> None:
        super().__init__(session_factory, session=session)

    def get_ref(self, asset_id: str) -> ResourceRef | None:
        with self.session_scope() as session:
            found = session.get(Asset, asset_id)
        if found is None or found.status == "deleted":
            return None
        return ResourceRef(resource_type="asset", resource_id=asset_id)

    def list_assets(
        self,
        *,
        owner_id: str,
        status: str | None = None,
        asset_type: str | None = None,
        q: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        with self.session_scope() as session:
            query = select(Asset).where(Asset.owner_id == owner_id, Asset.status != "deleted")
            if status is not None:
                query = query.where(Asset.status == status)
            if asset_type is not None:
                query = query.where(Asset.asset_type == asset_type)
            rows = session.scalars(query.order_by(Asset.updated_at.desc(), Asset.id)).all()
            filtered = _filter_assets_by_query(rows, q)
            return tuple(_asset_response(asset, versions=()) for asset in filtered)

    def get_asset(self, *, owner_id: str, asset_id: str) -> dict[str, Any] | None:
        with self.session_scope() as session:
            asset = _get_asset(session, owner_id=owner_id, asset_id=asset_id)
            if asset is None:
                return None
            versions = session.scalars(
                select(AssetVersion)
                .where(
                    AssetVersion.owner_id == owner_id,
                    AssetVersion.asset_id == asset.id,
                )
                .order_by(AssetVersion.version_number.desc(), AssetVersion.created_at.desc())
            ).all()
            return _asset_response(asset, versions=versions, include_content=True)

    def create_asset(
        self,
        *,
        owner_id: str,
        actor_id: str,
        title: str,
        asset_type: str,
        content: str,
        summary: str | None,
        rag_chunks: tuple[dict[str, Any], ...],
        embedding_model: str,
        embedding_dimension: int,
    ) -> dict[str, Any]:
        with self.session_scope() as session:
            try:
                now = utc_now()
                asset_id = generate_resource_id(ResourceIdPrefix.ASSET)
                version_id = f"assetver_{uuid4().hex[:24]}"
                document_id = f"ragdoc_{uuid4().hex[:24]}"
                asset = Asset(
                    id=asset_id,
                    owner_id=owner_id,
                    actor_id=actor_id,
                    record_version=1,
                    status="asset_confirmed",
                    created_at=now,
                    updated_at=now,
                    trace_ref_ids=[],
                    evidence_ref_ids=[],
                    normalized_title=_normalize_title(title),
                    asset_type=asset_type,
                    title=title,
                    summary=summary,
                    content=content,
                    current_version_id=version_id,
                    source_refs_json=[{"resource_type": "manual_input", "resource_id": asset_id}],
                    evidence_refs_json=[],
                    trace_refs_json=[],
                    fact_source="manual_asset_create",
                )
                version = AssetVersion(
                    id=version_id,
                    owner_id=owner_id,
                    actor_id=actor_id,
                    record_version=1,
                    status="current",
                    created_at=now,
                    updated_at=now,
                    trace_ref_ids=[],
                    evidence_ref_ids=[],
                    asset_id=asset_id,
                    version_number=1,
                    content=content,
                    edit_summary=summary or "手动新增资产首版",
                    created_by_actor_id=actor_id,
                )
                document = RagDocument(
                    id=document_id,
                    owner_id=owner_id,
                    actor_id=actor_id,
                    record_version=1,
                    status="active",
                    created_at=now,
                    updated_at=now,
                    trace_ref_ids=[],
                    evidence_ref_ids=[],
                    source_type="asset",
                    source_id=asset_id,
                    title=title,
                    metadata_json={
                        "asset_id": asset_id,
                        "asset_type": asset_type,
                        "asset_version_id": version_id,
                        "ingestion_mode": "sync_manual_create",
                    },
                )
                session.add_all([asset, version, document])
                for chunk in rag_chunks:
                    chunk_id = f"ragchk_{uuid4().hex[:24]}"
                    session.add(
                        RagChunk(
                            id=chunk_id,
                            owner_id=owner_id,
                            actor_id=actor_id,
                            record_version=1,
                            status="active",
                            created_at=now,
                            updated_at=now,
                            trace_ref_ids=[],
                            evidence_ref_ids=[],
                            document_id=document_id,
                            source_type="asset",
                            source_id=asset_id,
                            asset_id=asset_id,
                            chunk_index=int(chunk["chunk_index"]),
                            heading_path_json=list(chunk["heading_path"]),
                            content=str(chunk["content"]),
                            char_count=int(chunk["char_count"]),
                            metadata_json={
                                "asset_type": asset_type,
                                "asset_version_id": version_id,
                            },
                            embedding=chunk["embedding"],
                            embedding_model=embedding_model,
                            embedding_dimension=embedding_dimension,
                        )
                    )
                session.commit()
                return _asset_response(asset, versions=[version], include_content=True)
            except Exception as exc:
                session.rollback()
                raise AssetActionError(
                    code="internal_error",
                    message="Asset creation failed.",
                ) from exc

    def update_status(
        self,
        *,
        owner_id: str,
        actor_id: str,
        asset_id: str,
        status: str,
        action: str,
    ) -> dict[str, Any]:
        with self.session_scope() as session:
            try:
                asset = _get_asset(session, owner_id=owner_id, asset_id=asset_id)
                if asset is None:
                    _not_found()
                now = utc_now()
                previous_status = asset.status
                if previous_status == status:
                    return _asset_response(asset, versions=(), include_content=True)
                if not _is_allowed_status_transition(previous_status=previous_status, action=action):
                    raise AssetActionError(
                        code="validation_failed",
                        message="Asset status does not support this action.",
                    )
                asset.status = status
                asset.updated_at = now
                confirmation_ref = _create_confirmation(
                    session=session,
                    owner_id=owner_id,
                    actor_id=actor_id,
                    target_ref_id=asset.id,
                    action=action,
                    before_summary=previous_status,
                    after_summary=status,
                    trace_ref_ids=asset.trace_ref_ids,
                    evidence_ref_ids=asset.evidence_ref_ids,
                )
                asset.user_confirmation_ref_json = confirmation_ref
                session.commit()
                return _asset_response(asset, versions=(), include_content=True)
            except Exception:
                session.rollback()
                raise

    def soft_delete(
        self,
        *,
        owner_id: str,
        actor_id: str,
        asset_id: str,
    ) -> dict[str, Any]:
        with self.session_scope() as session:
            try:
                asset = _get_asset(session, owner_id=owner_id, asset_id=asset_id)
                if asset is None:
                    _not_found()
                now = utc_now()
                previous_status = asset.status
                asset.status = "deleted"
                asset.updated_at = now
                confirmation_ref = _create_confirmation(
                    session=session,
                    owner_id=owner_id,
                    actor_id=actor_id,
                    target_ref_id=asset.id,
                    action="delete_asset",
                    before_summary=previous_status,
                    after_summary="deleted",
                    trace_ref_ids=asset.trace_ref_ids,
                    evidence_ref_ids=asset.evidence_ref_ids,
                )
                asset.user_confirmation_ref_json = confirmation_ref
                session.commit()
                return _asset_response(asset, versions=(), include_content=True)
            except Exception:
                session.rollback()
                raise

    @classmethod
    def clear_state(cls) -> None:
        session_factory = get_session_factory()
        with session_factory() as session:
            session.execute(delete(RagChunk))
            session.execute(delete(RagDocument))
            session.execute(delete(AssetVersion))
            session.execute(delete(Asset))
            session.commit()


def _get_asset(session: Session, *, owner_id: str, asset_id: str) -> Asset | None:
    return session.scalar(
        select(Asset).where(Asset.owner_id == owner_id, Asset.id == asset_id, Asset.status != "deleted")
    )


def _asset_response(
    asset: Asset,
    *,
    versions: tuple[AssetVersion, ...] | list[AssetVersion],
    include_content: bool = False,
) -> dict[str, Any]:
    response = {
        "asset_id": asset.id,
        "owner_id": asset.owner_id,
        "status": asset.status,
        "asset_type": asset.asset_type,
        "title": asset.title,
        "summary": asset.summary,
        "current_version_id": asset.current_version_id,
        "source_refs": list(asset.source_refs_json or []),
        "evidence_refs": list(asset.evidence_refs_json or []),
        "trace_refs": list(asset.trace_refs_json or []),
        "resume_version_ref": asset.resume_version_ref_json,
        "job_version_ref": asset.job_version_ref_json,
        "question_pattern": asset.question_pattern,
        "created_from_candidate_id": asset.created_from_candidate_id,
        "user_confirmation_ref": asset.user_confirmation_ref_json,
        "fact_source": asset.fact_source,
        "created_at": asset.created_at.isoformat(),
        "updated_at": asset.updated_at.isoformat(),
    }
    if include_content:
        response["content"] = asset.content
        response["versions"] = [_asset_version_response(version) for version in versions]
    return response


def _asset_version_response(version: AssetVersion) -> dict[str, Any]:
    return {
        "asset_version_id": version.id,
        "asset_id": version.asset_id,
        "status": version.status,
        "version_number": version.version_number,
        "content": version.content,
        "edit_summary": version.edit_summary,
        "created_by_actor_id": version.created_by_actor_id,
        "created_from_candidate_id": version.created_from_candidate_id,
        "created_at": version.created_at.isoformat(),
        "updated_at": version.updated_at.isoformat(),
    }


def _filter_assets_by_query(rows: list[Asset], q: str | None) -> list[Asset]:
    needle = (q or "").strip().lower()
    if not needle:
        return rows
    return [asset for asset in rows if _asset_search_text(asset).find(needle) >= 0]


def _asset_search_text(asset: Asset) -> str:
    values: list[str] = [
        asset.title or "",
        asset.summary or "",
        asset.content or "",
        asset.asset_type or "",
        asset.status or "",
        asset.fact_source or "",
    ]
    values.extend(_json_ref_text(asset.source_refs_json))
    values.extend(_json_ref_text(asset.evidence_refs_json))
    return "\n".join(values).lower()


def _json_ref_text(refs: list[dict[str, Any]] | None) -> list[str]:
    values: list[str] = []
    for ref in refs or []:
        for value in ref.values():
            if isinstance(value, str):
                values.append(value)
    return values


def _normalize_title(title: str) -> str:
    return " ".join(title.strip().lower().split())


def _create_confirmation(
    *,
    session: Session,
    owner_id: str,
    actor_id: str,
    target_ref_id: str,
    action: str,
    before_summary: str,
    after_summary: str,
    trace_ref_ids: list[str] | None,
    evidence_ref_ids: list[str] | None,
) -> dict[str, str]:
    confirmation_id = f"uc_{uuid4().hex[:24]}"
    confirmation = UserConfirmation(
        id=confirmation_id,
        owner_id=owner_id,
        actor_id=actor_id,
        record_version=1,
        status="recorded",
        created_at=utc_now(),
        updated_at=utc_now(),
        trace_ref_ids=list(trace_ref_ids or []),
        evidence_ref_ids=list(evidence_ref_ids or []),
        target_ref_id=target_ref_id,
        audit_event_id=None,
        action=action,
        before_summary=before_summary,
        after_summary=after_summary,
    )
    session.add(confirmation)
    return {"resource_type": "user_confirmation", "resource_id": confirmation_id}


def _is_allowed_status_transition(*, previous_status: str, action: str) -> bool:
    if action == "archive_asset":
        return previous_status == "asset_confirmed"
    if action == "unarchive_asset":
        return previous_status == "asset_archived"
    return False


def _not_found() -> None:
    raise AssetActionError(code="not_found_or_inaccessible", message="Asset not found.")
