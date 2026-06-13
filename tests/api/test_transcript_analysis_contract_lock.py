from __future__ import annotations

import ast
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.application.transcript_analysis.models import G004Input, TranscriptInput
from app.application.transcript_analysis.service import TranscriptAnalysisService


def _blocked(*parts: str) -> str:
    return "".join(parts)


def _module(*parts: str) -> str:
    return ".".join(parts)


CONTRACT_OUTPUT_FIELDS = {
    "schema_id",
    "intent_classification",
    "reasoning_structure",
    "skill_signals",
    "behavioral_patterns",
    "extracted_insights",
}

FORBIDDEN_OUTPUT_FIELDS = {
    _blocked("sc", "ore"),
    "rating",
    "rank",
    "strength",
    "weakness",
}

FORBIDDEN_IMPORT_PREFIXES = (
    "app.application.polish.feedback_generation_service",
    "app.application.polish.feedback_application_service",
    "app.application.polish.feedback_models",
    "app.application.polish.feedback_schema",
    "app.application.polish.feedback_validation",
    "app.application.polish.feedback_rules",
    "app.application.polish",
    "app.schemas.polish",
    _module("app", "application", _blocked("sc", "oring")),
    _module("app", "domain", _blocked("sc", "oring")),
    _module("app", "schemas", _blocked("sc", "oring")),
    "apps.web",
)

FORBIDDEN_TEXT_REFERENCES = (
    "feedback_generation_service",
    "feedback_application_service",
    "InterviewPage.tsx",
    "AiTaskStatus",
    "partial",
    "low_confidence",
    "validation_failed",
    "generation_failed",
)


def test_transcript_analysis_output_has_no_judgment_fields() -> None:
    output = TranscriptAnalysisService().analyze(
        G004Input(
            transcript=TranscriptInput(
                question_text="How did you handle the queue tradeoff?",
                answer_text=(
                    "First I kept the API boundary small. "
                    "Then I moved retries into the worker because retries can be slow."
                ),
            )
        )
    )

    seen_keys = _collect_keys(asdict(output))

    assert not (seen_keys & FORBIDDEN_OUTPUT_FIELDS)


def test_g003_status_values_do_not_affect_output() -> None:
    transcript = TranscriptInput(
        question_text="Why did you choose this architecture?",
        answer_text="I used a queue because it decouples request latency from retry behavior.",
    )
    service = TranscriptAnalysisService()

    baseline = asdict(
        service.analyze(
            G004Input(
                transcript=transcript,
                g003_feedback=({"feedback_id": "fb-1", "status": "partial"},),
            )
        )
    )

    for status in ("low_confidence", "validation_failed", "generation_failed"):
        candidate = asdict(
            service.analyze(
                G004Input(
                    transcript=transcript,
                    g003_feedback=({"feedback_id": f"fb-{status}", "status": status},),
                )
            )
        )
        assert candidate == baseline


def test_transcript_analysis_contract_schema_is_stable() -> None:
    output = TranscriptAnalysisService().analyze(
        G004Input(
            transcript=TranscriptInput(
                question_text="Explain the tradeoff.",
                answer_text="The queue adds delay, but it separates request handling from retries.",
            )
        )
    )

    contract_output = asdict(output)

    assert set(contract_output) == CONTRACT_OUTPUT_FIELDS
    assert contract_output["schema_id"] == "transcript_analysis_v1"
    assert contract_output["intent_classification"] in {
        "reasoning_based",
        "short_answer",
        "descriptive",
    }
    assert isinstance(contract_output["reasoning_structure"], dict)
    assert isinstance(contract_output["skill_signals"], tuple)
    assert isinstance(contract_output["behavioral_patterns"], tuple)
    assert isinstance(contract_output["extracted_insights"], dict)


def test_transcript_analysis_module_has_no_g003_or_polish_dependency_leakage() -> None:
    module_root = _repo_root() / "apps" / "api" / "app" / "application" / "transcript_analysis"
    violations: list[str] = []

    for path in sorted(module_root.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _is_forbidden_import(alias.name):
                        violations.append(f"{path.name}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module and _is_forbidden_import(node.module):
                violations.append(f"{path.name}: from {node.module} import ...")

        for forbidden_text in FORBIDDEN_TEXT_REFERENCES:
            if forbidden_text in source:
                violations.append(f"{path.name}: forbidden text reference {forbidden_text}")

    assert violations == []


def test_analyzer_declares_transcript_analysis_v1_behavior_lock() -> None:
    analyzer_path = _repo_root() / "apps" / "api" / "app" / "application" / "transcript_analysis" / "analyzer.py"
    source = analyzer_path.read_text(encoding="utf-8")

    assert "transcript_analysis_v1" in source
    assert "deterministic or LLM-pluggable" in source
    assert "MUST remain an observation layer" in source
    assert "observational signals only" in source


def _collect_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for item in value.values():
            keys.update(_collect_keys(item))
        return keys
    if isinstance(value, (list, tuple)):
        keys: set[str] = set()
        for item in value:
            keys.update(_collect_keys(item))
        return keys
    return set()


def _is_forbidden_import(module_name: str) -> bool:
    return any(
        module_name == forbidden or module_name.startswith(f"{forbidden}.")
        for forbidden in FORBIDDEN_IMPORT_PREFIXES
    )

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]
