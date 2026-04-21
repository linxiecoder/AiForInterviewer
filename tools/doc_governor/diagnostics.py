from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Any


SEVERITIES = {"error", "warning"}


@dataclass(frozen=True)
class Evidence:
    type: str
    path: str
    ref: str
    value: Any | None = None
    line: int | None = None
    snippet: str | None = None


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: str
    entity_type: str
    entity_id: str
    field_path: str
    message: str
    evidence: list[Evidence]


def make_evidence(
    *,
    type: str,
    path: str,
    ref: str,
    value: Any | None = None,
    line: int | None = None,
    snippet: str | None = None,
) -> Evidence:
    return Evidence(
        type=type,
        path=path,
        ref=ref,
        value=value,
        line=line,
        snippet=snippet,
    )


def make_diagnostic(
    *,
    code: str,
    severity: str,
    entity_type: str,
    entity_id: str,
    field_path: str,
    message: str,
    evidence: list[Evidence],
) -> Diagnostic:
    if severity not in SEVERITIES:
        raise ValueError(f"Unsupported severity: {severity}")
    if not evidence:
        raise ValueError("Diagnostic evidence must not be empty")
    return Diagnostic(
        code=code,
        severity=severity,
        entity_type=entity_type,
        entity_id=entity_id,
        field_path=field_path,
        message=message,
        evidence=evidence,
    )


def evidence_to_dict(evidence: Evidence) -> dict[str, Any]:
    return asdict(evidence)


def diagnostic_to_dict(diagnostic: Diagnostic) -> dict[str, Any]:
    payload = asdict(diagnostic)
    payload["evidence"] = [evidence_to_dict(item) for item in diagnostic.evidence]
    return payload


def diagnostics_to_dicts(diagnostics: list[Diagnostic]) -> list[dict[str, Any]]:
    return [diagnostic_to_dict(item) for item in diagnostics]


def count_diagnostics(diagnostics: list[Diagnostic]) -> dict[str, int]:
    counts = {"error": 0, "warning": 0}
    for diagnostic in diagnostics:
        counts[diagnostic.severity] += 1
    return counts


def result_to_json(
    *,
    ok: bool,
    diagnostics: list[Diagnostic],
    **extra: Any,
) -> str:
    payload: dict[str, Any] = {
        "ok": ok,
        "counts": count_diagnostics(diagnostics),
        "diagnostics": diagnostics_to_dicts(diagnostics),
    }
    payload.update(extra)
    return json.dumps(payload, ensure_ascii=False, indent=2)
