"""Stable ID helpers for F5 contract baseline."""

from __future__ import annotations

from enum import Enum
from hashlib import sha256
from uuid import uuid4


class ResourceIdPrefix(str, Enum):
    USER = "usr"
    RESUME = "res"
    JOB = "job"
    BINDING = "bind"
    SESSION = "sess"
    QUESTION = "q"
    ANSWER = "ans"
    TASK = "task"
    SCORE = "score"
    REPORT = "report"
    REVIEW = "review"
    ASSET = "asset"
    WEAKNESS = "weak"
    TRAINING = "train"
    TRACE = "trace"
    AUDIT = "audit"


_ALLOWED_PREFIXES = frozenset(prefix.value for prefix in ResourceIdPrefix)


def generate_request_id() -> str:
    return generate_resource_id("trace")


def generate_trace_id() -> str:
    return generate_resource_id("trace")


def generate_resource_id(prefix: str | ResourceIdPrefix) -> str:
    normalized = _normalize_prefix(prefix)
    return f"{normalized}_{uuid4().hex}"


def stable_resource_id(prefix: str | ResourceIdPrefix, seed: str) -> str:
    normalized = _normalize_prefix(prefix)
    digest = sha256(seed.encode("utf-8")).hexdigest()[:24]
    return f"{normalized}_{digest}"


def _normalize_prefix(prefix: str | ResourceIdPrefix) -> str:
    value = prefix.value if isinstance(prefix, ResourceIdPrefix) else prefix
    if value not in _ALLOWED_PREFIXES:
        allowed = ", ".join(sorted(_ALLOWED_PREFIXES))
        raise ValueError(f"Unsupported resource id prefix: {value}. Allowed: {allowed}")
    return value

