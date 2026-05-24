from __future__ import annotations

import pytest

from app.application.ai_runtime.contracts import OwnerScopeError, RuntimeConflictError, RuntimeValidationError
from app.application.ai_runtime.interrupts import AgentInterruptService


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
