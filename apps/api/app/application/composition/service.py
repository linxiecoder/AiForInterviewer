"""Composition layer for routing G-003 feedback and G-004 analysis signals."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from app.application.polish.feedback_generation_service import (
    FeedbackGenerationContext,
    FeedbackGenerationService,
)
from app.application.transcript_analysis.models import G004Input, TranscriptInput
from app.application.transcript_analysis.service import TranscriptAnalysisService


CompositionMode = Literal["interview", "training", "analysis"]
FeedbackContextInput = FeedbackGenerationContext | Mapping[str, Any]

COMPOSITION_MODES: tuple[CompositionMode, ...] = ("interview", "training", "analysis")
_FEEDBACK_MODES: frozenset[CompositionMode] = frozenset(("interview", "training"))
_SYSTEM_HINTS: dict[CompositionMode, str] = {
    "interview": "fast_feedback: feedback_signal_enabled; analysis_signal_background",
    "training": "balanced: feedback_signal_enabled; analysis_signal_enabled",
    "analysis": "deep_understanding: analysis_signal_only",
}


@dataclass(frozen=True)
class CompositionCommand:
    transcript: G004Input | TranscriptInput | Mapping[str, Any]
    mode: CompositionMode | str = "training"
    feedback_context: FeedbackContextInput | None = None


class AnalysisSignalService(Protocol):
    def analyze(self, command: G004Input) -> Any:
        ...


class FeedbackSignalService(Protocol):
    def generate(self, context: FeedbackGenerationContext | dict[str, Any]) -> Any:
        ...


class CompositionService:
    """Route and compose independent G-003 / G-004 outputs."""

    def __init__(
        self,
        *,
        analysis_service: AnalysisSignalService | None = None,
        feedback_service: FeedbackSignalService | None = None,
    ) -> None:
        self._analysis_service = analysis_service or TranscriptAnalysisService()
        self._feedback_service = feedback_service or FeedbackGenerationService()

    def compose(
        self,
        command: CompositionCommand | G004Input | TranscriptInput | Mapping[str, Any],
        *,
        mode: CompositionMode | str | None = None,
        feedback_context: FeedbackContextInput | None = None,
    ) -> dict[str, Any]:
        selected_mode = _normalize_mode(mode or _command_mode(command))
        transcript = _extract_transcript(command)

        analysis = self._analysis_service.analyze(G004Input(transcript=transcript))
        result: dict[str, Any] = {
            "mode": selected_mode,
            "analysis": analysis,
            "system_hint": _SYSTEM_HINTS[selected_mode],
        }

        if selected_mode in _FEEDBACK_MODES:
            context = _feedback_context_for(
                transcript,
                explicit_context=feedback_context or _command_feedback_context(command),
            )
            result["feedback"] = self._feedback_service.generate(context)

        return result


def _normalize_mode(mode: CompositionMode | str | None) -> CompositionMode:
    if mode is None:
        return "training"
    normalized = str(mode).strip().lower()
    if normalized not in COMPOSITION_MODES:
        allowed = ", ".join(COMPOSITION_MODES)
        raise ValueError(f"unsupported composition mode: {mode!r}; expected one of {allowed}")
    return normalized  # type: ignore[return-value]


def _command_mode(command: CompositionCommand | G004Input | TranscriptInput | Mapping[str, Any]) -> str | None:
    if isinstance(command, CompositionCommand):
        return command.mode
    if isinstance(command, Mapping):
        mode = command.get("mode")
        return str(mode) if mode is not None else None
    return None


def _extract_transcript(command: CompositionCommand | G004Input | TranscriptInput | Mapping[str, Any]) -> TranscriptInput:
    if isinstance(command, CompositionCommand):
        return _extract_transcript(command.transcript)
    if isinstance(command, G004Input):
        return command.transcript
    if isinstance(command, TranscriptInput):
        return command
    if isinstance(command, Mapping):
        nested_transcript = command.get("transcript")
        if nested_transcript is not None:
            return _extract_transcript(nested_transcript)
        return TranscriptInput(
            question_text=_string_value(command.get("question_text")),
            answer_text=_string_value(command.get("answer_text")),
        )
    raise TypeError(f"unsupported composition command: {type(command).__name__}")


def _command_feedback_context(
    command: CompositionCommand | G004Input | TranscriptInput | Mapping[str, Any],
) -> FeedbackContextInput | None:
    if isinstance(command, CompositionCommand):
        return command.feedback_context
    if isinstance(command, Mapping):
        explicit_context = command.get("feedback_context")
        if explicit_context is not None:
            if isinstance(explicit_context, (FeedbackGenerationContext, Mapping)):
                return explicit_context
            raise TypeError("feedback_context must be FeedbackGenerationContext or mapping")
        if "transcript" not in command:
            return command
    return None


def _feedback_context_for(
    transcript: TranscriptInput,
    *,
    explicit_context: FeedbackContextInput | None,
) -> FeedbackGenerationContext | dict[str, Any]:
    if isinstance(explicit_context, FeedbackGenerationContext):
        return explicit_context

    context = dict(explicit_context or {})
    context.setdefault("question_text", transcript.question_text)
    context.setdefault("answer_text", transcript.answer_text)
    return context


def _string_value(value: object) -> str:
    if value is None:
        return ""
    return str(value)


__all__ = [
    "COMPOSITION_MODES",
    "CompositionCommand",
    "CompositionMode",
    "CompositionService",
]
