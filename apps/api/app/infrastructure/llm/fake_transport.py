"""Deterministic fake LLM transport for contract tests."""

from __future__ import annotations

from json import dumps

from app.domain.shared.enums import ConfidenceLevel, ValidationStatus
from app.domain.shared.ids import stable_resource_id
from app.infrastructure.llm.types import LlmTransportRequest, LlmTransportResult


class FakeLlmTransport:
    status = "deterministic_fake_only"

    def generate(self, request: LlmTransportRequest) -> LlmTransportResult:
        seed = dumps(
            {
                "contract_ids": sorted(request.contract_ids),
                "task_type": request.task_type,
                "input_refs": sorted(request.input_refs),
                "evidence_keys": sorted(request.evidence_bundle.keys()),
            },
            ensure_ascii=True,
            sort_keys=True,
        )
        has_evidence = bool(request.evidence_bundle)
        validation_status = ValidationStatus.VALID if has_evidence else ValidationStatus.VALID_WITH_WARNINGS
        confidence_level = ConfidenceLevel.MEDIUM if has_evidence else ConfidenceLevel.LOW
        low_confidence_flags = () if has_evidence else ("evidence_missing",)
        trace_ref = stable_resource_id("trace", f"fake-llm-trace:{seed}")
        evidence_ref = stable_resource_id("trace", f"fake-llm-evidence:{seed}")
        return LlmTransportResult(
            result={
                "transport": "fake",
                "task_type": request.task_type,
                "contract_ids": list(request.contract_ids),
                "result_ref": stable_resource_id("task", f"fake-llm-result:{seed}"),
                "summary": "deterministic skeleton result",
            },
            validation_status=validation_status,
            confidence_level=confidence_level,
            low_confidence_flags=low_confidence_flags,
            trace_refs=(trace_ref,),
            evidence_refs=(evidence_ref,),
        )

