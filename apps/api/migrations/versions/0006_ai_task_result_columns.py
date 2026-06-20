"""ai task result safe summary columns"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0006_ai_task_result_columns"
down_revision = "0005_answer_idempotency_columns"
branch_labels = None
depends_on = None


AI_TASK_RESULT_COLUMN_NAMES: tuple[str, ...] = (
    "candidate_refs_json",
    "suggestion_refs_json",
    "validation_errors_json",
    "source_availability",
    "low_confidence_flags_json",
    "safe_summary_json",
)


def _ai_task_result_columns() -> tuple[sa.Column, ...]:
    return (
        sa.Column("candidate_refs_json", sa.JSON(), nullable=True),
        sa.Column("suggestion_refs_json", sa.JSON(), nullable=True),
        sa.Column("validation_errors_json", sa.JSON(), nullable=True),
        sa.Column("source_availability", sa.String(length=40), nullable=True),
        sa.Column("low_confidence_flags_json", sa.JSON(), nullable=True),
        sa.Column("safe_summary_json", sa.JSON(), nullable=True),
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("ai_task_results"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("ai_task_results")}
    for column in _ai_task_result_columns():
        if column.name not in existing_columns:
            op.add_column("ai_task_results", column)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("ai_task_results"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("ai_task_results")}
    for column_name in reversed(AI_TASK_RESULT_COLUMN_NAMES):
        if column_name in existing_columns:
            op.drop_column("ai_task_results", column_name)
