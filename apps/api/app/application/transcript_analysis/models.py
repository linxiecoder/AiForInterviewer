"""G-004 transcript analysis contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


G004_SCHEMA_ID = "transcript_analysis_v1"

IntentLabel = Literal["reasoning_based", "short_answer", "descriptive"]
SkillDimension = Literal["communication", "reasoning", "structure", "correctness"]
SignalType = Literal["presence", "absence", "pattern", "gap", "inconsistency"]


@dataclass(frozen=True)
class TranscriptInput:
    question_text: str
    answer_text: str


@dataclass(frozen=True)
class G004Input:
    transcript: TranscriptInput
    g003_feedback: tuple[dict[str, Any], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TranscriptContext:
    question_text: str
    answer_text: str
    answer_spans: tuple[dict[str, str], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SkillSignal:
    dimension: SkillDimension
    observation: str
    signal_type: SignalType
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class BehavioralPattern:
    label: str
    description: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class G004Output:
    intent_classification: IntentLabel
    reasoning_structure: dict[str, Any]
    skill_signals: tuple[SkillSignal, ...]
    behavioral_patterns: tuple[BehavioralPattern, ...]
    extracted_insights: dict[str, Any]
    schema_id: str = G004_SCHEMA_ID
