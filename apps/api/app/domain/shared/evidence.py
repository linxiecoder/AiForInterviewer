"""Evidence helpers and shared concepts."""

from app.domain.shared.ids import stable_resource_id
from app.domain.shared.refs import EvidenceRef, ResourceRef


def make_evidence_ref(source_ref: ResourceRef, seed: str, summary: str | None = None) -> EvidenceRef:
    return EvidenceRef(
        evidence_ref_id=stable_resource_id("trace", f"evidence:{source_ref.resource_type}:{source_ref.resource_id}:{seed}"),
        source_ref=source_ref,
        summary=summary,
    )

