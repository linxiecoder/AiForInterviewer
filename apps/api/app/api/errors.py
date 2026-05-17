"""HTTP error mapping helpers."""

from app.domain.shared.enums import API_ERROR_CODES
from app.domain.shared.ids import generate_request_id, generate_trace_id
from app.schemas.envelope import ApiError, ApiErrorEnvelope


def error_envelope(
    *,
    code: str,
    message: str,
    retryable: bool = False,
    user_action: str | None = None,
) -> ApiErrorEnvelope:
    if code not in API_ERROR_CODES:
        code = "internal_error"
    return ApiErrorEnvelope(
        request_id=generate_request_id(),
        trace_id=generate_trace_id(),
        error=ApiError(code=code, message=message, retryable=retryable, user_action=user_action),
    )

