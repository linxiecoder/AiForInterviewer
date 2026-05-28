"""Asset use cases."""

from typing import Any

from app.application.common.result import ApplicationResult
from app.application.embeddings.ports import EmbeddingProvider, EmbeddingProviderError
from app.application.rag.chunking import chunk_markdown_semantically
from app.application.assets.ports import AssetActionError, AssetRepository
from app.domain.shared.errors import DomainError


ASSET_STATUSES = {
    "asset_candidate_generated",
    "asset_confirmed",
    "asset_rejected",
    "asset_archived",
    "superseded",
    "disabled",
}

ASSET_TYPES = {
    "answer_material",
    "project_expression",
    "job_material",
    "feedback_summary",
    "project_story",
    "self_intro",
    "technical_note",
    "behavior_story",
}


class AssetUseCases:
    def __init__(self, repository: AssetRepository, *, embedding_provider: EmbeddingProvider | None = None) -> None:
        self._repository = repository
        self._embedding_provider = embedding_provider

    def bootstrap(self) -> ApplicationResult[str]:
        return ApplicationResult(value="asset_skeleton")

    def list_assets(
        self,
        *,
        owner_id: str,
        status: str | None = None,
        asset_type: str | None = None,
        q: str | None = None,
    ) -> ApplicationResult[tuple[dict[str, Any], ...]]:
        if status is not None and status not in ASSET_STATUSES:
            return ApplicationResult(
                error=DomainError(code="validation_failed", message="Unsupported asset status.")
            )
        if asset_type is not None and asset_type not in ASSET_TYPES:
            return ApplicationResult(
                error=DomainError(code="validation_failed", message="Unsupported asset type.")
            )
        return ApplicationResult(
            value=self._repository.list_assets(
                owner_id=owner_id,
                status=status,
                asset_type=asset_type,
                q=_normalize_optional(q),
            )
        )

    def create_asset(
        self,
        *,
        owner_id: str,
        actor_id: str,
        title: str,
        asset_type: str,
        content: str,
        summary: str | None = None,
    ) -> ApplicationResult[dict[str, Any]]:
        normalized_title = title.strip()
        normalized_content = content.strip()
        normalized_summary = _normalize_optional(summary)
        normalized_asset_type = asset_type.strip()
        if not normalized_title:
            return ApplicationResult(error=DomainError(code="validation_failed", message="Title cannot be empty."))
        if not normalized_content:
            return ApplicationResult(error=DomainError(code="validation_failed", message="Asset content cannot be empty."))
        if normalized_asset_type not in ASSET_TYPES:
            return ApplicationResult(error=DomainError(code="validation_failed", message="Unsupported asset type."))
        if self._embedding_provider is None:
            return ApplicationResult(error=DomainError(code="provider_unavailable", message="Embedding provider is not configured."))

        chunk_drafts = chunk_markdown_semantically(normalized_content)
        embedding_inputs = tuple(chunk.embedding_input for chunk in chunk_drafts)
        try:
            embedding_result = self._embedding_provider.embed_texts(embedding_inputs)
            _validate_embedding_result(embedding_result, expected_count=len(chunk_drafts))
        except EmbeddingProviderError as exc:
            return ApplicationResult(error=DomainError(code="provider_unavailable", message=str(exc)))
        except ValueError as exc:
            return ApplicationResult(error=DomainError(code="provider_unavailable", message=str(exc)))

        rag_chunks = tuple(
            {
                "chunk_index": chunk.chunk_index,
                "heading_path": list(chunk.heading_path),
                "content": chunk.content,
                "char_count": chunk.char_count,
                "embedding": embedding_result.vectors[index],
            }
            for index, chunk in enumerate(chunk_drafts)
        )
        try:
            return ApplicationResult(
                value=self._repository.create_asset(
                    owner_id=owner_id,
                    actor_id=actor_id,
                    title=normalized_title,
                    asset_type=normalized_asset_type,
                    content=normalized_content,
                    summary=normalized_summary,
                    rag_chunks=rag_chunks,
                    embedding_model=embedding_result.model,
                    embedding_dimension=embedding_result.dimension,
                )
            )
        except AssetActionError as exc:
            return ApplicationResult(error=DomainError(code=exc.code, message=exc.message))

    def get_asset(self, *, owner_id: str, asset_id: str) -> ApplicationResult[dict[str, Any]]:
        asset = self._repository.get_asset(owner_id=owner_id, asset_id=asset_id)
        if asset is None:
            return ApplicationResult(
                error=DomainError(code="not_found_or_inaccessible", message="Asset not found.")
            )
        return ApplicationResult(value=asset)

    def archive_asset(
        self,
        *,
        owner_id: str,
        actor_id: str,
        asset_id: str,
    ) -> ApplicationResult[dict[str, Any]]:
        return self._update_status(
            owner_id=owner_id,
            actor_id=actor_id,
            asset_id=asset_id,
            status="asset_archived",
            action="archive_asset",
        )

    def unarchive_asset(
        self,
        *,
        owner_id: str,
        actor_id: str,
        asset_id: str,
    ) -> ApplicationResult[dict[str, Any]]:
        return self._update_status(
            owner_id=owner_id,
            actor_id=actor_id,
            asset_id=asset_id,
            status="asset_confirmed",
            action="unarchive_asset",
        )

    def _update_status(
        self,
        *,
        owner_id: str,
        actor_id: str,
        asset_id: str,
        status: str,
        action: str,
    ) -> ApplicationResult[dict[str, Any]]:
        try:
            return ApplicationResult(
                value=self._repository.update_status(
                    owner_id=owner_id,
                    actor_id=actor_id,
                    asset_id=asset_id,
                    status=status,
                    action=action,
                )
            )
        except AssetActionError as exc:
            return ApplicationResult(error=DomainError(code=exc.code, message=exc.message))


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _validate_embedding_result(result, *, expected_count: int) -> None:
    if len(result.vectors) != expected_count:
        raise ValueError("Embedding provider returned an unexpected vector count.")
    if result.dimension <= 0:
        raise ValueError("Embedding provider returned an invalid dimension.")
    for vector in result.vectors:
        if len(vector) != result.dimension:
            raise ValueError("Embedding provider returned a vector with unexpected dimension.")
