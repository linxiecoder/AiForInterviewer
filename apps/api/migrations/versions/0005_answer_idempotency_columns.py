"""answer idempotency columns"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0005_answer_idempotency_columns"
down_revision = "0004_feedback_reserved_pending"
branch_labels = None
depends_on = None

ANSWER_IDEMPOTENCY_CONSTRAINT = "uq_answers_owner_actor_session_question_idem"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("answers"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("answers")}
    if "idempotency_key" not in existing_columns:
        op.add_column("answers", sa.Column("idempotency_key", sa.String(length=128), nullable=True))
    if "request_body_hash" not in existing_columns:
        op.add_column("answers", sa.Column("request_body_hash", sa.String(length=64), nullable=True))

    if bind.dialect.name == "sqlite":
        return

    constraint_names = {constraint["name"] for constraint in inspector.get_unique_constraints("answers")}
    if ANSWER_IDEMPOTENCY_CONSTRAINT in constraint_names:
        return
    op.create_unique_constraint(
        ANSWER_IDEMPOTENCY_CONSTRAINT,
        "answers",
        ["owner_id", "actor_id", "session_id", "question_id", "idempotency_key"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("answers"):
        return

    if bind.dialect.name != "sqlite":
        constraint_names = {constraint["name"] for constraint in inspector.get_unique_constraints("answers")}
        if ANSWER_IDEMPOTENCY_CONSTRAINT in constraint_names:
            op.drop_constraint(ANSWER_IDEMPOTENCY_CONSTRAINT, "answers", type_="unique")

    existing_columns = {column["name"] for column in inspector.get_columns("answers")}
    if "request_body_hash" in existing_columns:
        op.drop_column("answers", "request_body_hash")
    if "idempotency_key" in existing_columns:
        op.drop_column("answers", "idempotency_key")
