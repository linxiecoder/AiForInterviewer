from __future__ import annotations

import pytest

from app.application.ai_runtime.contracts import AgentTimelineEvent, AgentRunTimelinePage, RuntimePolicyError
from app.infrastructure.ai_runtime.langgraph.serializer import LangGraphRuntimeSerializer


RAW_KEY = "raw" + "_prompt"
PROVIDER_KEY = "provider_" + "payload"


def test_pr4_serializer_rejects_raw_internal_graph_state() -> None:
    serializer = LangGraphRuntimeSerializer()

    with pytest.raises(RuntimePolicyError, match="raw internal graph state"):
        serializer.serialize_graph_state(
            {
                "__pregel_internal": {"node": "fake"},
                "checkpoint_payload": {"state": "hidden"},
                RAW_KEY: "system instructions",
            }
        )


def test_pr4_serializer_emits_sanitized_runtime_timeline_only() -> None:
    serializer = LangGraphRuntimeSerializer()
    page = AgentRunTimelinePage(
        run_id="arun_pr4",
        events=(
            AgentTimelineEvent(
                event_id="evt_1",
                event_type="node_completed",
                summary="fake runtime node completed",
                refs=("runtime_ref_1",),
                metadata={
                    RAW_KEY: "hidden prompt",
                    PROVIDER_KEY: {"secret": "hidden"},
                    "checkpoint_id": "ckpt_internal",
                    "state_hash": "sha256:state",
                    "safe": "visible",
                },
            ),
        ),
    )

    payload = serializer.serialize_timeline_page(page)
    serialized = repr(payload)

    assert payload == {
        "run_id": "arun_pr4",
        "events": (
            {
                "event_id": "evt_1",
                "event_type": "node_completed",
                "summary": "fake runtime node completed",
                "refs": ("runtime_ref_1",),
                "metadata": {"safe": "visible"},
            },
        ),
        "next_cursor": None,
    }
    for forbidden in ("hidden prompt", "provider_payload", "checkpoint_id", "state_hash", "secret"):
        assert forbidden not in serialized
