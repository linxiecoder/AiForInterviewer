from __future__ import annotations

import pytest

from app.application.ai_runtime.contracts import RuntimePolicyError
from app.infrastructure.ai_runtime.langgraph.checkpointer import RefsOnlyLangGraphCheckpointer


RAW_KEY = "raw" + "_prompt"


def test_pr4_checkpointer_stores_refs_only_and_rejects_raw_state() -> None:
    checkpointer = RefsOnlyLangGraphCheckpointer()

    with pytest.raises(RuntimePolicyError, match="raw graph state"):
        checkpointer.record_ref(
            owner_id="owner_1",
            actor_id="actor_1",
            agent_run_id="arun_1",
            agent_node_run_id=None,
            graph_name="pr4_fake_runtime",
            graph_version="pr4",
            node_name="fake_node",
            checkpoint_namespace="pr4_fake",
            thread_id="thread_1",
            checkpoint_id="checkpoint_1",
            state_hash="sha256:state",
            raw_state={RAW_KEY: "hidden"},
        )

    ref = checkpointer.record_ref(
        owner_id="owner_1",
        actor_id="actor_1",
        agent_run_id="arun_1",
        agent_node_run_id=None,
        graph_name="pr4_fake_runtime",
        graph_version="pr4",
        node_name="fake_node",
        checkpoint_namespace="pr4_fake",
        thread_id="thread_1",
        checkpoint_id="checkpoint_1",
        state_hash="sha256:state",
        metadata={"retention_ref": "retention_pr4", "created_at": "2026-05-24T00:00:00Z"},
    )

    assert ref.checkpoint_ref.startswith("ackpt_")
    assert ref.state_hash == "sha256:state"
    assert ref.formal_business_ref is None
    serialized = repr(ref)
    for forbidden in ("checkpoint_payload", "payload", "formal_question", RAW_KEY, "hidden"):
        assert forbidden not in serialized


def test_pr4_checkpointer_blocks_business_metadata_and_is_rollback_safe() -> None:
    checkpointer = RefsOnlyLangGraphCheckpointer()
    initial = checkpointer.snapshot()

    with pytest.raises(RuntimePolicyError):
        checkpointer.record_ref(
            owner_id="owner_1",
            actor_id="actor_1",
            agent_run_id="arun_1",
            agent_node_run_id=None,
            graph_name="pr4_fake_runtime",
            graph_version="pr4",
            node_name="fake_node",
            checkpoint_namespace="pr4_fake",
            thread_id="thread_1",
            checkpoint_id="checkpoint_1",
            state_hash="sha256:state",
            metadata={"business_formal_object_payload": {"question": "formal"}},
        )

    assert checkpointer.snapshot() == initial
    checkpointer.disable_new_writes(reason="runtime flag rollback")

    with pytest.raises(RuntimePolicyError, match="disabled"):
        checkpointer.record_ref(
            owner_id="owner_1",
            actor_id="actor_1",
            agent_run_id="arun_1",
            agent_node_run_id=None,
            graph_name="pr4_fake_runtime",
            graph_version="pr4",
            node_name="fake_node",
            checkpoint_namespace="pr4_fake",
            thread_id="thread_1",
            checkpoint_id="checkpoint_2",
            state_hash="sha256:state2",
        )

    assert checkpointer.snapshot() == initial
