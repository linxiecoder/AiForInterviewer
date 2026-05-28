"""Asset API DTOs."""

from typing import Any

from pydantic import BaseModel, Field


class AssetResponse(BaseModel):
    asset_id: str
    status: str


class AssetListQuery(BaseModel):
    status: str | None = None
    asset_type: str | None = None
    q: str | None = None


class AssetCreateRequest(BaseModel):
    title: str = Field(max_length=160)
    asset_type: str = Field(max_length=64)
    content: str = Field(max_length=20000)
    summary: str | None = Field(default=None, max_length=2000)


class AssetActionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class AssetVersionResponse(BaseModel):
    asset_version_id: str
    asset_id: str
    status: str
    version_number: int
    content: str | None = None
    edit_summary: str | None = None
    created_by_actor_id: str | None = None
    created_from_candidate_id: str | None = None
    created_at: str
    updated_at: str


class AssetDetailResponse(AssetResponse):
    owner_id: str
    asset_type: str | None = None
    title: str | None = None
    summary: str | None = None
    content: str | None = None
    current_version_id: str | None = None
    source_refs: list[dict[str, Any]] = Field(default_factory=list)
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    trace_refs: list[dict[str, Any]] = Field(default_factory=list)
    resume_version_ref: dict[str, Any] | None = None
    job_version_ref: dict[str, Any] | None = None
    question_pattern: str | None = None
    created_from_candidate_id: str | None = None
    user_confirmation_ref: dict[str, Any] | None = None
    fact_source: str | None = None
    versions: list[AssetVersionResponse] = Field(default_factory=list)
    created_at: str
    updated_at: str
