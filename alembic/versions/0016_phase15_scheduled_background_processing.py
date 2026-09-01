"""OpenEA Community 1.5.2 scheduled background processing.

Revision ID: 0016_phase15
Revises: 0015_phase15
"""
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

import sqlalchemy as sa

from alembic import op

revision: str = "0016_phase15"
down_revision: str | None = "0015_phase15"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scheduled_job_settings",
        sa.Column("job_key", sa.String(length=100), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("interval_minutes", sa.Integer(), nullable=False),
        sa.Column("last_enqueued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.String(length=30), nullable=False, server_default="Never run"),
        sa.Column("last_result_count", sa.Integer(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("updated_by_user_id", sa.String(length=36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("job_key"),
    )
    op.create_index(
        "ix_scheduled_job_settings_enabled",
        "scheduled_job_settings",
        ["enabled"],
        unique=False,
    )
    op.create_index(
        "ix_scheduled_job_settings_next_run_at",
        "scheduled_job_settings",
        ["next_run_at"],
        unique=False,
    )

    now = datetime.now(timezone.utc)
    settings = sa.table(
        "scheduled_job_settings",
        sa.column("job_key", sa.String()),
        sa.column("enabled", sa.Boolean()),
        sa.column("interval_minutes", sa.Integer()),
        sa.column("next_run_at", sa.DateTime(timezone=True)),
        sa.column("last_status", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(
        settings,
        [
            {
                "job_key": "recalculate_all_metrics",
                "enabled": True,
                "interval_minutes": 360,
                "next_run_at": now + timedelta(hours=6),
                "last_status": "Never run",
                "created_at": now,
                "updated_at": now,
            },
            {
                "job_key": "evaluate_findings",
                "enabled": True,
                "interval_minutes": 60,
                "next_run_at": now + timedelta(hours=1),
                "last_status": "Never run",
                "created_at": now,
                "updated_at": now,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_scheduled_job_settings_next_run_at", table_name="scheduled_job_settings")
    op.drop_index("ix_scheduled_job_settings_enabled", table_name="scheduled_job_settings")
    op.drop_table("scheduled_job_settings")
