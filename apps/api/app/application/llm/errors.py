"""Application-level LLM transport exceptions."""


class LlmTransportError(RuntimeError):
    """Base error raised by LLM transports."""


class LlmTransportConfigurationError(LlmTransportError):
    """Raised when local LLM configuration is missing or invalid."""


class LlmTransportUnavailableError(LlmTransportError):
    """Raised when the provider cannot be reached or rejects a request."""


class LlmTransportResponseError(LlmTransportError):
    """Raised when the provider returns an unusable response."""
