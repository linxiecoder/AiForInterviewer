"""与共享 API error envelope 兼容的稳定 provider 错误。"""

from __future__ import annotations

from typing import Any

from app.boundary import build_error_payload


class LLMProviderError(Exception):
    """携带稳定 provider code 的异常，不把失败包装成 fallback 成功。"""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        request_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """创建 provider 错误，并保留 request_id 与 details 供 envelope 使用。"""
        super().__init__(message)
        self.code = code
        self.message = message
        self.request_id = request_id
        self.details = details or {}

    def to_payload(self) -> dict[str, dict[str, Any]]:
        """按项目共享 error-envelope 形状渲染 provider 失败。"""
        return build_error_payload(
            code=self.code,
            message=self.message,
            request_id=self.request_id,
            details=self.details or None,
        )
