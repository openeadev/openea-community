"""Phase 7 governance, reviews, audit, and comments.

Revision ID: 0007_phase7
Revises: 0006_phase6
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0007_phase7"
down_revision: str | None = "0006_phase6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSON_TYPE = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("object_id", sa.String(36), sa.ForeignKey("objects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewed_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_review_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
    )
    op.create_index("ix_reviews_object_id", "reviews", ["object_id"])
    op.create_index("ix_reviews_reviewed_at", "reviews", ["reviewed_at"])
    op.create_index("ix_reviews_next_review_date", "reviews", ["next_review_date"])

    op.create_table(
        "comments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("object_id", sa.String(36), sa.ForeignKey("objects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_comments_object_id", "comments", ["object_id"])
    op.create_index("ix_comments_created_at", "comments", ["created_at"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("before_state", JSON_TYPE, nullable=True),
        sa.Column("after_state", JSON_TYPE, nullable=True),
        sa.Column("source", sa.String(80), nullable=False, server_default="Web"),
        sa.Column("correlation_id", sa.String(80), nullable=True),
    )
    for column in ("timestamp", "user_id", "action", "entity_type", "entity_id", "correlation_id"):
        op.create_index(f"ix_audit_events_{column}", "audit_events", [column])
    op.execute("""
        CREATE OR REPLACE FUNCTION openea_prevent_audit_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_events is append-only';
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("CREATE TRIGGER trg_audit_events_immutable BEFORE UPDATE OR DELETE ON audit_events FOR EACH ROW EXECUTE FUNCTION openea_prevent_audit_mutation()")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_audit_events_immutable ON audit_events")
    op.execute("DROP FUNCTION IF EXISTS openea_prevent_audit_mutation()")
    op.drop_table("audit_events")
    op.drop_table("comments")
    op.drop_table("reviews")
