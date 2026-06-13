"""Core G-004 transcript understanding logic.

Transcript Analysis v1 Contract: transcript_analysis_v1.

The analyzer MUST remain deterministic or LLM-pluggable behind a neutral
transcript-understanding port. It MUST remain an observation layer, and all
returned values are observational signals only.
"""

from __future__ import annotations

from app.application.transcript_analysis.models import (
    BehavioralPattern,
    IntentLabel,
    SkillSignal,
    TranscriptContext,
)


_REASONING_MARKERS = (
    "because",
    "therefore",
    "so",
    "since",
    "then",
    "first",
    "second",
    "finally",
    "however",
    "but",
    "tradeoff",
    "原因",
    "所以",
    "因此",
    "首先",
    "其次",
    "最后",
    "但是",
    "不过",
    "权衡",
)
_QUESTION_REASONING_MARKERS = ("why", "how", "explain", "tradeoff", "为什么", "如何", "解释", "权衡")
_UNCERTAINTY_MARKERS = ("i don't know", "not sure", "不知道", "不确定")
_CONTRAST_MARKERS = ("however", "but", "tradeoff", "但是", "不过", "权衡")
_SEQUENCE_MARKERS = ("first", "second", "then", "finally", "首先", "其次", "然后", "最后")


class TranscriptAnalyzer:
    def analyze(self, context: TranscriptContext) -> dict[str, object]:
        intent = self._extract_intent(context)
        return {
            "intent_classification": intent,
            "reasoning_structure": self._extract_reasoning_structure(context),
            "skill_signals": self._extract_skill_signals(context),
            "behavioral_patterns": self._detect_behavioral_patterns(context),
            "extracted_insights": self._extract_insights(context),
        }

    def _extract_intent(self, context: TranscriptContext) -> IntentLabel:
        if not context.answer_text or self._word_count(context.answer_text) <= 6:
            return "short_answer"
        if self._contains_any(context.answer_text, _REASONING_MARKERS) or len(context.answer_spans) >= 2:
            return "reasoning_based"
        return "descriptive"

    def _extract_reasoning_structure(self, context: TranscriptContext) -> dict[str, object]:
        if not context.answer_spans:
            return {
                "main_claim": None,
                "supporting_points": [],
                "assumptions": [],
                "tradeoffs": [],
                "missing_links": [],
            }

        first_span = context.answer_spans[0]
        return {
            "main_claim": {
                "text": first_span["text"],
                "evidence_ref": first_span["span_id"],
            },
            "supporting_points": [
                {
                    "text": span["text"],
                    "evidence_ref": span["span_id"],
                }
                for span in context.answer_spans[1:]
            ],
            "assumptions": [],
            "tradeoffs": self._extract_marker_spans(context, _CONTRAST_MARKERS),
            "missing_links": [],
        }

    def _extract_skill_signals(self, context: TranscriptContext) -> tuple[SkillSignal, ...]:
        if not context.answer_text:
            return (
                SkillSignal(
                    dimension="communication",
                    observation="未提供可观察的回答文本。",
                    signal_type="absence",
                    evidence_refs=(),
                ),
            )

        refs = tuple(span["span_id"] for span in context.answer_spans)
        signals: list[SkillSignal] = [
            SkillSignal(
                dimension="communication",
                observation="回答包含可观察文本内容。",
                signal_type="presence",
                evidence_refs=refs[:1],
            )
        ]

        if len(context.answer_spans) >= 2:
            signals.append(
                SkillSignal(
                    dimension="structure",
                    observation="回答由多个句段组成。",
                    signal_type="presence",
                    evidence_refs=refs,
                )
            )
        else:
            signals.append(
                SkillSignal(
                    dimension="structure",
                    observation="回答集中在单一句段内。",
                    signal_type="pattern",
                    evidence_refs=refs,
                )
            )

        reasoning_refs = self._marker_refs(context, _REASONING_MARKERS)
        if reasoning_refs:
            signals.append(
                SkillSignal(
                    dimension="reasoning",
                    observation="回答中出现因果、顺序或转折连接表达。",
                    signal_type="presence",
                    evidence_refs=reasoning_refs,
                )
            )
        elif self._contains_any(context.question_text, _QUESTION_REASONING_MARKERS):
            signals.append(
                SkillSignal(
                    dimension="reasoning",
                    observation="问题包含解释请求，但回答中未出现明显连接表达。",
                    signal_type="gap",
                    evidence_refs=refs,
                )
            )

        if self._contains_any(context.answer_text, _UNCERTAINTY_MARKERS):
            signals.append(
                SkillSignal(
                    dimension="correctness",
                    observation="回答中出现不确定表达。",
                    signal_type="pattern",
                    evidence_refs=self._marker_refs(context, _UNCERTAINTY_MARKERS),
                )
            )
        else:
            signals.append(
                SkillSignal(
                    dimension="correctness",
                    observation="回答包含可被后续材料核验的陈述。",
                    signal_type="pattern",
                    evidence_refs=refs[:1],
                )
            )

        return tuple(signals)

    def _detect_behavioral_patterns(self, context: TranscriptContext) -> tuple[BehavioralPattern, ...]:
        if not context.answer_text:
            return (
                BehavioralPattern(
                    label="unanswered_response",
                    description="未观察到回答文本。",
                    evidence_refs=(),
                ),
            )

        patterns: list[BehavioralPattern] = []
        refs = tuple(span["span_id"] for span in context.answer_spans)
        if len(context.answer_spans) == 1:
            patterns.append(
                BehavioralPattern(
                    label="concise_response",
                    description="回答以单一句段表达。",
                    evidence_refs=refs,
                )
            )
        else:
            patterns.append(
                BehavioralPattern(
                    label="multi_span_response",
                    description="回答通过多个句段展开。",
                    evidence_refs=refs,
                )
            )
        sequence_refs = self._marker_refs(context, _SEQUENCE_MARKERS)
        if sequence_refs:
            patterns.append(
                BehavioralPattern(
                    label="sequence_framing",
                    description="回答使用顺序连接表达组织内容。",
                    evidence_refs=sequence_refs,
                )
            )
        contrast_refs = self._marker_refs(context, _CONTRAST_MARKERS)
        if contrast_refs:
            patterns.append(
                BehavioralPattern(
                    label="contrastive_framing",
                    description="回答使用转折或权衡表达。",
                    evidence_refs=contrast_refs,
                )
            )
        return tuple(patterns)

    def _extract_insights(self, context: TranscriptContext) -> dict[str, object]:
        return {
            "question_present": bool(context.question_text),
            "answer_present": bool(context.answer_text),
            "answer_span_count": len(context.answer_spans),
            "observed_connectors": self._observed_markers(context.answer_text, _REASONING_MARKERS),
        }

    def _extract_marker_spans(
        self,
        context: TranscriptContext,
        markers: tuple[str, ...],
    ) -> list[dict[str, str]]:
        return [
            {
                "text": span["text"],
                "evidence_ref": span["span_id"],
            }
            for span in context.answer_spans
            if self._contains_any(span["text"], markers)
        ]

    def _marker_refs(self, context: TranscriptContext, markers: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            span["span_id"]
            for span in context.answer_spans
            if self._contains_any(span["text"], markers)
        )

    def _observed_markers(self, text: str, markers: tuple[str, ...]) -> tuple[str, ...]:
        lowered = text.casefold()
        return tuple(marker for marker in markers if marker.casefold() in lowered)

    def _contains_any(self, text: str, markers: tuple[str, ...]) -> bool:
        lowered = text.casefold()
        return any(marker.casefold() in lowered for marker in markers)

    def _word_count(self, text: str) -> int:
        return len([part for part in text.split() if part.strip()])
