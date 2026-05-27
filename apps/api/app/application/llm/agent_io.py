"""Shared agent input objects for LLM prompt payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AgentEvidenceItem:
    ref: str
    source_type: str
    title: str
    excerpt: str
    source_ref: dict[str, Any] = field(default_factory=dict)
    availability: str | None = None
    priority: int = 0
    reason: str | None = None
    keywords: tuple[str, ...] = ()

    def to_prompt_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ref": self.ref,
            "source_type": self.source_type,
            "title": self.title,
            "excerpt": self.excerpt,
        }
        if self.availability is not None:
            payload["availability"] = self.availability
        if self.source_ref:
            payload["source_ref"] = self.source_ref
        if self.priority != 0:
            payload["priority"] = self.priority
        if self.reason:
            payload["reason"] = self.reason
        if self.keywords:
            payload["keywords"] = list(self.keywords)
        return payload
