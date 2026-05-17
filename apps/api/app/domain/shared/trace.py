"""Trace helpers and constants."""

from app.domain.shared.ids import stable_resource_id
from app.domain.shared.refs import TraceRef


def make_trace_ref(trace_type: str, seed: str) -> TraceRef:
    return TraceRef(trace_ref_id=stable_resource_id("trace", f"{trace_type}:{seed}"), trace_type=trace_type)

