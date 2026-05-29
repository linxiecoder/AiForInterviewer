"""Asset HTTP adapters."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db_session_factory, get_embedding_provider, require_authenticated_actor
from app.api.envelope import success_envelope
from app.api.errors import raise_api_error
from app.application.embeddings.ports import EmbeddingProvider
from app.application.assets.use_cases import AssetUseCases
from app.domain.auth.entities import CurrentActor
from app.domain.shared.errors import DomainError
from app.infrastructure.db.repositories.assets import SqlAlchemyAssetRepository
from app.schemas.assets import AssetActionRequest, AssetCreateRequest

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("")
async def list_assets(
    status: str | None = Query(default=None),
    asset_type: str | None = Query(default=None),
    q: str | None = Query(default=None),
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    result = _use_cases(session_factory).list_assets(
        owner_id=actor.owner_id,
        status=status,
        asset_type=asset_type,
        q=q,
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(resource_type="asset_list", data=list(result.value or ()))


@router.post("")
async def create_asset(
    payload: AssetCreateRequest,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
) -> Any:
    result = _use_cases(session_factory, embedding_provider=embedding_provider).create_asset(
        owner_id=actor.owner_id,
        actor_id=actor.actor_id,
        title=payload.title,
        asset_type=payload.asset_type,
        content=payload.content,
        summary=payload.summary,
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(resource_type="asset_detail", data=result.value)


@router.get("/{asset_id}")
async def get_asset(
    asset_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    result = _use_cases(session_factory).get_asset(owner_id=actor.owner_id, asset_id=asset_id)
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(resource_type="asset_detail", data=result.value)


@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    result = _use_cases(session_factory).soft_delete_asset(
        owner_id=actor.owner_id,
        actor_id=actor.actor_id,
        asset_id=asset_id,
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(resource_type="asset_detail", data=result.value)


@router.post("/{asset_id}/archive")
async def archive_asset(
    asset_id: str,
    _payload: AssetActionRequest | None = None,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    result = _use_cases(session_factory).archive_asset(
        owner_id=actor.owner_id,
        actor_id=actor.actor_id,
        asset_id=asset_id,
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(resource_type="asset_detail", data=result.value)


@router.post("/{asset_id}/unarchive")
async def unarchive_asset(
    asset_id: str,
    _payload: AssetActionRequest | None = None,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    result = _use_cases(session_factory).unarchive_asset(
        owner_id=actor.owner_id,
        actor_id=actor.actor_id,
        asset_id=asset_id,
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(resource_type="asset_detail", data=result.value)


def _use_cases(
    session_factory: sessionmaker[Session],
    *,
    embedding_provider: EmbeddingProvider | None = None,
) -> AssetUseCases:
    return AssetUseCases(
        repository=SqlAlchemyAssetRepository(session_factory),
        embedding_provider=embedding_provider,
    )


def _raise_result_error(error: DomainError | None) -> None:
    if error is None:
        raise_api_error(status_code=500, code="internal_error", message="Unknown asset error.")
    status_code = _error_status(error.code)
    raise_api_error(status_code=status_code, code=error.code, message=error.message)


def _error_status(code: str) -> int:
    if code == "not_found_or_inaccessible":
        return 404
    if code == "validation_failed":
        return 422
    if code == "provider_unavailable":
        return 502
    if code == "internal_error":
        return 500
    if code.endswith("_conflict"):
        return 409
    return 400
