from __future__ import annotations

import pytest

from app.application.ai_runtime.contracts import OwnerScopeError, RuntimeConflictError, RuntimeValidationError
from app.application.ai_runtime.interrupts import AgentInterruptService, P8_HITL_INTERRUPT_TYPES


RAW_KEY = "raw" + "_completion"
RESUME_SCHEMA_ID = "agent.resume.user_confirmation.v1"


def test_interrupt_create_get_resume_reject_and_expire_are_owner_scoped_and_sanitized() -> None:
    service = AgentInterruptService()
    interrupt = service.create_interrupt(
        owner_id="owner_1",
        actor_id="actor_1",
        run_id="arun_1",
        node_name="candidate_review",
        interrupt_type="user_confirmation",
        resume_schema_id=RESUME_SCHEMA_ID,
        drawer_payload={RAW_KEY: "hidden", "candidate_refs": ["candidate_1"]},
        base_version=1,
    )

    visible = service.get_interrupt(interrupt.interrupt_id, owner_id="owner_1")

    assert visible is not None
    assert visible.drawer_payload == {"candidate_refs": ["candidate_1"]}
    assert service.get_interrupt(interrupt.interrupt_id, owner_id="owner_2") is None

    resumed = service.resume_interrupt(
        run_id="arun_1",
        interrupt_id=interrupt.interrupt_id,
        owner_id="owner_1",
        actor_id="actor_1",
        resume_payload={"action": "approve"},
        base_version=visible.record_version,
        idempotency_key="idem_1",
    )
    repeated = service.resume_interrupt(
        run_id="arun_1",
        interrupt_id=interrupt.interrupt_id,
        owner_id="owner_1",
        actor_id="actor_1",
        resume_payload={"action": "approve"},
        base_version=visible.record_version,
        idempotency_key="idem_1",
    )

    assert repeated == resumed
    assert resumed.formal_refs == ()
    assert service.validate_resume_payload(
        interrupt_id=interrupt.interrupt_id,
        owner_id="owner_1",
        resume_payload={"action": "reject"},
        base_version=visible.record_version,
    ) == {"action": "reject"}
    assert service.reject_interrupt("arun_1", interrupt.interrupt_id, "owner_1", "not_now").status == "rejected"
    assert service.expire_interrupts("arun_1", "owner_1", reason="timeout") == 0


def test_interrupt_resume_schema_validation_fails_closed_for_invalid_action_or_missing_edit_payload() -> None:
    service = AgentInterruptService()
    interrupt = service.create_interrupt(
        owner_id="owner_1",
        actor_id="actor_1",
        run_id="arun_1",
        node_name="candidate_review",
        interrupt_type="user_confirmation",
        resume_schema_id=RESUME_SCHEMA_ID,
        drawer_payload={"candidate_refs": ["candidate_1"]},
        base_version=3,
    )

    with pytest.raises(RuntimeValidationError):
        service.validate_resume_payload(
            interrupt_id=interrupt.interrupt_id,
            owner_id="owner_1",
            resume_payload={"action": "escalate"},
            base_version=3,
        )

    with pytest.raises(RuntimeValidationError):
        service.validate_resume_payload(
            interrupt_id=interrupt.interrupt_id,
            owner_id="owner_1",
            resume_payload={"action": "edit"},
            base_version=3,
        )

    assert service.validate_resume_payload(
        interrupt_id=interrupt.interrupt_id,
        owner_id="owner_1",
        resume_payload={"action": "edit", "edits": {"candidate_refs": ["candidate_2"]}},
        base_version=3,
    ) == {"action": "edit", "edits": {"candidate_refs": ["candidate_2"]}}


def test_interrupt_unknown_resume_schema_and_owner_mismatch_fail_closed() -> None:
    service = AgentInterruptService()
    interrupt = service.create_interrupt(
        owner_id="owner_1",
        actor_id="actor_1",
        run_id="arun_1",
        node_name="candidate_review",
        interrupt_type="user_confirmation",
        resume_schema_id="agent.resume.unknown.v1",
        drawer_payload={"candidate_refs": ["candidate_1"]},
        base_version=3,
    )

    with pytest.raises(RuntimeValidationError):
        service.validate_resume_payload(
            interrupt_id=interrupt.interrupt_id,
            owner_id="owner_1",
            resume_payload={"action": "approve"},
            base_version=3,
        )

    with pytest.raises(OwnerScopeError):
        service.validate_resume_payload(
            interrupt_id=interrupt.interrupt_id,
            owner_id="owner_2",
            resume_payload={"action": "approve"},
            base_version=3,
        )


def test_interrupt_resume_conflicts_on_stale_version_or_idempotency_body_change() -> None:
    service = AgentInterruptService()
    interrupt = service.create_interrupt(
        owner_id="owner_1",
        actor_id="actor_1",
        run_id="arun_1",
        node_name="candidate_review",
        interrupt_type="user_confirmation",
        resume_schema_id=RESUME_SCHEMA_ID,
        drawer_payload={"candidate_refs": ["candidate_1"]},
        base_version=7,
    )

    with pytest.raises(RuntimeConflictError):
        service.resume_interrupt(
            run_id="arun_1",
            interrupt_id=interrupt.interrupt_id,
            owner_id="owner_1",
            actor_id="actor_1",
            resume_payload={"action": "approve"},
            base_version=6,
            idempotency_key="idem_1",
        )

    service.resume_interrupt(
        run_id="arun_1",
        interrupt_id=interrupt.interrupt_id,
        owner_id="owner_1",
        actor_id="actor_1",
        resume_payload={"action": "approve"},
        base_version=7,
        idempotency_key="idem_1",
    )

    with pytest.raises(RuntimeConflictError):
        service.resume_interrupt(
            run_id="arun_1",
            interrupt_id=interrupt.interrupt_id,
            owner_id="owner_1",
            actor_id="actor_1",
            resume_payload={"action": "reject"},
            base_version=7,
            idempotency_key="idem_1",
        )


def test_hitl_interrupt_matrix_requires_checkpoint_refs_and_sanitizes_payloads() -> None:
    service = AgentInterruptService()

    for interrupt_type in P8_HITL_INTERRUPT_TYPES:
        interrupt = service.create_hitl_interrupt(
            owner_id="owner_1",
            actor_id="actor_1",
            run_id="arun_1",
            node_name=f"node_{interrupt_type}",
            interrupt_type=interrupt_type,
            checkpoint_ref="ackpt_p8_1",
            base_version=11,
            candidate_refs=("candidate_ref_1",),
            validation_refs=("validation_ref_1",),
            low_confidence_flags=("source_gap",),
            drawer_payload={RAW_KEY: "hidden", "safe": interrupt_type},
        )

        assert interrupt.interrupt_type == interrupt_type
        assert interrupt.resume_schema_id == "agent.resume.hitl.v1"
        assert interrupt.checkpoint_ref == "ackpt_p8_1"
        assert interrupt.formal_refs == ()
        assert interrupt.drawer_payload["trigger_type"] == interrupt_type
        assert interrupt.drawer_payload["checkpoint_ref"] == "ackpt_p8_1"
        assert interrupt.drawer_payload["candidate_refs"] == ("candidate_ref_1",)
        assert interrupt.drawer_payload["validation_refs"] == ("validation_ref_1",)
        assert interrupt.drawer_payload["low_confidence_flags"] == ("source_gap",)
        assert RAW_KEY not in interrupt.drawer_payload

    with pytest.raises(RuntimeValidationError, match="checkpoint"):
        service.create_hitl_interrupt(
            owner_id="owner_1",
            actor_id="actor_1",
            run_id="arun_missing_checkpoint",
            node_name="formal_write",
            interrupt_type="formal_write_attempt",
            checkpoint_ref="",
            base_version=1,
        )
    with pytest.raises(RuntimeValidationError, match="interrupt type"):
        service.create_hitl_interrupt(
            owner_id="owner_1",
            actor_id="actor_1",
            run_id="arun_bad_type",
            node_name="unknown",
            interrupt_type="not_a_p8_trigger",
            checkpoint_ref="ackpt_p8_1",
            base_version=1,
        )


def test_hitl_resume_validates_checkpoint_ref_base_version_and_allowed_action() -> None:
    service = AgentInterruptService()
    interrupt = service.create_hitl_interrupt(
        owner_id="owner_1",
        actor_id="actor_1",
        run_id="arun_1",
        node_name="low_confidence_update",
        interrupt_type="low_confidence_formal_update",
        checkpoint_ref="ackpt_p8_1",
        base_version=5,
        candidate_refs=("candidate_ref_1",),
    )

    with pytest.raises(RuntimeValidationError, match="checkpoint"):
        service.resume_interrupt(
            run_id="arun_1",
            interrupt_id=interrupt.interrupt_id,
            owner_id="owner_1",
            actor_id="actor_1",
            resume_payload={"action": "defer_to_handoff"},
            base_version=5,
            idempotency_key="idem_missing_checkpoint",
        )
    with pytest.raises(RuntimeConflictError, match="checkpoint"):
        service.resume_interrupt(
            run_id="arun_1",
            interrupt_id=interrupt.interrupt_id,
            owner_id="owner_1",
            actor_id="actor_1",
            resume_payload={"action": "defer_to_handoff"},
            base_version=5,
            idempotency_key="idem_wrong_checkpoint",
            checkpoint_ref="ackpt_other",
        )
    with pytest.raises(RuntimeConflictError, match="stale"):
        service.resume_interrupt(
            run_id="arun_1",
            interrupt_id=interrupt.interrupt_id,
            owner_id="owner_1",
            actor_id="actor_1",
            resume_payload={"action": "defer_to_handoff"},
            base_version=4,
            idempotency_key="idem_stale",
            checkpoint_ref="ackpt_p8_1",
        )
    with pytest.raises(RuntimeValidationError, match="unsupported"):
        service.resume_interrupt(
            run_id="arun_1",
            interrupt_id=interrupt.interrupt_id,
            owner_id="owner_1",
            actor_id="actor_1",
            resume_payload={"action": "approve"},
            base_version=5,
            idempotency_key="idem_bad_action",
            checkpoint_ref="ackpt_p8_1",
        )

    resumed = service.resume_interrupt(
        run_id="arun_1",
        interrupt_id=interrupt.interrupt_id,
        owner_id="owner_1",
        actor_id="actor_1",
        resume_payload={"action": "defer_to_handoff"},
        base_version=5,
        idempotency_key="idem_valid",
        checkpoint_ref="ackpt_p8_1",
    )

    assert resumed.status == "running"
    assert resumed.formal_refs == ()
    assert resumed.interrupt_refs == (interrupt.interrupt_id,)
