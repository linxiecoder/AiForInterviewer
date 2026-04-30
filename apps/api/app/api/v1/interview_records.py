"""R0 interview record routes for save, restore, history, review, and export trace."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.interview_record_contract import (
    DEFAULT_RECORD_SOURCE,
    DEFAULT_RECORD_VERSION,
    ERROR_INTERVIEW_RECORD_NOT_FOUND,
    FIELD_CREATED_AT,
    FIELD_ID,
    FIELD_OWNER_ID,
    FIELD_PAYLOAD,
    FIELD_SOURCE,
    FIELD_UPDATED_AT,
    FIELD_VERSION,
    INTERVIEW_RECORDS_ROUTE_PREFIX,
    PAYLOAD_EXPORT,
    PAYLOAD_REVIEW,
    RECORD_EXPORT_TRACE_ROUTE,
    RECORD_ID_ROUTE,
    RECORD_REVIEW_ROUTE,
    RESPONSE_ITEMS,
)
from app.persistence import InterviewRecordStore

router = APIRouter(prefix=INTERVIEW_RECORDS_ROUTE_PREFIX, tags=["interview-records"])


class InterviewRecordCreate(BaseModel):
    """Input body for the minimal R0 interview record save operation."""

    owner_id: str = Field(min_length=1)
    source: str = Field(default=DEFAULT_RECORD_SOURCE, min_length=1)
    version: int = Field(default=DEFAULT_RECORD_VERSION, ge=1)
    payload: dict[str, Any] = Field(default_factory=dict)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_interview_record(
    request: Request,
    body: InterviewRecordCreate,
) -> dict[str, Any]:
    """Save one interview record payload with traceability metadata."""
    return _store(request).create_record(
        owner_id=body.owner_id,
        source=body.source,
        version=body.version,
        payload=body.payload,
    )


@router.get("")
async def list_interview_records(
    request: Request,
    owner_id: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Return the minimal R0 history list, optionally filtered by owner_id."""
    return {RESPONSE_ITEMS: _store(request).list_records(owner_id=owner_id)}


@router.get(RECORD_ID_ROUTE)
async def get_interview_record(request: Request, record_id: str) -> dict[str, Any]:
    """Restore one saved interview record by id."""
    return _record_or_404(request, record_id)


@router.get(RECORD_REVIEW_ROUTE)
async def get_interview_record_review(request: Request, record_id: str) -> dict[str, Any]:
    """Read the review fragment from a saved interview record."""
    record = _record_or_404(request, record_id)
    payload = _payload_dict(record)
    review = payload.get(PAYLOAD_REVIEW) if isinstance(payload.get(PAYLOAD_REVIEW), dict) else {}
    return {
        FIELD_ID: record[FIELD_ID],
        FIELD_OWNER_ID: record[FIELD_OWNER_ID],
        FIELD_SOURCE: record[FIELD_SOURCE],
        FIELD_VERSION: record[FIELD_VERSION],
        PAYLOAD_REVIEW: review,
        FIELD_CREATED_AT: record[FIELD_CREATED_AT],
        FIELD_UPDATED_AT: record[FIELD_UPDATED_AT],
    }


@router.get(RECORD_EXPORT_TRACE_ROUTE)
async def get_interview_record_export_trace(request: Request, record_id: str) -> dict[str, Any]:
    """Read export traceability metadata from a saved interview record."""
    record = _record_or_404(request, record_id)
    payload = _payload_dict(record)
    export = payload.get(PAYLOAD_EXPORT) if isinstance(payload.get(PAYLOAD_EXPORT), dict) else {}
    return {
        FIELD_ID: record[FIELD_ID],
        FIELD_OWNER_ID: record[FIELD_OWNER_ID],
        FIELD_SOURCE: record[FIELD_SOURCE],
        FIELD_VERSION: record[FIELD_VERSION],
        PAYLOAD_EXPORT: export,
        FIELD_CREATED_AT: record[FIELD_CREATED_AT],
        FIELD_UPDATED_AT: record[FIELD_UPDATED_AT],
    }


def _store(request: Request) -> InterviewRecordStore:
    return request.app.state.interview_record_store


def _payload_dict(record: dict[str, Any]) -> dict[str, Any]:
    payload = record.get(FIELD_PAYLOAD)
    return payload if isinstance(payload, dict) else {}


def _record_or_404(request: Request, record_id: str) -> dict[str, Any]:
    record = _store(request).get_record(record_id)
    if record is None:
        # Keep the existing HTTPException path so the app-wide error envelope
        # remains the single response-shape adapter.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_INTERVIEW_RECORD_NOT_FOUND,
        )
    return record
