"""G-004 transcript analysis pipeline orchestration."""

from __future__ import annotations

from app.application.transcript_analysis.analyzer import TranscriptAnalyzer
from app.application.transcript_analysis.models import G004Input, G004Output
from app.application.transcript_analysis.parser import TranscriptParser


class TranscriptAnalysisService:
    def __init__(
        self,
        *,
        parser: TranscriptParser | None = None,
        analyzer: TranscriptAnalyzer | None = None,
    ) -> None:
        self._parser = parser or TranscriptParser()
        self._analyzer = analyzer or TranscriptAnalyzer()

    def analyze(self, command: G004Input) -> G004Output:
        context = self._parser.parse(command.transcript)
        analysis = self._analyzer.analyze(context)
        return G004Output(
            intent_classification=analysis["intent_classification"],
            reasoning_structure=analysis["reasoning_structure"],
            skill_signals=analysis["skill_signals"],
            behavioral_patterns=analysis["behavioral_patterns"],
            extracted_insights=analysis["extracted_insights"],
        )
