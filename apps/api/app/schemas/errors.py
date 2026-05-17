"""API error schemas and stable codes."""

from app.domain.shared.enums import API_ERROR_CODES
from app.schemas.envelope import ApiError, ApiErrorEnvelope

__all__ = ["API_ERROR_CODES", "ApiError", "ApiErrorEnvelope"]

