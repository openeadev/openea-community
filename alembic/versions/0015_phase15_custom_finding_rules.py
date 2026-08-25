"""OpenEA Community 1.5.0 custom declarative finding rules.

Revision ID: 0015_phase15
Revises: 0014_phase14
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0015_phase15"
down_revision: str | None = "0014_phase14"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "rule_definitions", sa.Column("created_by", sa.String(length=36), nullable=True)
    )
    op.add_column(
        "rule_definitions", sa.Column("updated_by", sa.String(length=36), nullable=True)
    )
    op.add_column(
        "rule_definitions",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_rule_definitions_created_by_users",
        "rule_definitions",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_rule_definitions_updated_by_users",
        "rule_definitions",
        "users",
        ["updated_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_rule_definitions_archived_at",
        "rule_definitions",
        ["archived_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_rule_definitions_archived_at", table_name="rule_definitions")
    op.drop_constraint(
        "fk_rule_definitions_updated_by_users", "rule_definitions", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_rule_definitions_created_by_users", "rule_definitions", type_="foreignkey"
    )
    op.drop_column("rule_definitions", "archived_at")
    op.drop_column("rule_definitions", "updated_by")
    op.drop_column("rule_definitions", "created_by")
