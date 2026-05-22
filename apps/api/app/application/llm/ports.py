"""Application-level LLM transport protocol."""

from typing import Protocol

from app.application.llm.types import LlmTransportRequest, LlmTransportResult


class LlmTransport(Protocol):
    """LLM 基础调用接口：应用层只依赖该协议，不直接耦合具体模型厂商。"""

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult: ...
