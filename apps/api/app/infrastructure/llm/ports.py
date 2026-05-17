"""LLM transport protocol."""

from typing import Protocol

from app.infrastructure.llm.types import LlmTransportRequest, LlmTransportResult


class LlmTransport(Protocol):
    def generate(self, request: LlmTransportRequest) -> LlmTransportResult: ...

