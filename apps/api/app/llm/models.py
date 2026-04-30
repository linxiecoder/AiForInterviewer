"""Provider typed model；prompt 编排不放在本 package 内。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from app.llm.constants import DEFAULT_PROMPT_VERSION


@dataclass(frozen=True)
class LLMGenerateRequest:
    """通过单一 generate 边界传递的 provider-neutral 请求。"""

    purpose: str
    job: Mapping[str, Any]
    resume: Mapping[str, Any]
    history: Sequence[Mapping[str, Any]]
    last_answer: str | None
    metadata: Mapping[str, Any]
    request_id: str
    session_id: str
    turn_index: int
    prompt_version: str = DEFAULT_PROMPT_VERSION


@dataclass(frozen=True)
class LLMGenerateResult:
    """Provider-neutral 结果，不代表下游主链路状态已推进。"""

    provider: str
    model: str
    content: str
    finish_reason: str
    request_id: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
    usage: Mapping[str, Any] | None = None
    provider_request_id: str | None = None
