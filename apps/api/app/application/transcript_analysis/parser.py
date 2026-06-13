"""Transcript parsing without semantic interpretation."""

from __future__ import annotations

import re

from app.application.transcript_analysis.models import TranscriptContext, TranscriptInput


_SENTENCE_PATTERN = re.compile(r"[^.!?。！？]+(?:[.!?。！？]+|$)")


class TranscriptParser:
    def parse(self, transcript: TranscriptInput) -> TranscriptContext:
        question_text = transcript.question_text.strip()
        answer_text = transcript.answer_text.strip()
        return TranscriptContext(
            question_text=question_text,
            answer_text=answer_text,
            answer_spans=self._split_answer_spans(answer_text),
        )

    def _split_answer_spans(self, answer_text: str) -> tuple[dict[str, str], ...]:
        if not answer_text:
            return ()

        spans: list[dict[str, str]] = []
        for match in _SENTENCE_PATTERN.finditer(answer_text):
            text = match.group(0).strip()
            if text:
                spans.append({"span_id": f"span_{len(spans) + 1}", "text": text})
        if not spans:
            spans.append({"span_id": "span_1", "text": answer_text})
        return tuple(spans)
