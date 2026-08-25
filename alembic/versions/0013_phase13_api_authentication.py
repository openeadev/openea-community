"""OpenEA Community 1.3.0 API authentication.

Revision ID: 0013_phase13
Revises: 0012_phase12
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0013_phase13"
down_revision: str | None = "0012_phase12"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_service_account", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_users_is_service_account", "users", ["is_service_account"])
    json_type = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")
    op.create_table(
        "api_tokens",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("token_prefix", sa.String(length=32), nullable=False, unique=True),
        sa.Column("token_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("scopes", json_type, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
    )
    op.create_index("ix_api_tokens_user_id", "api_tokens", ["user_id"])
    op.create_index("ix_api_tokens_token_prefix", "api_tokens", ["token_prefix"], unique=True)
    op.create_index("ix_api_tokens_expires_at", "api_tokens", ["expires_at"])
    op.create_index("ix_api_tokens_revoked_at", "api_tokens", ["revoked_at"])


def downgrade() -> None:
    op.drop_table("api_tokens")
    op.drop_index("ix_users_is_service_account", table_name="users")
    op.drop_column("users", "is_service_account")
