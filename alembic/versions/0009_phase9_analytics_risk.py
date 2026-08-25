"""Phase 9 analytics, persisted metrics, and PostgreSQL-backed jobs.

Revision ID: 0009_phase9
Revises: 0008_phase8
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0009_phase9"
down_revision: str | None = "0008_phase8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSON_TYPE = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.create_table(
        "object_metrics",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("object_id", sa.String(length=36), nullable=False),
        sa.Column("metric_type", sa.String(length=80), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("band", sa.String(length=40), nullable=False),
        sa.Column("explanation", JSON_TYPE, nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("object_id", "metric_type", name="uq_object_metric_type"),
    )
    op.create_index("ix_object_metrics_object_id", "object_metrics", ["object_id"], unique=False)
    op.create_index("ix_object_metrics_metric_type", "object_metrics", ["metric_type"], unique=False)
    op.create_index("ix_object_metrics_band", "object_metrics", ["band"], unique=False)
    op.create_index("ix_object_metrics_calculated_at", "object_metrics", ["calculated_at"], unique=False)

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_type", sa.String(length=100), nullable=False),
        sa.Column("payload", JSON_TYPE, nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.String(length=120), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_job_type", "jobs", ["job_type"], unique=False)
    op.create_index("ix_jobs_status", "jobs", ["status"], unique=False)
    op.create_index("ix_jobs_available_at", "jobs", ["available_at"], unique=False)
    op.create_index("ix_jobs_correlation_id", "jobs", ["correlation_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_jobs_correlation_id", table_name="jobs")
    op.drop_index("ix_jobs_available_at", table_name="jobs")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_index("ix_jobs_job_type", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index("ix_object_metrics_calculated_at", table_name="object_metrics")
    op.drop_index("ix_object_metrics_band", table_name="object_metrics")
    op.drop_index("ix_object_metrics_metric_type", table_name="object_metrics")
    op.drop_index("ix_object_metrics_object_id", table_name="object_metrics")
    op.drop_table("object_metrics")
