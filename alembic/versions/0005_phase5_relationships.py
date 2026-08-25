"""Phase 5 relationship records.

Revision ID: 0005_phase5
Revises: 0004_phase4
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005_phase5"
down_revision: str | None = "0004_phase4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    json_type = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")
    op.create_table(
        "relationships",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("relationship_type_id", sa.String(length=36), sa.ForeignKey("relationship_types.id"), nullable=False),
        sa.Column("source_object_id", sa.String(length=36), sa.ForeignKey("objects.id"), nullable=False),
        sa.Column("target_object_id", sa.String(length=36), sa.ForeignKey("objects.id"), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("criticality", sa.String(length=40), nullable=True),
        sa.Column("confidence", sa.String(length=40), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("properties", json_type, nullable=False),
        sa.Column("source", sa.String(length=80), nullable=True),
        sa.Column("provenance", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("relationship_type_id", "source_object_id", "target_object_id", name="uq_relationship_instance"),
    )
    for column in ("relationship_type_id", "source_object_id", "target_object_id", "archived_at"):
        op.create_index(f"ix_relationships_{column}", "relationships", [column])


def downgrade() -> None:
    op.drop_table("relationships")
