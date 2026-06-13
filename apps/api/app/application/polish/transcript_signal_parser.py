"""Parse raw interview answers into structured signals for polish evaluation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


POLISH_TRANSCRIPT_SIGNALS_SCHEMA_ID = "polish_transcript_signals_v1"
_MAX_CLAIMS = 8
_MAX_TOPICS = 12

_TOPIC_KEYWORDS = (
    "fastapi",
    "postgresql",
    "redis",
    "cache",
    "queue",
    "message queue",
    "retry jobs",
    "retries",
    "alerts",
    "observability",
    "idempotency",
    "migration",
    "payment",
    "timeout",
    "api",
    "latency",
    "消息队列",
    "队列",
    "幂等",
    "重试",
    "告警",
    "监控",
    "补偿",
)
_UNCERTAINTY_KEYWORDS = ("maybe", "might", "probably", "think", "unsure", "可能", "也许", "不确定")
_RISK_KEYWORDS = ("risk", "timeout", "failed", "failure", "缺少", "失败", "风险", "超时")
_POSITIVE_KEYWORDS = ("improved", "reduced", "increased", "success", "solved", "提升", "降低", "改善", "成功")
_NEGATIVE_KEYWORDS = ("risk", "failed", "failure", "timeout", "缺少", "失败", "风险", "超时")
_OWNERSHIP_KEYWORDS = ("i led", "i owned", "i was responsible", "i built", "i implemented", "我负责", "我主导", "我实现")
_IMPACT_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\s*%|\b(improved|reduced|increased)\b|提升|降低|改善")


@dataclass(frozen=True)
class StructuredAnswerSignals:
    claims: tuple[dict[str, str], ...] = field(default_factory=tuple)
    topics: tuple[str, ...] = field(default_factory=tuple)
    sentiment: str | None = None
    confidence_indicators: tuple[dict[str, str], ...] = field(default_factory=tuple)
    experience_signals: tuple[dict[str, str], ...] = field(default_factory=tuple)
    parse_status: str = "parsed"
    schema_id: str = POLISH_TRANSCRIPT_SIGNALS_SCHEMA_ID

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "parse_status": self.parse_status,
            "claims": [dict(claim) for claim in self.claims],
            "topics": list(self.topics),
            "sentiment": self.sentiment,
            "confidence_indicators": [dict(indicator) for indicator in self.confidence_indicators],
            "experience_signals": [dict(signal) for signal in self.experience_signals],
        }


class TranscriptSignalParser:
    """Deterministic, local signal extraction for the G-003 feedback path."""

    def parse(self, answer_text: str) -> StructuredAnswerSignals:
        cleaned = _clean(answer_text, max_chars=12000)
        spans = _answer_spans(cleaned)
        claims = tuple(
            {
                "claim_id": f"claim_{index}",
                "text": span,
                "evidence_ref": f"span_{index}",
            }
            for index, span in enumerate(spans[:_MAX_CLAIMS], start=1)
        )
        return StructuredAnswerSignals(
            claims=claims,
            topics=_topics(cleaned),
            sentiment=_sentiment(cleaned),
            confidence_indicators=_confidence_indicators(cleaned),
            experience_signals=_experience_signals(spans),
            parse_status="parsed",
        )


def build_fallback_structured_answer(answer_text: str) -> StructuredAnswerSignals:
    text = _clean(answer_text, max_chars=1200)
    claims: tuple[dict[str, str], ...] = ()
    if text:
        claims = (
            {
                "claim_id": "claim_fallback_1",
                "text": text,
                "evidence_ref": "answer_fallback",
            },
        )
    return StructuredAnswerSignals(
        claims=claims,
        topics=(),
        sentiment=None,
        confidence_indicators=(
            {
                "indicator_id": "confidence_fallback_1",
                "text": "parser_failed",
                "kind": "parser_fallback",
                "evidence_ref": "answer_fallback",
            },
        ),
        experience_signals=(),
        parse_status="fallback",
    )


def structured_answer_to_evaluation_text(structured_answer: dict[str, Any]) -> str:
    claims = _dict_list(structured_answer.get("claims"))
    topics = _string_list(structured_answer.get("topics"))
    confidence_indicators = _dict_list(structured_answer.get("confidence_indicators"))
    experience_signals = _dict_list(structured_answer.get("experience_signals"))
    sentiment = _clean(structured_answer.get("sentiment"))

    sections: list[str] = []
    if claims:
        sections.append("Claims: " + "; ".join(_clean(claim.get("text"), max_chars=240) for claim in claims if claim.get("text")))
    if topics:
        sections.append("Topics: " + ", ".join(topics))
    if sentiment:
        sections.append(f"Sentiment: {sentiment}")
    if confidence_indicators:
        sections.append(
            "Confidence indicators: "
            + "; ".join(
                _clean(indicator.get("text"), max_chars=120)
                for indicator in confidence_indicators
                if indicator.get("text")
            )
        )
    if experience_signals:
        sections.append(
            "Experience signals: "
            + "; ".join(
                _clean(signal.get("signal_type"), max_chars=80) + ":" + _clean(signal.get("text"), max_chars=160)
                for signal in experience_signals
                if signal.get("signal_type") or signal.get("text")
            )
        )
    return "\n".join(section for section in sections if section).strip()


def _answer_spans(answer_text: str) -> tuple[str, ...]:
    if not answer_text:
        return ()
    spans = [_clean(match.group(0), max_chars=500) for match in re.finditer(r"[^.!?。！？]+[.!?。！？]?", answer_text)]
    return tuple(span for span in spans if span)


def _topics(answer_text: str) -> tuple[str, ...]:
    lowered = answer_text.lower()
    topics: list[str] = []
    for keyword in _TOPIC_KEYWORDS:
        if keyword.lower() in lowered and keyword not in topics:
            topics.append(keyword)
    return tuple(topics[:_MAX_TOPICS])


def _sentiment(answer_text: str) -> str | None:
    lowered = answer_text.lower()
    has_positive = any(keyword in lowered for keyword in _POSITIVE_KEYWORDS)
    has_negative = any(keyword in lowered for keyword in _NEGATIVE_KEYWORDS)
    if has_positive and has_negative:
        return "mixed"
    if has_positive:
        return "positive"
    if has_negative:
        return "negative"
    return None


def _confidence_indicators(answer_text: str) -> tuple[dict[str, str], ...]:
    lowered = answer_text.lower()
    indicators: list[dict[str, str]] = []
    for keyword in _UNCERTAINTY_KEYWORDS:
        if keyword in lowered:
            indicators.append(
                {
                    "indicator_id": f"confidence_{len(indicators) + 1}",
                    "text": keyword,
                    "kind": "uncertainty",
                    "evidence_ref": "answer_text",
                }
            )
    for keyword in _RISK_KEYWORDS:
        if keyword in lowered:
            indicators.append(
                {
                    "indicator_id": f"confidence_{len(indicators) + 1}",
                    "text": keyword,
                    "kind": "risk",
                    "evidence_ref": "answer_text",
                }
            )
    return tuple(indicators[:6])


def _experience_signals(spans: tuple[str, ...]) -> tuple[dict[str, str], ...]:
    signals: list[dict[str, str]] = []
    for index, span in enumerate(spans, start=1):
        lowered = span.lower()
        if any(keyword in lowered for keyword in _OWNERSHIP_KEYWORDS):
            signals.append(
                {
                    "signal_id": f"experience_{len(signals) + 1}",
                    "signal_type": "ownership",
                    "text": span,
                    "evidence_ref": f"span_{index}",
                }
            )
        if _IMPACT_PATTERN.search(lowered):
            signals.append(
                {
                    "signal_id": f"experience_{len(signals) + 1}",
                    "signal_type": "impact",
                    "text": span,
                    "evidence_ref": f"span_{index}",
                }
            )
    return tuple(signals[:6])


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _clean(item, max_chars=120))]


def _clean(value: object, *, max_chars: int = 240) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text
