"""Envelope builders for HTTP adapters."""

from typing import Any

from app.domain.shared.enums import ApiStatus
from app.domain.shared.ids import generate_request_id, generate_trace_id
from app.schemas.envelope import ApiSuccessEnvelope


def success_envelope(
    *,
    resource_type: str,
    data: Any,
    status: ApiStatus = ApiStatus.SUCCESS,
    request_id: str | None = None,
    trace_id: str | None = None,
) -> ApiSuccessEnvelope:
    return ApiSuccessEnvelope(
        request_id=request_id or generate_request_id(),
        trace_id=trace_id or generate_trace_id(),
        status=status,
        resource_type=resource_type,
        data=data,
    )

