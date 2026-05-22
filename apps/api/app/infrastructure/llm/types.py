"""Compatibility re-exports for application-level LLM DTOs."""

from app.application.llm.types import LlmTransportRequest, LlmTransportResult

__all__ = ["LlmTransportRequest", "LlmTransportResult"]
