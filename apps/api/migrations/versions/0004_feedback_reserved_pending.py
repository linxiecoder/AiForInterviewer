"""feedback reserved pending"""

from __future__ import annotations

import json
from typing import Any

from alembic import op
import sqlalchemy as sa

revision = "0004_feedback_reserved_pending"
down_revision = "0003_asset_rag_pgvector"
branch_labels = None
depends_on = None

_GENERATED_SCHEMA_ID = "polish_feedback_generated_v1"
_GENERATED_SCHEMA_VERSION = "1.0"
_RESERVED_SCHEMA_ID = "polish_feedback_reserved_v1"
_PENDING_FEEDBACK_TEXT = "本轮反馈尚未生成"
_DEFAULT_CONTRACT_IDS = ["P-POLISH-003"]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "feedback" not in inspector.get_table_names():
        return

    feedback = sa.table(
        "feedback",
        sa.column("id", sa.String),
        sa.column("status", sa.String),
        sa.column("feedback_summary", sa.Text),
    )
    rows = bind.execute(
        sa.select(feedback.c.id, feedback.c.status, feedback.c.feedback_summary).where(
            sa.or_(
                feedback.c.status == "reserved",
                feedback.c.feedback_summary.like('%"status": "reserved"%'),
                feedback.c.feedback_summary.like(f"%{_RESERVED_SCHEMA_ID}%"),
            )
        )
    ).mappings()

    for row in rows:
        payload = _json_payload(row["feedback_summary"])
        pending_payload = _pending_payload(feedback_id=str(row["id"]), old_payload=payload)
        bind.execute(
            feedback.update()
            .where(feedback.c.id == row["id"])
            .values(
                status="pending",
                feedback_summary=json.dumps(pending_payload, ensure_ascii=False, sort_keys=True),
            )
        )


def downgrade() -> None:
    return None


def _json_payload(value: object) -> dict[str, Any]:
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _pending_payload(*, feedback_id: str, old_payload: dict[str, Any]) -> dict[str, Any]:
    old_metadata = old_payload.get("feedback_metadata")
    metadata = dict(old_metadata) if isinstance(old_metadata, dict) else {}
    metadata.pop("reserved", None)
    metadata.update(
        {
            "llm_called": False,
            "migration": revision,
        }
    )

    payload: dict[str, Any] = {
        "schema_id": _GENERATED_SCHEMA_ID,
        "schema_version": _GENERATED_SCHEMA_VERSION,
        "status": "pending",
        "contract_ids": _contract_ids(old_payload.get("contract_ids")),
        "feedback_id": str(old_payload.get("feedback_id") or feedback_id),
        "feedback_text": _PENDING_FEEDBACK_TEXT,
        "answer_summary": None,
        "score_reasoning": "",
        "score_result": None,
        "loss_points": [],
        "reference_answer": None,
        "next_recommended_actions": ["answer_again", "continue_same_question", "generate_next_question"],
        "evidence_refs": _string_list(old_payload.get("evidence_refs")),
        "trace_refs": _trace_refs(old_payload.get("trace_refs")),
        "low_confidence_flags": [],
        "feedback_metadata": metadata,
    }
    for ref_field in ("polish_session_ref", "question_ref", "answer_ref"):
        ref_value = old_payload.get(ref_field)
        if isinstance(ref_value, dict):
            payload[ref_field] = dict(ref_value)
    return payload


def _contract_ids(value: object) -> list[str]:
    if not isinstance(value, list):
        return list(_DEFAULT_CONTRACT_IDS)
    cleaned = [str(item).strip() for item in value if str(item).strip()]
    return cleaned or list(_DEFAULT_CONTRACT_IDS)


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _trace_refs(value: object) -> list[Any]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, (dict, str))]
