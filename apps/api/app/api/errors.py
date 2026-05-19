"""HTTP error mapping helpers."""

from typing import NoReturn

from fastapi import Request
from fastapi.responses import JSONResponse

from app.domain.shared.enums import API_ERROR_CODES
from app.domain.shared.ids import generate_request_id, generate_trace_id
from app.infrastructure.observability.http_logging import get_request_trace_context
from app.schemas.envelope import ApiError, ApiErrorEnvelope


class ApiHttpError(Exception):
    def __init__(self, *, status_code: int, envelope: ApiErrorEnvelope, headers: dict[str, str] | None = None) -> None:
        self.status_code = status_code
        self.envelope = envelope
        self.headers = headers or {}


def error_envelope(
    *,
    code: str,
    message: str,
    details: dict | None = None,
    retryable: bool = False,
    user_action: str | None = None,
) -> ApiErrorEnvelope:
    if code not in API_ERROR_CODES:
        code = "internal_error"
    context = get_request_trace_context()
    return ApiErrorEnvelope(
        request_id=(context.request_id if context else None) or generate_request_id(),
        trace_id=(context.trace_id if context else None) or generate_trace_id(),
        error=ApiError(
            code=code,
            message=message,
            details=details,
            retryable=retryable,
            user_action=user_action,
        ),
    )


def raise_api_error(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict | None = None,
    retryable: bool = False,
    user_action: str | None = None,
    headers: dict[str, str] | None = None,
) -> NoReturn:
    raise ApiHttpError(
        status_code=status_code,
        envelope=error_envelope(
            code=code,
            message=message,
            details=details,
            retryable=retryable,
            user_action=user_action,
        ),
        headers=headers,
    )


async def api_http_error_handler(_request: Request, exc: ApiHttpError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.envelope.model_dump(mode="json"),
        headers=exc.headers,
    )
