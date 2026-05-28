"""Weakness API DTOs."""

from typing import Any

from pydantic import BaseModel, Field


class WeaknessResponse(BaseModel):
    weakness_id: str
    status: str


class WeaknessListQuery(BaseModel):
    status: str | None = None
    severity: str | None = None
    q: str | None = None


class UpdateWeaknessStatusRequest(BaseModel):
    status: str = Field(min_length=1, max_length=64)


class WeaknessDetailResponse(WeaknessResponse):
    owner_id: str
    title: str | None = None
    summary: str | None = None
    severity: str | None = None
    confidence_level: str | None = None
    dimension: str | None = None
    source_refs: list[dict[str, Any]] = Field(default_factory=list)
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    trace_refs: list[dict[str, Any]] = Field(default_factory=list)
    related_refs: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    occurrence_count: int
    first_seen_at: str | None = None
    last_seen_at: str | None = None
    archived_at: str | None = None
    created_from_candidate_id: str | None = None
    user_confirmation_ref: dict[str, Any] | None = None
    suggested_training_actions: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
