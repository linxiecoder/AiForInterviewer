"""known column backfills"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_known_column_backfills"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


KNOWN_COLUMN_BACKFILLS: tuple[tuple[str, sa.Column], ...] = (
    ("interview_sessions", sa.Column("resume_id", sa.String(80), nullable=True)),
    ("interview_sessions", sa.Column("job_id", sa.String(80), nullable=True)),
    ("polish_session_details", sa.Column("custom_topic_text_summary", sa.String(240), nullable=True)),
    ("polish_session_details", sa.Column("progress_tree_status", sa.String(40), nullable=True)),
    ("polish_session_details", sa.Column("progress_percent", sa.Integer(), nullable=True)),
    ("polish_session_details", sa.Column("progress_tree_plan_json", sa.JSON(), nullable=True)),
    ("polish_session_details", sa.Column("progress_tree_state_json", sa.JSON(), nullable=True)),
    ("questions", sa.Column("question_sources_json", sa.JSON(), nullable=True)),
    ("questions", sa.Column("question_metadata_json", sa.JSON(), nullable=True)),
    ("questions", sa.Column("progress_node_ref", sa.String(120), nullable=True)),
    ("questions", sa.Column("context_digest", sa.String(120), nullable=True)),
    ("questions", sa.Column("evidence_ref_ids", sa.JSON(), nullable=True)),
    ("weaknesses", sa.Column("title", sa.String(160), nullable=True)),
    ("weaknesses", sa.Column("summary", sa.Text(), nullable=True)),
    ("weaknesses", sa.Column("severity_hint", sa.String(40), nullable=True)),
    ("weaknesses", sa.Column("confidence_level", sa.String(40), nullable=True)),
    ("weaknesses", sa.Column("source_refs_json", sa.JSON(), nullable=True)),
    ("weaknesses", sa.Column("session_refs_json", sa.JSON(), nullable=True)),
    ("weaknesses", sa.Column("feedback_refs_json", sa.JSON(), nullable=True)),
    ("weaknesses", sa.Column("question_refs_json", sa.JSON(), nullable=True)),
    ("weaknesses", sa.Column("answer_refs_json", sa.JSON(), nullable=True)),
    ("weaknesses", sa.Column("loss_point_refs_json", sa.JSON(), nullable=True)),
    ("weaknesses", sa.Column("repeated_loss_point_refs_json", sa.JSON(), nullable=True)),
    ("weaknesses", sa.Column("evidence_refs_json", sa.JSON(), nullable=True)),
    ("weaknesses", sa.Column("trace_refs_json", sa.JSON(), nullable=True)),
    ("weaknesses", sa.Column("user_confirmation_ref_json", sa.JSON(), nullable=True)),
    ("weaknesses", sa.Column("occurrence_count", sa.Integer(), nullable=True)),
    ("weaknesses", sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True)),
    ("weaknesses", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True)),
    ("weaknesses", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True)),
    ("assets", sa.Column("asset_type", sa.String(64), nullable=True)),
    ("assets", sa.Column("title", sa.String(160), nullable=True)),
    ("assets", sa.Column("summary", sa.Text(), nullable=True)),
    ("assets", sa.Column("content", sa.Text(), nullable=True)),
    ("assets", sa.Column("source_refs_json", sa.JSON(), nullable=True)),
    ("assets", sa.Column("evidence_refs_json", sa.JSON(), nullable=True)),
    ("assets", sa.Column("trace_refs_json", sa.JSON(), nullable=True)),
    ("assets", sa.Column("resume_version_ref_json", sa.JSON(), nullable=True)),
    ("assets", sa.Column("job_version_ref_json", sa.JSON(), nullable=True)),
    ("assets", sa.Column("question_pattern", sa.String(120), nullable=True)),
    ("assets", sa.Column("created_from_candidate_id", sa.String(80), nullable=True)),
    ("assets", sa.Column("user_confirmation_ref_json", sa.JSON(), nullable=True)),
    ("assets", sa.Column("fact_source", sa.String(80), nullable=True)),
    ("asset_versions", sa.Column("content", sa.Text(), nullable=True)),
    ("asset_versions", sa.Column("edit_summary", sa.Text(), nullable=True)),
    ("asset_versions", sa.Column("created_by_actor_id", sa.String(80), nullable=True)),
    ("training_recommendations", sa.Column("title", sa.String(160), nullable=True)),
    ("training_recommendations", sa.Column("summary", sa.Text(), nullable=True)),
    ("training_recommendations", sa.Column("reason", sa.Text(), nullable=True)),
    ("training_recommendations", sa.Column("confidence_level", sa.String(40), nullable=True)),
    ("training_recommendations", sa.Column("source_refs_json", sa.JSON(), nullable=True)),
    ("training_recommendations", sa.Column("evidence_refs_json", sa.JSON(), nullable=True)),
    ("training_recommendations", sa.Column("trace_refs_json", sa.JSON(), nullable=True)),
    ("training_recommendations", sa.Column("candidate_ref_json", sa.JSON(), nullable=True)),
    ("training_recommendations", sa.Column("target_weakness_refs_json", sa.JSON(), nullable=True)),
    ("training_recommendations", sa.Column("question_pattern", sa.String(120), nullable=True)),
    ("training_recommendations", sa.Column("expected_answer_dimensions_json", sa.JSON(), nullable=True)),
    ("training_recommendations", sa.Column("created_from_candidate_id", sa.String(80), nullable=True)),
    ("training_recommendations", sa.Column("user_confirmation_ref_json", sa.JSON(), nullable=True)),
    ("training_recommendations", sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True)),
)


def upgrade() -> None:
    for table_name, column in KNOWN_COLUMN_BACKFILLS:
        _add_column_if_missing(table_name, column)


def downgrade() -> None:
    pass


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table(table_name):
        return
    existing_columns = {item["name"] for item in inspector.get_columns(table_name)}
    if column.name in existing_columns:
        return
    op.add_column(table_name, column.copy())
