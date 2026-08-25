"""Phase 10 findings engine and declarative rules.

Revision ID: 0010_phase10
Revises: 0009_phase9
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0010_phase10"
down_revision: str | None = "0009_phase9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSON_TYPE = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.create_table(
        "rule_definitions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("rule_id", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("rule_type", sa.String(80), nullable=False),
        sa.Column("severity", sa.String(30), nullable=False),
        sa.Column("config", JSON_TYPE, nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_rule_definitions_rule_id", "rule_definitions", ["rule_id"])
    op.create_index("ix_rule_definitions_rule_type", "rule_definitions", ["rule_type"])
    op.create_index("ix_rule_definitions_severity", "rule_definitions", ["severity"])
    op.create_index("ix_rule_definitions_enabled", "rule_definitions", ["enabled"])

    op.create_table(
        "findings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("finding_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(30), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("rule_definition_id", sa.String(36), nullable=False),
        sa.Column("related_object_id", sa.String(36), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("assigned_user_id", sa.String(36), nullable=True),
        sa.Column("assigned_role", sa.String(80), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("dismissal_reason", sa.Text(), nullable=True),
        sa.Column("evidence", JSON_TYPE, nullable=False),
        sa.ForeignKeyConstraint(["rule_definition_id"], ["rule_definitions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["related_object_id"], ["objects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("rule_definition_id", "related_object_id", name="uq_finding_rule_object"),
    )
    for column in ["finding_type", "severity", "rule_definition_id", "related_object_id", "detected_at", "last_evaluated_at", "status", "assigned_user_id"]:
        op.create_index(f"ix_findings_{column}", "findings", [column])




def downgrade() -> None:
    op.drop_table("findings")
    op.drop_table("rule_definitions")
